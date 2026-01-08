"""Library, progress, and history schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LibraryStatus(str, Enum):
    """Library item status."""
    WATCHING = "watching"
    PLANNED = "planned"
    COMPLETED = "completed"
    DROPPED = "dropped"


class LibraryItemUpdate(BaseModel):
    """Update library item request."""
    status: Optional[LibraryStatus] = None
    is_favorite: Optional[bool] = None


class LibraryItemResponse(BaseModel):
    """Library item response."""
    id: int
    user_id: int
    provider: str
    title_id: str
    status: LibraryStatus
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    """Update progress request."""
    title_id: str
    position_seconds: float = Field(ge=0)
    duration_seconds: float = Field(ge=0)


class ProgressResponse(BaseModel):
    """Progress response."""
    id: int
    user_id: int
    provider: str
    title_id: str
    episode_id: str
    position_seconds: float
    duration_seconds: float
    updated_at: datetime
    
    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    """History response."""
    id: int
    user_id: int
    provider: str
    title_id: str
    episode_id: str
    position_seconds: Optional[float]
    watched_at: datetime
    
    class Config:
        from_attributes = True


# Legacy import schemas
class LegacyProgressItem(BaseModel):
    """Legacy progress item from localStorage."""
    animeId: str
    episodeNumber: int
    currentTime: float
    duration: float
    updatedAt: int  # Unix timestamp in milliseconds
    poster: Optional[str] = None
    name: Optional[str] = None


class LegacySavedSeries(BaseModel):
    """Legacy saved series from localStorage."""
    id: str
    name: str
    poster: str
    savedAt: int  # Unix timestamp in milliseconds


class LegacyImportRequest(BaseModel):
    """Request to import legacy local data."""
    progress: list[LegacyProgressItem] = Field(default_factory=list)
    savedSeries: list[LegacySavedSeries] = Field(default_factory=list)
    provider: str = "rpc"


class LegacyImportResponse(BaseModel):
    """Response from legacy import."""
    success: bool
    progress_imported: int
    progress_skipped: int
    library_imported: int
    library_skipped: int
    message: str
