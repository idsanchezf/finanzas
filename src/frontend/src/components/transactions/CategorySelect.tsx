'use client';

import { cn } from '@/lib/utils';
import type { Category } from '@/types/transaction';

interface CategorySelectProps {
  categories: Category[];
  value: string | null;
  onChange: (categoryId: string) => void;
  disabled?: boolean;
  size?: 'sm' | 'md';
  placeholder?: string;
  className?: string;
}

/** Selector de categoria desplegable. */
export function CategorySelect({
  categories,
  value,
  onChange,
  disabled = false,
  size = 'sm',
  placeholder = 'Asignar categoria...',
  className,
}: CategorySelectProps) {
  return (
    <select
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={cn(
        'rounded-lg border border-gray-300 bg-white text-gray-700 transition-colors',
        'focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500',
        'disabled:cursor-not-allowed disabled:opacity-50',
        size === 'sm' ? 'px-2 py-1 text-xs' : 'px-3 py-1.5 text-sm',
        className
      )}
    >
      <option value="">{placeholder}</option>
      {categories.map((cat) => (
        <option key={cat.id} value={cat.id}>
          {cat.icon} {cat.name}
        </option>
      ))}
    </select>
  );
}
