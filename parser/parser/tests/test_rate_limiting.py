"""Tests for rate limiting logic."""
import asyncio
import time
import pytest
from parser.utils import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basic rate limiting."""
    rate = 2.0  # 2 requests per second
    limiter = RateLimiter(rate)
    
    start_time = time.time()
    
    # Make 3 requests
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()
    
    elapsed = time.time() - start_time
    
    # Should take at least 1 second (2 requests/sec = 0.5s per request minimum)
    # 3 requests = at least 1 second (0s + 0.5s + 0.5s)
    assert elapsed >= 0.9  # Allow some margin for timing


@pytest.mark.asyncio
async def test_rate_limiter_zero_rate():
    """Test rate limiter with zero rate (unlimited)."""
    limiter = RateLimiter(0)
    
    start_time = time.time()
    
    # Make multiple requests
    for _ in range(5):
        await limiter.acquire()
    
    elapsed = time.time() - start_time
    
    # Should be nearly instant
    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_rate_limiter_high_rate():
    """Test rate limiter with high rate."""
    rate = 10.0  # 10 requests per second
    limiter = RateLimiter(rate)
    
    start_time = time.time()
    
    # Make 5 requests
    for _ in range(5):
        await limiter.acquire()
    
    elapsed = time.time() - start_time
    
    # Should take at least 0.4 seconds (5 requests * 0.1s interval)
    assert elapsed >= 0.35
    # Should not take too long
    assert elapsed < 1.0
