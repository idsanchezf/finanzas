'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Card } from '@/components/ui/Card';
import { formatCOP } from '@/lib/utils';

const MOCK_DATA = [
  { name: 'Alimentacion', value: 580000, color: '#FF6B6B' },
  { name: 'Transporte', value: 320000, color: '#4ECDC4' },
  { name: 'Vivienda', value: 750000, color: '#45B7D1' },
  { name: 'Entretenimiento', value: 280000, color: '#FFEAA7' },
  { name: 'Financieros', value: 120000, color: '#E74C3C' },
  { name: 'Otros', value: 800000, color: '#7F8C8D' },
];

export function CategoryDonut() {
  return (
    <Card>
      <h3 className="mb-4 text-base font-semibold text-gray-900">Gasto por categoria</h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={MOCK_DATA}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
          >
            {MOCK_DATA.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => formatCOP(value)} />
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            formatter={(value: string) => (
              <span className="text-xs text-gray-600">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );
}
