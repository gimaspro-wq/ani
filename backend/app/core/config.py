from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


# Cookie constants
REFRESH_COOKIE_NAME = "refresh_token"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Anirohi API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "dev"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ani_user:ani_password@localhost:5432/ani_db"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    JWT_ACCESS_TTL_MINUTES: int = 15
    REFRESH_TTL_DAYS: int = 30
    COOKIE_SECURE: bool = False
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate SECRET_KEY is set and secure in production."""
        if not v:
            raise ValueError("SECRET_KEY must be set")
        
        # In production, ensure secret key is strong enough
        env = info.data.get("ENV", "dev")
        if env == "production" and len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters in production. "
                "Generate with: openssl rand -hex 32"
            )
        
        # Warn about default/weak keys
        weak_keys = [
            "your-secret-key",
            "change-this",
            "changeme",
            "secret",
            "default",
        ]
        if any(weak in v.lower() for weak in weak_keys):
            if env == "production":
                raise ValueError(
                    "SECRET_KEY appears to be a default/weak value. "
                    "Generate a secure key with: openssl rand -hex 32"
                )
        
        return v
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
