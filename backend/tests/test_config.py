from app.core.config import Settings


def test_database_url_converts_postgresql_to_asyncpg():
    settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/dbname",
        SECRET_KEY="TEST_SECRET_KEY_OVERRIDE_FOR_URL_NORMALIZE_32",
        INTERNAL_TOKEN="TEST_INTERNAL_TOKEN_OVERRIDE_FOR_URL_NORMALIZE",
    )

    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/dbname"


def test_database_url_keeps_asyncpg_intact():
    url = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
    settings = Settings(
        DATABASE_URL=url,
        SECRET_KEY="TEST_SECRET_KEY_OVERRIDE_FOR_URL_NORMALIZE_32",
        INTERNAL_TOKEN="TEST_INTERNAL_TOKEN_OVERRIDE_FOR_URL_NORMALIZE",
    )

    assert settings.DATABASE_URL == url
