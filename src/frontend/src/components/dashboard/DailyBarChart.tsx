'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Card } from '@/components/ui/Card';
import { formatCOP } from '@/lib/utils';

const MOCK_DATA = Array.from({ length: 20 }, (_, i) => ({
  dia: `${i + 1}`,
  alimentacion: Math.floor(Math.random() * 50000) + 10000,
  transporte: Math.floor(Math.random() * 30000) + 5000,
  otros: Math.floor(Math.random() * 40000) + 10000,
}));

export function DailyBarChart() {
  return (
    <Card>
      <h3 className="mb-4 text-base font-semibold text-gray-900">Gasto diario</h3>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={MOCK_DATA}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="dia" tick={{ fontSize: 11 }} stroke="#9CA3AF" />
          <YAxis tick={{ fontSize: 11 }} stroke="#9CA3AF" tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} />
          <Tooltip formatter={(value: number) => formatCOP(value)} />
          <Bar dataKey="alimentacion" stackId="a" fill="#FF6B6B" name="Alimentacion" />
          <Bar dataKey="transporte" stackId="a" fill="#4ECDC4" name="Transporte" />
          <Bar dataKey="otros" stackId="a" fill="#93C5FD" name="Otros" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
