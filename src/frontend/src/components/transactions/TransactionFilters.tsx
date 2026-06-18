'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { cn, debounce } from '@/lib/utils';
import type { Category } from '@/types/transaction';
import type { TransactionFilters as FilterState } from '@/types/transaction';

interface TransactionFiltersProps {
  categories: Category[];
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  className?: string;
}

const CONFIDENCE_OPTIONS: { value: string; label: string; min?: number; max?: number }[] = [
  { value: '', label: 'Todas' },
  { value: 'alta', label: 'Alta', min: 0.8, max: 1 },
  { value: 'media', label: 'Media', min: 0.5, max: 0.8 },
  { value: 'baja', label: 'Baja', min: 0, max: 0.5 },
  { value: 'sin_clasificar', label: 'Sin clasificar', min: undefined, max: undefined },
];

/** Barra de filtros para transacciones. */
export function TransactionFilters({
  categories,
  filters,
  onFiltersChange,
  className,
}: TransactionFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search || '');

  // Ref to always hold latest filters for the debounced callback
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  // Debounced search handler
  const debouncedSearch = useRef(
    debounce((value: unknown) => {
      const searchTerm = String(value ?? '');
      onFiltersChange({ ...filtersRef.current, search: searchTerm || undefined, cursor: undefined });
    }, 300)
  ).current;

  // Sync external filter changes to local search input
  useEffect(() => {
    setSearchInput(filters.search || '');
  }, [filters.search]);

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setSearchInput(value);
      debouncedSearch(value);
    },
    [debouncedSearch]
  );

  const handleFilterChange = useCallback(
    (key: keyof FilterState, value: string | undefined) => {
      onFiltersChange({ ...filters, [key]: value || undefined, cursor: undefined });
    },
    [filters, onFiltersChange]
  );

  const handleConfidenceChange = useCallback(
    (value: string) => {
      const option = CONFIDENCE_OPTIONS.find((o) => o.value === value);
      if (option && value === 'sin_clasificar') {
        onFiltersChange({
          ...filters,
          confidence_min: undefined,
          confidence_max: undefined,
          // Sin clasificar: confidence is null, which can't be expressed as min/max
          // We'll send a special param or handle server-side
          cursor: undefined,
        });
      } else if (option) {
        onFiltersChange({
          ...filters,
          confidence_min: option.min,
          confidence_max: option.max,
          cursor: undefined,
        });
      } else {
        onFiltersChange({
          ...filters,
          confidence_min: undefined,
          confidence_max: undefined,
          cursor: undefined,
        });
      }
    },
    [filters, onFiltersChange]
  );

  const handleSortChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      const [sort_by, sort_order] = e.target.value.split('-') as [
        FilterState['sort_by'],
        FilterState['sort_order']
      ];
      onFiltersChange({ ...filters, sort_by, sort_order, cursor: undefined });
    },
    [filters, onFiltersChange]
  );

  const toggleSortOrder = useCallback(() => {
    const newOrder = filters.sort_order === 'asc' ? 'desc' : 'asc';
    onFiltersChange({ ...filters, sort_order: newOrder, cursor: undefined });
  }, [filters, onFiltersChange]);

  const currentSortValue = filters.sort_by
    ? `${filters.sort_by}-${filters.sort_order || 'desc'}`
    : 'fecha-desc';

  const currentConfidenceValue = (() => {
    if (filters.confidence_min === undefined && filters.confidence_max === undefined) return '';
    if (filters.confidence_min === 0.8) return 'alta';
    if (filters.confidence_min === 0.5) return 'media';
    if (filters.confidence_max === 0.5) return 'baja';
    return '';
  })();

  return (
    <div className={cn('space-y-3', className)}>
      {/* Search bar */}
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          type="text"
          value={searchInput}
          onChange={handleSearchChange}
          placeholder="Buscar por nombre de comercio..."
          className="input-field pl-10"
        />
        {searchInput && (
          <button
            onClick={() => {
              setSearchInput('');
              onFiltersChange({ ...filters, search: undefined, cursor: undefined });
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        )}
      </div>

      {/* Filter pills / selects */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Category filter */}
        <select
          value={filters.category_id || ''}
          onChange={(e) => handleFilterChange('category_id', e.target.value || undefined)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        >
          <option value="">Todas las categorias</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.icon} {cat.name}
            </option>
          ))}
        </select>

        {/* Period filter */}
        <input
          type="month"
          value={filters.periodo || ''}
          onChange={(e) => handleFilterChange('periodo', e.target.value || undefined)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          placeholder="Periodo"
        />

        {/* Confidence filter */}
        <select
          value={currentConfidenceValue}
          onChange={(e) => handleConfidenceChange(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        >
          <option value="">Confianza: Todas</option>
          <option value="alta">Confianza: Alta &gt;80%</option>
          <option value="media">Confianza: Media 50-80%</option>
          <option value="baja">Confianza: Baja &lt;50%</option>
          <option value="sin_clasificar">Sin clasificar</option>
        </select>

        {/* Sort */}
        <select
          value={currentSortValue}
          onChange={handleSortChange}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs text-gray-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        >
          <option value="fecha-desc">Fecha ↓</option>
          <option value="fecha-asc">Fecha ↑</option>
          <option value="valor-desc">Valor ↓</option>
          <option value="valor-asc">Valor ↑</option>
          <option value="comercio-asc">Comercio A-Z</option>
          <option value="comercio-desc">Comercio Z-A</option>
        </select>

        {/* Active filters count */}
        {(filters.category_id || filters.search || filters.periodo) && (
          <button
            onClick={() =>
              onFiltersChange({
                sort_by: filters.sort_by,
                sort_order: filters.sort_order,
              })
            }
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-danger-600 hover:bg-danger-50 transition-colors"
          >
            Limpiar filtros
          </button>
        )}
      </div>
    </div>
  );
}
