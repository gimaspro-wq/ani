"""Dependency injection container for services and repositories."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.authentication import AuthenticationService
from app.db.database import get_db
from app.infrastructure.adapters.refresh_token_service import RefreshTokenService
from app.infrastructure.adapters.security_service import security_service
from app.infrastructure.repositories.library_repository import LibraryRepository
from app.infrastructure.repositories.user_repository import UserRepository


# Repository factories
def get_user_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    """Get user repository."""
    return UserRepository(db)


def get_library_repository(db: Annotated[AsyncSession, Depends(get_db)]) -> LibraryRepository:
    """Get library repository."""
    return LibraryRepository(db)


def get_refresh_token_service(db: Annotated[AsyncSession, Depends(get_db)]) -> RefreshTokenService:
    """Get refresh token service."""
    return RefreshTokenService(db, security_service)


# Use case factories
def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_token_service: Annotated[RefreshTokenService, Depends(get_refresh_token_service)],
) -> AuthenticationService:
    """Get authentication service."""
    return AuthenticationService(
        user_repo=user_repo,
        security_service=security_service,
        refresh_token_service=refresh_token_service,
    )
