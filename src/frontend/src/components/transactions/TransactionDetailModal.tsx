'use client';

import { useEffect } from 'react';
import { cn, formatCOP, formatDate, truncate, formatInstallments, isCredit } from '@/lib/utils';
import type { Transaction } from '@/types/transaction';
import { ConfidenceBadge } from './ConfidenceBadge';
import { CategoryBadge } from './CategoryBadge';

interface TransactionDetailModalProps {
  transaction: Transaction | null;
  onClose: () => void;
}

/** Modal de detalle completo de una transaccion. */
export function TransactionDetailModal({ transaction, onClose }: TransactionDetailModalProps) {
  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!transaction) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-2xl bg-white shadow-xl animate-slide-up">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-gray-100 bg-white px-6 py-4 rounded-t-2xl">
          <h2 className="text-lg font-semibold text-gray-900">Detalle de transaccion</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="space-y-5 px-6 py-5">
          {/* Comercio */}
          <div>
            <label className="text-xs font-medium uppercase tracking-wider text-gray-500">
              Comercio
            </label>
            <p className="mt-1 text-base font-medium text-gray-900">
              {transaction.comercio_traducido || transaction.comercio}
            </p>
            {transaction.comercio_traducido && (
              <p className="text-sm text-gray-500">Original: {transaction.comercio}</p>
            )}
          </div>

          {/* Monto */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Valor
              </label>
              <p
                className={cn(
                  'mt-1 text-xl font-bold',
                  isCredit(transaction.valor) ? 'text-success-600' : 'text-gray-900'
                )}
              >
                {isCredit(transaction.valor) && '+'}
                {formatCOP(Math.abs(transaction.valor))}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Categoria
              </label>
              <div className="mt-1">
                <CategoryBadge category={transaction.categoria} size="md" />
              </div>
            </div>
          </div>

          {/* Fecha y autorizacion */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Fecha
              </label>
              <p className="mt-1 text-sm text-gray-900">
                {transaction.fecha ? formatDate(transaction.fecha) : '—'}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Autorizacion
              </label>
              <p className="mt-1 text-sm font-mono text-gray-900">
                {transaction.autorizacion || '—'}
              </p>
            </div>
          </div>

          {/* Confianza */}
          <div>
            <label className="text-xs font-medium uppercase tracking-wider text-gray-500">
              Confianza de clasificacion
            </label>
            <div className="mt-1">
              <ConfidenceBadge confidence={transaction.confidence} />
            </div>
          </div>

          {/* Cuotas */}
          {transaction.es_cuota && (
            <div className="rounded-xl border border-warning-200 bg-warning-50 p-4">
              <h4 className="mb-3 text-sm font-semibold text-warning-800">
                📅 Informacion de cuotas
              </h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-warning-600">Progreso:</span>
                  <span className="ml-2 font-medium text-warning-900">
                    {formatInstallments(transaction.cuota_actual, transaction.cuotas_totales)}
                  </span>
                </div>
                {transaction.cuota_valor != null && (
                  <div>
                    <span className="text-warning-600">Valor cuota:</span>
                    <span className="ml-2 font-medium text-warning-900">
                      {formatCOP(transaction.cuota_valor)}
                    </span>
                  </div>
                )}
                {transaction.interes_mensual != null && (
                  <div>
                    <span className="text-warning-600">Interes mensual:</span>
                    <span className="ml-2 font-medium text-warning-900">
                      {formatCOP(transaction.interes_mensual)}
                    </span>
                  </div>
                )}
                {transaction.interes_anual != null && (
                  <div>
                    <span className="text-warning-600">Interes anual:</span>
                    <span className="ml-2 font-medium text-warning-900">
                      {(transaction.interes_anual * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
                {transaction.saldo_pendiente != null && (
                  <div>
                    <span className="text-warning-600">Saldo pendiente:</span>
                    <span className="ml-2 font-medium text-warning-900">
                      {formatCOP(transaction.saldo_pendiente)}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Moneda original */}
          {transaction.moneda_original && transaction.moneda_original !== 'COP' && (
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
              <h4 className="mb-2 text-sm font-semibold text-gray-700">
                💱 Moneda original
              </h4>
              <p className="text-sm text-gray-700">
                {transaction.moneda_original}{' '}
                {transaction.valor_moneda_original != null
                  ? new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: transaction.moneda_original,
                    }).format(transaction.valor_moneda_original)
                  : '—'}
              </p>
            </div>
          )}

          {/* Historial de cambios de categoria */}
          {transaction.category_history && transaction.category_history.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-700">
                Historial de categoria
              </h4>
              <div className="space-y-2">
                {transaction.category_history.map((entry) => (
                  <div
                    key={entry.id}
                    className="rounded-lg border border-gray-100 bg-gray-50 px-3 py-2 text-xs text-gray-600"
                  >
                    <span className="font-medium">
                      Cambio: {formatDate(entry.changed_at)}
                    </span>
                    {/* IDs de categoria se mostrarian aqui si tuvieramos el nombre */}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-100 px-6 py-4">
          <button onClick={onClose} className="btn-secondary w-full text-sm">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}
