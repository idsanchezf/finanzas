'use client';

import { useState, useCallback } from 'react';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Hook generico para llamadas a la API con manejo de estado loading/error.
 *
 * @example
 * const { data, loading, error, execute } = useApi(api.getDashboardSummary);
 * useEffect(() => { execute(extractId); }, [extractId]);
 */
export function useApi<T>(
  apiCall: (...args: unknown[]) => Promise<T>
): UseApiState<T> & { execute: (...args: unknown[]) => Promise<T | null> } {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args: unknown[]): Promise<T | null> => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const result = await apiCall(...args);
        setState({ data: result, loading: false, error: null });
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error desconocido';
        setState({ data: null, loading: false, error: message });
        return null;
      }
    },
    [apiCall]
  );

  return { ...state, execute };
}
