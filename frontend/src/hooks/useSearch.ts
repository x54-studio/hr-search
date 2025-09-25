import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import type { SearchResult, AutocompleteSuggestion } from '../services/api';

export function useSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSuggestions([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [searchResponse, autocompleteResponse] = await Promise.all([
          apiService.search(query),
          apiService.autocomplete(query)
        ]);
        
        setResults(searchResponse.results);
        setSuggestions(autocompleteResponse.suggestions);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
        setResults([]);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query]);

  const handleQueryChange = useCallback((newQuery: string) => {
    setQuery(newQuery);
    setShowSuggestions(true);
  }, []);

  const handleSuggestionClick = useCallback((suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
  }, []);

  const clearSearch = useCallback(() => {
    setQuery('');
    setResults([]);
    setSuggestions([]);
    setShowSuggestions(false);
    setError(null);
  }, []);

  return {
    query,
    results,
    suggestions,
    loading,
    error,
    showSuggestions,
    handleQueryChange,
    handleSuggestionClick,
    clearSearch,
  };
}
