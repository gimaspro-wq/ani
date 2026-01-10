"""Minimal Prometheus metrics for operational visibility."""
from __future__ import annotations

import time
from typing import Dict

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

_registry = CollectorRegistry()
_start_time = time.monotonic()

process_uptime_seconds = Gauge(
    "process_uptime_seconds",
    "Process uptime in seconds",
    registry=_registry,
)
process_uptime_seconds.set_function(lambda: time.monotonic() - _start_time)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ("method", "path"),
    registry=_registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration seconds",
    ("method", "path"),
    registry=_registry,
)

db_connection_errors_total = Counter(
    "db_connection_errors_total",
    "Total database connection errors",
    registry=_registry,
)

redis_connection_errors_total = Counter(
    "redis_connection_errors_total",
    "Total Redis connection errors",
    registry=_registry,
)


def record_http_request(method: str, path: str, duration_seconds: float) -> None:
    """Record metrics for a handled HTTP request."""
    labels: Dict[str, str] = {"method": method.upper(), "path": path}
    http_requests_total.labels(**labels).inc()
    http_request_duration_seconds.labels(**labels).observe(duration_seconds)


def increment_db_connection_error() -> None:
    """Increment database connection error counter."""
    db_connection_errors_total.inc()


def increment_redis_connection_error() -> None:
    """Increment Redis connection error counter."""
    redis_connection_errors_total.inc()


async def metrics_endpoint(request: Request) -> Response:
    """Expose metrics in Prometheus text format."""
    data = generate_latest(_registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
