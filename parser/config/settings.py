import os
from dataclasses import dataclass, field
from typing import List


def _split_user_agents(raw: str | None) -> List[str]:
    if not raw:
        return []
    return [ua.strip() for ua in raw.splitlines() if ua.strip()]


@dataclass
class Settings:
    """Parser runtime settings loaded from environment."""

    backend_url: str = field(default_factory=lambda: os.getenv("PARSER_BACKEND_URL", "http://localhost:8000"))
    internal_token: str = field(default_factory=lambda: os.getenv("PARSER_INTERNAL_TOKEN", ""))
    consumet_base_url: str = field(
        default_factory=lambda: os.getenv("CONSUMET_BASE_URL", "https://api.consumet.org/anime/gogoanime")
    )
    source_limit: int = field(default_factory=lambda: int(os.getenv("PARSER_SOURCE_LIMIT", "5")))
    request_timeout: float = field(default_factory=lambda: float(os.getenv("PARSER_REQUEST_TIMEOUT", "15")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("PARSER_MAX_RETRIES", "3")))
    backoff_factor: float = field(default_factory=lambda: float(os.getenv("PARSER_BACKOFF_FACTOR", "1.0")))
    rate_limit_per_second: float = field(default_factory=lambda: float(os.getenv("PARSER_RPS", "1.0")))
    dry_run: bool = field(default_factory=lambda: os.getenv("PARSER_DRY_RUN", "0") in {"1", "true", "True"})
    user_agents: List[str] = field(
        default_factory=lambda: _split_user_agents(
            os.getenv(
                "PARSER_USER_AGENTS",
                "\n".join(
                    [
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
                        " (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
                    ]
                ),
            )
        )
    )


def load_settings(overrides: dict | None = None) -> Settings:
    """Load settings with optional overrides (useful for tests)."""
    settings = Settings()
    if overrides:
        for key, value in overrides.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
    return settings
