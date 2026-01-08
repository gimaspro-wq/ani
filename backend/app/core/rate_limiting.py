"""Rate limiting middleware using slowapi and Redis."""
import logging
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.errors import RateLimitError

logger = logging.getLogger(__name__)


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    Uses X-Forwarded-For if behind proxy, otherwise remote address.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP in X-Forwarded-For chain
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    enabled=settings.RATE_LIMIT_ENABLED,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to handle rate limit exceptions."""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request and handle rate limit exceptions."""
        try:
            response = await call_next(request)
            return response
        except RateLimitExceeded as e:
            logger.warning(
                f"Rate limit exceeded for {get_client_identifier(request)}"
            )
            raise RateLimitError(str(e))
