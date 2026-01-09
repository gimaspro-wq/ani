/**
 * Admin API client for communicating with the backend admin endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AdminLoginRequest {
  email: string;
  password: string;
}

export interface AdminTokenResponse {
  access_token: string;
  token_type: string;
}

export interface AdminUser {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_anime: number;
  active_anime: number;
  inactive_anime: number;
  total_episodes: number;
  total_video_sources: number;
  recent_anime: Array<{
    id: string;
    title: string;
    created_at: string;
  }>;
  recent_episodes: Array<{
    id: string;
    anime_id: string;
    number: number;
    created_at: string;
  }>;
}

export interface AnimeListItem {
  id: string;
  title: string;
  year: number | null;
  status: string | null;
  source_name: string;
  is_active: boolean;
  admin_modified: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnimeListResponse {
  items: AnimeListItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface AnimeDetail {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  year: number | null;
  status: string | null;
  poster: string | null;
  source_name: string;
  source_id: string;
  genres: string[] | null;
  alternative_titles: string[] | null;
  is_active: boolean;
  admin_modified: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnimeUpdateRequest {
  title?: string;
  slug?: string;
  description?: string;
  year?: number;
  status?: string;
  poster?: string;
  is_active?: boolean;
}

export interface EpisodeListItem {
  id: string;
  anime_id: string;
  number: number;
  title: string | null;
  source_episode_id: string;
  is_active: boolean;
  admin_modified: boolean;
  created_at: string;
  updated_at: string;
}

export interface EpisodeListResponse {
  items: EpisodeListItem[];
  total: number;
  anime_title: string;
}

export interface EpisodeCreateRequest {
  anime_id: string;
  number: number;
  title?: string;
  source_episode_id: string;
  is_active?: boolean;
}

export interface EpisodeUpdateRequest {
  number?: number;
  title?: string;
  is_active?: boolean;
}

export interface VideoSourceListItem {
  id: string;
  episode_id: string;
  type: string;
  url: string;
  source_name: string;
  priority: number;
  is_active: boolean;
  admin_modified: boolean;
  created_at: string;
  updated_at: string;
}

export interface VideoSourceListResponse {
  items: VideoSourceListItem[];
  total: number;
  episode_number: number;
}

export interface VideoSourceCreateRequest {
  episode_id: string;
  type: string;
  url: string;
  source_name: string;
  priority?: number;
  is_active?: boolean;
}

export interface VideoSourceUpdateRequest {
  type?: string;
  url?: string;
  source_name?: string;
  priority?: number;
  is_active?: boolean;
}

class AdminAPIClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('admin_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = new Headers(options.headers);
    headers.set('Content-Type', 'application/json');

    if (this.token) {
      headers.set('Authorization', `Bearer ${this.token}`);
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const error = await response.json();
        if (error.detail) {
          errorMessage = error.detail;
        }
      } catch {
        // Response was not JSON, use the default error message
      }
      throw new Error(errorMessage);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('admin_token', token);
      } else {
        localStorage.removeItem('admin_token');
      }
    }
  }

  getToken(): string | null {
    return this.token;
  }

  // Auth endpoints
  async login(data: AdminLoginRequest): Promise<AdminTokenResponse> {
    const response = await this.request<AdminTokenResponse>('/api/v1/admin/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(response.access_token);
    return response;
  }

  async logout() {
    this.setToken(null);
  }

  async getCurrentAdmin(): Promise<AdminUser> {
    return this.request<AdminUser>('/api/v1/admin/me');
  }

  // Dashboard
  async getDashboard(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/api/v1/admin/dashboard');
  }

  // Anime management
  async listAnime(params?: {
    page?: number;
    per_page?: number;
    search?: string;
    is_active?: boolean;
    source_name?: string;
  }): Promise<AnimeListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.per_page) query.append('per_page', params.per_page.toString());
    if (params?.search) query.append('search', params.search);
    if (params?.is_active !== undefined) query.append('is_active', params.is_active.toString());
    if (params?.source_name) query.append('source_name', params.source_name);

    return this.request<AnimeListResponse>(`/api/v1/admin/anime?${query}`);
  }

  async getAnime(id: string): Promise<AnimeDetail> {
    return this.request<AnimeDetail>(`/api/v1/admin/anime/${id}`);
  }

  async updateAnime(id: string, data: AnimeUpdateRequest): Promise<AnimeDetail> {
    return this.request<AnimeDetail>(`/api/v1/admin/anime/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Episode management
  async listEpisodes(animeId: string): Promise<EpisodeListResponse> {
    return this.request<EpisodeListResponse>(`/api/v1/admin/anime/${animeId}/episodes`);
  }

  async createEpisode(data: EpisodeCreateRequest): Promise<EpisodeListItem> {
    return this.request<EpisodeListItem>('/api/v1/admin/episodes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateEpisode(id: string, data: EpisodeUpdateRequest): Promise<EpisodeListItem> {
    return this.request<EpisodeListItem>(`/api/v1/admin/episodes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Video source management
  async listVideoSources(episodeId: string): Promise<VideoSourceListResponse> {
    return this.request<VideoSourceListResponse>(`/api/v1/admin/episodes/${episodeId}/video`);
  }

  async createVideoSource(data: VideoSourceCreateRequest): Promise<VideoSourceListItem> {
    return this.request<VideoSourceListItem>('/api/v1/admin/video', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateVideoSource(id: string, data: VideoSourceUpdateRequest): Promise<VideoSourceListItem> {
    return this.request<VideoSourceListItem>(`/api/v1/admin/video/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteVideoSource(id: string): Promise<void> {
    return this.request<void>(`/api/v1/admin/video/${id}`, {
      method: 'DELETE',
    });
  }
}

export const adminAPI = new AdminAPIClient();
