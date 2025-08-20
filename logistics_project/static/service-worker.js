
cat > logistics_project/static/service-worker.js <<'EOF'
const CACHE_NAME = "gwx-v1";
const ASSETS = [
  "/",
  "/manifest.json"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request).then((cached) => {
      const fetchPromise = fetch(e.request).then((response) => {
        try {
          if (response && response.status === 200 && response.type === "basic") {
            const respClone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(e.request, respClone));
          }
        } catch (err) {}
        return response;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
EOF
