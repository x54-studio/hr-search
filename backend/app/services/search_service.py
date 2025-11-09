"""
Search service containing business logic for search operations.

Handles the orchestration of search algorithms, result ranking,
and business rules for the HR Search application.
"""

import time
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .embedding_service import EmbeddingService

from ..exceptions import (
    SearchError,
    ValidationError,
)
from ..logging_config import LoggingMixin, get_request_id
from ..config import settings
from ..repositories import (
    WebinarRepository,
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
        webinar_repo: WebinarRepository,
        category_repo: CategoryRepository,
        speaker_repo: SpeakerRepository,
        tag_repo: TagRepository,
        autocomplete_repo: AutocompleteRepository,
        embedding_repo: EmbeddingRepository,
        embedding_service: "EmbeddingService",
    ):
        """Initialize search service with required repositories."""
        self.webinar_repo = webinar_repo
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
            # Step 1: Quick fuzzy check for spell correction
            fuzzy_start = time.time()
            fuzzy_suggestions = await self.webinar_repo.search_fuzzy(
                query, limit=3, threshold=0.6
            )
            fuzzy_time = time.time() - fuzzy_start

            # If fuzzy finds close matches, extract corrected term
            if (
                fuzzy_suggestions
                and fuzzy_suggestions[0].get("similarity", 0) > 0.85
            ):
                corrected_query = self._extract_correction(
                    query, fuzzy_suggestions
                )
                if corrected_query != query:
                    self.log_info(
                        "Spell correction applied",
                        extra={
                            "original_query": query,
                            "corrected_query": corrected_query,
                            "fuzzy_duration_sec": round(fuzzy_time, 3),
                        },
                    )

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
            results = await self.webinar_repo.search_semantic(
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

            # If no semantic results, try fuzzy search as fallback
            if not results:
                self.log_warning(
                    "No semantic results found, trying fuzzy search fallback",
                    extra={"semantic_threshold": settings.SEMANTIC_THRESHOLD},
                )

                fuzzy_fallback_start = time.time()
                results = await self.webinar_repo.search_fuzzy(
                    corrected_query, limit, settings.FUZZY_THRESHOLD
                )

                fuzzy_fallback_time = time.time() - fuzzy_fallback_start
                self.log_info(
                    "Fuzzy search fallback completed",
                    extra={
                        "duration_sec": round(fuzzy_fallback_time, 3),
                        "results_count": len(results),
                    },
                )

            # If still no results, try speaker name search
            if not results:
                self.log_warning(
                    "No fuzzy results found, trying speaker name search",
                    extra={"query": corrected_query},
                )

                speaker_search_start = time.time()
                speaker_results = await self._search_by_speaker_name(
                    corrected_query, limit
                )

                speaker_search_time = time.time() - speaker_search_start
                self.log_info(
                    "Speaker name search completed",
                    extra={
                        "duration_sec": round(speaker_search_time, 3),
                        "results_count": len(speaker_results),
                    },
                )

                if speaker_results:
                    results = speaker_results

            total_time = time.time() - start_time
            self.log_info(
                "Search completed successfully",
                extra={
                    "total_duration_sec": round(total_time, 3),
                    "results_count": len(results),
                    "search_type": (
                        "semantic"
                        if results and "similarity" in results[0]
                        else "fuzzy"
                    ),
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

    async def get_webinar_details(self, webinar_id: str) -> Dict:
        """
        Get detailed information about a specific webinar.

        Args:
            webinar_id: UUID of the webinar

        Returns:
            Webinar details with speakers, tags, and category

        Raises:
            SearchError: If webinar not found
            SearchError: If operation fails
        """
        try:
            return await self.webinar_repo.get_by_id(webinar_id)
        except Exception as e:
            self.log_error(
                "Get webinar details operation failed",
                exception=e,
                extra={"webinar_id": webinar_id},
            )
            raise SearchError(
                f"Get webinar details operation failed: {str(e)}",
                search_type="webinar_details",
            )

    @cached(ttl=600, key_prefix="categories")
    async def get_categories(self) -> List[Dict]:
        """
        Get all categories with webinar counts.

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
        Get all speakers with webinar counts.

        Args:
            limit: Maximum number of speakers to return

        Returns:
            List of speakers with counts

        Raises:
            ValidationError: If limit is invalid
            SearchError: If operation fails
        """
        if limit < 1 or limit > 500:
            raise ValidationError(
                f"Limit must be between 1 and 500, got {limit}",
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
        Get all tags with webinar counts.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of tags with counts

        Raises:
            ValidationError: If limit is invalid
            SearchError: If operation fails
        """
        if limit < 1 or limit > 500:
            raise ValidationError(
                f"Limit must be between 1 and 500, got {limit}",
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

    async def list_webinars(
        self,
        category: Optional[str] = None,
        speaker: Optional[str] = None,
        tags: Optional[List[str]] = None,
        offset: int = 0,
        limit: int = 20,
        date_range: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Tuple[List[Dict], int]:
        """
        List webinars with optional filtering and pagination.

        Args:
            category: Filter by category slug
            speaker: Filter by speaker name
            tags: Filter by tag slugs
            offset: Number of records to skip
            limit: Maximum number of records
            date_range: Optional date range filter ('last_30_days', 'last_90_days', 'last_365_days')
            content_type: Optional content type filter ('webinar', 'pdf')

        Returns:
            Tuple of (webinar_list, total_count)

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

        if content_type and content_type not in ('webinar', 'pdf'):
            raise ValidationError(
                f"Invalid content_type: {content_type}. Must be one of: webinar, pdf",
                field="content_type",
                value=content_type,
            )

        try:
            if category:
                return await self.webinar_repo.get_by_category(
                    category, offset, limit, date_range, content_type
                )
            elif speaker:
                return await self.webinar_repo.get_by_speaker(
                    speaker, offset, limit, date_range, content_type
                )
            elif tags:
                return await self.webinar_repo.get_by_tags(tags, offset, limit, date_range, content_type)
            else:
                return await self.webinar_repo.get_recent(offset, limit, date_range, content_type)

        except Exception as e:
            self.log_error(
                "Database operation failed during webinar listing",
                exception=e,
                extra={
                    "category": category,
                    "speaker": speaker,
                    "tags": tags,
                    "offset": offset,
                    "limit": limit,
                    "date_range": date_range,
                    "content_type": content_type,
                },
            )
            raise SearchError(
                f"Failed to list webinars: {str(e)}",
                search_type="recent_webinars",
            ) from e

    def _extract_correction(
        self, original_query: str, fuzzy_results: List[Dict]
    ) -> str:
        """
        Extract spell-corrected query from fuzzy search results.

        Uses title words from top-matching webinars to identify correction.

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

    async def _search_by_speaker_name(
        self, query: str, limit: int
    ) -> List[Dict]:
        """
        Search for webinars by speaker name.

        Args:
            query: Search query (speaker name)
            limit: Maximum number of results

        Returns:
            List of webinar results matching the speaker name
        """
        try:
            # First, find speakers matching the query
            matching_speakers = await self.speaker_repo.search_by_name(
                query, limit=5
            )

            if not matching_speakers:
                return []

            # Get webinars for each matching speaker
            all_results = []
            seen_webinar_ids = set()

            for speaker in matching_speakers:
                speaker_name = speaker["suggestion"]
                
                # Get webinars for this speaker
                speaker_webinars, _ = await self.webinar_repo.get_by_speaker(
                    speaker_name, offset=0, limit=limit
                )

                # Add unique webinars to results
                for webinar in speaker_webinars:
                    if webinar["id"] not in seen_webinar_ids:
                        # Add similarity score for consistency with other search results
                        webinar["similarity"] = 0.8  # High similarity for exact speaker match
                        all_results.append(webinar)
                        seen_webinar_ids.add(webinar["id"])

                        # Stop if we have enough results
                        if len(all_results) >= limit:
                            break

                if len(all_results) >= limit:
                    break

            # Sort by recorded_date DESC to show most recent first
            all_results.sort(
                key=lambda x: x.get("recorded_date", ""), reverse=True
            )

            return all_results[:limit]

        except Exception as e:
            self.log_error(
                "Speaker name search failed",
                exception=e,
                extra={"query": query, "limit": limit},
            )
            return []
