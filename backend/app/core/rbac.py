"""RBAC permission checking utilities."""
import logging
from functools import wraps
from typing import Callable, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.errors import AuthorizationError
from app.db.models import User
from app.db.rbac_models import Permission, Role

logger = logging.getLogger(__name__)


async def check_permission(
    user: User,
    permission_code: str,
    db: AsyncSession
) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        user: User to check
        permission_code: Permission code (e.g., 'library:read')
        db: Database session
        
    Returns:
        True if user has permission, False otherwise
    """
    # Load user with roles and permissions
    result = await db.execute(
        select(User)
        .options(
            joinedload(User.roles).joinedload(Role.permissions)
        )
        .filter(User.id == user.id)
    )
    user_with_roles = result.unique().scalar_one_or_none()
    
    if not user_with_roles:
        return False
    
    # Check if user has the permission through any role
    for role in user_with_roles.roles:
        if not role.is_active:
            continue
        for permission in role.permissions:
            if permission.is_active and permission.code == permission_code:
                logger.debug(
                    f"User {user.id} has permission {permission_code} "
                    f"through role {role.code}"
                )
                return True
    
    logger.debug(f"User {user.id} does not have permission {permission_code}")
    return False


async def require_permission_check(
    user: User,
    permission_code: str,
    db: AsyncSession
) -> None:
    """
    Require user to have specific permission.
    
    Raises:
        AuthorizationError: If user doesn't have permission
    """
    has_permission = await check_permission(user, permission_code, db)
    if not has_permission:
        raise AuthorizationError(
            f"Permission required: {permission_code}"
        )


def require_permission(permission_code: str) -> Callable:
    """
    Decorator to require permission for endpoint.
    
    Usage:
        @router.get("/protected")
        @require_permission("library:read")
        async def protected_endpoint(user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract user and db from kwargs
            user = kwargs.get("current_user") or kwargs.get("user")
            db = kwargs.get("db")
            
            if not user:
                raise AuthorizationError("User not authenticated")
            if not db:
                raise RuntimeError("Database session not available")
            
            # Check permission
            await require_permission_check(user, permission_code, db)
            
            # Call original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
