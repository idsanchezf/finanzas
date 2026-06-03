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
}

export interface ExtractUploadResponse {
  extract_id: string;
  estado: string;
  progress_pct: number;
}

export interface ExtractStatusResponse {
  status: ExtractStatus;
  progress_pct: number;
  message: string | null;
}
