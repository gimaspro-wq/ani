"""Pydantic schemas for anime API."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Internal API Schemas (for parser import)
# ============================================================================

class AnimeImportSchema(BaseModel):
    """Schema for importing anime from parser."""
    source_name: str = Field(..., description="Source name (e.g., 'example_source')")
    source_id: str = Field(..., description="Source ID (unique within source)")
    title: str = Field(..., min_length=1, description="Anime title")
    alternative_titles: Optional[list[str]] = Field(default=None, description="Alternative titles")
    description: Optional[str] = Field(default=None, description="Anime description")
    year: Optional[int] = Field(default=None, ge=1900, le=2100, description="Release year")
    status: Optional[str] = Field(default=None, description="Anime status (ongoing, completed, upcoming)")
    poster: Optional[str] = Field(default=None, description="Poster URL")
    genres: Optional[list[str]] = Field(default=None, description="List of genres")
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status is one of allowed values."""
        if v is not None:
            allowed = ["ongoing", "completed", "upcoming"]
            if v not in allowed:
                raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v


class EpisodeImportItem(BaseModel):
    """Schema for a single episode in import."""
    source_episode_id: str = Field(..., description="Source episode ID")
    number: int = Field(..., ge=0, description="Episode number")
    title: Optional[str] = Field(default=None, description="Episode title")
    is_available: bool = Field(default=True, description="Whether episode is available")


class EpisodesImportSchema(BaseModel):
    """Schema for importing episodes from parser."""
    source_name: str = Field(..., description="Source name")
    anime_source_id: str = Field(..., description="Anime source ID")
    episodes: list[EpisodeImportItem] = Field(..., min_length=1, description="List of episodes")


class VideoPlayerSchema(BaseModel):
    """Schema for video player in import."""
    type: str = Field(..., description="Player type (e.g., 'iframe', 'direct')")
    url: str = Field(..., description="Player URL")
    source_name: str = Field(..., description="Player source name")
    priority: int = Field(default=0, description="Player priority (higher = preferred)")


class VideoImportSchema(BaseModel):
    """Schema for importing video source from parser."""
    source_name: str = Field(..., description="Source name")
    source_episode_id: str = Field(..., description="Source episode ID")
    player: VideoPlayerSchema = Field(..., description="Player information")


class ImportResultSchema(BaseModel):
    """Result of an import operation."""
    success: bool = Field(..., description="Whether import was successful")
    message: str = Field(..., description="Result message")
    errors: Optional[list[str]] = Field(default=None, description="List of errors if any")


class EpisodesImportResultSchema(BaseModel):
    """Result of episodes import operation."""
    success: bool = Field(..., description="Whether import was successful")
    total: int = Field(..., description="Total episodes processed")
    imported: int = Field(..., description="Successfully imported episodes")
    errors: list[str] = Field(default_factory=list, description="List of errors")


# ============================================================================
# Public API Schemas (for frontend)
# ============================================================================

class VideoSourcePublicSchema(BaseModel):
    """Public schema for video source (excludes internal fields)."""
    id: UUID
    type: str
    url: str
    source_name: str
    priority: int
    
    class Config:
        from_attributes = True


class EpisodePublicSchema(BaseModel):
    """Public schema for episode (excludes internal fields)."""
    id: UUID
    number: int
    title: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EpisodeWithVideoSourcesSchema(BaseModel):
    """Public schema for episode with video sources."""
    id: UUID
    number: int
    title: Optional[str]
    video_sources: list[VideoSourcePublicSchema]
    
    class Config:
        from_attributes = True


class AnimeListItemSchema(BaseModel):
    """Public schema for anime in list view."""
    id: UUID
    title: str
    slug: str
    description: Optional[str]
    year: Optional[int]
    status: Optional[str]
    poster: Optional[str]
    genres: Optional[list[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnimeDetailSchema(BaseModel):
    """Public schema for anime detail view."""
    id: UUID
    title: str
    slug: str
    description: Optional[str]
    year: Optional[int]
    status: Optional[str]
    poster: Optional[str]
    genres: Optional[list[str]]
    alternative_titles: Optional[list[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
