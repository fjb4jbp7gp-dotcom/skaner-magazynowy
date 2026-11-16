// Service worker (PWA, praca offline). Pliki własne: zawsze sieć z kontrolą świeżości, w razie braku sieci – cache.
const CACHE = 'skaner-sp-v4';
const FILES = ['./', './index.html', './products.js', './zxing-wasm-reader.js', './zxing_reader.wasm', './manifest.webmanifest'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => Promise.allSettled(FILES.map(f => fetch(f, {cache: 'no-cache'}).then(r => r.ok && c.put(f, r))))).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || !e.request.url.startsWith(self.location.origin)) return;
  e.respondWith(fetch(e.request.url, {cache: 'no-cache'}).then(res => { if (res && res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(e.request, cp)); } return res; })
    .catch(() => caches.match(e.request, {ignoreSearch: true})));
});
