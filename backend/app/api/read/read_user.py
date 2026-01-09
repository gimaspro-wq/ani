"""Read-only user endpoints served from Redis read models."""
from dataclasses import asdict
from typing import Annotated, Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.db.models import User
from app.infrastructure.read.repositories.user_read_repository import UserReadRepository


router = APIRouter(prefix="/api/read/me", tags=["read-user"])


async def get_user_repo() -> UserReadRepository:
    """Factory for user read repository."""
    return UserReadRepository()


@router.get("/library", response_model=List[dict[str, Any]])
async def get_my_library(
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[UserReadRepository, Depends(get_user_repo)],
):
    """Return current user's library from Redis."""
    provider = "rpc"
    library = await repo.get_library(current_user.id, provider)
    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Library read model not available",
        )
    return [asdict(item) for item in library]


@router.get("/progress", response_model=List[dict[str, Any]])
async def get_my_progress(
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[UserReadRepository, Depends(get_user_repo)],
):
    """Return current user's progress from Redis."""
    provider = "rpc"
    progress = await repo.get_progress(current_user.id, provider)
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress read model not available",
        )
    return [asdict(item) for item in progress]


@router.get("/history/last", response_model=dict[str, Any])
async def get_my_history_last(
    current_user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[UserReadRepository, Depends(get_user_repo)],
):
    """Return current user's last history entry from Redis."""
    provider = "rpc"
    history = await repo.get_history_last(current_user.id, provider)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History read model not available",
        )
    return asdict(history)
