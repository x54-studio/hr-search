import React from 'react';
import { SearchInput } from './components/SearchInput';
import { SearchSuggestions } from './components/SearchSuggestions';
import { SearchResults } from './components/SearchResults';
import { useSearch } from './hooks/useSearch';

function App() {
  const {
    query,
    results,
    suggestions,
    loading,
    error,
    showSuggestions,
    handleQueryChange,
    handleSuggestionClick,
    clearSearch,
  } = useSearch();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              HR Knowledge Search
            </h1>
            <p className="text-gray-600">
              Znajdź potrzebne materiały szkoleniowe w sekundach
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
          />
          <SearchSuggestions
            suggestions={suggestions}
            visible={showSuggestions && query.length > 0}
            onSuggestionClick={handleSuggestionClick}
          />
        </div>

        {/* Results Section */}
        <SearchResults
          results={results}
          loading={loading}
          error={error}
        />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>HR Knowledge Search System - Semantic Search for Training Materials</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
