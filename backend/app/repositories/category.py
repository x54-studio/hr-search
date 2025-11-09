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
        Get all categories with webinar counts.
        
        Returns:
            List of categories with id, name, slug, and webinar_count
        """
        query = """
        SELECT 
            c.id, c.name, c.slug,
            COUNT(w.id) as webinar_count
        FROM categories c
        LEFT JOIN webinars w ON c.id = w.category_id AND w.status = 'published'
        GROUP BY c.id, c.name, c.slug
        ORDER BY c.name
        """
        return await self._fetch(query)


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
        Get all speakers with webinar counts.
        
        Args:
            limit: Maximum number of speakers to return
            
        Returns:
            List of speakers with id, name, bio, and webinar_count
        """
        query = """
        SELECT 
            s.id, s.name, s.bio,
            COUNT(ws.webinar_id) as webinar_count
        FROM speakers s
        LEFT JOIN webinar_speakers ws ON s.id = ws.speaker_id
        LEFT JOIN webinars w ON ws.webinar_id = w.id AND w.status = 'published'
        GROUP BY s.id, s.name, s.bio
        ORDER BY webinar_count DESC, s.name
        LIMIT $1
        """
        return await self._fetch(query, limit)
    
    async def search_by_name(self, name: str, limit: int) -> List[Dict]:
        """
        Search speakers by name using trigram similarity.
        
        Args:
            name: Speaker name to search for
            limit: Maximum number of results to return
            
        Returns:
            List of speakers with name as 'suggestion' and similarity score
        """
        query = """
        SELECT 
            s.id, s.name as suggestion,
            similarity(lower(unaccent(s.name)), lower(unaccent($1))) as similarity
        FROM speakers s
        WHERE similarity(lower(unaccent(s.name)), lower(unaccent($1))) > 0.3
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
    
    async def get_all_with_counts(self, limit: int) -> List[Dict]:
        """
        Get all tags with webinar counts.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of tags with id, name, slug, and webinar_count
        """
        query = """
        SELECT 
            t.id, t.name, t.slug,
            COUNT(wt.webinar_id) as webinar_count
        FROM tags t
        LEFT JOIN webinar_tags wt ON t.id = wt.tag_id
        LEFT JOIN webinars w ON wt.webinar_id = w.id AND w.status = 'published'
        GROUP BY t.id, t.name, t.slug
        ORDER BY webinar_count DESC, t.name
        LIMIT $1
        """
        return await self._fetch(query, limit)
    
    async def get_popular(self, limit: int) -> List[Dict]:
        """
        Get popular tags ordered by usage count.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of popular tags with id, name, slug, and webinar_count
        """
        query = """
        SELECT 
            t.id, t.name, t.slug,
            COUNT(wt.webinar_id) as webinar_count
        FROM tags t
        JOIN webinar_tags wt ON t.id = wt.tag_id
        JOIN webinars w ON wt.webinar_id = w.id AND w.status = 'published'
        GROUP BY t.id, t.name, t.slug
        HAVING COUNT(wt.webinar_id) > 0
        ORDER BY webinar_count DESC, t.name
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
        Get autocomplete suggestions from webinars, speakers, and tags.
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
            SELECT title as suggestion, 'webinar' as type, 1 as priority
            FROM webinars
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
                SELECT title as suggestion, 'webinar' as type, 1 as priority,
                       similarity(lower(unaccent(title)), lower(unaccent($1))) as sim
                FROM webinars
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
                ORDER BY sim DESC
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
