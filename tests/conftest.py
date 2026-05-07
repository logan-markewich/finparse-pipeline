import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite://"

# Ensure no real API keys are needed for basic tests
os.environ.setdefault("LLAMA_CLOUD_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)


@pytest.fixture
async def test_session_factory():
    """Create a fresh in-memory database and return a session factory."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(test_session_factory):
    """Create a test client with the DB session factory patched globally."""
    import app.db
    from app.main import app as fastapi_app

    original = app.db.async_session
    app.db.async_session = test_session_factory
    try:
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.db.async_session = original
