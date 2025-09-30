"""
Test configuration and fixtures for HR Search backend.
"""
import asyncio
import pytest
import asyncpg
import sys
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Any
from unittest.mock import Mock, patch
import re

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db import get_pool, close_pool
from app.config import settings


class MockDatabase:
    """Intelligent mock database that simulates real database behavior."""
    
    def __init__(self):
        self.tables = {
            'webinars': [],
            'webinar_embeddings': [],
            'speakers': [],
            'tags': [],
            'categories': [],
            'webinar_speakers': [],
            'webinar_tags': []
        }
        self._setup_default_data()
    
    def _setup_default_data(self):
        """Setup some default test data."""
        # Add default categories
        self.tables['categories'].append({
            'id': 'cat-1', 'name': 'Test Category', 'slug': 'test-category'
        })
        
        # Add default speakers
        self.tables['speakers'].append({
            'id': 'speaker-1', 'name': 'Test Speaker', 'bio': 'Test bio'
        })
        
        # Add default tags
        self.tables['tags'].append({
            'id': 'tag-1', 'name': 'test-tag', 'slug': 'test-tag'
        })
    
    def execute(self, query: str, *args):
        """Simulate INSERT/UPDATE/DELETE operations."""
        query_lower = query.lower().strip()
        
        if query_lower.startswith('insert into'):
            self._handle_insert(query, args)
        elif query_lower.startswith('delete from'):
            self._handle_delete(query, args)
        elif query_lower.startswith('update'):
            self._handle_update(query, args)
    
    def _handle_insert(self, query: str, args: tuple):
        """Handle INSERT operations."""
        # Extract table name
        table_match = re.search(r'insert into (\w+)', query.lower())
        if not table_match:
            return
        
        table_name = table_match.group(1)
        if table_name not in self.tables:
            return
        
        # Extract column names
        columns_match = re.search(r'\(([^)]+)\)', query)
        if not columns_match:
            return
        
        columns = [col.strip() for col in columns_match.group(1).split(',')]
        
        # Extract VALUES part
        values_match = re.search(r'values\s*\(([^)]+)\)', query.lower())
        if not values_match:
            return
        
        values_str = values_match.group(1)
        values = []
        
        # Parse VALUES - handle both parameters ($1, $2) and literals ('title', 'published')
        param_index = 0
        i = 0
        while i < len(values_str):
            if values_str[i:i+2] == '$1' or values_str[i:i+2] == '$2' or values_str[i:i+2] == '$3' or values_str[i:i+2] == '$4':
                # Parameter
                if param_index < len(args):
                    values.append(args[param_index])
                    param_index += 1
                i += 2
            elif values_str[i] == "'":
                # Literal string
                end_quote = values_str.find("'", i + 1)
                if end_quote != -1:
                    literal = values_str[i+1:end_quote]
                    values.append(literal)
                    i = end_quote + 1
                else:
                    i += 1
            else:
                i += 1
        
        # Create record
        record = {}
        for i, col in enumerate(columns):
            if i < len(values):
                record[col] = values[i]
        
        self.tables[table_name].append(record)
    
    def _handle_delete(self, query: str, args: tuple):
        """Handle DELETE operations."""
        # Extract table name
        table_match = re.search(r'delete from (\w+)', query.lower())
        if not table_match:
            return
        
        table_name = table_match.group(1)
        if table_name not in self.tables:
            return
        
        # Simple implementation - remove records matching WHERE conditions
        if 'where' in query.lower():
            # For test cleanup, remove records with test IDs
            self.tables[table_name] = [
                record for record in self.tables[table_name]
                if not any(str(record.get('id', '')).startswith('test-') for record in [record])
            ]
    
    def _handle_update(self, query: str, args: tuple):
        """Handle UPDATE operations."""
        # For now, just pass - not used in current tests
        pass
    
    def fetch(self, query: str, *args):
        """Simulate SELECT operations."""
        query_lower = query.lower().strip()
        
        # Handle semantic search
        if 'vector' in query_lower and 'similarity' in query_lower:
            return self._handle_semantic_search(query, args)
        
        # Handle fuzzy search
        if 'similarity(' in query_lower and 'unaccent' in query_lower:
            return self._handle_fuzzy_search(query, args)
        
        # Handle autocomplete
        if 'union all' in query_lower and 'suggestion' in query_lower:
            return self._handle_autocomplete(query, args)
        
        # Handle category search
        if 'join categories' in query_lower and 'c.slug =' in query_lower:
            return self._handle_category_search(query, args)
        
        # Handle tag search (check this before speaker search to avoid conflicts)
        if 'webinar_tags' in query_lower and 't.slug in' in query_lower:
            return self._handle_tag_search(query, args)
        
        # Handle speaker search
        if 'join webinar_speakers' in query_lower and 'speaker' in query_lower:
            return self._handle_speaker_search(query, args)
        
        # Handle count queries
        if 'count(*)' in query_lower:
            return self._handle_count_query(query, args)
        
        # Default: return empty results
        return []
    
    def _handle_semantic_search(self, query: str, args: tuple):
        """Handle semantic search queries."""
        results = []
        limit = args[1] if len(args) > 1 else 20
        
        for webinar in self.tables['webinars']:
            if webinar.get('status') == 'published':
                # Find matching embedding
                embedding = next(
                    (e for e in self.tables['webinar_embeddings'] 
                     if e.get('webinar_id') == webinar['id'] and e.get('embedding_type') == 'title'),
                    None
                )
                if embedding:
                    # Mock similarity score
                    similarity = 0.8 if 'test' in webinar.get('title', '').lower() else 0.3
                    if similarity > 0.3:  # Above threshold
                        result = {
                            'id': webinar['id'],
                            'title': webinar['title'],
                            'description': webinar.get('description', ''),
                            'category_name': 'Test Category',
                            'similarity': similarity,
                            'speakers': ['Test Speaker'],
                            'tags': ['test-tag']
                        }
                        results.append(result)
        
        # Sort by similarity and apply limit
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def _handle_fuzzy_search(self, query: str, args: tuple):
        """Handle fuzzy search queries."""
        results = []
        search_term = args[0].lower() if args else ''
        limit = args[1] if len(args) > 1 else 20
        
        for webinar in self.tables['webinars']:
            if webinar.get('status') == 'published':
                title = webinar.get('title', '').lower()
                if search_term in title:
                    similarity = 0.7 if search_term in title else 0.1
                    if similarity > 0.2:  # Above fuzzy threshold
                        result = {
                            'id': webinar['id'],
                            'title': webinar['title'],
                            'description': webinar.get('description', ''),
                            'category_name': 'Test Category',
                            'similarity': similarity,
                            'speakers': ['Test Speaker'],
                            'tags': ['test-tag']
                        }
                        results.append(result)
        
        # Sort by similarity and apply limit
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def _handle_autocomplete(self, query: str, args: tuple):
        """Handle autocomplete queries."""
        results = []
        search_term = args[0].lower() if args else ''
        limit = args[1] if len(args) > 1 else 10
        
        # Webinar suggestions
        webinar_count = 0
        for webinar in self.tables['webinars']:
            if webinar.get('status') == 'published' and search_term in webinar.get('title', '').lower():
                if webinar_count < 3:  # Limit webinar suggestions to 3
                    results.append({
                        'suggestion': webinar['title'],
                        'type': 'webinar',
                        'priority': 1
                    })
                    webinar_count += 1
        
        # Speaker suggestions
        speaker_count = 0
        for speaker in self.tables['speakers']:
            if search_term in speaker.get('name', '').lower():
                if speaker_count < 3:  # Limit speaker suggestions to 3
                    results.append({
                        'suggestion': speaker['name'],
                        'type': 'speaker',
                        'priority': 2
                    })
                    speaker_count += 1
        
        # Tag suggestions
        tag_count = 0
        for tag in self.tables['tags']:
            if search_term in tag.get('name', '').lower():
                if tag_count < 3:  # Limit tag suggestions to 3
                    results.append({
                        'suggestion': tag['name'],
                        'type': 'tag',
                        'priority': 3
                    })
                    tag_count += 1
        
        # Sort by priority and apply overall limit
        results.sort(key=lambda x: x['priority'])
        return results[:limit]
    
    def _handle_category_search(self, query: str, args: tuple):
        """Handle category-based search."""
        results = []
        category_slug = args[0] if args else ''
        
        for webinar in self.tables['webinars']:
            if webinar.get('status') == 'published':
                # Check if webinar belongs to the category
                category_id = webinar.get('category_id')
                category = next(
                    (c for c in self.tables['categories'] if c.get('id') == category_id),
                    None
                )
                if category and category.get('slug') == category_slug:
                    result = {
                        'id': webinar['id'],
                        'title': webinar['title'],
                        'description': webinar.get('description', ''),
                        'category_name': category['name'],
                        'speakers': ['Test Speaker'],
                        'tags': ['test-tag']
                    }
                    results.append(result)
        return results
    
    def _handle_speaker_search(self, query: str, args: tuple):
        """Handle speaker-based search."""
        results = []
        speaker_name = args[0].lower() if args else ''
        
        for webinar in self.tables['webinars']:
            if webinar.get('status') == 'published':
                # Check if webinar has the speaker
                webinar_id = webinar['id']
                speaker_links = [
                    link for link in self.tables['webinar_speakers']
                    if link.get('webinar_id') == webinar_id
                ]
                
                for link in speaker_links:
                    speaker = next(
                        (s for s in self.tables['speakers'] if s.get('id') == link.get('speaker_id')),
                        None
                    )
                    if speaker and speaker_name in speaker.get('name', '').lower():
                        result = {
                            'id': webinar['id'],
                            'title': webinar['title'],
                            'description': webinar.get('description', ''),
                            'category_name': 'Test Category',
                            'speakers': [speaker['name']],
                            'tags': ['test-tag']
                        }
                        results.append(result)
                        break
        return results
    
    def _handle_tag_search(self, query: str, args: tuple):
        """Handle tag-based search."""
        results = []
        tag_slugs = args[2:] if len(args) > 2 else []  # Skip limit and offset
        
        for webinar in self.tables['webinars']:
            if webinar.get('status') == 'published':
                # Check if webinar has any of the tags
                webinar_id = webinar['id']
                tag_links = [
                    link for link in self.tables['webinar_tags']
                    if link.get('webinar_id') == webinar_id
                ]
                
                webinar_tags = []
                for link in tag_links:
                    tag = next(
                        (t for t in self.tables['tags'] if t.get('id') == link.get('tag_id')),
                        None
                    )
                    if tag and tag.get('slug') in tag_slugs:
                        webinar_tags.append(tag['name'])
                
                if webinar_tags:
                    result = {
                        'id': webinar['id'],
                        'title': webinar['title'],
                        'description': webinar.get('description', ''),
                        'category_name': 'Test Category',
                        'speakers': ['Test Speaker'],
                        'tags': webinar_tags
                    }
                    results.append(result)
        return results
    
    def _handle_count_query(self, query: str, args: tuple):
        """Handle COUNT queries."""
        if 'webinars' in query.lower():
            return len([w for w in self.tables['webinars'] if w.get('status') == 'published'])
        return 0
    
    def fetchval(self, query: str, *args):
        """Simulate single value queries."""
        if 'count' in query.lower():
            return self._handle_count_query(query, args)
        return None
    
    def fetchrow(self, query: str, *args):
        """Simulate single row queries."""
        results = self.fetch(query, *args)
        return results[0] if results else None


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def mock_database():
    """Create a fresh mock database instance for each test."""
    return MockDatabase()


