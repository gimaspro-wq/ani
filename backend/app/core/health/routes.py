"""Health and readiness endpoints."""
import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis import exceptions as redis_exceptions
import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.observability.metrics import (
    increment_db_connection_error,
    increment_redis_connection_error,
)
from app.db.database import engine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health() -> dict[str, str]:
    """Liveness probe – process is up."""
    return {"status": "healthy", "version": settings.VERSION}


async def _is_database_ready() -> bool:
    """Check database connectivity."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as exc:
        logger.warning("Database readiness check failed", exc_info=exc if settings.DEBUG else None)
        increment_db_connection_error()
        return False


async def _is_redis_ready() -> bool:
    """Check Redis connectivity."""
    client: redis.Redis | None = None
    try:
        client = redis.from_url(settings.REDIS_URL)
        await client.ping()
        return True
    except redis_exceptions.RedisError as exc:
        logger.warning("Redis readiness check failed", exc_info=exc if settings.DEBUG else None)
        increment_redis_connection_error()
        return False
    finally:
        if client:
            try:
                await client.aclose()
            except Exception:
                pass


@router.get("/ready")
async def ready() -> JSONResponse:
    """Readiness probe – verifies downstream dependencies."""
    db_ready = await _is_database_ready()
    redis_ready = await _is_redis_ready()

    if db_ready and redis_ready:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ready", "checks": {"database": True, "redis": True}},
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "not_ready",
            "checks": {"database": db_ready, "redis": redis_ready},
        },
    )
