"""Authentication use cases."""
from typing import Optional

from app.core.errors import AuthenticationError, ConflictError
from app.domain.entities import User
from app.domain.interfaces.repositories import (
    IUserRepository,
    ISecurityService,
    IRefreshTokenService,
)


class AuthenticationService:
    """Authentication use case orchestrator."""
    
    def __init__(
        self,
        user_repo: IUserRepository,
        security_service: ISecurityService,
        refresh_token_service: IRefreshTokenService,
    ):
        self.user_repo = user_repo
        self.security = security_service
        self.refresh_tokens = refresh_token_service
    
    async def register(self, email: str, password: str) -> tuple[User, str, str]:
        """
        Register new user.
        
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            ConflictError: If email already exists
        """
        # Check if user exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ConflictError("Email already registered")
        
        # Create user
        hashed_password = self.security.hash_password(password)
        user = await self.user_repo.create(email, hashed_password)
        
        # Create tokens
        access_token = self.security.create_access_token(user.id)
        refresh_token = await self.refresh_tokens.create_refresh_token(user.id)
        
        return user, access_token, refresh_token
    
    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        """
        Authenticate user.
        
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Get user
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise AuthenticationError("Incorrect email or password")
        
        # Verify password
        if not self.security.verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        # Create tokens
        access_token = self.security.create_access_token(user.id)
        refresh_token = await self.refresh_tokens.create_refresh_token(user.id)
        
        return user, access_token, refresh_token
    
    async def refresh(self, refresh_token: str) -> tuple[User, str, str]:
        """
        Refresh access token.
        
        Returns:
            Tuple of (user, new_access_token, new_refresh_token)
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Verify refresh token
        user = await self.refresh_tokens.verify_refresh_token(refresh_token)
        if not user:
            raise AuthenticationError("Invalid or expired refresh token")
        
        # Revoke old token (rotation)
        await self.refresh_tokens.revoke_refresh_token(refresh_token)
        
        # Create new tokens
        access_token = self.security.create_access_token(user.id)
        new_refresh_token = await self.refresh_tokens.create_refresh_token(user.id)
        
        return user, access_token, new_refresh_token
    
    async def logout(self, refresh_token: Optional[str]) -> None:
        """
        Logout user.
        
        Args:
            refresh_token: Refresh token to revoke
        """
        if refresh_token:
            await self.refresh_tokens.revoke_refresh_token(refresh_token)
    
    async def get_current_user(self, access_token: str) -> User:
        """
        Get current authenticated user from access token.
        
        Returns:
            User
            
        Raises:
            AuthenticationError: If token is invalid or user not found
        """
        # Decode token
        payload = self.security.decode_access_token(access_token)
        if not payload:
            raise AuthenticationError("Could not validate credentials")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Could not validate credentials")
        
        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("Could not validate credentials")
        
        return user
