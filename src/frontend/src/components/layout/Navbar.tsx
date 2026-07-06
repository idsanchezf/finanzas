'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useAuthContext } from '@/lib/context/AuthContext';
import { Avatar } from '@/components/ui/Avatar';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Componente principal
// ---------------------------------------------------------------------------

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthContext();
  const [menuOpen, setMenuOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Cerrar menus al hacer clic fuera
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
        setNotifOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-gray-200 bg-white/95 px-4 shadow-sm backdrop-blur-sm md:hidden">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2">
        <span className="text-xl" aria-hidden="true">💰</span>
        <span className="text-lg font-bold text-primary-600">Finance Report</span>
      </Link>

      {/* Acciones derecha */}
      <div className="flex items-center gap-1" ref={menuRef}>
        {/* Notificaciones */}
        <button
          onClick={() => { setNotifOpen(!notifOpen); setMenuOpen(false); }}
          className="touch-target relative rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100"
          aria-label="Notificaciones"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
          </svg>
          {/* Badge de notificaciones */}
          <span className="absolute right-1 top-1 flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-danger-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-danger-500" />
          </span>
        </button>

        {/* Dropdown notificaciones */}
        {notifOpen && (
          <div className="absolute right-2 top-12 w-72 rounded-xl border border-gray-200 bg-white shadow-lg animate-fade-in">
            <div className="border-b border-gray-100 p-3">
              <p className="text-sm font-semibold text-gray-900">Notificaciones</p>
            </div>
            <div className="max-h-64 overflow-y-auto p-2">
              <div className="rounded-lg p-3 text-center text-sm text-gray-400">
                No tienes notificaciones nuevas
              </div>
            </div>
          </div>
        )}

        {/* Menu usuario / Login */}
        {isAuthenticated && user ? (
          <>
            <button
              onClick={() => { setMenuOpen(!menuOpen); setNotifOpen(false); }}
              className="touch-target rounded-lg p-1 transition-colors hover:bg-gray-100"
              aria-label="Menu de usuario"
            >
              <Avatar
                src={user.avatar_url}
                name={user.nombre}
                size="sm"
              />
            </button>

            {/* Dropdown menu usuario */}
            {menuOpen && (
              <div className="absolute right-2 top-12 w-56 rounded-xl border border-gray-200 bg-white shadow-lg animate-fade-in">
                <div className="border-b border-gray-100 p-3">
                  <p className="text-sm font-medium text-gray-900">{user.nombre}</p>
                  <p className="text-xs text-gray-500 truncate">{user.email}</p>
                </div>
                <div className="p-1">
                  <Link
                    href="/settings"
                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                    onClick={() => setMenuOpen(false)}
                  >
                    <span aria-hidden="true">⚙️</span>
                    Configuracion
                  </Link>
                  <button
                    onClick={() => { setMenuOpen(false); logout(); }}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-danger-500 hover:bg-danger-50"
                  >
                    <span aria-hidden="true">🚪</span>
                    Cerrar sesion
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <Link href="/auth" className="btn-primary-sm">
            Iniciar sesion
          </Link>
        )}
      </div>
    </header>
  );
}
