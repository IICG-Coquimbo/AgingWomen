/* Service Worker — soporte offline (Sección 5.1 del spec).
   - Precachea SOLO estáticos sin sesión (CSS, JS, manifest, icono).
   - /encuesta/ es un documento con sesión: red primero; si no hay conexión se
     sirve la última copia BUENA. Nunca se cachea ni se sirve una respuesta
     redirigida (una redirección a /cuenta/ingresar/ rompería la navegación
     con net::ERR_FAILED).
   - Esquema (/api/esquema/): red primero, caché de respaldo.
   - Nunca intercepta POST (login, salir y /api/sincronizar/ van siempre por red).
*/
var CACHE = 'aging-women-v10';  // subir la versión cuando cambian encuesta.js o tema.css
var SHELL = '/encuesta/';
var ESTATICOS = [
    '/static/css/tema.css',
    '/static/js/encuesta.js',
    '/static/manifest.webmanifest',
    '/static/icons/icono.svg'
];

self.addEventListener('install', function (e) {
    e.waitUntil(
        caches.open(CACHE)
            .then(function (c) { return c.addAll(ESTATICOS); })
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

// Guarda en caché solo respuestas completas y NO redirigidas.
function guardar(req, resp) {
    if (resp && resp.ok && !resp.redirected) {
        var copia = resp.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copia); });
    }
    return resp;
}

self.addEventListener('fetch', function (e) {
    var req = e.request;
    if (req.method !== 'GET') { return; }  // POST pasa directo a la red

    var url = new URL(req.url);
    if (url.origin !== self.location.origin) { return; }

    // Navegaciones (incluye /encuesta/ y la salida): SIEMPRE red primero.
    // Sin conexión se cae a la última copia buena de /encuesta/.
    if (req.mode === 'navigate') {
        e.respondWith(
            fetch(req)
                .then(function (resp) {
                    if (url.pathname === SHELL) { guardar(SHELL, resp); }
                    return resp;
                })
                .catch(function () { return caches.match(SHELL); })
        );
        return;
    }

    // Esquema de la encuesta: red primero, caché de respaldo.
    if (url.pathname === '/api/esquema/') {
        e.respondWith(
            fetch(req).then(function (resp) { return guardar(req, resp); })
                .catch(function () { return caches.match(req); })
        );
        return;
    }

    // Estáticos: caché al instante, se revalida en segundo plano.
    if (url.pathname.indexOf('/static/') === 0) {
        e.respondWith(
            caches.match(req).then(function (hit) {
                var red = fetch(req).then(function (resp) { return guardar(req, resp); })
                    .catch(function () { return hit; });
                return hit || red;
            })
        );
        return;
    }
});
