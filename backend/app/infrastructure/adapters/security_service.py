"""Security service implementation."""
from typing import Any, Optional

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.domain.interfaces.repositories import ISecurityService


class SecurityService(ISecurityService):
    """Security service implementation."""
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return get_password_hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return verify_password(plain_password, hashed_password)
    
    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token."""
        return create_access_token(data={"sub": user_id})
    
    def decode_access_token(self, token: str) -> Optional[dict[str, Any]]:
        """Decode and verify JWT access token."""
        return decode_access_token(token)


# Global instance
security_service = SecurityService()
