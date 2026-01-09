"""Refresh token service implementation."""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import RefreshToken, User as UserModel
from app.domain.entities import User
from app.domain.interfaces.repositories import IRefreshTokenService, ISecurityService


class RefreshTokenService(IRefreshTokenService):
    """Refresh token service implementation."""
    
    def __init__(self, db: AsyncSession, security_service: ISecurityService):
        self.db = db
        self.security = security_service

    @staticmethod
    def _to_domain(user: UserModel | None) -> Optional[User]:
        if not user:
            return None
        return User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
            created_at=user.created_at,
        )
    
    async def create_refresh_token(self, user_id: int) -> str:
        """Create refresh token."""
        # Generate random token
        token = secrets.token_urlsafe(32)
        token_hash = self.security.hash_password(token)
        
        # Calculate expiration
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TTL_DAYS
        )
        
        # Store in database
        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(db_token)
        await self.db.commit()
        
        return token
    
    async def verify_refresh_token(self, token: str) -> Optional[User]:
        """Verify refresh token and return user."""
        # Find all non-revoked tokens with their users using a join
        result = await self.db.execute(
            select(RefreshToken, UserModel)
            .join(UserModel, RefreshToken.user_id == UserModel.id)
            .filter(
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        tokens_with_users = result.all()
        
        # Check each token hash
        for db_token, user in tokens_with_users:
            if self.security.verify_password(token, db_token.token_hash):
                return self._to_domain(user)
        
        return None
    
    async def revoke_refresh_token(self, token: str) -> None:
        """Revoke refresh token."""
        # Find all non-revoked tokens
        result = await self.db.execute(
            select(RefreshToken).filter(RefreshToken.revoked == False)
        )
        tokens = result.scalars().all()
        
        # Check each token hash and revoke if match
        for db_token in tokens:
            if self.security.verify_password(token, db_token.token_hash):
                db_token.revoked = True
                await self.db.commit()
                return
    
    async def revoke_all_user_tokens(self, user_id: int) -> None:
        """Revoke all refresh tokens for a user."""
        result = await self.db.execute(
            select(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
        await self.db.commit()
