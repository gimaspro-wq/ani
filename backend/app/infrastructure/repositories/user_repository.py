"""User repository implementation."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import User as UserModel
from app.db.rbac_models import Role, Permission
from app.domain.interfaces.repositories import IUserRepository
from app.domain.entities import User


class UserRepository(IUserRepository):
    """User repository implementation."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
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

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(UserModel).filter(UserModel.id == user_id)
        )
        return self._to_domain(result.scalar_one_or_none())
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(UserModel).filter(UserModel.email == email)
        )
        return self._to_domain(result.scalar_one_or_none())
    
    async def create(self, email: str, hashed_password: str) -> User:
        """Create new user."""
        user = UserModel(email=email, hashed_password=hashed_password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        domain_user = self._to_domain(user)
        assert domain_user is not None
        return domain_user
    
    async def check_permissions(self, user_id: int, permission_code: str) -> bool:
        """Check if user has permission."""
        # Load user with roles and permissions
        result = await self.db.execute(
            select(UserModel)
            .options(
                joinedload(UserModel.roles).joinedload(Role.permissions)
            )
            .filter(UserModel.id == user_id)
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
