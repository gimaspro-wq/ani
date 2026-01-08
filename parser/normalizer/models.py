from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Anime:
    source_name: str
    source_id: str
    title: str
    alternative_titles: List[str] = field(default_factory=list)
    description: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    poster: Optional[str] = None
    genres: List[str] = field(default_factory=list)


@dataclass
class Episode:
    anime_source_id: str
    source_episode_id: str
    number: int
    title: Optional[str] = None
    is_available: bool = True


@dataclass
class VideoPlayer:
    type: str
    url: str
    source_name: str
    priority: int = 0


@dataclass
class VideoSource:
    source_name: str
    source_episode_id: str
    player: VideoPlayer
