import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TransactionError } from '@/components/transactions/TransactionError';

describe('TransactionError', () => {
  // --- Default message ---
  it('Should_DisplayDefaultErrorMessage_When_NoMessageProvided', () => {
    // Arrange
    // Act
    render(<TransactionError />);
    // Assert
    expect(screen.getByText('Error al cargar las transacciones')).toBeInTheDocument();
  });

  // --- Custom message ---
  it('Should_DisplayCustomErrorMessage_When_MessageProvided', () => {
    // Arrange
    const customMsg = 'Error de conexion con el servidor';
    // Act
    render(<TransactionError message={customMsg} />);
    // Assert
    expect(screen.getByText(customMsg)).toBeInTheDocument();
  });

  // --- Retry button ---
  it('Should_ShowRetryButton_When_OnRetryProvided', () => {
    // Arrange
    // Act
    render(<TransactionError onRetry={vi.fn()} />);
    // Assert
    expect(screen.getByText('Reintentar')).toBeInTheDocument();
  });

  it('Should_NotShowRetryButton_When_OnRetryNotProvided', () => {
    // Arrange
    // Act
    render(<TransactionError />);
    // Assert
    expect(screen.queryByText('Reintentar')).not.toBeInTheDocument();
  });

  // --- Retry action ---
  it('Should_CallOnRetry_When_RetryButtonClicked', async () => {
    // Arrange
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(<TransactionError onRetry={onRetry} />);
    // Act
    await user.click(screen.getByText('Reintentar'));
    // Assert
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
