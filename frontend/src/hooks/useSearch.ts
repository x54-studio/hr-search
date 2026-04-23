import { useState, useEffect, useCallback, useRef } from 'react';
import { apiService, ApiError } from '../services/api';
import type { SearchResult, AutocompleteSuggestion } from '../services/api';

export interface SearchState {
  query: string;
  results: SearchResult[];
  suggestions: AutocompleteSuggestion[];
  loading: boolean;
  error: string | null;
  errorCode: string | null;
  errorDetails: Record<string, any> | null;
  showSuggestions: boolean;
  hasSearched: boolean;
  correctedQuery: string | null;
  originalQuery: string | null;
  selectedCategories: string[];
  selectedSpeakers: string[];
  selectedTags: string[];
  selectedDateRange: string | null;
}

export interface SearchActions {
  handleQueryChange: (newQuery: string) => void;
  handleSubmit: () => void;
  handleSuggestionClick: (suggestion: string) => void;
  clearSearch: () => void;
  retrySearch: () => void;
  handleCategoryChange: (categories: string[]) => void;
  handleSpeakerChange: (speakers: string[]) => void;
  handleTagChange: (tags: string[]) => void;
  handleDateRangeChange: (range: string | null) => void;
  clearFilters: () => void;
  handleFilterDataReady: (data: { categoryMap: Map<string, string>; tagMap: Map<string, string> }) => void;
}

