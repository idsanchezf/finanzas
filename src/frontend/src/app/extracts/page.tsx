'use client';

import { useState, useCallback } from 'react';
import { UploadForm } from '@/components/extracts/UploadForm';
import { ExtractCard } from '@/components/extracts/ExtractCard';
import { useExtracts } from '@/hooks/useExtracts';
import { useToast } from '@/components/ui/Toast';
import type { Extract, ExtractStatusResponse } from '@/types/extract';

/**
 * Pagina de extractos:
 * - Lista de extractos cargados con ExtractCard
 * - Boton "Cargar extracto" que muestra el formulario
 * - Estado vacio cuando no hay extractos
 * - Toast notifications para exito/error
 */
export default function ExtractsPage() {
  const { extracts, loading, error, addExtract, updateExtract, refresh } =
    useExtracts();
  const { addToast } = useToast();
  const [showUpload, setShowUpload] = useState(false);

  const handleUploadComplete = useCallback(
    (extractId: string, status: ExtractStatusResponse) => {
      // Crear un extracto optimista para mostrarlo inmediatamente
      const newExtract: Extract = {
        id: extractId,
        tarjeta_id: '',
        estado: 'COMPLETED',
        periodo_inicio: status.periodo_inicio ?? null,
        periodo_fin: status.periodo_fin ?? null,
        fecha_corte: null,
        fecha_limite_pago: null,
        pago_minimo: 0,
        pago_total: 0,
        cupo_total: 0,
        cupo_disponible: 0,
        progress_pct: 100,
        created_at: new Date().toISOString(),
        transacciones: status.transacciones_extraidas ?? 0,
        message: status.message,
      };

      addExtract(newExtract);
      setShowUpload(false);

      addToast(
        'success',
        status.transacciones_extraidas != null
          ? `¡Listo! Se extrajeron ${status.transacciones_extraidas} transacciones.`
          : '¡Extracto procesado exitosamente!'
      );

      // Refrescar la lista del backend para obtener datos completos
      setTimeout(() => refresh(), 1000);
    },
    [addExtract, refresh, addToast]
  );

  const handleUploadError = useCallback(
    (errorMsg: string) => {
      addToast('error', errorMsg || 'Error al procesar el extracto.');
    },
    [addToast]
  );

  return (
    <div className="space-y-6 p-4 md:p-6 animate-fade-in">
      {/* Encabezado */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 md:text-3xl">
            Extractos
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Gestiona tus extractos bancarios y su procesamiento
          </p>
        </div>
        {!showUpload && (
          <button
            onClick={() => setShowUpload(true)}
            className="btn-primary text-sm self-start"
          >
            <svg
              className="h-4 w-4 mr-1.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 6v6m0 0v6m0-6h6m-6 0H6"
              />
            </svg>
            Cargar extracto
          </button>
        )}
      </div>

      {/* Formulario de carga */}
      {showUpload && (
        <div className="animate-slide-up">
          <UploadForm
            onUploadComplete={handleUploadComplete}
            onUploadError={handleUploadError}
          />
          <button
            onClick={() => setShowUpload(false)}
            className="mt-3 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            ← Volver a la lista
          </button>
        </div>
      )}

      {/* Estado de carga */}
      {loading && !showUpload && (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400">
          <div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-primary-500" />
          <p className="text-sm">Cargando extractos...</p>
        </div>
      )}

      {/* Estado de error */}
      {error && !loading && (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="rounded-lg border border-danger-200 bg-danger-50 p-6 text-center max-w-md">
            <span className="text-3xl mb-3 block">⚠️</span>
            <p className="text-sm font-medium text-danger-700 mb-3">{error}</p>
            <button onClick={refresh} className="btn-secondary text-sm">
              Reintentar
            </button>
          </div>
        </div>
      )}

      {/* Lista de extractos */}
      {!loading && !error && (
        <>
          {extracts.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {extracts.map((extract) => (
                <ExtractCard key={extract.id} extract={extract} />
              ))}
            </div>
          ) : (
            !showUpload && (
              /* Estado vacio */
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-gray-100">
                  <svg
                    className="h-10 w-10 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-700 mb-1">
                  No tienes extractos
                </h3>
                <p className="text-sm text-gray-500 mb-6 max-w-xs">
                  Carga tu primer extracto bancario en formato Excel (.xlsx)
                  para empezar a analizar tus gastos.
                </p>
                <button
                  onClick={() => setShowUpload(true)}
                  className="btn-primary text-sm"
                >
                  <svg
                    className="h-4 w-4 mr-1.5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                    />
                  </svg>
                  Cargar mi primer extracto
                </button>
              </div>
            )
          )}
        </>
      )}
    </div>
  );
}
