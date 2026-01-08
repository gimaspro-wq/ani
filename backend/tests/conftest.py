import asyncio
import os
from typing import AsyncGenerator, Generator
from collections.abc import AsyncIterator

# Set testing environment variables BEFORE importing settings
os.environ["TESTING"] = "1"
os.environ["DEBUG"] = "true"
os.environ["COOKIE_SECURE"] = "false"
# Use clearly identifiable test secret key (32+ chars for validation)
os.environ["SECRET_KEY"] = "TEST_SECRET_KEY_DO_NOT_USE_IN_PRODUCTION_32CHARS"
os.environ["ENV"] = "dev"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app

# Use SQLite for testing with async
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
)
AsyncTestingSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def init_test_db():
    """Initialize test database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_test_db():
    """Drop test database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Setup and teardown test database for each test."""
    asyncio.run(init_test_db())
    yield
    asyncio.run(drop_test_db())


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client with async database override."""
    
    async def override_get_db() -> AsyncIterator[AsyncSession]:
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
