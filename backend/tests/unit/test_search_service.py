"""
Unit tests for SearchService.

Tests core search functionality with mocked repositories.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from app.services.search_service import SearchService
from app.exceptions import ValidationError, SearchError


class TestSearchService:
    """Test SearchService core functionality."""
    
    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories."""
        return {
            'webinar_repo': AsyncMock(),
            'category_repo': AsyncMock(),
            'speaker_repo': AsyncMock(),
            'tag_repo': AsyncMock(),
            'autocomplete_repo': AsyncMock(),
            'embedding_repo': AsyncMock()
        }
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        return AsyncMock()
    
    @pytest.fixture
    def search_service(self, mock_repositories, mock_embedding_service):
        """Create SearchService instance with mocked dependencies."""
        return SearchService(
            webinar_repo=mock_repositories['webinar_repo'],
            category_repo=mock_repositories['category_repo'],
            speaker_repo=mock_repositories['speaker_repo'],
            tag_repo=mock_repositories['tag_repo'],
            autocomplete_repo=mock_repositories['autocomplete_repo'],
            embedding_repo=mock_repositories['embedding_repo'],
            embedding_service=mock_embedding_service
        )
    
    @pytest.mark.asyncio
    async def test_search_semantic_success(self, search_service, mock_repositories, mock_embedding_service):
        """Test successful semantic search."""
        # Setup
        query = "machine learning"
        limit = 10
        mock_embedding = [0.1, 0.2, 0.3]
        mock_results = [{"id": "1", "title": "ML Basics", "similarity": 0.8}]
        
        mock_embedding_service.generate_embedding.return_value = mock_embedding
        mock_repositories['webinar_repo'].search_semantic.return_value = mock_results
        mock_repositories['webinar_repo'].search_fuzzy.return_value = []  # No fuzzy suggestions
        
        # Execute
        result = await search_service.search(query, limit)
        
        # Verify
        assert result["results"] == mock_results
        assert result["count"] == len(mock_results)
        assert result["original_query"] == query
        assert result["corrected_query"] is None
        
        mock_embedding_service.generate_embedding.assert_called_once_with(query)
        mock_repositories['webinar_repo'].search_semantic.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_fuzzy_fallback(self, search_service, mock_repositories, mock_embedding_service):
        """Test fuzzy search fallback when semantic search fails."""
        # Setup
        query = "machine learning"
        limit = 10
        mock_results = [{"id": "1", "title": "ML Basics", "similarity": 0.6}]
        
        mock_embedding_service.generate_embedding.return_value = [0.1, 0.2, 0.3]
        mock_repositories['webinar_repo'].search_semantic.return_value = []
        mock_repositories['webinar_repo'].search_fuzzy.return_value = mock_results
        
        # Execute
        result = await search_service.search(query, limit)
        
        # Verify
        assert result["results"] == mock_results
        assert result["count"] == len(mock_results)
        assert result["original_query"] == query
        assert result["corrected_query"] is None
        
        mock_repositories['webinar_repo'].search_fuzzy.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_spell_correction(self, search_service, mock_repositories, mock_embedding_service):
        """Test spell correction functionality."""
        # Setup
        query = "machne learning"  # typo
        limit = 10
        mock_embedding = [0.1, 0.2, 0.3]
        mock_results = [{"id": "1", "title": "Machine Learning Basics", "similarity": 0.8}]
        
        mock_embedding_service.generate_embedding.return_value = mock_embedding
        mock_repositories['webinar_repo'].search_semantic.return_value = mock_results
        mock_repositories['webinar_repo'].search_fuzzy.return_value = []  # No fuzzy suggestions
        
        # Execute
        result = await search_service.search(query, limit)
        
        # Verify
        assert result["results"] == mock_results
        assert result["count"] == len(mock_results)
        assert result["original_query"] == query
        assert result["corrected_query"] is None  # No correction in this simple test
        
        mock_embedding_service.generate_embedding.assert_called_once_with(query)
    
    @pytest.mark.asyncio
    async def test_search_validation_empty_query(self, search_service):
        """Test validation with empty query."""
        with pytest.raises(ValidationError) as exc_info:
            await search_service.search("", 10)
        
        assert "Query cannot be empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_validation_invalid_limit(self, search_service):
        """Test validation with invalid limit."""
        with pytest.raises(ValidationError) as exc_info:
            await search_service.search("test", 0)
        
        assert "Limit must be between 1 and 50" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_autocomplete_success(self, search_service, mock_repositories):
        """Test successful autocomplete."""
        # Setup
        query = "machine"
        limit = 5
        mock_suggestions = [
            {"suggestion": "Machine Learning", "type": "webinar", "priority": 1},
            {"suggestion": "Machine Learning Expert", "type": "speaker", "priority": 2}
        ]
        
        mock_repositories['autocomplete_repo'].get_suggestions.return_value = mock_suggestions
        
        # Execute
        result = await search_service.autocomplete(query, limit)
        
        # Verify
        assert result == mock_suggestions
        assert len(result) == len(mock_suggestions)
        
        mock_repositories['autocomplete_repo'].get_suggestions.assert_called_once_with(query, limit)
    
    @pytest.mark.asyncio
    async def test_autocomplete_validation(self, search_service):
        """Test autocomplete validation."""
        with pytest.raises(ValidationError) as exc_info:
            await search_service.autocomplete("", 10)
        
        assert "Query cannot be empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_service, mock_embedding_service):
        """Test error handling in search."""
        # Setup
        query = "test"
        limit = 10
        
        mock_embedding_service.generate_embedding.side_effect = Exception("Embedding error")
        
        # Execute & Verify
        with pytest.raises(SearchError) as exc_info:
            await search_service.search(query, limit)
        
        assert "Search operation failed" in str(exc_info.value)