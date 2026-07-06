'use client';

import { cn } from '@/lib/utils';
import type { Category } from '@/types/transaction';

interface CategoryBadgeProps {
  category: Category | null | undefined;
  size?: 'sm' | 'md';
  onClick?: () => void;
  className?: string;
}

/** Badge de categoria con color e icono. */
export function CategoryBadge({ category, size = 'sm', onClick, className }: CategoryBadgeProps) {
  if (!category) {
    return (
      <span
        className={cn(
          'inline-flex items-center rounded-full border border-dashed border-gray-300 bg-gray-50 text-gray-400',
          size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
          onClick && 'cursor-pointer hover:border-gray-400 hover:text-gray-500',
          className
        )}
        onClick={onClick}
      >
        Sin categoria
      </span>
    );
  }

  const bgColor = category.color || '#6B7280';
  const isDark = isColorDark(bgColor);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium transition-colors',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        onClick && 'cursor-pointer hover:opacity-80',
        className
      )}
      style={{
        backgroundColor: bgColor + '20',
        color: bgColor,
        border: `1px solid ${bgColor}40`,
      }}
      onClick={onClick}
    >
      <span className="text-sm leading-none">{category.icon || '📌'}</span>
      <span>{category.name}</span>
    </span>
  );
}

/** Detecta si un color hex es oscuro para ajustar el texto. */
function isColorDark(hex: string): boolean {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  // Relative luminance approximation
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance < 0.5;
}
