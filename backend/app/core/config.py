from pydantic_settings import BaseSettings, SettingsConfigDict


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
    SECRET_KEY: str = "your-secret-key-change-in-production"
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
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
