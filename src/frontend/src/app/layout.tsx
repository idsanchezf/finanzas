import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/context/AuthContext';
import { AppLayout } from '@/components/layout/AppLayout';
import { ToastProvider } from '@/components/ui/Toast';

// ---------------------------------------------------------------------------
// Fonts
// ---------------------------------------------------------------------------

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
  fallback: ['system-ui', '-apple-system', 'sans-serif'],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
  fallback: ['ui-monospace', 'monospace'],
});

// ---------------------------------------------------------------------------
// Metadata (SEO)
// ---------------------------------------------------------------------------

export const metadata: Metadata = {
  title: {
    default: 'Finance Report — Controla tus finanzas',
    template: '%s | Finance Report',
  },
  description:
    'Clasifica tus gastos, analiza tus habitos financieros y recibe recomendaciones personalizadas con inteligencia artificial. Conecta tus extractos bancarios y toma el control de tu dinero.',
  keywords: [
    'finanzas personales',
    'control de gastos',
    'extractos bancarios',
    'presupuesto',
    'ahorro',
    'clasificacion de gastos',
    'Colombia',
    'COP',
    'tarjeta de credito',
  ],
  authors: [{ name: 'Finance Report' }],
  creator: 'Finance Report',
  publisher: 'Finance Report',
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'https://financereport.app'),
  openGraph: {
    type: 'website',
    locale: 'es_CO',
    siteName: 'Finance Report',
    title: 'Finance Report — Controla tus finanzas',
    description:
      'Clasifica tus gastos, analiza tus habitos financieros y recibe recomendaciones con IA.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Finance Report — Controla tus finanzas',
    description: 'Clasifica tus gastos y analiza tus finanzas con IA.',
  },
  robots: {
    index: true,
    follow: true,
  },
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    title: 'Finance Report',
    statusBarStyle: 'black-translucent',
  },
  icons: {
    icon: [
      { url: '/icons/icon-48x48.png', sizes: '48x48', type: 'image/png' },
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
    shortcut: '/icons/icon-192x192.png',
    apple: [
      { url: '/icons/icon-192x192.png', sizes: '192x192' },
    ],
    other: [
      {
        rel: 'mask-icon',
        url: '/icons/icon-512x512.png',
      },
    ],
  },
};

// ---------------------------------------------------------------------------
// Viewport
// ---------------------------------------------------------------------------

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#3B82F6' },
    { media: '(prefers-color-scheme: dark)', color: '#1E3A8A' },
  ],
};

// ---------------------------------------------------------------------------
// RootLayout
// ---------------------------------------------------------------------------

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-CO" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <head>
        {/* Apple PWA meta tags */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Finance Report" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        <link rel="apple-touch-icon" sizes="512x512" href="/icons/icon-512x512.png" />

        {/* Microsoft Tiles */}
        <meta name="msapplication-TileColor" content="#3B82F6" />
        <meta name="msapplication-TileImage" content="/icons/icon-144x144.png" />

        {/* Theme color (fallback para navegadores que no soportan viewport export) */}
        <meta name="theme-color" content="#3B82F6" />

        {/* Prevenir zoom en inputs en iOS */}
        <meta name="format-detection" content="telephone=no" />
      </head>
      <body className="min-h-screen bg-[var(--color-bg-primary)] font-sans antialiased">
        <AuthProvider>
          <ToastProvider>
            <AppLayout>{children}</AppLayout>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
