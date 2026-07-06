'use client';

import { cn, formatCOP, formatDate, truncate, isCredit, formatInstallments } from '@/lib/utils';
import type { Transaction, Category } from '@/types/transaction';
import { ConfidenceBadge } from './ConfidenceBadge';
import { CategoryBadge } from './CategoryBadge';
import { CategorySelect } from './CategorySelect';

interface TransactionCardProps {
  transaction: Transaction;
  categories: Category[];
  selected: boolean;
  onSelect: (id: string, checked: boolean) => void;
  onCategoryChange: (id: string, categoryId: string) => void;
  onDetail: (transaction: Transaction) => void;
}

/** Card de transaccion para vista movil. */
export function TransactionCard({
  transaction,
  categories,
  selected,
  onSelect,
  onCategoryChange,
  onDetail,
}: TransactionCardProps) {
  const isAbono = isCredit(transaction.valor);
  const installments = formatInstallments(transaction.cuota_actual, transaction.cuotas_totales);

  return (
    <div
      className={cn(
        'rounded-xl border bg-white p-4 shadow-sm transition-all',
        'hover:shadow-md',
        selected && 'border-primary-300 bg-primary-50/50 ring-1 ring-primary-300',
        !transaction.categoria_id && 'border-l-4 border-l-warning-400'
      )}
    >
      <div className="flex items-start gap-3">
        {/* Checkbox */}
        <input
          type="checkbox"
          checked={selected}
          onChange={(e) => onSelect(transaction.id, e.target.checked)}
          className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Top row: date + amount */}
          <div className="flex items-start justify-between gap-2 mb-1">
            <p className="text-xs text-gray-500">
              {transaction.fecha ? formatDate(transaction.fecha) : '—'}
            </p>
            <p
              className={cn(
                'text-base font-bold whitespace-nowrap',
                isAbono ? 'text-success-600' : 'text-gray-900'
              )}
            >
              {isAbono ? '+' : ''}
              {formatCOP(Math.abs(transaction.valor))}
            </p>
          </div>

          {/* Commerce name */}
          <button
            onClick={() => onDetail(transaction)}
            className="text-left w-full mb-2"
          >
            <p className="text-sm font-medium text-gray-900 leading-tight">
              {truncate(transaction.comercio_traducido || transaction.comercio, 40)}
            </p>
            {transaction.comercio_traducido && (
              <p className="text-xs text-gray-400 truncate mt-0.5">
                {transaction.comercio}
              </p>
            )}
          </button>

          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-2 mb-2">
            {transaction.categoria ? (
              <CategoryBadge
                category={transaction.categoria}
                size="sm"
                onClick={() => onDetail(transaction)}
              />
            ) : (
              <span className="inline-flex items-center rounded-full border border-dashed border-warning-300 bg-warning-50 px-2 py-0.5 text-xs text-warning-600">
                ⚡ Sin clasificar
              </span>
            )}

            {installments && (
              <span className="inline-flex items-center rounded-full bg-warning-50 px-2 py-0.5 text-xs font-medium text-warning-700">
                {installments}
              </span>
            )}

            <ConfidenceBadge confidence={transaction.confidence} />
          </div>

          {/* Actions row */}
          <div className="flex items-center gap-2 pt-1 border-t border-gray-50">
            <CategorySelect
              categories={categories}
              value={transaction.categoria_id}
              onChange={(catId) => onCategoryChange(transaction.id, catId)}
              size="sm"
              placeholder="Clasificar..."
              className="flex-1"
            />
            <button
              onClick={() => onDetail(transaction)}
              className="rounded-lg px-2 py-1 text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
            >
              Detalle
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
