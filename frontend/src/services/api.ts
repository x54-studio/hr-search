const API_BASE_URL = 'http://localhost:8000/api';

export interface SearchResult {
  id: string;
  title: string;
  description: string;
  category_name?: string;
  speakers: string[];
  tags: string[];
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
}

export interface AutocompleteResponse {
  suggestions: AutocompleteSuggestion[];
}

class ApiService {
  private async request<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${API_BASE_URL}${endpoint}`);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async search(query: string, limit = 20): Promise<SearchResponse> {
    return this.request<SearchResponse>('/search', { q: query, limit: limit.toString() });
  }

  async autocomplete(query: string, limit = 10): Promise<AutocompleteResponse> {
    return this.request<AutocompleteResponse>('/autocomplete', { q: query, limit: limit.toString() });
  }

  async getWebinar(id: string): Promise<SearchResult> {
    return this.request<SearchResult>(`/webinars/${id}`);
  }

  async getCategories(): Promise<{ categories: Array<{ slug: string; name: string; count: number }> }> {
    return this.request('/categories');
  }

  async getSpeakers(): Promise<{ speakers: Array<{ name: string; bio?: string; count: number }> }> {
    return this.request('/speakers');
  }
}

export const apiService = new ApiService();