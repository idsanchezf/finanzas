'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Card } from '@/components/ui/Card';
import type { Transaction, TransactionFilters as FilterState, Category } from '@/types/transaction';
import { getTransactions, updateTransactionCategory, bulkUpdateCategory } from '@/services/transactionService';
import { getCategories } from '@/services/categoryService';
import { TransactionFilters } from '@/components/transactions/TransactionFilters';
import { TransactionTable } from '@/components/transactions/TransactionTable';
import { TransactionCard } from '@/components/transactions/TransactionCard';
import { TransactionDetailModal } from '@/components/transactions/TransactionDetailModal';
import { TransactionSkeleton } from '@/components/transactions/TransactionSkeleton';
import { TransactionEmpty } from '@/components/transactions/TransactionEmpty';
import { TransactionError } from '@/components/transactions/TransactionError';
import { BulkCategoryBar } from '@/components/transactions/BulkCategoryBar';

const DEFAULT_LIMIT = 20;

export default function TransactionsPage() {
  // Data state
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [filters, setFilters] = useState<FilterState>({
    sort_by: 'fecha',
    sort_order: 'desc',
    limit: DEFAULT_LIMIT,
  });

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkApplying, setBulkApplying] = useState(false);

  // Detail modal
  const [detailTransaction, setDetailTransaction] = useState<Transaction | null>(null);

  // Pagination
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // ----- Data fetching -----

  const fetchTransactions = useCallback(
    async (f: FilterState, append = false) => {
      if (!append) {
        setLoading(true);
        setError(null);
      } else {
        setLoadingMore(true);
      }

      try {
        const response = await getTransactions(f);
        if (append) {
          setTransactions((prev) => [...prev, ...response.items]);
        } else {
          setTransactions(response.items);
        }
        setNextCursor(response.next_cursor);
        setHasMore(response.has_more);
        setError(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error al cargar transacciones';
        setError(message);
        if (!append) setTransactions([]);
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    []
  );

  const fetchCategories = useCallback(async () => {
    try {
      const cats = await getCategories();
      setCategories(cats);
    } catch {
      // Categories are non-critical; silently fail with empty array
      setCategories([]);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  // Reload on filter change
  useEffect(() => {
    fetchTransactions(filters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.search,
    filters.category_id,
    filters.periodo,
    filters.confidence_min,
    filters.confidence_max,
    filters.sort_by,
    filters.sort_order,
  ]);

  // ----- Infinite scroll -----
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading && !loadingMore) {
          fetchTransactions({ ...filters, cursor: nextCursor ?? undefined }, true);
        }
      },
      { threshold: 0.1 }
    );

    const el = loadMoreRef.current;
    if (el) observer.observe(el);

    return () => {
      if (el) observer.unobserve(el);
    };
  }, [hasMore, loading, loadingMore, nextCursor, filters, fetchTransactions]);

  // ----- Handlers -----

  const handleFiltersChange = useCallback((newFilters: FilterState) => {
    setFilters(newFilters);
    setSelectedIds(new Set()); // Clear selection on filter change
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilters({
      sort_by: 'fecha',
      sort_order: 'desc',
      limit: DEFAULT_LIMIT,
    });
    setSelectedIds(new Set());
  }, []);

  const handleSelect = useCallback((id: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(
    (checked: boolean) => {
      if (checked) {
        setSelectedIds(new Set(transactions.map((t) => t.id)));
      } else {
        setSelectedIds(new Set());
      }
    },
    [transactions]
  );

  const handleClearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  // Optimistic category update (single)
  const handleCategoryChange = useCallback(
    async (id: string, categoryId: string) => {
      const targetCategory = categories.find((c) => c.id === categoryId) || null;

      // Optimistic update
      setTransactions((prev) =>
        prev.map((tx) =>
          tx.id === id
            ? {
                ...tx,
                categoria_id: categoryId,
                categoria: targetCategory || undefined,
                confidence: targetCategory ? 1 : tx.confidence,
              }
            : tx
        )
      );

      try {
        await updateTransactionCategory(id, categoryId);
      } catch {
        // Revert optimistic update on error
        setTransactions((prev) =>
          prev.map((tx) =>
            tx.id === id
              ? {
                  ...tx,
                  categoria_id: tx.categoria_id,
                  categoria: tx.categoria,
                  confidence: tx.confidence,
                }
              : tx
          )
        );
      }
    },
    [categories]
  );

  // Bulk category update
  const handleBulkCategoryChange = useCallback(
    async (categoryId: string) => {
      if (selectedIds.size === 0) return;

      const targetCategory = categories.find((c) => c.id === categoryId) || null;
      const ids = Array.from(selectedIds);

      setBulkApplying(true);

      // Optimistic update
      setTransactions((prev) =>
        prev.map((tx) =>
          ids.includes(tx.id)
            ? {
                ...tx,
                categoria_id: categoryId,
                categoria: targetCategory || undefined,
                confidence: targetCategory ? 1 : tx.confidence,
              }
            : tx
        )
      );

      try {
        await bulkUpdateCategory({
          transaction_ids: ids,
          category_id: categoryId,
        });
        setSelectedIds(new Set());
      } catch {
        // Revert on error - refetch
        fetchTransactions(filters);
      } finally {
        setBulkApplying(false);
      }
    },
    [selectedIds, categories, fetchTransactions, filters]
  );

  const handleDetail = useCallback((transaction: Transaction) => {
    setDetailTransaction(transaction);
  }, []);

  const handleRetry = useCallback(() => {
    fetchTransactions(filters);
  }, [fetchTransactions, filters]);

  // ----- Computed -----
  const hasActiveFilters = !!(
    filters.search ||
    filters.category_id ||
    filters.periodo ||
    filters.confidence_min !== undefined
  );

  // ----- Render -----
  return (
    <div className="space-y-4 p-4 md:p-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 md:text-3xl">Transacciones</h1>
          <p className="text-sm text-gray-500">
            Gestiona y clasifica tus transacciones bancarias
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <TransactionFilters
          categories={categories}
          filters={filters}
          onFiltersChange={handleFiltersChange}
        />
      </Card>

      {/* Bulk action bar */}
      <BulkCategoryBar
        selectedCount={selectedIds.size}
        categories={categories}
        onApplyCategory={handleBulkCategoryChange}
        onClearSelection={handleClearSelection}
        loading={bulkApplying}
      />

      {/* Content */}
      <Card className="overflow-hidden p-0">
        {/* Loading state */}
        {loading && <TransactionSkeleton rows={8} className="p-4" />}

        {/* Error state */}
        {!loading && error && (
          <TransactionError message={error} onRetry={handleRetry} />
        )}

        {/* Empty state */}
        {!loading && !error && transactions.length === 0 && (
          <TransactionEmpty
            hasFilters={hasActiveFilters}
            onClearFilters={handleClearFilters}
          />
        )}

        {/* Desktop Table */}
        {!loading && !error && transactions.length > 0 && (
          <>
            <div className="hidden md:block">
              <TransactionTable
                transactions={transactions}
                categories={categories}
                selectedIds={selectedIds}
                onSelect={handleSelect}
                onSelectAll={handleSelectAll}
                onCategoryChange={handleCategoryChange}
                onDetail={handleDetail}
              />
            </div>

            {/* Mobile Cards */}
            <div className="space-y-3 p-4 md:hidden">
              {transactions.map((tx) => (
                <TransactionCard
                  key={tx.id}
                  transaction={tx}
                  categories={categories}
                  selected={selectedIds.has(tx.id)}
                  onSelect={handleSelect}
                  onCategoryChange={handleCategoryChange}
                  onDetail={handleDetail}
                />
              ))}
            </div>
          </>
        )}

        {/* Load more trigger (infinite scroll) */}
        {hasMore && !loading && (
          <div
            ref={loadMoreRef}
            className="flex items-center justify-center border-t border-gray-100 py-4"
          >
            {loadingMore ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <svg
                  className="h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
                Cargando mas...
              </div>
            ) : (
              <button
                onClick={() =>
                  fetchTransactions({ ...filters, cursor: nextCursor ?? undefined }, true)
                }
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                Cargar mas transacciones
              </button>
            )}
          </div>
        )}

        {/* Results count */}
        {!loading && !error && transactions.length > 0 && (
          <div className="border-t border-gray-100 px-4 py-2 text-xs text-gray-500">
            {transactions.length} transaccion{transactions.length !== 1 ? 'es' : ''} mostrada{transactions.length !== 1 ? 's' : ''}
          </div>
        )}
      </Card>

      {/* Detail modal */}
      {detailTransaction && (
        <TransactionDetailModal
          transaction={detailTransaction}
          onClose={() => setDetailTransaction(null)}
        />
      )}
    </div>
  );
}
