"""Admin panel schemas for authentication and data management."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Admin Authentication Schemas
class AdminLoginRequest(BaseModel):
    """Admin login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class AdminTokenResponse(BaseModel):
    """Admin token response schema."""
    access_token: str
    token_type: str = "bearer"


class AdminUserResponse(BaseModel):
    """Admin user response schema."""
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard Schemas
class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response."""
    total_anime: int
    active_anime: int
    inactive_anime: int
    total_episodes: int
    total_video_sources: int
    recent_anime: list[dict]
    recent_episodes: list[dict]


# Anime Management Schemas
class AnimeListItem(BaseModel):
    """Anime list item schema."""
    id: UUID
    title: str
    year: Optional[int]
    status: Optional[str]
    source_name: str
    is_active: bool
    admin_modified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnimeListResponse(BaseModel):
    """Anime list response schema."""
    items: list[AnimeListItem]
    total: int
    page: int
    per_page: int
    total_pages: int


class AnimeDetailResponse(BaseModel):
    """Anime detail response schema."""
    id: UUID
    title: str
    slug: str
    description: Optional[str]
    year: Optional[int]
    status: Optional[str]
    poster: Optional[str]
    source_name: str
    source_id: str
    genres: Optional[list[str]]
    alternative_titles: Optional[list[str]]
    is_active: bool
    admin_modified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnimeUpdateRequest(BaseModel):
    """Anime update request schema."""
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    poster: Optional[str] = None
    is_active: Optional[bool] = None


# Episode Management Schemas
class EpisodeListItem(BaseModel):
    """Episode list item schema."""
    id: UUID
    anime_id: UUID
    number: int
    title: Optional[str]
    source_episode_id: str
    is_active: bool
    admin_modified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EpisodeListResponse(BaseModel):
    """Episode list response schema."""
    items: list[EpisodeListItem]
    total: int
    anime_title: str


class EpisodeCreateRequest(BaseModel):
    """Episode create request schema."""
    anime_id: UUID
    number: int
    title: Optional[str] = None
    source_episode_id: str
    is_active: bool = True


class EpisodeUpdateRequest(BaseModel):
    """Episode update request schema."""
    number: Optional[int] = None
    title: Optional[str] = None
    is_active: Optional[bool] = None


# Video Source Management Schemas
class VideoSourceListItem(BaseModel):
    """Video source list item schema."""
    id: UUID
    episode_id: UUID
    type: str
    url: str
    source_name: str
    priority: int
    is_active: bool
    admin_modified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VideoSourceListResponse(BaseModel):
    """Video source list response schema."""
    items: list[VideoSourceListItem]
    total: int
    episode_number: int


class VideoSourceCreateRequest(BaseModel):
    """Video source create request schema."""
    episode_id: UUID
    type: str = Field(..., pattern="^(iframe|embed|m3u8|mp4)$")
    url: str
    source_name: str
    priority: int = 0
    is_active: bool = True


class VideoSourceUpdateRequest(BaseModel):
    """Video source update request schema."""
    type: Optional[str] = Field(None, pattern="^(iframe|embed|m3u8|mp4)$")
    url: Optional[str] = None
    source_name: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    """Audit log response schema."""
    id: int
    admin_id: int
    action: str
    resource_type: str
    resource_id: str
    changes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
