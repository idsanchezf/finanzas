import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UploadForm } from '@/components/extracts/UploadForm';
import { api, ApiError } from '@/lib/api';

// Mock del modulo api
vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>();
  return {
    ...actual,
    api: {
      upload: vi.fn(),
    },
  };
});

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

/** Helper: crea un archivo Excel valido. */
function createExcelFile(name = 'extracto.xlsx'): File {
  return new File(['test-data'], name, {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
}

/** Helper: simula el drop de un archivo en la dropzone. */
function dropFile(container: HTMLElement, file: File) {
  const dropzone = container.querySelector('.border-dashed')!;
  fireEvent.drop(dropzone, {
    dataTransfer: { files: [file] },
  });
}

describe('UploadForm — Render', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ------------------------------------------------------------------
  it('Should_RenderDropzone_When_Mounted', () => {
    // Arrange --------------------------------------------------------

    // Act ------------------------------------------------------------
    render(<UploadForm />);

    // Assert ----------------------------------------------------------
    expect(screen.getByText('Cargar nuevo extracto')).toBeInTheDocument();
    expect(screen.getByText(/Arrastra tu extracto/i)).toBeInTheDocument();
    expect(screen.getByText(/Formatos aceptados: .xlsx/i)).toBeInTheDocument();
    expect(screen.getByText('Seleccionar archivo')).toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_ShowFilePreview_When_FileIsDropped', () => {
    // Arrange --------------------------------------------------------
    const file = createExcelFile();

    // Act ------------------------------------------------------------
    const { container } = render(<UploadForm />);
    dropFile(container, file);

    // Assert ----------------------------------------------------------
    expect(screen.getByText('extracto.xlsx')).toBeInTheDocument();
    expect(screen.getByText('Procesar')).toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_ShowFilePreview_When_FileIsSelectedViaInput', async () => {
    // Arrange --------------------------------------------------------
    const file = createExcelFile();

    // Act ------------------------------------------------------------
    render(<UploadForm />);
    const input = screen.getByTestId('file-input');
    await userEvent.upload(input, file);

    // Assert ----------------------------------------------------------
    expect(screen.getByText('extracto.xlsx')).toBeInTheDocument();
    expect(screen.getByText('Procesar')).toBeInTheDocument();
  });
});

describe('UploadForm — Validate', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ------------------------------------------------------------------
  it('Should_ShowError_When_FileIsNotExcel', () => {
    // Arrange --------------------------------------------------------
    const badFile = new File(['test'], 'documento.pdf', {
      type: 'application/pdf',
    });

    // Act ------------------------------------------------------------
    const { container } = render(<UploadForm />);
    dropFile(container, badFile);

    // Assert ----------------------------------------------------------
    expect(screen.getByText(/Formato no soportado/)).toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_ShowError_When_FileIsEmpty', () => {
    // Arrange --------------------------------------------------------
    const emptyFile = new File([], 'vacio.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    // Act ------------------------------------------------------------
    const { container } = render(<UploadForm />);
    dropFile(container, emptyFile);

    // Assert ----------------------------------------------------------
    expect(screen.getByText(/vacio/)).toBeInTheDocument();
  });
});

describe('UploadForm — Upload Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ------------------------------------------------------------------
  it('Should_NotShowProcessButton_When_NoFileSelected', () => {
    // Arrange --------------------------------------------------------

    // Act ------------------------------------------------------------
    render(<UploadForm />);

    // Assert ----------------------------------------------------------
    expect(screen.queryByText('Procesar')).not.toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_CallApiUpload_When_ProcesarIsClicked', async () => {
    // Arrange --------------------------------------------------------
    (api.upload as ReturnType<typeof vi.fn>).mockResolvedValue({
      extract_id: 'ext-001',
      estado: 'PENDING',
      progress_pct: 0,
    });

    // Act ------------------------------------------------------------
    const { container } = render(<UploadForm />);
    dropFile(container, createExcelFile());
    await userEvent.click(screen.getByText('Procesar'));

    // Assert ----------------------------------------------------------
    await waitFor(() => {
      expect(api.upload).toHaveBeenCalledTimes(1);
    });
  });

  // ------------------------------------------------------------------
  it('Should_ShowUploadingState_When_UploadInProgress', async () => {
    // Arrange --------------------------------------------------------
    (api.upload as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({
        extract_id: 'ext-001',
        estado: 'PENDING',
        progress_pct: 0,
      }), 1000))
    );

    // Act ------------------------------------------------------------
    const { container } = render(<UploadForm />);
    dropFile(container, createExcelFile());
    await userEvent.click(screen.getByText('Procesar'));

    // Assert ----------------------------------------------------------
    expect(screen.getByText('Subiendo archivo...')).toBeInTheDocument();
  });

  // ------------------------------------------------------------------
  it('Should_ShowError_When_UploadFails', async () => {
    // Arrange --------------------------------------------------------
    (api.upload as ReturnType<typeof vi.fn>).mockRejectedValue(
      new ApiError(500, 'Error de conexion')
    );

    // Act ------------------------------------------------------------
    const { container } = render(<UploadForm />);
    dropFile(container, createExcelFile());
    await userEvent.click(screen.getByText('Procesar'));

    // Assert ----------------------------------------------------------
    await waitFor(() => {
      expect(screen.getByText(/Error de conexion/)).toBeInTheDocument();
    });
  });
});
