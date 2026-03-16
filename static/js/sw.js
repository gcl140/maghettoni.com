const CACHE = 'maghettoni-v2';
const PRECACHE = [
  '/static/css/dashboardd-base.css',
  '/static/js/base.js',
  '/static/js/notifications.js',
  '/static/images/fav.png',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  // Only handle same-origin GET requests
  if (e.request.method !== 'GET' || !e.request.url.startsWith(self.location.origin)) return;

  const url = new URL(e.request.url);
  const accept = e.request.headers.get('accept') || '';
  const isHtml = e.request.mode === 'navigate' || accept.includes('text/html');
  const isStatic = url.pathname.startsWith('/static/');

  // Dynamic pages/API: always prefer fresh network to avoid stale UI after form submits.
  if (isHtml && !isStatic) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then(cached => {
      const network = fetch(e.request).then(res => {
        // Cache only static assets; avoid caching dynamic HTML/API responses.
        if (res.ok && isStatic) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return res;
      });
      // Return cache immediately if available, otherwise wait for network
      return cached || network;
    })
  );
});
