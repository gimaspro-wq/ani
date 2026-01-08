import itertools
import logging
import random
import threading
import time
from typing import Any, Dict, Optional

import httpx


class RateLimiter:
    """Simple rate limiter that enforces a minimum interval between requests."""

    def __init__(self, rate_per_second: float = 1.0) -> None:
        self.min_interval = 1.0 / rate_per_second if rate_per_second > 0 else 0
        self._lock = threading.Lock()
        self._last = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait_for = self.min_interval - (now - self._last)
            if wait_for > 0:
                time.sleep(wait_for)
            self._last = time.monotonic()


class HttpClient:
    """HTTP client with retries, backoff, user-agent rotation, and rate limiting."""

    def __init__(
        self,
        timeout: float = 15.0,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        rate_limit_per_second: float = 1.0,
        user_agents: Optional[list[str]] = None,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.rate_limiter = RateLimiter(rate_limit_per_second)
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self._ua_cycle = itertools.cycle(self.user_agents)
        self._client = httpx.Client(timeout=self.timeout, follow_redirects=True, transport=transport)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_exc: Optional[Exception] = None
        base_headers: Dict[str, str] = (kwargs.get("headers") or {}).copy()
        base_kwargs = {key: value for key, value in kwargs.items() if key != "headers"}
        for attempt in range(self.max_retries):
            self.rate_limiter.wait()
            headers: Dict[str, str] = base_headers.copy()
            headers.setdefault("User-Agent", next(self._ua_cycle))
            request_kwargs = base_kwargs.copy()
            request_kwargs["headers"] = headers
            try:
                response = self._client.request(method, url, **request_kwargs)
                if response.status_code >= 500 or response.status_code in (429,):
                    raise httpx.HTTPStatusError(
                        f"Server error {response.status_code}", request=response.request, response=response
                    )
                return response
            except (httpx.TimeoutException, httpx.HTTPError) as exc:  # noqa: PERF203
                last_exc = exc
                sleep_for = self.backoff_factor * (2**attempt) + random.uniform(0, 0.25)
                logging.warning("Request failed (%s). Retrying in %.2fs", exc, sleep_for)
                time.sleep(sleep_for)
        if last_exc:
            raise last_exc
        raise RuntimeError("Request failed without raising an exception")

    def close(self) -> None:
        self._client.close()
