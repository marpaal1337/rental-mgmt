const CACHE_NAME = 'rental-mgmt-v1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
]

self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS)),
  )
})

self.addEventListener('fetch', (event: FetchEvent) => {
  const { request } = event

  if (request.method !== 'GET') return

  if (request.url.includes('/api/')) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) =>
        fetch(request)
          .then((response) => {
            cache.put(request, response.clone())
            return response
          })
          .catch(() => cache.match(request) ?? new Response(null, { status: 503 })),
      ),
    )
    return
  }

  event.respondWith(
    caches.match(request).then((cached) => cached ?? fetch(request)),
  )
})

self.addEventListener('activate', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))),
    ),
  )
})
