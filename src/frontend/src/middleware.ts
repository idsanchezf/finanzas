/**
 * Next.js Middleware — Proteccion de rutas privadas.
 *
 * Logica:
 * - Si la ruta es publica (/auth, /api, /_next, /icons, etc.) → permite
 * - Si no hay cookie `auth_token` → redirige a /auth
 * - Si hay cookie → permite (la validacion real la hace el backend)
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/** Rutas que NO requieren autenticacion. */
const PUBLIC_PATHS = [
  '/auth',
  '/_next',
  '/api',
  '/icons',
  '/manifest.json',
  '/favicon.ico',
];

/** Extensiones de archivos estaticos que siempre se permiten. */
const STATIC_EXTENSIONS = /\.(svg|png|jpg|jpeg|gif|ico|css|js|woff2?|ttf|eot)$/;

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Permitir archivos estaticos
  if (STATIC_EXTENSIONS.test(pathname)) {
    return NextResponse.next();
  }

  // Permitir rutas publicas explicitas
  const isPublic = PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`) || pathname.startsWith(`${p}?`)
  );

  // La raiz (landing) es publica en MVP
  if (isPublic || pathname === '/') {
    return NextResponse.next();
  }

  // Verificar cookie de autenticacion
  const authToken = request.cookies.get('auth_token')?.value;

  if (!authToken) {
    const loginUrl = new URL('/auth', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

/** Aplica middleware a todas las rutas excepto las estaticas internas de Next.js. */
export const config = {
  matcher: ['/((?!_next/static|_next/image|icons).*)'],
};
