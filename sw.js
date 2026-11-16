// Service worker (PWA, praca offline). Pliki własne: najpierw sieć, w razie braku – cache. Biblioteka z unpkg: cache.
const CACHE = 'skaner-sp-v2';
const FILES = ['./', './index.html', './products.js', './zxing.min.js', './manifest.webmanifest', 'https://unpkg.com/@zxing/library@0.21.3/umd/index.min.js'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => Promise.allSettled(FILES.map(f => c.add(f)))).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const own = e.request.url.startsWith(self.location.origin);
  if (own) {
    e.respondWith(fetch(e.request).then(res => { if (res && res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(e.request, cp)); } return res; })
      .catch(() => caches.match(e.request, {ignoreSearch: true})));
  } else {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => { if (res && (res.ok || res.type === 'opaque')) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(e.request, cp)); } return res; })));
  }
});
