import type { Metadata } from 'next';

// ---------------------------------------------------------------------------
// Metadata especifico del Dashboard
// ---------------------------------------------------------------------------

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Resumen de tus finanzas: KPIs, graficos y alertas inteligentes.',
};

// ---------------------------------------------------------------------------
// Layout — hereda del RootLayout
// ---------------------------------------------------------------------------

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
