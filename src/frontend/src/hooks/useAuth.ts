'use client';

import { useState, useEffect, useCallback } from 'react';
import { auth } from '@/lib/auth';
import { api } from '@/lib/api';
import type { User, LoginResponse } from '@/types/user';

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Verificar sesion al montar
  useEffect(() => {
    if (auth.isAuthenticated()) {
      api
        .get<User>('/auth/me')
        .then(setUser)
        .catch(() => auth.clearTokens())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  // Login con provider (Google / Microsoft) — requiere idToken ya obtenido del provider
  const login = useCallback(async (provider: 'google' | 'microsoft', idToken: string) => {
    const response = await api.post<LoginResponse>(
      '/auth/login',
      { provider, id_token: idToken }
    );
    auth.setTokens(response.access_token, response.refresh_token);
    setUser(response.user);
    return response.user;
  }, []);

  // Login con Google via Google Identity Services (One Tap)
  const loginWithGoogle = useCallback(async (): Promise<void> => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId) {
      throw new Error('Google Client ID no configurado. Configura NEXT_PUBLIC_GOOGLE_CLIENT_ID.');
    }

    if (typeof window === 'undefined' || !window.google?.accounts?.id) {
      throw new Error('Google Identity Services no esta disponible aun. Recarga la pagina.');
    }

    return new Promise((resolve, reject) => {
      try {
        // Trigger Google One Tap prompt
        window.google!.accounts.id.prompt((notification) => {
          if (notification.isNotDisplayed()) {
            reject(
              new Error(
                `One Tap no disponible: ${notification.getNotDisplayedReason()}. ` +
                'Verifica que los cookies de terceros esten habilitados o que Google Client ID sea valido.'
              )
            );
          } else if (notification.isSkippedMoment()) {
            reject(
              new Error(
                `One Tap omitido: ${notification.getSkippedReason()}. Intenta en otro momento.`
              )
            );
          }
          // Si no hay errores, el callback de initialize se encarga del login
        });
      } catch (err) {
        reject(err instanceof Error ? err : new Error('Error iniciando sesion con Google'));
      }
    });
  }, []);

  // Logout
  const logout = useCallback(() => {
    auth.logout();
    setUser(null);
  }, []);

  return {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    loginWithGoogle,
    logout,
  };
}
