"""
Item repository for database operations related to content items.

Handles all SQL queries for item data including search, filtering,
and relationship management with categories, speakers, and tags.
"""

import asyncpg
from typing import List, Dict, Tuple, Optional
from datetime import date, timedelta


class ItemRepository:
    """Repository for item-related database operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    def _parse_date_range(self, date_range: str) -> Tuple[date, date]:
        """
        Parse date range string into start and end dates.

        Args:
            date_range: One of 'last_30_days', 'last_90_days', 'last_365_days'

        Returns:
            Tuple of (start_date, end_date) where end_date is today

        Raises:
            ValueError: If date_range is not recognized
        """
        today = date.today()
        if date_range == 'last_30_days':
            start_date = today - timedelta(days=30)
        elif date_range == 'last_90_days':
            start_date = today - timedelta(days=90)
        elif date_range == 'last_365_days':
            start_date = today - timedelta(days=365)
        else:
            raise ValueError(f"Invalid date_range: {date_range}. Must be one of: last_30_days, last_90_days, last_365_days")
        return start_date, today

    def _get_source_type_condition(self, source_type: Optional[str]) -> str:
        """
        Get SQL condition for source type filtering.

        Args:
            source_type: Source type string (e.g. 'webinar', 'youtube') or None

        Returns:
            SQL WHERE condition string for source type filtering
        """
        if source_type:
            return f" AND i.source_type = '{source_type}'"
        return ""

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
            List of item records with similarity scores
        """
        # Format embedding as string for PostgreSQL
        embedding_str = f"[{','.join(map(str, embedding))}]"

        query = """
        WITH vector_matches AS (
            SELECT
                e.item_id,
                1 - (e.vector <=> $1::vector) as similarity
            FROM item_embeddings e
            WHERE
                e.embedding_type = 'title'
                AND 1 - (e.vector <=> $1::vector) > $3
            ORDER BY similarity DESC
            LIMIT $2
        )
        SELECT
            i.id, i.title, i.description, i.duration_ms, i.published_date,
            i.source_url, i.source_type, i.metadata,
            c.name as category_name,
            vm.similarity,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM vector_matches vm
        JOIN items i ON vm.item_id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_speakers isp ON i.id = isp.item_id
        LEFT JOIN speakers s ON isp.speaker_id = s.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE i.status = 'published'
        GROUP BY i.id, i.title, i.description, i.duration_ms, i.published_date,
                 i.source_url, i.source_type, i.metadata, c.name, vm.similarity
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
            List of item records with similarity scores
        """
        query = """
        WITH title_matches AS (
            SELECT
                i.id,
                similarity(lower(unaccent(i.title)), lower(unaccent($1))) as similarity
            FROM items i
            WHERE
                similarity(lower(unaccent(i.title)), lower(unaccent($1))) > $3
                AND i.status = 'published'
            ORDER BY similarity DESC
            LIMIT $2
        )
        SELECT
            i.id, i.title, i.description, i.duration_ms, i.published_date,
            i.source_url, i.source_type, i.metadata,
            c.name as category_name,
            tm.similarity,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM title_matches tm
        JOIN items i ON tm.id = i.id
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_speakers isp ON i.id = isp.item_id
        LEFT JOIN speakers s ON isp.speaker_id = s.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        GROUP BY i.id, i.title, i.description, i.duration_ms, i.published_date,
                 i.source_url, i.source_type, i.metadata, c.name, tm.similarity
        ORDER BY tm.similarity DESC
        """

        return await self._fetch(query, query_text, limit, threshold)

    async def get_by_id(self, item_id: str) -> Dict:
        """
        Get item details by ID with all related data.

        Args:
            item_id: UUID of the item

        Returns:
            Item record with speakers, tags, and category
        """
        query = """
        SELECT
            i.id, i.title, i.description, i.duration_ms, i.published_date,
            i.source_url, i.source_type, i.metadata, i.status,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM items i
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_speakers isp ON i.id = isp.item_id
        LEFT JOIN speakers s ON isp.speaker_id = s.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE i.id = $1
        GROUP BY i.id, i.title, i.description, i.duration_ms, i.published_date,
                 i.source_url, i.source_type, i.metadata, i.status, c.name
        """

        result = await self._fetch_one(query, item_id)
        if not result:
            raise ValueError(f"Item not found: {item_id}")
        return result

    async def get_by_category(
        self, category_slug: str, offset: int, limit: int, date_range: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get items by category with pagination.

        Args:
            category_slug: Category slug identifier
            offset: Number of records to skip
            limit: Maximum number of records to return
            date_range: Optional date range filter
            source_type: Optional source type filter

        Returns:
            Tuple of (item_list, total_count)
        """
        date_condition = ""
        date_params = []
        if date_range:
            start_date, end_date = self._parse_date_range(date_range)
            date_condition = " AND i.published_date >= $2 AND i.published_date <= $3"
            date_params = [start_date, end_date]

        type_condition = self._get_source_type_condition(source_type)

        count_query = f"""
        SELECT COUNT(*)
        FROM items i
        JOIN categories c ON i.category_id = c.id
        WHERE c.slug = $1
          AND i.status = 'published'{date_condition}{type_condition}
        """
        count_args = [category_slug] + date_params
        total_result = await self._fetch_one(count_query, *count_args)
        total = total_result['count'] if total_result else 0

        param_offset = 1 + len(date_params)
        data_query = f"""
        SELECT
            i.id, i.title, i.description, i.duration_ms, i.published_date,
            i.source_url, i.source_type, i.metadata,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM items i
        JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_speakers isp ON i.id = isp.item_id
        LEFT JOIN speakers s ON isp.speaker_id = s.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE c.slug = $1
          AND i.status = 'published'{date_condition}{type_condition}
        GROUP BY i.id, i.title, i.description, i.duration_ms, i.published_date,
                 i.source_url, i.source_type, i.metadata, c.name
        ORDER BY i.published_date DESC NULLS LAST
        LIMIT ${param_offset + 1} OFFSET ${param_offset + 2}
        """

        results = await self._fetch(data_query, category_slug, *date_params, limit, offset)
        return results, int(total)

    async def get_by_speaker(
        self, speaker_name: str, offset: int, limit: int, date_range: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get items by speaker with pagination.

        Args:
            speaker_name: Speaker name (partial match)
            offset: Number of records to skip
            limit: Maximum number of records to return
            date_range: Optional date range filter
            source_type: Optional source type filter

        Returns:
            Tuple of (item_list, total_count)
        """
        date_condition = ""
        date_params = []
        if date_range:
            start_date, end_date = self._parse_date_range(date_range)
            date_condition = " AND i.published_date >= $2 AND i.published_date <= $3"
            date_params = [start_date, end_date]

        type_condition = self._get_source_type_condition(source_type)

        count_query = f"""
        SELECT COUNT(DISTINCT i.id)
        FROM items i
        JOIN item_speakers isp ON i.id = isp.item_id
        JOIN speakers s ON isp.speaker_id = s.id
        WHERE lower(s.name) LIKE '%' || lower($1) || '%'
          AND i.status = 'published'{date_condition}{type_condition}
        """
        count_args = [speaker_name] + date_params
        total_result = await self._fetch_one(count_query, *count_args)
        total = total_result['count'] if total_result else 0

        param_offset = 1 + len(date_params)
        data_query = f"""
        SELECT
            i.id, i.title, i.description, i.duration_ms, i.published_date,
            i.source_url, i.source_type, i.metadata,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM items i
        JOIN item_speakers isp ON i.id = isp.item_id
        JOIN speakers s ON isp.speaker_id = s.id
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_tags it ON i.id = it.item_id
        LEFT JOIN tags t ON it.tag_id = t.id
        WHERE lower(s.name) LIKE '%' || lower($1) || '%'
          AND i.status = 'published'{date_condition}{type_condition}
        GROUP BY i.id, i.title, i.description, i.duration_ms, i.published_date,
                 i.source_url, i.source_type, i.metadata, c.name
        ORDER BY i.published_date DESC NULLS LAST
        LIMIT ${param_offset + 1} OFFSET ${param_offset + 2}
        """

        results = await self._fetch(data_query, speaker_name, *date_params, limit, offset)
        return results, int(total)

    async def get_by_tags(
        self, tag_slugs: List[str], offset: int, limit: int, date_range: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get items by tags with pagination.

        Args:
            tag_slugs: List of tag slug identifiers
            offset: Number of records to skip
            limit: Maximum number of records to return
            date_range: Optional date range filter
            source_type: Optional source type filter

        Returns:
            Tuple of (item_list, total_count)
        """
        date_condition = ""
        date_params = []
        if date_range:
            start_date, end_date = self._parse_date_range(date_range)
            date_condition = " AND i.published_date >= $2 AND i.published_date <= $3"
            date_params = [start_date, end_date]

        type_condition = self._get_source_type_condition(source_type)

        count_query = f"""
        SELECT COUNT(DISTINCT i.id)
        FROM items i
        JOIN item_tags it ON i.id = it.item_id
        JOIN tags t ON it.tag_id = t.id
        WHERE t.slug = ANY($1::text[])
          AND i.status = 'published'{date_condition}{type_condition}
        """
        count_args = [tag_slugs] + date_params
        total_result = await self._fetch_one(count_query, *count_args)
        total = total_result['count'] if total_result else 0

        param_offset = 1 + len(date_params)
        data_query = f"""
        SELECT
            i.id, i.title, i.description, i.duration_ms, i.published_date,
            i.source_url, i.source_type, i.metadata,
            c.name as category_name,
            array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
            array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
        FROM items i
        JOIN item_tags it ON i.id = it.item_id
        JOIN tags t ON it.tag_id = t.id
        LEFT JOIN categories c ON i.category_id = c.id
        LEFT JOIN item_speakers isp ON i.id = isp.item_id
        LEFT JOIN speakers s ON isp.speaker_id = s.id
        WHERE t.slug = ANY($1::text[])
          AND i.status = 'published'{date_condition}{type_condition}
        GROUP BY i.id, i.title, i.description, i.duration_ms, i.published_date,
                 i.source_url, i.source_type, i.metadata, c.name
        ORDER BY i.published_date DESC NULLS LAST
        LIMIT ${param_offset + 1} OFFSET ${param_offset + 2}
        """

        results = await self._fetch(data_query, tag_slugs, *date_params, limit, offset)
        return results, int(total)

    async def get_recent(
        self, offset: int, limit: int, date_range: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> Tuple[List[Dict], int]:
        """
        Get most recent published items with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return
            date_range: Optional date range filter
            source_type: Optional source type filter

        Returns:
            Tuple of (item_list, total_count)
        """
        date_condition = ""
        date_params = []
        if date_range:
            start_date, end_date = self._parse_date_range(date_range)
            date_condition = " AND i.published_date >= $1 AND i.published_date <= $2"
            date_params = [start_date, end_date]

        type_condition = self._get_source_type_condition(source_type)

        count_query = f"""
        SELECT COUNT(*)
        FROM items i
        WHERE i.status = 'published'{date_condition}{type_condition}
        """
        total_result = await self._fetch_one(count_query, *date_params) if date_params else await self._fetch_one(count_query)
        total = total_result['count'] if total_result else 0

        if date_params:
            data_query = f"""
            SELECT
                i.id, i.title, i.description, i.duration_ms, i.published_date,
                i.source_url, i.source_type, i.metadata,
                c.name as category_name,
                array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM items i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN item_speakers isp ON i.id = isp.item_id
            LEFT JOIN speakers s ON isp.speaker_id = s.id
            LEFT JOIN item_tags it ON i.id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE i.status = 'published'{date_condition}{type_condition}
            GROUP BY i.id, i.title, i.description, i.duration_ms, i.published_date,
                     i.source_url, i.source_type, i.metadata, c.name
            ORDER BY i.published_date DESC NULLS LAST, i.created_at DESC
            LIMIT $3 OFFSET $4
            """
            results = await self._fetch(data_query, *date_params, limit, offset)
        else:
            data_query = f"""
            SELECT
                i.id, i.title, i.description, i.duration_ms, i.published_date,
                i.source_url, i.source_type, i.metadata,
                c.name as category_name,
                array_agg(DISTINCT s.name) FILTER (WHERE s.name IS NOT NULL) as speakers,
                array_agg(DISTINCT t.name) FILTER (WHERE t.name IS NOT NULL) as tags
            FROM items i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN item_speakers isp ON i.id = isp.item_id
            LEFT JOIN speakers s ON isp.speaker_id = s.id
            LEFT JOIN item_tags it ON i.id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE i.status = 'published'{type_condition}
            GROUP BY i.id, i.title, i.description, i.duration_ms, i.published_date,
                     i.source_url, i.source_type, i.metadata, c.name
            ORDER BY i.published_date DESC NULLS LAST, i.created_at DESC
            LIMIT $1 OFFSET $2
            """
            results = await self._fetch(data_query, limit, offset)

        return results, int(total)
