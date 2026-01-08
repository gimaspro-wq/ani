from dataclasses import asdict
from typing import List

from .models import Anime, Episode, VideoSource


def anime_payload(anime: Anime) -> dict:
    """Convert Anime dataclass into backend payload."""
    payload = asdict(anime)
    # Ensure optional lists are not empty lists for nullable fields
    if not payload.get("alternative_titles"):
        payload["alternative_titles"] = []
    if not payload.get("genres"):
        payload["genres"] = []
    return payload


def episodes_payload(source_name: str, anime_source_id: str, episodes: List[Episode]) -> dict:
    """Convert Episode list into backend payload."""
    return {
        "source_name": source_name,
        "anime_source_id": anime_source_id,
        "episodes": [asdict(ep) for ep in episodes],
    }


def video_payload(video: VideoSource) -> dict:
    """Convert VideoSource dataclass into backend payload."""
    payload = asdict(video)
    payload["player"] = payload.get("player", {})
    return payload
