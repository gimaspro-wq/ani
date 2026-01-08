"""Configuration for the parser service."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parser service settings loaded from environment variables."""
    
    # Backend Configuration
    BACKEND_BASE_URL: str = "http://localhost:8000"
    INTERNAL_TOKEN: str = "test_token"  # Default for testing
    
    # Concurrency and Rate Limiting
    CONCURRENCY: int = 4
    RATE_LIMIT_RPS: float = 2.0
    HTTP_TIMEOUT_SECONDS: int = 30
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    BACKOFF_BASE_SECONDS: float = 1.0
    BACKOFF_MAX_SECONDS: float = 60.0
    
    # External APIs
    KODIK_API_TOKEN: str = "test_token"  # Default for testing
    SHIKIMORI_BASE_URL: str = "https://shikimori.one/api"
    KODIK_BASE_URL: str = "https://kodikapi.com"
    
    # State Management
    STATE_PATH: str = "/tmp/parser_state.json"
    
    # Backend source name (fixed as per requirements)
    SOURCE_NAME: str = "kodik-shikimori"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
