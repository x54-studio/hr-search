import { useState, useEffect } from 'react';
import { Filter, X, Check, Loader2 } from 'lucide-react';
import { apiService, ApiError } from '../services/api';

interface Category {
  slug: string;
  name: string;
  item_count: number;
}

interface Speaker {
  name: string;
  bio?: string;
  item_count: number;
}

interface Tag {
  slug: string;
  name: string;
  item_count: number;
}

interface SearchFiltersProps {
  selectedCategories: string[];
  selectedSpeakers: string[];
  selectedTags: string[];
  selectedDateRange: string | null;
  onCategoryChange: (categories: string[]) => void;
  onSpeakerChange: (speakers: string[]) => void;
  onTagChange: (tags: string[]) => void;
  onDateRangeChange: (range: string | null) => void;
  onClearAll: () => void;
  onFilterDataReady?: (data: {
    categoryMap: Map<string, string>; // name -> slug
    tagMap: Map<string, string>; // name -> slug
  }) => void;
}

export function SearchFilters({
  selectedCategories,
  selectedSpeakers,
  selectedTags,
  selectedDateRange,
  onCategoryChange,
  onSpeakerChange,
  onTagChange,
  onDateRangeChange,
  onClearAll,
  onFilterDataReady,
}: SearchFiltersProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState({
    dateRange: true,
    categories: true,
    speakers: true,
    tags: true,
  });

  useEffect(() => {
    const fetchFilterData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [categoriesResponse, speakersResponse, tagsResponse] = await Promise.all([
          apiService.getCategories(),
          apiService.getSpeakers(),
          apiService.getTags(100),
        ]);

        setCategories(categoriesResponse.categories);
        setSpeakers(speakersResponse.speakers);
        setTags(tagsResponse.tags);

        // Build maps for efficient lookup: name -> slug
        if (onFilterDataReady) {
          const categoryMap = new Map<string, string>();
          categoriesResponse.categories.forEach(cat => {
            categoryMap.set(cat.name, cat.slug);
          });

          const tagMap = new Map<string, string>();
          tagsResponse.tags.forEach(tag => {
            tagMap.set(tag.name, tag.slug);
          });

          onFilterDataReady({ categoryMap, tagMap });
        }
      } catch (err) {
        const errorMessage = err instanceof ApiError 
          ? err.message 
          : 'Nie udało się załadować filtrów';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchFilterData();
  }, [onFilterDataReady]);

  const toggleCategory = (slug: string) => {
    if (selectedCategories.includes(slug)) {
      onCategoryChange(selectedCategories.filter(c => c !== slug));
    } else {
      onCategoryChange([...selectedCategories, slug]);
    }
  };

  const toggleSpeaker = (name: string) => {
    if (selectedSpeakers.includes(name)) {
      onSpeakerChange(selectedSpeakers.filter(s => s !== name));
    } else {
      onSpeakerChange([...selectedSpeakers, name]);
    }
  };

  const toggleTag = (slug: string) => {
    if (selectedTags.includes(slug)) {
      onTagChange(selectedTags.filter(t => t !== slug));
    } else {
      onTagChange([...selectedTags, slug]);
    }
  };

  const hasActiveFilters = selectedCategories.length > 0 || 
                           selectedSpeakers.length > 0 || 
                           selectedTags.length > 0 ||
                           selectedDateRange !== null;

  const toggleSection = (section: 'dateRange' | 'categories' | 'speakers' | 'tags') => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-600">Ładowanie filtrów...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <div className="text-red-600 text-sm">
          <p className="font-medium">Błąd ładowania filtrów</p>
          <p className="mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 sm:p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Filtry</h2>
          {hasActiveFilters && (
            <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
              {selectedCategories.length + selectedSpeakers.length + selectedTags.length + (selectedDateRange ? 1 : 0)}
            </span>
          )}
        </div>
        {hasActiveFilters && (
          <button
            onClick={onClearAll}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
            Wyczyść wszystkie
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Date Range Section */}
        <div className="border rounded-lg">
          <button
            onClick={() => toggleSection('dateRange')}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Okres
              {selectedDateRange && (
                <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                  1
                </span>
              )}
            </span>
            <span className="text-gray-400 text-sm">
              {expandedSections.dateRange ? '−' : '+'}
            </span>
          </button>
          {expandedSections.dateRange && (
            <div className="p-3 border-t">
              <div className="space-y-2">
                <label className="flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-gray-50 transition-colors">
                  <input
                    type="radio"
                    name="dateRange"
                    value=""
                    checked={selectedDateRange === null}
                    onChange={() => onDateRangeChange(null)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-900">Wszystkie</span>
                </label>
                <label className="flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-gray-50 transition-colors">
                  <input
                    type="radio"
                    name="dateRange"
                    value="last_30_days"
                    checked={selectedDateRange === 'last_30_days'}
                    onChange={() => onDateRangeChange('last_30_days')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-900">Ostatnie 30 dni</span>
                </label>
                <label className="flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-gray-50 transition-colors">
                  <input
                    type="radio"
                    name="dateRange"
                    value="last_90_days"
                    checked={selectedDateRange === 'last_90_days'}
                    onChange={() => onDateRangeChange('last_90_days')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-900">Ostatnie 90 dni</span>
                </label>
                <label className="flex items-center gap-2 p-2 rounded-md cursor-pointer hover:bg-gray-50 transition-colors">
                  <input
                    type="radio"
                    name="dateRange"
                    value="last_365_days"
                    checked={selectedDateRange === 'last_365_days'}
                    onChange={() => onDateRangeChange('last_365_days')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-sm font-medium text-gray-900">Ostatnie 365 dni</span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Categories Section */}
        <div className="border rounded-lg">
          <button
            onClick={() => toggleSection('categories')}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Kategorie
              {selectedCategories.length > 0 && (
                <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                  {selectedCategories.length}
                </span>
              )}
            </span>
            <span className="text-gray-400 text-sm">
              {expandedSections.categories ? '−' : '+'}
            </span>
          </button>
          {expandedSections.categories && (
            <div className="p-3 border-t max-h-64 overflow-y-auto">
              {categories.length === 0 ? (
                <p className="text-sm text-gray-500">Brak kategorii</p>
              ) : (
                <div className="space-y-2">
                  {categories.map((category) => {
                    const isSelected = selectedCategories.includes(category.slug);
                    return (
                      <label
                        key={category.slug}
                        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-blue-50 border border-blue-200'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="relative flex-shrink-0">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleCategory(category.slug)}
                            className="sr-only"
                          />
                          <div
                            className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                              isSelected
                                ? 'bg-blue-600 border-blue-600'
                                : 'border-gray-300'
                            }`}
                          >
                            {isSelected && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="text-sm font-medium text-gray-900">
                            {category.name}
                          </span>
                          <span className="ml-2 text-xs text-gray-500">
                            ({category.item_count})
                          </span>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Speakers Section */}
        <div className="border rounded-lg">
          <button
            onClick={() => toggleSection('speakers')}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Prelegenci
              {selectedSpeakers.length > 0 && (
                <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                  {selectedSpeakers.length}
                </span>
              )}
            </span>
            <span className="text-gray-400 text-sm">
              {expandedSections.speakers ? '−' : '+'}
            </span>
          </button>
          {expandedSections.speakers && (
            <div className="p-3 border-t max-h-64 overflow-y-auto">
              {speakers.length === 0 ? (
                <p className="text-sm text-gray-500">Brak prelegentów</p>
              ) : (
                <div className="space-y-2">
                  {speakers.map((speaker) => {
                    const isSelected = selectedSpeakers.includes(speaker.name);
                    return (
                      <label
                        key={speaker.name}
                        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-blue-50 border border-blue-200'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="relative flex-shrink-0">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleSpeaker(speaker.name)}
                            className="sr-only"
                          />
                          <div
                            className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                              isSelected
                                ? 'bg-blue-600 border-blue-600'
                                : 'border-gray-300'
                            }`}
                          >
                            {isSelected && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="text-sm font-medium text-gray-900">
                            {speaker.name}
                          </span>
                          <span className="ml-2 text-xs text-gray-500">
                            ({speaker.item_count})
                          </span>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tags Section */}
        <div className="border rounded-lg">
          <button
            onClick={() => toggleSection('tags')}
            className="w-full flex items-center justify-between p-3 text-left hover:bg-gray-50 transition-colors"
          >
            <span className="font-medium text-gray-900">
              Tagi
              {selectedTags.length > 0 && (
                <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                  {selectedTags.length}
                </span>
              )}
            </span>
            <span className="text-gray-400 text-sm">
              {expandedSections.tags ? '−' : '+'}
            </span>
          </button>
          {expandedSections.tags && (
            <div className="p-3 border-t max-h-64 overflow-y-auto">
              {tags.length === 0 ? (
                <p className="text-sm text-gray-500">Brak tagów</p>
              ) : (
                <div className="space-y-2">
                  {tags.map((tag) => {
                    const isSelected = selectedTags.includes(tag.slug);
                    return (
                      <label
                        key={tag.slug}
                        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-blue-50 border border-blue-200'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="relative flex-shrink-0">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleTag(tag.slug)}
                            className="sr-only"
                          />
                          <div
                            className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                              isSelected
                                ? 'bg-blue-600 border-blue-600'
                                : 'border-gray-300'
                            }`}
                          >
                            {isSelected && (
                              <Check className="w-3 h-3 text-white" />
                            )}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="text-sm font-medium text-gray-900">
                            {tag.name}
                          </span>
                          <span className="ml-2 text-xs text-gray-500">
                            ({tag.item_count})
                          </span>
                        </div>
                      </label>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

