'use client';

import { cn } from '@/lib/utils';

interface TransactionSkeletonProps {
  rows?: number;
  className?: string;
}

/** Skeleton rows para estado de carga de la tabla de transacciones. */
export function TransactionSkeleton({ rows = 5, className }: TransactionSkeletonProps) {
  return (
    <div className={cn('space-y-0', className)}>
      {/* Desktop skeleton table */}
      <div className="hidden md:block">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              {['', 'Fecha', 'Comercio', 'Categoria', 'Valor', 'Cuotas', 'Confianza'].map(
                (header, i) => (
                  <th
                    key={i}
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
                  >
                    {header}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, i) => (
              <tr key={i} className="border-b border-gray-100">
                <td className="px-4 py-3">
                  <div className="h-4 w-4 animate-pulse rounded bg-gray-200" />
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 w-20 animate-pulse rounded bg-gray-200" />
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 w-40 animate-pulse rounded bg-gray-200" />
                </td>
                <td className="px-4 py-3">
                  <div className="h-5 w-24 animate-pulse rounded-full bg-gray-200" />
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 w-24 animate-pulse rounded bg-gray-200" />
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 w-12 animate-pulse rounded bg-gray-200" />
                </td>
                <td className="px-4 py-3">
                  <div className="h-5 w-20 animate-pulse rounded-full bg-gray-200" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile skeleton cards */}
      <div className="space-y-3 md:hidden">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="h-4 w-28 animate-pulse rounded bg-gray-200" />
                <div className="h-4 w-44 animate-pulse rounded bg-gray-200" />
                <div className="h-5 w-20 animate-pulse rounded-full bg-gray-200" />
              </div>
              <div className="space-y-2 text-right">
                <div className="h-5 w-24 animate-pulse rounded bg-gray-200" />
                <div className="h-4 w-16 animate-pulse rounded bg-gray-200" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
