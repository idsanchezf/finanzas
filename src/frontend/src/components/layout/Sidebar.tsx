'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthContext } from '@/lib/context/AuthContext';
import { Avatar } from '@/components/ui/Avatar';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Navegacion principal
// ---------------------------------------------------------------------------

const NAV_ITEMS = [
  {
    href: '/dashboard',
    label: 'Dashboard',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1h-2z" />
      </svg>
    ),
  },
  {
    href: '/extracts',
    label: 'Extractos',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    href: '/transactions',
    label: 'Transacciones',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      </svg>
    ),
  },
  {
    href: '/budgets',
    label: 'Presupuestos',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    href: '/insights',
    label: 'Insights',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    href: '/chat',
    label: 'Chat IA',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
  },
  {
    href: '/settings',
    label: 'Configuracion',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
];

// Opcion "Metas de ahorro" (proximamente, deshabilitada en MVP)
const COMING_SOON_ITEMS = [
  {
    href: '#',
    label: 'Metas',
    icon: (
      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    disabled: true,
  },
];

// ---------------------------------------------------------------------------
// Componente
// ---------------------------------------------------------------------------

export function Sidebar() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuthContext();

  return (
    <aside className="hidden md:fixed md:inset-y-0 md:left-0 md:z-20 md:flex md:w-64 md:flex-col">
      <div className="flex flex-1 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        {/* Header del sidebar */}
        <div className="flex h-14 items-center gap-2 border-b border-gray-200 px-6 dark:border-gray-800">
          <span className="text-xl" aria-hidden="true">💰</span>
          <Link href="/" className="text-lg font-bold text-primary-600">
            Finance Report
          </Link>
        </div>

        {/* Navegacion */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150',
                  isActive
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800/50 dark:hover:text-gray-200'
                )}
              >
                <span className={cn(
                  'h-5 w-5',
                  isActive ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400'
                )}>
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}

          {/* Separador */}
          <div className="py-2">
            <div className="border-t border-gray-200 dark:border-gray-800" />
          </div>

          {/* Items "proximamente" */}
          {COMING_SOON_ITEMS.map((item) => (
            <span
              key={item.label}
              className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-300 dark:text-gray-600"
            >
              <span className="h-5 w-5 text-gray-300 dark:text-gray-600">{item.icon}</span>
              {item.label}
              <span className="ml-auto rounded-full bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-400 dark:bg-gray-800 dark:text-gray-500">
                Prox.
              </span>
            </span>
          ))}
        </nav>

        {/* Footer del sidebar — perfil de usuario */}
        <div className="border-t border-gray-200 p-4 dark:border-gray-800">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <Avatar src={user.avatar_url} name={user.nombre} size="md" />
              <div className="flex-1 truncate">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {user.nombre}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  {user.email}
                </p>
              </div>
              <button
                onClick={logout}
                className="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-danger-500 dark:hover:bg-gray-800"
                aria-label="Cerrar sesion"
                title="Cerrar sesion"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          ) : (
            <Link href="/auth" className="btn-primary w-full text-sm">
              Iniciar sesion
            </Link>
          )}
        </div>
      </div>
    </aside>
  );
}
