/** Servicio para operaciones de categorias via API. */
import { api } from '@/lib/api';
import type { Category } from '@/types/transaction';

/** Obtiene todas las categorias disponibles. */
export async function getCategories(): Promise<Category[]> {
  return api.get<Category[]>('/categories');
}
