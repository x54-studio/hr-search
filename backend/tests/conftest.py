"""
Test configuration and fixtures for HR Search backend.
"""
import asyncio
import pytest
import asyncpg
import sys
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import Mock, patch

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
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
def test_db_pool():
    """Create a mock database connection pool for testing."""
    from unittest.mock import Mock, AsyncMock
    
    # Create a mock pool
    mock_pool = Mock()
    
    # Create a mock connection
    mock_conn = Mock()
    mock_conn.fetchval = AsyncMock()
    mock_conn.fetch = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetchrow = AsyncMock()
    
    # Configure the acquire method to return an async context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire = Mock(return_value=mock_context_manager)
    
    yield mock_pool


@pytest.fixture
def db_connection(test_db_pool):
    """Get a mock database connection for individual tests."""
    from unittest.mock import Mock, AsyncMock
    
    # Create a mock connection
    mock_conn = Mock()
    mock_conn.fetchval = AsyncMock()
    mock_conn.fetch = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetchrow = AsyncMock()
    
    # Add transaction support
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    mock_conn.transaction = Mock(return_value=mock_transaction)
    
    # Set default return values
    mock_conn.fetchval.return_value = 42
    mock_conn.fetch.return_value = [
        {'id': 1, 'name': 'test1'},
        {'id': 2, 'name': 'test2'},
        {'id': 3, 'name': 'test3'}
    ]
    
    return mock_conn


@pytest.fixture
def mock_embedding():
    """Mock embedding for testing search functionality."""
    return [0.1] * 384  # 384-dimensional vector


@pytest.fixture
def sample_webinar_data():
    """Sample webinar data for testing."""
    return {
        "id": "test-webinar-id",
        "title": "Test Webinar Title",
        "description": "Test webinar description",
        "category_name": "Test Category",
        "speakers": ["Test Speaker"],
        "tags": ["test", "webinar"],
        "duration_ms": 1800000,
        "recorded_date": "2024-01-01",
        "video_url": "https://example.com/video.mp4",
        "pdf_url": "https://example.com/slides.pdf"
    }


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return [
        {
            "id": "webinar-1",
            "title": "Rekrutacja w IT",
            "description": "Jak rekrutować programistów",
            "category_name": "Rekrutacja",
            "speakers": ["Jan Kowalski"],
            "tags": ["rekrutacja", "IT"],
            "similarity": 0.85
        },
        {
            "id": "webinar-2", 
            "title": "Motywacja zespołu",
            "description": "Techniki motywowania pracowników",
            "category_name": "Zarządzanie",
            "speakers": ["Anna Nowak"],
            "tags": ["motywacja", "zespół"],
            "similarity": 0.72
        }
    ]


@pytest.fixture
def mock_model():
    """Mock sentence transformer model."""
    mock = Mock()
    mock.encode.return_value = [[0.1] * 384]  # Return 384-dim vector
    return mock


@pytest.fixture(autouse=True)
async def cleanup_database(test_db_pool):
    """Clean up test data after each test."""
    yield
    # Clean up any test data if needed
    async with test_db_pool.acquire() as conn:
        # Remove any test data created during tests
        await conn.execute("DELETE FROM webinar_embeddings WHERE webinar_id LIKE 'test-%'")
        await conn.execute("DELETE FROM webinar_tags WHERE webinar_id LIKE 'test-%'")
        await conn.execute("DELETE FROM webinar_speakers WHERE webinar_id LIKE 'test-%'")
        await conn.execute("DELETE FROM webinars WHERE id LIKE 'test-%'")
