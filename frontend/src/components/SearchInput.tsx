import { useState, useRef, useEffect } from 'react';
import { Search, X } from 'lucide-react';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onClear: () => void;
  placeholder?: string;
  suggestions?: Array<{ suggestion: string }>;
  showSuggestions?: boolean;
  onSuggestionSelect?: (suggestion: string) => void;
  onSelectedIndexChange?: (index: number) => void;
}

export function SearchInput({ 
  value, 
  onChange, 
  onClear, 
  placeholder = "Szukaj webinaru, tematu lub prelegenta...",
  suggestions = [],
  showSuggestions = false,
  onSuggestionSelect,
  onSelectedIndexChange
}: SearchInputProps) {
  const [focused, setFocused] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset selected index when suggestions change
  useEffect(() => {
    setSelectedIndex(-1);
    onSelectedIndexChange?.(-1);
  }, [suggestions.length, value, onSelectedIndexChange]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Escape') {
        onClear();
        inputRef.current?.blur();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => {
          const newIndex = prev < suggestions.length - 1 ? prev + 1 : 0;
          onSelectedIndexChange?.(newIndex);
          return newIndex;
        });
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => {
          const newIndex = prev > 0 ? prev - 1 : suggestions.length - 1;
          onSelectedIndexChange?.(newIndex);
          return newIndex;
        });
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < suggestions.length && onSuggestionSelect) {
          onSuggestionSelect(suggestions[selectedIndex].suggestion);
          setSelectedIndex(-1);
          onSelectedIndexChange?.(-1);
        }
        break;
      case 'Escape':
        e.preventDefault();
        onClear();
        inputRef.current?.blur();
        setSelectedIndex(-1);
        onSelectedIndexChange?.(-1);
        break;
    }
  };

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !showSuggestions) {
        onClear();
        inputRef.current?.blur();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClear, showSuggestions]);

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 200)}
          placeholder={placeholder}
          className="search-input pl-12 pr-12"
          autoComplete="off"
        />
        {value && (
          <button
            onClick={onClear}
            className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    </div>
  );
}
