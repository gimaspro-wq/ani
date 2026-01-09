"""Read-only anime endpoints served from Redis read models."""
from dataclasses import asdict
from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.infrastructure.read.repositories.anime_read_repository import AnimeReadRepository


router = APIRouter(prefix="/api/read/anime", tags=["read-anime"])


async def get_anime_repo() -> AnimeReadRepository:
    """Factory for anime read repository."""
    return AnimeReadRepository()


@router.get("", response_model=List[dict[str, Any]])
async def list_anime_read(
    repo: Annotated[AnimeReadRepository, Depends(get_anime_repo)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    year: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
):
    """Return canonical anime catalog from Redis, with in-API filtering/pagination."""
    catalog = await repo.get_catalog()
    if catalog is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog read model not available",
        )

    items = catalog
    if year is not None:
        items = [item for item in items if item.year == year]
    if status is not None:
        items = [item for item in items if item.status == status]
    if genre is not None:
        items = [item for item in items if genre in (item.genres or [])]

    sliced = items[skip : skip + limit]
    return [asdict(item) for item in sliced]


@router.get("/{slug}", response_model=dict[str, Any])
async def get_anime_read(
    slug: str,
    repo: Annotated[AnimeReadRepository, Depends(get_anime_repo)],
):
    """Return anime detail from Redis read model."""
    detail = await repo.get_detail(slug)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anime not found in read model",
        )
    return asdict(detail)
