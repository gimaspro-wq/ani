"""Event handlers for user last-history read model."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserHistory
from app.infrastructure.read.events.event_types import UserHistoryChanged
from app.infrastructure.read.models.user_history import UserHistoryLast
from app.infrastructure.read.repositories.user_read_repository import UserReadRepository


async def rebuild_user_history_last(
    session: AsyncSession,
    repo: UserReadRepository,
    user_id: int,
    provider: str,
) -> None:
    """Rebuild user's last history entry for a provider."""
    result = await session.execute(
        select(UserHistory)
        .where(
            UserHistory.user_id == user_id,
            UserHistory.provider == provider,
        )
        .order_by(UserHistory.watched_at.desc())
        .limit(1)
    )
    item = result.scalar_one_or_none()
    if not item:
        await repo.save_history_last(user_id, provider, None)
        return

    entry = UserHistoryLast(
        history_id=item.id,
        title_id=item.title_id,
        episode_id=item.episode_id,
        provider=item.provider,
        position_seconds=item.position_seconds,
        watched_at=item.watched_at.isoformat(),
    )
    await repo.save_history_last(user_id, provider, entry)


async def handle_user_history_changed(
    session: AsyncSession,
    repo: UserReadRepository,
    event: UserHistoryChanged,
) -> None:
    """Handle history change by rebuilding last entry cache."""
    await rebuild_user_history_last(session, repo, event.user_id, event.provider)
