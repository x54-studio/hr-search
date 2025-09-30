"""
Unit tests for search functionality.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.search import (
    search, autocomplete, generate_embedding, 
    search_by_category, search_by_speaker, search_by_tags
)


class TestGenerateEmbedding:
    """Test embedding generation functionality."""
    
    @patch('app.search.get_model')
    def test_generate_embedding_basic(self, mock_get_model):
        """Test basic embedding generation."""
        # Setup
        mock_model = Mock()
        mock_array = Mock()
        mock_array.tolist.return_value = [0.1, 0.2, 0.3]
        mock_model.encode.return_value = mock_array
        mock_get_model.return_value = mock_model
        
        # Test
        result = generate_embedding("test query")
        
        # Assertions
        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with(
            "test query", 
            normalize_embeddings=True, 
            show_progress_bar=False
        )
    
    @patch('app.search.get_model')
    def test_generate_embedding_empty_text(self, mock_get_model):
        """Test embedding generation with empty text."""
        mock_model = Mock()
        mock_array = Mock()
        mock_array.tolist.return_value = [0.0] * 384
        mock_model.encode.return_value = mock_array
        mock_get_model.return_value = mock_model
        
        result = generate_embedding("")
        
        assert len(result) == 384
        assert all(x == 0.0 for x in result)


class TestSearch:
    """Test main search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, test_db_pool):
        """Test search with empty query returns empty results."""
        result = await search("", test_db_pool, limit=10)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_search_whitespace_query(self, test_db_pool):
        """Test search with whitespace-only query returns empty results."""
        result = await search("   ", test_db_pool, limit=10)
        assert result == []
    
    @pytest.mark.asyncio
    @patch('app.search.generate_embedding')
    async def test_search_semantic_success(self, mock_generate_embedding, test_db_pool, db_connection):
        """Test successful semantic search."""
        # Setup
        mock_generate_embedding.return_value = [0.1] * 384
        
        # Create test webinar with embedding
        webinar_id = "test-semantic-webinar"
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, status)
            VALUES ($1, $2, $3, 'published')
        """, webinar_id, "Test Semantic Webinar", "Test description")
        
        await db_connection.execute("""
            INSERT INTO webinar_embeddings (webinar_id, embedding_type, vector)
            VALUES ($1, 'title', $2::vector)
        """, webinar_id, '[' + ','.join(['0.1'] * 384) + ']')
        
        # Test
        result = await search("test query", test_db_pool, limit=10)
        
        # Assertions
        assert len(result) > 0
        assert result[0]['id'] == webinar_id
        mock_generate_embedding.assert_called_once_with("test query")
    
    @pytest.mark.asyncio
    @patch('app.search.generate_embedding')
    async def test_search_fuzzy_fallback(self, mock_generate_embedding, test_db_pool, db_connection):
        """Test fuzzy search fallback when semantic search fails."""
        # Setup
        mock_generate_embedding.return_value = [0.1] * 384
        
        # Create test webinar without embedding (semantic will fail)
        webinar_id = "test-fuzzy-webinar"
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, status)
            VALUES ($1, $2, $3, 'published')
        """, webinar_id, "Test Fuzzy Webinar", "Test description")
        
        # Test
        result = await search("test", test_db_pool, limit=10)
        
        # Should fall back to fuzzy search
        assert len(result) > 0
        assert result[0]['id'] == webinar_id
    
    @pytest.mark.asyncio
    async def test_search_limit_respected(self, test_db_pool, db_connection):
        """Test that search respects the limit parameter."""
        # Create multiple test webinars
        for i in range(5):
            webinar_id = f"test-limit-webinar-{i}"
            await db_connection.execute("""
                INSERT INTO webinars (id, title, description, status)
                VALUES ($1, $2, $3, 'published')
            """, webinar_id, f"Test Webinar {i}", f"Description {i}")
        
        # Test with limit
        result = await search("test", test_db_pool, limit=3)
        
        # Should respect limit
        assert len(result) <= 3


