"""Tests for backoff and retry logic."""
import pytest
import httpx
import respx
from parser.clients import HTTPClient
from parser.utils import exponential_backoff_with_jitter, RateLimiter


def test_exponential_backoff_calculation():
    """Test exponential backoff calculation."""
    base = 1.0
    max_delay = 60.0
    
    # First attempt (0) should be between 0 and base
    delay_0 = exponential_backoff_with_jitter(0, base, max_delay)
    assert 0 <= delay_0 <= base
    
    # Second attempt (1) should be between 0 and 2*base
    delay_1 = exponential_backoff_with_jitter(1, base, max_delay)
    assert 0 <= delay_1 <= 2 * base
    
    # Third attempt (2) should be between 0 and 4*base
    delay_2 = exponential_backoff_with_jitter(2, base, max_delay)
    assert 0 <= delay_2 <= 4 * base
    
    # High attempt should not exceed max
    delay_high = exponential_backoff_with_jitter(10, base, max_delay)
    assert 0 <= delay_high <= max_delay


def test_backoff_respects_max():
    """Test that backoff respects maximum delay."""
    base = 1.0
    max_delay = 10.0
    
    # Even with high attempt number, should not exceed max
    for attempt in range(20):
        delay = exponential_backoff_with_jitter(attempt, base, max_delay)
        assert delay <= max_delay


@pytest.mark.asyncio
@respx.mock
async def test_http_client_retry_on_500(respx_mock):
    """Test HTTP client retries on 500 error."""
    # Mock endpoint that returns 500 twice, then succeeds
    route = respx_mock.get("http://test.com/api/test")
    route.side_effect = [
        httpx.Response(500, json={"error": "server error"}),
        httpx.Response(500, json={"error": "server error"}),
        httpx.Response(200, json={"success": True}),
    ]
    
    client = HTTPClient("http://test.com")
    
    try:
        # Should retry and eventually succeed
        response = await client.get("/api/test")
        assert response.status_code == 200
        assert response.json() == {"success": True}
        
        # Should have made 3 attempts
        assert route.call_count == 3
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_http_client_retry_on_429(respx_mock):
    """Test HTTP client retries on 429 rate limit."""
    # Mock endpoint that returns 429 once, then succeeds
    route = respx_mock.get("http://test.com/api/test")
    route.side_effect = [
        httpx.Response(429, json={"error": "rate limit"}),
        httpx.Response(200, json={"success": True}),
    ]
    
    client = HTTPClient("http://test.com")
    
    try:
        response = await client.get("/api/test")
        assert response.status_code == 200
        
        # Should have made 2 attempts (1 retry)
        assert route.call_count == 2
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_http_client_no_retry_on_404(respx_mock):
    """Test HTTP client does NOT retry on 404."""
    route = respx_mock.get("http://test.com/api/test")
    route.return_value = httpx.Response(404, json={"error": "not found"})
    
    client = HTTPClient("http://test.com")
    
    try:
        # Should fail immediately without retrying
        with pytest.raises(httpx.HTTPStatusError):
            await client.get("/api/test")
        
        # Should have made only 1 attempt (no retries)
        assert route.call_count == 1
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_http_client_timeout_retry(respx_mock):
    """Test HTTP client retries on timeout."""
    route = respx_mock.get("http://test.com/api/test")
    route.side_effect = [
        httpx.TimeoutException("Request timeout"),
        httpx.Response(200, json={"success": True}),
    ]
    
    client = HTTPClient("http://test.com")
    
    try:
        # Should retry after timeout and succeed
        response = await client.get("/api/test")
        assert response.status_code == 200
        
        # Should have made 2 attempts
        assert route.call_count == 2
    finally:
        await client.close()
