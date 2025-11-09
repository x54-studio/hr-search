// Auto-detect API URL based on current hostname
const getApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  
  // If running on localhost, use localhost for API
  // If running on IP, use same IP for API
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
  recorded_date?: string;
  video_url?: string;
  pdf_url?: string;
}

export interface AutocompleteSuggestion {
  suggestion: string;
  type: 'webinar' | 'speaker' | 'tag';
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

export class ApiError extends Error {
  constructor(
    public errorCode: string,
    message: string,
    public details: Record<string, any> = {},
    public statusCode: number = 500,
    public timestamp?: number,
    public requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiService {
  private async request<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
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
        
        // Handle FastAPI error format
        if (errorData.detail) {
          const detail = Array.isArray(errorData.detail) ? errorData.detail[0] : errorData.detail;
          throw new ApiError(
            'VALIDATION_ERROR',
            detail.msg || detail.message || 'Validation error',
            { field: detail.loc, input: detail.input },
            response.status
          );
        }
        
        // Handle custom error format
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
      
      // Network or other errors
      throw new ApiError(
        'NETWORK_ERROR',
        error instanceof Error ? error.message : 'Network request failed',
        {},
        0
      );
    }
  }

  async search(query: string, limit = 20): Promise<SearchResponse> {
    if (!query || !query.trim()) {
      throw new ApiError('VALIDATION_ERROR', 'Search query cannot be empty', { field: 'query' });
    }
    
    if (query.length > 200) {
      throw new ApiError('VALIDATION_ERROR', 'Search query too long (max 200 characters)', { field: 'query', value: query.length });
    }
    
    if (limit < 1 || limit > 50) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 50', { field: 'limit', value: limit });
    }
    
    return this.request<SearchResponse>('/search', { q: query, limit: limit.toString() });
  }

  async autocomplete(query: string, limit = 10): Promise<AutocompleteResponse> {
    if (!query || !query.trim()) {
      throw new ApiError('VALIDATION_ERROR', 'Autocomplete query cannot be empty', { field: 'query' });
    }
    
    if (limit < 1 || limit > 20) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 20', { field: 'limit', value: limit });
    }
    
    return this.request<AutocompleteResponse>('/autocomplete', { q: query, limit: limit.toString() });
  }

  async getWebinar(id: string): Promise<SearchResult> {
    if (!id || !id.trim()) {
      throw new ApiError('VALIDATION_ERROR', 'Webinar ID cannot be empty', { field: 'id' });
    }
    
    return this.request<SearchResult>(`/webinars/${id}`);
  }

  async getCategories(): Promise<{ categories: Array<{ slug: string; name: string; webinar_count: number }> }> {
    return this.request('/categories');
  }

  async getSpeakers(): Promise<{ speakers: Array<{ name: string; bio?: string; webinar_count: number }> }> {
    return this.request('/speakers');
  }

  async getTags(limit = 100): Promise<{ tags: Array<{ slug: string; name: string; webinar_count: number }> }> {
    if (limit < 1 || limit > 500) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 500', { field: 'limit', value: limit });
    }
    
    return this.request('/tags', { limit: limit.toString() });
  }

  async getPopularTags(limit = 20): Promise<{ tags: Array<{ slug: string; name: string; webinar_count: number }> }> {
    if (limit < 1 || limit > 100) {
      throw new ApiError('VALIDATION_ERROR', 'Limit must be between 1 and 100', { field: 'limit', value: limit });
    }
    
    return this.request('/tags/popular', { limit: limit.toString() });
  }

  async listWebinars(params: {
    category?: string;
    speaker?: string;
    tags?: string;
    date_range?: string;
    offset?: number;
    limit?: number;
  } = {}): Promise<{
    webinars: SearchResult[];
    total: number;
    offset: number;
    limit: number;
    hasMore: boolean;
  }> {
    const { category, speaker, tags, date_range, offset = 0, limit = 20 } = params;
    
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
    
    return this.request('/webinars', queryParams);
  }
}

export const apiService = new ApiService();