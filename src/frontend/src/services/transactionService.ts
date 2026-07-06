/** Servicio para operaciones de transacciones via API. */
import { api } from '@/lib/api';
import type {
  Transaction,
  TransactionListResponse,
  TransactionFilters,
  BulkCategoryUpdate,
} from '@/types/transaction';

/** Obtiene listado paginado de transacciones con filtros. */
export async function getTransactions(
  filters: TransactionFilters
): Promise<TransactionListResponse> {
  return api.get<TransactionListResponse>('/transactions', filters as Record<string, string | number | undefined>);
}

/** Actualiza la categoria de una transaccion. */
export async function updateTransactionCategory(
  id: string,
  categoryId: string
): Promise<Transaction> {
  return api.patch<Transaction>(`/transactions/${id}/category`, {
    category_id: categoryId,
  });
}

/** Actualiza la categoria de multiples transacciones en lote. */
export async function bulkUpdateCategory(data: BulkCategoryUpdate): Promise<void> {
  await api.patch('/transactions/bulk/category', data);
}

/** Obtiene una transaccion por ID con detalle completo. */
export async function getTransactionById(id: string): Promise<Transaction> {
  return api.get<Transaction>(`/transactions/${id}`);
}
