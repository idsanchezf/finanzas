'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { api, ApiError } from '@/lib/api';
import type { ExtractUploadResponse, ExtractStatusResponse } from '@/types/extract';

interface Tarjeta {
  id: string;
  banco: string;
  ultimos_4_digitos: string;
  alias?: string | null;
}

interface UploadFormProps {
  tarjetas?: Tarjeta[];
  onUploadComplete?: (extractId: string, summary: ExtractStatusResponse) => void;
  onUploadError?: (error: string) => void;
}

/** Tamaño maximo de archivo: 10MB */
const MAX_FILE_SIZE = 10 * 1024 * 1024;

/** Intervalo de polling (ms) */
const POLL_INTERVAL_MS = 2500;

/** Extensiones aceptadas */
const ACCEPTED_EXTENSIONS = ['.xlsx', '.xls'];

/** Estado interno del formulario */
type FormState =
  | 'idle'
  | 'selected'
  | 'uploading'
  | 'polling'
  | 'completed'
  | 'error';

/**
 * Formulario de carga de extracto bancario con:
 * - Dropzone para arrastrar/soltar archivos Excel
 * - Validacion de formato y tamaño (max 10MB)
 * - Vista previa del archivo seleccionado
 * - Selector de tarjeta
 * - Barra de progreso durante upload
 * - Polling de estado post-upload con progreso visual
 * - Feedback: subiendo → procesando → completado → error
 */
