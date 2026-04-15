import { useState, useEffect } from 'react';
import { SearchInput } from './components/SearchInput';
import { SearchSuggestions } from './components/SearchSuggestions';
import { SearchResults } from './components/SearchResults';
import { SearchFilters } from './components/SearchFilters';
import { useSearch } from './hooks/useSearch';
import { apiService } from './services/api';
import type { AppConfig } from './services/api';

const DEFAULT_TITLE = 'Knowledge Search';

function App() {
  const {
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
  } = useSearch();

  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [config, setConfig] = useState<AppConfig | null>(null);

  // Fetch config on mount
  useEffect(() => {
    apiService.getConfig()
      .then(setConfig)
      .catch(() => setConfig({ title: DEFAULT_TITLE, source_types: [] }));
  }, []);

  // Reset highlighted index when suggestions change
  useEffect(() => {
    setHighlightedIndex(-1);
  }, [suggestions.length, query]);

  const handleCorrectedSearch = (correctedQuery: string) => {
    handleQueryChange(correctedQuery);
  };

  const title = config?.title || DEFAULT_TITLE;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {title}
            </h1>
            <p className="text-gray-600">
              Znajdź potrzebne materiały w sekundach
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="relative mb-8">
          <SearchInput
            value={query}
            onChange={handleQueryChange}
            onClear={clearSearch}
            onSubmit={handleSubmit}
            suggestions={suggestions}
            showSuggestions={showSuggestions && query.length > 0 && !loading}
            onSuggestionSelect={handleSuggestionClick}
            onSelectedIndexChange={setHighlightedIndex}
          />
          <SearchSuggestions
            suggestions={suggestions}
            visible={showSuggestions && query.length > 0 && !loading}
            onSuggestionClick={handleSuggestionClick}
            highlightedIndex={highlightedIndex}
          />
        </div>

        {/* Filters Section */}
        <SearchFilters
          selectedCategories={selectedCategories}
          selectedSpeakers={selectedSpeakers}
          selectedTags={selectedTags}
          selectedDateRange={selectedDateRange}
          onCategoryChange={handleCategoryChange}
          onSpeakerChange={handleSpeakerChange}
          onTagChange={handleTagChange}
          onDateRangeChange={handleDateRangeChange}
          onClearAll={clearFilters}
          onFilterDataReady={handleFilterDataReady}
        />

        {/* Results Section — visible only after explicit search */}
        {hasSearched && (
          <SearchResults
            results={results}
            loading={loading}
            error={error}
            errorCode={errorCode}
            errorDetails={errorDetails}
            correctedQuery={correctedQuery}
            originalQuery={originalQuery}
            onRetry={retrySearch}
            onCorrectedSearch={handleCorrectedSearch}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>{title} - Semantic Search for Knowledge Materials</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
