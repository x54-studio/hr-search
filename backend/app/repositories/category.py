"""
Category, Speaker, Tag, and Autocomplete repository classes.
"""

import asyncpg
from typing import List, Dict, Optional, Tuple, Any
from ..logging_config import LoggingMixin


class CategoryRepository(LoggingMixin):
    """Repository for category-related database operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def _fetch(self, query: str, *args) -> List[Dict]:
        """Execute query and return results as list of dictionaries."""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(query, *args)
            return [dict(r) for r in results]

    async def get_all_with_counts(self) -> List[Dict]:
        """
        Get all categories with item counts.

        Returns:
            List of categories with id, name, slug, and item_count
        """
        query = """
        SELECT
            c.id, c.name, c.slug,
            COUNT(i.id) as item_count
        FROM categories c
        LEFT JOIN items i ON c.id = i.category_id AND i.status = 'published'
        GROUP BY c.id, c.name, c.slug
        ORDER BY c.name
        """
        return await self._fetch(query)

    async def search_by_name(self, name: str, limit: int) -> List[Dict]:
        """Search categories by name using pg_trgm word similarity."""
        query = """
        SELECT
            c.id, c.name as suggestion, c.slug,
            word_similarity(lower(unaccent($1)), lower(unaccent(c.name))) as similarity
        FROM categories c
        WHERE word_similarity(lower(unaccent($1)), lower(unaccent(c.name))) > 0.3
        ORDER BY similarity DESC
        LIMIT $2
        """
        return await self._fetch(query, name, limit)


class SpeakerRepository(LoggingMixin):
    """Repository for speaker-related database operations."""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def _fetch(self, query: str, *args) -> List[Dict]:
        """Execute query and return results as list of dictionaries."""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(query, *args)
            return [dict(r) for r in results]
    
    async def get_all_with_counts(self, limit: int) -> List[Dict]:
        """
        Get all speakers with item counts.

        Args:
            limit: Maximum number of speakers to return

        Returns:
            List of speakers with id, name, bio, and item_count
        """
        query = """
        SELECT
            s.id, s.name, s.bio,
            COUNT(isp.item_id) as item_count
        FROM speakers s
        LEFT JOIN item_speakers isp ON s.id = isp.speaker_id
        LEFT JOIN items i ON isp.item_id = i.id AND i.status = 'published'
        GROUP BY s.id, s.name, s.bio
        ORDER BY item_count DESC, s.name
        LIMIT $1
        """
        return await self._fetch(query, limit)
    
    async def search_by_name(self, name: str, limit: int) -> List[Dict]:
        """
        Search speakers by name using pg_trgm word similarity.

        Uses word_similarity() rather than similarity() so that partial
        queries like "agnies" or "Lewandowska" align with the best-matching
        word inside the full speaker name. similarity() scores a 6-char
        query against a 20-char full name at ~0.2 (diluted by length);
        word_similarity scores it at ~0.7 against the actual matching word.

        Args:
            name: Speaker name to search for
            limit: Maximum number of results to return

        Returns:
            List of speakers with name as 'suggestion' and similarity score
        """
        query = """
        SELECT
            s.id, s.name as suggestion,
            word_similarity(lower(unaccent($1)), lower(unaccent(s.name))) as similarity
        FROM speakers s
        WHERE word_similarity(lower(unaccent($1)), lower(unaccent(s.name))) > 0.3
        ORDER BY similarity DESC
        LIMIT $2
        """
        return await self._fetch(query, name, limit)


class TagRepository(LoggingMixin):
    """Repository for tag-related database operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def _fetch(self, query: str, *args) -> List[Dict]:
        """Execute query and return results as list of dictionaries."""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(query, *args)
            return [dict(r) for r in results]

    async def search_by_name(self, name: str, limit: int) -> List[Dict]:
        """Search tags by name using pg_trgm word similarity."""
        query = """
        SELECT
            t.id, t.name as suggestion, t.slug,
            word_similarity(lower(unaccent($1)), lower(unaccent(t.name))) as similarity
        FROM tags t
        WHERE word_similarity(lower(unaccent($1)), lower(unaccent(t.name))) > 0.3
        ORDER BY similarity DESC
        LIMIT $2
        """
        return await self._fetch(query, name, limit)

    async def get_all_with_counts(self, limit: int) -> List[Dict]:
        """
        Get all tags with item counts.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of tags with id, name, slug, and item_count
        """
        query = """
        SELECT
            t.id, t.name, t.slug,
            COUNT(it.item_id) as item_count
        FROM tags t
        LEFT JOIN item_tags it ON t.id = it.tag_id
        LEFT JOIN items i ON it.item_id = i.id AND i.status = 'published'
        GROUP BY t.id, t.name, t.slug
        ORDER BY item_count DESC, t.name
        LIMIT $1
        """
        return await self._fetch(query, limit)
    
    async def get_popular(self, limit: int) -> List[Dict]:
        """
        Get popular tags ordered by usage count.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of popular tags with id, name, slug, and item_count
        """
        query = """
        SELECT
            t.id, t.name, t.slug,
            COUNT(it.item_id) as item_count
        FROM tags t
        JOIN item_tags it ON t.id = it.tag_id
        JOIN items i ON it.item_id = i.id AND i.status = 'published'
        GROUP BY t.id, t.name, t.slug
        HAVING COUNT(it.item_id) > 0
        ORDER BY item_count DESC, t.name
        LIMIT $1
        """
        return await self._fetch(query, limit)


