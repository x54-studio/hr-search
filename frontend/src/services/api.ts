// Auto-detect API URL based on current hostname
const getApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  const port = '8000';

  return `${protocol}//${hostname}:${port}/api`;
};

const API_BASE_URL = getApiBaseUrl();

export interface SearchResult {
  id: string;
  title: string;
  description: string;
  category_name?: string;
  speakers?: string[];
  tags?: string[];
  duration_ms?: number;
  published_date?: string;
  source_type?: string;
  source_url?: string;
  metadata?: Record<string, unknown>;
}

export interface AutocompleteSuggestion {
  suggestion: string;
  type: 'title' | 'speaker' | 'tag';
}

export interface SearchResponse {
  results: SearchResult[];
  count: number;
  corrected_query?: string;
  original_query?: string;
}

export interface AutocompleteResponse {
  suggestions: AutocompleteSuggestion[];
}

export interface AppConfig {
  title: string;
  source_types: string[];
}

export class ApiError extends Error {
  errorCode: string;
  details: Record<string, any>;
  statusCode: number;
  timestamp?: number;
  requestId?: string;

  constructor(
    errorCode: string,
    message: string,
    details: Record<string, any> = {},
    statusCode: number = 500,
    timestamp?: number,
    requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.errorCode = errorCode;
    this.details = details;
    this.statusCode = statusCode;
    this.timestamp = timestamp;
    this.requestId = requestId;
  }
}

class ApiService {
  private async request<T>(endpoint: string, params?: Record<string, string>, signal?: AbortSignal): Promise<T> {
    const url = new URL(`${API_BASE_URL}${endpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    try {
      const response = await fetch(url.toString(), {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        signal,
      });

      if (!response.ok) {
        let errorData: any;
        try {
          errorData = await response.json();
        } catch {
          errorData = {
            error: 'NETWORK_ERROR',
            message: `HTTP ${response.status}: ${response.statusText}`,
            details: {}
          };
        }

        if (errorData.detail) {
          const detail = Array.isArray(errorData.detail) ? errorData.detail[0] : errorData.detail;
          throw new ApiError(
            'VALIDATION_ERROR',
            detail.msg || detail.message || 'Validation error',
            { field: detail.loc, input: detail.input },
            response.status
          );
        }

        throw new ApiError(
          errorData.error || 'NETWORK_ERROR',
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          errorData.details || {},
          response.status,
          errorData.timestamp,
          errorData.request_id
        );
      }

      return response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw error;
      }

      throw new ApiError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : 'Network request failed',
        {},
        0
      );
    }
  }

  async getConfig(): Promise<AppConfig> {
    return this.request<AppConfig>('/config');
  }

  async search(query: string, limit = 20, signal?: AbortSignal): Promise<SearchResponse> {
    if (!query || !query.trim()) {
      throw new ApiError('VALIDATION_ERROR', 'Search query cannot be empty', { field: 'query' });
    }

    if (query.length > 200) {
      throw new ApiError('VALIDATION_ERROR', 'Search query too long (max 200 characters)', { field: 'query', value: query.length });
    }

    if (limit < 1 || limit > 50) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 50', { field: 'limit', value: limit });
    }

    return this.request<SearchResponse>('/search', { q: query, limit: limit.toString() }, signal);
  }

  async autocomplete(query: string, limit = 10, signal?: AbortSignal): Promise<AutocompleteResponse> {
    if (!query || !query.trim()) {
      throw new ApiError('VALIDATION_ERROR', 'Autocomplete query cannot be empty', { field: 'query' });
    }

    if (limit < 1 || limit > 20) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 20', { field: 'limit', value: limit });
    }

    return this.request<AutocompleteResponse>('/autocomplete', { q: query, limit: limit.toString() }, signal);
  }

  async getItem(id: string): Promise<SearchResult> {
    if (!id || !id.trim()) {
      throw new ApiError('VALIDATION_ERROR', 'Item ID cannot be empty', { field: 'id' });
    }

    return this.request<SearchResult>(`/items/${id}`);
  }

  async getCategories(): Promise<{ categories: Array<{ slug: string; name: string; item_count: number }> }> {
    return this.request('/categories');
  }

  async getSpeakers(): Promise<{ speakers: Array<{ name: string; bio?: string; item_count: number }> }> {
    return this.request('/speakers');
  }

  async getTags(limit = 100): Promise<{ tags: Array<{ slug: string; name: string; item_count: number }> }> {
    if (limit < 1 || limit > 500) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 500', { field: 'limit', value: limit });
    }

    return this.request('/tags', { limit: limit.toString() });
  }

  async getPopularTags(limit = 20): Promise<{ tags: Array<{ slug: string; name: string; item_count: number }> }> {
    if (limit < 1 || limit > 100) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 100', { field: 'limit', value: limit });
    }

    return this.request('/tags/popular', { limit: limit.toString() });
  }

  async listItems(params: {
    category?: string;
    speaker?: string;
    tags?: string;
    date_range?: string;
    source_type?: string;
    offset?: number;
    limit?: number;
    signal?: AbortSignal;
  } = {}): Promise<{
    items: SearchResult[];
    total: number;
    offset: number;
    limit: number;
    hasMore: boolean;
  }> {
    const { category, speaker, tags, date_range, source_type, offset = 0, limit = 20, signal } = params;

    if (offset < 0) {
      throw new ApiError('VALIDATION_ERROR', 'Offset must be non-negative', { field: 'offset', value: offset });
    }

    if (limit < 1 || limit > 50) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 50', { field: 'limit', value: limit });
    }

    const queryParams: Record<string, string> = {
      offset: offset.toString(),
      limit: limit.toString(),
    };

    if (category) queryParams.category = category;
    if (speaker) queryParams.speaker = speaker;
    if (tags) queryParams.tags = tags;
    if (date_range) queryParams.date_range = date_range;
    if (source_type) queryParams.source_type = source_type;

    return this.request('/items', queryParams, signal);
  }
}

export const apiService = new ApiService();
