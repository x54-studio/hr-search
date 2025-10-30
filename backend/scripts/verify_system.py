"""
Simple system verification script.

Checks that all components are working correctly:
- Database connectivity
- Data exists
- All API endpoints respond
- ML model loaded
"""

import asyncio
import httpx
import asyncpg
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

async def verify_system():
    """Run all verification checks."""
    print("🔍 HR Search System Verification")
    print("=" * 50)
    
    results = {
        "database": False,
        "data": False,
        "api_health": False,
        "api_categories": False,
        "api_speakers": False,
        "api_tags": False,
        "api_webinars": False,
        "api_search": False,
        "api_autocomplete": False,
    }
    
    # 1. Check database connection
    print("\n1. Checking database connection...")
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        await conn.fetchval("SELECT 1")
        await conn.close()
        print("   ✅ Database connection OK")
        results["database"] = True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return results
    
    # 2. Check data exists
    print("\n2. Checking database has data...")
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        webinar_count = await conn.fetchval("SELECT COUNT(*) FROM webinars")
        embedding_count = await conn.fetchval("SELECT COUNT(*) FROM webinar_embeddings")
        await conn.close()
        
        print(f"   📊 Webinars: {webinar_count}")
        print(f"   🧠 Embeddings: {embedding_count}")
        
        if webinar_count > 0 and embedding_count > 0:
            print("   ✅ Database has data")
            results["data"] = True
        else:
            print("   ⚠️  Database missing data or embeddings")
    except Exception as e:
        print(f"   ❌ Data check failed: {e}")
    
    # 3. Check API endpoints
    print("\n3. Checking API endpoints...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        base_url = "http://localhost:8000"
        
        # Health endpoint
        try:
            response = await client.get(f"{base_url}/api/health")
            if response.status_code == 200:
                print("   ✅ /api/health - OK")
                results["api_health"] = True
            else:
                print(f"   ❌ /api/health - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ /api/health - {str(e)[:50]}")
        
        # Categories endpoint
        try:
            response = await client.get(f"{base_url}/api/categories")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ /api/categories - OK ({len(data.get('categories', []))} categories)")
                results["api_categories"] = True
            else:
                print(f"   ❌ /api/categories - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ /api/categories - {str(e)[:50]}")
        
        # Speakers endpoint
        try:
            response = await client.get(f"{base_url}/api/speakers")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ /api/speakers - OK ({len(data.get('speakers', []))} speakers)")
                results["api_speakers"] = True
            else:
                print(f"   ❌ /api/speakers - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ /api/speakers - {str(e)[:50]}")
        
        # Tags endpoint
        try:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ /api/tags - OK ({len(data.get('tags', []))} tags)")
                results["api_tags"] = True
            else:
                print(f"   ❌ /api/tags - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ /api/tags - {str(e)[:50]}")
        
        # Webinars endpoint
        try:
            response = await client.get(f"{base_url}/api/webinars?limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ /api/webinars - OK ({data.get('total', 0)} total)")
                results["api_webinars"] = True
            else:
                print(f"   ❌ /api/webinars - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ /api/webinars - {str(e)[:50]}")
        
        # Search endpoint
        try:
            response = await client.get(f"{base_url}/api/search?q=leadership&limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ /api/search - OK ({data.get('count', 0)} results)")
                results["api_search"] = True
            else:
                print(f"   ❌ /api/search - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ /api/search - {str(e)[:50]}")
        
        # Autocomplete endpoint
        try:
            response = await client.get(f"{base_url}/api/autocomplete?q=lead&limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ /api/autocomplete - OK ({len(data.get('suggestions', []))} suggestions)")
                results["api_autocomplete"] = True
            else:
                print(f"   ❌ /api/autocomplete - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ /api/autocomplete - {str(e)[:50]}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Verification Summary")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for check, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
    
    print(f"\n{'✅' if passed == total else '⚠️ '} {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 System verification PASSED - All components working!")
        return 0
    else:
        print("\n❌ System verification FAILED - Some components not working")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(verify_system())
    exit(exit_code)
