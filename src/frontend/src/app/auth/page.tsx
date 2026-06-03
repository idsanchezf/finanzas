'use client';

export default function AuthPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <span className="text-5xl">💰</span>
          <h1 className="mt-4 text-2xl font-bold text-gray-900">Finance Report</h1>
          <p className="mt-2 text-sm text-gray-500">
            Controla tus finanzas con inteligencia artificial
          </p>
        </div>
        <div className="space-y-3">
          <button className="btn-secondary w-full justify-center gap-2 py-2.5">
            <span>G</span> Continuar con Google
          </button>
          <button className="btn-secondary w-full justify-center gap-2 py-2.5">
            <span>M</span> Continuar con Microsoft
          </button>
        </div>
        <p className="text-center text-xs text-gray-400">
          Al continuar, aceptas nuestros terminos y politica de privacidad.
        </p>
      </div>
    </div>
  );
}
