from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "Anirohi API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://ani_user:ani_password@localhost:5432/ani_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
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
