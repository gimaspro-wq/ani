from typing import Annotated

from fastapi import APIRouter, Depends, Response, Cookie, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings, REFRESH_COOKIE_NAME
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.core.rate_limiting import limiter
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services.auth import (
    authenticate_user,
    create_refresh_token,
    create_user,
    revoke_refresh_token,
    verify_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    user_data: UserCreate,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Register a new user.
    
    Returns access token in response body and sets refresh token in httpOnly cookie.
    """
    # Create user
    user = await create_user(db, user_data)
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = await create_refresh_token(db, user.id)
    
    # Set refresh token cookie with proper security flags
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=settings.REFRESH_TTL_DAYS * 24 * 60 * 60,
    )
    
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Login with email and password.
    
    Returns access token in response body and sets refresh token in httpOnly cookie.
    """
    # Authenticate user
    user = await authenticate_user(db, login_data.email, login_data.password)
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = await create_refresh_token(db, user.id)
    
    # Set refresh token cookie with proper security flags
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=settings.REFRESH_TTL_DAYS * 24 * 60 * 60,
    )
    
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
async def refresh(
    response: Response,
    request: Request,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token from cookie.
    
    Implements token rotation: issues new refresh token and revokes old one.
    """
    if not refresh_token:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    # Verify refresh token and get user
    user = await verify_refresh_token(db, refresh_token)
    
    # Revoke old refresh token (rotation)
    await revoke_refresh_token(db, refresh_token)
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = await create_refresh_token(db, user.id)
    
    # Set new refresh token cookie with proper security flags
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=new_refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=settings.REFRESH_TTL_DAYS * 24 * 60 * 60,
    )
    
    return TokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Logout user by revoking refresh token and clearing cookie.
    """
    # Revoke refresh token if present
    if refresh_token:
        await revoke_refresh_token(db, refresh_token)
    
    # Clear refresh token cookie with explicit deletion
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", samesite="lax")
    
    return MessageResponse(message="Logged out successfully")
