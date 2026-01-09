"""Redis-backed read repository for user library/progress/history-last."""
from dataclasses import asdict
from typing import Optional

from app.infrastructure.adapters.redis_client import redis_client
from app.infrastructure.read.models.user_library import UserLibrary, UserLibraryEntry
from app.infrastructure.read.models.user_progress import UserProgress, UserProgressEntry
from app.infrastructure.read.models.user_history import UserHistoryLast
from app.infrastructure.read.redis_keys import (
    user_history_last_key,
    user_library_key,
    user_progress_key,
)


class UserReadRepository:
    """Handles serialization to/from Redis for user-centric read models."""

    async def save_library(self, user_id: int, provider: str, items: UserLibrary) -> None:
        payload = [asdict(item) for item in items]
        await redis_client.set_json(user_library_key(user_id, provider), payload)

    async def get_library(self, user_id: int, provider: str) -> Optional[UserLibrary]:
        data = await redis_client.get_json(user_library_key(user_id, provider))
        if data is None:
            return None
        return [UserLibraryEntry(**item) for item in data if isinstance(item, dict)]

    async def save_progress(self, user_id: int, provider: str, items: UserProgress) -> None:
        payload = [asdict(item) for item in items]
        await redis_client.set_json(user_progress_key(user_id, provider), payload)

    async def get_progress(self, user_id: int, provider: str) -> Optional[UserProgress]:
        data = await redis_client.get_json(user_progress_key(user_id, provider))
        if data is None:
            return None
        return [UserProgressEntry(**item) for item in data if isinstance(item, dict)]

    async def save_history_last(self, user_id: int, provider: str, item: Optional[UserHistoryLast]) -> None:
        key = user_history_last_key(user_id, provider)
        if item is None:
            await redis_client.delete(key)
            return
        await redis_client.set_json(key, asdict(item))

    async def get_history_last(self, user_id: int, provider: str) -> Optional[UserHistoryLast]:
        data = await redis_client.get_json(user_history_last_key(user_id, provider))
        if data is None:
            return None
        return UserHistoryLast(**data)
