"""Domain interfaces for repositories and services."""
from abc import ABC, abstractmethod
from typing import Optional, List

from app.domain.entities import User, UserLibraryItem, UserProgress, UserHistory
from app.domain.enums import LibraryStatus


class IUserRepository(ABC):
    """Interface for user repository."""
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def create(self, email: str, hashed_password: str) -> User:
        """Create new user."""
        pass
    
    @abstractmethod
    async def check_permissions(self, user_id: int, permission_code: str) -> bool:
        """Check if user has permission."""
        pass


class ILibraryRepository(ABC):
    """Interface for library repository."""
    
    @abstractmethod
    async def get_user_library(
        self,
        user_id: int,
        provider: str,
        status_filter: Optional[LibraryStatus],
        favorites_only: bool
    ) -> List[UserLibraryItem]:
        """Get user's library items."""
        pass
    
    @abstractmethod
    async def get_library_item(
        self,
        user_id: int,
        title_id: str,
        provider: str
    ) -> Optional[UserLibraryItem]:
        """Get specific library item."""
        pass
    
    @abstractmethod
    async def upsert_library_item(
        self,
        user_id: int,
        title_id: str,
        status: Optional[LibraryStatus],
        is_favorite: Optional[bool],
        provider: str
    ) -> UserLibraryItem:
        """Create or update library item."""
        pass
    
    @abstractmethod
    async def delete_library_item(
        self,
        user_id: int,
        title_id: str,
        provider: str
    ) -> bool:
        """Delete library item."""
        pass


class ISecurityService(ABC):
    """Interface for security operations."""
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        pass
    
    @abstractmethod
    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token."""
        pass
    
    @abstractmethod
    def decode_access_token(self, token: str) -> Optional[dict]:
        """Decode and verify JWT access token."""
        pass


class IRefreshTokenService(ABC):
    """Interface for refresh token operations."""
    
    @abstractmethod
    async def create_refresh_token(self, user_id: int) -> str:
        """Create refresh token."""
        pass
    
    @abstractmethod
    async def verify_refresh_token(self, token: str) -> Optional[User]:
        """Verify refresh token and return user."""
        pass
    
    @abstractmethod
    async def revoke_refresh_token(self, token: str) -> None:
        """Revoke refresh token."""
        pass
    
    @abstractmethod
    async def revoke_all_user_tokens(self, user_id: int) -> None:
        """Revoke all refresh tokens for a user."""
        pass
