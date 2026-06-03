'use client';

import { Card } from '@/components/ui/Card';
import { formatCOP } from '@/lib/utils';

export function SummaryCards() {
  const kpis = [
    { label: 'Total gastado', value: formatCOP(2850000), change: '+12%', trend: 'up', icon: '💳' },
    { label: 'Total ingresos', value: formatCOP(5200000), change: '+5%', trend: 'up', icon: '💰' },
    { label: 'Promedio diario', value: formatCOP(92000), change: '-3%', trend: 'down', icon: '📊' },
    { label: 'Cupo utilizado', value: '45%', change: '', trend: 'neutral', icon: '📈' },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {kpis.map((kpi) => (
        <Card key={kpi.label} className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-2xl">{kpi.icon}</span>
            {kpi.change && (
              <span
                className={`text-xs font-medium ${
                  kpi.trend === 'up' ? 'text-danger-500' : 'text-success-500'
                }`}
              >
                {kpi.change}
              </span>
            )}
          </div>
          <p className="mt-2 text-lg font-bold text-gray-900 md:text-xl">{kpi.value}</p>
          <p className="text-xs text-gray-500">{kpi.label}</p>
        </Card>
      ))}
    </div>
  );
}
