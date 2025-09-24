#!/usr/bin/env python3
"""
Test script to verify search functionality works correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import modules
# Handle both running from backend/ and from project root
script_dir = Path(__file__).parent
backend_dir = script_dir.parent  # Go up from scripts to backend
sys.path.insert(0, str(backend_dir))

from app.db import get_pool, close_pool
from app.search import search, autocomplete, get_categories, get_speakers

async def test_search():
    """Test the search functionality"""
    print("🧪 Testing search functionality...")
    
    try:
        pool = await get_pool()
        print("✅ Connected to database")
        
        # Test 1: Basic search
        print("\n1. Testing basic search...")
        results = await search("rekrutacja", pool, 5)
        print(f"   Found {len(results)} results for 'rekrutacja'")
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. {result.get('title', 'No title')}")
        
        # Test 2: Autocomplete
        print("\n2. Testing autocomplete...")
        suggestions = await autocomplete("mot", pool, 5)
        print(f"   Found {len(suggestions)} suggestions for 'mot'")
        for suggestion in suggestions:
            print(f"   - {suggestion.get('suggestion', 'No suggestion')} ({suggestion.get('type', 'unknown')})")
        
        # Test 3: Categories
        print("\n3. Testing categories...")
        categories = await get_categories(pool)
        print(f"   Found {len(categories)} categories")
        for cat in categories[:3]:
            print(f"   - {cat.get('name', 'No name')} ({cat.get('count', 0)} webinars)")
        
        # Test 4: Speakers
        print("\n4. Testing speakers...")
        speakers = await get_speakers(pool, 5)
        print(f"   Found {len(speakers)} speakers")
        for speaker in speakers[:3]:
            print(f"   - {speaker.get('name', 'No name')} ({speaker.get('count', 0)} webinars)")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        raise
    finally:
        await close_pool()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(test_search())




