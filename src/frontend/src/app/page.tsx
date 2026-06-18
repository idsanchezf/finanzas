import { redirect } from 'next/navigation';

/**
 * Pagina raiz: redirige automaticamente al dashboard.
 * En el futuro podria mostrar landing page para usuarios no autenticados.
 */
export default function HomePage() {
  redirect('/dashboard');
}
