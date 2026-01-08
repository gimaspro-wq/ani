/**
 * Backend API client for authentication and user data.
 * Handles JWT tokens, library, progress, and history.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export type LibraryStatus = 'watching' | 'planned' | 'completed' | 'dropped';

export interface LibraryItem {
  id: number;
  user_id: number;
  provider: string;
  title_id: string;
  status: LibraryStatus;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface Progress {
  id: number;
  user_id: number;
  provider: string;
  title_id: string;
  episode_id: string;
  position_seconds: number;
  duration_seconds: number;
  updated_at: string;
}

export interface History {
  id: number;
  user_id: number;
  provider: string;
  title_id: string;
  episode_id: string;
  position_seconds: number | null;
  watched_at: string;
}

class BackendAPIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'BackendAPIError';
  }
}

class BackendAPI {
  private baseURL: string;
  private accessToken: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    
    // Try to load token from localStorage
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: response.statusText };
      }
      
      throw new BackendAPIError(
        errorData.detail || `Request failed with status ${response.status}`,
        response.status,
        errorData
      );
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  async register(email: string, password: string) {
    const response = await this.request<{ access_token: string; token_type: string }>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    this.setAccessToken(response.access_token);
    return response;
  }

  async login(email: string, password: string) {
    const response = await this.request<{ access_token: string; token_type: string }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    
    this.setAccessToken(response.access_token);
    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/api/v1/auth/logout', { method: 'POST' });
    } finally {
      this.clearAccessToken();
    }
  }

  async getLibrary(params?: {
    provider?: string;
    status?: LibraryStatus;
    favorites?: boolean;
  }): Promise<LibraryItem[]> {
    const searchParams = new URLSearchParams();
    if (params?.provider) searchParams.set('provider', params.provider);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.favorites) searchParams.set('favorites', 'true');
    
    const query = searchParams.toString();
    return this.request<LibraryItem[]>(`/api/v1/me/library${query ? `?${query}` : ''}`);
  }

  async updateLibraryItem(
    titleId: string,
    data: { status?: LibraryStatus; is_favorite?: boolean },
    provider: string = 'rpc'
  ): Promise<LibraryItem> {
    return this.request<LibraryItem>(
      `/api/v1/me/library/${titleId}?provider=${provider}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    );
  }

  async deleteLibraryItem(titleId: string, provider: string = 'rpc'): Promise<void> {
    await this.request(`/api/v1/me/library/${titleId}?provider=${provider}`, {
      method: 'DELETE',
    });
  }

  async getProgress(params?: {
    provider?: string;
    title_id?: string;
  }): Promise<Progress[]> {
    const searchParams = new URLSearchParams();
    if (params?.provider) searchParams.set('provider', params.provider);
    if (params?.title_id) searchParams.set('title_id', params.title_id);
    
    const query = searchParams.toString();
    return this.request<Progress[]>(`/api/v1/me/progress${query ? `?${query}` : ''}`);
  }

  async updateProgress(
    episodeId: string,
    data: {
      title_id: string;
      position_seconds: number;
      duration_seconds: number;
    },
    provider: string = 'rpc'
  ): Promise<Progress> {
    return this.request<Progress>(
      `/api/v1/me/progress/${episodeId}?provider=${provider}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    );
  }

  async getHistory(params?: {
    provider?: string;
    limit?: number;
  }): Promise<History[]> {
    const searchParams = new URLSearchParams();
    if (params?.provider) searchParams.set('provider', params.provider);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    
    const query = searchParams.toString();
    return this.request<History[]>(`/api/v1/me/history${query ? `?${query}` : ''}`);
  }

  setAccessToken(token: string) {
    this.accessToken = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  clearAccessToken() {
    this.accessToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }
}

export const backendAPI = new BackendAPI();
export { BackendAPIError };
