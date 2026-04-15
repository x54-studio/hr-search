#!/usr/bin/env python3
"""
Check database state and diagnose search issues.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import modules
script_dir = Path(__file__).parent
backend_dir = script_dir.parent.parent
sys.path.insert(0, str(backend_dir))

from app.dependencies import get_database_pool

async def check_database():
    """Check database state and diagnose issues."""
    print("Checking database state...")

    try:
        pool = await get_database_pool()
        print("Connected to database")

        async with pool.acquire() as conn:
            item_count = await conn.fetchval("SELECT COUNT(*) FROM items WHERE status = 'published'")
            print(f"Published items: {item_count}")

            embedding_count = await conn.fetchval("SELECT COUNT(*) FROM item_embeddings")
            print(f"Stored embeddings: {embedding_count}")

            missing_embeddings = await conn.fetchval("""
                SELECT COUNT(*) FROM items i
                WHERE i.status = 'published'
                AND NOT EXISTS (
                    SELECT 1 FROM item_embeddings e
                    WHERE e.item_id = i.id
                    AND e.embedding_type = 'title'
                )
            """)
            print(f"Items missing embeddings: {missing_embeddings}")

            sample_items = await conn.fetch("""
                SELECT title, published_date
                FROM items
                WHERE status = 'published'
                ORDER BY published_date DESC
                LIMIT 5
            """)
            print(f"\nSample item titles:")
            for item in sample_items:
                print(f"   - {item['title']} ({item['published_date']})")

            if embedding_count > 0:
                dim = await conn.fetchval("""
                    SELECT vector_dims(vector)
                    FROM item_embeddings
                    LIMIT 1
                """)
                print(f"Embedding vector dims: {dim}")

            category_count = await conn.fetchval("SELECT COUNT(*) FROM categories")
            print(f"Categories: {category_count}")

            speaker_count = await conn.fetchval("SELECT COUNT(*) FROM speakers")
            print(f"Speakers: {speaker_count}")

            tag_count = await conn.fetchval("SELECT COUNT(*) FROM tags")
            print(f"Tags: {tag_count}")

    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(check_database())
