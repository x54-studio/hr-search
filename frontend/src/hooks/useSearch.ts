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
}

export interface SearchActions {
  handleQueryChange: (newQuery: string) => void;
  handleSuggestionClick: (suggestion: string) => void;
  clearSearch: () => void;
  retrySearch: () => void;
  search: (query: string) => Promise<void>;
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

  // Proper search function that can be called directly
  const search = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
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
      
      const [searchResponse, autocompleteResponse] = await Promise.all([
        apiService.search(searchQuery),
        apiService.autocomplete(searchQuery)
      ]);
      
      setResults(searchResponse.results);
      setSuggestions(autocompleteResponse.suggestions);
      setCorrectedQuery(searchResponse.corrected_query || null);
      setOriginalQuery(searchResponse.original_query || null);
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
  }, [clearError, setApiError]);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSuggestions([]);
      setCorrectedQuery(null);
      setOriginalQuery(null);
      clearError();
      return;
    }

    const timeoutId = setTimeout(() => {
      search(query);
    }, 300); // 300ms debounce

    return () => clearTimeout(timeoutId);
  }, [query, search]);

  const retrySearch = useCallback(() => {
    if (query.trim()) {
      // Use the proper search function instead of hacky setTimeout
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
    handleQueryChange,
    handleSuggestionClick,
    clearSearch,
    retrySearch,
    search,
  };
}
