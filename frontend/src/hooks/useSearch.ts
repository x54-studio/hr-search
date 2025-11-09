import { useState, useEffect, useCallback } from 'react';
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
  correctedQuery: string | null;
  originalQuery: string | null;
  selectedCategories: string[];
  selectedSpeakers: string[];
  selectedTags: string[];
  selectedDateRange: string | null;
}

export interface SearchActions {
  handleQueryChange: (newQuery: string) => void;
  handleSuggestionClick: (suggestion: string) => void;
  clearSearch: () => void;
  retrySearch: () => void;
  search: (query: string) => Promise<void>;
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
  const [correctedQuery, setCorrectedQuery] = useState<string | null>(null);
  const [originalQuery, setOriginalQuery] = useState<string | null>(null);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedSpeakers, setSelectedSpeakers] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedDateRange, setSelectedDateRange] = useState<string | null>(null);
  const [categoryNameToSlug, setCategoryNameToSlug] = useState<Map<string, string>>(new Map());
  const [tagNameToSlug, setTagNameToSlug] = useState<Map<string, string>>(new Map());

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

  // Handler to receive filter data maps from SearchFilters component
  const handleFilterDataReady = useCallback((data: {
    categoryMap: Map<string, string>;
    tagMap: Map<string, string>;
  }) => {
    setCategoryNameToSlug(data.categoryMap);
    setTagNameToSlug(data.tagMap);
  }, []);

  // Helper function to apply client-side filters
  const applyFilters = useCallback((results: SearchResult[]): SearchResult[] => {
    let filtered = [...results];

    // Filter by categories
    // Backend returns category_name, but filters use slugs
    // Use map from SearchFilters to convert name -> slug
    if (selectedCategories.length > 0) {
      filtered = filtered.filter(r => {
        if (!r.category_name) return false;
        const categorySlug = categoryNameToSlug.get(r.category_name);
        if (!categorySlug) return false;
        return selectedCategories.includes(categorySlug);
      });
    }

    // Filter by speakers (array intersection)
    if (selectedSpeakers.length > 0) {
      filtered = filtered.filter(r => 
        r.speakers?.some(speaker => 
          selectedSpeakers.includes(speaker)
        ) ?? false
      );
    }

    // Filter by tags (array intersection)
    // Backend returns tag names, but filters use slugs
    // Use map from SearchFilters to convert name -> slug
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

  // Proper search function that can be called directly
  const search = useCallback(async (searchQuery: string) => {
    const hasQuery = searchQuery.trim().length > 0;
    const hasFilters = selectedCategories.length > 0 || selectedSpeakers.length > 0 || selectedTags.length > 0 || selectedDateRange !== null;

    // No query and no filters: clear results
    if (!hasQuery && !hasFilters) {
      setResults([]);
      setSuggestions([]);
      setCorrectedQuery(null);
      setOriginalQuery(null);
      clearError();
      return;
    }

    try {
      setLoading(true);
      clearError();

      let searchResults: SearchResult[] = [];
      let searchCorrectedQuery: string | null = null;
      let searchOriginalQuery: string | null = null;

      if (hasQuery) {
        // Query exists: use semantic search
        const [searchResponse, autocompleteResponse] = await Promise.all([
          apiService.search(searchQuery),
          apiService.autocomplete(searchQuery)
        ]);
        
        searchResults = searchResponse.results;
        searchCorrectedQuery = searchResponse.corrected_query || null;
        searchOriginalQuery = searchResponse.original_query || null;
        setSuggestions(autocompleteResponse.suggestions);
      } else {
        // No query but filters exist: use listWebinars
        setSuggestions([]);
        setCorrectedQuery(null);
        setOriginalQuery(null);

        // If only date_range is selected, fetch all webinars with date filter
        if (selectedDateRange && selectedCategories.length === 0 && selectedSpeakers.length === 0 && selectedTags.length === 0) {
          try {
            const response = await apiService.listWebinars({ date_range: selectedDateRange || undefined, limit: 50 });
            searchResults = response.webinars;
          } catch (err) {
            console.error(`Failed to fetch webinars with date_range "${selectedDateRange}":`, err);
            searchResults = [];
          }
        } else {
          // Backend supports single values, so we need to handle multiple selections
          // Strategy: make calls for each filter type and merge results
          const allResults: SearchResult[] = [];
          const seenIds = new Set<string>();

          // Fetch by categories
          for (const category of selectedCategories) {
            try {
              const response = await apiService.listWebinars({ category, date_range: selectedDateRange || undefined, limit: 50 });
              response.webinars.forEach(webinar => {
                if (!seenIds.has(webinar.id)) {
                  seenIds.add(webinar.id);
                  allResults.push(webinar);
                }
              });
            } catch (err) {
              // Continue with other filters if one fails
              console.error(`Failed to fetch category "${category}":`, err);
            }
          }

          // Fetch by speakers
          for (const speaker of selectedSpeakers) {
            try {
              const response = await apiService.listWebinars({ speaker, date_range: selectedDateRange || undefined, limit: 50 });
              response.webinars.forEach(webinar => {
                if (!seenIds.has(webinar.id)) {
                  seenIds.add(webinar.id);
                  allResults.push(webinar);
                }
              });
            } catch (err) {
              console.error(`Failed to fetch speaker ${speaker}:`, err);
            }
          }

          // Fetch by tags (backend accepts comma-separated, but we'll do one at a time for consistency)
          for (const tag of selectedTags) {
            try {
              // URLSearchParams will automatically encode the tag slug
              const response = await apiService.listWebinars({ tags: tag, date_range: selectedDateRange || undefined, limit: 50 });
              response.webinars.forEach(webinar => {
                if (!seenIds.has(webinar.id)) {
                  seenIds.add(webinar.id);
                  allResults.push(webinar);
                }
              });
            } catch (err) {
              console.error(`Failed to fetch tag "${tag}":`, err);
              // Continue with other tags if one fails
            }
          }

          searchResults = allResults;
        }
      }

      // Apply client-side filters if query exists (semantic search results)
      // For filters-only case, results are already filtered by API
      if (hasQuery && hasFilters) {
        searchResults = applyFilters(searchResults);
      } else if (!hasQuery && hasFilters) {
        // For filters-only, we need to apply intersection logic client-side
        // since we fetched union of all filters
        searchResults = applyFilters(searchResults);
      }

      setResults(searchResults);
      setCorrectedQuery(searchCorrectedQuery);
      setOriginalQuery(searchOriginalQuery);
    } catch (err) {
      if (err instanceof ApiError) {
        setApiError(err);
      } else {
        setError(err instanceof Error ? err.message : 'Search failed');
        setErrorCode('UNKNOWN_ERROR');
        setErrorDetails({});
      }
      setResults([]);
      setSuggestions([]);
      setCorrectedQuery(null);
      setOriginalQuery(null);
    } finally {
      setLoading(false);
    }
  }, [clearError, setApiError, selectedCategories, selectedSpeakers, selectedTags, selectedDateRange, applyFilters]);

  // Debounced search - triggers on query or filter changes
  useEffect(() => {
    const hasQuery = query.trim().length > 0;
    const hasFilters = selectedCategories.length > 0 || selectedSpeakers.length > 0 || selectedTags.length > 0 || selectedDateRange !== null;

    // No query and no filters: clear results
    if (!hasQuery && !hasFilters) {
      setResults([]);
      setSuggestions([]);
      setCorrectedQuery(null);
      setOriginalQuery(null);
      clearError();
      return;
    }

    // Debounce only for query changes, immediate for filter changes
    const timeoutId = setTimeout(() => {
      search(query);
    }, hasQuery ? 100 : 0); // 100ms debounce for query, immediate for filters

    return () => clearTimeout(timeoutId);
  }, [query, selectedCategories, selectedSpeakers, selectedTags, selectedDateRange, search]);

  const retrySearch = useCallback(() => {
    if (query.trim()) {
      search(query);
    }
  }, [query, search]);

  const handleQueryChange = useCallback((newQuery: string) => {
    setQuery(newQuery);
    setShowSuggestions(true);
    clearError();
  }, [clearError]);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    clearError();
  }, [clearError]);

  const clearSearch = useCallback(() => {
    setQuery('');
    setResults([]);
    setSuggestions([]);
    setShowSuggestions(false);
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
    correctedQuery,
    originalQuery,
    selectedCategories,
    selectedSpeakers,
    selectedTags,
    selectedDateRange,
    handleQueryChange,
    handleSuggestionClick,
    clearSearch,
    retrySearch,
    search,
    handleCategoryChange,
    handleSpeakerChange,
    handleTagChange,
    handleDateRangeChange,
    clearFilters,
    handleFilterDataReady,
  };
}