export function UploadForm({
  tarjetas = [],
  onUploadComplete,
  onUploadError,
}: UploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [formState, setFormState] = useState<FormState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [pollProgress, setPollProgress] = useState(0);
  const [pollMessage, setPollMessage] = useState<string>('');
  const [extractId, setExtractId] = useState<string | null>(null);
  const [summary, setSummary] = useState<ExtractStatusResponse | null>(null);
  const [selectedTarjetaId, setSelectedTarjetaId] = useState<string>(
    tarjetas[0]?.id ?? ''
  );

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);
  const [isDragOver, setIsDragOver] = useState(false);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
      }
    };
  }, []);

  /** Valida el archivo seleccionado. */
  const validateFile = useCallback((f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return `Formato no soportado. Solo se aceptan archivos Excel (${ACCEPTED_EXTENSIONS.join(', ')}).`;
    }
    if (f.size > MAX_FILE_SIZE) {
      return `El archivo excede el tamaño maximo permitido de 10MB. Tamaño actual: ${formatFileSize(f.size)}.`;
    }
    if (f.size === 0) {
      return 'El archivo esta vacio. Por favor selecciona un archivo valido.';
    }
    return null;
  }, []);

  /** Procesa la seleccion/arrastre de archivo */
  const handleFile = useCallback(
    (f: File) => {
      const validationError = validateFile(f);
      if (validationError) {
        setError(validationError);
        setFile(null);
        setFormState('error');
        return;
      }
      setError(null);
      setFile(f);
      setFormState('selected');
    },
    [validateFile]
  );

  // Drag & Drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragOver(true);
    }
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragOver(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      dragCounter.current = 0;

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        handleFile(droppedFile);
      }
    },
    [handleFile]
  );

  // File input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFile(selectedFile);
    }
    // Reset input para permitir re-seleccion del mismo archivo
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  /** Inicia el upload del archivo. */
  const handleUpload = async () => {
    if (!file) return;

    setFormState('uploading');
    setUploadProgress(0);
    setError(null);
    setPollProgress(0);
    setPollMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const queryParams: string[] = [];
      if (selectedTarjetaId) {
        queryParams.push(`tarjeta_id=${encodeURIComponent(selectedTarjetaId)}`);
      }

      const path = `/extracts/upload${queryParams.length ? '?' + queryParams.join('&') : ''}`;

      // Simular progreso de upload
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          const next = prev + Math.random() * 20;
          return next >= 90 ? 90 : next;
        });
      }, 200);

      const result = await api.upload<ExtractUploadResponse>(path, formData);

      clearInterval(progressInterval);
      setUploadProgress(100);

      // Iniciar polling
      setExtractId(result.extract_id);
      setFormState('polling');
      setPollProgress(result.progress_pct ?? 0);

      startPolling(result.extract_id);
    } catch (err) {
      setFormState('error');
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Error al subir el archivo';
      setError(message);
      onUploadError?.(message);
    }
  };

  /** Inicia el polling del estado de procesamiento. */
  const startPolling = (id: string) => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }

    pollRef.current = setInterval(async () => {
      try {
        const status = await api.get<ExtractStatusResponse>(
          `/extracts/${id}/status`
        );

        setPollProgress(status.progress_pct);
        setPollMessage(status.message ?? getPollMessage(status.status));

        if (status.status === 'COMPLETED') {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setFormState('completed');
          setSummary(status);
          setFile(null);
          onUploadComplete?.(id, status);
        } else if (status.status === 'ERROR') {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setFormState('error');
          setError(status.message ?? 'Error en el procesamiento del extracto.');
          onUploadError?.(status.message ?? 'Error desconocido.');
        }
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : 'Error al verificar estado.';
        // No paramos el polling por errores de red, pero si por 404
        if (err instanceof ApiError && err.status === 404) {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setFormState('error');
          setError('Extracto no encontrado.');
        }
      }
    }, POLL_INTERVAL_MS);
  };

  /** Reinicia el formulario para una nueva carga. */
  const handleReset = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setFile(null);
    setFormState('idle');
    setError(null);
    setUploadProgress(0);
    setPollProgress(0);
    setPollMessage('');
    setExtractId(null);
    setSummary(null);
  };

  /** Retry after error */
  const handleRetry = () => {
    handleReset();
  };

  return (
    <Card className="p-4 md:p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Cargar nuevo extracto
        </h2>
        {file && formState !== 'idle' && (
          <button
            onClick={handleReset}
            className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
            title="Cancelar y empezar de nuevo"
          >
            Cancelar
          </button>
        )}
      </div>

      {/* Selector de tarjeta */}
      {tarjetas.length > 1 && formState === 'idle' && (
        <div className="mb-4">
          <label
            htmlFor="tarjeta-select"
            className="block text-xs font-medium text-gray-600 mb-1"
          >
            Tarjeta
          </label>
          <select
            id="tarjeta-select"
            value={selectedTarjetaId}
            onChange={(e) => setSelectedTarjetaId(e.target.value)}
            className="input-field text-sm"
          >
            {tarjetas.map((t) => (
              <option key={t.id} value={t.id}>
                {t.banco} — ****{t.ultimos_4_digitos}
                {t.alias ? ` (${t.alias})` : ''}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Zona de drop / Seleccion de archivo */}
      {formState !== 'uploading' && formState !== 'polling' && formState !== 'completed' && (
        <div
          onDrop={handleDrop}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 md:p-8 transition-all duration-200 ${
            isDragOver
              ? 'border-primary-400 bg-primary-50 scale-[1.02]'
              : 'border-gray-300 hover:border-primary-400'
          } ${file ? 'bg-primary-50/50' : ''}`}
        >
          {/* Icono de upload */}
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary-100">
            <svg
              className="h-6 w-6 text-primary-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          <p className="mb-1 text-sm font-medium text-gray-700">
            Arrastra tu extracto aqui o haz clic para seleccionar
          </p>
          <p className="mb-4 text-xs text-gray-500">
            Formatos aceptados: .xlsx, .xls. Maximo 10MB.
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
            data-testid="file-input"
          />
          <label
            htmlFor="file-upload"
            className="btn-secondary cursor-pointer text-sm"
          >
            Seleccionar archivo
          </label>
        </div>
      )}

      {/* Vista previa del archivo seleccionado */}
      {file && (formState === 'selected' || formState === 'error') && (
        <div className="mt-4 animate-slide-up">
          <div className="flex items-center justify-between rounded-lg bg-primary-50 p-3">
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-2xl flex-shrink-0">📊</span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-primary-800 truncate">
                  {file.name}
                </p>
                <p className="text-xs text-primary-600">
                  {formatFileSize(file.size)}
                </p>
              </div>
            </div>
            <button
              onClick={handleUpload}
              className="btn-primary text-sm ml-3 flex-shrink-0"
            >
              Procesar
            </button>
          </div>
        </div>
      )}

      {/* Barra de progreso — Upload en curso */}
      {formState === 'uploading' && (
        <div className="mt-4 animate-slide-up">
          <div className="rounded-lg border border-primary-100 bg-primary-50/50 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-primary-700">
                Subiendo archivo...
              </span>
              <span className="text-sm font-semibold text-primary-600">
                {Math.round(uploadProgress)}%
              </span>
            </div>
            <div
              role="progressbar"
              aria-valuenow={uploadProgress}
              aria-valuemin={0}
              aria-valuemax={100}
              className="h-2 w-full rounded-full bg-primary-100 overflow-hidden"
            >
              <div
                className="h-full rounded-full bg-primary-500 transition-all duration-300 ease-out"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Progreso de procesamiento (polling) */}
      {formState === 'polling' && (
        <div className="mt-4 animate-slide-up">
          <div className="rounded-lg border border-primary-100 bg-primary-50/50 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-primary-700">
                {pollMessage || 'Procesando extracto...'}
              </span>
              <span className="text-sm font-semibold text-primary-600">
                {pollProgress}%
              </span>
            </div>
            <div
              role="progressbar"
              aria-valuenow={pollProgress}
              aria-valuemin={0}
              aria-valuemax={100}
              className="h-2 w-full rounded-full bg-primary-100 overflow-hidden"
            >
              <div
                className="h-full rounded-full bg-primary-500 transition-all duration-700 ease-out"
                style={{ width: `${pollProgress}%` }}
              />
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-primary-600">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-300 border-t-primary-600" />
              {extractId && (
                <span className="text-primary-400 font-mono text-[10px] truncate">
                  ID: {extractId}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Completado */}
      {formState === 'completed' && summary && (
        <div className="mt-4 animate-slide-up">
          <div className="rounded-lg border border-success-200 bg-success-50 p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-success-500 text-white">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-success-700">
                  ¡Extracto procesado exitosamente!
                </p>
                <p className="text-xs text-success-600">
                  {summary.transacciones_extraidas != null
                    ? `${summary.transacciones_extraidas} transacciones extraidas`
                    : 'Procesamiento completado'}
                </p>
              </div>
            </div>
            {(summary.periodo_inicio || summary.periodo_fin) && (
              <p className="text-xs text-success-600 mb-3">
                Periodo:{' '}
                {summary.periodo_inicio && summary.periodo_fin
                  ? `${formatShortDate(summary.periodo_inicio)} — ${formatShortDate(summary.periodo_fin)}`
                  : 'N/A'}
              </p>
            )}
            <button onClick={handleReset} className="btn-secondary text-sm w-full">
              Cargar otro extracto
            </button>
          </div>
        </div>
      )}

      {/* Mensaje de error */}
      {formState === 'error' && error && (
        <div className="mt-4 animate-slide-up">
          <div className="rounded-lg border border-danger-200 bg-danger-50 p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-danger-100">
                <svg className="h-4 w-4 text-danger-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-danger-700">Error al procesar</p>
                <p className="text-xs text-danger-600 mt-0.5 break-words">{error}</p>
              </div>
            </div>
            <div className="mt-3 flex gap-2">
              <button onClick={handleRetry} className="btn-primary text-xs flex-1">
                Reintentar
              </button>
              <button onClick={handleReset} className="btn-secondary text-xs flex-1">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

/** Obtiene el mensaje descriptivo segun estado de procesamiento. */
function getPollMessage(status: string): string {
  switch (status) {
    case 'PENDING':
      return 'Extracto en cola de procesamiento...';
    case 'PARSING':
      return 'Analizando archivo Excel...';
    case 'CLASSIFYING':
      return 'Clasificando transacciones...';
    case 'COMPLETED':
      return 'Procesamiento completado';
    case 'ERROR':
      return 'Error en el procesamiento';
    default:
      return 'Procesando...';
  }
}

/** Formatea el tamaño de archivo en formato legible. */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const size = parseFloat((bytes / Math.pow(k, i)).toFixed(1));
  return `${size} ${sizes[i]}`;
}

/** Formatea una fecha ISO a formato corto. */
function formatShortDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('es-CO', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}
