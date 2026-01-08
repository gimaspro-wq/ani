"""Admin service for authentication and admin operations."""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AdminUser, AuditLog, Anime, Episode, VideoSource

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_admin(db: AsyncSession, email: str, password: str) -> AdminUser:
    """
    Authenticate an admin user.
    
    Args:
        db: Database session
        email: Admin email
        password: Admin password
        
    Returns:
        AdminUser: Authenticated admin user
        
    Raises:
        HTTPException: If authentication fails
    """
    result = await db.execute(
        select(AdminUser).filter(AdminUser.email == email)
    )
    admin = result.scalar_one_or_none()
    
    if not admin or not verify_password(password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive"
        )
    
    return admin


async def create_admin_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str
) -> AdminUser:
    """
    Create a new admin user.
    
    Args:
        db: Database session
        email: Admin email
        username: Admin username
        password: Admin password
        
    Returns:
        AdminUser: Created admin user
        
    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    result = await db.execute(
        select(AdminUser).filter(AdminUser.email == email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    result = await db.execute(
        select(AdminUser).filter(AdminUser.username == username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create admin user
    admin = AdminUser(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        is_active=True
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    
    logger.info(f"Created admin user: {email}")
    
    return admin


async def log_admin_action(
    db: AsyncSession,
    admin_id: int,
    action: str,
    resource_type: str,
    resource_id: str,
    changes: Optional[dict] = None
) -> None:
    """
    Log an admin action to audit log.
    
    Args:
        db: Database session
        admin_id: Admin user ID
        action: Action performed (e.g., "update", "create", "delete")
        resource_type: Type of resource (e.g., "anime", "episode", "video_source")
        resource_id: ID of the resource
        changes: Optional dict of changes made
    """
    audit_log = AuditLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        changes=json.dumps(changes) if changes else None
    )
    db.add(audit_log)
    await db.commit()
    
    logger.info(
        f"Admin action logged: admin={admin_id}, action={action}, "
        f"resource={resource_type}/{resource_id}"
    )


async def get_dashboard_stats(db: AsyncSession) -> dict:
    """
    Get dashboard statistics.
    
    Args:
        db: Database session
        
    Returns:
        dict: Dashboard statistics
    """
    # Total anime count
    total_anime_result = await db.execute(select(func.count()).select_from(Anime))
    total_anime = total_anime_result.scalar()
    
    # Active anime count
    active_anime_result = await db.execute(
        select(func.count()).select_from(Anime).filter(Anime.is_active == True)
    )
    active_anime = active_anime_result.scalar()
    
    # Inactive anime count
    inactive_anime = total_anime - active_anime
    
    # Total episodes count
    total_episodes_result = await db.execute(select(func.count()).select_from(Episode))
    total_episodes = total_episodes_result.scalar()
    
    # Total video sources count
    total_video_sources_result = await db.execute(select(func.count()).select_from(VideoSource))
    total_video_sources = total_video_sources_result.scalar()
    
    # Recent anime (last 5)
    recent_anime_result = await db.execute(
        select(Anime)
        .order_by(Anime.created_at.desc())
        .limit(5)
    )
    recent_anime = recent_anime_result.scalars().all()
    
    # Recent episodes (last 5)
    recent_episodes_result = await db.execute(
        select(Episode)
        .order_by(Episode.created_at.desc())
        .limit(5)
    )
    recent_episodes = recent_episodes_result.scalars().all()
    
    return {
        "total_anime": total_anime,
        "active_anime": active_anime,
        "inactive_anime": inactive_anime,
        "total_episodes": total_episodes,
        "total_video_sources": total_video_sources,
        "recent_anime": [
            {
                "id": str(anime.id),
                "title": anime.title,
                "created_at": anime.created_at.isoformat()
            }
            for anime in recent_anime
        ],
        "recent_episodes": [
            {
                "id": str(episode.id),
                "anime_id": str(episode.anime_id),
                "number": episode.number,
                "created_at": episode.created_at.isoformat()
            }
            for episode in recent_episodes
        ]
    }
