"""User repository implementation."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import User
from app.db.rbac_models import Role, Permission
from app.domain.interfaces.repositories import IUserRepository


class UserRepository(IUserRepository):
    """User repository implementation."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).filter(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).filter(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def create(self, email: str, hashed_password: str) -> User:
        """Create new user."""
        user = User(email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def check_permissions(self, user_id: int, permission_code: str) -> bool:
        """Check if user has permission."""
        # Load user with roles and permissions
        result = await self.db.execute(
            select(User)
            .options(
                joinedload(User.roles).joinedload(Role.permissions)
            )
            .filter(User.id == user_id)
        )
        user = result.unique().scalar_one_or_none()
        
        if not user:
            return False
        
        # Check if user has the permission through any role
        for role in user.roles:
            if not role.is_active:
                continue
            for permission in role.permissions:
                if permission.is_active and permission.code == permission_code:
                    return True
        
        return False
