from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.db.models import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current user information.
    
    Requires Bearer access token in Authorization header.
    """
    return current_user
