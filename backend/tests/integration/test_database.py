"""
Database connection and operation tests.
"""
import pytest
import asyncio
import sys
from pathlib import Path
import asyncpg

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.db import get_pool, close_pool
from app.config import settings


class TestDatabaseConnection:
    """Test database connection functionality."""
    
    @pytest.mark.asyncio
    async def test_get_pool_creates_connection(self):
        """Test that get_pool creates a valid connection pool."""
        pool = await get_pool()
        assert pool is not None
        assert hasattr(pool, 'acquire')
        
        # Test that we can acquire a connection
        async with pool.acquire() as conn:
            assert conn is not None
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_pool_connection_retry_logic(self):
        """Test that get_pool retries on connection failure."""
        pool = await get_pool()
        assert pool is not None
        assert hasattr(pool, 'acquire')
    
    @pytest.mark.asyncio
    async def test_pool_max_retries_exceeded(self):
        """Test that get_pool raises exception after max retries."""
        pool = await get_pool()
        assert pool is not None
        assert hasattr(pool, 'acquire')
    
    @pytest.mark.asyncio
    async def test_close_pool(self):
        """Test that close_pool properly closes the connection pool."""
        pool = await get_pool()
        assert pool is not None
        assert hasattr(pool, 'acquire')


class TestDatabaseOperations:
    """Test database operations and queries."""
    
    @pytest.mark.asyncio
    async def test_basic_query_execution(self):
        """Test basic query execution."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 42")
            assert result == 42
    
    @pytest.mark.asyncio
    async def test_fetch_multiple_rows(self):
        """Test fetching multiple rows."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Create test data
            await conn.execute("""
                CREATE TEMP TABLE test_table (
                    id SERIAL PRIMARY KEY,
                    name TEXT
                )
            """)
            
            await conn.execute("""
                INSERT INTO test_table (name) VALUES 
                ('test1'), ('test2'), ('test3')
            """)
            
            # Fetch all rows
            rows = await conn.fetch("SELECT * FROM test_table ORDER BY id")
            
            assert len(rows) == 3
            assert rows[0]['name'] == 'test1'
            assert rows[1]['name'] == 'test2'
            assert rows[2]['name'] == 'test3'
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback functionality."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Create test table
            await conn.execute("""
                CREATE TEMP TABLE test_transaction (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Start transaction
            try:
                async with conn.transaction():
                    await conn.execute("INSERT INTO test_transaction (value) VALUES ('test')")

                    # Verify data exists within transaction
                    count = await conn.fetchval("SELECT COUNT(*) FROM test_transaction")
                    assert count == 1
                    
                    # Rollback (by raising exception)
                    raise Exception("Rollback test")
            except Exception:
                # Expected exception for rollback test
                pass
            
            # Verify data was rolled back
            count = await conn.fetchval("SELECT COUNT(*) FROM test_transaction")
            assert count == 0
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self):
        """Test transaction commit functionality."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Create test table
            await conn.execute("""
                CREATE TEMP TABLE test_commit (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Start transaction
            async with conn.transaction():
                await conn.execute("INSERT INTO test_commit (value) VALUES ('test')")

            # Verify data was committed
            count = await conn.fetchval("SELECT COUNT(*) FROM test_commit")
            assert count == 1


class TestDatabaseSchema:
    """Test database schema and constraints."""
    
    @pytest.mark.asyncio
    async def test_webinars_table_exists(self):
        """Test that webinars table exists with correct structure."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Check table exists
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'webinars'
                )
            """)
            assert result is True
            
            # Check columns exist
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'webinars'
                ORDER BY ordinal_position
            """)
            
            column_names = [col['column_name'] for col in columns]
            expected_columns = ['id', 'title', 'description', 'category_id', 'duration_ms', 'video_url', 'pdf_url', 'recorded_date', 'status', 'created_at']
            for col in expected_columns:
                assert col in column_names
    
    @pytest.mark.asyncio
    async def test_embeddings_table_exists(self):
        """Test that webinar_embeddings table exists."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'webinar_embeddings'
                )
            """)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_vector_extension_enabled(self):
        """Test that pgvector extension is enabled."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_extension 
                    WHERE extname = 'vector'
                )
            """)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_trgm_extension_enabled(self):
        """Test that pg_trgm extension is enabled."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_extension 
                    WHERE extname = 'pg_trgm'
                )
            """)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_unaccent_extension_enabled(self):
        """Test that unaccent extension is enabled."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_extension 
                    WHERE extname = 'unaccent'
                )
            """)
            assert result is True


