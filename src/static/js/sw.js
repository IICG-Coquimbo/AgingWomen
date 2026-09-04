/* Service Worker — soporte offline (Sección 5.1 del spec).
   - Cachea el shell de la app.
   - Esquema (/api/esquema/): red primero, cae al caché sin conexión.
   - Estáticos: se sirve el caché al instante y se revalida en segundo plano.
   - Nunca intercepta POST (la sincronización va siempre por la red).
*/
var CACHE = 'aging-women-v1';
var SHELL = [
    '/encuesta/',
    '/static/css/tema.css',
    '/static/js/encuesta.js',
    '/static/manifest.webmanifest',
    '/static/icons/icono.svg'
];

self.addEventListener('install', function (e) {
    e.waitUntil(
        caches.open(CACHE)
            .then(function (c) { return c.addAll(SHELL); })
            .then(function () { return self.skipWaiting(); })
    );
});

self.addEventListener('activate', function (e) {
    e.waitUntil(
        caches.keys().then(function (claves) {
            return Promise.all(claves
                .filter(function (k) { return k !== CACHE; })
                .map(function (k) { return caches.delete(k); }));
        }).then(function () { return self.clients.claim(); })
    );
});

self.addEventListener('fetch', function (e) {
    var req = e.request;
    if (req.method !== 'GET') { return; }  // POST /api/sincronizar/ pasa directo a la red

    var url = new URL(req.url);
    if (url.origin !== self.location.origin) { return; }

    // Esquema de la encuesta: red primero, caché de respaldo.
    if (url.pathname === '/api/esquema/') {
        e.respondWith(
            fetch(req).then(function (resp) {
                var copia = resp.clone();
                caches.open(CACHE).then(function (c) { c.put(req, copia); });
                return resp;
            }).catch(function () { return caches.match(req); })
        );
        return;
    }

    // Shell y estáticos: stale-while-revalidate.
    if (SHELL.indexOf(url.pathname) !== -1 || url.pathname.indexOf('/static/') === 0) {
        e.respondWith(
            caches.match(req).then(function (hit) {
                var red = fetch(req).then(function (resp) {
                    var copia = resp.clone();
                    caches.open(CACHE).then(function (c) { c.put(req, copia); });
                    return resp;
                }).catch(function () { return hit; });
                return hit || red;
            })
        );
        return;
    }

    // Navegación sin conexión: cae a la pantalla de la encuesta.
    if (req.mode === 'navigate') {
        e.respondWith(fetch(req).catch(function () { return caches.match('/encuesta/'); }));
    }
});
