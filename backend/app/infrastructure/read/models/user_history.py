"""Read model for user last history entry."""
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class UserHistoryLast:
    history_id: int
    title_id: str
    episode_id: str
    provider: str
    position_seconds: Optional[float]
    watched_at: str
