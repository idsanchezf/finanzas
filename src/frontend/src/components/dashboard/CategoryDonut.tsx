'use client';

import { useRef, useState, useCallback } from 'react';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  type TooltipItem,
  type ChartOptions,
} from 'chart.js';
import { Card } from '@/components/ui/Card';
import { formatCOP, cn } from '@/lib/utils';
import type { CategoryBreakdown } from '@/types/dashboard';

ChartJS.register(ArcElement, Tooltip, Legend);

// Datos mock para desarrollo/sin backend
const MOCK_DATA: CategoryBreakdown = {
  items: [
    { categoria: 'Alimentacion', total: 580000, percentage: 22.8, color: '#FF6B6B' },
    { categoria: 'Vivienda', total: 750000, percentage: 29.5, color: '#45B7D1' },
    { categoria: 'Transporte', total: 320000, percentage: 12.6, color: '#4ECDC4' },
    { categoria: 'Entretenimiento', total: 280000, percentage: 11.0, color: '#FFEAA7' },
    { categoria: 'Suscripciones', total: 150000, percentage: 5.9, color: '#8E44AD' },
    { categoria: 'Financieros', total: 120000, percentage: 4.7, color: '#E74C3C' },
    { categoria: 'Tecnologia', total: 100000, percentage: 3.9, color: '#3498DB' },
    { categoria: 'Otros', total: 245000, percentage: 9.6, color: '#7F8C8D' },
  ],
  otros: { total: 245000, percentage: 9.6 },
};

interface CategoryDonutProps {
  data: CategoryBreakdown | null;
  loading?: boolean;
  onRetry?: () => void;
}

export function CategoryDonut({ data, loading, onRetry }: CategoryDonutProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const chartRef = useRef<ChartJS<'doughnut'>>(null);

  const handleHover = useCallback(
    (_event: unknown, elements: { index: number }[]) => {
      if (elements.length > 0) {
        setActiveIndex(elements[0].index);
      } else {
        setActiveIndex(null);
      }
    },
    []
  );

  // Usar datos mock si no hay data real (desarrollo)
  const chartData = data ?? MOCK_DATA;
  const items = chartData.items;
  const topItems = items.slice(0, 7); // Top 7

  const donutData = {
    labels: topItems.map((i) => i.categoria),
    datasets: [
      {
        data: topItems.map((i) => i.total),
        backgroundColor: topItems.map((i) => i.color),
        borderColor: '#ffffff',
        borderWidth: 2,
        hoverBorderWidth: 3,
        hoverBorderColor: '#ffffff',
        borderRadius: 4,
      },
    ],
  };

  const options: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {
      legend: {
        display: false, // Leyenda custom abajo
      },
      tooltip: {
        backgroundColor: '#1F2937',
        titleColor: '#F9FAFB',
        bodyColor: '#D1D5DB',
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        boxPadding: 3,
        callbacks: {
          label: (context: TooltipItem<'doughnut'>) => {
            const item = topItems[context.dataIndex];
            return ` ${item.categoria}: ${formatCOP(item.total)} (${item.percentage.toFixed(1)}%)`;
          },
        },
      },
    },
    onHover: handleHover as unknown as ChartOptions<'doughnut'>['onHover'],
    animation: {
      animateScale: true,
      animateRotate: true,
      duration: 800,
    },
  };

  // Loading state
  if (loading) {
    return (
      <Card className="p-4 md:p-6">
        <div className="animate-pulse">
          <div className="h-5 w-40 bg-gray-200 rounded mb-4" />
          <div className="flex flex-col lg:flex-row items-center gap-4">
            <div className="w-48 h-48 bg-gray-200 rounded-full" />
            <div className="flex-1 space-y-2 w-full">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-gray-200" />
                  <div className="h-3 flex-1 bg-gray-200 rounded" />
                  <div className="h-3 w-12 bg-gray-200 rounded" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // Error state
  if (!chartData) {
    return (
      <Card className="p-4 md:p-6 text-center">
        <p className="text-sm text-gray-500 mb-3">No se pudo cargar la distribucion por categoria.</p>
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
      <h3 className="text-base font-semibold text-gray-900 mb-4">Gasto por categoria</h3>

      <div className="flex flex-col lg:flex-row items-center gap-4">
        {/* Donut chart */}
        <div className="w-48 h-48 shrink-0">
          <Doughnut ref={chartRef} data={donutData} options={options} />
        </div>

        {/* Custom legend */}
        <div className="flex-1 w-full space-y-1.5">
          {topItems.map((item, i) => {
            const isActive = activeIndex === null || activeIndex === i;
            return (
              <div
                key={item.categoria}
                className={cn(
                  'flex items-center gap-2 px-2 py-1 rounded-md transition-all duration-200',
                  isActive ? 'bg-gray-50' : 'opacity-90'
                )}
                onMouseEnter={() => setActiveIndex(i)}
                onMouseLeave={() => setActiveIndex(null)}
              >
                <span
                  className="h-3 w-3 rounded-full shrink-0"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-gray-700 flex-1 truncate">{item.categoria}</span>
                <span className="text-xs font-semibold text-gray-900 whitespace-nowrap">
                  {formatCOP(item.total)}
                </span>
                <span className="text-xs text-gray-400 w-10 text-right">
                  {item.percentage.toFixed(1)}%
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
