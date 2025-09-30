"""
Integration test configuration and fixtures for HR Search backend.
These tests connect to the real database.
"""
import asyncio
import pytest
import asyncpg
import sys
from pathlib import Path
from typing import AsyncGenerator

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.db import get_pool, close_pool
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
@pytest.mark.asyncio
async def real_db_pool():
    """Create a real database connection pool for integration testing."""
    # Ensure we're using the real database URL
    pool = await get_pool()
    yield pool
    await close_pool()


@pytest.fixture
@pytest.mark.asyncio
async def db_connection(real_db_pool):
    """Get a real database connection for individual tests."""
    async with real_db_pool.acquire() as conn:
        yield conn


@pytest.fixture(autouse=True)
@pytest.mark.asyncio
async def cleanup_test_data(real_db_pool):
    """Clean up test data after each test."""
    yield
    # Clean up any test data created during tests
    async with real_db_pool.acquire() as conn:
        # Remove any test data created during tests
        await conn.execute("DELETE FROM webinar_embeddings WHERE webinar_id LIKE 'test-%'")
        await conn.execute("DELETE FROM webinar_tags WHERE webinar_id LIKE 'test-%'")
        await conn.execute("DELETE FROM webinar_speakers WHERE webinar_id LIKE 'test-%'")
        await conn.execute("DELETE FROM webinars WHERE id LIKE 'test-%'")
        await conn.execute("DELETE FROM speakers WHERE id LIKE 'test-%'")
        await conn.execute("DELETE FROM tags WHERE id LIKE 'test-%'")
        await conn.execute("DELETE FROM categories WHERE id LIKE 'test-%'")
