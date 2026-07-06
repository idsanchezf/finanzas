'use client';

import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  type TooltipItem,
  type ChartOptions,
} from 'chart.js';
import { Card } from '@/components/ui/Card';
import { formatCOP } from '@/lib/utils';
import type { MonthlyTrend } from '@/types/dashboard';

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend);

// Datos mock para desarrollo
const MOCK_DATA: MonthlyTrend = {
  items: [
    { mes: 'Ene', gastos: 2700000, ingresos: 5000000, saldo_neto: 2300000 },
    { mes: 'Feb', gastos: 2900000, ingresos: 5100000, saldo_neto: 2200000 },
    { mes: 'Mar', gastos: 3100000, ingresos: 5200000, saldo_neto: 2100000 },
    { mes: 'Abr', gastos: 2800000, ingresos: 5000000, saldo_neto: 2200000 },
    { mes: 'May', gastos: 3200000, ingresos: 5400000, saldo_neto: 2200000 },
    { mes: 'Jun', gastos: 2850000, ingresos: 5200000, saldo_neto: 2350000 },
    { mes: 'Jul', gastos: 3400000, ingresos: 5600000, saldo_neto: 2200000 },
    { mes: 'Ago', gastos: 3100000, ingresos: 5300000, saldo_neto: 2200000 },
    { mes: 'Sep', gastos: 2950000, ingresos: 5100000, saldo_neto: 2150000 },
    { mes: 'Oct', gastos: 3300000, ingresos: 5500000, saldo_neto: 2200000 },
    { mes: 'Nov', gastos: 3050000, ingresos: 5200000, saldo_neto: 2150000 },
    { mes: 'Dic', gastos: 3600000, ingresos: 5800000, saldo_neto: 2200000 },
  ],
  promedio_movil: 3080000,
};

interface MonthlyTrendLineProps {
  data: MonthlyTrend | null;
  loading?: boolean;
  onRetry?: () => void;
}

/** Calcula promedio movil simple de 3 periodos. */
function movingAverage(values: number[], window: number = 3): (number | null)[] {
  return values.map((_, i) => {
    if (i < window - 1) return null;
    const slice = values.slice(i - window + 1, i + 1);
    return slice.reduce((a, b) => a + b, 0) / slice.length;
  });
}

export function MonthlyTrendLine({ data, loading, onRetry }: MonthlyTrendLineProps) {
  const chartData = data ?? MOCK_DATA;
  const items = chartData.items;

  const gastosValues = items.map((d) => d.gastos);
  const maGastos = movingAverage(gastosValues, 3);

  const lineData = {
    labels: items.map((d) => d.mes),
    datasets: [
      {
        label: 'Gastos',
        data: gastosValues,
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.05)',
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#EF4444',
        pointBorderColor: '#FFFFFF',
        pointBorderWidth: 2,
        pointHoverRadius: 6,
        tension: 0.3,
        fill: true,
      },
      {
        label: 'Ingresos',
        data: items.map((d) => d.ingresos),
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.05)',
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#10B981',
        pointBorderColor: '#FFFFFF',
        pointBorderWidth: 2,
        pointHoverRadius: 6,
        tension: 0.3,
        fill: false,
      },
      {
        label: 'Prom. movil gastos (3m)',
        data: maGastos,
        borderColor: '#F59E0B',
        backgroundColor: 'transparent',
        borderWidth: 1.5,
        borderDash: [6, 4],
        pointRadius: 2,
        pointBackgroundColor: '#F59E0B',
        pointBorderWidth: 0,
        tension: 0.4,
        fill: false,
      },
    ],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          boxWidth: 16,
          boxHeight: 3,
          padding: 16,
          font: { size: 11 },
          color: '#6B7280',
          usePointStyle: true,
          pointStyleWidth: 16,
        },
      },
      tooltip: {
        backgroundColor: '#1F2937',
        titleColor: '#F9FAFB',
        bodyColor: '#D1D5DB',
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: (ctx: TooltipItem<'line'>) => {
            const label = ctx.dataset.label ?? '';
            const value = formatCOP(ctx.raw as number);
            return ` ${label}: ${value}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: { size: 11 },
          color: '#9CA3AF',
        },
      },
      y: {
        beginAtZero: false,
        grid: {
          color: '#F3F4F6',
        },
        ticks: {
          font: { size: 11 },
          color: '#9CA3AF',
          callback: (value: string | number) => {
            const v = Number(value);
            if (v >= 1000000) return `$${(v / 1000000).toFixed(1)}M`;
            return `$${(v / 1000).toFixed(0)}k`;
          },
        },
      },
    },
    animation: {
      duration: 800,
    },
  };

  if (loading) {
    return (
      <Card className="p-4 md:p-6">
        <div className="animate-pulse">
          <div className="h-5 w-40 bg-gray-200 rounded mb-4" />
          <div className="h-72 bg-gray-100 rounded-lg" />
        </div>
      </Card>
    );
  }

  if (!chartData) {
    return (
      <Card className="p-4 md:p-6 text-center">
        <p className="text-sm text-gray-500 mb-3">No se pudo cargar la tendencia mensual.</p>
        {onRetry && (
          <button onClick={onRetry} className="btn-secondary text-sm">
            Reintentar
          </button>
        )}
      </Card>
    );
  }

  return (
    <Card className="p-4 md:p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-900">Tendencia mensual</h3>
        <span className="text-xs text-gray-500">
          Prom. movil: <span className="font-semibold text-gray-700">{formatCOP(chartData.promedio_movil)}</span>
        </span>
      </div>
      <div className="h-72">
        <Line data={lineData} options={options} />
      </div>
    </Card>
  );
}