class TestAutocomplete:
    """Test autocomplete functionality."""
    
    @pytest.mark.asyncio
    async def test_autocomplete_empty_query(self, test_db_pool):
        """Test autocomplete with empty query returns empty results."""
        result = await autocomplete("", test_db_pool, limit=10)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_autocomplete_webinar_suggestions(self, test_db_pool, db_connection):
        """Test autocomplete returns webinar suggestions."""
        # Create test webinar
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, status)
            VALUES ($1, $2, $3, 'published')
        """, "test-autocomplete-webinar", "Test Autocomplete Webinar", "Test description")
        
        # Test
        result = await autocomplete("test", test_db_pool, limit=10)
        
        # Should return webinar suggestions
        assert len(result) > 0
        assert any(s['type'] == 'webinar' for s in result)
    
    @pytest.mark.asyncio
    async def test_autocomplete_speaker_suggestions(self, test_db_pool, db_connection):
        """Test autocomplete returns speaker suggestions."""
        # Create test speaker
        await db_connection.execute("""
            INSERT INTO speakers (id, name, bio)
            VALUES ($1, $2, $3)
        """, "test-speaker-id", "Test Speaker", "Test bio")
        
        # Test
        result = await autocomplete("test", test_db_pool, limit=10)
        
        # Should return speaker suggestions
        assert len(result) > 0
        assert any(s['type'] == 'speaker' for s in result)
    
    @pytest.mark.asyncio
    async def test_autocomplete_tag_suggestions(self, test_db_pool, db_connection):
        """Test autocomplete returns tag suggestions."""
        # Create test tag
        await db_connection.execute("""
            INSERT INTO tags (id, name, slug)
            VALUES ($1, $2, $3)
        """, "test-tag-id", "test-tag", "test-tag")
        
        # Test
        result = await autocomplete("test", test_db_pool, limit=10)
        
        # Should return tag suggestions
        assert len(result) > 0
        assert any(s['type'] == 'tag' for s in result)
    
    @pytest.mark.asyncio
    async def test_autocomplete_limit_respected(self, test_db_pool, db_connection):
        """Test that autocomplete respects the limit parameter."""
        # Create multiple test webinars
        for i in range(5):
            await db_connection.execute("""
                INSERT INTO webinars (id, title, description, status)
                VALUES ($1, $2, $3, 'published')
            """, f"test-autocomplete-{i}", f"Test Webinar {i}", f"Description {i}")
        
        # Test with limit
        result = await autocomplete("test", test_db_pool, limit=3)
        
        # Should respect limit
        assert len(result) <= 3


class TestSearchByCategory:
    """Test category-based search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_by_category_success(self, test_db_pool, db_connection):
        """Test successful category search."""
        # Create test category and webinar
        category_id = "test-category-id"
        await db_connection.execute("""
            INSERT INTO categories (id, name, slug)
            VALUES ($1, $2, $3)
        """, category_id, "Test Category", "test-category")
        
        webinar_id = "test-category-webinar"
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, category_id, status)
            VALUES ($1, $2, $3, $4, 'published')
        """, webinar_id, "Test Category Webinar", "Test description", category_id)
        
        # Test
        results, total = await search_by_category("test-category", test_db_pool, offset=0, limit=10)
        
        # Assertions
        assert len(results) > 0
        assert total > 0
        assert results[0]['id'] == webinar_id
    
    @pytest.mark.asyncio
    async def test_search_by_category_not_found(self, test_db_pool):
        """Test category search with non-existent category."""
        results, total = await search_by_category("non-existent", test_db_pool, offset=0, limit=10)
        
        assert len(results) == 0
        assert total == 0


class TestSearchBySpeaker:
    """Test speaker-based search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_by_speaker_success(self, test_db_pool, db_connection):
        """Test successful speaker search."""
        # Create test speaker and webinar
        speaker_id = "test-speaker-id"
        await db_connection.execute("""
            INSERT INTO speakers (id, name, bio)
            VALUES ($1, $2, $3)
        """, speaker_id, "Test Speaker", "Test bio")
        
        webinar_id = "test-speaker-webinar"
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, status)
            VALUES ($1, $2, $3, 'published')
        """, webinar_id, "Test Speaker Webinar", "Test description")
        
        await db_connection.execute("""
            INSERT INTO webinar_speakers (webinar_id, speaker_id)
            VALUES ($1, $2)
        """, webinar_id, speaker_id)
        
        # Test
        results, total = await search_by_speaker("Test Speaker", test_db_pool, offset=0, limit=10)
        
        # Assertions
        assert len(results) > 0
        assert total > 0
        assert results[0]['id'] == webinar_id
    
    @pytest.mark.asyncio
    async def test_search_by_speaker_partial_match(self, test_db_pool, db_connection):
        """Test speaker search with partial name match."""
        # Create test speaker and webinar
        speaker_id = "test-speaker-id"
        await db_connection.execute("""
            INSERT INTO speakers (id, name, bio)
            VALUES ($1, $2, $3)
        """, speaker_id, "John Doe", "Test bio")
        
        webinar_id = "test-speaker-webinar"
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, status)
            VALUES ($1, $2, $3, 'published')
        """, webinar_id, "Test Speaker Webinar", "Test description")
        
        await db_connection.execute("""
            INSERT INTO webinar_speakers (webinar_id, speaker_id)
            VALUES ($1, $2)
        """, webinar_id, speaker_id)
        
        # Test with partial match
        results, total = await search_by_speaker("John", test_db_pool, offset=0, limit=10)
        
        # Should find the speaker
        assert len(results) > 0
        assert total > 0


