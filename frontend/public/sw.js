/* Minimal offline support: cache shell, fallback to offline.html */
const CACHE = "streamhub-v1";
const SHELL = ["/", "/index.html", "/offline.html", "/manifest.webmanifest"];
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => { e.waitUntil(self.clients.claim()); });
self.addEventListener("fetch", (e) => {
  const { request } = e;
  if (request.method !== "GET" || request.url.includes("/api/")) return;
  e.respondWith(
    fetch(request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(request, copy));
        return res;
      })
      .catch(async () => (await caches.match(request)) || caches.match("/offline.html"))
  );
});
