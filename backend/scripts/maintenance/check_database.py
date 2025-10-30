#!/usr/bin/env python3
"""
Check database state and diagnose search issues.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import modules
# Handle both running from backend/ and from project root
script_dir = Path(__file__).parent
backend_dir = script_dir.parent.parent  # Go up from scripts/maintenance to backend
sys.path.insert(0, str(backend_dir))

from app.dependencies import get_database_pool

async def check_database():
    """Check database state and diagnose issues."""
    print("🔍 Checking database state...")
    
    try:
        pool = await get_database_pool()
        print("✅ Connected to database")
        
        async with pool.acquire() as conn:
            # Check webinars count
            webinar_count = await conn.fetchval("SELECT COUNT(*) FROM webinars WHERE status = 'published'")
            print(f"📊 Published webinars: {webinar_count}")
            
            # Check embeddings count
            embedding_count = await conn.fetchval("SELECT COUNT(*) FROM webinar_embeddings")
            print(f"🧠 Stored embeddings: {embedding_count}")
            
            # Check if embeddings exist for published webinars
            missing_embeddings = await conn.fetchval("""
                SELECT COUNT(*) FROM webinars w
                WHERE w.status = 'published'
                AND NOT EXISTS (
                    SELECT 1 FROM webinar_embeddings e 
                    WHERE e.webinar_id = w.id 
                    AND e.embedding_type = 'title'
                )
            """)
            print(f"❌ Webinars missing embeddings: {missing_embeddings}")
            
            # Check sample webinar titles
            sample_webinars = await conn.fetch("""
                SELECT title, recorded_date 
                FROM webinars 
                WHERE status = 'published' 
                ORDER BY recorded_date DESC 
                LIMIT 5
            """)
            print(f"\n📝 Sample webinar titles:")
            for webinar in sample_webinars:
                print(f"   - {webinar['title']} ({webinar['recorded_date']})")
            
            # Check embedding dimension using pgvector function
            if embedding_count > 0:
                dim = await conn.fetchval("""
                    SELECT vector_dims(vector)
                    FROM webinar_embeddings
                    LIMIT 1
                """)
                print(f"🧮 Embedding vector dims: {dim}")
            
            # Check categories
            category_count = await conn.fetchval("SELECT COUNT(*) FROM categories")
            print(f"📂 Categories: {category_count}")
            
            # Check speakers
            speaker_count = await conn.fetchval("SELECT COUNT(*) FROM speakers")
            print(f"👥 Speakers: {speaker_count}")
            
            # Check tags
            tag_count = await conn.fetchval("SELECT COUNT(*) FROM tags")
            print(f"🏷️  Tags: {tag_count}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        # Pool cleanup is handled by the app lifespan
        print("🔌 Database connection cleanup completed")

if __name__ == "__main__":
    asyncio.run(check_database())
