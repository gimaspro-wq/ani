from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, ValidationError as PydanticValidationError


# Cookie constants
REFRESH_COOKIE_NAME = "refresh_token"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Anirohi API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: Literal["dev", "production", "test"] = "dev"
    
    # Database
    DATABASE_URL: str
    
    # Security - NO DEFAULTS for secrets
    SECRET_KEY: str
    INTERNAL_TOKEN: str  # Token for internal API (parser access)
    ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL_MINUTES: int = 15
    REFRESH_TTL_DAYS: int = 30
    COOKIE_SECURE: bool = False
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Observability
    METRICS_ENABLED: bool = True
    TRACING_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "anirohi-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate and normalize DATABASE_URL for async usage.
        
        Non-URL DSN strings (without '://') pass through unchanged.
        """
        if not v:
            raise ValueError("DATABASE_URL must be set")
        
        if "://" not in v:
            return v
        
        scheme, rest = v.split("://", 1)
        scheme_lower = scheme.lower()
        
        # Idempotent: leave asyncpg URLs untouched
        if scheme_lower == "postgresql+asyncpg":
            return v
        
        # Normalize common postgres schemes (including psycopg2) to asyncpg
        if scheme_lower in {"postgresql", "postgres"} or scheme_lower.startswith("postgresql+psycopg"):
            return f"postgresql+asyncpg://{rest}"
        
        return v
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate SECRET_KEY is set and secure in production."""
        if not v:
            raise ValueError("SECRET_KEY must be set and cannot be empty")
        
        # Get env from info.data (works with both v1 and v2 validation)
        env = info.data.get("ENV", "dev")
        
        # In production, ensure secret key is strong enough
        if env == "production":
            if len(v) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters in production. "
                    "Generate with: openssl rand -hex 32"
                )
            
            # Reject weak/default keys
            weak_keys = [
                "your-secret-key",
                "change-this",
                "changeme",
                "secret",
                "default",
                "dev-secret",
            ]
            if any(weak in v.lower() for weak in weak_keys):
                raise ValueError(
                    "SECRET_KEY appears to be a default/weak value. "
                    "Generate a secure key with: openssl rand -hex 32"
                )
        
        return v
    
    @field_validator("INTERNAL_TOKEN")
    @classmethod
    def validate_internal_token(cls, v: str, info) -> str:
        """Validate INTERNAL_TOKEN is set."""
        if not v:
            raise ValueError("INTERNAL_TOKEN must be set and cannot be empty")
        
        env = info.data.get("ENV", "dev")
        if env == "production" and len(v) < 32:
            raise ValueError(
                "INTERNAL_TOKEN must be at least 32 characters in production. "
                "Generate with: openssl rand -hex 32"
            )
        
        return v
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


def load_settings() -> Settings:
    """Load and validate settings."""
    try:
        return Settings()
    except PydanticValidationError as e:
        # Re-raise with better error message for missing configs
        error_messages = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            error_messages.append(f"  - {field}: {msg}")
        
        raise RuntimeError(
            "Configuration validation failed:\n" + "\n".join(error_messages)
        ) from e


settings = load_settings()
