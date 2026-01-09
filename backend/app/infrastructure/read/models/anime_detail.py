"""Read model for anime detail."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(slots=True)
class VideoSourceItem:
    type: str
    url: str
    source_name: str
    priority: int
    is_active: bool


@dataclass(slots=True)
class EpisodeItem:
    id: int
    number: int
    title: str
    video_sources: List[VideoSourceItem]


@dataclass(slots=True)
class AnimeDetail:
    slug: str
    title: str
    description: Optional[str]
    year: Optional[int]
    status: Optional[str]
    poster: Optional[str]
    genres: List[str]
    alternative_titles: List[str]
    is_active: bool
    episodes: List[EpisodeItem]
    last_updated: str
