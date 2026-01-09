"""Utility helpers for deterministic Redis key construction (string formatting only)."""


def anime_catalog_key() -> str:
    """Canonical catalog key (all anime)."""
    return "anime:catalog:all"


def anime_detail_key(slug: str) -> str:
    """Anime detail key scoped by slug."""
    return f"anime:detail:{slug}"


def user_library_key(user_id: int, provider: str) -> str:
    """User library key."""
    return f"user:{user_id}:library:{provider}"


def user_progress_key(user_id: int, provider: str) -> str:
    """User progress key."""
    return f"user:{user_id}:progress:{provider}"


def user_history_last_key(user_id: int, provider: str) -> str:
    """User last-history entry key."""
    return f"user:{user_id}:history:last:{provider}"
