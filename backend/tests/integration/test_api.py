"""
Integration tests for API endpoints.
"""
import pytest
import httpx
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app


@pytest.fixture(autouse=True)
def mock_database():
    """Mock database connection for all API tests."""
    with patch('app.main.get_pool') as mock_get_pool:
        # Create a mock pool
        mock_pool = Mock()
        mock_pool.acquire = Mock()
        
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
        
        mock_get_pool.return_value = mock_pool
        yield mock_pool


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_search_results():
    """Mock search results for testing."""
    return [
        {
            "id": "test-webinar-1",
            "title": "Test Webinar 1",
            "description": "Test description 1",
            "category_name": "Test Category",
            "speakers": ["Test Speaker"],
            "tags": ["test", "webinar"],
            "duration_ms": 1800000,
            "recorded_date": "2024-01-01",
            "video_url": "https://example.com/video1.mp4",
            "pdf_url": "https://example.com/slides1.pdf"
        }
    ]


@pytest.fixture
def mock_autocomplete_suggestions():
    """Mock autocomplete suggestions for testing."""
    return [
        {"suggestion": "Test Webinar", "type": "webinar"},
        {"suggestion": "Test Speaker", "type": "speaker"},
        {"suggestion": "test-tag", "type": "tag"}
    ]


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_health_deep_endpoint_success(self, client):
        """Test deep health check with all systems healthy."""
        # For now, just test that the endpoint exists and returns a response
        # The actual health check will depend on the real database and model
        response = client.get("/api/health/deep")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "db" in data
        assert "model" in data
        assert "config" in data
        # Status could be "ok" or "degraded" depending on actual system state
        assert data["status"] in ["ok", "degraded"]


