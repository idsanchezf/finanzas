'use client';

import { cn, formatCOP, formatDate, truncate, isCredit, formatInstallments } from '@/lib/utils';
import type { Transaction, Category } from '@/types/transaction';
import { ConfidenceBadge } from './ConfidenceBadge';
import { CategoryBadge } from './CategoryBadge';
import { CategorySelect } from './CategorySelect';

interface TransactionRowProps {
  transaction: Transaction;
  categories: Category[];
  selected: boolean;
  onSelect: (id: string, checked: boolean) => void;
  onCategoryChange: (id: string, categoryId: string) => void;
  onDetail: (transaction: Transaction) => void;
}

/** Fila de la tabla de transacciones (desktop). */
export function TransactionRow({
  transaction,
  categories,
  selected,
  onSelect,
  onCategoryChange,
  onDetail,
}: TransactionRowProps) {
  const isAbono = isCredit(transaction.valor);
  const installments = formatInstallments(transaction.cuota_actual, transaction.cuotas_totales);

  return (
    <tr
      className={cn(
        'group border-b border-gray-50 transition-colors',
        'hover:bg-primary-50/30',
        selected && 'bg-primary-50/50',
        !transaction.categoria_id && 'bg-yellow-50/20'
      )}
    >
      {/* Checkbox */}
      <td className="w-10 px-3 py-3">
        <input
          type="checkbox"
          checked={selected}
          onChange={(e) => onSelect(transaction.id, e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
        />
      </td>

      {/* Fecha */}
      <td className="whitespace-nowrap px-3 py-3 text-sm text-gray-600">
        {transaction.fecha ? formatDate(transaction.fecha) : '—'}
      </td>

      {/* Comercio */}
      <td className="px-3 py-3">
        <button
          onClick={() => onDetail(transaction)}
          className="text-left hover:text-primary-600 transition-colors"
        >
          <p className="text-sm font-medium text-gray-900 group-hover:text-primary-700">
            {truncate(transaction.comercio_traducido || transaction.comercio, 35)}
          </p>
          {transaction.comercio_traducido && (
            <p className="text-xs text-gray-400 truncate max-w-[200px]">
              {transaction.comercio}
            </p>
          )}
        </button>
      </td>

      {/* Categoria */}
      <td className="px-3 py-3">
        <div className="flex items-center gap-2">
          {transaction.categoria ? (
            <CategoryBadge
              category={transaction.categoria}
              size="sm"
              onClick={() => onDetail(transaction)}
            />
          ) : (
            <button
              onClick={() => onDetail(transaction)}
              className="inline-flex items-center rounded-full border border-dashed border-warning-300 bg-warning-50 px-2 py-0.5 text-xs text-warning-600 hover:bg-warning-100"
            >
              ⚡ Sin clasificar
            </button>
          )}
          <div className="opacity-0 group-hover:opacity-100 transition-opacity">
            <CategorySelect
              categories={categories}
              value={transaction.categoria_id}
              onChange={(catId) => onCategoryChange(transaction.id, catId)}
              size="sm"
              placeholder="+"
            />
          </div>
        </div>
      </td>

      {/* Valor */}
      <td
        className={cn(
          'whitespace-nowrap px-3 py-3 text-right text-sm font-medium',
          isAbono ? 'text-success-600' : 'text-gray-900'
        )}
      >
        {isAbono ? '+' : ''}
        {formatCOP(Math.abs(transaction.valor))}
      </td>

      {/* Cuotas */}
      <td className="whitespace-nowrap px-3 py-3 text-center text-sm">
        {installments ? (
          <span className="inline-flex items-center rounded-full bg-warning-50 px-2 py-0.5 text-xs font-medium text-warning-700">
            {installments}
          </span>
        ) : (
          <span className="text-gray-300">—</span>
        )}
      </td>

      {/* Confianza */}
      <td className="whitespace-nowrap px-3 py-3">
        <ConfidenceBadge confidence={transaction.confidence} />
      </td>
    </tr>
  );
}
