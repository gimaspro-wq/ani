"""Redis client for caching and rate limiting."""
import logging
from typing import Any, Optional
import json

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper."""
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True
            )
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.aclose()
            logger.info("Redis connection closed")
        if self._pool:
            await self._pool.aclose()
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if not self._client:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in Redis with optional expiration."""
        try:
            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from Redis."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from key {key}")
        return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value in Redis."""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, expire)
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to encode JSON for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in Redis."""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCRBY error for key {key}: {e}")
            return 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        try:
            await self.client.expire(key, seconds)
            return True
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency to get Redis client."""
    return redis_client
