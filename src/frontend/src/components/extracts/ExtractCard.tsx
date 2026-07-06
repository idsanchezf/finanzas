'use client';

import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { formatCOP, formatDate } from '@/lib/utils';
import { STATUS_CONFIG } from '@/types/extract';
import type { Extract, ExtractStatus } from '@/types/extract';

interface ExtractCardProps {
  extract: Extract;
}

/**
 * Tarjeta de extracto que muestra:
 * - Periodo, banco, # transacciones, estado, fecha de carga
 * - Badge de estado con colores semanticos
 * - Barra de progreso durante procesamiento
 * - Click para ver detalle del extracto
 */
export function ExtractCard({ extract }: ExtractCardProps) {
  const router = useRouter();
  const statusConfig = STATUS_CONFIG[extract.estado] || {
    label: extract.estado,
    classes: 'bg-gray-100 text-gray-700',
  };

  const isProcessing = ['PENDING', 'PARSING', 'CLASSIFYING'].includes(extract.estado);
  const isError = extract.estado === 'ERROR';
  const isComplete = extract.estado === 'COMPLETED';

  const handleClick = () => {
    router.push(`/extracts/${extract.id}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  // Formatear periodo
  const periodoStr = extract.periodo_inicio
    ? formatMonthYear(extract.periodo_inicio, extract.periodo_fin)
    : 'Periodo pendiente';

  // Formatear fecha de carga
  const fechaCarga = formatDate(extract.created_at);

  return (
    <Card
      className="p-4 transition-all hover:shadow-md focus-within:ring-2 focus-within:ring-primary-500 cursor-pointer animate-fade-in"
      onClick={handleClick}
    >
      <div
        role="button"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        className="focus:outline-none"
        aria-label={`Extracto ${periodoStr} - ${extract.banco ?? 'Banco desconocido'} - ${statusConfig.label}`}
      >
        {/* Encabezado: Banco + Badge */}
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-semibold text-gray-900">
              {extract.banco ?? 'Banco'}
            </p>
            <p className="text-xs text-gray-500">{periodoStr}</p>
            <p className="text-xs text-gray-400 mt-0.5">{fechaCarga}</p>
          </div>
          <span className={`badge-category text-xs ${statusConfig.classes}`}>
            {statusConfig.label}
          </span>
        </div>

        {/* Barra de progreso (solo durante procesamiento) */}
        {isProcessing && (
          <div className="mt-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500">
                {extract.estado === 'PENDING' && 'En cola...'}
                {extract.estado === 'PARSING' && 'Analizando archivo...'}
                {extract.estado === 'CLASSIFYING' && 'Clasificando transacciones...'}
              </span>
              <span className="text-xs font-medium text-primary-600">
                {extract.progress_pct}%
              </span>
            </div>
            <div
              role="progressbar"
              aria-valuenow={extract.progress_pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Progreso de procesamiento"
              className="h-1.5 w-full rounded-full bg-gray-100 overflow-hidden"
            >
              <div
                className="h-full rounded-full bg-primary-500 transition-all duration-700 ease-out"
                style={{ width: `${extract.progress_pct}%` }}
              />
            </div>
          </div>
        )}

        {/* Mensaje de error */}
        {isError && extract.message && (
          <div className="mt-3 rounded-md bg-danger-50 p-2 text-xs text-danger-700">
            ⚠️ {extract.message}
          </div>
        )}

        {/* Informacion financiera (solo completado) */}
        <div className="mt-4 flex items-end justify-between">
          <div>
            {isComplete && (
              <>
                <p className="text-lg font-bold text-gray-900">
                  {formatCOP(extract.total ?? extract.pago_total)}
                </p>
                <p className="text-xs text-gray-500">
                  {extract.transacciones != null && extract.transacciones > 0
                    ? `${extract.transacciones} transacciones`
                    : 'Cargando datos...'}
                </p>
              </>
            )}
            {isProcessing && (
              <p className="text-sm text-gray-400 italic">Procesando extracto...</p>
            )}
            {isError && (
              <p className="text-sm text-danger-600 font-medium">
                Reintentar carga
              </p>
            )}
          </div>
          <span className="text-sm text-primary-600 hover:text-primary-800 transition-colors">
            Ver detalle →
          </span>
        </div>
      </div>
    </Card>
  );
}

/** Formatea un periodo a partir de fechas ISO (usa UTC para evitar timezone issues). */
function formatMonthYear(start: string, end: string | null): string {
  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];

  try {
    // Usar parsing manual para evitar desplazamiento de timezone
    const parts = start.split('-');
    const month = months[parseInt(parts[1], 10) - 1];
    const year = parts[0];
    return `${month} ${year}`;
  } catch {
    return start;
  }
}
