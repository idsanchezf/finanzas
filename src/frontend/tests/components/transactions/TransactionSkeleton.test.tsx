import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TransactionSkeleton } from '@/components/transactions/TransactionSkeleton';

describe('TransactionSkeleton', () => {
  // --- Renders default rows ---
  it('Should_RenderDefaultNumberOfRows_When_NoRowsPropProvided', () => {
    // Arrange
    // Act
    const { container } = render(<TransactionSkeleton />);
    // Assert
    const rows = container.querySelectorAll('tbody tr');
    expect(rows).toHaveLength(5);
  });

  // --- Renders custom rows ---
  it('Should_RenderCustomNumberOfRows_When_RowsPropIsProvided', () => {
    // Arrange
    // Act
    const { container } = render(<TransactionSkeleton rows={3} />);
    // Assert
    const rows = container.querySelectorAll('tbody tr');
    expect(rows).toHaveLength(3);
  });

  // --- Has table structure ---
  it('Should_RenderTableStructure_When_Rendered', () => {
    // Arrange
    // Act
    const { container } = render(<TransactionSkeleton rows={1} />);
    // Assert
    expect(container.querySelector('table')).toBeInTheDocument();
    expect(container.querySelector('thead')).toBeInTheDocument();
    expect(container.querySelector('tbody')).toBeInTheDocument();
  });

  // --- Mobile cards visible ---
  it('Should_RenderMobileSkeletonCards_When_Rendered', () => {
    // Arrange
    // Act
    const { container } = render(<TransactionSkeleton rows={2} />);
    // Assert
    // Mobile cards should exist (md:hidden)
    const mobileCards = container.querySelectorAll('.md\\:hidden > div');
    expect(mobileCards.length).toBeGreaterThan(0);
  });
});
