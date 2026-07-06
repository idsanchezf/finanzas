'use client';

import Link from 'next/link';

/** Pagina 404 personalizada. */
export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="text-center">
        <p className="text-6xl font-extrabold text-primary-600">404</p>
        <h1 className="mt-4 text-2xl font-bold text-gray-900">
          Pagina no encontrada
        </h1>
        <p className="mt-2 max-w-sm text-gray-500">
          La pagina que buscas no existe o fue movida a otra direccion.
        </p>
        <Link href="/" className="btn-primary mt-8 inline-block">
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}
