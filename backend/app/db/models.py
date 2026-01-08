from datetime import datetime, timezone
import uuid
import json

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Index, event
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableList
import enum

from app.db.database import Base
# Import RBAC association table
from app.db.rbac_models import user_roles


# Custom JSON-backed array type for SQLite compatibility
class JSONEncodedList(Text):
    """JSON-encoded list column type for SQLite."""
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'sqlite':
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'sqlite':
            return json.loads(value)
        return value


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
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class AdminUser(Base):
    """Admin user model for admin panel authentication."""
    
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
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
    audit_logs = relationship("AuditLog", back_populates="admin", cascade="all, delete-orphan")


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


class AuditLog(Base):
    """Audit log for admin actions."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # e.g., "update", "create", "delete"
    resource_type = Column(String, nullable=False, index=True)  # e.g., "anime", "episode", "video_source"
    resource_id = Column(String, nullable=False, index=True)  # UUID as string
    changes = Column(Text, nullable=True)  # JSON string of changes
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Relationships
    admin = relationship("AdminUser", back_populates="audit_logs")


class AnimeStatus(str, enum.Enum):
    """Anime status enum."""
    ONGOING = "ongoing"
    COMPLETED = "completed"
    UPCOMING = "upcoming"


class Anime(Base):
    """Anime model for catalog."""
    
    __tablename__ = "anime"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False, index=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=True, index=True)
    status = Column(Enum(AnimeStatus), nullable=True, index=True)
    poster = Column(String, nullable=True)
    source_name = Column(String, nullable=False, index=True)
    source_id = Column(String, nullable=False, index=True)
    genres = Column(JSONEncodedList().with_variant(ARRAY(String), 'postgresql'), nullable=True)
    alternative_titles = Column(JSONEncodedList().with_variant(ARRAY(String), 'postgresql'), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    admin_modified = Column(Boolean, default=False, nullable=False)  # Track if admin modified this record
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
    episodes = relationship("Episode", back_populates="anime", cascade="all, delete-orphan")
    
    # Unique constraint on source_name + source_id
    __table_args__ = (
        UniqueConstraint("source_name", "source_id", name="uq_anime_source"),
        Index("idx_anime_active_title", "is_active", "title"),
    )


class Episode(Base):
    """Episode model for anime episodes."""
    
    __tablename__ = "episodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    anime_id = Column(UUID(as_uuid=True), ForeignKey("anime.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=True)
    source_episode_id = Column(String, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    admin_modified = Column(Boolean, default=False, nullable=False)  # Track if admin modified this record
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
    anime = relationship("Anime", back_populates="episodes")
    video_sources = relationship("VideoSource", back_populates="episode", cascade="all, delete-orphan")
    
    # Unique constraint on anime_id + source_episode_id
    __table_args__ = (
        UniqueConstraint("anime_id", "source_episode_id", name="uq_episode_source"),
        Index("idx_episode_anime_number", "anime_id", "number"),
    )


class VideoSource(Base):
    """Video source model for episode players."""
    
    __tablename__ = "video_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    episode_id = Column(UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)  # e.g., "iframe", "direct", etc.
    url = Column(String, nullable=False)
    source_name = Column(String, nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=0, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    admin_modified = Column(Boolean, default=False, nullable=False)  # Track if admin modified this record
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
    episode = relationship("Episode", back_populates="video_sources")
    
    __table_args__ = (
        Index("idx_video_source_episode_priority", "episode_id", "priority"),
    )

