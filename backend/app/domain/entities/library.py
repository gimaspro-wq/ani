"""Domain entities for user library, progress, and history."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.enums import LibraryStatus


@dataclass(slots=True)
class UserLibraryItem:
    id: int
    user_id: int
    provider: str
    title_id: str
    status: LibraryStatus
    is_favorite: bool
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class UserProgress:
    id: int
    user_id: int
    provider: str
    title_id: str
    episode_id: str
    position_seconds: float
    duration_seconds: float
    updated_at: datetime


@dataclass(slots=True)
class UserHistory:
    id: int
    user_id: int
    provider: str
    title_id: str
    episode_id: str
    position_seconds: Optional[float]
    watched_at: datetime
