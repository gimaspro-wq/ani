"""Admin API endpoints for admin panel."""
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_admin, get_db
from app.core.security import create_access_token
from app.db.models import AdminUser, Anime, Episode, VideoSource, AnimeStatus
from app.schemas.admin import (
    AdminLoginRequest,
    AdminTokenResponse,
    AdminUserResponse,
    DashboardStatsResponse,
    AnimeListResponse,
    AnimeListItem,
    AnimeDetailResponse,
    AnimeUpdateRequest,
    EpisodeListResponse,
    EpisodeListItem,
    EpisodeCreateRequest,
    EpisodeUpdateRequest,
    VideoSourceListResponse,
    VideoSourceListItem,
    VideoSourceCreateRequest,
    VideoSourceUpdateRequest,
)
from app.services.admin import authenticate_admin, log_admin_action, get_dashboard_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(
    login_data: AdminLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Admin login endpoint.
    
    Returns JWT access token with admin claim.
    """
    admin = await authenticate_admin(db, login_data.email, login_data.password)
    
    # Create access token with admin claim
    access_token = create_access_token(
        data={"sub": admin.id, "admin": True, "email": admin.email}
    )
    
    logger.info(f"Admin logged in: {admin.email}")
    
    return AdminTokenResponse(access_token=access_token)


@router.get("/me", response_model=AdminUserResponse)
async def get_current_admin_user(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
):
    """Get current admin user information."""
    return admin


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get dashboard statistics."""
    stats = await get_dashboard_stats(db)
    return stats


# Anime Management Endpoints
@router.get("/anime", response_model=AnimeListResponse)
async def list_anime(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    source_name: Optional[str] = None,
):
    """
    List anime with filters and pagination.
    """
    query = select(Anime)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Anime.title.ilike(f"%{search}%"),
                Anime.slug.ilike(f"%{search}%")
            )
        )
    
    if is_active is not None:
        query = query.filter(Anime.is_active == is_active)
    
    if source_name:
        query = query.filter(Anime.source_name == source_name)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    query = query.order_by(Anime.updated_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Execute query
    result = await db.execute(query)
    anime_list = result.scalars().all()
    
    return AnimeListResponse(
        items=[AnimeListItem.model_validate(anime) for anime in anime_list],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )


@router.get("/anime/{anime_id}", response_model=AnimeDetailResponse)
async def get_anime(
    anime_id: UUID,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get anime details by ID."""
    result = await db.execute(
        select(Anime).filter(Anime.id == anime_id)
    )
    anime = result.scalar_one_or_none()
    
    if not anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found"
        )
    
    return AnimeDetailResponse.model_validate(anime)


@router.patch("/anime/{anime_id}", response_model=AnimeDetailResponse)
async def update_anime(
    anime_id: UUID,
    update_data: AnimeUpdateRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update anime details."""
    result = await db.execute(
        select(Anime).filter(Anime.id == anime_id)
    )
    anime = result.scalar_one_or_none()
    
    if not anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found"
        )
    
    # Track changes
    changes = {}
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        old_value = getattr(anime, field)
        if old_value != value:
            changes[field] = {"old": str(old_value), "new": str(value)}
            setattr(anime, field, value)
    
    # Mark as admin modified
    if changes:
        anime.admin_modified = True
        
        await db.commit()
        await db.refresh(anime)
        
        # Log the action
        await log_admin_action(
            db=db,
            admin_id=admin.id,
            action="update",
            resource_type="anime",
            resource_id=str(anime_id),
            changes=changes
        )
        
        logger.info(f"Admin {admin.email} updated anime {anime_id}: {changes}")
    
    return AnimeDetailResponse.model_validate(anime)


# Episode Management Endpoints
@router.get("/anime/{anime_id}/episodes", response_model=EpisodeListResponse)
async def list_episodes(
    anime_id: UUID,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List episodes for an anime."""
    # Check if anime exists
    anime_result = await db.execute(
        select(Anime).filter(Anime.id == anime_id)
    )
    anime = anime_result.scalar_one_or_none()
    
    if not anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found"
        )
    
    # Get episodes
    result = await db.execute(
        select(Episode)
        .filter(Episode.anime_id == anime_id)
        .order_by(Episode.number)
    )
    episodes = result.scalars().all()
    
    return EpisodeListResponse(
        items=[EpisodeListItem.model_validate(ep) for ep in episodes],
        total=len(episodes),
        anime_title=anime.title
    )


@router.post("/episodes", response_model=EpisodeListItem, status_code=status.HTTP_201_CREATED)
async def create_episode(
    episode_data: EpisodeCreateRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new episode manually."""
    # Check if anime exists
    anime_result = await db.execute(
        select(Anime).filter(Anime.id == episode_data.anime_id)
    )
    anime = anime_result.scalar_one_or_none()
    
    if not anime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found"
        )
    
    # Create episode
    episode = Episode(
        anime_id=episode_data.anime_id,
        number=episode_data.number,
        title=episode_data.title,
        source_episode_id=episode_data.source_episode_id,
        is_active=episode_data.is_active,
        admin_modified=True
    )
    
    db.add(episode)
    await db.commit()
    await db.refresh(episode)
    
    # Log the action
    await log_admin_action(
        db=db,
        admin_id=admin.id,
        action="create",
        resource_type="episode",
        resource_id=str(episode.id),
        changes={"anime_id": str(episode_data.anime_id), "number": episode_data.number}
    )
    
    logger.info(f"Admin {admin.email} created episode {episode.id}")
    
    return EpisodeListItem.model_validate(episode)


@router.patch("/episodes/{episode_id}", response_model=EpisodeListItem)
async def update_episode(
    episode_id: UUID,
    update_data: EpisodeUpdateRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update episode details."""
    result = await db.execute(
        select(Episode).filter(Episode.id == episode_id)
    )
    episode = result.scalar_one_or_none()
    
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    # Track changes
    changes = {}
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        old_value = getattr(episode, field)
        if old_value != value:
            changes[field] = {"old": str(old_value), "new": str(value)}
            setattr(episode, field, value)
    
    # Mark as admin modified
    if changes:
        episode.admin_modified = True
        
        await db.commit()
        await db.refresh(episode)
        
        # Log the action
        await log_admin_action(
            db=db,
            admin_id=admin.id,
            action="update",
            resource_type="episode",
            resource_id=str(episode_id),
            changes=changes
        )
        
        logger.info(f"Admin {admin.email} updated episode {episode_id}: {changes}")
    
    return EpisodeListItem.model_validate(episode)


# Video Source Management Endpoints
@router.get("/episodes/{episode_id}/video", response_model=VideoSourceListResponse)
async def list_video_sources(
    episode_id: UUID,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List video sources for an episode."""
    # Check if episode exists
    episode_result = await db.execute(
        select(Episode).filter(Episode.id == episode_id)
    )
    episode = episode_result.scalar_one_or_none()
    
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    # Get video sources
    result = await db.execute(
        select(VideoSource)
        .filter(VideoSource.episode_id == episode_id)
        .order_by(VideoSource.priority.desc())
    )
    video_sources = result.scalars().all()
    
    return VideoSourceListResponse(
        items=[VideoSourceListItem.model_validate(vs) for vs in video_sources],
        total=len(video_sources),
        episode_number=episode.number
    )


@router.post("/video", response_model=VideoSourceListItem, status_code=status.HTTP_201_CREATED)
async def create_video_source(
    video_data: VideoSourceCreateRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new video source manually."""
    # Check if episode exists
    episode_result = await db.execute(
        select(Episode).filter(Episode.id == video_data.episode_id)
    )
    episode = episode_result.scalar_one_or_none()
    
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found"
        )
    
    # Create video source
    video_source = VideoSource(
        episode_id=video_data.episode_id,
        type=video_data.type,
        url=video_data.url,
        source_name=video_data.source_name,
        priority=video_data.priority,
        is_active=video_data.is_active,
        admin_modified=True
    )
    
    db.add(video_source)
    await db.commit()
    await db.refresh(video_source)
    
    # Log the action
    await log_admin_action(
        db=db,
        admin_id=admin.id,
        action="create",
        resource_type="video_source",
        resource_id=str(video_source.id),
        changes={"episode_id": str(video_data.episode_id), "url": video_data.url}
    )
    
    logger.info(f"Admin {admin.email} created video source {video_source.id}")
    
    return VideoSourceListItem.model_validate(video_source)


@router.patch("/video/{video_id}", response_model=VideoSourceListItem)
async def update_video_source(
    video_id: UUID,
    update_data: VideoSourceUpdateRequest,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update video source details."""
    result = await db.execute(
        select(VideoSource).filter(VideoSource.id == video_id)
    )
    video_source = result.scalar_one_or_none()
    
    if not video_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video source not found"
        )
    
    # Track changes
    changes = {}
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        old_value = getattr(video_source, field)
        if old_value != value:
            changes[field] = {"old": str(old_value), "new": str(value)}
            setattr(video_source, field, value)
    
    # Mark as admin modified
    if changes:
        video_source.admin_modified = True
        
        await db.commit()
        await db.refresh(video_source)
        
        # Log the action
        await log_admin_action(
            db=db,
            admin_id=admin.id,
            action="update",
            resource_type="video_source",
            resource_id=str(video_id),
            changes=changes
        )
        
        logger.info(f"Admin {admin.email} updated video source {video_id}: {changes}")
    
    return VideoSourceListItem.model_validate(video_source)


@router.delete("/video/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video_source(
    video_id: UUID,
    admin: Annotated[AdminUser, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a video source."""
    result = await db.execute(
        select(VideoSource).filter(VideoSource.id == video_id)
    )
    video_source = result.scalar_one_or_none()
    
    if not video_source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video source not found"
        )
    
    # Log the action before deletion
    await log_admin_action(
        db=db,
        admin_id=admin.id,
        action="delete",
        resource_type="video_source",
        resource_id=str(video_id),
        changes={"url": video_source.url, "source_name": video_source.source_name}
    )
    
    await db.delete(video_source)
    await db.commit()
    
    logger.info(f"Admin {admin.email} deleted video source {video_id}")
    
    return None
