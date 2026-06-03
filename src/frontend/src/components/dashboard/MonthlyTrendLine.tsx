'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card } from '@/components/ui/Card';
import { formatCOP } from '@/lib/utils';

const MOCK_DATA = [
  { mes: 'Ene', gastos: 2700000, ingresos: 5000000 },
  { mes: 'Feb', gastos: 2900000, ingresos: 5100000 },
  { mes: 'Mar', gastos: 3100000, ingresos: 5200000 },
  { mes: 'Abr', gastos: 2800000, ingresos: 5000000 },
  { mes: 'May', gastos: 3200000, ingresos: 5400000 },
  { mes: 'Jun', gastos: 2850000, ingresos: 5200000 },
];

export function MonthlyTrendLine() {
  return (
    <Card>
      <h3 className="mb-4 text-base font-semibold text-gray-900">Tendencia mensual</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={MOCK_DATA}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="#9CA3AF" />
          <YAxis tick={{ fontSize: 12 }} stroke="#9CA3AF" tickFormatter={(v: number) => `${(v / 1000000).toFixed(1)}M`} />
          <Tooltip formatter={(value: number) => formatCOP(value)} />
          <Legend />
          <Line type="monotone" dataKey="gastos" stroke="#EF4444" strokeWidth={2} name="Gastos" dot={{ r: 4 }} />
          <Line type="monotone" dataKey="ingresos" stroke="#10B981" strokeWidth={2} name="Ingresos" dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
