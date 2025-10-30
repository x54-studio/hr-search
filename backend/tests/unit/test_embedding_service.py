"""
Unit tests for EmbeddingService.

Tests core embedding generation functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np
from sentence_transformers import SentenceTransformer

from app.services.embedding_service import EmbeddingService
from app.exceptions import ValidationError, SearchError


class TestEmbeddingService:
    """Test EmbeddingService core functionality."""
    
    @pytest.fixture
    def mock_embedding_repo(self):
        """Create mock embedding repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create mock model manager."""
        return Mock()
    
    @pytest.fixture
    def embedding_service(self, mock_embedding_repo, mock_model_manager):
        """Create EmbeddingService instance with mocked repository."""
        return EmbeddingService(mock_embedding_repo, mock_model_manager)
    
    def test_get_model_lazy_loading(self, embedding_service):
        """Test that model is loaded lazily on first access."""
        mock_model = Mock(spec=SentenceTransformer)
        embedding_service.model_manager.get_model.return_value = mock_model
        
        # First call should load the model
        model1 = embedding_service.get_model()
        
        # Second call should return the same instance
        model2 = embedding_service.get_model()
        
        assert model1 is model2
        assert model1 is mock_model
        embedding_service.model_manager.get_model.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, embedding_service):
        """Test successful embedding generation."""
        # Setup
        text = "machine learning basics"
        mock_model = Mock(spec=SentenceTransformer)
        mock_embedding = np.array([0.1, 0.2, 0.3])
        
        embedding_service.model_manager.get_model.return_value = mock_model
        mock_model.encode.return_value = mock_embedding
        
        # Execute
        result = await embedding_service.generate_embedding(text)
        
        # Verify
        assert result == mock_embedding.tolist()
        mock_model.encode.assert_called_once_with(
            text, normalize_embeddings=True, show_progress_bar=False
        )
    
    @pytest.mark.asyncio
    async def test_generate_embedding_validation_empty_text(self, embedding_service):
        """Test validation with empty text."""
        with pytest.raises(ValidationError) as exc_info:
            await embedding_service.generate_embedding("")
        
        assert "Text cannot be empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_validation_long_text(self, embedding_service):
        """Test validation with text too long."""
        long_text = "x" * 201  # Over 200 character limit
        
        with pytest.raises(ValidationError) as exc_info:
            await embedding_service.generate_embedding(long_text)
        
        assert "Text too long" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_embedding_error_handling(self, embedding_service):
        """Test error handling in embedding generation."""
        # Setup
        text = "test"
        mock_model = Mock(spec=SentenceTransformer)
        embedding_service.model_manager.get_model.return_value = mock_model
        mock_model.encode.side_effect = Exception("Model error")
        
        # Execute & Verify
        with pytest.raises(SearchError) as exc_info:
            await embedding_service.generate_embedding(text)
        
        assert "Failed to generate embedding" in str(exc_info.value)