class AutocompleteRepository(LoggingMixin):
    """Repository for autocomplete-related database operations."""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def _fetch(self, query: str, *args) -> List[Dict]:
        """Execute query and return results as list of dictionaries."""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(query, *args)
            return [dict(r) for r in results]
    
    async def get_suggestions(self, query: str, limit: int) -> List[Dict]:
        """
        Get autocomplete suggestions from items, speakers, and tags.
        Uses prefix matching first, then fuzzy search as fallback for typos.
        
        Args:
            query: Partial query text for prefix matching
            limit: Maximum number of suggestions to return
            
        Returns:
            List of suggestions with 'suggestion', 'type', and 'priority' fields
        """
        # First try prefix matching
        query_sql = """
        (
            SELECT title as suggestion, 'title' as type, 1 as priority
            FROM items
            WHERE lower(unaccent(title)) LIKE lower(unaccent($1)) || '%'
            AND status = 'published'
            LIMIT 3
        )
        UNION ALL
        (
            SELECT name as suggestion, 'speaker' as type, 2 as priority
            FROM speakers
            WHERE lower(unaccent(name)) LIKE lower(unaccent($1)) || '%'
            LIMIT 3
        )
        UNION ALL
        (
            SELECT name as suggestion, 'tag' as type, 3 as priority
            FROM tags
            WHERE lower(unaccent(name)) LIKE lower(unaccent($1)) || '%'
            LIMIT 3
        )
        ORDER BY priority, suggestion
        LIMIT $2
        """
        results = await self._fetch(query_sql, query, limit)
        
        # If prefix matching found results, return them
        if len(results) > 0:
            return results
        
        # Fallback to fuzzy search for typos (only for queries >= 3 chars)
        if len(query.strip()) >= 3:
            fuzzy_sql = """
            (
                SELECT title as suggestion, 'title' as type, 1 as priority,
                       similarity(lower(unaccent(title)), lower(unaccent($1))) as sim
                FROM items
                WHERE similarity(lower(unaccent(title)), lower(unaccent($1))) > 0.3
                  AND status = 'published'
                ORDER BY sim DESC
                LIMIT 3
            )
            UNION ALL
            (
                SELECT name as suggestion, 'speaker' as type, 2 as priority,
                       similarity(lower(unaccent(name)), lower(unaccent($1))) as sim
                FROM speakers
                WHERE similarity(lower(unaccent(name)), lower(unaccent($1))) > 0.3
                ORDER BY sim DESC
                LIMIT 3
            )
            UNION ALL
            (
                SELECT name as suggestion, 'tag' as type, 3 as priority,
                       similarity(lower(unaccent(name)), lower(unaccent($1))) as sim
                FROM tags
                WHERE similarity(lower(unaccent(name)), lower(unaccent($1))) > 0.3
                Order BY sim DESC
                LIMIT 3
            )
            ORDER BY priority, sim DESC
            LIMIT $2
            """
            fuzzy_results = await self._fetch(fuzzy_sql, query, limit)
            if len(fuzzy_results) > 0:
                # Remove 'sim' field from results
                return [{k: v for k, v in r.items() if k != 'sim'} for r in fuzzy_results]
        
        return results