class TestSearchByTags:
    """Test tag-based search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_by_tags_success(self, test_db_pool, db_connection):
        """Test successful tag search."""
        # Create test tag and webinar
        tag_id = "test-tag-id"
        await db_connection.execute("""
            INSERT INTO tags (id, name, slug)
            VALUES ($1, $2, $3)
        """, tag_id, "test-tag", "test-tag")
        
        webinar_id = "test-tag-webinar"
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, status)
            VALUES ($1, $2, $3, 'published')
        """, webinar_id, "Test Tag Webinar", "Test description")
        
        await db_connection.execute("""
            INSERT INTO webinar_tags (webinar_id, tag_id)
            VALUES ($1, $2)
        """, webinar_id, tag_id)
        
        # Test
        results, total = await search_by_tags(["test-tag"], test_db_pool, offset=0, limit=10)
        
        # Assertions
        assert len(results) > 0
        assert total > 0
        assert results[0]['id'] == webinar_id
    
    @pytest.mark.asyncio
    async def test_search_by_tags_empty_list(self, test_db_pool):
        """Test tag search with empty tag list."""
        results, total = await search_by_tags([], test_db_pool, offset=0, limit=10)
        
        assert len(results) == 0
        assert total == 0
    
    @pytest.mark.asyncio
    async def test_search_by_tags_multiple_tags(self, test_db_pool, db_connection):
        """Test tag search with multiple tags (OR logic)."""
        # Create test tags
        tag1_id = "test-tag-1"
        tag2_id = "test-tag-2"
        
        await db_connection.execute("""
            INSERT INTO tags (id, name, slug)
            VALUES ($1, $2, $3)
        """, tag1_id, "tag1", "tag1")
        
        await db_connection.execute("""
            INSERT INTO tags (id, name, slug)
            VALUES ($1, $2, $3)
        """, tag2_id, "tag2", "tag2")
        
        # Create webinars with different tags
        webinar1_id = "test-tag-webinar-1"
        webinar2_id = "test-tag-webinar-2"
        
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, status)
            VALUES ($1, $2, $3, 'published')
        """, webinar1_id, "Test Tag Webinar 1", "Test description")
        
        await db_connection.execute("""
            INSERT INTO webinars (id, title, description, status)
            VALUES ($1, $2, $3, 'published')
        """, webinar2_id, "Test Tag Webinar 2", "Test description")
        
        # Link tags
        await db_connection.execute("""
            INSERT INTO webinar_tags (webinar_id, tag_id)
            VALUES ($1, $2)
        """, webinar1_id, tag1_id)
        
        await db_connection.execute("""
            INSERT INTO webinar_tags (webinar_id, tag_id)
            VALUES ($1, $2)
        """, webinar2_id, tag2_id)
        
        # Test with multiple tags
        results, total = await search_by_tags(["tag1", "tag2"], test_db_pool, offset=0, limit=10)
        
        # Should find both webinars (OR logic)
        assert len(results) == 2
        assert total == 2
