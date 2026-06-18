'use client';

import Link from 'next/link';

/** Pagina offline para PWA — se muestra cuando no hay conexion a internet. */
export default function OfflinePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="text-center">
        {/* Icono */}
        <div className="mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-primary-100">
          <svg
            className="h-12 w-12 text-primary-600"
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

        <h1 className="mb-2 text-2xl font-bold text-gray-900">Sin conexion</h1>
        <p className="mb-8 max-w-sm text-gray-500">
          No tienes conexion a internet. Algunas funcionalidades no estaran
          disponibles hasta que te reconectes.
        </p>

        <div className="space-y-3">
          <button
            onClick={() => window.location.reload()}
            className="btn-primary w-full"
          >
            Reintentar
          </button>
          <Link href="/" className="btn-secondary block w-full text-center">
            Ir al inicio
          </Link>
        </div>

        <p className="mt-8 text-xs text-gray-400">
          Finance Report — Tus finanzas bajo control
        </p>
      </div>
    </div>
  );
}
