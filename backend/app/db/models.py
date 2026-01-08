from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base


class LibraryStatus(str, enum.Enum):
    """Library item status enum."""
    WATCHING = "watching"
    PLANNED = "planned"
    COMPLETED = "completed"
    DROPPED = "dropped"


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    library_items = relationship("UserLibraryItem", back_populates="user", cascade="all, delete-orphan")
    progress_items = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    history_items = relationship("UserHistory", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    """Refresh token model for token rotation."""
    
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    revoked = Column(Boolean, default=False, nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="refresh_tokens")


class UserLibraryItem(Base):
    """User library item (watching, planned, completed, dropped)."""
    
    __tablename__ = "user_library_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, default="rpc", index=True)
    title_id = Column(String, nullable=False, index=True)
    status = Column(Enum(LibraryStatus), nullable=False, default=LibraryStatus.WATCHING)
    is_favorite = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationship to user
    user = relationship("User", back_populates="library_items")


class UserProgress(Base):
    """User episode watch progress."""
    
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, default="rpc", index=True)
    title_id = Column(String, nullable=False, index=True)
    episode_id = Column(String, nullable=False, index=True)
    position_seconds = Column(Float, nullable=False, default=0.0)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Relationship to user
    user = relationship("User", back_populates="progress_items")


class UserHistory(Base):
    """User watch history."""
    
    __tablename__ = "user_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, default="rpc", index=True)
    title_id = Column(String, nullable=False, index=True)
    episode_id = Column(String, nullable=False, index=True)
    position_seconds = Column(Float, nullable=True)
    watched_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Relationship to user
    user = relationship("User", back_populates="history_items")
