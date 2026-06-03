'use client';

import { SummaryCards } from '@/components/dashboard/SummaryCards';
import { CategoryDonut } from '@/components/dashboard/CategoryDonut';
import { DailyBarChart } from '@/components/dashboard/DailyBarChart';
import { MonthlyTrendLine } from '@/components/dashboard/MonthlyTrendLine';

export default function DashboardPage() {
  return (
    <div className="space-y-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 md:text-3xl">Dashboard</h1>
          <p className="text-sm text-gray-500">Resumen de tus finanzas del periodo actual</p>
        </div>
        <button className="btn-primary text-sm">
          <span className="mr-2">📤</span>
          Cargar extracto
        </button>
      </div>

      {/* KPIs */}
      <SummaryCards />

      {/* Graficos */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CategoryDonut />
        <DailyBarChart />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-1">
        <MonthlyTrendLine />
      </div>

      {/* Seccion de habitos / alertas */}
      <div className="card">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">Alertas y recomendaciones</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <span className="text-xl">⚠️</span>
            <div>
              <p className="text-sm font-medium text-amber-800">Gasto hormiga detectado</p>
              <p className="text-xs text-amber-600">
                12 compras menores a $15,000 COP suman $128,500 este mes.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-3">
            <span className="text-xl">💡</span>
            <div>
              <p className="text-sm font-medium text-green-800">Oportunidad de ahorro</p>
              <p className="text-xs text-green-600">
                Reduciendo un 20% en alimentacion ahorrarias $85,000 al mes.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
