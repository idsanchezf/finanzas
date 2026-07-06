import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceBadge } from '@/components/transactions/ConfidenceBadge';

describe('ConfidenceBadge', () => {
  // --- Alta confianza ---
  it('Should_DisplayHighConfidence_When_ConfidenceIsAbove80Percent', () => {
    // Arrange
    // Act
    render(<ConfidenceBadge confidence={0.85} />);
    // Assert
    expect(screen.getByText('Alta')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  // --- Media confianza ---
  it('Should_DisplayMediumConfidence_When_ConfidenceIsBetween50And80Percent', () => {
    // Arrange
    // Act
    render(<ConfidenceBadge confidence={0.65} />);
    // Assert
    expect(screen.getByText('Media')).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();
  });

  // --- Baja confianza ---
  it('Should_DisplayLowConfidence_When_ConfidenceIsBelow50Percent', () => {
    // Arrange
    // Act
    render(<ConfidenceBadge confidence={0.3} />);
    // Assert
    expect(screen.getByText('Baja')).toBeInTheDocument();
    expect(screen.getByText('30%')).toBeInTheDocument();
  });

  // --- Sin clasificar ---
  it('Should_DisplayUnclassified_When_ConfidenceIsNull', () => {
    // Arrange
    // Act
    render(<ConfidenceBadge confidence={null} />);
    // Assert
    expect(screen.getByText('Sin clasificar')).toBeInTheDocument();
  });

  it('Should_DisplayUnclassified_When_ConfidenceIsUndefined', () => {
    // Arrange
    // Act
    render(<ConfidenceBadge confidence={undefined} />);
    // Assert
    expect(screen.getByText('Sin clasificar')).toBeInTheDocument();
  });

  // --- Boundary: exactly 80% ---
  it('Should_DisplayHighConfidence_When_ConfidenceIsExactly80Percent', () => {
    // Arrange
    // Act
    render(<ConfidenceBadge confidence={0.8} />);
    // Assert
    expect(screen.getByText('Alta')).toBeInTheDocument();
  });

  // --- Boundary: exactly 50% ---
  it('Should_DisplayMediumConfidence_When_ConfidenceIsExactly50Percent', () => {
    // Arrange
    // Act
    render(<ConfidenceBadge confidence={0.5} />);
    // Assert
    expect(screen.getByText('Media')).toBeInTheDocument();
  });
});
