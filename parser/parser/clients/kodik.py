"""Kodik API client for fetching video sources."""
import logging
from typing import Optional, Dict, Any, List

from parser.clients import HTTPClient
from parser.config import settings
from parser.utils import RateLimiter

logger = logging.getLogger(__name__)


class KodikClient:
    """Client for Kodik API."""
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize Kodik client.
        
        Args:
            rate_limiter: Optional rate limiter instance
        """
        self.http_client = HTTPClient(
            base_url=settings.KODIK_BASE_URL,
            rate_limiter=rate_limiter,
        )
        self.api_token = settings.KODIK_API_TOKEN
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def list_anime(
        self,
        limit: int = 100,
        page: int = 1,
        with_material_data: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        List anime from Kodik catalog.
        
        Args:
            limit: Number of results per page (max 100)
            page: Page number (1-indexed)
            with_material_data: Include material data (Shikimori ID, etc.)
            
        Returns:
            API response with 'results' and 'total' fields, or None on error
        """
        try:
            params = {
                "token": self.api_token,
                "types": "anime-serial,anime",
                "limit": min(limit, 100),
                "page": page,
            }
            if with_material_data:
                params["with_material_data"] = "true"
            
            response = await self.http_client.get("/list", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error listing anime from Kodik (page {page}): {e}")
            return None
    
    async def get_anime_episodes(
        self,
        shikimori_id: int,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get episodes for a specific anime by Shikimori ID.
        
        Args:
            shikimori_id: The Shikimori anime ID
            
        Returns:
            List of episode data from Kodik, or None on error
        """
        try:
            params = {
                "token": self.api_token,
                "shikimori_id": str(shikimori_id),
                "with_episodes": "true",
            }
            
            response = await self.http_client.get("/search", params=params)
            data = response.json()
            
            if not data.get("results"):
                logger.warning(f"No episodes found for Shikimori ID {shikimori_id}")
                return []
            
            return data["results"]
        except Exception as e:
            logger.error(f"Error fetching episodes for Shikimori ID {shikimori_id}: {e}")
            return None
    
    def extract_shikimori_id(self, kodik_item: Dict[str, Any]) -> Optional[int]:
        """
        Extract Shikimori ID from Kodik API item.
        
        Args:
            kodik_item: Item from Kodik API results
            
        Returns:
            Shikimori ID or None if not found
        """
        # Try material_data first
        if kodik_item.get("material_data"):
            if isinstance(kodik_item["material_data"], dict):
                shiki_id = kodik_item["material_data"].get("shikimori_id")
                if shiki_id:
                    try:
                        return int(shiki_id)
                    except (ValueError, TypeError):
                        pass
        
        # Fallback to direct shikimori_id field
        if kodik_item.get("shikimori_id"):
            try:
                return int(kodik_item["shikimori_id"])
            except (ValueError, TypeError):
                pass
        
        return None
    
    def parse_episodes(
        self,
        kodik_results: List[Dict[str, Any]],
        shikimori_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Parse episodes from Kodik results into a structured format.
        
        Args:
            kodik_results: Results from Kodik API
            shikimori_id: The Shikimori anime ID for this anime
            
        Returns:
            List of episode data with numbers, translations, and player URLs
        """
        episodes_data = {}
        
        for item in kodik_results:
            # Get translation info
            translation = item.get("translation", {})
            translation_id = translation.get("id") if isinstance(translation, dict) else None
            translation_title = translation.get("title") if isinstance(translation, dict) else "Unknown"
            
            # Get link (player URL)
            link = item.get("link")
            if not link:
                continue
            
            # Parse episodes from the item
            seasons = item.get("seasons")
            if not seasons:
                continue
            
            # Kodik can have multiple seasons; we'll process all episodes
            for season_num, episodes in seasons.items():
                if not isinstance(episodes, dict):
                    continue
                
                for ep_num_str, ep_data in episodes.items():
                    try:
                        ep_num = int(ep_num_str)
                    except (ValueError, TypeError):
                        continue
                    
                    if ep_num not in episodes_data:
                        episodes_data[ep_num] = {
                            "number": ep_num,
                            "title": ep_data.get("title"),
                            "translations": [],
                        }
                    
                    # Add translation/player info
                    episodes_data[ep_num]["translations"].append({
                        "translation_id": translation_id,
                        "translation_title": translation_title,
                        "link": link,
                    })
        
        # Convert to sorted list
        return sorted(episodes_data.values(), key=lambda x: x["number"])
