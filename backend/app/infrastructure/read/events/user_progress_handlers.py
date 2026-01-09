"""Event handlers for user progress read model.

Operational use only: invoked by rebuild workflows to populate Redis.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProgress
from app.infrastructure.read.events.event_types import UserProgressChanged
from app.infrastructure.read.models.user_progress import UserProgressEntry
from app.infrastructure.read.repositories.user_read_repository import UserReadRepository


async def rebuild_user_progress(
    session: AsyncSession,
    repo: UserReadRepository,
    user_id: int,
    provider: str,
) -> None:
    """Rebuild user progress for a provider."""
    result = await session.execute(
        select(UserProgress)
        .where(
            UserProgress.user_id == user_id,
            UserProgress.provider == provider,
        )
        .order_by(UserProgress.updated_at.desc())
    )
    items = result.scalars().all()
    progress = [
        UserProgressEntry(
            episode_id=item.episode_id,
            title_id=item.title_id,
            provider=item.provider,
            position_seconds=item.position_seconds,
            duration_seconds=item.duration_seconds,
            updated_at=item.updated_at.isoformat(),
        )
        for item in items
    ]
    await repo.save_progress(user_id, provider, progress)


async def handle_user_progress_changed(
    session: AsyncSession,
    repo: UserReadRepository,
    event: UserProgressChanged,
) -> None:
    """Handle progress change by full rebuild for the user/provider."""
    await rebuild_user_progress(session, repo, event.user_id, event.provider)
