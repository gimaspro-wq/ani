"""Main orchestrator for the parser service."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from parser.config import settings
from parser.clients.kodik import KodikClient
from parser.clients.shikimori import ShikimoriClient
from parser.clients.backend import BackendClient
from parser.utils import (
    RateLimiter,
    generate_source_id,
    generate_episode_source_id,
    normalize_hls_url,
)
from parser.state import StateManager

logger = logging.getLogger(__name__)


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
            
            try:
                # Step 1: Fetch metadata from Shikimori
                logger.info(f"Fetching metadata for anime {shikimori_id} from Shikimori")
                shikimori_data = await self.shikimori_client.get_anime(shikimori_id)
                
                if not shikimori_data:
                    logger.warning(f"No metadata found for anime {shikimori_id}")
                    return False
                
                # Parse Shikimori data
                anime_data = self.shikimori_client.parse_anime_data(shikimori_data)
                
                # Step 2: Import anime to backend
                logger.info(f"Importing anime: {anime_data['title']}")
                success = await self.backend_client.import_anime(anime_data)
                
                if not success:
                    logger.error(f"Failed to import anime {anime_data['title']}")
                    return False
                
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
                
                # Update metadata with episode-derived fields
                episode_numbers = [
                    ep.get("number") for ep in episodes_data
                    if isinstance(ep.get("number"), (int, float))
                ]
                last_episode_number = max(episode_numbers) if episode_numbers else None
                now_iso = datetime.now(timezone.utc).isoformat()
                anime_metadata = {
                    **anime_data,
                    "updated_at": now_iso,
                    "last_episode_number": last_episode_number,
                    # Use import timestamp as best-available proxy for last episode time
                    "last_episode_at": now_iso if last_episode_number is not None else None,
                }
                await self.backend_client.import_anime(anime_metadata)
                
                # Step 4: Import episodes to backend
                episodes_for_import = []
                normalized_links_by_episode: dict[str, list[str]] = {}
                for ep in episodes_data:
                    episode_source_id = generate_episode_source_id(source_id, ep["number"])
                    normalized_links = []
                    for translation in ep.get("translations", []):
                        normalized = normalize_hls_url(translation.get("link"))
                        if normalized:
                            normalized_links.append(normalized)
                    normalized_links_by_episode[episode_source_id] = normalized_links
                    episodes_for_import.append({
                        "source_episode_id": episode_source_id,
                        "number": ep["number"],
                        "title": ep.get("title"),
                        "is_available": bool(normalized_links),
                    })
                
                logger.info(f"Importing {len(episodes_for_import)} episodes for anime {source_id}")
                success = await self.backend_client.import_episodes(
                    anime_source_id=source_id,
                    episodes=episodes_for_import,
                )
                
                if not success:
                    logger.error(f"Failed to import episodes for anime {source_id}")
                    return False
                
                # Step 5: Import video sources for each episode
                video_import_errors = 0
                for ep in episodes_data:
                    episode_source_id = generate_episode_source_id(source_id, ep["number"])
                    seen_urls = set()
                    normalized_links = normalized_links_by_episode.get(episode_source_id, [])
                    
                    # Check if episode has any translations
                    if not normalized_links:
                        logger.warning(
                            f"No videos for episode {ep['number']} of anime {source_id}, "
                            "but episode remains"
                        )
                        continue
                    
                    # Import all translations/players for this episode
                    for idx, normalized_url in enumerate(normalized_links):
                        if normalized_url in seen_urls:
                            continue
                        seen_urls.add(normalized_url)
                        
                        player_data = {
                            "type": "hls",
                            "url": normalized_url,
                            "source_name": settings.SOURCE_NAME,
                            "priority": idx,  # Lower index = higher priority
                        }
                        
                        # Skip this video on error, but continue with others
                        success = await self.backend_client.import_video(
                            source_episode_id=episode_source_id,
                            player_data=player_data,
                        )
                        if not success:
                            logger.error(
                                "Failed to import video for anime %s episode %s (url=%s)",
                                source_id,
                                ep["number"],
                                normalized_url,
                            )
                            video_import_errors += 1
                
                if video_import_errors > 0:
                    logger.warning(
                        f"Failed to import {video_import_errors} video(s) for anime {source_id}"
                    )
                
                # Mark as processed
                self.state_manager.mark_anime_processed(
                    source_id=source_id,
                    title=anime_data["title"],
                    episodes_count=len(episodes_data),
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
