'use client';

import { cn } from '@/lib/utils';

interface TransactionErrorProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

/** Estado de error con boton de reintentar. */
export function TransactionError({
  message = 'Error al cargar las transacciones',
  onRetry,
  className,
}: TransactionErrorProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      <div className="mb-4 text-6xl">⚠️</div>
      <h3 className="mb-2 text-lg font-semibold text-gray-800">Algo salio mal</h3>
      <p className="mb-6 max-w-sm text-sm text-gray-500">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-primary text-sm">
          Reintentar
        </button>
      )}
    </div>
  );
}
