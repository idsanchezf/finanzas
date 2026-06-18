'use client';

import { cn } from '@/lib/utils';

interface TransactionEmptyProps {
  hasFilters?: boolean;
  onClearFilters?: () => void;
  className?: string;
}

/** Estado vacio: sin transacciones. */
export function TransactionEmpty({ hasFilters = false, onClearFilters, className }: TransactionEmptyProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      <div className="mb-4 text-6xl">📭</div>
      <h3 className="mb-2 text-lg font-semibold text-gray-800">
        {hasFilters ? 'Sin resultados' : 'No se encontraron transacciones'}
      </h3>
      <p className="mb-6 max-w-sm text-sm text-gray-500">
        {hasFilters
          ? 'Intenta ajustar los filtros de busqueda para encontrar lo que necesitas.'
          : 'Carga tu primer extracto bancario para empezar a clasificar tus gastos.'}
      </p>
      {hasFilters && onClearFilters && (
        <button
          onClick={onClearFilters}
          className="btn-secondary text-sm"
        >
          Limpiar filtros
        </button>
      )}
    </div>
  );
}
