'use client';

import { useState, useCallback, useMemo } from 'react';
import { SummaryCards } from '@/components/dashboard/SummaryCards';
import { CategoryDonut } from '@/components/dashboard/CategoryDonut';
import { DailyBarChart } from '@/components/dashboard/DailyBarChart';
import { MonthlyTrendLine } from '@/components/dashboard/MonthlyTrendLine';
import { useDashboard } from '@/hooks/useDashboard';
import { cn } from '@/lib/utils';

/** Rango de meses disponibles para el selector (ultimos 12 meses). */
function generateMonthOptions(): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [];
  const now = new Date();
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const label = d.toLocaleDateString('es-CO', { year: 'numeric', month: 'long' });
    options.push({ value, label });
  }
  return options;
}

/** Skeleton para un grafico. */
function GraphSkeleton({ height = 'h-64' }: { height?: string }) {
  return (
    <div className="card p-4 md:p-6 animate-pulse">
      <div className="h-5 w-40 bg-gray-200 rounded mb-4" />
      <div className={cn('bg-gray-100 rounded-lg', height)} />
    </div>
  );
}

export default function DashboardPage() {
  const monthOptions = useMemo(() => generateMonthOptions(), []);
  const [period, setPeriod] = useState(monthOptions[0]?.value ?? '2026-06');

  const { data, loading, error, refetch, fetchPartial } = useDashboard({
    period,
  });

  const handlePeriodChange = useCallback((newPeriod: string) => {
    setPeriod(newPeriod);
  }, []);

  // Construir opciones de periodo agrupadas por año
  const groupedOptions = useMemo(() => {
    const groups: Record<string, typeof monthOptions> = {};
    for (const opt of monthOptions) {
      const year = opt.value.split('-')[0];
      if (!groups[year]) groups[year] = [];
      groups[year].push(opt);
    }
    return groups;
  }, [monthOptions]);

  return (
    <div className="space-y-6 p-4 md:p-6 animate-fade-in">
      {/* Header con selector de periodo */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 md:text-3xl">Dashboard</h1>
          <p className="text-sm text-gray-500">Resumen de tus finanzas del periodo seleccionado</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Selector de mes */}
          <div className="relative">
            <select
              value={period}
              onChange={(e) => handlePeriodChange(e.target.value)}
              className="input-field pr-8 appearance-none cursor-pointer text-sm min-w-[160px]"
              aria-label="Seleccionar periodo"
            >
              {Object.entries(groupedOptions).map(([year, options]) => (
                <optgroup key={year} label={year}>
                  {options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            <span className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400 text-xs">
              ▼
            </span>
          </div>

          {/* Boton de refrescar */}
          <button
            onClick={refetch}
            disabled={loading}
            className="btn-secondary text-sm"
            aria-label="Refrescar datos"
          >
            <span className={cn('inline-block', loading && 'animate-spin')}>🔄</span>
          </button>
        </div>
      </div>

      {/* Error global */}
      {error && (
        <div className="card border-danger-500 bg-danger-50 p-4">
          <div className="flex items-start gap-3">
            <span className="text-xl">⚠️</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-danger-700">Error al cargar el dashboard</p>
              <p className="text-xs text-danger-600 mt-1">{error}</p>
            </div>
            <button onClick={refetch} className="btn-secondary text-sm shrink-0">
              Reintentar
            </button>
          </div>
        </div>
      )}

      {/* KPIs */}
      {loading && !data ? (
        <SummaryCards data={null} loading={true} />
      ) : (
        <SummaryCards
          data={data?.summary ?? null}
          loading={loading}
          onRetry={() => fetchPartial('summary')}
        />
      )}

      {/* Graficos: donut + barras */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {loading && !data?.byCategory ? (
          <GraphSkeleton height="h-72" />
        ) : (
          <CategoryDonut
            data={data?.byCategory ?? null}
            loading={loading}
            onRetry={() => fetchPartial('byCategory')}
          />
        )}

        {loading && !data?.daily ? (
          <GraphSkeleton height="h-64" />
        ) : (
          <DailyBarChart
            data={data?.daily ?? null}
            loading={loading}
            onRetry={() => fetchPartial('daily')}
          />
        )}
      </div>

      {/* Tendencia mensual */}
      {loading && !data?.monthlyTrend ? (
        <GraphSkeleton height="h-72" />
      ) : (
        <MonthlyTrendLine
          data={data?.monthlyTrend ?? null}
          loading={loading}
          onRetry={() => fetchPartial('monthlyTrend')}
        />
      )}

      {/* Seccion de alertas y recomendaciones */}
      <div className="card">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Alertas y recomendaciones</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <span className="text-xl">⚠️</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-800">Gasto hormiga detectado</p>
              <p className="text-xs text-amber-600">
                12 compras menores a $15.000 COP suman $128.500 este mes.
              </p>
            </div>
            <button className="text-xs text-amber-700 underline shrink-0">Ver detalle</button>
          </div>
          <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-3">
            <span className="text-xl">💡</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-green-800">Oportunidad de ahorro</p>
              <p className="text-xs text-green-600">
                Reduciendo un 20% en alimentacion ahorrarias $85.000 al mes.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-lg border border-primary-200 bg-primary-50 p-3">
            <span className="text-xl">📅</span>
            <div className="flex-1">
              <p className="text-sm font-medium text-primary-800">Fecha de corte proxima</p>
              <p className="text-xs text-primary-600">
                Tu fecha de corte es el dia 18. Te quedan {data?.summary?.dias_para_corte ?? '...'} dias.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
