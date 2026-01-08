from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Iterable, Optional

from parser.client import HttpClient
from parser.normalizer import Anime, Episode, VideoSource


class SourceAdapter(ABC):
    """Abstract base class for all source adapters."""

    source_name: str

    def __init__(self, http_client: HttpClient) -> None:
        self.http = http_client
        self.log = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fetch_anime_list(self, limit: int) -> Iterable[Anime]:
        """Return iterable of Anime objects."""

    @abstractmethod
    def fetch_episodes(self, anime: Anime) -> list[Episode]:
        """Return list of Episode objects for the given anime."""

    @abstractmethod
    def fetch_video(self, episode: Episode) -> Optional[VideoSource]:
        """Return video source for the given episode if available."""
