"""Main orchestrator for the parser service."""
import asyncio
import logging
from typing import Optional

from parser.config import settings
from parser.clients.kodik import KodikClient
from parser.clients.shikimori import ShikimoriClient
from parser.clients.backend import BackendClient
from parser.utils import RateLimiter, generate_source_id, generate_episode_source_id
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
            
            # Check if already processed (idempotent)
            if self.state_manager.is_anime_processed(source_id):
                logger.debug(f"Anime {source_id} already processed, skipping")
                return True
            
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
                    logger.error(f"Failed to fetch episodes for anime {shikimori_id}")
                    return False
                
                if not kodik_results:
                    logger.warning(f"No episodes found for anime {shikimori_id}")
                    # Mark as processed even if no episodes
                    self.state_manager.mark_anime_processed(
                        source_id=source_id,
                        title=anime_data["title"],
                        episodes_count=0,
                    )
                    return True
                
                # Parse episodes
                episodes_data = self.kodik_client.parse_episodes(kodik_results, shikimori_id)
                
                if not episodes_data:
                    logger.warning(f"No episodes parsed for anime {shikimori_id}")
                    self.state_manager.mark_anime_processed(
                        source_id=source_id,
                        title=anime_data["title"],
                        episodes_count=0,
                    )
                    return True
                
                # Step 4: Import episodes to backend
                episodes_for_import = []
                for ep in episodes_data:
                    episode_source_id = generate_episode_source_id(source_id, ep["number"])
                    episodes_for_import.append({
                        "source_episode_id": episode_source_id,
                        "number": ep["number"],
                        "title": ep.get("title"),
                        "is_available": True,
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
                for ep in episodes_data:
                    episode_source_id = generate_episode_source_id(source_id, ep["number"])
                    
                    # Import all translations/players for this episode
                    for idx, translation in enumerate(ep.get("translations", [])):
                        player_data = {
                            "type": "iframe",
                            "url": translation["link"],
                            "source_name": "kodik",  # Player source name as per requirement
                            "priority": idx,  # Lower index = higher priority
                        }
                        
                        await self.backend_client.import_video(
                            source_episode_id=episode_source_id,
                            player_data=player_data,
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
        
        try:
            while True:
                if max_pages and page > max_pages:
                    logger.info(f"Reached max pages limit: {max_pages}")
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
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count results
                for result in results:
                    if isinstance(result, Exception):
                        total_failed += 1
                    elif result:
                        total_processed += 1
                    else:
                        total_failed += 1
                
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
            logger.error(f"Error during parser run: {e}", exc_info=True)
        finally:
            await self.close()
