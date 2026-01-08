"""Base HTTP client with retry logic and rate limiting."""
import asyncio
import logging
from typing import Any, Optional, Dict
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from parser.config import settings
from parser.utils import RateLimiter

logger = logging.getLogger(__name__)


class HTTPClient:
    """Base HTTP client with rate limiting and retry logic."""
    
    def __init__(self, base_url: str, rate_limiter: Optional[RateLimiter] = None):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL for API requests
            rate_limiter: Optional rate limiter instance
        """
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter
        self.client = httpx.AsyncClient(
            timeout=settings.HTTP_TIMEOUT_SECONDS,
            follow_redirects=True,
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    def _should_retry(self, exc: Exception) -> bool:
        """
        Determine if request should be retried based on exception.
        
        Args:
            exc: The exception that occurred
            
        Returns:
            True if request should be retried
        """
        if isinstance(exc, httpx.HTTPStatusError):
            # Retry on 429 (rate limit), 5xx (server errors)
            return exc.response.status_code == 429 or exc.response.status_code >= 500
        
        # Retry on timeout and connection errors
        return isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError))
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with rate limiting and retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (relative to base_url)
            **kwargs: Additional arguments for httpx.request
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPStatusError: For non-retryable HTTP errors
            httpx.RequestError: For request errors after retries exhausted
        """
        url = f"{self.base_url}{path}"
        
        # Apply rate limiting
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        # Define retry decorator with custom retry condition
        def should_retry_exception(retry_state):
            """Check if exception should trigger retry."""
            exc = retry_state.outcome.exception()
            if exc is None:
                return False
            return self._should_retry(exc)
        
        @retry(
            stop=stop_after_attempt(settings.MAX_RETRIES + 1),
            wait=wait_exponential(
                multiplier=settings.BACKOFF_BASE_SECONDS,
                max=settings.BACKOFF_MAX_SECONDS,
            ),
            retry=should_retry_exception,
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        async def _do_request():
            try:
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if not self._should_retry(e):
                    raise
                logger.warning(
                    f"HTTP {e.response.status_code} error for {method} {url}, will retry"
                )
                raise
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                logger.warning(f"Request error for {method} {url}: {e}, will retry")
                raise
        
        return await _do_request()
    
    async def get(self, path: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        return await self._request("GET", path, **kwargs)
    
    async def post(self, path: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        return await self._request("POST", path, **kwargs)
    
    async def put(self, path: str, **kwargs) -> httpx.Response:
        """Make PUT request."""
        return await self._request("PUT", path, **kwargs)
    
    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """Make DELETE request."""
        return await self._request("DELETE", path, **kwargs)
