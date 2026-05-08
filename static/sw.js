const CACHE_NAME = 'troqui-cache-v2';
const urlsToCache = [
  '/static/style.css',
  '/static/manifest.json'
];

// Instala o Service Worker e armazena os arquivos principais (estáticos) em cache
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Ativa e limpa caches antigos se houver
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Estratégia "Network First" (Sempre tenta a rede primeiro, evita quebrar o site dinâmico)
self.addEventListener('fetch', event => {
  // Ignora requisições que não sejam GET (como POST de login)
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Se a rede funcionou, pode até salvar no cache, mas aqui apenas retornamos
        return response;
      })
      .catch(() => {
        // Se a rede falhar (offline), tenta buscar do cache
        return caches.match(event.request);
      })
  );
});
