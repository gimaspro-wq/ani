"""Shikimori API client for fetching anime metadata."""
import logging
from typing import Optional, Dict, Any, List

from parser.clients import HTTPClient
from parser.config import settings
from parser.utils import RateLimiter

logger = logging.getLogger(__name__)


class ShikimoriClient:
    """Client for Shikimori API."""
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize Shikimori client.
        
        Args:
            rate_limiter: Optional rate limiter instance
        """
        self.http_client = HTTPClient(
            base_url=settings.SHIKIMORI_BASE_URL,
            rate_limiter=rate_limiter,
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def get_anime(self, shikimori_id: int) -> Optional[Dict[str, Any]]:
        """
        Get anime details from Shikimori.
        
        Args:
            shikimori_id: The Shikimori anime ID
            
        Returns:
            Anime data dictionary or None if not found
        """
        try:
            response = await self.http_client.get(f"/animes/{shikimori_id}")
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching anime {shikimori_id} from Shikimori: {e}")
            return None
    
    def parse_anime_data(self, shikimori_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Shikimori anime data into backend schema format.
        
        Args:
            shikimori_data: Raw data from Shikimori API
            
        Returns:
            Parsed data matching AnimeImportSchema
        """
        # Extract relevant fields
        anime_id = shikimori_data.get("id")
        
        # Get title (prefer English, fallback to Russian or romaji)
        title = shikimori_data.get("name") or shikimori_data.get("russian") or ""
        
        # Alternative titles
        alternative_titles = []
        if shikimori_data.get("russian") and shikimori_data.get("russian") != title:
            alternative_titles.append(shikimori_data["russian"])
        if shikimori_data.get("japanese"):
            japanese_title = ", ".join(shikimori_data["japanese"]) if isinstance(
                shikimori_data["japanese"], list
            ) else shikimori_data["japanese"]
            if japanese_title:
                alternative_titles.append(japanese_title)
        if shikimori_data.get("english"):
            english_titles = shikimori_data["english"] if isinstance(
                shikimori_data["english"], list
            ) else [shikimori_data["english"]]
            for eng_title in english_titles:
                if eng_title and eng_title != title:
                    alternative_titles.append(eng_title)
        
        # Description
        description = shikimori_data.get("description") or None
        
        # Year from aired_on date
        year = None
        if shikimori_data.get("aired_on"):
            try:
                year = int(shikimori_data["aired_on"][:4])
            except (ValueError, TypeError):
                pass
        
        # Status mapping
        status_map = {
            "ongoing": "ongoing",
            "released": "completed",
            "anons": "upcoming",
        }
        status = status_map.get(shikimori_data.get("status"), None)
        
        # Poster URL
        poster = None
        if shikimori_data.get("image"):
            if isinstance(shikimori_data["image"], dict):
                # Prefer original, fallback to preview or x96
                poster = (
                    shikimori_data["image"].get("original") or
                    shikimori_data["image"].get("preview") or
                    shikimori_data["image"].get("x96")
                )
                # Make absolute URL
                if poster and poster.startswith("/"):
                    poster = f"https://shikimori.one{poster}"
            elif isinstance(shikimori_data["image"], str):
                poster = shikimori_data["image"]
                if poster.startswith("/"):
                    poster = f"https://shikimori.one{poster}"
        
        # Genres
        genres = []
        if shikimori_data.get("genres"):
            for genre in shikimori_data["genres"]:
                if isinstance(genre, dict) and genre.get("name"):
                    genres.append(genre["name"])
                elif isinstance(genre, str):
                    genres.append(genre)
        
        return {
            "source_id": str(anime_id),
            "title": title,
            "alternative_titles": alternative_titles if alternative_titles else None,
            "description": description,
            "year": year,
            "status": status,
            "poster": poster,
            "genres": genres if genres else None,
        }
