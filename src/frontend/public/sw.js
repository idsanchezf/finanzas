// ---------------------------------------------------------------------------
// Service Worker — Finance Report PWA
// ---------------------------------------------------------------------------
// Estrategia: Cache-First para assets estaticos, Network-First para API calls.
// ---------------------------------------------------------------------------

const CACHE_VERSION = 'finance-report-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const API_CACHE = `${CACHE_VERSION}-api`;

// Recursos a pre-cachear en la instalacion
const PRECACHE_URLS = [
  '/',
  '/offline',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];

// ---------------------------------------------------------------------------
// Install — Pre-cachea recursos estaticos esenciales
// ---------------------------------------------------------------------------
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => {
        return cache.addAll(PRECACHE_URLS).catch((err) => {
          // No falla la instalacion si algun recurso no esta disponible aun
          console.warn('[SW] Precache fallo para algunos recursos:', err);
        });
      })
      .then(() => self.skipWaiting())
  );
});

// ---------------------------------------------------------------------------
// Activate — Limpia caches antiguos
// ---------------------------------------------------------------------------
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) =>
        Promise.all(
          cacheNames
            .filter((name) => name.startsWith('finance-report-') && name !== CACHE_VERSION && !name.startsWith(CACHE_VERSION))
            .map((name) => caches.delete(name))
        )
      )
      .then(() => self.clients.claim())
  );
});

// ---------------------------------------------------------------------------
// Fetch — Estrategia de cache segun tipo de recurso
// ---------------------------------------------------------------------------
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // No interceptar peticiones no-GET ni a otros origenes
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;

  // API calls: Network-First con fallback a cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request, API_CACHE));
    return;
  }

  // Navegacion (paginas HTML): Network-First con fallback a offline page
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cachear la respuesta para uso offline
          const clone = response.clone();
          caches.open(DYNAMIC_CACHE).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(async () => {
          // Intentar servir de cache
          const cached = await caches.match(request);
          if (cached) return cached;
          // Fallback: pagina offline
          return caches.match('/offline');
        })
    );
    return;
  }

  // Assets estaticos: Cache-First
  event.respondWith(cacheFirst(request, STATIC_CACHE));
});

// ---------------------------------------------------------------------------
// Estrategias
// ---------------------------------------------------------------------------

/** Cache-First: sirve de cache si existe, sino va a red y cachea. */
async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    // Fallback offline
    if (request.mode === 'navigate') {
      return caches.match('/offline');
    }
    throw error;
  }
}

/** Network-First: intenta red primero, cae a cache si falla. */
async function networkFirst(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    throw error;
  }
}
