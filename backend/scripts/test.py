#!/usr/bin/env python3
"""
Unified test script for HR Search system.
Tests both Polish HR terms and IT-related content.
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
from app.search import search

async def test_hr_terms(pool):
    """Test Polish HR terms."""
    print("🇵🇱 Testing Polish HR terms...")
    
    hr_queries = ["praca", "rekrutacja", "motywacja", "wynagrodzenia", "onboarding"]
    
    for query in hr_queries:
        print(f"\n🔍 Testing: '{query}'")
        results = await search(query, pool, limit=3, debug=False)
        
        if results:
            print(f"✅ Found {len(results)} results")
            for i, r in enumerate(results[:2], 1):
                print(f"  {i}. {r['title']}")
        else:
            print("❌ No results")

async def test_it_terms(pool):
    """Test IT-related terms."""
    print("\n💻 Testing IT-related terms...")
    
    it_queries = ["AI", "IT", "tech", "development", "analytics", "cybersecurity"]
    
    for query in it_queries:
        print(f"\n🔍 Testing: '{query}'")
        results = await search(query, pool, limit=3, debug=False)
        
        if results:
            print(f"✅ Found {len(results)} results")
            for i, r in enumerate(results[:2], 1):
                print(f"  {i}. {r['title']}")
        else:
            print("❌ No results")

async def main():
    """Run all tests."""
    print("🧪 HR Search System Test Suite")
    print("=" * 50)
    
    try:
        pool = await get_pool()
        print("✅ Connected to database")
        
        await test_hr_terms(pool)
        await test_it_terms(pool)
        
        await close_pool()
        print("\n🔌 Database connection closed")
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await close_pool()

if __name__ == "__main__":
    asyncio.run(main())
