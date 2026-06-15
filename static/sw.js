// 灵枢 — Service Worker v1
// PWA 离线缓存 + 安装支持

const CACHE_NAME = 'lingshu-v2.4.0';
const urlsToCache = [
  '/',
  '/index.html',
  '/css/app.css',
  '/js/storage.js',
  '/js/almanac.js',
  '/js/fortune.js',
  '/js/constitution.js',
  '/js/companion.js',
  '/js/voice.js',
  '/js/agent.js',
  '/js/camera.js',
  '/js/share.js',
  '/js/app.js',
  '/assets/manifest.json',
  '/assets/icon-192.png',
  '/assets/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache).catch((err) => {
        console.warn('[SW] Cache addAll partial:', err.message);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // 跳过 API 请求和 TTS 音频
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/')) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, clone);
            });
          }
          return response;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