export function useSearch(): SearchState & SearchActions {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<Record<string, any> | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [correctedQuery, setCorrectedQuery] = useState<string | null>(null);
  const [originalQuery, setOriginalQuery] = useState<string | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedSpeakers, setSelectedSpeakers] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedDateRange, setSelectedDateRange] = useState<string | null>(null);
  const [categoryNameToSlug, setCategoryNameToSlug] = useState<Map<string, string>>(new Map());
  const [tagNameToSlug, setTagNameToSlug] = useState<Map<string, string>>(new Map());
  const searchAbortRef = useRef<AbortController | null>(null);

  const clearError = useCallback(() => {
    setError(null);
    setErrorCode(null);
    setErrorDetails(null);
  }, []);

  const setApiError = useCallback((apiError: ApiError) => {
    setError(apiError.message);
    setErrorCode(apiError.errorCode);
    setErrorDetails(apiError.details);
  }, []);

  const handleCategoryChange = useCallback((categories: string[]) => {
    setSelectedCategories(categories);
  }, []);

  const handleSpeakerChange = useCallback((speakers: string[]) => {
    setSelectedSpeakers(speakers);
  }, []);

  const handleTagChange = useCallback((tags: string[]) => {
    setSelectedTags(tags);
  }, []);

  const handleDateRangeChange = useCallback((range: string | null) => {
    setSelectedDateRange(range);
  }, []);

  const clearFilters = useCallback(() => {
    setSelectedCategories([]);
    setSelectedSpeakers([]);
    setSelectedTags([]);
    setSelectedDateRange(null);
  }, []);

  const handleFilterDataReady = useCallback((data: {
    categoryMap: Map<string, string>;
    tagMap: Map<string, string>;
  }) => {
    setCategoryNameToSlug(data.categoryMap);
    setTagNameToSlug(data.tagMap);
  }, []);

  // Client-side filter application
  const applyFilters = useCallback((results: SearchResult[]): SearchResult[] => {
    let filtered = [...results];

    if (selectedCategories.length > 0) {
      filtered = filtered.filter(r => {
        if (!r.category_name) return false;
        const categorySlug = categoryNameToSlug.get(r.category_name);
        if (!categorySlug) return false;
        return selectedCategories.includes(categorySlug);
      });
    }

    if (selectedSpeakers.length > 0) {
      filtered = filtered.filter(r =>
        r.speakers?.some(speaker =>
          selectedSpeakers.includes(speaker)
        ) ?? false
      );
    }

    if (selectedTags.length > 0) {
      filtered = filtered.filter(r =>
        r.tags?.some(tag => {
          const tagSlug = tagNameToSlug.get(tag);
          if (!tagSlug) return false;
          return selectedTags.includes(tagSlug);
        }) ?? false
      );
    }

    return filtered;
  }, [selectedCategories, selectedSpeakers, selectedTags, categoryNameToSlug, tagNameToSlug]);

  // Full search — fires on Enter / suggestion click / filter change
  const executeSearch = useCallback(async (searchQuery: string) => {
    const hasQuery = searchQuery.trim().length > 0;
    const hasFilters = selectedCategories.length > 0 || selectedSpeakers.length > 0 || selectedTags.length > 0 || selectedDateRange !== null;

    // Initial state (nothing searched yet and nothing requested): stay empty.
    // After hasSearched, clearing filters to "Wszystkie" should list all items,
    // not silently wipe the results — hence we only bail pre-search.
    if (!hasQuery && !hasFilters && !hasSearched) {
      setResults([]);
      setSuggestions([]);
      setCorrectedQuery(null);
      setOriginalQuery(null);
      clearError();
      return;
    }

    searchAbortRef.current?.abort();
    const controller = new AbortController();
    searchAbortRef.current = controller;
    const { signal } = controller;

    try {
      setLoading(true);
      setShowSuggestions(false);
      clearError();

      let searchResults: SearchResult[] = [];
      let searchCorrectedQuery: string | null = null;
      let searchOriginalQuery: string | null = null;

      if (hasQuery) {
        const searchResponse = await apiService.search(searchQuery, 20, signal);
        searchResults = searchResponse.results;
        searchCorrectedQuery = searchResponse.corrected_query || null;
        searchOriginalQuery = searchResponse.original_query || null;
      } else {
        setCorrectedQuery(null);
        setOriginalQuery(null);

        const hasEntityFilter = selectedCategories.length > 0 || selectedSpeakers.length > 0 || selectedTags.length > 0;

        if (!hasEntityFilter) {
          try {
            const response = await apiService.listItems({ date_range: selectedDateRange || undefined, limit: 50, signal });
            searchResults = response.items;
          } catch (err) {
            if (err instanceof DOMException && err.name === 'AbortError') throw err;
            console.error(`Failed to fetch items (date_range=${selectedDateRange ?? 'any'}):`, err);
            searchResults = [];
          }
        } else {
          const allResults: SearchResult[] = [];
          const seenIds = new Set<string>();

          for (const category of selectedCategories) {
            try {
              const response = await apiService.listItems({ category, date_range: selectedDateRange || undefined, limit: 50, signal });
              response.items.forEach(item => {
                if (!seenIds.has(item.id)) {
                  seenIds.add(item.id);
                  allResults.push(item);
                }
              });
            } catch (err) {
              if (err instanceof DOMException && err.name === 'AbortError') throw err;
              console.error(`Failed to fetch category "${category}":`, err);
            }
          }

          for (const speaker of selectedSpeakers) {
            try {
              const response = await apiService.listItems({ speaker, date_range: selectedDateRange || undefined, limit: 50, signal });
              response.items.forEach(item => {
                if (!seenIds.has(item.id)) {
                  seenIds.add(item.id);
                  allResults.push(item);
                }
              });
            } catch (err) {
              if (err instanceof DOMException && err.name === 'AbortError') throw err;
              console.error(`Failed to fetch speaker ${speaker}:`, err);
            }
          }

          for (const tag of selectedTags) {
            try {
              const response = await apiService.listItems({ tags: tag, date_range: selectedDateRange || undefined, limit: 50, signal });
              response.items.forEach(item => {
                if (!seenIds.has(item.id)) {
                  seenIds.add(item.id);
                  allResults.push(item);
                }
              });
            } catch (err) {
              if (err instanceof DOMException && err.name === 'AbortError') throw err;
              console.error(`Failed to fetch tag "${tag}":`, err);
            }
          }

          searchResults = allResults;
        }
      }

      if (signal.aborted) return;

      // Apply client-side filters
      if (hasFilters) {
        searchResults = applyFilters(searchResults);
      }

      setResults(searchResults);
      setCorrectedQuery(searchCorrectedQuery);
      setOriginalQuery(searchOriginalQuery);
      setHasSearched(true);
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      if (err instanceof ApiError) {
        setApiError(err);
      } else {
        setError(err instanceof Error ? err.message : 'Search failed');
        setErrorCode('UNKNOWN_ERROR');
        setErrorDetails({});
      }
      setResults([]);
      setCorrectedQuery(null);
      setOriginalQuery(null);
    } finally {
      if (!signal.aborted) {
        setLoading(false);
      }
    }
  }, [clearError, setApiError, selectedCategories, selectedSpeakers, selectedTags, selectedDateRange, applyFilters, hasSearched]);

  // Autocomplete only — fires on keystroke (250ms debounce)
  useEffect(() => {
    if (query.trim().length === 0) {
      setSuggestions([]);
      return;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(async () => {
      try {
        const response = await apiService.autocomplete(query, 10, controller.signal);
        setSuggestions(response.suggestions);
      } catch {
        // AbortError or network error — either way, don't update suggestions
      }
    }, 250);

    return () => {
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [query]);

  // Re-run search on filter changes (only if already searched)
  useEffect(() => {
    if (!hasSearched) {
      // If not searched yet but filters are active, run filter-only search
      const hasFilters = selectedCategories.length > 0 || selectedSpeakers.length > 0 || selectedTags.length > 0 || selectedDateRange !== null;
      if (hasFilters) {
        executeSearch(query);
      }
      return;
    }

    executeSearch(query);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategories, selectedSpeakers, selectedTags, selectedDateRange]);

  const handleQueryChange = useCallback((newQuery: string) => {
    setQuery(newQuery);
    setShowSuggestions(true);
    clearError();
  }, [clearError]);

  const handleSubmit = useCallback(() => {
    setShowSuggestions(false);
    if (query.trim()) {
      executeSearch(query);
    }
  }, [query, executeSearch]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    clearError();
    executeSearch(suggestion);
  }, [clearError, executeSearch]);

  const retrySearch = useCallback(() => {
    if (query.trim()) {
      executeSearch(query);
    }
  }, [query, executeSearch]);

  const clearSearch = useCallback(() => {
    setQuery('');
    setResults([]);
    setSuggestions([]);
    setShowSuggestions(false);
    setHasSearched(false);
    setCorrectedQuery(null);
    setOriginalQuery(null);
    setSelectedCategories([]);
    setSelectedSpeakers([]);
    setSelectedTags([]);
    setSelectedDateRange(null);
    clearError();
  }, [clearError]);

  return {
    query,
    results,
    suggestions,
    loading,
    error,
    errorCode,
    errorDetails,
    showSuggestions,
    hasSearched,
    correctedQuery,
    originalQuery,
    selectedCategories,
    selectedSpeakers,
    selectedTags,
    selectedDateRange,
    handleQueryChange,
    handleSubmit,
    handleSuggestionClick,
    clearSearch,
    retrySearch,
    handleCategoryChange,
    handleSpeakerChange,
    handleTagChange,
    handleDateRangeChange,
    clearFilters,
    handleFilterDataReady,
  };
}
