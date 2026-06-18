'use client';

/**
 * AuthContext — Proveedor global de autenticacion.
 *
 * - Carga el script de Google Identity Services (GIS)
 * - Delegado en el hook `useAuth()` para la logica de sesion
 * - Expone user, loading, isAuthenticated, login, loginWithGoogle, logout
 */

import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import Script from 'next/script';
import { useAuth } from '@/hooks/useAuth';
import type { User } from '@/types/user';

// ── Google Identity Services — tipado minimo ────────────────────────

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string; select_by: string }) => void;
            auto_select?: boolean;
            context?: 'signin' | 'signup' | 'use';
          }) => void;
          prompt: (callback?: (notification: PromptNotification) => void) => void;
          cancel: () => void;
        };
      };
    };
  }
}

interface PromptNotification {
  isNotDisplayed: () => boolean;
  isSkippedMoment: () => boolean;
  isDismissedMoment: () => boolean;
  getNotDisplayedReason: () => string;
  getSkippedReason: () => string;
  getDismissedReason: () => string;
}

// ── Types ────────────────────────────────────────────────────────────

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (provider: 'google' | 'microsoft', idToken: string) => Promise<User>;
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
}

// ── Context ──────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ── Provider ─────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();
  const gisInitialized = useRef(false);
  const [gisReady, setGisReady] = useState(false);

  // ── Inicializar Google Identity Services al cargar el script ─────

  const handleGisLoad = useCallback(() => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    if (!clientId || gisInitialized.current || typeof window === 'undefined' || !window.google) {
      return;
    }

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response) => {
        try {
          await auth.login('google', response.credential);
        } catch (err) {
          console.error('[Auth] Error en callback de Google:', err);
        }
      },
      auto_select: false,
      context: 'signin',
    });

    gisInitialized.current = true;
    setGisReady(true);
  }, [auth]);

  const value: AuthContextType = {
    user: auth.user,
    loading: auth.loading,
    isAuthenticated: auth.isAuthenticated,
    login: auth.login,
    loginWithGoogle: auth.loginWithGoogle,
    logout: auth.logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {/* Carga el script de Google Identity Services */}
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={handleGisLoad}
      />
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ─────────────────────────────────────────────────────────────

export function useAuthContext(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (ctx === undefined) {
    throw new Error('useAuthContext debe usarse dentro de un <AuthProvider>');
  }
  return ctx;
}