@pytest.fixture(scope="function")
def test_db_pool(mock_database):
    """Create a mock database connection pool for testing."""
    from unittest.mock import Mock, AsyncMock
    
    # Create a mock pool
    mock_pool = Mock()
    
    # Create a mock connection that uses the shared mock database
    mock_conn = Mock()
    mock_conn.fetchval = AsyncMock(side_effect=lambda query, *args: mock_database.fetchval(query, *args))
    mock_conn.fetch = AsyncMock(side_effect=lambda query, *args: mock_database.fetch(query, *args))
    mock_conn.execute = AsyncMock(side_effect=lambda query, *args: mock_database.execute(query, *args))
    mock_conn.fetchrow = AsyncMock(side_effect=lambda query, *args: mock_database.fetchrow(query, *args))
    
    # Configure the acquire method to return an async context manager
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire = Mock(return_value=mock_context_manager)
    
    yield mock_pool


@pytest.fixture(scope="function")
def db_connection(mock_database):
    """Get a mock database connection for individual tests."""
    from unittest.mock import Mock, AsyncMock
    
    # Create a mock connection that uses the shared mock database
    mock_conn = Mock()
    mock_conn.fetchval = AsyncMock(side_effect=lambda query, *args: mock_database.fetchval(query, *args))
    mock_conn.fetch = AsyncMock(side_effect=lambda query, *args: mock_database.fetch(query, *args))
    mock_conn.execute = AsyncMock(side_effect=lambda query, *args: mock_database.execute(query, *args))
    mock_conn.fetchrow = AsyncMock(side_effect=lambda query, *args: mock_database.fetchrow(query, *args))
    
    # Add transaction support
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    mock_conn.transaction = Mock(return_value=mock_transaction)
    
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
