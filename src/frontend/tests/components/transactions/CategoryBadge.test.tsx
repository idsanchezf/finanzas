import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CategoryBadge } from '@/components/transactions/CategoryBadge';
import type { Category } from '@/types/transaction';

const mockCategory: Category = {
  id: 'cat-1',
  name: 'Alimentacion',
  icon: '🍔',
  color: '#FF6B6B',
  is_default: true,
};

describe('CategoryBadge', () => {
  // --- Con categoria ---
  it('Should_DisplayCategoryNameAndIcon_When_CategoryIsProvided', () => {
    // Arrange
    // Act
    render(<CategoryBadge category={mockCategory} />);
    // Assert
    expect(screen.getByText('Alimentacion')).toBeInTheDocument();
    expect(screen.getByText('🍔')).toBeInTheDocument();
  });

  // --- Sin categoria ---
  it('Should_DisplaySinCategoria_When_CategoryIsNull', () => {
    // Arrange
    // Act
    render(<CategoryBadge category={null} />);
    // Assert
    expect(screen.getByText('Sin categoria')).toBeInTheDocument();
  });

  it('Should_DisplaySinCategoria_When_CategoryIsUndefined', () => {
    // Arrange
    // Act
    render(<CategoryBadge category={undefined} />);
    // Assert
    expect(screen.getByText('Sin categoria')).toBeInTheDocument();
  });

  // --- Size variants ---
  it('Should_RenderWithSmallSize_When_SizeIsSm', () => {
    // Arrange
    // Act
    const { container } = render(<CategoryBadge category={mockCategory} size="sm" />);
    // Assert
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('text-xs');
  });

  it('Should_RenderWithMediumSize_When_SizeIsMd', () => {
    // Arrange
    // Act
    const { container } = render(<CategoryBadge category={mockCategory} size="md" />);
    // Assert
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain('text-sm');
  });
});
