'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { api, ApiError } from '@/lib/api';
import type { Extract, ExtractListResponse } from '@/types/extract';

interface UseExtractsState {
  extracts: Extract[];
  loading: boolean;
  error: string | null;
}

interface UseExtractsReturn extends UseExtractsState {
  refresh: () => Promise<void>;
  addExtract: (extract: Extract) => void;
  updateExtract: (id: string, updates: Partial<Extract>) => void;
}

/**
 * Hook para gestionar la lista de extractos del usuario.
 * Carga inicial automatica y refresh manual.
 */
export function useExtracts(): UseExtractsReturn {
  const [state, setState] = useState<UseExtractsState>({
    extracts: [],
    loading: true,
    error: null,
  });
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await api.get<ExtractListResponse>('/extracts');
      if (mountedRef.current) {
        setState({
          extracts: data.items ?? [],
          loading: false,
          error: null,
        });
      }
    } catch (err) {
      if (mountedRef.current) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Error al cargar extractos';
        setState((prev) => ({
          ...prev,
          loading: false,
          error: message,
        }));
      }
    }
  }, []);

  // Carga inicial
  useEffect(() => {
    refresh();
  }, [refresh]);

  const addExtract = useCallback((extract: Extract) => {
    setState((prev) => ({
      ...prev,
      extracts: [extract, ...prev.extracts],
    }));
  }, []);

  const updateExtract = useCallback((id: string, updates: Partial<Extract>) => {
    setState((prev) => ({
      ...prev,
      extracts: prev.extracts.map((e) =>
        e.id === id ? { ...e, ...updates } : e
      ),
    }));
  }, []);

  return {
    ...state,
    refresh,
    addExtract,
    updateExtract,
  };
}
