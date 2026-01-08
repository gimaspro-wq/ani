"""Public API endpoints for anime catalog."""
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Anime, Episode, VideoSource
from app.schemas.anime import (
    AnimeListItemSchema,
    AnimeDetailSchema,
    EpisodeWithVideoSourcesSchema,
    VideoSourcePublicSchema,
    EpisodePublicSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/anime",
    tags=["anime"],
)


@router.get("", response_model=list[AnimeListItemSchema])
async def list_anime(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    year: Optional[int] = Query(None, description="Filter by year"),
    status: Optional[str] = Query(None, description="Filter by status"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
):
    """
    Get list of active anime.
    
    Returns only anime with is_active=True.
    Excludes internal fields (source_id, etc).
    Supports pagination and filtering.
    """
    try:
        query = select(Anime).filter(Anime.is_active == True)
        
        # Apply filters
        if year:
            query = query.filter(Anime.year == year)
        if status:
            query = query.filter(Anime.status == status)
        if genre:
            # Filter by genre (case-insensitive)
            query = query.filter(Anime.genres.contains([genre]))
        
        # Order by title and apply pagination
        query = query.order_by(Anime.title).offset(skip).limit(limit)
        
        result = await db.execute(query)
        anime_list = result.scalars().all()
        
        return [AnimeListItemSchema.model_validate(anime) for anime in anime_list]
        
    except Exception as e:
        logger.error(f"Error listing anime: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve anime list"
        )


@router.get("/{slug}", response_model=AnimeDetailSchema)
async def get_anime(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get anime details by slug.
    
    Returns only if is_active=True.
    Excludes internal fields (source_id, etc).
    """
    try:
        result = await db.execute(
            select(Anime).filter(
                Anime.slug == slug,
                Anime.is_active == True
            )
        )
        anime = result.scalar_one_or_none()
        
        if not anime:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anime not found: {slug}"
            )
        
        return AnimeDetailSchema.model_validate(anime)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting anime {slug}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve anime"
        )


@router.get("/{slug}/episodes", response_model=list[EpisodeWithVideoSourcesSchema])
async def get_anime_episodes(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get episodes for an anime by slug.
    
    Returns only active episodes (is_active=True) with their video sources.
    Video sources are sorted by priority (descending - higher priority first).
    Excludes internal fields (source_episode_id, etc).
    """
    try:
        # First, get the anime
        anime_result = await db.execute(
            select(Anime).filter(
                Anime.slug == slug,
                Anime.is_active == True
            )
        )
        anime = anime_result.scalar_one_or_none()
        
        if not anime:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anime not found: {slug}"
            )
        
        # Get episodes with video sources
        episodes_result = await db.execute(
            select(Episode)
            .filter(
                Episode.anime_id == anime.id,
                Episode.is_active == True
            )
            .options(selectinload(Episode.video_sources))
            .order_by(Episode.number)
        )
        episodes = episodes_result.scalars().all()
        
        # Build response with sorted video sources
        response = []
        for episode in episodes:
            # Filter active video sources and sort by priority (descending)
            active_sources = [
                vs for vs in episode.video_sources 
                if vs.is_active
            ]
            sorted_sources = sorted(
                active_sources,
                key=lambda x: x.priority,
                reverse=True  # Higher priority first
            )
            
            response.append(
                EpisodeWithVideoSourcesSchema(
                    id=episode.id,
                    number=episode.number,
                    title=episode.title,
                    video_sources=[
                        VideoSourcePublicSchema.model_validate(vs)
                        for vs in sorted_sources
                    ]
                )
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting episodes for {slug}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve episodes"
        )
