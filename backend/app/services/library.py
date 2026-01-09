"""Library, progress, and history service functions."""
from datetime import datetime, timezone
from typing import List, Optional
import logging

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.db.models import (
    UserLibraryItem,
    UserProgress,
    UserHistory,
    LibraryStatus,
    normalize_library_status,
)

logger = logging.getLogger(__name__)


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
            item.status = normalize_library_status(status)
        if is_favorite is not None:
            item.is_favorite = is_favorite
        item.updated_at = datetime.now(timezone.utc)
    else:
        # Create new
        item = UserLibraryItem(
            user_id=user_id,
            provider=provider,
            title_id=title_id,
            status=normalize_library_status(status) or LibraryStatus.WATCHING.value,
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
    """
    Add entry to watch history with deduplication.
    If an entry for this episode already exists, update its watched_at timestamp.
    """
    # Check if history entry already exists for this episode
    existing = await get_history_by_episode(db, user_id, episode_id, provider)
    
    if existing:
        # Update existing entry's timestamp
        existing.watched_at = datetime.now(timezone.utc)
        existing.position_seconds = position_seconds
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        # Create new history entry
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


async def delete_history_entry(
    db: AsyncSession,
    user_id: int,
    history_id: int
) -> bool:
    """Delete a specific history entry."""
    query = select(UserHistory).where(
        and_(
            UserHistory.id == history_id,
            UserHistory.user_id == user_id
        )
    )
    result = await db.execute(query)
    history = result.scalar_one_or_none()
    
    if not history:
        return False
    
    await db.delete(history)
    await db.commit()
    return True


async def clear_user_history(
    db: AsyncSession,
    user_id: int,
    provider: str = "rpc"
) -> int:
    """Clear all history for a user. Returns number of deleted entries."""
    query = select(UserHistory).where(
        and_(
            UserHistory.user_id == user_id,
            UserHistory.provider == provider
        )
    )
    result = await db.execute(query)
    entries = result.scalars().all()
    
    count = len(entries)
    for entry in entries:
        await db.delete(entry)
    
    await db.commit()
    return count


# Deduplication helper
async def get_history_by_episode(
    db: AsyncSession,
    user_id: int,
    episode_id: str,
    provider: str = "rpc"
) -> Optional[UserHistory]:
    """Get history entry for a specific episode (for deduplication)."""
    query = select(UserHistory).where(
        and_(
            UserHistory.user_id == user_id,
            UserHistory.provider == provider,
            UserHistory.episode_id == episode_id
        )
    ).order_by(UserHistory.watched_at.desc())
    result = await db.execute(query)
    return result.scalar()


# Legacy import service
async def import_legacy_data(
    db: AsyncSession,
    user_id: int,
    progress_items: List[dict],
    saved_series: List[dict],
    provider: str = "rpc"
) -> dict:
    """
    Import legacy local data to server.
    
    Returns dict with:
    - progress_imported: number of progress items imported
    - progress_skipped: number of progress items skipped (already exists with newer data)
    - library_imported: number of library items imported
    - library_skipped: number of library items skipped (already exists with newer data)
    """
    progress_imported = 0
    progress_skipped = 0
    library_imported = 0
    library_skipped = 0
    
    # Import progress items
    for item in progress_items:
        try:
            anime_id = item.get("animeId")
            episode_number = item.get("episodeNumber")
            current_time = item.get("currentTime")
            duration = item.get("duration")
            updated_at_ms = item.get("updatedAt")
            
            if not all([anime_id, episode_number is not None, current_time is not None, duration is not None, updated_at_ms]):
                progress_skipped += 1
                continue
            
            episode_id = f"{anime_id}-ep-{episode_number}"
            
            # Check if progress already exists
            existing = await get_progress_by_episode(db, user_id, episode_id, provider)
            
            # Convert legacy timestamp (ms) to datetime
            legacy_updated_at = datetime.fromtimestamp(updated_at_ms / 1000, tz=timezone.utc)
            
            if existing:
                # Only update if legacy data is newer
                if legacy_updated_at > existing.updated_at:
                    existing.position_seconds = current_time
                    existing.duration_seconds = duration
                    existing.updated_at = legacy_updated_at
                    progress_imported += 1
                else:
                    progress_skipped += 1
            else:
                # Create new progress entry
                progress = UserProgress(
                    user_id=user_id,
                    provider=provider,
                    title_id=anime_id,
                    episode_id=episode_id,
                    position_seconds=current_time,
                    duration_seconds=duration
                )
                # Preserve the original updated_at from legacy data
                db.add(progress)
                await db.flush()  # Flush to get ID and set updated_at
                progress.updated_at = legacy_updated_at
                progress_imported += 1
                
                # Also add to history (dedupe by episode_id)
                existing_history = await get_history_by_episode(db, user_id, episode_id, provider)
                if not existing_history:
                    history = UserHistory(
                        user_id=user_id,
                        provider=provider,
                        title_id=anime_id,
                        episode_id=episode_id,
                        position_seconds=current_time
                    )
                    db.add(history)
                    await db.flush()
                    # Set watched_at to match legacy updated_at
                    history.watched_at = legacy_updated_at
        except Exception as e:
            # Log error but continue processing
            logger.error(f"Error importing progress item: {e}", exc_info=True)
            progress_skipped += 1
    
    # Import saved series as library items (with "planned" status)
    for item in saved_series:
        try:
            title_id = item.get("id")
            saved_at_ms = item.get("savedAt")
            
            if not all([title_id, saved_at_ms]):
                library_skipped += 1
                continue
            
            # Check if library item already exists
            existing = await get_library_item(db, user_id, title_id, provider)
            
            # Convert legacy timestamp (ms) to datetime
            legacy_saved_at = datetime.fromtimestamp(saved_at_ms / 1000, tz=timezone.utc)
            
            if existing:
                # Only update if legacy data is newer
                if legacy_saved_at > existing.updated_at:
                    # Keep existing status but mark as favorite
                    existing.is_favorite = True
                    existing.updated_at = legacy_saved_at
                    library_imported += 1
                else:
                    library_skipped += 1
            else:
                # Create new library item with "planned" status and favorite flag
                library_item = UserLibraryItem(
                    user_id=user_id,
                    provider=provider,
                    title_id=title_id,
                    status=LibraryStatus.PLANNED,
                    is_favorite=True
                )
                db.add(library_item)
                await db.flush()
                # Set created_at and updated_at to match legacy saved_at
                library_item.created_at = legacy_saved_at
                library_item.updated_at = legacy_saved_at
                library_imported += 1
        except Exception as e:
            # Log error but continue processing
            logger.error(f"Error importing library item: {e}", exc_info=True)
            library_skipped += 1
    
    await db.commit()
    
    return {
        "progress_imported": progress_imported,
        "progress_skipped": progress_skipped,
        "library_imported": library_imported,
        "library_skipped": library_skipped,
    }
