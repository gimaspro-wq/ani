"""Startup safety and metadata logging."""
from __future__ import annotations

import logging
import os
from typing import Iterable

from app.core.config import settings

logger = logging.getLogger(__name__)


def _commit_hash() -> str:
    """Return commit hash from common environment variables if available."""
    return (
        os.getenv("GIT_COMMIT")
        or os.getenv("COMMIT_SHA")
        or os.getenv("SOURCE_VERSION")
        or "unknown"
    )


def log_startup_metadata() -> None:
    """Log environment metadata at startup."""
    logger.info(
        "Startup metadata",
        extra={
            "extra_fields": {
                "environment": settings.ENV,
                "version": settings.VERSION,
                "commit": _commit_hash(),
                "service": settings.APP_NAME,
            }
        },
    )


def validate_required_env() -> None:
    """Validate required environment variables are present."""
    required_fields: Iterable[str] = (
        "DATABASE_URL",
        "SECRET_KEY",
        "INTERNAL_TOKEN",
        "REDIS_URL",
    )

    missing = [field for field in required_fields if not getattr(settings, field, None)]
    if missing:
        logger.error(
            "Missing required configuration",
            extra={"extra_fields": {"missing": missing}},
        )
        raise SystemExit("Missing required environment variables")
