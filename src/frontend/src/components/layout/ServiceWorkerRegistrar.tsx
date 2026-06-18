'use client';

import { useEffect } from 'react';

// ---------------------------------------------------------------------------
// Service Worker Registration
// ---------------------------------------------------------------------------
// Registra el service worker para funcionalidad PWA.
// Solo se ejecuta en produccion para evitar interferencia con HMR en dev.
// ---------------------------------------------------------------------------

export function ServiceWorkerRegistrar() {
  useEffect(() => {
    if (
      typeof window !== 'undefined' &&
      'serviceWorker' in navigator &&
      process.env.NODE_ENV === 'production'
    ) {
      navigator.serviceWorker
        .register('/sw.js', { scope: '/' })
        .then((registration) => {
          console.log('[PWA] Service Worker registrado:', registration.scope);

          // Escuchar actualizaciones
          registration.addEventListener('updatefound', () => {
            const installingWorker = registration.installing;
            if (!installingWorker) return;

            installingWorker.addEventListener('statechange', () => {
              if (
                installingWorker.state === 'installed' &&
                navigator.serviceWorker.controller
              ) {
                // Nueva version disponible
                console.log('[PWA] Nueva version disponible. Refresca para actualizar.');
                // Opcional: mostrar toast de "nueva version disponible"
                if (typeof window !== 'undefined') {
                  window.dispatchEvent(new CustomEvent('sw-update-available'));
                }
              }
            });
          });
        })
        .catch((error) => {
          console.warn('[PWA] Error registrando Service Worker:', error);
        });
    }
  }, []);

  // Este componente no renderiza nada
  return null;
}
