/** Tipos para transacciones. */

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
  confidence: number | null;
  es_cuota: boolean;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  size: number;
}
