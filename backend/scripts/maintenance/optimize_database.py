#!/usr/bin/env python3
"""
Database optimization migration script.

This script applies database optimizations to an existing database,
including index creation, statistics updates, and performance tuning.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

import asyncpg
from app.config import settings
from app.logging_config import setup_logging

# Setup logging
logger = setup_logging()

# Index definitions for optimization
OPTIMIZATION_INDEXES = [
    {
        "name": "idx_webinars_search_polish",
        "sql": """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_webinars_search_polish 
        ON webinars USING GIN(to_tsvector('polish', title || ' ' || COALESCE(description, '')))
        """,
        "description": "Full-text search index for Polish"
    },
    {
        "name": "idx_embeddings_vector_cosine",
        "sql": """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embeddings_vector_cosine 
        ON webinar_embeddings USING hnsw (vector vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64)
        """,
        "description": "Optimized vector operations index"
    },
    {
        "name": "idx_webinars_category_date_published",
        "sql": """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_webinars_category_date_published
        ON webinars(category_id, recorded_date DESC)
        WHERE status = 'published'
        """,
        "description": "Composite index for category + date filtering"
    },
    {
        "name": "idx_speakers_name_lower",
        "sql": """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_speakers_name_lower
        ON speakers(lower(name))
        """,
        "description": "Case-insensitive speaker name index"
    },
    {
        "name": "idx_tags_name_lower",
        "sql": """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tags_name_lower
        ON tags(lower(name))
        """,
        "description": "Case-insensitive tag name index"
    },
    {
        "name": "idx_speakers_bio_gin",
        "sql": """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_speakers_bio_gin
        ON speakers USING GIN(to_tsvector('polish', COALESCE(bio, '')))
        """,
        "description": "Speaker bio full-text search index"
    },
    {
        "name": "idx_tags_name_gin",
        "sql": """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tags_name_gin
        ON tags USING GIN(to_tsvector('polish', name))
        """,
        "description": "Tag name full-text search index"
    },
    {
        "name": "idx_webinars_category_status_date",
        "sql": """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_webinars_category_status_date
        ON webinars(category_id, status, recorded_date DESC)
        """,
        "description": "Composite index for multi-criteria filtering"
    }
]

# Tables to analyze after index creation
TABLES_TO_ANALYZE = [
    "webinars",
    "categories", 
    "speakers",
    "tags",
    "webinar_speakers",
    "webinar_tags",
    "webinar_embeddings"
]


async def check_database_connection() -> asyncpg.Connection:
    """Check database connection and return connection object."""
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        logger.info("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def check_index_exists(conn: asyncpg.Connection, index_name: str) -> bool:
    """Check if an index already exists."""
    query = """
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = $1
    )
    """
    exists = await conn.fetchval(query, index_name)
    return exists


async def create_index(conn: asyncpg.Connection, index_def: Dict[str, str]) -> bool:
    """Create a single index with error handling."""
    index_name = index_def["name"]
    sql = index_def["sql"]
    description = index_def["description"]
    
    try:
        # Check if index already exists
        if await check_index_exists(conn, index_name):
            logger.info(f"Index {index_name} already exists, skipping")
            return True
            
        logger.info(f"Creating index: {index_name} - {description}")
        await conn.execute(sql)
        logger.info(f"Successfully created index: {index_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create index {index_name}: {e}")
        return False


async def analyze_tables(conn: asyncpg.Connection) -> None:
    """Run ANALYZE on all tables to update statistics."""
    logger.info("Updating table statistics...")
    
    for table in TABLES_TO_ANALYZE:
        try:
            await conn.execute(f"ANALYZE {table}")
            logger.info(f"Analyzed table: {table}")
        except Exception as e:
            logger.error(f"Failed to analyze table {table}: {e}")


async def get_index_usage_stats(conn: asyncpg.Connection) -> List[Dict[str, Any]]:
    """Get index usage statistics."""
    query = """
    SELECT 
        schemaname,
        tablename,
        indexname,
        idx_scan,
        idx_tup_read,
        idx_tup_fetch
    FROM pg_stat_user_indexes 
    WHERE schemaname = 'public'
    ORDER BY idx_scan DESC
    """
    
    rows = await conn.fetch(query)
    return [dict(row) for row in rows]


async def get_table_sizes(conn: asyncpg.Connection) -> List[Dict[str, Any]]:
    """Get table size information."""
    query = """
    SELECT 
        schemaname,
        tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
    FROM pg_tables 
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """
    
    rows = await conn.fetch(query)
    return [dict(row) for row in rows]


async def optimize_database() -> None:
    """Main optimization function."""
    conn = None
    try:
        # Connect to database
        conn = await check_database_connection()
        
        # Create indexes
        logger.info("Starting index creation...")
        successful_indexes = 0
        failed_indexes = 0
        
        for index_def in OPTIMIZATION_INDEXES:
            if await create_index(conn, index_def):
                successful_indexes += 1
            else:
                failed_indexes += 1
        
        logger.info(f"Index creation completed: {successful_indexes} successful, {failed_indexes} failed")
        
        # Update table statistics
        await analyze_tables(conn)
        
        # Get performance statistics
        logger.info("Collecting performance statistics...")
        index_stats = await get_index_usage_stats(conn)
        table_sizes = await get_table_sizes(conn)
        
        # Log statistics
        logger.info("Index Usage Statistics:")
        for stat in index_stats[:10]:  # Top 10 most used indexes
            logger.info(f"  {stat['indexname']}: {stat['idx_scan']} scans")
        
        logger.info("Table Sizes:")
        for size_info in table_sizes:
            logger.info(f"  {size_info['tablename']}: {size_info['size']}")
        
        logger.info("Database optimization completed successfully")
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise
    finally:
        if conn:
            await conn.close()
            logger.info("Database connection closed")


async def main():
    """Main entry point."""
    logger.info("Starting database optimization...")
    
    try:
        await optimize_database()
        logger.info("Database optimization completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
