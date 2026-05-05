import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import get_db
from app.models import Base

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite://"

# Ensure no real API keys are needed for basic tests
os.environ.setdefault("LLAMA_CLOUD_API_KEY", "test-key")
os.environ.setdefault("LLM_MODEL", "openai/gpt-4o")
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)


@pytest.fixture
async def db_session():
    """Create a fresh in-memory database for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession):
    """Create a test client with the DB session overridden."""
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
