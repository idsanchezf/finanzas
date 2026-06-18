/** Tipos para transacciones y categorias. */

export interface Transaction {
  id: string;
  extracto_id: string;
  autorizacion: string | null;
  fecha: string | null;
  comercio: string;
  comercio_traducido: string | null;
  valor: number;
  cuotas: string | null;
  cuotas_totales: number | null;
  cuota_actual: number | null;
  moneda_original: string | null;
  valor_moneda_original: number | null;
  categoria_id: string | null;
  categoria?: Category;
  confidence: number | null;
  es_cuota: boolean;
  /** Campos de detalle (disponibles en endpoint individual) */
  cuota_valor?: number | null;
  interes_mensual?: number | null;
  interes_anual?: number | null;
  saldo_pendiente?: number | null;
  /** Historial de cambios de categoria */
  category_history?: CategoryHistory[];
}

export interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
  is_default: boolean;
  user_id?: string | null;
}

export interface CategoryHistory {
  id: string;
  previous_category_id: string | null;
  new_category_id: string;
  changed_at: string;
  changed_by: string | null;
}

export interface TransactionListResponse {
  items: Transaction[];
  next_cursor: string | null;
  has_more: boolean;
  total?: number;
}

export interface TransactionFilters {
  search?: string;
  category_id?: string;
  periodo?: string;
  confidence_min?: number;
  confidence_max?: number;
  sort_by?: 'fecha' | 'valor' | 'comercio';
  sort_order?: 'asc' | 'desc';
  cursor?: string;
  limit?: number;
}

export type ConfidenceLevel = 'alta' | 'media' | 'baja' | 'sin_clasificar';

export interface BulkCategoryUpdate {
  transaction_ids: string[];
  category_id: string;
}
