from __future__ import annotations

import logging
from typing import Iterable, Optional

import httpx

from parser.client import HttpClient
from parser.config import Settings
from parser.normalizer import Anime, Episode, VideoPlayer, VideoSource

from .base import SourceAdapter


class GogoAnimeAdapter(SourceAdapter):
    """
    Adapter for the consumet.org gogoanime API.

    The adapter relies on the following endpoints:
    - `{base_url}/top-airing?page={page}`
    - `{base_url}/info/{anime_id}`
    - `{base_url}/watch/{episode_id}`
    """

    source_name = "gogoanime"

    def __init__(self, http_client: HttpClient, settings: Settings) -> None:
        super().__init__(http_client)
        self.base_url = settings.consumet_base_url.rstrip("/")
        self.settings = settings
        self.log = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def fetch_anime_list(self, limit: int) -> Iterable[Anime]:
        collected = 0
        page = 1
        while collected < limit:
            url = f"{self.base_url}/top-airing"
            try:
                response = self.http.request("GET", url, params={"page": page})
                data = response.json()
            except Exception as exc:  # noqa: BLE001
                self.log.error("Failed to fetch top airing page %s: %s", page, exc)
                break

            results = data.get("results") or []
            if not results:
                break
            for item in results:
                anime = self._normalize_anime(item)
                if anime:
                    yield anime
                    collected += 1
                    if collected >= limit:
                        break
            if not data.get("hasNextPage"):
                break
            page += 1

    def fetch_episodes(self, anime: Anime) -> list[Episode]:
        info = self._fetch_info(anime.source_id)
        if not info:
            return []
        episodes_data = info.get("episodes") or []
        episodes: list[Episode] = []
        for ep in episodes_data:
            number = ep.get("number")
            source_episode_id = ep.get("id")
            if source_episode_id is None or number is None:
                continue
            episodes.append(
                Episode(
                    anime_source_id=anime.source_id,
                    source_episode_id=str(source_episode_id),
                    number=int(number),
                    title=ep.get("title"),
                    is_available=True,
                )
            )
        return episodes

    def fetch_video(self, episode: Episode) -> Optional[VideoSource]:
        url = f"{self.base_url}/watch/{episode.source_episode_id}"
        try:
            response = self.http.request("GET", url)
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            self.log.error("Failed to fetch video for %s: %s", episode.source_episode_id, exc)
            return None

        sources = payload.get("sources") or []
        if not sources:
            return None

        # Choose the best available source (prefer m3u8, then highest quality)
        def score(item: dict) -> tuple[int, int]:
            is_m3u8 = 1 if item.get("isM3U8") else 0
            quality = item.get("quality") or ""
            try:
                numeric = int(str(quality).replace("p", ""))
            except ValueError:
                numeric = 0
            return (is_m3u8, numeric)

        best = sorted(sources, key=score, reverse=True)[0]
        player_type = "m3u8" if best.get("isM3U8") else "mp4"
        url_value = best.get("url")
        if not url_value:
            return None
        return VideoSource(
            source_name=self.source_name,
            source_episode_id=episode.source_episode_id,
            player=VideoPlayer(
                type=player_type,
                url=url_value,
                source_name=best.get("server") or "gogoanime-cdn",
                priority=10 if best.get("isM3U8") else 5,
            ),
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _fetch_info(self, anime_id: str) -> dict:
        url = f"{self.base_url}/info/{anime_id}"
        try:
            response = self.http.request("GET", url)
            return response.json()
        except Exception as exc:  # noqa: BLE001
            self.log.error("Failed to fetch info for %s: %s", anime_id, exc)
            return {}

    def _normalize_anime(self, item: dict) -> Optional[Anime]:
        try:
            source_id = str(item["id"])
            title = item.get("title") or item.get("name")
            if not title:
                return None
            year = self._parse_year(item.get("releaseDate") or item.get("released"))
            status = self._normalize_status(item.get("status"))
            return Anime(
                source_name=self.source_name,
                source_id=source_id,
                title=title,
                alternative_titles=[],
                description=item.get("description"),
                year=year,
                status=status,
                poster=item.get("image"),
                genres=item.get("genres") or [],
            )
        except Exception as exc:  # noqa: BLE001
            self.log.error("Failed to normalize anime item %s: %s", item, exc)
            return None

    @staticmethod
    def _normalize_status(status: Optional[str]) -> Optional[str]:
        if not status:
            return None
        status_lower = status.lower()
        if "ongoing" in status_lower or "airing" in status_lower:
            return "ongoing"
        if "completed" in status_lower or "finished" in status_lower:
            return "completed"
        if "upcoming" in status_lower:
            return "upcoming"
        return None

    @staticmethod
    def _parse_year(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(str(value)[:4])
        except ValueError:
            return None
