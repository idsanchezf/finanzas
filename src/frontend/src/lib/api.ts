/**
 * Cliente API — Wrapper de fetch para comunicacion con el backend FastAPI.
 *
 * Maneja:
 * - JWT Bearer token automatico
 * - Refresh token automatico ante 401 (interceptor)
 * - Cola de requests pendientes durante el refresh (evita renovaciones concurrentes)
 * - Correlation ID propagation
 * - Errores estandarizados
 */

import { auth } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// ── Tipos ────────────────────────────────────────────────────────────

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | undefined>;
  /** Si es true, no dispara refresh ni redireccion ante 401 (ej: /auth/login). */
  skipAuth?: boolean;
}

/** Funcion que resuelve una cola de requests pendientes tras el refresh. */
type PendingRequest = (token: string | null) => void;

// ── Estado global del interceptor ────────────────────────────────────

let isRefreshing = false;
let pendingRequests: PendingRequest[] = [];

function resolvePendingRequests(token: string | null): void {
  pendingRequests.forEach((resolve) => resolve(token));
  pendingRequests = [];
}

// ── Cliente ──────────────────────────────────────────────────────────

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
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

  /**
   * Ejecuta una request HTTP con interceptor de refresh automatico.
   *
   * Flujo ante 401:
   * 1. Si ya hay un refresh en curso → encola este request y espera
   * 2. Si no hay refresh en curso → inicia refresh → reintenta
   * 3. Si el refresh falla → limpia tokens y redirige al login
   */
  async request<T = unknown>(path: string, options: RequestOptions = {}): Promise<T> {
    const { params, skipAuth, ...fetchOptions } = options;

    // Intenta la request original
    try {
      return await this.executeRequest<T>(path, { params, ...fetchOptions });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401 && !skipAuth) {
        return await this.handle401<T>(path, { params, ...fetchOptions });
      }
      throw error;
    }
  }

  /** Realiza la request HTTP cruda (sin interceptor). */
  private async executeRequest<T = unknown>(
    path: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { params, ...fetchOptions } = options;
    const url = this.buildUrl(path, params);
    const token = auth.getAccessToken();

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

  /**
   * Maneja una respuesta 401: refresca el token y reintenta.
   * Si ya hay un refresh en curso, espera en cola.
   */
  private async handle401<T = unknown>(
    path: string,
    options: RequestInit & { params?: Record<string, string | number | undefined> }
  ): Promise<T> {
    // Si otro request ya esta refrescando, encolamos este
    if (isRefreshing) {
      return new Promise<T>((resolve, reject) => {
        pendingRequests.push((token: string | null) => {
          if (token) {
            // Reintenta con el nuevo token
            this.executeRequest<T>(path, options)
              .then(resolve)
              .catch(reject);
          } else {
            reject(new ApiError(401, 'Sesion expirada. Inicia sesion de nuevo.'));
          }
        });
      });
    }

    // Inicia el refresh
    isRefreshing = true;

    try {
      const newToken = await auth.refreshAccessToken();
      resolvePendingRequests(newToken);

      if (!newToken) {
        throw new ApiError(401, 'Sesion expirada. Inicia sesion de nuevo.');
      }

      // Reintenta la request original con el nuevo token
      return await this.executeRequest<T>(path, options);
    } finally {
      isRefreshing = false;
    }
  }

  // ── Metodos HTTP ─────────────────────────────────────────────────

  async get<T = unknown>(
    path: string,
    params?: Record<string, string | number | undefined>
  ): Promise<T> {
    return this.request<T>(path, { method: 'GET', params });
  }

  async post<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
      skipAuth: path === '/auth/login' || path === '/auth/refresh',
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
    const token = auth.getAccessToken();

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
      // Para uploads, un 401 tambien dispara el interceptor
      if (response.status === 401) {
        const newToken = await auth.refreshAccessToken();
        if (newToken) {
          headers['Authorization'] = `Bearer ${newToken}`;
          const retryResponse = await fetch(url, {
            method: 'POST',
            headers,
            body: formData,
          });
          if (!retryResponse.ok) {
            const error = await retryResponse.json().catch(() => ({ detail: 'Error al subir archivo' }));
            throw new ApiError(retryResponse.status, error.detail || 'Error en la carga');
          }
          return retryResponse.json();
        }
        throw new ApiError(401, 'Sesion expirada. Inicia sesion de nuevo.');
      }
      const error = await response.json().catch(() => ({ detail: 'Error al subir archivo' }));
      throw new ApiError(response.status, error.detail || 'Error en la carga');
    }

    return response.json();
  }
}

// ── Error tipado ────────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

// ── Instancia singleton ─────────────────────────────────────────────

export const api = new ApiClient(API_URL);
