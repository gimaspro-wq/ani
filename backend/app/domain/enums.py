"""Domain enums kept framework-agnostic."""
import enum


class LibraryStatus(str, enum.Enum):
    WATCHING = "watching"
    PLANNED = "planned"
    COMPLETED = "completed"
    DROPPED = "dropped"


__all__ = ["LibraryStatus"]
