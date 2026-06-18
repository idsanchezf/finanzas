import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TransactionEmpty } from '@/components/transactions/TransactionEmpty';

describe('TransactionEmpty', () => {
  // --- Without filters ---
  it('Should_DisplayGenericMessage_When_NoFiltersActive', () => {
    // Arrange
    // Act
    render(<TransactionEmpty hasFilters={false} />);
    // Assert
    expect(screen.getByText('No se encontraron transacciones')).toBeInTheDocument();
  });

  // --- With filters ---
  it('Should_DisplayFilterMessage_When_FiltersAreActive', () => {
    // Arrange
    // Act
    render(<TransactionEmpty hasFilters={true} />);
    // Assert
    expect(screen.getByText('Sin resultados')).toBeInTheDocument();
  });

  // --- Clear filters button ---
  it('Should_ShowClearFiltersButton_When_FiltersAreActive', () => {
    // Arrange
    // Act
    render(<TransactionEmpty hasFilters={true} onClearFilters={vi.fn()} />);
    // Assert
    expect(screen.getByText('Limpiar filtros')).toBeInTheDocument();
  });

  it('Should_NotShowClearFiltersButton_When_NoFilters', () => {
    // Arrange
    // Act
    render(<TransactionEmpty hasFilters={false} />);
    // Assert
    expect(screen.queryByText('Limpiar filtros')).not.toBeInTheDocument();
  });

  // --- onClearFilters called ---
  it('Should_CallOnClearFilters_When_ClearButtonClicked', async () => {
    // Arrange
    const onClear = vi.fn();
    const user = userEvent.setup();
    render(<TransactionEmpty hasFilters={true} onClearFilters={onClear} />);
    // Act
    await user.click(screen.getByText('Limpiar filtros'));
    // Assert
    expect(onClear).toHaveBeenCalledOnce();
  });
});
