import React from 'react';
import type { AutocompleteSuggestion } from '../services/api';

interface SearchSuggestionsProps {
  suggestions: AutocompleteSuggestion[];
  visible: boolean;
  onSuggestionClick: (suggestion: string) => void;
}

export function SearchSuggestions({ suggestions, visible, onSuggestionClick }: SearchSuggestionsProps) {
  if (!visible || suggestions.length === 0) return null;

  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          onClick={() => onSuggestionClick(suggestion.suggestion)}
          className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0"
        >
          <div className="flex items-center justify-between">
            <span className="text-gray-900">{suggestion.suggestion}</span>
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
              {suggestion.type}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}
