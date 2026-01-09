"""Read model for anime catalog (canonical full set)."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(slots=True)
class AnimeCatalogItem:
    slug: str
    title: str
    poster: Optional[str]
    year: Optional[int]
    status: Optional[str]
    genres: List[str]
    alternative_titles: List[str]
    is_active: bool
    last_updated: str


AnimeCatalog = list[AnimeCatalogItem]
