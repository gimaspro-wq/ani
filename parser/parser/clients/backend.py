"""Backend API client for importing data to the internal API."""
import logging
from typing import Dict, Any, List, Optional

from parser.clients import HTTPClient
from parser.config import settings
from parser.utils import RateLimiter

logger = logging.getLogger(__name__)


class BackendClient:
    """Client for backend internal API."""
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize backend client.
        
        Args:
            rate_limiter: Optional rate limiter instance
        """
        self.http_client = HTTPClient(
            base_url=settings.BACKEND_BASE_URL,
            rate_limiter=rate_limiter,
        )
        self.headers = {
            "X-Internal-Token": settings.INTERNAL_TOKEN,
            "Content-Type": "application/json",
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def import_anime(self, anime_data: Dict[str, Any]) -> bool:
        """
        Import anime to backend.
        
        Args:
            anime_data: Anime data matching AnimeImportSchema
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure source_name is set correctly
            anime_data["source_name"] = settings.SOURCE_NAME
            
            response = await self.http_client.post(
                "/api/v1/internal/import/anime",
                headers=self.headers,
                json=anime_data,
            )
            result = response.json()
            
            if result.get("success"):
                logger.info(f"Successfully imported anime: {anime_data.get('title')}")
                return True
            else:
                logger.error(f"Failed to import anime: {result.get('message')}")
                return False
        except Exception as e:
            logger.error(f"Error importing anime {anime_data.get('title')}: {e}")
            return False
    
    async def import_episodes(
        self,
        anime_source_id: str,
        episodes: List[Dict[str, Any]],
    ) -> bool:
        """
        Import episodes to backend.
        
        Args:
            anime_source_id: The anime source ID
            episodes: List of episodes matching EpisodeImportItem schema
            
        Returns:
            True if successful, False otherwise
        """
        if not episodes:
            logger.warning(f"No episodes to import for anime {anime_source_id}")
            return True
        
        try:
            data = {
                "source_name": settings.SOURCE_NAME,
                "anime_source_id": anime_source_id,
                "episodes": episodes,
            }
            
            response = await self.http_client.post(
                "/api/v1/internal/import/episodes",
                headers=self.headers,
                json=data,
            )
            result = response.json()
            
            if result.get("success"):
                logger.info(
                    f"Successfully imported {result.get('imported', 0)}/{result.get('total', 0)} "
                    f"episodes for anime {anime_source_id}"
                )
                return True
            else:
                logger.error(
                    f"Failed to import episodes for anime {anime_source_id}: "
                    f"{result.get('errors', [])}"
                )
                return False
        except Exception as e:
            logger.error(f"Error importing episodes for anime {anime_source_id}: {e}")
            return False
    
    async def import_video(
        self,
        source_episode_id: str,
        player_data: Dict[str, Any],
    ) -> bool:
        """
        Import video source to backend.
        
        Args:
            source_episode_id: The episode source ID
            player_data: Player data matching VideoPlayerSchema
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "source_name": settings.SOURCE_NAME,
                "source_episode_id": source_episode_id,
                "player": player_data,
            }
            
            response = await self.http_client.post(
                "/api/v1/internal/import/video",
                headers=self.headers,
                json=data,
            )
            result = response.json()
            
            if result.get("success"):
                logger.debug(f"Successfully imported video for episode {source_episode_id}")
                return True
            else:
                logger.error(f"Failed to import video: {result.get('message')}")
                return False
        except Exception as e:
            logger.error(f"Error importing video for episode {source_episode_id}: {e}")
            return False
