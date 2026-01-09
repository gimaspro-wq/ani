"""Read model for user progress."""
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class UserProgressEntry:
    episode_id: str
    title_id: str
    provider: str
    position_seconds: float
    duration_seconds: float
    updated_at: str


UserProgress = list[UserProgressEntry]
