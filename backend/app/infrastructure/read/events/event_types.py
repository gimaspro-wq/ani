"""Business-level event DTOs carrying only primitive data."""
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class AnimeContentChanged:
    anime_id: int
    slug: str
    source_name: Optional[str] = None


@dataclass(slots=True)
class UserLibraryChanged:
    user_id: int
    provider: str


@dataclass(slots=True)
class UserProgressChanged:
    user_id: int
    provider: str


@dataclass(slots=True)
class UserHistoryChanged:
    user_id: int
    provider: str
