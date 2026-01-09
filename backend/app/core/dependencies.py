from typing import Annotated

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.authentication import AuthenticationService
from app.core.config import settings
from app.core.container import get_auth_service
from app.core.errors import AuthenticationError
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import AdminUser
from app.domain.entities import User

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
    auth_service: Annotated[AuthenticationService, Depends(get_auth_service)],
) -> User:
    """
    Get the current authenticated user from the access token.
    
    Raises:
        HTTPException: If token is invalid or user not found.
    """
    try:
        return await auth_service.get_current_user(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AdminUser:
    """
    Get the current authenticated admin from the access token.
    
    Raises:
        HTTPException: If token is invalid or admin not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Check if this is an admin token (has 'admin' claim)
    is_admin: bool = payload.get("admin", False)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    admin_id: int | None = payload.get("sub")
    if admin_id is None:
        raise credentials_exception
    
    result = await db.execute(select(AdminUser).filter(AdminUser.id == admin_id))
    admin = result.scalar_one_or_none()
    if admin is None or not admin.is_active:
        raise credentials_exception
    
    return admin
