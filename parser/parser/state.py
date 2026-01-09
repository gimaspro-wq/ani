"""State management for incremental parser runs."""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StateManager:
    """Manages parser state for incremental runs."""
    
    def __init__(self, state_path: str):
        """
        Initialize state manager.
        
        Args:
            state_path: Path to state file
        """
        self.state_path = Path(state_path)
        self.state: Dict[str, Any] = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """
        Load state from file.
        
        Returns:
            State dictionary or empty dict if file doesn't exist
        """
        if not self.state_path.exists():
            logger.info("No previous state found, starting fresh")
            return {
                "last_run": None,
                "last_page": 0,
                "processed_anime": {},
            }
        
        try:
            with open(self.state_path, "r") as f:
                state = json.load(f)
                logger.info(f"Loaded state from {self.state_path}")
                return state
        except Exception as e:
            logger.error(f"Error loading state from {self.state_path}: {e}")
            return {
                "last_run": None,
                "last_page": 0,
                "processed_anime": {},
            }
    
    def save_state(self) -> bool:
        """
        Save state to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directory if it doesn't exist
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Update last run timestamp
            self.state["last_run"] = datetime.utcnow().isoformat()
            
            with open(self.state_path, "w") as f:
                json.dump(self.state, f, indent=2)
            
            logger.info(f"Saved state to {self.state_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving state to {self.state_path}: {e}")
            return False
    
    def mark_anime_processed(
        self,
        source_id: str,
        title: str,
        episodes_count: int = 0,
        anime_payload: Optional[Dict[str, Any]] = None,
        episodes_payload: Optional[Dict[str, Dict[str, Any]]] = None,
        videos_payload: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        """
        Mark anime as processed.
        
        Args:
            source_id: The anime source ID
            title: The anime title
            episodes_count: Number of episodes imported
            anime_payload: Last imported anime payload
            episodes_payload: Mapping of episode_id -> payload
            videos_payload: Mapping of video key -> payload
        """
        entry = self.state["processed_anime"].get(source_id, {})
        entry.update({
            "title": title,
            "episodes_count": episodes_count,
            "timestamp": datetime.utcnow().isoformat(),
        })
        optional_fields = {
            "anime_payload": anime_payload,
            "episodes": episodes_payload,
            "videos": videos_payload,
        }
        entry.update({k: v for k, v in optional_fields.items() if v is not None})
        self.state["processed_anime"][source_id] = entry
    
    def is_anime_processed(self, source_id: str) -> bool:
        """
        Check if anime has been processed.
        
        Args:
            source_id: The anime source ID
            
        Returns:
            True if anime has been processed
        """
        return source_id in self.state.get("processed_anime", {})

    def get_anime_entry(self, source_id: str) -> Dict[str, Any]:
        """
        Get stored state entry for anime.

        Args:
            source_id: Anime source ID

        Returns:
            Entry dict (empty if missing)
        """
        return self.state.get("processed_anime", {}).get(source_id, {})
    
    def get_last_page(self) -> int:
        """
        Get the last processed page number.
        
        Returns:
            Last page number (0 if never run)
        """
        return self.state.get("last_page", 0)
    
    def set_last_page(self, page: int):
        """
        Set the last processed page number.
        
        Args:
            page: Page number
        """
        self.state["last_page"] = page
