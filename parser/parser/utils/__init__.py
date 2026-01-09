"""Utility functions for the parser."""
import asyncio
import random
import time
from typing import Optional


def generate_source_id(shikimori_id: int) -> str:
    """
    Generate deterministic source_id from Shikimori ID.
    
    Args:
        shikimori_id: The Shikimori anime ID
        
    Returns:
        Source ID as string (as per backend contract)
    """
    return str(shikimori_id)


def generate_episode_source_id(source_id: str, episode_number: int) -> str:
    """
    Generate deterministic episode source_id.
    
    Args:
        source_id: The anime source ID
        episode_number: The episode number
        
    Returns:
        Episode source ID in format "{source_id}:{episode_number}"
    """
    return f"{source_id}:{episode_number}"


def exponential_backoff_with_jitter(
    attempt: int,
    base_seconds: float = 1.0,
    max_seconds: float = 60.0
) -> float:
    """
    Calculate exponential backoff delay with jitter.
    
    Args:
        attempt: The retry attempt number (0-indexed)
        base_seconds: Base delay in seconds
        max_seconds: Maximum delay in seconds
        
    Returns:
        Delay in seconds with jitter applied
    """
    # Calculate exponential delay: base * 2^attempt
    delay = min(base_seconds * (2 ** attempt), max_seconds)
    
    # Add jitter: random value between 0 and delay
    jittered_delay = delay * random.random()
    
    return jittered_delay


def compute_diff(new: dict, old: dict | None) -> dict:
    """
    Compute shallow diff between two dictionaries.

    Args:
        new: New dictionary
        old: Old dictionary (can be None)

    Returns:
        Dict of changed keys with old/new values.
    """
    if not old:
        return {k: {"old": None, "new": v} for k, v in new.items()}

    diff: dict = {}
    for key, value in new.items():
        if old.get(key) != value:
            diff[key] = {"old": old.get(key), "new": value}
    return diff


def normalize_video_source(
    url: str,
    source_name: str,
    priority: int,
) -> dict | None:
    """
    Normalize and validate a single video source.

    Args:
        url: Video URL
        source_name: Provider/source name
        priority: Priority (lower = higher)

    Returns:
        Normalized player payload or None if invalid.
    """
    if not url or not isinstance(url, str):
        return None
    trimmed = url.strip()
    if not trimmed:
        return None
    # Enforce HLS player-ready link
    if not trimmed.lower().endswith(".m3u8"):
        return None
    return {
        "type": "hls",
        "url": trimmed,
        "source_name": source_name,
        "priority": int(priority),
    }


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""
    
    def __init__(self, rate_per_second: float):
        """
        Initialize rate limiter.
        
        Args:
            rate_per_second: Maximum requests per second
        """
        self.rate = rate_per_second
        self.min_interval = 1.0 / rate_per_second if rate_per_second > 0 else 0
        self.last_request_time: Optional[float] = None
    
    async def acquire(self):
        """Wait if necessary to respect rate limit."""
        if self.last_request_time is None:
            self.last_request_time = time.time()
            return
        
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
