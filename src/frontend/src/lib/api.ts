/** Cliente API — Wrapper de fetch para comunicacion con el backend FastAPI.

 * Maneja:
 * - JWT Bearer token automatico
 * - Correlation ID propagation
 * - Errores estandarizados
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | undefined>;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  private buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    return url.toString();
  }

  async request<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, ...fetchOptions } = options;
    const url = this.buildUrl(path, params);
    const token = this.getToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Correlation-ID': crypto.randomUUID(),
      ...((options.headers as Record<string, string>) || {}),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
      throw new ApiError(response.status, error.detail || 'Error en la solicitud');
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async get<T = unknown>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
    return this.request<T>(path, { method: 'GET', params });
  }

  async post<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async patch<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete(path: string): Promise<void> {
    await this.request(path, { method: 'DELETE' });
  }

  async upload<T = unknown>(path: string, formData: FormData): Promise<T> {
    const url = this.buildUrl(path);
    const token = this.getToken();

    const headers: Record<string, string> = {
      'X-Correlation-ID': crypto.randomUUID(),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error al subir archivo' }));
      throw new ApiError(response.status, error.detail || 'Error en la carga');
    }

    return response.json();
  }
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export const api = new ApiClient(API_URL);
