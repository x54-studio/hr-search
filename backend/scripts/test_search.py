#!/usr/bin/env python3
"""
Test script to verify search functionality works correctly.
"""
import asyncio
import sys
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.dependencies import get_database_pool, dependency_lifespan
from app.services import SearchService, EmbeddingService
from app.repositories import (
    ItemRepository, CategoryRepository, SpeakerRepository,
    TagRepository, AutocompleteRepository, EmbeddingRepository
)

async def test_search():
    """Test the search functionality"""
    print("Testing search functionality...")

    async with dependency_lifespan():
        try:
            pool = await get_database_pool()
            print("Connected to database")

            item_repo = ItemRepository(pool)
            category_repo = CategoryRepository(pool)
            speaker_repo = SpeakerRepository(pool)
            tag_repo = TagRepository(pool)
            autocomplete_repo = AutocompleteRepository(pool)
            embedding_repo = EmbeddingRepository(pool)

            embedding_service = EmbeddingService(embedding_repo)
            search_service = SearchService(
                item_repo, category_repo, speaker_repo,
                tag_repo, autocomplete_repo, embedding_repo, embedding_service
            )

            print("\n1. Testing basic search...")
            results = await search_service.search("rekrutacja", 5)
            print(f"   Found {len(results)} results for 'rekrutacja'")
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. {result.get('title', 'No title')}")

            print("\n2. Testing autocomplete...")
            suggestions = await search_service.autocomplete("mot", 5)
            print(f"   Found {len(suggestions)} suggestions for 'mot'")
            for suggestion in suggestions:
                print(f"   - {suggestion.get('suggestion', 'No suggestion')} ({suggestion.get('type', 'unknown')})")

            print("\n3. Testing categories...")
            categories = await search_service.get_categories()
            print(f"   Found {len(categories)} categories")

            print("\n4. Testing speakers...")
            speakers = await search_service.get_speakers(5)
            print(f"   Found {len(speakers)} speakers")

            print("\nAll tests completed successfully!")

        except Exception as e:
            print(f"Error during testing: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(test_search())