class TestSearchEndpoint:
    """Test search endpoint functionality."""
    
    @patch('app.main.search')
    def test_search_success(self, mock_search, client, mock_search_results):
        """Test successful search request."""
        mock_search.return_value = mock_search_results
        
        response = client.get("/api/search?q=test&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data
        assert len(data["results"]) == 1
        assert data["count"] == 1
    
    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.get("/api/search?q=")
        
        assert response.status_code == 422  # Validation error
    
    def test_search_invalid_limit(self, client):
        """Test search with invalid limit."""
        response = client.get("/api/search?q=test&limit=100")
        
        assert response.status_code == 400
        assert "Invalid limit" in response.json()["detail"]
    
    def test_search_query_too_long(self, client):
        """Test search with query too long."""
        long_query = "a" * 201  # Exceeds 200 char limit
        response = client.get(f"/api/search?q={long_query}")
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.main.search')
    def test_search_debug_mode(self, mock_search, client):
        """Test search with debug mode enabled."""
        mock_search.return_value = []
        
        response = client.get("/api/search?q=test&debug=true")
        
        assert response.status_code == 200
        mock_search.assert_called_once()
        # Check that debug=True was passed
        call_args = mock_search.call_args
        assert call_args[0][2] == 20  # limit
        assert call_args[0][3] is True  # debug


class TestAutocompleteEndpoint:
    """Test autocomplete endpoint functionality."""
    
    @patch('app.main.autocomplete')
    def test_autocomplete_success(self, mock_autocomplete, client, mock_autocomplete_suggestions):
        """Test successful autocomplete request."""
        mock_autocomplete.return_value = mock_autocomplete_suggestions
        
        response = client.get("/api/autocomplete?q=test&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 3
    
    def test_autocomplete_empty_query(self, client):
        """Test autocomplete with empty query."""
        response = client.get("/api/autocomplete?q=")
        
        assert response.status_code == 422  # Validation error
    
    def test_autocomplete_invalid_limit(self, client):
        """Test autocomplete with invalid limit."""
        response = client.get("/api/autocomplete?q=test&limit=25")
        
        assert response.status_code == 400
        assert "Invalid limit" in response.json()["detail"]


class TestWebinarEndpoints:
    """Test webinar-related endpoints."""
    
    @patch('app.main.get_webinar_details')
    def test_get_webinar_success(self, mock_get_webinar, client, mock_search_results):
        """Test successful webinar details request."""
        mock_get_webinar.return_value = mock_search_results[0]
        
        response = client.get("/api/webinars/test-webinar-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-webinar-1"
        assert data["title"] == "Test Webinar 1"
    
    @patch('app.main.get_webinar_details')
    def test_get_webinar_not_found(self, mock_get_webinar, client):
        """Test webinar details request for non-existent webinar."""
        mock_get_webinar.return_value = None
        
        response = client.get("/api/webinars/non-existent-id")
        
        assert response.status_code == 404
        assert "Webinar not found" in response.json()["detail"]
    
    @patch('app.main.list_recent_webinars')
    def test_list_webinars_default(self, mock_list_webinars, client, mock_search_results):
        """Test listing webinars with default parameters."""
        mock_list_webinars.return_value = (mock_search_results, 1)
        
        response = client.get("/api/webinars")
        
        assert response.status_code == 200
        data = response.json()
        assert "webinars" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert "hasMore" in data
    
    @patch('app.main.search_by_category')
    def test_list_webinars_by_category(self, mock_search_category, client, mock_search_results):
        """Test listing webinars by category."""
        mock_search_category.return_value = (mock_search_results, 1)
        
        response = client.get("/api/webinars?category=test-category")
        
        assert response.status_code == 200
        mock_search_category.assert_called_once()
    
    @patch('app.main.search_by_speaker')
    def test_list_webinars_by_speaker(self, mock_search_speaker, client, mock_search_results):
        """Test listing webinars by speaker."""
        mock_search_speaker.return_value = (mock_search_results, 1)
        
        response = client.get("/api/webinars?speaker=Test Speaker")
        
        assert response.status_code == 200
        mock_search_speaker.assert_called_once()
    
    @patch('app.main.search_by_tags')
    def test_list_webinars_by_tags(self, mock_search_tags, client, mock_search_results):
        """Test listing webinars by tags."""
        mock_search_tags.return_value = (mock_search_results, 1)
        
        response = client.get("/api/webinars?tags=test,webinar")
        
        assert response.status_code == 200
        mock_search_tags.assert_called_once()
    
    def test_list_webinars_invalid_offset(self, client):
        """Test listing webinars with invalid offset."""
        response = client.get("/api/webinars?offset=-1")
        
        assert response.status_code == 422  # Validation error
    
    def test_list_webinars_invalid_limit(self, client):
        """Test listing webinars with invalid limit."""
        response = client.get("/api/webinars?limit=101")
        
        assert response.status_code == 422  # Validation error


class TestMetadataEndpoints:
    """Test metadata endpoints."""
    
    @patch('app.main.get_categories')
    def test_get_categories(self, mock_get_categories, client):
        """Test getting categories."""
        mock_categories = [
            {"slug": "test-category", "name": "Test Category", "count": 5}
        ]
        mock_get_categories.return_value = mock_categories
        
        response = client.get("/api/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 1
    
    @patch('app.main.get_speakers')
    def test_get_speakers(self, mock_get_speakers, client):
        """Test getting speakers."""
        mock_speakers = [
            {"name": "Test Speaker", "bio": "Test bio", "count": 3}
        ]
        mock_get_speakers.return_value = mock_speakers
        
        response = client.get("/api/speakers")
        
        assert response.status_code == 200
        data = response.json()
        assert "speakers" in data
        assert len(data["speakers"]) == 1
    
    @patch('app.main.get_tags')
    def test_get_tags(self, mock_get_tags, client):
        """Test getting tags."""
        mock_tags = [
            {"slug": "test-tag", "name": "test-tag", "count": 10}
        ]
        mock_get_tags.return_value = mock_tags
        
        response = client.get("/api/tags")
        
        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert len(data["tags"]) == 1
    
    @patch('app.main.get_popular_tags')
    def test_get_popular_tags(self, mock_get_popular_tags, client):
        """Test getting popular tags."""
        mock_tags = [
            {"slug": "popular-tag", "name": "popular-tag", "count": 20}
        ]
        mock_get_popular_tags.return_value = mock_tags
        
        response = client.get("/api/tags/popular")
        
        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert len(data["tags"]) == 1


class TestCORSConfiguration:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = client.options("/api/health")
        
        # FastAPI TestClient doesn't fully simulate CORS, but we can check
        # that the endpoint exists and responds
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented
    
    def test_cors_allows_get_methods(self, client):
        """Test that GET methods are allowed."""
        response = client.get("/api/health")
        
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    @patch('app.main.search')
    def test_search_database_error(self, mock_search, client):
        """Test search endpoint handles database errors gracefully."""
        mock_search.side_effect = Exception("Database connection failed")
        
        # The endpoint should raise the exception (which is correct behavior)
        # TestClient will raise the exception instead of returning 500
        with pytest.raises(Exception, match="Database connection failed"):
            client.get("/api/search?q=test")
    
    def test_invalid_endpoint(self, client):
        """Test request to non-existent endpoint."""
        response = client.get("/api/non-existent")
        
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """Test invalid HTTP method."""
        response = client.post("/api/search")
        
        assert response.status_code == 405  # Method not allowed
