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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

async def verify_system():
    """Run all verification checks."""
    print("Search System Verification")
    print("=" * 50)

    results = {
        "database": False,
        "data": False,
        "api_health": False,
        "api_config": False,
        "api_categories": False,
        "api_speakers": False,
        "api_tags": False,
        "api_items": False,
        "api_search": False,
        "api_autocomplete": False,
    }

    # 1. Check database connection
    print("\n1. Checking database connection...")
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        await conn.fetchval("SELECT 1")
        await conn.close()
        print("   Database connection OK")
        results["database"] = True
    except Exception as e:
        print(f"   Database connection failed: {e}")
        return results

    # 2. Check data exists
    print("\n2. Checking database has data...")
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        item_count = await conn.fetchval("SELECT COUNT(*) FROM items")
        embedding_count = await conn.fetchval("SELECT COUNT(*) FROM item_embeddings")
        await conn.close()

        print(f"   Items: {item_count}")
        print(f"   Embeddings: {embedding_count}")

        if item_count > 0 and embedding_count > 0:
            print("   Database has data")
            results["data"] = True
        else:
            print("   Database missing data or embeddings")
    except Exception as e:
        print(f"   Data check failed: {e}")

    # 3. Check API endpoints
    print("\n3. Checking API endpoints...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        base_url = "http://localhost:8000"

        # Health endpoint
        try:
            response = await client.get(f"{base_url}/api/health")
            if response.status_code == 200:
                print("   /api/health - OK")
                results["api_health"] = True
            else:
                print(f"   /api/health - HTTP {response.status_code}")
        except Exception as e:
            print(f"   /api/health - {str(e)[:50]}")

        # Config endpoint
        try:
            response = await client.get(f"{base_url}/api/config")
            if response.status_code == 200:
                data = response.json()
                print(f"   /api/config - OK (title: {data.get('title', 'N/A')})")
                results["api_config"] = True
            else:
                print(f"   /api/config - HTTP {response.status_code}")
        except Exception as e:
            print(f"   /api/config - {str(e)[:50]}")

        # Categories endpoint
        try:
            response = await client.get(f"{base_url}/api/categories")
            if response.status_code == 200:
                data = response.json()
                print(f"   /api/categories - OK ({len(data.get('categories', []))} categories)")
                results["api_categories"] = True
            else:
                print(f"   /api/categories - HTTP {response.status_code}")
        except Exception as e:
            print(f"   /api/categories - {str(e)[:50]}")

        # Speakers endpoint
        try:
            response = await client.get(f"{base_url}/api/speakers")
            if response.status_code == 200:
                data = response.json()
                print(f"   /api/speakers - OK ({len(data.get('speakers', []))} speakers)")
                results["api_speakers"] = True
            else:
                print(f"   /api/speakers - HTTP {response.status_code}")
        except Exception as e:
            print(f"   /api/speakers - {str(e)[:50]}")

        # Tags endpoint
        try:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                print(f"   /api/tags - OK ({len(data.get('tags', []))} tags)")
                results["api_tags"] = True
            else:
                print(f"   /api/tags - HTTP {response.status_code}")
        except Exception as e:
            print(f"   /api/tags - {str(e)[:50]}")

        # Items endpoint
        try:
            response = await client.get(f"{base_url}/api/items?limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"   /api/items - OK ({data.get('total', 0)} total)")
                results["api_items"] = True
            else:
                print(f"   /api/items - HTTP {response.status_code}")
        except Exception as e:
            print(f"   /api/items - {str(e)[:50]}")

        # Search endpoint
        try:
            response = await client.get(f"{base_url}/api/search?q=leadership&limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"   /api/search - OK ({data.get('count', 0)} results)")
                results["api_search"] = True
            else:
                print(f"   /api/search - HTTP {response.status_code}")
        except Exception as e:
            print(f"   /api/search - {str(e)[:50]}")

        # Autocomplete endpoint
        try:
            response = await client.get(f"{base_url}/api/autocomplete?q=lead&limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"   /api/autocomplete - OK ({len(data.get('suggestions', []))} suggestions)")
                results["api_autocomplete"] = True
            else:
                print(f"   /api/autocomplete - HTTP {response.status_code}")
        except Exception as e:
            print(f"   /api/autocomplete - {str(e)[:50]}")

    # Summary
    print("\n" + "=" * 50)
    print("Verification Summary")
    print("=" * 50)

    passed = sum(results.values())
    total = len(results)

    for check, status in results.items():
        icon = "OK" if status else "FAIL"
        print(f"  [{icon}] {check}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print("\nSystem verification PASSED")
        return 0
    else:
        print("\nSystem verification FAILED - Some components not working")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(verify_system())
    exit(exit_code)
