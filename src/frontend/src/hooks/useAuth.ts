'use client';

import { useState, useEffect, useCallback } from 'react';
import { auth } from '@/lib/auth';
import { api } from '@/lib/api';
import type { User } from '@/types/user';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

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

  const login = useCallback(async (provider: 'google' | 'microsoft', idToken: string) => {
    const response = await api.post<{ access_token: string; refresh_token: string; user: User }>(
      '/auth/login',
      { provider, id_token: idToken }
    );
    auth.setTokens(response.access_token, response.refresh_token);
    setUser(response.user);
    return response.user;
  }, []);

  const logout = useCallback(() => {
    auth.logout();
    setUser(null);
  }, []);

  return {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
  };
}
