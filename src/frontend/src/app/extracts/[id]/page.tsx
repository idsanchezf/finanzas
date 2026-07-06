'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { api, ApiError } from '@/lib/api';
import { formatCOP, formatDate } from '@/lib/utils';
import { STATUS_CONFIG } from '@/types/extract';
import type { Extract, ExtractStatus as ExtractStatusType } from '@/types/extract';

/**
 * Pagina de detalle de un extracto.
 * Muestra informacion completa del extracto y sus transacciones.
 */
export default function ExtractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [extract, setExtract] = useState<Extract | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pollingActive, setPollingActive] = useState(true);

  // Carga inicial
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await api.get<Extract>(`/extracts/${id}`);
        if (!cancelled) {
          setExtract(data);
          setLoading(false);

          // Si aun esta procesando, seguir haciendo polling
          if (data.estado !== 'COMPLETED' && data.estado !== 'ERROR') {
            setPollingActive(true);
          } else {
            setPollingActive(false);
          }
        }
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof ApiError ? err.message : 'Error al cargar extracto';
          setError(message);
          setLoading(false);
        }
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  // Polling para actualizaciones en tiempo real
  useEffect(() => {
    if (!pollingActive || !id) return;

    const interval = setInterval(async () => {
      try {
        const status = await api.get<{ status: ExtractStatusType; progress_pct: number }>(
          `/extracts/${id}/status`
        );

        setExtract((prev) =>
          prev
            ? {
                ...prev,
                estado: status.status,
                progress_pct: status.progress_pct,
              }
            : prev
        );

        if (status.status === 'COMPLETED' || status.status === 'ERROR') {
          setPollingActive(false);
          // Recargar completo
          const fullData = await api.get<Extract>(`/extracts/${id}`);
          setExtract(fullData);
        }
      } catch {
        // Ignorar errores de polling
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [pollingActive, id]);

  // Loading
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="mb-4 mx-auto h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-primary-500" />
          <p className="text-sm text-gray-500">Cargando extracto...</p>
        </div>
      </div>
    );
  }

  // Error
  if (error || !extract) {
    return (
      <div className="p-4 md:p-6">
        <div className="flex flex-col items-center justify-center py-20">
          <span className="text-4xl mb-4">😕</span>
          <h2 className="text-lg font-semibold text-gray-700 mb-2">
            Extracto no encontrado
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            {error ?? 'El extracto solicitado no existe o fue eliminado.'}
          </p>
          <button onClick={() => router.back()} className="btn-secondary text-sm">
            ← Volver
          </button>
        </div>
      </div>
    );
  }

  const statusConfig = STATUS_CONFIG[extract.estado] || {
    label: extract.estado,
    classes: 'bg-gray-100 text-gray-700',
  };

  return (
    <div className="space-y-6 p-4 md:p-6 animate-fade-in">
      {/* Breadcrumb */}
      <button
        onClick={() => router.push('/extracts')}
        className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        ← Extractos
      </button>

      {/* Encabezado del extracto */}
      <Card className="p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 md:text-2xl">
              {extract.banco ?? 'Extracto'}
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              {extract.periodo_inicio
                ? formatPeriodo(extract.periodo_inicio, extract.periodo_fin)
                : 'Periodo no disponible'}
            </p>
          </div>
          <span className={`badge-category text-sm self-start ${statusConfig.classes}`}>
            {statusConfig.label}
          </span>
        </div>

        {/* Progreso si esta procesando */}
        {['PENDING', 'PARSING', 'CLASSIFYING'].includes(extract.estado) && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-primary-700">
                Procesando extracto...
              </span>
              <span className="text-sm font-semibold text-primary-600">
                {extract.progress_pct}%
              </span>
            </div>
            <div
              role="progressbar"
              className="h-2 w-full rounded-full bg-gray-100 overflow-hidden"
            >
              <div
                className="h-full rounded-full bg-primary-500 transition-all duration-700 ease-out"
                style={{ width: `${extract.progress_pct}%` }}
              />
            </div>
          </div>
        )}
      </Card>

      {/* Detalles financieros (solo si completado) */}
      {extract.estado === 'COMPLETED' && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <DetailCard label="Pago total" value={formatCOP(extract.pago_total || extract.total || 0)} />
          <DetailCard label="Pago minimo" value={formatCOP(extract.pago_minimo)} />
          <DetailCard label="Cupo total" value={formatCOP(extract.cupo_total)} />
          <DetailCard
            label="Cupo disponible"
            value={formatCOP(extract.cupo_disponible)}
            highlight={extract.cupo_total > 0 && extract.cupo_disponible / extract.cupo_total < 0.3}
          />
        </div>
      )}

      {/* Fechas clave */}
      <Card className="p-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">
          Fechas del periodo
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {extract.periodo_inicio && (
            <DateItem label="Inicio del periodo" date={extract.periodo_inicio} />
          )}
          {extract.periodo_fin && (
            <DateItem label="Fin del periodo" date={extract.periodo_fin} />
          )}
          {extract.fecha_corte && (
            <DateItem label="Fecha de corte" date={extract.fecha_corte} />
          )}
          {extract.fecha_limite_pago && (
            <DateItem label="Fecha limite de pago" date={extract.fecha_limite_pago} highlight />
          )}
          <DateItem label="Fecha de carga" date={extract.created_at} />
        </div>
      </Card>

      {/* Transacciones (placeholder) */}
      {extract.estado === 'COMPLETED' && (
        <Card className="p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            Transacciones
          </h2>
          <p className="text-sm text-gray-500">
            {extract.transacciones != null && extract.transacciones > 0
              ? `${extract.transacciones} transacciones en este extracto.`
              : 'Cargando lista de transacciones...'}
          </p>
          <button
            onClick={() =>
              router.push(`/transactions?extracto_id=${extract.id}`)
            }
            className="btn-secondary text-sm mt-3"
          >
            Ver todas las transacciones
          </button>
        </Card>
      )}
    </div>
  );
}

// ---- Sub-componentes ----

function DetailCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <Card className={`p-4 ${highlight ? 'border-warning-300 bg-warning-50/50' : ''}`}>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p
        className={`text-lg font-bold ${
          highlight ? 'text-warning-700' : 'text-gray-900'
        }`}
      >
        {value}
      </p>
    </Card>
  );
}

function DateItem({
  label,
  date,
  highlight,
}: {
  label: string;
  date: string;
  highlight?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between rounded-lg border p-3 ${highlight ? 'border-warning-300 bg-warning-50/50' : 'border-gray-100'}`}>
      <span className="text-xs text-gray-500">{label}</span>
      <span
        className={`text-sm font-medium ${highlight ? 'text-warning-700' : 'text-gray-900'}`}
      >
        {formatDate(date)}
      </span>
    </div>
  );
}

// ---- Utilidades locales ----

function formatPeriodo(start: string, end: string | null): string {
  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];
  try {
    const dStart = new Date(start);
    const startStr = `${months[dStart.getMonth()]} ${dStart.getFullYear()}`;
    if (end) {
      const dEnd = new Date(end);
      const endStr = `${months[dEnd.getMonth()]} ${dEnd.getFullYear()}`;
      return startStr === endStr ? startStr : `${startStr} — ${endStr}`;
    }
    return startStr;
  } catch {
    return start ?? 'N/A';
  }
}
