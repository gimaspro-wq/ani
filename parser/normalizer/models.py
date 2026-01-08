from dataclasses import dataclass, field


@dataclass
class Anime:
    source_name: str
    source_id: str
    title: str
    alternative_titles: list[str] = field(default_factory=list)
    description: str | None = None
    year: int | None = None
    status: str | None = None
    poster: str | None = None
    genres: list[str] = field(default_factory=list)


@dataclass
class Episode:
    anime_source_id: str
    source_episode_id: str
    number: int
    title: str | None = None
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
