"""Event handlers for anime read models.

Operational use only: invoke via rebuild workflows to populate Redis; not called by request handlers.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Anime, Episode, VideoSource
from app.infrastructure.read.events.event_types import AnimeContentChanged
from app.infrastructure.read.models.anime_catalog import AnimeCatalogItem
from app.infrastructure.read.models.anime_detail import AnimeDetail, EpisodeItem, VideoSourceItem
from app.infrastructure.read.repositories.anime_read_repository import AnimeReadRepository


async def rebuild_catalog(session: AsyncSession, repo: AnimeReadRepository) -> None:
    """Rebuild canonical anime catalog."""
    result = await session.execute(
        select(Anime).where(Anime.is_active == True).order_by(Anime.title)
    )
    anime_list = result.scalars().all()
    now_iso = datetime.now(timezone.utc).isoformat()
    catalog = [
        AnimeCatalogItem(
            slug=anime.slug,
            title=anime.title,
            poster=anime.poster,
            year=anime.year,
            status=anime.status.value if anime.status else None,
            genres=anime.genres or [],
            alternative_titles=anime.alternative_titles or [],
            is_active=anime.is_active,
            last_updated=now_iso,
        )
        for anime in anime_list
    ]
    await repo.save_catalog(catalog)


async def rebuild_detail(session: AsyncSession, repo: AnimeReadRepository, slug: str) -> None:
    """Rebuild a single anime detail entry."""
    result = await session.execute(
        select(Anime)
        .where(Anime.slug == slug)
        .options(selectinload(Anime.episodes).selectinload(Episode.video_sources))
    )
    anime = result.scalars().first()
    if not anime:
        await repo.delete_detail(slug)
        return

    episodes: list[EpisodeItem] = []
    for ep in sorted(anime.episodes, key=lambda e: e.number):
        active_sources = [vs for vs in ep.video_sources if vs.is_active]
        sources = [
            VideoSourceItem(
                type=vs.type,
                url=vs.url,
                source_name=vs.source_name,
                priority=vs.priority,
                is_active=vs.is_active,
            )
            for vs in active_sources
        ]
        episodes.append(
            EpisodeItem(
                id=ep.id,
                number=ep.number,
                title=ep.title,
                video_sources=sources,
            )
        )

    detail = AnimeDetail(
        slug=anime.slug,
        title=anime.title,
        description=anime.description,
        year=anime.year,
        status=anime.status.value if anime.status else None,
        poster=anime.poster,
        genres=anime.genres or [],
        alternative_titles=anime.alternative_titles or [],
        is_active=anime.is_active,
        episodes=episodes,
        last_updated=datetime.now(timezone.utc).isoformat(),
    )
    await repo.save_detail(detail)


async def handle_anime_content_changed(
    session: AsyncSession,
    repo: AnimeReadRepository,
    event: AnimeContentChanged,
) -> None:
    """Handle AnimeContentChanged by rebuilding catalog and affected detail."""
    await rebuild_catalog(session, repo)
    await rebuild_detail(session, repo, event.slug)
