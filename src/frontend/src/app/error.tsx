'use client';

import { useEffect } from 'react';

// ---------------------------------------------------------------------------
// Error Boundary — Next.js App Router
// ---------------------------------------------------------------------------
// Captura errores en tiempo de renderizado en paginas.
// Para errores en el RootLayout, usar global-error.tsx.
// ---------------------------------------------------------------------------

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    // Loggear el error a un servicio de observabilidad
    console.error('[ErrorBoundary]', error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <div className="text-center">
        {/* Icono */}
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-danger-100 dark:bg-danger-900/30">
          <svg
            className="h-10 w-10 text-danger-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <h1 className="mb-2 text-2xl font-bold text-gray-900 dark:text-gray-100">
          Algo salio mal
        </h1>
        <p className="mb-2 max-w-sm text-gray-500 dark:text-gray-400">
          Ha ocurrido un error inesperado. Puedes intentar recargar la pagina.
        </p>
        {error.digest && (
          <p className="mb-6 font-mono text-xs text-gray-400">
            Error ID: {error.digest}
          </p>
        )}

        <div className="space-y-3">
          <button onClick={reset} className="btn-primary w-full">
            Intentar de nuevo
          </button>
          <button
            onClick={() => (window.location.href = '/')}
            className="btn-secondary w-full"
          >
            Ir al inicio
          </button>
        </div>

        {process.env.NODE_ENV === 'development' && (
          <details className="mt-6 max-w-lg text-left">
            <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700">
              Detalles del error (dev)
            </summary>
            <pre className="mt-2 overflow-auto rounded-lg bg-gray-100 p-3 text-xs text-gray-800 dark:bg-gray-800 dark:text-gray-300">
              {error.stack || error.message}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}