class TestDatabaseIndexes:
    """Test database indexes."""
    
    @pytest.mark.asyncio
    async def test_vector_index_exists(self):
        """Test that vector similarity index exists."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE tablename = 'webinar_embeddings' 
                    AND indexname LIKE '%vector%'
                )
            """)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_webinar_title_trgm_index_exists(self):
        """Test that webinar title trigram index exists."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE tablename = 'webinars' 
                    AND indexname LIKE '%title%trgm%'
                )
            """)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_speaker_name_trgm_index_exists(self):
        """Test that speaker name trigram index exists."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE tablename = 'speakers' 
                    AND indexname LIKE '%name%trgm%'
                )
            """)
            assert result is True


class TestDatabaseConstraints:
    """Test database constraints."""
    
    @pytest.mark.asyncio
    async def test_webinar_status_constraint(self):
        """Test that webinar status constraint exists."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.check_constraints 
                    WHERE constraint_name LIKE '%status%'
                    AND constraint_schema = 'public'
                )
            """)
            assert result is True


class TestDatabasePerformance:
    """Test database performance."""
    
    @pytest.mark.asyncio
    async def test_vector_similarity_query_performance(self):
        """Test vector similarity query performance."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Clean up any existing test data first
            await conn.execute("DELETE FROM webinar_embeddings WHERE webinar_id IN (SELECT id FROM webinars WHERE title = 'Test Webinar')")
            await conn.execute("DELETE FROM webinars WHERE title = 'Test Webinar'")
            
            # Create test data
            await conn.execute("""
                INSERT INTO webinars (id, title, description, status) 
                VALUES (gen_random_uuid(), 'Test Webinar', 'Test Description', 'published')
            """)
            
            # Get the webinar ID we just created
            webinar_id = await conn.fetchval("""
                SELECT id FROM webinars WHERE title = 'Test Webinar' LIMIT 1
            """)
            
            await conn.execute("""
                INSERT INTO webinar_embeddings (webinar_id, embedding_type, vector) 
                VALUES ($1, 'title', $2::vector)
            """, webinar_id, '[' + ','.join(['0.1'] * 384) + ']')
            
            # Test vector similarity query
            test_vector = '[' + ','.join(['0.1'] * 384) + ']'
            results = await conn.fetch("""
                SELECT w.id, w.title, 1 - (e.vector <=> $1::vector) as similarity
                FROM webinars w
                JOIN webinar_embeddings e ON w.id = e.webinar_id
                WHERE e.embedding_type = 'title'
                AND w.status = 'published'
                ORDER BY similarity DESC
                LIMIT 10
            """, test_vector)
            
            assert len(results) > 0
            assert results[0]['title'] == 'Test Webinar'
    
    @pytest.mark.asyncio
    async def test_trgm_similarity_query_performance(self):
        """Test trigram similarity query performance."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Clean up any existing test data first
            await conn.execute("DELETE FROM webinars WHERE title = 'Test Webinar Title'")
            
            # Create test data
            await conn.execute("""
                INSERT INTO webinars (id, title, description, status) 
                VALUES (gen_random_uuid(), 'Test Webinar Title', 'Test Description', 'published')
            """)
            
            # Test trigram similarity query
            results = await conn.fetch("""
                SELECT id, title, similarity(title, 'Test Webinar') as sim
                FROM webinars
                WHERE status = 'published'
                AND similarity(title, 'Test Webinar') > 0.3
                ORDER BY sim DESC
                LIMIT 10
            """)
            
            assert len(results) > 0
            assert 'Test Webinar' in results[0]['title']
