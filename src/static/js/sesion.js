/* ==========================================================================
   Fase 40 — privacidad del dispositivo (P1, P3, P5)
   --------------------------------------------------------------------------
   - «Salir»: si hay respuestas sin enviar, se ofrece enviarlas, conservarlas
     cifradas en este dispositivo o descartarlas, explicando qué pasa en cada caso.
     Nunca se borran en silencio.
   - Al salir se borra la clave de la cuenta (sin ella, lo guardado en IndexedDB es
     ilegible) y la copia sin conexión de /encuesta/, y se avisa a las otras pestañas.
   - Sin conexión, la salida se completa en el dispositivo y queda anotada para
     cerrar la sesión en el servidor apenas vuelva la red.
   - Al cargar cualquier página con conexión se borran las claves que no
     corresponden a la sesión abierta (p. ej., una sesión que venció).
   ========================================================================== */
(function () {
    'use strict';

    var DB_NOMBRE = 'encuesta_agingwomen';
    var DB_VERSION = 2;
    var SHELL = '/encuesta/';
    var SALIDA_PENDIENTE = 'aw_salida_pendiente';
    var cuenta = document.body.getAttribute('data-cuenta') || '';
    var canal = null;
    try { canal = window.BroadcastChannel ? new BroadcastChannel('aw-sesion') : null; } catch (e) { canal = null; }

    function csrfDeCookie() {
        var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }
    function leerLocal(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
    function escribirLocal(k, v) {
        try { if (v === null) { window.localStorage.removeItem(k); } else { window.localStorage.setItem(k, v); } }
        catch (e) { /* almacenamiento bloqueado */ }
    }

    // Misma estructura que encuesta.js (versión 2).
    function abrirDB() {
        return new Promise(function (resolve, reject) {
            if (!window.indexedDB) { reject(new Error('sin-indexeddb')); return; }
            var req = indexedDB.open(DB_NOMBRE, DB_VERSION);
            req.onupgradeneeded = function (e) {
                var db = req.result;
                if (!db.objectStoreNames.contains('estado')) {
                    db.createObjectStore('estado', { keyPath: 'clave' });
                } else if (e.oldVersion < 2) {
                    req.transaction.objectStore('estado').clear();
                }
                if (!db.objectStoreNames.contains('llaves')) {
                    db.createObjectStore('llaves', { keyPath: 'cuenta' });
                }
            };
            req.onsuccess = function () {
                req.result.onversionchange = function () { req.result.close(); };
                resolve(req.result);
            };
            req.onerror = function () { reject(req.error); };
        });
    }
    function conTransaccion(almacenes, modo, fn) {
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction(almacenes, modo);
                var resultado = fn(tx);
                tx.oncomplete = function () { resolve(resultado && resultado.result !== undefined ? resultado.result : resultado); };
                tx.onerror = function () { reject(tx.error); };
            });
        });
    }
    function registroDeCuenta(c) {
        return conTransaccion('llaves', 'readonly', function (tx) { return tx.objectStore('llaves').get(c); })
            .catch(function () { return null; });
    }
    function hayPendientes(c) {
        if (window.awEncuesta && window.awEncuesta.hayPendiente()) { return Promise.resolve(true); }
        return registroDeCuenta(c).then(function (reg) {
            return !!(reg && reg.pendientes && Object.keys(reg.pendientes).length);
        });
    }
    // Quita la clave (lo cifrado queda guardado pero ilegible) y, si se pide, borra los datos.
    function cerrarLocal(c, descartar) {
        var almacenes = descartar ? ['estado', 'llaves'] : ['llaves'];
        var local = conTransaccion(almacenes, 'readwrite', function (tx) {
            tx.objectStore('llaves').delete(c);
            if (descartar) { tx.objectStore('estado').delete(IDBKeyRange.bound(c + '|', c + '|￿')); }
        }).catch(function () { return null; });
        return Promise.all([local, borrarCopiaEncuesta()]).then(function () {
            if (canal) { canal.postMessage({ tipo: 'salida', cuenta: c }); }
        });
    }
    function borrarCopiaEncuesta() {
        if (!window.caches) { return Promise.resolve(); }
        return caches.keys().then(function (claves) {
            return Promise.all(claves.map(function (k) {
                return caches.open(k).then(function (cache) { return cache.delete(SHELL); });
            }));
        }).catch(function () { return null; });
    }
    function borrarClavesAjenas(conservar) {
        return conTransaccion('llaves', 'readwrite', function (tx) {
            var almacen = tx.objectStore('llaves');
            var req = almacen.getAllKeys();
            req.onsuccess = function () {
                req.result.forEach(function (k) { if (k !== conservar) { almacen.delete(k); } });
            };
        }).catch(function () { return null; });
    }

    function salirEnServidor() {
        var datos = new FormData();
        datos.append('csrfmiddlewaretoken', csrfDeCookie());
        return fetch('/cuenta/salir/', {
            method: 'POST', body: datos, credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrfDeCookie() }, redirect: 'manual',
        });
    }

    function mostrar(html) {
        var main = document.querySelector('main');
        if (main) { main.innerHTML = '<div class="tarjeta" data-salida-local>' + html + '</div>'; }
    }

    function completarSalida(descartar) {
        return cerrarLocal(cuenta, descartar).then(function () {
            if (!navigator.onLine) { throw new Error('sin-conexion'); }
            return salirEnServidor();
        }).then(function () {
            escribirLocal(SALIDA_PENDIENTE, null);
            window.location.href = '/cuenta/ingresar/';
        }).catch(function () {
            escribirLocal(SALIDA_PENDIENTE, cuenta);   // se anota de qué cuenta es la salida pendiente
            mostrar('<p><strong>Cerraste sesión en este dispositivo.</strong></p>' +
                '<p>No hay conexión a internet. Lo guardado en este dispositivo ya quedó protegido; la sesión ' +
                'se cerrará también en el servidor apenas vuelva la conexión.</p>');
        });
    }

    // Diálogo cuando hay respuestas sin enviar.
    function preguntar() {
        var fondo = document.createElement('div');
        fondo.className = 'dialogo-salida';
        fondo.setAttribute('role', 'dialog');
        fondo.setAttribute('aria-modal', 'true');
        fondo.setAttribute('aria-labelledby', 'dialogo-salida-titulo');
        var puedeEnviar = !!window.awEncuesta;
        fondo.innerHTML =
            '<div class="tarjeta" data-dialogo-salida>' +
            '<h2 id="dialogo-salida-titulo">Tienes respuestas sin enviar</h2>' +
            '<p>Algunas respuestas guardadas en este dispositivo todavía no llegan al servidor. Elige qué hacer:</p>' +
            (puedeEnviar
                ? '<p><button type="button" class="boton" data-opcion="enviar">Enviarlas ahora</button><br>' +
                  '<span class="ayuda">Necesita conexión a internet. Si se envían bien, se cerrará la sesión.</span></p>'
                : '<p><a class="boton" href="/encuesta/" data-opcion="ir">Ir a la encuesta para enviarlas</a><br>' +
                  '<span class="ayuda">Se envían solas al abrir la encuesta con conexión.</span></p>') +
            '<p><button type="button" data-opcion="conservar">Salir y conservarlas protegidas</button><br>' +
            '<span class="ayuda">Quedan cifradas en este dispositivo: nadie puede verlas sin iniciar sesión con ' +
            'esta cuenta. Se enviarán cuando vuelvas a entrar aquí.</span></p>' +
            '<p><button type="button" class="boton boton-peligro" data-opcion="descartar">Descartarlas y salir</button><br>' +
            '<span class="ayuda">Se eliminan de este dispositivo y <strong>no se podrán recuperar</strong>. ' +
            'Lo que ya se envió al servidor no se pierde.</span></p>' +
            '<p><button type="button" data-opcion="cancelar">Cancelar</button></p>' +
            '<p class="errores" data-dialogo-error hidden></p>' +
            '</div>';
        document.body.appendChild(fondo);
        var error = fondo.querySelector('[data-dialogo-error]');
        fondo.addEventListener('click', function (e) {
            var b = e.target.closest('[data-opcion]');
            if (!b) { return; }
            var op = b.getAttribute('data-opcion');
            if (op === 'cancelar') { fondo.remove(); return; }
            if (op === 'conservar') { fondo.remove(); completarSalida(false); return; }
            if (op === 'descartar') {
                if (!window.confirm('¿Eliminar de este dispositivo las respuestas que no se han enviado? ' +
                    'No se podrán recuperar.')) { return; }
                fondo.remove(); completarSalida(true); return;
            }
            if (op === 'enviar') {
                error.hidden = true;
                window.awEncuesta.enviarAhora().then(function () {
                    if (window.awEncuesta.hayPendiente()) {
                        error.textContent = 'No se pudieron enviar (sin conexión o con algún error). ' +
                            'Siguen guardadas en este dispositivo. Elige otra opción o inténtalo más tarde.';
                        error.hidden = false;
                    } else {
                        fondo.remove(); completarSalida(false);
                    }
                });
            }
        });
        var primero = fondo.querySelector('[data-opcion]');
        if (primero) { primero.focus(); }
    }

    // «Salir»
    var form = document.querySelector('form[data-salir]');
    if (form && cuenta) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            hayPendientes(cuenta).then(function (hay) {
                if (hay) { preguntar(); } else { completarSalida(false); }
            });
        });
    }

    // Al cargar: completar una salida hecha sin conexión, y limpiar claves que ya no corresponden.
    var pendiente = leerLocal(SALIDA_PENDIENTE);
    if (pendiente && pendiente === cuenta) {
        cerrarLocal(cuenta, false);
        mostrar('<p><strong>La sesión se cerró en este dispositivo.</strong></p>' +
            '<p>Se terminará de cerrar en el servidor cuando haya conexión.</p>');
        if (navigator.onLine) {
            salirEnServidor().then(function () {
                escribirLocal(SALIDA_PENDIENTE, null);
                window.location.href = '/cuenta/ingresar/';
            }, function () { /* se reintenta en la próxima carga */ });
        }
    } else if (navigator.onLine) {
        // Página recibida del servidor. Si la salida pendiente era de otra cuenta, esa sesión ya
        // fue reemplazada (el ingreso de otra cuenta la termina) o venció: la marca ya no aplica.
        if (pendiente) { escribirLocal(SALIDA_PENDIENTE, null); }
        // Solo la cuenta con sesión abierta conserva su clave.
        borrarClavesAjenas(cuenta);
        if (!cuenta) { borrarCopiaEncuesta(); }
    }

    // ---------- Fase 40, Etapa 2: cierre por inactividad ----------
    // El servidor aplica el límite (apps.usuarios.inactividad). Aquí se avisa antes y, al vencer,
    // se protege el dispositivo: se borra la clave (lo pendiente queda cifrado, no se descarta) y la
    // copia sin conexión, se avisa a las otras pestañas y se vuelve al ingreso. Solo la interacción
    // real (teclado, toque, clic) renueva la sesión; las tareas en segundo plano no.
    var LIMITE = parseInt(document.body.getAttribute('data-inactividad') || '0', 10) * 1000;
    var AVISO = parseInt(document.body.getAttribute('data-aviso') || '120', 10) * 1000;
    var MARGEN = 45000;              // el servidor puede tener la marca hasta 30 s más antigua
    var RENOVAR_CADA = 60000;        // como mucho un aviso de actividad por minuto
    var CLAVE_ACT = 'aw_actividad:' + cuenta;
    var ultimoAvisoEnviado = 0;
    var dialogoInactividad = null;
    var vencida = false;

    function ultimaActividad() { return parseInt(leerLocal(CLAVE_ACT) || '0', 10) || 0; }
    function marcarActividad(t) {
        if (t > ultimaActividad()) { escribirLocal(CLAVE_ACT, String(t)); }
    }
    function avisarActividad() {
        var ahora = Date.now();
        if (ahora - ultimoAvisoEnviado < RENOVAR_CADA) { return; }
        ultimoAvisoEnviado = ahora;
        if (!navigator.onLine) { marcarActividad(ahora); return; }   // sin conexión: cuenta en el dispositivo
        var datos = new FormData();
        datos.append('csrfmiddlewaretoken', csrfDeCookie());
        fetch('/cuenta/actividad/', { method: 'POST', body: datos, credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrfDeCookie() }, redirect: 'manual' })
            .then(function (r) {
                if (r.status === 204) { marcarActividad(ahora); } else if (r.status === 401) { vencer(); }
            }, function () { marcarActividad(ahora); });               // error de red: igual que sin conexión
    }
    function quitarDialogo() { if (dialogoInactividad) { dialogoInactividad.remove(); dialogoInactividad = null; } }
    function mostrarAvisoInactividad(restante) {
        if (!dialogoInactividad) {
            dialogoInactividad = document.createElement('div');
            dialogoInactividad.className = 'dialogo-salida';
            dialogoInactividad.setAttribute('role', 'alertdialog');
            dialogoInactividad.setAttribute('aria-modal', 'true');
            dialogoInactividad.setAttribute('aria-labelledby', 'aviso-inactividad-titulo');
            dialogoInactividad.innerHTML = '<div class="tarjeta" data-aviso-inactividad>' +
                '<h2 id="aviso-inactividad-titulo">¿Sigues ahí?</h2>' +
                '<p>Por seguridad, la sesión se cerrará por inactividad en <strong data-restante></strong>. ' +
                'Las respuestas que no hayas enviado quedarán protegidas en este dispositivo.</p>' +
                '<p><button type="button" class="boton" data-seguir>Seguir conectada</button></p></div>';
            document.body.appendChild(dialogoInactividad);
            dialogoInactividad.querySelector('[data-seguir]').addEventListener('click', function () {
                ultimoAvisoEnviado = 0; avisarActividad(); quitarDialogo();
            });
            dialogoInactividad.querySelector('[data-seguir]').focus();
        }
        var s = Math.max(0, Math.ceil(restante / 1000));
        dialogoInactividad.querySelector('[data-restante]').textContent =
            Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2) + ' minutos';
    }
    function vencer() {
        if (vencida) { return; }
        vencida = true;
        quitarDialogo();
        cerrarLocal(cuenta, false).then(function () {
            if (!navigator.onLine) { throw new Error('sin-conexion'); }
            return salirEnServidor();
        }).then(function () {
            escribirLocal(SALIDA_PENDIENTE, null);
            window.location.href = '/cuenta/ingresar/?inactividad=1';
        }).catch(function () {
            escribirLocal(SALIDA_PENDIENTE, cuenta);
            mostrar('<p><strong>La sesión se cerró por inactividad.</strong></p>' +
                '<p>Lo guardado en este dispositivo quedó protegido. Para seguir, vuelve a iniciar sesión ' +
                'cuando tengas conexión.</p><p class="enlaces"><a href="/cuenta/ingresar/">Iniciar sesión</a></p>');
        });
    }
    function revisarInactividad() {
        if (vencida || !LIMITE) { return; }
        var restante = ultimaActividad() + LIMITE - MARGEN - Date.now();
        if (restante <= 0) { vencer(); return; }
        if (restante <= AVISO) { mostrarAvisoInactividad(restante); } else { quitarDialogo(); }
    }
    if (cuenta && LIMITE && leerLocal(SALIDA_PENDIENTE) !== cuenta) {
        // Con conexión, esta página llegó del servidor: su marca de actividad es de ahora. Sin
        // conexión (copia guardada) solo se marca si no había ninguna.
        if (navigator.onLine || !ultimaActividad()) { marcarActividad(Date.now()); }
        ['keydown', 'pointerdown', 'input', 'touchstart'].forEach(function (ev) {
            document.addEventListener(ev, function () {
                if (!vencida && !dialogoInactividad) { avisarActividad(); }
            }, { passive: true, capture: true });
        });
        window.addEventListener('storage', function (e) { if (e.key === CLAVE_ACT) { revisarInactividad(); } });
        // encuesta.js avisa cuando el servidor responde 401 (sesión vencida).
        window.addEventListener('aw:sesion-vencida', vencer);
        if (canal) {
            canal.addEventListener('message', function (e) {
                if (e.data && e.data.tipo === 'salida' && e.data.cuenta === cuenta && !vencida) {
                    // Otra pestaña cerró la sesión (voluntariamente o por inactividad): esta deja de mostrar datos.
                    vencida = true; quitarDialogo();
                    if (!window.awEncuesta) {
                        mostrar('<p><strong>La sesión se cerró en este dispositivo.</strong></p>' +
                            '<p class="enlaces"><a href="/cuenta/ingresar/">Iniciar sesión</a></p>');
                    }
                }
            });
        }
        setInterval(revisarInactividad, 5000);
    } else if (cuenta && LIMITE) {
        window.addEventListener('aw:sesion-vencida', vencer);
    }

    // Retiro (encuestas/retirado.html): borra los datos de esta cuenta en este dispositivo.
    window.awSesion = {
        revisarInactividad: revisarInactividad,
        borrarCuenta: function () {
            if (!cuenta) { return Promise.resolve(); }
            return cerrarLocal(cuenta, true).then(function () {
                if (canal) { canal.postMessage({ tipo: 'retiro', cuenta: cuenta }); }
            });
        },
    };
})();
