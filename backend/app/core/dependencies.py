from typing import Annotated

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User

security = HTTPBearer()


async def verify_internal_token(x_internal_token: str = Header(...)) -> None:
    """
    Verify the internal API token.
    
    Args:
        x_internal_token: The internal token from X-Internal-Token header
        
    Raises:
        HTTPException: If token is invalid
    """
    if x_internal_token != settings.INTERNAL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid internal token"
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get the current authenticated user from the access token.
    
    Raises:
        HTTPException: If token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    
    return user
