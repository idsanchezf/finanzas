import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ExtractCard } from '@/components/extracts/ExtractCard';
import type { Extract, ExtractStatus } from '@/types/extract';

const mockRouter = { push: vi.fn() };
vi.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
}));

const baseExtract: Extract = {
  id: 'ext-001',
  tarjeta_id: 'card-001',
  estado: 'COMPLETED' as ExtractStatus,
  periodo_inicio: '2026-05-01',
  periodo_fin: '2026-05-31',
  fecha_corte: '2026-05-15',
  fecha_limite_pago: '2026-06-05',
  pago_minimo: 150000,
  pago_total: 2850000,
  cupo_total: 8000000,
  cupo_disponible: 5150000,
  progress_pct: 100,
  created_at: '2026-05-20T10:30:00Z',
  banco: 'Bancolombia',
  total: 2850000,
  transacciones: 67,
};

describe('ExtractCard — Render', () => {
  // ------------------------------------------------------------------
  it('Should_RenderExtractCard_When_ExtractIsComplete', () => {
    // Arrange --------------------------------------------------------

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={baseExtract} />);

    // Assert ----------------------------------------------------------
    expect(screen.getByText('Bancolombia')).toBeInTheDocument();
    expect(screen.getByText(/Mayo 2026/)).toBeInTheDocument();
    expect(screen.getByText('Completado')).toBeInTheDocument();
    expect(screen.getByText('67 transacciones')).toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_ShowGreenBadge_When_StatusIsCOMPLETED', () => {
    // Arrange --------------------------------------------------------
    const extract = { ...baseExtract, estado: 'COMPLETED' as ExtractStatus };

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    const badge = screen.getByText('Completado');
    expect(badge.className).toContain('bg-success-50');
    expect(badge.className).toContain('text-success-700');
  });

  // ------------------------------------------------------------------
  it('Should_ShowBlueBadge_When_StatusIsPARSING', () => {
    // Arrange --------------------------------------------------------
    const extract = {
      ...baseExtract,
      estado: 'PARSING' as ExtractStatus,
      progress_pct: 30,
    };

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    const badge = screen.getByText('Procesando');
    expect(badge.className).toContain('bg-primary-50');
    expect(badge.className).toContain('text-primary-700');
  });

  // ------------------------------------------------------------------
  it('Should_ShowYellowBadge_When_StatusIsPENDING', () => {
    // Arrange --------------------------------------------------------
    const extract = { ...baseExtract, estado: 'PENDING' as ExtractStatus, progress_pct: 0 };

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    const badge = screen.getByText('Pendiente');
    expect(badge.className).toContain('bg-warning-50');
    expect(badge.className).toContain('text-warning-700');
  });

  // ------------------------------------------------------------------
  it('Should_ShowRedBadge_When_StatusIsERROR', () => {
    // Arrange --------------------------------------------------------
    const extract = { ...baseExtract, estado: 'ERROR' as ExtractStatus, progress_pct: 25 };

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    const badge = screen.getByText('Error');
    expect(badge.className).toContain('bg-danger-50');
    expect(badge.className).toContain('text-danger-700');
  });

  // ------------------------------------------------------------------
  it('Should_ShowBlueBadge_When_StatusIsCLASSIFYING', () => {
    // Arrange --------------------------------------------------------
    const extract = {
      ...baseExtract,
      estado: 'CLASSIFYING' as ExtractStatus,
      progress_pct: 60,
    };

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    const badge = screen.getByText('Clasificando');
    expect(badge.className).toContain('bg-primary-50');
    expect(badge.className).toContain('text-primary-700');
  });

  // ------------------------------------------------------------------
  it('Should_ShowProgressBar_When_ExtractIsProcessing', () => {
    // Arrange --------------------------------------------------------
    const extract = {
      ...baseExtract,
      estado: 'PARSING' as ExtractStatus,
      progress_pct: 45,
    };

    // Act ------------------------------------------------------------
    const { container } = render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    const progressBar = container.querySelector('[role="progressbar"]');
    expect(progressBar).toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_HideProgressBar_When_ExtractIsComplete', () => {
    // Arrange --------------------------------------------------------
    const extract = { ...baseExtract, estado: 'COMPLETED' as ExtractStatus, progress_pct: 100 };

    // Act ------------------------------------------------------------
    const { container } = render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    const progressBar = container.querySelector('[role="progressbar"]');
    expect(progressBar).not.toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_NavigateToDetail_When_CardIsClicked', () => {
    // Arrange --------------------------------------------------------
    mockRouter.push.mockClear();

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={baseExtract} />);
    fireEvent.click(screen.getByText('Ver detalle →'));

    // Assert ----------------------------------------------------------
    expect(mockRouter.push).toHaveBeenCalledWith('/extracts/ext-001');
  });

  // ------------------------------------------------------------------
  it('Should_ShowTransaccionesCount_When_ExtractIsComplete', () => {
    // Arrange --------------------------------------------------------
    const extract = { ...baseExtract, estado: 'COMPLETED' as ExtractStatus };

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    expect(screen.getByText('67 transacciones')).toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_ShowCargando_When_TransaccionesIsZero', () => {
    // Arrange --------------------------------------------------------
    const extract = { ...baseExtract, transacciones: 0 };

    // Act ------------------------------------------------------------
    render(<ExtractCard extract={extract} />);

    // Assert ----------------------------------------------------------
    expect(screen.getByText('Cargando datos...')).toBeInTheDocument();
  });
});
