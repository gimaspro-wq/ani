import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.models import RefreshToken, User
from app.schemas.auth import UserCreate


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Async database session
        user_data: User registration data
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Async database session
        email: User email
        password: User password
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If credentials are invalid
    """
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def create_refresh_token(db: AsyncSession, user_id: int) -> str:
    """
    Create a refresh token for a user.
    
    Args:
        db: Async database session
        user_id: User ID
        
    Returns:
        Refresh token string
    """
    # Generate random token
    token = secrets.token_urlsafe(32)
    token_hash = get_password_hash(token)
    
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
    db.add(db_token)
    await db.commit()
    
    return token


async def verify_refresh_token(db: AsyncSession, token: str) -> User:
    """
    Verify a refresh token and return the associated user.
    
    Args:
        db: Async database session
        token: Refresh token string
        
    Returns:
        User associated with the token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Find all non-revoked tokens with their users using a join
    result = await db.execute(
        select(RefreshToken, User)
        .join(User, RefreshToken.user_id == User.id)
        .filter(
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        )
    )
    tokens_with_users = result.all()
    
    # Check each token hash
    for db_token, user in tokens_with_users:
        if verify_password(token, db_token.token_hash):
            return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def revoke_refresh_token(db: AsyncSession, token: str) -> None:
    """
    Revoke a refresh token.
    
    Args:
        db: Async database session
        token: Refresh token string
    """
    # Find all non-revoked tokens
    result = await db.execute(select(RefreshToken).filter(RefreshToken.revoked == False))
    tokens = result.scalars().all()
    
    # Check each token hash and revoke if match
    for db_token in tokens:
        if verify_password(token, db_token.token_hash):
            db_token.revoked = True
            await db.commit()
            return


async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> None:
    """
    Revoke all refresh tokens for a user.
    
    Args:
        db: Async database session
        user_id: User ID
    """
    result = await db.execute(
        select(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.revoked = True
    await db.commit()
