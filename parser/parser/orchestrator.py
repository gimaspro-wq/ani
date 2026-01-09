"""Main orchestrator for the parser service."""
import asyncio
import logging
from typing import Optional, Any, Dict

from parser.config import settings
from parser.clients.kodik import KodikClient
from parser.clients.shikimori import ShikimoriClient
from parser.clients.backend import BackendClient
from parser.utils import (
    RateLimiter,
    compute_diff,
    generate_source_id,
    generate_episode_source_id,
    normalize_video_source,
)
from parser.state import StateManager

logger = logging.getLogger(__name__)


def _video_key(episode_source_id: str, player_data: Dict[str, Any]) -> str:
    """Build consistent deduplication key for a video payload."""
    url = player_data.get("url")
    source_name = player_data.get("source_name")
    if not url or not source_name:
        raise ValueError("player_data must include url and source_name")
    return f"{episode_source_id}|{url}|{source_name}"


def _build_episode_payload(episode_source_id: str, ep: Dict[str, Any], is_available: bool) -> Dict[str, Any]:
    """Create canonical episode payload for backend import."""
    return {
        "source_episode_id": episode_source_id,
        "number": ep["number"],
        "title": ep.get("title"),
        "is_available": is_available,
    }


class ParserOrchestrator:
    """Orchestrates the parsing and import process."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.rate_limiter = RateLimiter(settings.RATE_LIMIT_RPS)
        self.kodik_client = KodikClient(rate_limiter=self.rate_limiter)
        self.shikimori_client = ShikimoriClient(rate_limiter=self.rate_limiter)
        self.backend_client = BackendClient(rate_limiter=self.rate_limiter)
        self.state_manager = StateManager(settings.STATE_PATH)
        self.semaphore = asyncio.Semaphore(settings.CONCURRENCY)
    
    async def close(self):
        """Close all clients."""
        await self.kodik_client.close()
        await self.shikimori_client.close()
        await self.backend_client.close()
    
    async def process_anime(self, shikimori_id: int) -> bool:
        """
        Process a single anime: fetch metadata and import.
        
        Args:
            shikimori_id: The Shikimori anime ID
            
        Returns:
            True if successful, False otherwise
        """
        async with self.semaphore:
            source_id = generate_source_id(shikimori_id)
            previous_entry = self.state_manager.get_anime_entry(source_id)
            
            try:
                # Step 1: Fetch metadata from Shikimori
                logger.info(f"Fetching metadata for anime {shikimori_id} from Shikimori")
                shikimori_data = await self.shikimori_client.get_anime(shikimori_id)
                
                if not shikimori_data:
                    logger.warning(f"No metadata found for anime {shikimori_id}")
                    return False
                
                # Parse Shikimori data
                anime_data = self.shikimori_client.parse_anime_data(shikimori_data)
                anime_payload = {
                    "title": anime_data["title"],
                    "alternative_titles": anime_data.get("alternative_titles"),
                    "description": anime_data.get("description"),
                    "year": anime_data.get("year"),
                    "status": anime_data.get("status"),
                    "poster": anime_data.get("poster"),
                    "genres": anime_data.get("genres"),
                    "source_id": anime_data.get("source_id"),
                }
                
                previous_anime_payload = previous_entry.get("anime_payload")
                anime_diff = compute_diff(anime_payload, previous_anime_payload)
                if previous_anime_payload is None or anime_diff:
                    if anime_diff:
                        logger.debug(f"Anime diff for {source_id}: {anime_diff}")
                    logger.info(f"Importing anime: {anime_data['title']}")
                    success = await self.backend_client.import_anime(anime_data)
                    
                    if not success:
                        logger.error(f"Failed to import anime {anime_data['title']}")
                        return False
                else:
                    logger.info(f"Anime {source_id} up-to-date, skipping import")
                
                # Step 3: Fetch episodes from Kodik
                logger.info(f"Fetching episodes for anime {shikimori_id} from Kodik")
                kodik_results = await self.kodik_client.get_anime_episodes(shikimori_id)
                
                if kodik_results is None:
                    logger.error(f"Failed to fetch episodes for anime {shikimori_id}, skipping title")
                    return False
                
                if not kodik_results:
                    logger.warning(f"No episodes found for anime {shikimori_id}, skipping title")
                    return False
                
                # Parse episodes
                episodes_data = self.kodik_client.parse_episodes(kodik_results, shikimori_id)
                
                # Step 4: Validate episode count is known
                if not episodes_data:
                    logger.warning(
                        f"Episode count unknown for anime {shikimori_id}, skipping title"
                    )
                    return False
                
                logger.info(f"Found {len(episodes_data)} episodes for anime {shikimori_id}")
                
                # Step 4: Import episodes to backend (only changed/new)
                episodes_for_import = []
                episodes_state: dict[str, dict[str, Any]] = previous_entry.get("episodes", {})
                videos_state: dict[str, dict[str, Any]] = previous_entry.get("videos", {})
                
                episode_videos: dict[str, list[dict[str, Any]]] = {}
                
                for ep in episodes_data:
                    episode_source_id = generate_episode_source_id(source_id, ep["number"])
                    
                    translations = ep.get("translations") or []
                    normalized_videos = []
                    seen_keys: set[str] = set()
                    for idx, translation in enumerate(translations):
                        player = normalize_video_source(
                            translation.get("link"),
                            "kodik",
                            idx,
                        )
                        if player is None:
                            continue
                        key = _video_key(episode_source_id, player)
                        if key in seen_keys:
                            continue
                        seen_keys.add(key)
                        normalized_videos.append(player)
                    episode_videos[episode_source_id] = normalized_videos
                    
                    is_available = bool(normalized_videos)
                    
                    episode_payload = _build_episode_payload(episode_source_id, ep, is_available)
                    
                    previous_episode_payload = episodes_state.get(episode_source_id)
                    ep_diff = compute_diff(episode_payload, previous_episode_payload)
                    if previous_episode_payload is None or ep_diff:
                        if ep_diff:
                            logger.debug(f"Episode diff for {episode_source_id}: {ep_diff}")
                        episodes_for_import.append(episode_payload)
                        episodes_state[episode_source_id] = episode_payload
                
                if episodes_for_import:
                    logger.info(f"Importing {len(episodes_for_import)} episodes for anime {source_id}")
                    success = await self.backend_client.import_episodes(
                        anime_source_id=source_id,
                        episodes=episodes_for_import,
                    )
                    
                    if not success:
                        logger.error(f"Failed to import episodes for anime {source_id}")
                        return False
                else:
                    logger.info(f"No episode changes detected for anime {source_id}, skipping import")
                
                # Step 5: Import video sources for each episode (only changed/new)
                video_import_errors = 0
                latest_video_payloads = {}
                for ep in episodes_data:
                    episode_source_id = generate_episode_source_id(source_id, ep["number"])
                    videos_for_episode = episode_videos.get(episode_source_id, [])
                    
                    if not videos_for_episode:
                        logger.warning(
                            f"No videos for episode {ep['number']} of anime {source_id}, "
                            "but episode remains"
                        )
                        continue
                    
                    for player_data in videos_for_episode:
                        key = _video_key(episode_source_id, player_data)
                        previous_video_payload = videos_state.get(key)
                        video_diff = compute_diff(player_data, previous_video_payload)
                        if previous_video_payload is not None and not video_diff:
                            logger.debug(
                                f"Video already imported for episode {episode_source_id}: {player_data['url']}"
                            )
                            continue
                        
                        success = await self.backend_client.import_video(
                            source_episode_id=episode_source_id,
                            player_data=player_data,
                        )
                        if not success:
                            video_import_errors += 1
                        else:
                            videos_state[key] = player_data
                            latest_video_payloads[key] = player_data
                
                if video_import_errors > 0:
                    logger.warning(
                        f"Failed to import {video_import_errors} video(s) for anime {source_id}"
                    )
                
                # Persist latest payloads for idempotency on subsequent runs
                latest_episode_payloads: dict[str, dict[str, Any]] = dict(episodes_state)
                # Mark as processed with payload snapshots
                self.state_manager.mark_anime_processed(
                    source_id=source_id,
                    title=anime_data["title"],
                    episodes_count=len(episodes_data),
                    anime_payload=anime_payload,
                    episodes_payload=latest_episode_payloads,
                    videos_payload=latest_video_payloads,
                )
                
                logger.info(
                    f"Successfully processed anime: {anime_data['title']} "
                    f"({len(episodes_data)} episodes)"
                )
                return True
                
            except Exception as e:
                logger.error(f"Error processing anime {shikimori_id}: {e}", exc_info=True)
                return False
    
    async def run(self, max_pages: Optional[int] = None):
        """
        Run the parser to fetch and import anime.
        
        Args:
            max_pages: Maximum number of pages to process (None = all)
        """
        logger.info("Starting parser run")
        logger.info(f"Backend: {settings.BACKEND_BASE_URL}")
        logger.info(f"Source name: {settings.SOURCE_NAME}")
        logger.info(f"Concurrency: {settings.CONCURRENCY}")
        logger.info(f"Rate limit: {settings.RATE_LIMIT_RPS} RPS")
        
        page = 1
        total_processed = 0
        total_failed = 0
        consecutive_errors = 0
        
        try:
            while True:
                if max_pages and page > max_pages:
                    logger.info(f"Reached max pages limit: {max_pages}")
                    break
                
                # Fail-fast: Stop if too many consecutive errors
                if consecutive_errors >= settings.MAX_CONSECUTIVE_ERRORS:
                    logger.error(
                        f"Stopping job: {consecutive_errors} consecutive errors "
                        f"(threshold: {settings.MAX_CONSECUTIVE_ERRORS})"
                    )
                    break
                
                logger.info(f"Fetching page {page} from Kodik")
                response = await self.kodik_client.list_anime(
                    limit=100,
                    page=page,
                    with_material_data=True,
                )
                
                if not response or not response.get("results"):
                    logger.info("No more results from Kodik")
                    break
                
                results = response["results"]
                logger.info(f"Got {len(results)} anime from page {page}")
                
                # Process anime in parallel (controlled by semaphore)
                tasks = []
                for item in results:
                    shikimori_id = self.kodik_client.extract_shikimori_id(item)
                    if not shikimori_id:
                        logger.warning(f"No Shikimori ID found for item: {item.get('title')}")
                        continue
                    
                    tasks.append(self.process_anime(shikimori_id))
                
                # Wait for all tasks in this page to complete
                # Use return_exceptions=True to prevent one failure from stopping all
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count results and track consecutive errors
                page_success = 0
                page_failed = 0
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Exception during processing: {result}")
                        page_failed += 1
                        total_failed += 1
                    elif result:
                        page_success += 1
                        total_processed += 1
                    else:
                        page_failed += 1
                        total_failed += 1
                
                # Update consecutive error counter
                if page_success > 0:
                    # Reset counter if any success in this page
                    consecutive_errors = 0
                else:
                    # All failed in this page
                    consecutive_errors += 1
                    logger.warning(
                        f"Page {page}: All {page_failed} anime failed. "
                        f"Consecutive error pages: {consecutive_errors}"
                    )
                
                # Save state after each page
                self.state_manager.set_last_page(page)
                self.state_manager.save_state()
                
                # Check if there are more pages
                total = response.get("total", 0)
                if page * 100 >= total:
                    logger.info("Reached last page")
                    break
                
                page += 1
            
            logger.info(
                f"Parser run completed. Processed: {total_processed}, Failed: {total_failed}"
            )
            
        except Exception as e:
            # Log but don't crash - graceful degradation
            logger.error(f"Error during parser run: {e}", exc_info=True)
            logger.warning("Parser run stopped due to error, but processed data is saved")
        finally:
            await self.close()
