'use client';

import { cn } from '@/lib/utils';
import type { Transaction, Category } from '@/types/transaction';
import { TransactionRow } from './TransactionRow';

interface TransactionTableProps {
  transactions: Transaction[];
  categories: Category[];
  selectedIds: Set<string>;
  onSelect: (id: string, checked: boolean) => void;
  onSelectAll: (checked: boolean) => void;
  onCategoryChange: (id: string, categoryId: string) => void;
  onDetail: (transaction: Transaction) => void;
  className?: string;
}

/** Tabla de transacciones (desktop). */
export function TransactionTable({
  transactions,
  categories,
  selectedIds,
  onSelect,
  onSelectAll,
  onCategoryChange,
  onDetail,
  className,
}: TransactionTableProps) {
  const allSelected = transactions.length > 0 && transactions.every((t) => selectedIds.has(t.id));
  const someSelected = transactions.some((t) => selectedIds.has(t.id));

  return (
    <div className={cn('overflow-x-auto', className)}>
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50/80">
            <th className="w-10 px-3 py-3">
              <input
                type="checkbox"
                checked={allSelected}
                ref={(el) => {
                  if (el) el.indeterminate = someSelected && !allSelected;
                }}
                onChange={(e) => onSelectAll(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
            </th>
            <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Fecha
            </th>
            <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Comercio
            </th>
            <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Categoria
            </th>
            <th className="px-3 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
              Valor
            </th>
            <th className="px-3 py-3 text-center text-xs font-semibold uppercase tracking-wider text-gray-500">
              Cuotas
            </th>
            <th className="px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
              Confianza
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {transactions.map((tx) => (
            <TransactionRow
              key={tx.id}
              transaction={tx}
              categories={categories}
              selected={selectedIds.has(tx.id)}
              onSelect={onSelect}
              onCategoryChange={onCategoryChange}
              onDetail={onDetail}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
