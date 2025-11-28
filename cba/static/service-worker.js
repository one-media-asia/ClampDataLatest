const CACHE_NAME = 'clamping-admin-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/style.css',
  '/static/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Network first for API routes, cache-first for static
  const req = event.request;
  if (req.url.includes('/api/') || req.method !== 'GET') {
    event.respondWith(fetch(req).catch(() => caches.match(req)));
    return;
  }
  event.respondWith(caches.match(req).then(res => res || fetch(req)));
});
