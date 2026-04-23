"""
Search service containing business logic for search operations.

Handles the orchestration of search algorithms, result ranking,
and business rules for the Search application.
"""

import time
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .embedding_service import EmbeddingService

from ..exceptions import (
    SearchException,
    SearchError,
    ValidationError,
)
from ..logging_config import LoggingMixin, get_request_id
from ..config import settings, ALLOWED_SOURCE_TYPES
from ..repositories import (
    ItemRepository,
    CategoryRepository,
    SpeakerRepository,
    TagRepository,
    AutocompleteRepository,
    EmbeddingRepository,
)
from ..cache import cached


class SearchService(LoggingMixin):
    """Service for search-related business logic."""

    def __init__(
        self,
        item_repo: ItemRepository,
        category_repo: CategoryRepository,
        speaker_repo: SpeakerRepository,
        tag_repo: TagRepository,
        autocomplete_repo: AutocompleteRepository,
        embedding_repo: EmbeddingRepository,
        embedding_service: "EmbeddingService",
    ):
        """Initialize search service with required repositories."""
        self.item_repo = item_repo
        self.category_repo = category_repo
        self.speaker_repo = speaker_repo
        self.tag_repo = tag_repo
        self.autocomplete_repo = autocomplete_repo
        self.embedding_repo = embedding_repo
        self.embedding_service = embedding_service

    @cached(ttl=60, key_prefix="search")
    async def search(
        self, query: str, limit: int = 20, debug: bool = False
    ) -> Dict:
        """
        Perform spell-corrected semantic search.

        Uses a single fuzzy search call for both spell correction and fallback:
        1. Fuzzy search with full parameters (limit, dynamic threshold)
        2. Extract corrected query from fuzzy results if similarity > 0.85
        3. Semantic search with corrected query
        4. If no semantic results, use fuzzy results as fallback

        Args:
            query: Search query text
            limit: Maximum number of results
            debug: Enable debug logging

        Returns:
            Dict containing results, corrected_query, and original_query

        Raises:
            ValidationError: If query is invalid
            SearchError: If search operation fails
        """
        start_time = time.time()

        # Input validation
        if not query or not query.strip():
            raise ValidationError(
                "Query cannot be empty", field="query", value=query
            )

        if len(query) > 200:
            raise ValidationError(
                "Query too long (max 200 characters)",
                field="query",
                value=len(query),
            )

        if limit < 1 or limit > 50:
            raise ValidationError(
                f"Limit must be between 1 and 50, got {limit}",
                field="limit",
                value=limit,
            )

        query = query[:200].strip()
        corrected_query = query

        self.log_info(
            "Starting spell-corrected semantic search",
            extra={
                "query": query,
                "limit": limit,
                "semantic_threshold": settings.SEMANTIC_THRESHOLD,
                "fuzzy_threshold": settings.FUZZY_THRESHOLD,
                "debug": debug,
                "request_id": get_request_id(),
            },
        )

        try:
            # Entity gate: check if the query matches a known speaker, tag,
            # or category. Pick the best match across all three. If above
            # ENTITY_MATCH_THRESHOLD, return entity-filtered results instead
            # of semantic search (embeddings rank entity-name queries poorly).
            entity_result = await self._try_entity_gate(query, limit)
            if entity_result:
                return entity_result

            # Step 1: Fuzzy search with full parameters (for spell correction + potential fallback)
            # Lower threshold for short queries (better typo tolerance)
            # Short words in long titles have lower similarity scores
            # For queries < 8 characters, use 0.1 instead of 0.2
            fuzzy_threshold = settings.FUZZY_THRESHOLD
            if len(query.strip()) < 8:
                fuzzy_threshold = 0.1

            fuzzy_start = time.time()
            fuzzy_results = await self.item_repo.search_fuzzy(
                query, limit=limit, threshold=fuzzy_threshold
            )
            fuzzy_time = time.time() - fuzzy_start

            # Extract corrected query from fuzzy results
            if fuzzy_results and fuzzy_results[0].get("similarity", 0) > 0.85:
                corrected_query = self._extract_correction(query, fuzzy_results)
                if corrected_query != query:
                    self.log_info(
                        "Spell correction applied",
                        extra={
                            "original_query": query,
                            "corrected_query": corrected_query,
                            "fuzzy_duration_sec": round(fuzzy_time, 3),
                        },
                    )
            else:
                corrected_query = query

            # Step 2: Always run semantic search (with corrected query)
            embedding_start = time.time()
            query_embedding = await self.embedding_service.generate_embedding(
                corrected_query
            )
            embedding_time = time.time() - embedding_start

            self.log_info(
                "Embedding generated",
                extra={
                    "duration_sec": round(embedding_time, 3),
                    "dimensions": len(query_embedding),
                    "query_used": corrected_query,
                },
            )

            # Convert embedding list to PostgreSQL vector format
            # The asyncpg codec will handle the conversion automatically

            # Semantic search with corrected query
            semantic_start = time.time()
            results = await self.item_repo.search_semantic(
                query_embedding, limit, settings.SEMANTIC_THRESHOLD
            )

            semantic_time = time.time() - semantic_start
            self.log_info(
                "Semantic search completed",
                extra={
                    "duration_sec": round(semantic_time, 3),
                    "results_count": len(results),
                },
            )

            # If no semantic results, use fuzzy results (already fetched)
            search_type = "semantic"
            if not results:
                self.log_warning(
                    "No semantic results found, using fuzzy search results",
                    extra={"semantic_threshold": settings.SEMANTIC_THRESHOLD},
                )
                results = fuzzy_results
                search_type = "fuzzy"

            # If still no results, try entity name search as last resort
            if not results:
                self.log_warning(
                    "No fuzzy results found, trying entity name fallback",
                    extra={"query": corrected_query},
                )

                entity_fallback = await self._try_entity_gate(corrected_query, limit)
                if entity_fallback:
                    results = entity_fallback["results"]

            total_time = time.time() - start_time
            self.log_info(
                "Search completed successfully",
                extra={
                    "total_duration_sec": round(total_time, 3),
                    "results_count": len(results),
                    "search_type": search_type,
                    "original_query": query,
                    "corrected_query": corrected_query,
                    "correction_applied": corrected_query != query,
                    "request_id": get_request_id(),
                },
            )

            return {
                "results": results,
                "corrected_query": (
                    corrected_query if corrected_query != query else None
                ),
                "original_query": query,
                "count": len(results),
            }

        except ValidationError:
            raise
        except Exception as e:
            self.log_error(
                "Search operation failed",
                exception=e,
                extra={"query": query, "limit": limit},
            )
            raise SearchError(
                f"Search operation failed: {str(e)}",
                search_type="unknown",
                cause=e,
            )

    async def autocomplete(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Get autocomplete suggestions.

        Args:
            query: Partial query text
            limit: Maximum number of suggestions

        Returns:
            List of suggestions with type and priority

        Raises:
            ValidationError: If query is invalid
            SearchError: If autocomplete operation fails
        """
        if not query or not query.strip():
            raise ValidationError(
                "Query cannot be empty", field="query", value=query
            )

        if limit < 1 or limit > 20:
            raise ValidationError(
                f"Limit must be between 1 and 20, got {limit}",
                field="limit",
                value=limit,
            )

        query = query.strip()

        try:
            suggestions = await self.autocomplete_repo.get_suggestions(
                query, limit
            )
            return suggestions

        except Exception as e:
            self.log_error(
                "Database operation failed during autocomplete",
                exception=e,
                extra={"query": query, "limit": limit},
            )
            raise SearchError(
                f"Autocomplete operation failed: {str(e)}",
                search_type="autocomplete",
                cause=e,
            )

    async def get_item_details(self, item_id: str) -> Dict:
        """
        Get detailed information about a specific item.

        Args:
            item_id: UUID of the item

        Returns:
            Item details with speakers, tags, and category

        Raises:
            SearchError: If item not found or operation fails
        """
        try:
            return await self.item_repo.get_by_id(item_id)
        except SearchException:
            raise
        except Exception as e:
            self.log_error(
                "Get item details operation failed",
                exception=e,
                extra={"item_id": item_id},
            )
            raise SearchError(
                f"Get item details operation failed: {str(e)}",
                search_type="item_details",
            )

    @cached(ttl=600, key_prefix="categories")
    async def get_categories(self) -> List[Dict]:
        """
        Get all categories with item counts.

        Returns:
            List of categories with counts

        Raises:
            SearchError: If operation fails
        """
        try:
            return await self.category_repo.get_all_with_counts()
        except Exception as e:
            self.log_error(
                "Database operation failed during categories retrieval",
                exception=e,
            )
            raise SearchError(
                f"Failed to get categories: {str(e)}", search_type="categories"
            )

    @cached(ttl=300, key_prefix="speakers")
    async def get_speakers(self, limit: int = 100) -> List[Dict]:
        """
        Get all speakers with item counts.

        Args:
            limit: Maximum number of speakers to return

        Returns:
            List of speakers with counts

        Raises:
            ValidationError: If limit is invalid
            SearchError: If operation fails
        """
        if limit < 1 or limit > 100:
            raise ValidationError(
                f"Limit must be between 1 and 100, got {limit}",
                field="limit",
                value=limit,
            )

        try:
            return await self.speaker_repo.get_all_with_counts(limit)
        except Exception as e:
            self.log_error(
                "Database operation failed during speakers retrieval",
                exception=e,
                extra={"limit": limit},
            )
            raise SearchError(
                f"Failed to get speakers: {str(e)}", search_type="speakers"
            ) from e

    @cached(ttl=300, key_prefix="tags")
    async def get_tags(self, limit: int = 100) -> List[Dict]:
        """
        Get all tags with item counts.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of tags with counts

        Raises:
            ValidationError: If limit is invalid
            SearchError: If operation fails
        """
        if limit < 1 or limit > 100:
            raise ValidationError(
                f"Limit must be between 1 and 100, got {limit}",
                field="limit",
                value=limit,
            )

        try:
            return await self.tag_repo.get_all_with_counts(limit)
        except Exception as e:
            self.log_error(
                "Database operation failed during tags retrieval",
                exception=e,
                extra={"limit": limit},
            )
            raise SearchError(
                f"Failed to get tags: {str(e)}", search_type="tags"
            ) from e

    @cached(ttl=300, key_prefix="popular_tags")
    async def get_popular_tags(self, limit: int = 20) -> List[Dict]:
        """
        Get most used tags ordered by usage count.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of popular tags with usage counts

        Raises:
            ValidationError: If limit is invalid
            SearchError: If operation fails
        """
        if limit < 1 or limit > 50:
            raise ValidationError(
                f"Limit must be between 1 and 50, got {limit}",
                field="limit",
                value=limit,
            )

        try:
            return await self.tag_repo.get_popular(limit)
        except Exception as e:
            self.log_error(
                "Database operation failed during popular tags retrieval",
                exception=e,
                extra={"limit": limit},
            )
            raise SearchError(
                f"Failed to get popular tags: {str(e)}",
                search_type="popular_tags",
            ) from e

    async def list_items(
        self,
        category: Optional[str] = None,
        speaker: Optional[str] = None,
        tags: Optional[List[str]] = None,
        offset: int = 0,
        limit: int = 20,
        date_range: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> Tuple[List[Dict], int]:
        """
        List items with optional filtering and pagination.

        Args:
            category: Filter by category slug
            speaker: Filter by speaker name
            tags: Filter by tag slugs
            offset: Number of records to skip
            limit: Maximum number of records
            date_range: Optional date range filter ('last_30_days', 'last_90_days', 'last_365_days')
            source_type: Optional source type filter (e.g. 'webinar', 'youtube')

        Returns:
            Tuple of (item_list, total_count)

        Raises:
            ValidationError: If parameters are invalid
            SearchError: If operation fails
        """
        if offset < 0:
            raise ValidationError(
                "Offset must be non-negative", field="offset", value=offset
            )

        if limit < 1 or limit > 50:
            raise ValidationError(
                f"Limit must be between 1 and 50, got {limit}",
                field="limit",
                value=limit,
            )

        if date_range and date_range not in ('last_30_days', 'last_90_days', 'last_365_days'):
            raise ValidationError(
                f"Invalid date_range: {date_range}. Must be one of: last_30_days, last_90_days, last_365_days",
                field="date_range",
                value=date_range,
            )

        if source_type and source_type not in ALLOWED_SOURCE_TYPES:
            raise ValidationError(
                f"Invalid source_type: {source_type}. Must be one of: {', '.join(ALLOWED_SOURCE_TYPES)}",
                field="source_type",
                value=source_type,
            )

        try:
            if category:
                return await self.item_repo.get_by_category(
                    category, offset, limit, date_range, source_type
                )
            elif speaker:
                return await self.item_repo.get_by_speaker(
                    speaker, offset, limit, date_range, source_type
                )
            elif tags:
                return await self.item_repo.get_by_tags(tags, offset, limit, date_range, source_type)
            else:
                return await self.item_repo.get_recent(offset, limit, date_range, source_type)

        except Exception as e:
            self.log_error(
                "Database operation failed during item listing",
                exception=e,
                extra={
                    "category": category,
                    "speaker": speaker,
                    "tags": tags,
                    "offset": offset,
                    "limit": limit,
                    "date_range": date_range,
                    "source_type": source_type,
                },
            )
            raise SearchError(
                f"Failed to list items: {str(e)}",
                search_type="list_items",
            ) from e

    def _extract_correction(
        self, original_query: str, fuzzy_results: List[Dict]
    ) -> str:
        """
        Extract spell-corrected query from fuzzy search results.

        Uses title words from top-matching items to identify correction.

        Args:
            original_query: The original search query
            fuzzy_results: List of fuzzy search results

        Returns:
            Corrected query string
        """
        if (
            not fuzzy_results
            or not fuzzy_results[0].get("similarity", 0) > 0.85
        ):
            return original_query

        best_title = fuzzy_results[0].get("title", "")
        if not best_title:
            return original_query

        # Find closest matching word in title
        query_words = original_query.lower().split()
        corrected_words = []

        for query_word in query_words:
            best_match = query_word
            best_ratio = 0.0

            for title_word in best_title.lower().split():
                ratio = self._is_typo_of(query_word, title_word)
                if ratio > best_ratio and ratio > 0.85:
                    best_match = title_word
                    best_ratio = ratio

            corrected_words.append(best_match)

        corrected_query = " ".join(corrected_words)

        # Only return correction if it's significantly different
        if corrected_query.lower() != original_query.lower():
            return corrected_query

        return original_query

    def _is_typo_of(
        self, word1: str, word2: str, threshold: float = 0.85
    ) -> float:
        """
        Check if word1 is likely a typo of word2 using sequence matching.

        Args:
            word1: First word to compare
            word2: Second word to compare
            threshold: Minimum similarity ratio to consider a match

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        from difflib import SequenceMatcher

        # Clean words (remove punctuation, normalize case)
        clean_word1 = "".join(c for c in word1.lower() if c.isalnum())
        clean_word2 = "".join(c for c in word2.lower() if c.isalnum())

        if not clean_word1 or not clean_word2:
            return 0.0

        # Use SequenceMatcher for similarity
        matcher = SequenceMatcher(None, clean_word1, clean_word2)
        ratio = matcher.ratio()

        return ratio

    async def _try_entity_gate(
        self, query: str, limit: int
    ) -> Optional[Dict]:
        """Check speakers, tags, and categories for a name match.

        Returns a full search response dict if the best match is above
        ENTITY_MATCH_THRESHOLD, otherwise None (caller falls through to
        semantic search).
        """
        threshold = settings.ENTITY_MATCH_THRESHOLD

        top_speaker = await self.speaker_repo.search_by_name(query, limit=1)
        top_tag = await self.tag_repo.search_by_name(query, limit=1)
        top_category = await self.category_repo.search_by_name(query, limit=1)

        candidates = []
        if top_speaker:
            candidates.append(("speaker", top_speaker[0]))
        if top_tag:
            candidates.append(("tag", top_tag[0]))
        if top_category:
            candidates.append(("category", top_category[0]))

        if not candidates:
            return None

        best_type, best_match = max(candidates, key=lambda c: c[1].get("similarity", 0))
        best_sim = best_match.get("similarity", 0)

        if best_sim < threshold:
            return None

        self.log_info(
            "Entity gate matched",
            extra={
                "query": query,
                "entity_type": best_type,
                "entity_name": best_match.get("suggestion"),
                "similarity": best_sim,
                "threshold": threshold,
            },
        )

        if best_type == "speaker":
            results = await self._items_for_speakers(query, limit)
        elif best_type == "tag":
            results = await self._items_for_tags(query, limit)
        else:
            results = await self._items_for_categories(query, limit)

        if not results:
            return None

        return {
            "results": results,
            "corrected_query": None,
            "original_query": query,
            "count": len(results),
            "matched_entity": {
                "type": best_type,
                "name": best_match.get("suggestion"),
                "similarity": round(best_sim, 3),
            },
        }

    def _filter_by_relative_threshold(self, matches: List[Dict]) -> List[Dict]:
        """Keep only matches within 10% of the best score.

        Prevents "Agnieszka Lewandowska" (1.0) from pulling in
        "Agnieszka Kamińska" (0.47) while still letting "agnies"
        (all at 0.857) keep all three Agnieszkas.
        """
        if not matches:
            return []
        best_sim = matches[0].get("similarity", 0)
        floor = max(settings.ENTITY_MATCH_THRESHOLD, best_sim * 0.9)
        return [m for m in matches if m.get("similarity", 0) >= floor]

    async def _items_for_speakers(self, query: str, limit: int) -> List[Dict]:
        """Return items for all speakers matching the query above threshold."""
        try:
            matches = await self.speaker_repo.search_by_name(query, limit=5)
            strong = self._filter_by_relative_threshold(matches)
            if not strong:
                return []

            all_results: List[Dict] = []
            seen_ids: set = set()
            for speaker in strong:
                items, _ = await self.item_repo.get_by_speaker(speaker["suggestion"], offset=0, limit=limit)
                for item in items:
                    if item["id"] not in seen_ids:
                        item["similarity"] = float(speaker.get("similarity", 0))
                        all_results.append(item)
                        seen_ids.add(item["id"])
            all_results.sort(key=lambda x: x.get("published_date", ""), reverse=True)
            return all_results[:limit]
        except Exception as e:
            self.log_error("Speaker entity search failed", exception=e)
            return []

    async def _items_for_tags(self, query: str, limit: int) -> List[Dict]:
        """Return items for all tags matching the query above threshold."""
        try:
            matches = await self.tag_repo.search_by_name(query, limit=5)
            strong = self._filter_by_relative_threshold(matches)
            if not strong:
                return []

            slugs = [t["slug"] for t in strong]
            items, _ = await self.item_repo.get_by_tags(slugs, offset=0, limit=limit)
            best_sim = max(t.get("similarity", 0) for t in strong)
            for item in items:
                item["similarity"] = float(best_sim)
            return items
        except Exception as e:
            self.log_error("Tag entity search failed", exception=e)
            return []

    async def _items_for_categories(self, query: str, limit: int) -> List[Dict]:
        """Return items for all categories matching the query above threshold."""
        try:
            matches = await self.category_repo.search_by_name(query, limit=5)
            strong = self._filter_by_relative_threshold(matches)
            if not strong:
                return []

            all_results: List[Dict] = []
            seen_ids: set = set()
            for cat in strong:
                items, _ = await self.item_repo.get_by_category(cat["slug"], offset=0, limit=limit)
                for item in items:
                    if item["id"] not in seen_ids:
                        item["similarity"] = float(cat.get("similarity", 0))
                        all_results.append(item)
                        seen_ids.add(item["id"])
            all_results.sort(key=lambda x: x.get("published_date", ""), reverse=True)
            return all_results[:limit]
        except Exception as e:
            self.log_error("Category entity search failed", exception=e)
            return []
