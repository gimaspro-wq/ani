import logging

import httpx

from parser.normalizer import Anime, Episode, VideoSource, anime_payload, episodes_payload, video_payload

from .http_client import HttpClient


class BackendClient:
    """Client for internal backend API used by the parser."""

    def __init__(self, base_url: str, internal_token: str, http_client: HttpClient, dry_run: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.internal_token = internal_token
        self.http = http_client
        self.dry_run = dry_run

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "X-Internal-Token": self.internal_token,
        }

    def import_anime(self, anime: Anime) -> bool:
        payload = anime_payload(anime)
        if self.dry_run:
            logging.info("[DRY-RUN] Would import anime %s", anime.title)
            return True
        try:
            response = self.http.request(
                "POST",
                f"{self.base_url}/api/v1/internal/import/anime",
                json=payload,
                headers=self._headers(),
            )
            if response.status_code != httpx.codes.OK:
                logging.error("Failed to import anime %s: %s", anime.title, response.text)
                return False
            logging.info("Imported anime %s (%s)", anime.title, anime.source_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logging.exception("Error importing anime %s: %s", anime.title, exc)
            return False

    def import_episodes(self, source_name: str, anime_source_id: str, episodes: list[Episode]) -> bool:
        if not episodes:
            return True
        payload = episodes_payload(source_name, anime_source_id, episodes)
        if self.dry_run:
            logging.info("[DRY-RUN] Would import %d episodes for %s", len(episodes), anime_source_id)
            return True
        try:
            response = self.http.request(
                "POST",
                f"{self.base_url}/api/v1/internal/import/episodes",
                json=payload,
                headers=self._headers(),
            )
            if response.status_code != httpx.codes.OK:
                logging.error("Failed to import episodes for %s: %s", anime_source_id, response.text)
                return False
            logging.info("Imported %d episodes for %s", len(episodes), anime_source_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logging.exception("Error importing episodes for %s: %s", anime_source_id, exc)
            return False

    def import_video(self, video: VideoSource) -> bool:
        payload = video_payload(video)
        if self.dry_run:
            logging.info("[DRY-RUN] Would import video for episode %s", video.source_episode_id)
            return True
        try:
            response = self.http.request(
                "POST",
                f"{self.base_url}/api/v1/internal/import/video",
                json=payload,
                headers=self._headers(),
            )
            if response.status_code != httpx.codes.OK:
                logging.error(
                    "Failed to import video for episode %s: %s", video.source_episode_id, response.text
                )
                return False
            logging.info("Imported video for episode %s", video.source_episode_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logging.exception("Error importing video for episode %s: %s", video.source_episode_id, exc)
            return False
