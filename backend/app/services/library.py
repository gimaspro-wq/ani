"""Library, progress, and history service functions."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.db.models import UserLibraryItem, UserProgress, UserHistory, LibraryStatus


# Library services
async def get_user_library(
    db: AsyncSession,
    user_id: int,
    provider: str = "rpc",
    status_filter: Optional[LibraryStatus] = None,
    favorites_only: bool = False
) -> List[UserLibraryItem]:
    """Get user library items."""
    query = select(UserLibraryItem).where(
        and_(
            UserLibraryItem.user_id == user_id,
            UserLibraryItem.provider == provider
        )
    )
    
    if status_filter:
        query = query.where(UserLibraryItem.status == status_filter)
    
    if favorites_only:
        query = query.where(UserLibraryItem.is_favorite == True)
    
    query = query.order_by(UserLibraryItem.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


async def get_library_item(
    db: AsyncSession,
    user_id: int,
    title_id: str,
    provider: str = "rpc"
) -> Optional[UserLibraryItem]:
    """Get a specific library item."""
    query = select(UserLibraryItem).where(
        and_(
            UserLibraryItem.user_id == user_id,
            UserLibraryItem.provider == provider,
            UserLibraryItem.title_id == title_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def upsert_library_item(
    db: AsyncSession,
    user_id: int,
    title_id: str,
    status: Optional[LibraryStatus] = None,
    is_favorite: Optional[bool] = None,
    provider: str = "rpc"
) -> UserLibraryItem:
    """Create or update library item."""
    item = await get_library_item(db, user_id, title_id, provider)
    
    if item:
        # Update existing
        if status is not None:
            item.status = status
        if is_favorite is not None:
            item.is_favorite = is_favorite
        item.updated_at = datetime.now(timezone.utc)
    else:
        # Create new
        item = UserLibraryItem(
            user_id=user_id,
            provider=provider,
            title_id=title_id,
            status=status or LibraryStatus.WATCHING,
            is_favorite=is_favorite or False
        )
        db.add(item)
    
    await db.commit()
    await db.refresh(item)
    return item


async def delete_library_item(
    db: AsyncSession,
    user_id: int,
    title_id: str,
    provider: str = "rpc"
) -> bool:
    """Delete library item."""
    item = await get_library_item(db, user_id, title_id, provider)
    if not item:
        return False
    
    await db.delete(item)
    await db.commit()
    return True


# Progress services
async def get_user_progress(
    db: AsyncSession,
    user_id: int,
    provider: str = "rpc",
    title_id: Optional[str] = None
) -> List[UserProgress]:
    """Get user progress."""
    query = select(UserProgress).where(
        and_(
            UserProgress.user_id == user_id,
            UserProgress.provider == provider
        )
    )
    
    if title_id:
        query = query.where(UserProgress.title_id == title_id)
    
    query = query.order_by(UserProgress.updated_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


async def get_progress_by_episode(
    db: AsyncSession,
    user_id: int,
    episode_id: str,
    provider: str = "rpc"
) -> Optional[UserProgress]:
    """Get progress for a specific episode."""
    query = select(UserProgress).where(
        and_(
            UserProgress.user_id == user_id,
            UserProgress.provider == provider,
            UserProgress.episode_id == episode_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def upsert_progress(
    db: AsyncSession,
    user_id: int,
    episode_id: str,
    title_id: str,
    position_seconds: float,
    duration_seconds: float,
    provider: str = "rpc"
) -> UserProgress:
    """Create or update progress."""
    progress = await get_progress_by_episode(db, user_id, episode_id, provider)
    
    if progress:
        # Update existing
        progress.position_seconds = position_seconds
        progress.duration_seconds = duration_seconds
        progress.updated_at = datetime.now(timezone.utc)
    else:
        # Create new
        progress = UserProgress(
            user_id=user_id,
            provider=provider,
            title_id=title_id,
            episode_id=episode_id,
            position_seconds=position_seconds,
            duration_seconds=duration_seconds
        )
        db.add(progress)
    
    await db.commit()
    await db.refresh(progress)
    return progress


# History services
async def get_user_history(
    db: AsyncSession,
    user_id: int,
    provider: str = "rpc",
    limit: int = 50
) -> List[UserHistory]:
    """Get user watch history."""
    query = select(UserHistory).where(
        and_(
            UserHistory.user_id == user_id,
            UserHistory.provider == provider
        )
    ).order_by(UserHistory.watched_at.desc()).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def add_to_history(
    db: AsyncSession,
    user_id: int,
    title_id: str,
    episode_id: str,
    position_seconds: Optional[float] = None,
    provider: str = "rpc"
) -> UserHistory:
    """Add entry to watch history."""
    history = UserHistory(
        user_id=user_id,
        provider=provider,
        title_id=title_id,
        episode_id=episode_id,
        position_seconds=position_seconds
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history
