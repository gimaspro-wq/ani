from typing import Annotated

from fastapi import APIRouter, Depends, Response, Cookie, Request

from app.application.use_cases.authentication import AuthenticationService
from app.core.config import settings, REFRESH_COOKIE_NAME
from app.core.container import get_auth_service
from app.core.rate_limiting import limiter
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    user_data: UserCreate,
    response: Response,
    auth_service: Annotated[AuthenticationService, Depends(get_auth_service)],
):
    """
    Register a new user.
    
    Returns access token in response body and sets refresh token in httpOnly cookie.
    """
    user, access_token, refresh_token = await auth_service.register(
        email=user_data.email,
        password=user_data.password,
    )
    
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
    auth_service: Annotated[AuthenticationService, Depends(get_auth_service)],
):
    """
    Login with email and password.
    
    Returns access token in response body and sets refresh token in httpOnly cookie.
    """
    user, access_token, refresh_token = await auth_service.login(
        email=login_data.email,
        password=login_data.password,
    )
    
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
    auth_service: Annotated[AuthenticationService, Depends(get_auth_service)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
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
    
    user, access_token, new_refresh_token = await auth_service.refresh(refresh_token)
    
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
    auth_service: Annotated[AuthenticationService, Depends(get_auth_service)],
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
):
    """
    Logout user by revoking refresh token and clearing cookie.
    """
    # Revoke refresh token if present
    if refresh_token:
        await auth_service.logout(refresh_token)
    
    # Clear refresh token cookie with explicit deletion
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/", samesite="lax")
    
    return MessageResponse(message="Logged out successfully")
