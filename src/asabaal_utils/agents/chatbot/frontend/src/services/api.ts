import { MemoryItem, MemoryCreate, MemoryUpdate, ChatRequest, ChatResponse, ChatTurn } from '../types';

const API_BASE = '/api';

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Chat endpoints
  async chatComplete(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat/complete', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getChatTurns(limit: number = 50): Promise<ChatTurn[]> {
    return this.request<ChatTurn[]>(`/chat/turns?limit=${limit}`);
  }

  // Memory endpoints
  async getMemoryItems(params: {
    query?: string;
    tags?: string;
    status?: string;
    limit?: number;
  } = {}): Promise<MemoryItem[]> {
    const searchParams = new URLSearchParams();
    if (params.query) searchParams.append('query', params.query);
    if (params.tags) searchParams.append('tags', params.tags);
    if (params.status) searchParams.append('status', params.status);
    if (params.limit) searchParams.append('limit', params.limit.toString());

    const query = searchParams.toString();
    return this.request<MemoryItem[]>(`/memory/items${query ? `?${query}` : ''}`);
  }

  async createMemoryItem(memory: MemoryCreate): Promise<MemoryItem> {
    return this.request<MemoryItem>('/memory/items', {
      method: 'POST',
      body: JSON.stringify(memory),
    });
  }

  async updateMemoryItem(id: string, updates: MemoryUpdate): Promise<MemoryItem> {
    return this.request<MemoryItem>(`/memory/items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteMemoryItem(id: string, adminSecret: string): Promise<{ ok: boolean }> {
    return this.request<{ ok: boolean }>(`/memory/items/${id}`, {
      method: 'DELETE',
      body: JSON.stringify({ admin_secret: adminSecret }),
    });
  }

  async importMemoryFile(file: File): Promise<{ ok: boolean; item: MemoryItem }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/memory/import`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Import Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async exportMemoryItems(): Promise<{ count: number; items: MemoryItem[] }> {
    return this.request<{ count: number; items: MemoryItem[] }>('/memory/export');
  }

  // Admin endpoints
  async healthCheck(): Promise<{ status: string; version: string; memory_store_path: string }> {
    return this.request<{ status: string; version: string; memory_store_path: string }>('/admin/health', {
      method: 'POST',
    });
  }

  async getModels(): Promise<{ models: string[] }> {
    return this.request<{ models: string[] }>('/models');
  }
}

export const apiClient = new ApiClient();