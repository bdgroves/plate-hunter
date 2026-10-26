/* Plate Hunter service worker: lets the game open with no signal.
   The page and plate lists: network first (so new plates show up), cached copy when offline.
   Plate pictures: cache first, kept in 'ph-plates' (the page's "Save for offline" fills it). */
const SHELL = 'ph-shell-v11';
const PLATES = 'ph-plates';
const FILES = ['./', 'index.html', 'app.js', 'app.css', 'manifest.webmanifest',
  'data/states.json', 'data/collections.json', 'data/us-map.json', 'data/provinces.json', 'data/ca-map.json', 'data/mexico.json', 'data/mx-map.json',
  'data/WA.json', 'data/OR.json', 'data/ID.json', 'data/CA.json', 'data/NV.json',
  'icons/icon-192.png', 'icons/icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(k => k.startsWith('ph-shell') && k !== SHELL).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (url.origin === location.origin && url.pathname.includes('/plates/')) {
    e.respondWith(caches.open(PLATES).then(async c => {
      const hit = await c.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res.ok) c.put(req, res.clone());
      return res;
    }));
    return;
  }
  if (url.hostname.endsWith('fonts.googleapis.com') || url.hostname.endsWith('fonts.gstatic.com')) {
    e.respondWith(caches.open(SHELL).then(async c => {
      const hit = await c.match(req);
      const net = fetch(req).then(res => { c.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    }));
    return;
  }
  if (url.origin === location.origin) {
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(SHELL).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then(hit => hit || caches.match('index.html'))));
  }
});
