import asyncio
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.api.v1.admin import (
    reattach_episode,
    disable_video_source,
    update_video_source,
    list_anime,
)
from app.schemas.admin import EpisodeReattachRequest, VideoSourceUpdateRequest, VideoSourceDisableRequest
from app.db.models import Anime, Episode, VideoSource
from app.db.database import Base
from app.services.admin import create_admin_user
from tests.conftest import AsyncTestingSessionLocal, async_engine


async def _seed_anime_and_episode(suffix: str | None = None):
    suffix = suffix or ""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncTestingSessionLocal() as session:
        anime1 = Anime(
            title=f"Anime One{suffix}",
            slug=f"anime-one{suffix}",
            source_name="kodik",
            source_id=f"a1{suffix}",
            description=None,
        )
        anime2 = Anime(
            title=f"Anime Two{suffix}",
            slug=f"anime-two{suffix}",
            source_name="kodik",
            source_id=f"a2{suffix}",
            description=None,
        )
        session.add_all([anime1, anime2])
        await session.commit()
        await session.refresh(anime1)
        await session.refresh(anime2)

        episode = Episode(
            anime_id=anime1.id,
            number=1,
            title="Episode 1",
            source_episode_id="ep1",
            is_active=True,
        )
        session.add(episode)
        await session.commit()
        await session.refresh(episode)

        return str(anime1.id), str(anime2.id), str(episode.id)


async def _seed_video(episode_id: str):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncTestingSessionLocal() as session:
        video = VideoSource(
            episode_id=UUID(episode_id),
            type="m3u8",
            url="https://example.com/stream.m3u8",
            source_name="kodik",
            priority=0,
            is_active=True,
        )
        session.add(video)
        await session.commit()
        await session.refresh(video)
        return str(video.id)


async def _seed_admin():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    email = f"admin+{uuid4().hex[:6]}@example.com"
    async with AsyncTestingSessionLocal() as session:
        admin = await create_admin_user(
            session,
            email=email,
            username=email,
            password="strongpassword123",
        )
        return admin


@pytest.mark.asyncio
async def test_admin_can_reattach_and_detach_episode():
    anime1_id, anime2_id, episode_id = await _seed_anime_and_episode(suffix=uuid4().hex[:6])
    admin = await _seed_admin()

    async with AsyncTestingSessionLocal() as session:
        result = await reattach_episode(
            episode_id=UUID(episode_id),
            reattach_data=EpisodeReattachRequest(target_anime_id=UUID(anime2_id)),
            admin=admin,
            db=session,
        )
        assert result.anime_id == UUID(anime2_id)
        assert result.is_active is True

        result = await reattach_episode(
            episode_id=UUID(episode_id),
            reattach_data=EpisodeReattachRequest(detach=True),
            admin=admin,
            db=session,
        )
        assert result.is_active is False


@pytest.mark.asyncio
async def test_admin_can_disable_and_reorder_video_source():
    _, _, episode_id = await _seed_anime_and_episode(suffix=uuid4().hex[:6])
    video_id = await _seed_video(episode_id)
    admin = await _seed_admin()

    async with AsyncTestingSessionLocal() as session:
        disabled = await disable_video_source(
            video_id=UUID(video_id),
            disable_data=VideoSourceDisableRequest(),
            admin=admin,
            db=session,
        )
        assert disabled.is_active is False

        updated = await update_video_source(
            video_id=UUID(video_id),
            update_data=VideoSourceUpdateRequest(priority=5),
            admin=admin,
            db=session,
        )
        assert updated.priority == 5


@pytest.mark.asyncio
async def test_admin_list_anime_includes_source_and_visibility():
    suffix = uuid4().hex[:6]
    await _seed_anime_and_episode(suffix=suffix)
    admin = await _seed_admin()

    async with AsyncTestingSessionLocal() as session:
        response = await list_anime(
            admin=admin,
            db=session,
            page=1,
            per_page=10,
            search=f"anime-one{suffix}",
        )
        assert response.total == 1
        item = response.items[0]
        assert item.source_id == f"a1{suffix}"
        assert item.source_name == "kodik"
        assert item.is_active is True
