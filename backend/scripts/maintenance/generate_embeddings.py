#!/usr/bin/env python3
"""
Generate embeddings for all webinars in the database.
This script should be run after seeding sample data.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_pool, close_pool
from app.search import generate_all_embeddings

async def main():
    """Generate embeddings for all webinars."""
    print("🚀 Starting embedding generation...")
    
    try:
        pool = await get_pool()
        print("✅ Connected to database")
        
        # Generate embeddings
        await generate_all_embeddings(pool)
        
        print("✅ Embedding generation completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await close_pool()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(main())