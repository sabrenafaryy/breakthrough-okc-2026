/* Offline cache for the Playbook.
   The whole point: someone opens this at 9am while the network is quiet, and it keeps working all
   day even when 150 people are sharing the ballroom wifi. Everything needed to fill the workbook
   AND to build the final PDF is cached on first load. */
var VERSION = 'playbook-2026-09-23a';
var CORE = [
  './',
  './index.html',
  './fill.js',
  './pdf-lib.min.js',
  './playbook-template.pdf',
  '../assets/katie.webp',
  '../assets/cameron.webp',
  '../assets/ben.webp',
  '../assets/favicon-32.png',
  '../assets/boldonse.woff2'
];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(VERSION).then(function (c) {
      // one bad URL shouldn't fail the whole install
      return Promise.all(CORE.map(function (u) {
        return c.add(new Request(u, { cache: 'reload' })).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) { return k === VERSION ? null : caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;

  // Fonts and anything else cross-origin: use the cached copy if we have one, otherwise fetch
  // and keep it. Failing to reach Google Fonts must never stop the page rendering.
  e.respondWith(
    caches.match(req, { ignoreSearch: false }).then(function (hit) {
      if (hit) {
        // refresh in the background so a deploy is picked up next visit
        if (req.url.indexOf(self.registration.scope) === 0) {
          fetch(req).then(function (res) {
            if (res && res.ok) caches.open(VERSION).then(function (c) { c.put(req, res.clone()); });
          }).catch(function () {});
        }
        return hit;
      }
      return fetch(req).then(function (res) {
        if (res && (res.ok || res.type === 'opaque')) {
          var copy = res.clone();
          caches.open(VERSION).then(function (c) { c.put(req, copy); }).catch(function () {});
        }
        return res;
      }).catch(function () {
        // offline and never cached — for a page request, fall back to the workbook itself
        if (req.mode === 'navigate') return caches.match('./index.html');
        return new Response('', { status: 504, statusText: 'Offline' });
      });
    })
  );
});
