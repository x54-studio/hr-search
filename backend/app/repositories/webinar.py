"""
Webinar repository for database operations related to webinars.

Handles all SQL queries for webinar data including search, filtering,
and relationship management with categories, speakers, and tags.
"""

import asyncpg
from typing import List, Dict, Tuple


class WebinarRepository:
    """Repository for webinar-related database operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def _fetch(self, query: str, *args) -> List[Dict]:
        """Execute query and return results as list of dictionaries."""
        async with self.pool.acquire() as conn:
            results = await conn.fetch(query, *args)
            return [dict(r) for r in results]

    async def _fetch_one(self, query: str, *args) -> Dict:
        """Execute query and return single result as dictionary."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, *args)
            return dict(result) if result else None

    async def search_semantic(
        self, embedding: List[float], limit: int, threshold: float
    ) -> List[Dict]:
        """
        Perform semantic search using vector similarity.

        Args:
            embedding: Query embedding vector as list of floats
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of webinar records with similarity scores
        """
        # Format embedding as string for PostgreSQL
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        query = """
        WITH vector_matches AS (
            SELECT 
                e.webinar_id,
                1 - (e.vector <=> $1::vector) as similarity
            FROM webinar_embeddings e
            WHERE 
                e.embedding_type = 'title'
                AND 1 - (e.vector <=> $1::vector) > $3
            ORDER BY similarity DESC
            LIMIT $2
        )
        SELECT 
            w.id, w.title, w.description, w.duration_ms, w.recorded_date,
            w.video_url, w.pdf_url,
            c.name as category_name,
            vm.similarity,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM vector_matches vm
        JOIN webinars w ON vm.webinar_id = w.id
        LEFT JOIN categories c ON w.category_id = c.id
        LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
        LEFT JOIN speakers s ON ws.speaker_id = s.id
        LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
        LEFT JOIN tags t ON wt.tag_id = t.id
        WHERE w.status = 'published'
        GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                 w.video_url, w.pdf_url, c.name, vm.similarity
        ORDER BY vm.similarity DESC
        """

        return await self._fetch(query, embedding_str, limit, threshold)

    async def search_fuzzy(
        self, query_text: str, limit: int, threshold: float
    ) -> List[Dict]:
        """
        Perform fuzzy text search using pg_trgm similarity.

        Args:
            query_text: Search query text
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of webinar records with similarity scores
        """
        query = """
        WITH title_matches AS (
            SELECT 
                w.id,
                similarity(lower(unaccent(w.title)), lower(unaccent($1))) as similarity
            FROM webinars w
            WHERE 
                similarity(lower(unaccent(w.title)), lower(unaccent($1))) > $3
                AND w.status = 'published'
            ORDER BY similarity DESC
            LIMIT $2
        )
        SELECT 
            w.id, w.title, w.description, w.duration_ms, w.recorded_date,
            w.video_url, w.pdf_url,
            c.name as category_name,
            tm.similarity,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM title_matches tm
        JOIN webinars w ON tm.id = w.id
        LEFT JOIN categories c ON w.category_id = c.id
        LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
        LEFT JOIN speakers s ON ws.speaker_id = s.id
        LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
        LEFT JOIN tags t ON wt.tag_id = t.id
        GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                 w.video_url, w.pdf_url, c.name, tm.similarity
        ORDER BY tm.similarity DESC
        """

        return await self._fetch(query, query_text, limit, threshold)

    async def get_by_id(self, webinar_id: str) -> Dict:
        """
        Get webinar details by ID with all related data.

        Args:
            webinar_id: UUID of the webinar

        Returns:
            Webinar record with speakers, tags, and category
        """
        query = """
        SELECT 
            w.id, w.title, w.description, w.duration_ms, w.recorded_date,
            w.video_url, w.pdf_url, w.status,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM webinars w
        LEFT JOIN categories c ON w.category_id = c.id
        LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
        LEFT JOIN speakers s ON ws.speaker_id = s.id
        LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
        LEFT JOIN tags t ON wt.tag_id = t.id
        WHERE w.id = $1
        GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                 w.video_url, w.pdf_url, w.status, c.name
        """

        result = await self._fetch_one(query, webinar_id)
        if not result:
            raise ValueError(f"Webinar not found: {webinar_id}")
        return result

    async def get_by_category(
        self, category_slug: str, offset: int, limit: int
    ) -> Tuple[List[Dict], int]:
        """
        Get webinars by category with pagination.

        Args:
            category_slug: Category slug identifier
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (webinar_list, total_count)
        """
        # Count total records
        count_query = """
        SELECT COUNT(*)
        FROM webinars w
        JOIN categories c ON w.category_id = c.id
        WHERE c.slug = $1
          AND w.status = 'published'
        """
        total_result = await self._fetch_one(count_query, category_slug)
        total = total_result['count'] if total_result else 0

        # Get paginated results
        data_query = """
        SELECT 
            w.id, w.title, w.description, w.duration_ms, w.recorded_date,
            w.video_url, w.pdf_url,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM webinars w
        JOIN categories c ON w.category_id = c.id
        LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
        LEFT JOIN speakers s ON ws.speaker_id = s.id
        LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
        LEFT JOIN tags t ON wt.tag_id = t.id
        WHERE c.slug = $1 
          AND w.status = 'published'
        GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                 w.video_url, w.pdf_url, c.name
        ORDER BY w.recorded_date DESC NULLS LAST
        LIMIT $2 OFFSET $3
        """

        results = await self._fetch(data_query, category_slug, limit, offset)
        return results, int(total)

    async def get_by_speaker(
        self, speaker_name: str, offset: int, limit: int
    ) -> Tuple[List[Dict], int]:
        """
        Get webinars by speaker with pagination.

        Args:
            speaker_name: Speaker name (partial match)
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (webinar_list, total_count)
        """
        # Count total records
        count_query = """
        SELECT COUNT(DISTINCT w.id)
        FROM webinars w
        JOIN webinar_speakers ws ON w.id = ws.webinar_id
        JOIN speakers s ON ws.speaker_id = s.id
        WHERE lower(s.name) LIKE '%' || lower($1) || '%'
          AND w.status = 'published'
        """
        total_result = await self._fetch_one(count_query, speaker_name)
        total = total_result['count'] if total_result else 0

        # Get paginated results
        data_query = """
        SELECT 
            w.id, w.title, w.description, w.duration_ms, w.recorded_date,
            w.video_url, w.pdf_url,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM webinars w
        JOIN webinar_speakers ws ON w.id = ws.webinar_id
        JOIN speakers s ON ws.speaker_id = s.id
        LEFT JOIN categories c ON w.category_id = c.id
        LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
        LEFT JOIN tags t ON wt.tag_id = t.id
        WHERE lower(s.name) LIKE '%' || lower($1) || '%'
          AND w.status = 'published'
        GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                 w.video_url, w.pdf_url, c.name
        ORDER BY w.recorded_date DESC NULLS LAST
        LIMIT $2 OFFSET $3
        """

        results = await self._fetch(data_query, speaker_name, limit, offset)
        return results, int(total)

    async def get_by_tags(
        self, tag_slugs: List[str], offset: int, limit: int
    ) -> Tuple[List[Dict], int]:
        """
        Get webinars by tags with pagination.

        Args:
            tag_slugs: List of tag slug identifiers
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (webinar_list, total_count)
        """
        # Count total records
        count_query = """
        SELECT COUNT(DISTINCT w.id)
        FROM webinars w
        JOIN webinar_tags wt ON w.id = wt.webinar_id
        JOIN tags t ON wt.tag_id = t.id
        WHERE t.slug = ANY($1::text[])
          AND w.status = 'published'
        """
        total_result = await self._fetch_one(count_query, tag_slugs)
        total = total_result['count'] if total_result else 0

        # Get paginated results
        data_query = """
        SELECT 
            w.id, w.title, w.description, w.duration_ms, w.recorded_date,
            w.video_url, w.pdf_url,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM webinars w
        JOIN webinar_tags wt ON w.id = wt.webinar_id
        JOIN tags t ON wt.tag_id = t.id
        LEFT JOIN categories c ON w.category_id = c.id
        LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
        LEFT JOIN speakers s ON ws.speaker_id = s.id
        WHERE t.slug = ANY($1::text[])
          AND w.status = 'published'
        GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                 w.video_url, w.pdf_url, c.name
        ORDER BY w.recorded_date DESC NULLS LAST
        LIMIT $2 OFFSET $3
        """

        results = await self._fetch(data_query, tag_slugs, limit, offset)
        return results, int(total)

    async def get_recent(
        self, offset: int, limit: int
    ) -> Tuple[List[Dict], int]:
        """
        Get most recent published webinars with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (webinar_list, total_count)
        """
        # Count total records
        count_query = """
        SELECT COUNT(*)
        FROM webinars w
        WHERE w.status = 'published'
        """
        total_result = await self._fetch_one(count_query)
        total = total_result['count'] if total_result else 0

        # Get paginated results
        data_query = """
        SELECT 
            w.id, w.title, w.description, w.duration_ms, w.recorded_date,
            w.video_url, w.pdf_url,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM webinars w
        LEFT JOIN categories c ON w.category_id = c.id
        LEFT JOIN webinar_speakers ws ON w.id = ws.webinar_id
        LEFT JOIN speakers s ON ws.speaker_id = s.id
        LEFT JOIN webinar_tags wt ON w.id = wt.webinar_id
        LEFT JOIN tags t ON wt.tag_id = t.id
        WHERE w.status = 'published'
        GROUP BY w.id, w.title, w.description, w.duration_ms, w.recorded_date,
                 w.video_url, w.pdf_url, c.name
        ORDER BY w.recorded_date DESC NULLS LAST, w.created_at DESC
        LIMIT $1 OFFSET $2
        """

        results = await self._fetch(data_query, limit, offset)
        return results, int(total)