import React from 'react';
import type { SearchResult } from '../services/api';
import { Calendar, Clock, Users, Tag, AlertCircle, RefreshCw } from 'lucide-react';

interface SearchResultsProps {
  results: SearchResult[];
  loading: boolean;
  error: string | null;
  errorCode?: string | null;
  errorDetails?: Record<string, any> | null;
  correctedQuery?: string | null;
  originalQuery?: string | null;
  onRetry?: () => void;
  onCorrectedSearch?: (correctedQuery: string) => void;
}

export function SearchResults({ 
  results, 
  loading, 
  error, 
  errorCode, 
  errorDetails, 
  correctedQuery,
  originalQuery,
  onRetry,
  onCorrectedSearch
}: SearchResultsProps) {
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
        <div className="text-red-600 mb-4">
          <AlertCircle className="w-12 h-12 mx-auto mb-2" />
          <div className="text-lg font-semibold">Błąd wyszukiwania</div>
        </div>
        
        <div className="text-gray-600 mb-4 max-w-md mx-auto">
          <p className="mb-2">{error}</p>
          
          {errorCode && (
            <p className="text-sm text-gray-500">
              Kod błędu: {errorCode}
            </p>
          )}
          
          {errorDetails && Object.keys(errorDetails).length > 0 && (
            <details className="text-sm text-gray-500 mt-2">
              <summary className="cursor-pointer hover:text-gray-700">
                Szczegóły błędu
              </summary>
              <pre className="mt-2 text-left bg-gray-100 p-2 rounded text-xs overflow-auto">
                {JSON.stringify(errorDetails, null, 2)}
              </pre>
            </details>
          )}
        </div>
        
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Spróbuj ponownie
          </button>
        )}
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
      
      {/* Spell correction suggestion */}
      {correctedQuery && originalQuery && correctedQuery !== originalQuery && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="text-blue-800 text-sm">
                <span className="font-medium">Czy chodziło Ci o:</span>
                <span className="ml-2 font-semibold">"{correctedQuery}"</span>
                <span className="ml-2 text-blue-600">
                  (zamiast "{originalQuery}")
                </span>
              </div>
            </div>
            {onCorrectedSearch && (
              <button
                onClick={() => onCorrectedSearch(correctedQuery)}
                className="ml-4 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
              >
                Wyszukaj ponownie
              </button>
            )}
          </div>
        </div>
      )}
      
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
            {result.speakers && result.speakers.length > 0 && (
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
          
          {result.tags && result.tags.length > 0 && (
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
