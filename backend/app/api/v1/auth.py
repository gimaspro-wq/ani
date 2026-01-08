from typing import Annotated

from fastapi import APIRouter, Depends, Response, Cookie
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
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
    db: Annotated[Session, Depends(get_db)],
):
    """
    Register a new user.
    
    Returns access token in response body and sets refresh token in httpOnly cookie.
    """
    # Create user
    user = create_user(db, user_data)
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(db, user.id)
    
    # Set refresh token cookie (secure=False for testing, True in production)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,  # Only secure in production
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days
    )
    
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Login with email and password.
    
    Returns access token in response body and sets refresh token in httpOnly cookie.
    """
    # Authenticate user
    user = authenticate_user(db, login_data.email, login_data.password)
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(db, user.id)
    
    # Set refresh token cookie (secure=False for testing, True in production)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days
    )
    
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
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
    user = verify_refresh_token(db, refresh_token)
    
    # Revoke old refresh token
    revoke_refresh_token(db, refresh_token)
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(db, user.id)
    
    # Set new refresh token cookie (secure=False for testing, True in production)
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=30 * 24 * 60 * 60,  # 30 days
    )
    
    return TokenResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_db),
):
    """
    Logout user by revoking refresh token and clearing cookie.
    """
    # Revoke refresh token if present
    if refresh_token:
        revoke_refresh_token(db, refresh_token)
    
    # Clear refresh token cookie
    response.delete_cookie(key="refresh_token")
    
    return MessageResponse(message="Logged out successfully")
