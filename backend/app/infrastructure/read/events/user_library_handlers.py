"""Event handlers for user library read model.

Operational use only: invoked by rebuild workflows to populate Redis.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserLibraryItem
from app.infrastructure.read.events.event_types import UserLibraryChanged
from app.infrastructure.read.models.user_library import UserLibraryEntry
from app.infrastructure.read.repositories.user_read_repository import UserReadRepository


async def rebuild_user_library(
    session: AsyncSession,
    repo: UserReadRepository,
    user_id: int,
    provider: str,
) -> None:
    """Rebuild user library for a provider."""
    result = await session.execute(
        select(UserLibraryItem)
        .where(
            UserLibraryItem.user_id == user_id,
            UserLibraryItem.provider == provider,
        )
        .order_by(UserLibraryItem.updated_at.desc())
    )
    items = result.scalars().all()
    now_iso = datetime.now(timezone.utc).isoformat()
    library = [
        UserLibraryEntry(
            title_id=item.title_id,
            provider=item.provider,
            status=item.status,
            is_favorite=item.is_favorite,
            updated_at=item.updated_at.isoformat(),
        )
        for item in items
    ]
    await repo.save_library(user_id, provider, library)


async def handle_user_library_changed(
    session: AsyncSession,
    repo: UserReadRepository,
    event: UserLibraryChanged,
) -> None:
    """Handle library change by full rebuild for the user/provider."""
    await rebuild_user_library(session, repo, event.user_id, event.provider)
