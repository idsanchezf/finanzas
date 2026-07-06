'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { dashboardApi, type DashboardParams, type DashboardAllData } from '@/lib/dashboard-api';

interface UseDashboardState {
  data: DashboardAllData | null;
  loading: boolean;
  error: string | null;
  partials: {
    summary: boolean;
    byCategory: boolean;
    daily: boolean;
    monthlyTrend: boolean;
  };
}

interface UseDashboardReturn extends UseDashboardState {
  refetch: () => Promise<void>;
  fetchPartial: (key: keyof DashboardAllData) => Promise<void>;
}

/**
 * Hook para cargar datos del dashboard con carga parcial y reintento por grafico.
 */
export function useDashboard(params: DashboardParams): UseDashboardReturn {
  const [state, setState] = useState<UseDashboardState>({
    data: null,
    loading: true,
    error: null,
    partials: {
      summary: false,
      byCategory: false,
      daily: false,
      monthlyTrend: false,
    },
  });

  const paramsRef = useRef(params);
  paramsRef.current = params;

  const fetchAll = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      loading: true,
      error: null,
      partials: { summary: false, byCategory: false, daily: false, monthlyTrend: false },
    }));

    try {
      const data = await dashboardApi.getAll(paramsRef.current);
      setState({
        data,
        loading: false,
        error: null,
        partials: { summary: true, byCategory: true, daily: true, monthlyTrend: true },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar datos del dashboard';
      setState((prev) => ({
        ...prev,
        loading: false,
        error: message,
      }));
    }
  }, []);

  const fetchPartial = useCallback(async (key: keyof DashboardAllData) => {
    setState((prev) => ({
      ...prev,
      partials: { ...prev.partials, [key]: false },
    }));

    try {
      let partialData: Partial<DashboardAllData> = {};

      switch (key) {
        case 'summary':
          partialData.summary = await dashboardApi.getSummary(paramsRef.current);
          break;
        case 'byCategory':
          partialData.byCategory = await dashboardApi.getByCategory(paramsRef.current);
          break;
        case 'daily':
          partialData.daily = await dashboardApi.getDaily(paramsRef.current);
          break;
        case 'monthlyTrend':
          partialData.monthlyTrend = await dashboardApi.getMonthlyTrend(paramsRef.current);
          break;
      }

      setState((prev) => ({
        ...prev,
        data: prev.data ? { ...prev.data, ...partialData } : (partialData as DashboardAllData),
        error: null,
        partials: { ...prev.partials, [key]: true },
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : `Error al cargar ${key}`;
      setState((prev) => ({
        ...prev,
        partials: { ...prev.partials, [key]: true },
      }));
      // No sobreescribimos el error global, solo logueamos el parcial
      console.error(`[useDashboard] Error cargando ${key}:`, message);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    ...state,
    refetch: fetchAll,
    fetchPartial,
  };
}
