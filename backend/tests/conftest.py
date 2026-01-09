import asyncio
import os
import sys
from pathlib import Path
from typing import Generator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

# Ensure repository root is importable when pytest is run from any working directory
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ---------------------------------------------------------------------------
# Test environment configuration (PostgreSQL only)
# ---------------------------------------------------------------------------
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("SECRET_KEY", "TEST_SECRET_KEY_DO_NOT_USE_IN_PRODUCTION_32CHARS")
os.environ.setdefault("INTERNAL_TOKEN", "TEST_INTERNAL_TOKEN_FOR_PARSER_ACCESS_32CHARS")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")  # Use test DB 15
os.environ.setdefault("ENV", "test")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")  # Disable rate limiting in tests
os.environ.setdefault("METRICS_ENABLED", "false")  # Disable metrics in tests

# Start dedicated PostgreSQL test container
postgres = PostgresContainer("postgres:16-alpine")
postgres.start()
_async_db_url = make_url(postgres.get_connection_url()).set(
    drivername="postgresql+asyncpg"
).render_as_string(hide_password=False)
os.environ["DATABASE_URL"] = _async_db_url

from app.core.config import settings  # noqa: E402
from app.db.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

async_engine = create_async_engine(
    _async_db_url,
    poolclass=NullPool,
)
AsyncTestingSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def _run_migrations() -> None:
    """Apply Alembic migrations to the test database."""
    await _reset_schema()
    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", _async_db_url)
    await asyncio.to_thread(command.upgrade, config, "head")


async def _truncate_db() -> None:
    """Clean all application tables between tests."""
    table_names = ", ".join(Base.metadata.tables.keys())
    if not table_names:
        return
    async with async_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))


async def _reset_schema() -> None:
    """Drop and recreate public schema to ensure clean migrations."""
    async with async_engine.begin() as conn:
        await conn.execute(text("DROP TYPE IF EXISTS librarystatus CASCADE;"))
        await conn.execute(text("DROP TYPE IF EXISTS animestatus CASCADE;"))
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _database() -> Generator[None, None, None]:
    """Ensure database is migrated and container is stopped after tests."""
    await _run_migrations()
    yield
    await async_engine.dispose()
    postgres.stop()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def _clean_database() -> Generator[None, None, None]:
    """Reset database state before each test."""
    await _truncate_db()
    yield


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client with async database override."""

    async def override_get_db():
        async with AsyncTestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }
