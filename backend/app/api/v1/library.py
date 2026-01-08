"""Library, progress, and history endpoints."""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, LibraryStatus as DBLibraryStatus
from app.schemas.library import (
    LibraryItemUpdate,
    LibraryItemResponse,
    ProgressUpdate,
    ProgressResponse,
    HistoryResponse,
    LibraryStatus,
    LegacyImportRequest,
    LegacyImportResponse,
)
from app.schemas.auth import MessageResponse
from app.services import library as library_service


router = APIRouter(prefix="/me", tags=["user-library"])


# Library endpoints
@router.get("/library", response_model=List[LibraryItemResponse])
async def get_library(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str = Query(default="rpc"),
    status: Optional[LibraryStatus] = None,
    favorites: bool = False,
):
    """
    Get user's library items.
    
    - **provider**: Data provider (default: rpc)
    - **status**: Filter by status (watching, planned, completed, dropped)
    - **favorites**: Only return favorites
    """
    status_filter = DBLibraryStatus(status.value) if status else None
    items = await library_service.get_user_library(
        db,
        current_user.id,
        provider=provider,
        status_filter=status_filter,
        favorites_only=favorites
    )
    return items


@router.put("/library/{title_id}", response_model=LibraryItemResponse)
async def update_library_item(
    title_id: str,
    update_data: LibraryItemUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str = Query(default="rpc"),
):
    """
    Add or update a library item.
    
    - **title_id**: Title identifier
    - **provider**: Data provider (default: rpc)
    - **status**: Library status (watching, planned, completed, dropped)
    - **is_favorite**: Mark as favorite
    """
    status = DBLibraryStatus(update_data.status.value) if update_data.status else None
    item = await library_service.upsert_library_item(
        db,
        current_user.id,
        title_id,
        status=status,
        is_favorite=update_data.is_favorite,
        provider=provider
    )
    return item


@router.delete("/library/{title_id}", response_model=MessageResponse)
async def delete_library_item(
    title_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str = Query(default="rpc"),
):
    """
    Remove a library item.
    
    - **title_id**: Title identifier
    - **provider**: Data provider (default: rpc)
    """
    deleted = await library_service.delete_library_item(
        db,
        current_user.id,
        title_id,
        provider=provider
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library item not found"
        )
    return {"message": "Library item removed"}


# Progress endpoints
@router.get("/progress", response_model=List[ProgressResponse])
async def get_progress(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str = Query(default="rpc"),
    title_id: Optional[str] = None,
):
    """
    Get user's watch progress.
    
    - **provider**: Data provider (default: rpc)
    - **title_id**: Filter by title (optional)
    """
    items = await library_service.get_user_progress(
        db,
        current_user.id,
        provider=provider,
        title_id=title_id
    )
    return items


@router.put("/progress/{episode_id}", response_model=ProgressResponse)
async def update_progress(
    episode_id: str,
    progress_data: ProgressUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str = Query(default="rpc"),
):
    """
    Update episode watch progress.
    
    - **episode_id**: Episode identifier
    - **provider**: Data provider (default: rpc)
    - **title_id**: Title identifier
    - **position_seconds**: Current playback position
    - **duration_seconds**: Total episode duration
    """
    progress = await library_service.upsert_progress(
        db,
        current_user.id,
        episode_id,
        progress_data.title_id,
        progress_data.position_seconds,
        progress_data.duration_seconds,
        provider=provider
    )
    
    # Also add to history
    await library_service.add_to_history(
        db,
        current_user.id,
        progress_data.title_id,
        episode_id,
        progress_data.position_seconds,
        provider=provider
    )
    
    return progress


# History endpoints
@router.get("/history", response_model=List[HistoryResponse])
async def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str = Query(default="rpc"),
    limit: int = Query(default=50, le=100),
):
    """
    Get user's watch history.
    
    - **provider**: Data provider (default: rpc)
    - **limit**: Number of items to return (max: 100)
    """
    items = await library_service.get_user_history(
        db,
        current_user.id,
        provider=provider,
        limit=limit
    )
    return items


@router.delete("/history/{history_id}", response_model=MessageResponse)
async def delete_history_entry(
    history_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Delete a specific history entry.
    
    - **history_id**: History entry ID
    """
    deleted = await library_service.delete_history_entry(
        db,
        current_user.id,
        history_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History entry not found"
        )
    return {"message": "History entry deleted"}


@router.delete("/history", response_model=MessageResponse)
async def clear_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: str = Query(default="rpc"),
):
    """
    Clear all watch history for the user.
    
    - **provider**: Data provider (default: rpc)
    """
    count = await library_service.clear_user_history(
        db,
        current_user.id,
        provider=provider
    )
    return {"message": f"Cleared {count} history entries"}


@router.post("/import-legacy", response_model=LegacyImportResponse)
async def import_legacy_data(
    import_data: LegacyImportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Import legacy local data (progress and saved series) to server.
    
    This endpoint is idempotent - it can be called multiple times safely.
    Only imports data that is newer than existing server data.
    
    - **progress**: List of legacy progress items from localStorage
    - **savedSeries**: List of legacy saved series from localStorage
    - **provider**: Data provider (default: rpc)
    """
    # Convert Pydantic models to dicts for the service
    progress_items = [item.model_dump() for item in import_data.progress]
    saved_series = [item.model_dump() for item in import_data.savedSeries]
    
    result = await library_service.import_legacy_data(
        db,
        current_user.id,
        progress_items,
        saved_series,
        provider=import_data.provider
    )
    
    total_imported = result["progress_imported"] + result["library_imported"]
    total_skipped = result["progress_skipped"] + result["library_skipped"]
    
    return LegacyImportResponse(
        success=True,
        progress_imported=result["progress_imported"],
        progress_skipped=result["progress_skipped"],
        library_imported=result["library_imported"],
        library_skipped=result["library_skipped"],
        message=f"Imported {total_imported} items, skipped {total_skipped} items (already up-to-date)"
    )
