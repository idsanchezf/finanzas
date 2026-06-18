'use client';

import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  type TooltipItem,
  type ChartOptions,
} from 'chart.js';
import { Card } from '@/components/ui/Card';
import { formatCOP } from '@/lib/utils';
import type { DailyExpense } from '@/types/dashboard';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

// Datos mock para desarrollo
const MOCK_DATA: DailyExpense = {
  items: Array.from({ length: 30 }, (_, i) => {
    const dia = i + 1;
    // Patron realista: mas gasto los fines de semana
    const weekend = dia % 7 === 0 || dia % 7 === 6;
    const base = weekend ? 120000 : 75000;
    const total = base + Math.floor(Math.random() * 60000) - 15000;
    return {
      dia: `${dia}`,
      total: Math.max(total, 5000),
      categorias: { Alimentacion: total * 0.4, Transporte: total * 0.2, Otros: total * 0.4 },
    };
  }),
  promedio: 92000,
};

interface DailyBarChartProps {
  data: DailyExpense | null;
  loading?: boolean;
  onRetry?: () => void;
}

export function DailyBarChart({ data, loading, onRetry }: DailyBarChartProps) {
  const chartData = data ?? MOCK_DATA;
  const items = chartData.items;

  // Acortar labels de dias para pantallas chicas
  const barData = {
    labels: items.map((d) => d.dia),
    datasets: [
      {
        label: 'Gasto COP',
        data: items.map((d) => d.total),
        backgroundColor: items.map((d, i) => {
          // Color basado en si supera el promedio
          return d.total > chartData.promedio
            ? 'rgba(239, 68, 68, 0.85)' // danger
            : 'rgba(59, 130, 246, 0.85)'; // primary
        }),
        borderColor: items.map((d) =>
          d.total > chartData.promedio
            ? 'rgb(239, 68, 68)'
            : 'rgb(59, 130, 246)'
        ),
        borderWidth: 1,
        borderRadius: 5,
        borderSkipped: false,
        hoverBackgroundColor: items.map((d) =>
          d.total > chartData.promedio
            ? 'rgba(239, 68, 68, 1)'
            : 'rgba(59, 130, 246, 1)'
        ),
      },
    ],
  };

  const options: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: '#1F2937',
        titleColor: '#F9FAFB',
        bodyColor: '#D1D5DB',
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          title: (ctx: TooltipItem<'bar'>[]) => `Dia ${ctx[0].label}`,
          label: (ctx: TooltipItem<'bar'>) => ` ${formatCOP(ctx.raw as number)}`,
          footer: (ctx: TooltipItem<'bar'>[]) => {
            const val = ctx[0].raw as number;
            const diff = val - chartData.promedio;
            const sign = diff >= 0 ? 'sobre' : 'bajo';
            return ` ${Math.abs(diff).toLocaleString('es-CO')} COP ${sign} el promedio`;
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
          font: { size: 10 },
          color: '#9CA3AF',
          maxTicksLimit: 15,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: '#F3F4F6',
        },
        ticks: {
          font: { size: 10 },
          color: '#9CA3AF',
          callback: (value: string | number) => {
            const v = Number(value);
            if (v >= 1000000) return `$${(v / 1000000).toFixed(1)}M`;
            if (v >= 1000) return `$${(v / 1000).toFixed(0)}k`;
            return `$${v}`;
          },
        },
      },
    },
    animation: {
      duration: 600,
    },
  };

  if (loading) {
    return (
      <Card className="p-4 md:p-6">
        <div className="animate-pulse">
          <div className="h-5 w-32 bg-gray-200 rounded mb-4" />
          <div className="h-64 bg-gray-100 rounded-lg" />
        </div>
      </Card>
    );
  }

  if (!chartData) {
    return (
      <Card className="p-4 md:p-6 text-center">
        <p className="text-sm text-gray-500 mb-3">No se pudo cargar el gasto diario.</p>
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
        <h3 className="text-base font-semibold text-gray-900">Gasto diario</h3>
        <span className="text-xs text-gray-500">
          Promedio: <span className="font-semibold text-gray-700">{formatCOP(chartData.promedio)}</span>
        </span>
      </div>
      <div className="h-64">
        <Bar data={barData} options={options} />
      </div>
    </Card>
  );
}
