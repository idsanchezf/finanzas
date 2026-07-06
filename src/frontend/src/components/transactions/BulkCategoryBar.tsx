'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import type { Category } from '@/types/transaction';
import { CategorySelect } from './CategorySelect';

interface BulkCategoryBarProps {
  selectedCount: number;
  categories: Category[];
  onApplyCategory: (categoryId: string) => void;
  onClearSelection: () => void;
  loading?: boolean;
  className?: string;
}

/** Barra de accion masiva: clasificar multiples transacciones seleccionadas. */
export function BulkCategoryBar({
  selectedCount,
  categories,
  onApplyCategory,
  onClearSelection,
  loading = false,
  className,
}: BulkCategoryBarProps) {
  const [categoryId, setCategoryId] = useState('');

  const handleApply = () => {
    if (categoryId) {
      onApplyCategory(categoryId);
      setCategoryId('');
    }
  };

  if (selectedCount === 0) return null;

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-3 rounded-lg bg-primary-50 p-3 shadow-sm animate-slide-up',
        'border border-primary-200',
        className
      )}
    >
      <span className="text-sm font-medium text-primary-800">
        {selectedCount} {selectedCount === 1 ? 'transaccion seleccionada' : 'transacciones seleccionadas'}
      </span>

      <div className="flex items-center gap-2">
        <CategorySelect
          categories={categories}
          value={categoryId}
          onChange={setCategoryId}
          placeholder="Categoria..."
          size="sm"
        />
        <button
          onClick={handleApply}
          disabled={!categoryId || loading}
          className="btn-primary text-xs"
        >
          {loading ? 'Aplicando...' : 'Aplicar'}
        </button>
      </div>

      <button
        onClick={onClearSelection}
        disabled={loading}
        className="text-xs text-gray-500 hover:text-gray-700 disabled:opacity-50"
      >
        Deseleccionar todo
      </button>
    </div>
  );
}
