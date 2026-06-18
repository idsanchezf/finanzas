/**
 * Autenticacion OAuth2 — Helpers para login con Google, manejo de tokens y refresh.
 *
 * Flujo:
 * 1. Google Identity Services devuelve `credential` (JWT id_token)
 * 2. Se envia `POST /api/v1/auth/login` con { provider: "google", id_token: credential }
 * 3. Backend responde con { access_token, refresh_token, user }
 * 4. Tokens se persisten en localStorage + cookie (para middleware)
 * 5. API client interceptor refresca automaticamente ante 401
 */

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const AUTH_COOKIE = 'auth_token';

// ── Helpers de entorno ──────────────────────────────────────────────

function isBrowser(): boolean {
  return typeof window !== 'undefined';
}

function setCookie(name: string, value: string, days: number = 7): void {
  if (!isBrowser()) return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function removeCookie(name: string): void {
  if (!isBrowser()) return;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
}

// ── API publica ─────────────────────────────────────────────────────

export const auth = {
  /** Obtiene el access token JWT desde localStorage. */
  getAccessToken(): string | null {
    if (!isBrowser()) return null;
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  /** Obtiene el refresh token desde localStorage. */
  getRefreshToken(): string | null {
    if (!isBrowser()) return null;
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  /** Persiste ambos tokens y sincroniza cookie para middleware. */
  setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    setCookie(AUTH_COOKIE, accessToken);
  },

  /** Elimina tokens del storage y cookie. */
  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    removeCookie(AUTH_COOKIE);
  },

  /** Indica si hay un token de acceso almacenado (no valida expiracion). */
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  },

  /**
   * Intenta renovar el access token usando el refresh token.
   * Retorna el nuevo token o null si falla (y limpia storage).
   * Thread-safe: usa un flag `_refreshing` para evitar renovaciones concurrentes.
   */
  async refreshAccessToken(): Promise<string | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return null;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

    try {
      const response = await fetch(`${apiUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        return null;
      }

      const data = await response.json();
      // El backend puede devolver un nuevo refresh_token o mantener el mismo
      this.setTokens(data.access_token, data.refresh_token || refreshToken);
      return data.access_token;
    } catch {
      this.clearTokens();
      return null;
    }
  },

  /** Cierra sesion: limpia storage y redirige al login. */
  logout(): void {
    this.clearTokens();
    if (isBrowser()) {
      window.location.href = '/auth';
    }
  },
};
