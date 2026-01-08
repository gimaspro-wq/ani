"""Internal API endpoints for data import (parser access only)."""
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import verify_internal_token
from app.core.utils import generate_slug
from app.db.database import get_db
from app.db.models import Anime, Episode, VideoSource, AnimeStatus
from app.schemas.anime import (
    AnimeImportSchema,
    EpisodesImportSchema,
    VideoImportSchema,
    ImportResultSchema,
    EpisodesImportResultSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(verify_internal_token)],
)


@router.post("/import/anime", response_model=ImportResultSchema)
async def import_anime(
    data: AnimeImportSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Import or update anime from parser.
    
    Protected by internal token (X-Internal-Token header).
    Creates or updates anime based on (source_name + source_id).
    Does not modify is_active if already set to False.
    """
    try:
        # Check if anime already exists
        result = await db.execute(
            select(Anime).filter(
                Anime.source_name == data.source_name,
                Anime.source_id == data.source_id
            )
        )
        anime = result.scalar_one_or_none()
        
        # Generate slug from title
        slug = generate_slug(data.title)
        
        # If slug exists for a different anime, make it unique
        if anime is None or anime.slug != slug:
            counter = 1
            original_slug = slug
            while True:
                check_result = await db.execute(
                    select(Anime).filter(Anime.slug == slug)
                )
                existing = check_result.scalar_one_or_none()
                if existing is None or (anime and existing.id == anime.id):
                    break
                slug = f"{original_slug}-{counter}"
                counter += 1
        
        if anime:
            # Update existing anime (but don't change is_active if it was manually disabled)
            logger.info(f"Updating anime: {data.title} (source: {data.source_name}/{data.source_id})")
            
            anime.title = data.title
            anime.slug = slug
            anime.description = data.description
            anime.year = data.year
            if data.status:
                anime.status = AnimeStatus(data.status)
            anime.poster = data.poster
            anime.genres = data.genres
            anime.alternative_titles = data.alternative_titles
            # Note: is_active is NOT updated - manual override preserved
            
        else:
            # Create new anime
            logger.info(f"Creating anime: {data.title} (source: {data.source_name}/{data.source_id})")
            
            anime = Anime(
                title=data.title,
                slug=slug,
                description=data.description,
                year=data.year,
                status=AnimeStatus(data.status) if data.status else None,
                poster=data.poster,
                source_name=data.source_name,
                source_id=data.source_id,
                genres=data.genres,
                alternative_titles=data.alternative_titles,
                is_active=True,
            )
            db.add(anime)
        
        await db.commit()
        await db.refresh(anime)
        
        return ImportResultSchema(
            success=True,
            message=f"Anime imported successfully: {anime.title}",
        )
        
    except Exception as e:
        logger.error(f"Error importing anime: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import anime: {str(e)}"
        )


@router.post("/import/episodes", response_model=EpisodesImportResultSchema)
async def import_episodes(
    data: EpisodesImportSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Import or update episodes for an anime.
    
    Protected by internal token (X-Internal-Token header).
    Finds anime by (source_name + anime_source_id).
    Creates or updates episodes by source_episode_id.
    Does not delete episodes not in the import.
    """
    try:
        # Find the anime
        result = await db.execute(
            select(Anime).filter(
                Anime.source_name == data.source_name,
                Anime.source_id == data.anime_source_id
            )
        )
        anime = result.scalar_one_or_none()
        
        if not anime:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anime not found: {data.source_name}/{data.anime_source_id}"
            )
        
        logger.info(f"Importing {len(data.episodes)} episodes for anime: {anime.title}")
        
        imported = 0
        errors = []
        
        for ep_data in data.episodes:
            try:
                # Check if episode already exists
                ep_result = await db.execute(
                    select(Episode).filter(
                        Episode.anime_id == anime.id,
                        Episode.source_episode_id == ep_data.source_episode_id
                    )
                )
                episode = ep_result.scalar_one_or_none()
                
                if episode:
                    # Update existing episode
                    episode.number = ep_data.number
                    episode.title = ep_data.title
                    # Set is_active based on availability (but don't override manual disable)
                    if episode.is_active or ep_data.is_available:
                        episode.is_active = ep_data.is_available
                else:
                    # Create new episode
                    episode = Episode(
                        anime_id=anime.id,
                        number=ep_data.number,
                        title=ep_data.title,
                        source_episode_id=ep_data.source_episode_id,
                        is_active=ep_data.is_available,
                    )
                    db.add(episode)
                
                imported += 1
                
            except Exception as e:
                error_msg = f"Episode {ep_data.number} (ID: {ep_data.source_episode_id}): {str(e)}"
                logger.error(f"Error importing episode: {error_msg}")
                errors.append(error_msg)
                continue
        
        await db.commit()
        
        return EpisodesImportResultSchema(
            success=len(errors) == 0,
            total=len(data.episodes),
            imported=imported,
            errors=errors,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing episodes: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import episodes: {str(e)}"
        )


@router.post("/import/video", response_model=ImportResultSchema)
async def import_video(
    data: VideoImportSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Import video source for an episode.
    
    Protected by internal token (X-Internal-Token header).
    Finds episode by (source_name + source_episode_id).
    Allows multiple video sources per episode.
    Does not delete old sources.
    """
    try:
        # Find the episode - need to join with anime to filter by source_name
        result = await db.execute(
            select(Episode)
            .join(Anime)
            .filter(
                Anime.source_name == data.source_name,
                Episode.source_episode_id == data.source_episode_id
            )
        )
        episode = result.scalar_one_or_none()
        
        if not episode:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode not found: {data.source_name}/{data.source_episode_id}"
            )
        
        # Check if this exact video source already exists (by url and source_name)
        vs_result = await db.execute(
            select(VideoSource).filter(
                VideoSource.episode_id == episode.id,
                VideoSource.url == data.player.url,
                VideoSource.source_name == data.player.source_name
            )
        )
        video_source = vs_result.scalar_one_or_none()
        
        if video_source:
            # Update existing video source
            logger.info(f"Updating video source for episode {episode.source_episode_id}")
            video_source.type = data.player.type
            video_source.priority = data.player.priority
        else:
            # Create new video source
            logger.info(f"Creating video source for episode {episode.source_episode_id}")
            video_source = VideoSource(
                episode_id=episode.id,
                type=data.player.type,
                url=data.player.url,
                source_name=data.player.source_name,
                priority=data.player.priority,
                is_active=True,
            )
            db.add(video_source)
        
        await db.commit()
        
        return ImportResultSchema(
            success=True,
            message="Video source imported successfully",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing video source: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import video source: {str(e)}"
        )
