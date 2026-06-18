/** Tipos para extractos bancarios. */

export type ExtractStatus = 'PENDING' | 'PARSING' | 'CLASSIFYING' | 'COMPLETED' | 'ERROR';

export interface Extract {
  id: string;
  tarjeta_id: string;
  estado: ExtractStatus;
  periodo_inicio: string | null;
  periodo_fin: string | null;
  fecha_corte: string | null;
  fecha_limite_pago: string | null;
  pago_minimo: number;
  pago_total: number;
  cupo_total: number;
  cupo_disponible: number;
  progress_pct: number;
  created_at: string;
  // Campos extendidos (enriquecidos por el frontend o el backend)
  banco?: string;
  total?: number;
  transacciones?: number;
  message?: string | null;
}

export interface ExtractUploadResponse {
  extract_id: string;
  estado: string;
  progress_pct: number;
  status_url?: string;
  estimated_seconds?: number;
}

export interface ExtractStatusResponse {
  status: ExtractStatus;
  progress_pct: number;
  message: string | null;
  transacciones_extraidas?: number;
  periodo_inicio?: string;
  periodo_fin?: string;
}

export interface ExtractListResponse {
  items: Extract[];
  total: number;
}

/** Configuracion de badge por estado. */
export interface StatusBadgeConfig {
  label: string;
  classes: string;
}

export const STATUS_CONFIG: Record<ExtractStatus, StatusBadgeConfig> = {
  COMPLETED: { label: 'Completado', classes: 'bg-success-50 text-success-700' },
  PARSING: { label: 'Procesando', classes: 'bg-primary-50 text-primary-700' },
  CLASSIFYING: { label: 'Clasificando', classes: 'bg-primary-50 text-primary-700' },
  PENDING: { label: 'Pendiente', classes: 'bg-warning-50 text-warning-700' },
  ERROR: { label: 'Error', classes: 'bg-danger-50 text-danger-700' },
};
