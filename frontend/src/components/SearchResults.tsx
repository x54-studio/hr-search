import React from 'react';
import type { SearchResult } from '../services/api';
import { Calendar, Clock, Users, Tag } from 'lucide-react';

interface SearchResultsProps {
  results: SearchResult[];
  loading: boolean;
  error: string | null;
}

export function SearchResults({ results, loading, error }: SearchResultsProps) {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-3 text-gray-600">Szukam...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-2">❌ Błąd wyszukiwania</div>
        <div className="text-gray-600">{error}</div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500 mb-2">🔍 Brak wyników</div>
        <div className="text-gray-400">Spróbuj innych słów kluczowych</div>
      </div>
    );
  }

  const formatDuration = (ms?: number) => {
    if (!ms) return '';
    const minutes = Math.floor(ms / 60000);
    return `${minutes} min`;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('pl-PL');
  };

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-600 mb-4">
        Znaleziono {results.length} wyników
      </div>
      
      {results.map((result) => (
        <div key={result.id} className="result-card">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
              {result.title}
            </h3>
            {result.category_name && (
              <span className="text-xs bg-primary-100 text-primary-800 px-2 py-1 rounded ml-2 flex-shrink-0">
                {result.category_name}
              </span>
            )}
          </div>
          
          {result.description && (
            <p className="text-gray-600 mb-3 line-clamp-2">
              {result.description}
            </p>
          )}
          
          <div className="flex flex-wrap gap-4 text-sm text-gray-500">
            {result.speakers.length > 0 && (
              <div className="flex items-center">
                <Users className="w-4 h-4 mr-1" />
                {result.speakers.join(', ')}
              </div>
            )}
            
            {result.recorded_date && (
              <div className="flex items-center">
                <Calendar className="w-4 h-4 mr-1" />
                {formatDate(result.recorded_date)}
              </div>
            )}
            
            {result.duration_ms && (
              <div className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {formatDuration(result.duration_ms)}
              </div>
            )}
          </div>
          
          {result.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-3">
              {result.tags.slice(0, 5).map((tag, index) => (
                <span key={index} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded flex items-center">
                  <Tag className="w-3 h-3 mr-1" />
                  {tag}
                </span>
              ))}
              {result.tags.length > 5 && (
                <span className="text-xs text-gray-500">
                  +{result.tags.length - 5} więcej
                </span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
