'use client';

import { Card } from '@/components/ui/Card';
import { formatCOP, cn } from '@/lib/utils';
import type { DashboardSummary } from '@/types/dashboard';

interface SummaryCardsProps {
  data: DashboardSummary | null;
  loading?: boolean;
  onRetry?: () => void;
}

/** Tarjeta individual de KPI con variacion vs mes anterior. */
function KpiCard({
  label,
  value,
  icon,
  variation,
  variationLabel,
  loading,
}: {
  label: string;
  value: string;
  icon: string;
  variation?: number;
  variationLabel?: string;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <Card className="p-4 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-8 w-8 bg-gray-200 rounded" />
          <div className="h-5 w-12 bg-gray-200 rounded" />
        </div>
        <div className="mt-2 h-7 w-3/4 bg-gray-200 rounded" />
        <div className="mt-1 h-4 w-1/2 bg-gray-200 rounded" />
      </Card>
    );
  }

  const isPositive = variation != null && variation > 0;
  const isNegative = variation != null && variation < 0;
  const isZero = variation != null && variation === 0;

  return (
    <Card className="p-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <span className="text-2xl" role="img" aria-label={label}>
          {icon}
        </span>
        {variation != null && !isZero && (
          <span
            className={cn(
              'inline-flex items-center gap-0.5 text-xs font-semibold rounded-full px-2 py-0.5',
              isPositive ? 'bg-danger-50 text-danger-700' : 'bg-success-50 text-success-700'
            )}
            title={variationLabel ?? `Variacion: ${variation > 0 ? '+' : ''}${variation.toFixed(1)}%`}
          >
            <span className="text-[10px] leading-none">
              {isPositive ? '↑' : '↓'}
            </span>
            {Math.abs(variation).toFixed(1)}%
          </span>
        )}
        {variation != null && isZero && (
          <span className="text-xs text-gray-400 font-medium">= 0%</span>
        )}
      </div>
      <p className="mt-2 text-lg font-bold text-gray-900 md:text-xl truncate" title={value}>
        {value}
      </p>
      <p className="text-xs text-gray-500">{label}</p>
    </Card>
  );
}

/** KPI de porcentaje (cupo utilizado) con barra de progreso. */
function CupoCard({
  pct,
  diasCorte,
  loading,
}: {
  pct: number;
  diasCorte: number;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <Card className="p-4 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-8 w-8 bg-gray-200 rounded" />
          <div className="h-5 w-12 bg-gray-200 rounded" />
        </div>
        <div className="mt-2 h-4 w-full bg-gray-200 rounded-full" />
        <div className="mt-2 h-4 w-1/2 bg-gray-200 rounded" />
      </Card>
    );
  }

  const barColor =
    pct >= 80 ? 'bg-danger-500' : pct >= 50 ? 'bg-warning-500' : 'bg-success-500';

  return (
    <Card className="p-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <span className="text-2xl" role="img" aria-label="Cupo utilizado">
          📈
        </span>
      </div>
      <div className="mt-2 space-y-1">
        <div className="flex justify-between items-baseline">
          <p className="text-lg font-bold text-gray-900 md:text-xl">{pct.toFixed(1)}%</p>
          <p className="text-xs text-gray-500">
            {diasCorte > 0
              ? `${diasCorte} dias hasta corte`
              : diasCorte === 0
                ? 'Corte hoy'
                : `${Math.abs(diasCorte)} dias post-corte`}
          </p>
        </div>
        <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all duration-700', barColor)}
            style={{ width: `${Math.min(pct, 100)}%` }}
          />
        </div>
      </div>
      <p className="mt-1 text-xs text-gray-500">% Cupo utilizado</p>
    </Card>
  );
}

export function SummaryCards({ data, loading, onRetry }: SummaryCardsProps) {
  if (!loading && !data) {
    return (
      <div className="card text-center py-8">
        <p className="text-gray-500 text-sm mb-3">No se pudieron cargar los indicadores.</p>
        {onRetry && (
          <button onClick={onRetry} className="btn-secondary text-sm">
            Reintentar
          </button>
        )}
      </div>
    );
  }

  const isLoading = loading || !data;

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <KpiCard
        label="Total gastado"
        value={isLoading ? '' : formatCOP(data.total_gastado)}
        icon="💳"
        variation={isLoading ? undefined : data.variacion_vs_anterior}
        variationLabel="vs mes anterior"
        loading={isLoading}
      />
      <KpiCard
        label="Total ingresos"
        value={isLoading ? '' : formatCOP(data.total_ingresos)}
        icon="💰"
        loading={isLoading}
      />
      <KpiCard
        label="Promedio diario"
        value={isLoading ? '' : formatCOP(data.promedio_diario)}
        icon="📊"
        loading={isLoading}
      />
      <CupoCard
        pct={isLoading ? 0 : data.pct_cupo_utilizado}
        diasCorte={isLoading ? 0 : data.dias_para_corte}
        loading={isLoading}
      />
      <KpiCard
        label="Salud financiera"
        value={isLoading ? '' : `${(data.score_salud_financiera ?? 0).toFixed(0)}/100`}
        icon="🩺"
        loading={isLoading}
      />
    </div>
  );
}
