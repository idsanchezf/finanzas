'use client';

import { usePathname } from 'next/navigation';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { MobileNav } from './MobileNav';
import { ServiceWorkerRegistrar } from './ServiceWorkerRegistrar';

// ---------------------------------------------------------------------------
// Routes donde NO se muestra el layout de navegacion (auth, landing)
// ---------------------------------------------------------------------------

const BLANK_ROUTES = ['/auth', '/login', '/offline'];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // No mostrar navegacion en paginas de auth, offline, etc.
  if (BLANK_ROUTES.includes(pathname) || pathname.startsWith('/auth')) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Service Worker registration */}
      <ServiceWorkerRegistrar />

      {/* Navbar — visible solo en mobile */}
      <Navbar />

      {/* Contenido principal */}
      <div className="flex flex-1">
        {/* Sidebar — visible solo en desktop */}
        <Sidebar />

        {/* Main content — padding inferior para mobile nav */}
        <main className="flex-1 pb-20 md:pb-6 md:pl-64">
          {/* Background decorativo desktop */}
          <div className="mx-auto w-full max-w-[var(--content-max-width)] px-4 py-4 md:px-6 md:py-6">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile navigation — visible solo en mobile */}
      <MobileNav />
    </div>
  );
}
