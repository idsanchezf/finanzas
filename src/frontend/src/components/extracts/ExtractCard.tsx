'use client';

import { Card } from '@/components/ui/Card';
import { formatCOP } from '@/lib/utils';

interface ExtractCardProps {
  banco: string;
  periodo: string;
  estado: string;
  total: number;
  transacciones: number;
}

export function ExtractCard({ banco, periodo, estado, total, transacciones }: ExtractCardProps) {
  const estadoConfig: Record<string, { label: string; color: string }> = {
    COMPLETED: { label: 'Completado', color: 'bg-green-100 text-green-700' },
    PENDING: { label: 'Pendiente', color: 'bg-yellow-100 text-yellow-700' },
    ERROR: { label: 'Error', color: 'bg-red-100 text-red-700' },
    PARSING: { label: 'Procesando', color: 'bg-blue-100 text-blue-700' },
  };

  const estadoInfo = estadoConfig[estado] || { label: estado, color: 'bg-gray-100 text-gray-700' };

  return (
    <Card className="p-4 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-900">{banco}</p>
          <p className="text-xs text-gray-500">{periodo}</p>
        </div>
        <span className={`badge-category ${estadoInfo.color}`}>{estadoInfo.label}</span>
      </div>
      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="text-lg font-bold text-gray-900">{formatCOP(total)}</p>
          <p className="text-xs text-gray-500">{transacciones} transacciones</p>
        </div>
        <button className="text-sm text-primary-600 hover:text-primary-800">Ver detalle →</button>
      </div>
    </Card>
  );
}
