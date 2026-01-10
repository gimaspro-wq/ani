"""Request logging and metrics middleware."""
from __future__ import annotations

import logging
import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logging_config import get_trace_id
from app.core.observability.metrics import record_http_request

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Log requests and surface minimal metrics."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        method = request.method
        path = getattr(request.scope.get("route"), "path", request.url.path)
        response: Optional[Response] = None
        exc: Optional[Exception] = None

        try:
            response = await call_next(request)
            return response
        except Exception as error:
            exc = error
            raise
        finally:
            duration = time.perf_counter() - start_time
            status_code = response.status_code if response else 500

            record_http_request(method, path, duration)
            self._log_request(method, path, status_code, duration, exc)

    @staticmethod
    def _log_request(
        method: str,
        path: str,
        status_code: int,
        duration: float,
        exc: Optional[Exception],
    ) -> None:
        """Emit structured request log."""
        log_level = logging.ERROR if status_code >= 500 else logging.INFO
        log_kwargs = {
            "extra": {
                "extra_fields": {
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "request_id": get_trace_id(),
                    "service": settings.APP_NAME,
                }
            },
        }

        if exc and settings.DEBUG:
            log_kwargs["exc_info"] = exc

        logger.log(
            level=log_level,
            msg="Request completed" if status_code < 500 else "Request failed",
            **log_kwargs,
        )
