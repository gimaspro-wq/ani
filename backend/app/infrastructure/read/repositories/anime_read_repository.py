"""Redis-backed read repository for anime catalog and detail."""
from dataclasses import asdict
from typing import Optional

from app.infrastructure.adapters.redis_client import redis_client
from app.infrastructure.read.models.anime_catalog import AnimeCatalog, AnimeCatalogItem
from app.infrastructure.read.models.anime_detail import AnimeDetail, EpisodeItem, VideoSourceItem
from app.infrastructure.read.redis_keys import anime_catalog_key, anime_detail_key


class AnimeReadRepository:
    """Handles serialization to/from Redis for anime read models."""

    async def save_catalog(self, items: AnimeCatalog) -> None:
        payload = [asdict(item) for item in items]
        await redis_client.set_json(anime_catalog_key(), payload)

    async def get_catalog(self) -> Optional[AnimeCatalog]:
        data = await redis_client.get_json(anime_catalog_key())
        if data is None:
            return None
        return [
            AnimeCatalogItem(**item) for item in data
            if isinstance(item, dict)
        ]

    async def save_detail(self, detail: AnimeDetail) -> None:
        await redis_client.set_json(anime_detail_key(detail.slug), asdict(detail))

    async def get_detail(self, slug: str) -> Optional[AnimeDetail]:
        data = await redis_client.get_json(anime_detail_key(slug))
        if data is None:
            return None
        episodes = []
        for ep in data.get("episodes", []):
            if not isinstance(ep, dict):
                continue
            sources = []
            for vs in ep.get("video_sources", []):
                if isinstance(vs, dict):
                    sources.append(VideoSourceItem(**vs))
            episodes.append(
                EpisodeItem(
                    id=ep.get("id"),
                    number=ep.get("number"),
                    title=ep.get("title"),
                    video_sources=sources,
                )
            )
        return AnimeDetail(
            slug=data.get("slug"),
            title=data.get("title"),
            description=data.get("description"),
            year=data.get("year"),
            status=data.get("status"),
            poster=data.get("poster"),
            genres=data.get("genres", []),
            alternative_titles=data.get("alternative_titles", []),
            is_active=data.get("is_active", False),
            episodes=episodes,
            last_updated=data.get("last_updated"),
        )

    async def delete_detail(self, slug: str) -> None:
        await redis_client.delete(anime_detail_key(slug))
