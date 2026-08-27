const VERSION = 'ov-pwa-20260827-v121-tooltip-ui6';
const STATIC_CACHE = `${VERSION}-static`;
const RUNTIME_CACHE = `${VERSION}-runtime`;

const rootUrl = () => new URL('./', self.registration.scope).href;
const scoped = path => new URL(path, self.registration.scope).href;

const PRECACHE = [
  '',
  'offline.html',
  'site.webmanifest',
  'favicon.svg',
  'pwa/icon-192.png',
  'pwa/icon-512.png',
  'pwa/icon-maskable-512.png',
  'assets/brand-mark.svg',
  'assets/pwa.css',
  'assets/pwa.js'
].map(scoped);

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(STATIC_CACHE);
    await Promise.allSettled(PRECACHE.map(async url => {
      const response = await fetch(new Request(url, { cache: 'reload' }));
      if (response.ok) await cache.put(url, response.clone());
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter(key => key.startsWith('ov-pwa-') && ![STATIC_CACHE, RUNTIME_CACHE].includes(key))
        .map(key => caches.delete(key))
    );
    await self.clients.claim();
  })());
});

async function networkFirst(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) await cache.put(request, response.clone());
    return response;
  } catch (error) {
    const cached = await cache.match(request, { ignoreSearch: true });
    if (cached) return cached;
    throw error;
  }
}

async function navigationResponse(request) {
  try {
    return await networkFirst(request);
  } catch (_error) {
    const staticCache = await caches.open(STATIC_CACHE);
    const runtimeCache = await caches.open(RUNTIME_CACHE);
    return (
      await runtimeCache.match(request, { ignoreSearch: true }) ||
      await runtimeCache.match(rootUrl(), { ignoreSearch: true }) ||
      await staticCache.match(rootUrl(), { ignoreSearch: true }) ||
      await staticCache.match(scoped('offline.html'), { ignoreSearch: true }) ||
      Response.error()
    );
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  const cached = await cache.match(request, { ignoreSearch: false });
  const fresh = fetch(request).then(async response => {
    if (response.ok) await cache.put(request, response.clone());
    return response;
  }).catch(() => null);
  return cached || await fresh || Response.error();
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(navigationResponse(request));
    return;
  }

  if (url.pathname.endsWith('/data/site-data.json')) {
    event.respondWith(networkFirst(request).catch(() => caches.match(request, { ignoreSearch: true })));
    return;
  }

  // I moduli app-parts sono codice JavaScript anche se hanno estensione .txt:
  // devono aggiornarsi insieme all'HTML e agli altri asset applicativi.
  if (
    /\.(?:js|css)$/.test(url.pathname) ||
    url.pathname.endsWith('/site.webmanifest') ||
    /\/assets\/app-parts\/\d{2}\.txt$/.test(url.pathname)
  ) {
    event.respondWith(networkFirst(request).catch(() => caches.match(request, { ignoreSearch: true })));
    return;
  }

  event.respondWith(staleWhileRevalidate(request));
});
