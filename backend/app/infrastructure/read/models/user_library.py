"""Read model for user library."""
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class UserLibraryEntry:
    title_id: str
    provider: str
    status: str
    is_favorite: bool
    updated_at: str


UserLibrary = list[UserLibraryEntry]
