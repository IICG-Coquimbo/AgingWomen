/* ==========================================================================
   App cliente de la encuesta
   --------------------------------------------------------------------------
   - Descarga el esquema (/api/esquema/) y lo guarda en IndexedDB para uso offline.
   - Renderiza una sección a la vez desde el esquema.
   - Guarda cada respuesta en IndexedDB al instante y sincroniza cuando hay
     conexión (offline-first).
   - Motor de preguntas/secciones condicionales, 100% local: igualdad,
     'meses_desde_lt' (ausencia menstrual) y 'contiene' (selección múltiple).
   - Escalas: MRS con escala de calor + caritas; el resto, escala horizontal
     con gradiente de color sin caritas.
   ========================================================================== */
(function () {
    'use strict';

    var DB_NOMBRE = 'encuesta_agingwomen';
    // Fase 40 (privacidad): versión 2 = todo lo guardado va cifrado con la clave de la cuenta.
    var DB_VERSION = 2;
    var URL_CLAVE = '/api/clave-local/';
    var URL_ESQUEMA = '/api/esquema/';
    var URL_SYNC = '/api/sincronizar/';
    var URL_EVALUACION = '/mi-evaluacion/';
    var URL_RONDA = '/api/ronda-actual/';
    // Fase 40B-2: protocolo de sincronización (ver sync.py). El 2 envía la ronda local,
    // un id_cierre al finalizar y los ítems MRS confirmados.
    var PROTOCOLO = 2;

    var cont = document.getElementById('encuesta');

    // Fase 29: el personal de salud completa la encuesta de una paciente
    // existente (data-paciente) o registra una nueva (data-rut).
    var MODO_PROF = cont.dataset.modo === 'profesional';
    var pacienteId = cont.dataset.paciente ? parseInt(cont.dataset.paciente, 10) : null;
    var rutNueva = cont.dataset.rut || '';
    var urlFicha = cont.dataset.urlFicha || '';
    // Fase 40 (retiro presencial): participación vigente de la paciente según el servidor, y la
    // participación a la que pertenecen las respuestas guardadas en este dispositivo.
    var participacionPagina = cont.dataset.participacionPaciente || null;
    var participacionDatos = participacionPagina;
    var identBloqueada = false;  // la paciente se registró ella: su Identificación es solo lectura

    // El CSRF se lee de la cookie en cada envío (no al cargar el script): si
    // esta página quedó cacheada offline, el token embebido en el HTML puede
    // haber quedado obsoleto (rotó al iniciar sesión), pero la cookie
    // `csrftoken` siempre trae el valor vigente.
    function csrfToken() {
        var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : '';
    }

    var esquema = null;
    var respuestas = {};   // { seccion: { campo: valor } }
    var uuids = {};        // { seccion: uuid }
    var indice = 0;        // índice dentro de las secciones aplicables
    var bienvenidaOk = false;  // ya pasó la pantalla de definiciones + filtro de edad
    var envioFinalPendiente = false;  // se pulsó "Finalizar" pero aún no se confirma con el servidor
    // Fase 27: si al abrir la encuesta la Identificación ya estaba completa
    // (visita posterior), antes de mostrar el formulario se pregunta si desea
    // modificar algún dato. Se pregunta una sola vez por carga de página.
    var preguntarIdentificacion = false;
    var sucio = false;   // hay respuestas locales sin confirmar por el servidor
    var ronda = null;    // ronda a la que pertenecen las respuestas locales
    // Fase 31: fecha (AAAA-MM-DD) desde la que la usuaria puede responder otra
    // ronda. Se guarda localmente para respetar el plazo también sin conexión.
    var disponibleDesde = null;
    // Fase 40B-2: identificador del cierre en curso. Se genera al pulsar Finalizar y se
    // reutiliza en cada reintento, así el servidor no cierra dos veces la misma ronda.
    var idCierre = null;
    // Ítems MRS que la persona eligió en esta ronda ({ pregunta_n: true }).
    var confirmadosMrs = {};
    // Ítems MRS en 0 de un registro anterior a la 40B-2 que el servidor pide confirmar.
    var mrsPorConfirmar = [];
    // Respuestas locales que no pudieron enviarse porque su ronda ya estaba cerrada.
    // Nunca se borran solas: quedan en IndexedDB ('conflictos').
    var conflictos = [];
    // Etapa 5B-3: huella de lo que el servidor tenía cuando esta página leyó o guardó cada sección
    // (null = no tenía nada). Si ya no coincide, el servidor rechaza el envío sin escribir.
    var versiones = {};
    // Lo enviado sin recibir respuesta: si llegó a guardarse, el servidor lo reconoce como propio.
    var sinConfirmar = {};
    var MAX_SIN_CONFIRMAR = 5;
    var conflictoVersion = null;   // respuesta 409 a la espera de que la persona decida
    var generacion = 0;            // sube con cada respuesta; distingue lo cambiado durante un envío
    var envioEnCurso = null;       // solo un envío a la vez: cada uno parte de la versión del anterior
    var otroEnvio = null;          // envío pedido mientras había otro en curso
    var firmaVisible = '';         // secciones y preguntas visibles en el último dibujo completo
    var punteroPresionado = false;
    var trasPuntero = null;        // redibujo aplazado hasta soltar el ratón o el dedo

    function hoyISO() {
        var d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }
    function fechaLegible(iso) { return iso.split('-').reverse().join('-'); }
    function enEspera() { return !MODO_PROF && !!disponibleDesde && hoyISO() < disponibleDesde; }
    function textoEspera() {
        return 'Podrás volver a responder la encuesta a partir del ' + fechaLegible(disponibleDesde) + '.';
    }

    // Nombres cortos para los botones de navegación (los títulos completos de
    // algunas secciones son demasiado largos para un botón).
    var TITULOS_CORTOS = {
        mrs: 'Escala MRS',
        mrs_complementario: 'Cuestionario complementario',
        empa: 'EMPA',
        conocimiento_sistema: 'Conocimiento del sistema',
    };
    function tituloCorto(seccion) { return TITULOS_CORTOS[seccion.tipo] || seccion.titulo; }

    // Fase 27: tramos de la barra de progreso (rojo < 34 %, amarillo hasta 66 %, verde desde 67 %).
    function tramoProgreso(pct) {
        if (pct === 0) {
            return { clase: 'bajo', msg: '¡Comencemos! Tus respuestas se guardan a medida que avanzas.' };
        }
        if (pct < 34) { return { clase: 'bajo', msg: 'Buen comienzo. Cada sección que completas suma mucho.' }; }
        if (pct < 67) { return { clase: 'medio', msg: 'Vas a mitad de camino. ¡Sigue así!' }; }
        if (pct < 100) { return { clase: 'alto', msg: '¡Ya casi terminas! Te quedan pocas secciones.' }; }
        return { clase: 'alto', msg: '¡Completaste todas las secciones! Ya puedes presionar Finalizar.' };
    }

    // ---------- IndexedDB (cifrado, Fase 40) ----------
    // 'estado': {clave: '<cuenta>|[<contexto>|]<nombre>', iv, datos} — datos cifrados con AES-GCM.
    // 'llaves': {cuenta, llave (CryptoKey no exportable), participacion, expira, pendientes}.
    // La clave la entrega el servidor solo con sesión iniciada (/api/clave-local/) y se borra al
    // cerrar sesión (static/js/sesion.js): sin ella lo guardado es ilegible, aun sin conexión.
    // La versión 1 guardaba todo en claro: al actualizar se vacía (solo hubo datos de prueba).
    function abrirDB() {
        return new Promise(function (resolve, reject) {
            var req = indexedDB.open(DB_NOMBRE, DB_VERSION);
            req.onupgradeneeded = function (e) {
                var db = req.result;
                if (!db.objectStoreNames.contains('estado')) {
                    db.createObjectStore('estado', { keyPath: 'clave' });
                } else if (e && e.oldVersion < 2) {
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

    var cuentaActual = cont.dataset.cuenta || '';
    var llave = null;          // CryptoKey de la cuenta (null = no se puede leer ni escribir)
    var participacion = null;  // participación vigente (cambia tras un retiro y un consentimiento nuevo)
    var sesionCerrada = false;

    function errorConCodigo(codigo) { var e = new Error(codigo); e.codigo = codigo; return e; }

    function llavesGet(cuenta) {
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var r = db.transaction('llaves', 'readonly').objectStore('llaves').get(cuenta);
                r.onsuccess = function () { resolve(r.result || null); };
                r.onerror = function () { reject(r.error); };
            });
        });
    }
    function llavesPut(registro) {
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction('llaves', 'readwrite');
                tx.objectStore('llaves').put(registro);
                tx.oncomplete = function () { resolve(true); };
                tx.onerror = function () { reject(tx.error); };
            });
        });
    }
    // Borra todo lo guardado por una cuenta (solo cuando pertenece a una participación retirada).
    function borrarEspacio(cuenta) {
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction(['estado', 'llaves'], 'readwrite');
                tx.objectStore('estado').delete(IDBKeyRange.bound(cuenta + '|', cuenta + '|￿'));
                tx.objectStore('llaves').delete(cuenta);
                tx.oncomplete = function () { resolve(true); };
                tx.onerror = function () { reject(tx.error); };
            });
        });
    }
    function importarLlave(base64) {
        var bytes = Uint8Array.from(atob(base64), function (c) { return c.charCodeAt(0); });
        return crypto.subtle.importKey('raw', bytes, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
    }
    function vigente(reg) { return !!(reg && reg.llave && (!reg.expira || Date.parse(reg.expira) > Date.now())); }
    function borrarLlave() {
        return abrirDB().then(function (db) {
            return new Promise(function (resolve) {
                var tx = db.transaction('llaves', 'readwrite');
                tx.objectStore('llaves').delete(cuentaActual);
                tx.oncomplete = tx.onerror = function () { resolve(true); };
            });
        }).catch(function () { return true; });
    }

    // Obtiene la clave: del servidor si hay conexión; si no, la guardada en este dispositivo
    // mientras la sesión no haya terminado. Si la participación cambió (retiro y consentimiento
    // nuevo), lo guardado con la clave anterior pertenece a la participación retirada y se borra.
    // Fase 40 E2: avisa a sesion.js que el servidor cerró la sesión (sin fallar si no está disponible).
    function avisarSesionVencida() {
        try { window.dispatchEvent(new Event('aw:sesion-vencida')); } catch (e) { /* sin eventos de ventana */ }
    }

    function obtenerLlave() {
        if (!cuentaActual) { return Promise.reject(errorConCodigo('sin-sesion')); }
        return fetch(URL_CLAVE, { credentials: 'same-origin', headers: { 'Accept': 'application/json', 'X-Segundo-Plano': '1' } })
            .then(function (r) {
                return r.json().then(function (j) { return { status: r.status, cuerpo: j }; },
                    function () { return { status: 0, cuerpo: null }; });
            }, function () { return null; })   // sin conexión
            .then(function (res) {
                if (res && res.status === 401) {
                    avisarSesionVencida();   // Fase 40 E2 (sesion.js)
                    return borrarLlave().then(function () { throw errorConCodigo('sin-sesion'); });
                }
                if (res && res.status === 403) { throw errorConCodigo('sin-consentimiento'); }
                if (res && res.status === 200 && res.cuerpo && res.cuerpo.cuenta === cuentaActual) {
                    return llavesGet(cuentaActual).then(function (previo) {
                        var cambio = !!(previo && previo.participacion && previo.participacion !== res.cuerpo.participacion);
                        return (cambio ? borrarEspacio(cuentaActual) : Promise.resolve()).then(function () {
                            return importarLlave(res.cuerpo.clave);
                        }).then(function (k) {
                            return llavesPut({ cuenta: cuentaActual, llave: k, participacion: res.cuerpo.participacion,
                                expira: res.cuerpo.expira, pendientes: (!cambio && previo && previo.pendientes) || {} })
                                .then(function () { return { llave: k, participacion: res.cuerpo.participacion }; });
                        });
                    });
                }
                return llavesGet(cuentaActual).then(function (reg) {
                    if (!vigente(reg)) { throw errorConCodigo('sin-sesion'); }
                    return { llave: reg.llave, participacion: reg.participacion };
                });
            })
            .then(function (r) { llave = r.llave; participacion = r.participacion; });
    }

    // Indica (sin datos de salud) si esta cuenta tiene algo sin enviar: lo usa «Salir».
    function marcarPendiente() {
        var hay = !!(sucio || envioFinalPendiente || (conflictos && conflictos.length));
        var ctx = usuarioActual || 'propia';
        return llavesGet(cuentaActual).then(function (reg) {
            if (!reg) { return; }
            reg.pendientes = reg.pendientes || {};
            if (hay) { reg.pendientes[ctx] = true; } else { delete reg.pendientes[ctx]; }
            return llavesPut(reg);
        }).catch(function () { /* el aviso de «Salir» es complementario */ });
    }

    var codificador = new TextEncoder();
    var decodificador = new TextDecoder();
    function cifrar(valor) {
        var iv = crypto.getRandomValues(new Uint8Array(12));
        return crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv }, llave, codificador.encode(JSON.stringify(valor)))
            .then(function (datos) { return { iv: iv, datos: datos }; });
    }
    function descifrar(registro) {
        if (!registro || !registro.iv) { return Promise.resolve(null); }
        return crypto.subtle.decrypt({ name: 'AES-GCM', iv: registro.iv }, llave, registro.datos)
            .then(function (b) { return JSON.parse(decodificador.decode(b)); },
                function () { return null; });   // cifrado con otra clave: ilegible
    }

    // Cada cuenta tiene su propio espacio; en modo profesional, además, cada paciente.
    function claveIdb(clave) { return cuentaActual + '|' + (MODO_PROF ? usuarioActual + '|' : '') + clave; }

    function idbGet(clave) {
        if (!llave || sesionCerrada) { return Promise.resolve(null); }
        clave = claveIdb(clave);
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var r = db.transaction('estado', 'readonly').objectStore('estado').get(clave);
                r.onsuccess = function () { resolve(r.result); };
                r.onerror = function () { reject(r.error); };
            });
        }).then(descifrar);
    }
    // Fase 40B-2: si el dispositivo no puede guardar (almacenamiento lleno, modo privado),
    // se avisa en vez de fallar en silencio. Devuelve false en ese caso.
    var CLAVES_PENDIENTE = { sucio: 1, envio_final: 1, pendiente_envio: 1, conflictos: 1 };
    function idbSet(clave, valor) {
        if (sesionCerrada || !llave) { return Promise.resolve(false); }   // tras «Salir» no se escribe nada
        var nombre = clave;
        clave = claveIdb(clave);
        return Promise.all([abrirDB(), cifrar(valor)]).then(function (r) {
            var db = r[0], cifrado = r[1];
            // Cifrar toma tiempo: lo local pudo borrarse mientras tanto (retiro, «Salir»).
            if (sesionCerrada || !llave) { return false; }
            return new Promise(function (resolve, reject) {
                var tx = db.transaction('estado', 'readwrite');
                tx.objectStore('estado').put({ clave: clave, iv: cifrado.iv, datos: cifrado.datos });
                tx.oncomplete = function () { resolve(true); };
                tx.onerror = function () { reject(tx.error); };
            });
        }).then(function (ok) {
            if (CLAVES_PENDIENTE[nombre]) { marcarPendiente(); }
            return ok;
        }).catch(function (err) {
            console.error(err);
            avisoSync('No se pudo guardar en este dispositivo. No cierres esta página hasta que tus ' +
                'respuestas se envíen con conexión a internet.', 'error');
            return false;
        });
    }

    // ---------- Carga inicial ----------
    // IndexedDB es por navegador, no por cuenta: si en este dispositivo antes
    // respondió otra persona (u otro paciente, en el caso de un profesional)
    // sin cerrar sesión primero, hay que descartar ese estado — si no, se
    // arrastran uuid_local ajenos y el servidor rechaza el guardado (o peor,
    // se mezclan respuestas de otra persona).
    var usuarioActual = cont.dataset.usuario || '';

    // Fase 40B-2: si la persona anterior dejó respuestas sin enviar, no se borran: se
    // apartan con su identificador y se le devuelven cuando vuelva a entrar en este
    // dispositivo. Ya estaban guardadas aquí; solo cambian de clave.
    function limpiarEstadoLocal(usuarioAnterior) {
        var apartar = Promise.resolve();
        if (usuarioAnterior && (sucio || envioFinalPendiente)) {
            apartar = idbSet('respaldo_de|' + usuarioAnterior, {
                respuestas: respuestas, uuids: uuids, ronda: ronda, envio_final: envioFinalPendiente,
                id_cierre: idCierre, mrs_confirmados: confirmadosMrs, fecha: new Date().toISOString(),
            });
        }
        return apartar.then(function () {
            respuestas = {};
            uuids = {};
            bienvenidaOk = false;
            envioFinalPendiente = false;
            sucio = false;
            ronda = null;
            idCierre = null;
            confirmadosMrs = {};
            versiones = {};
            sinConfirmar = {};
            return Promise.all([
                idbSet('versiones', versiones),
                idbSet('sin_confirmar', sinConfirmar),
                idbSet('respuestas', respuestas),
                idbSet('uuids', uuids),
                idbSet('bienvenida', false),
                idbSet('envio_final', false),
                idbSet('sucio', false),
                idbSet('pendiente_envio', false),
                idbSet('ronda', null),
                idbSet('id_cierre', null),
                idbSet('mrs_confirmados', {}),
            ]);
        });
    }

    // Devuelve a esta persona lo que había dejado sin enviar en este dispositivo.
    function recuperarRespaldoPropio() {
        var clave = 'respaldo_de|' + usuarioActual;
        return idbGet(clave).then(function (r) {
            if (!r || Object.keys(respuestas).length) { return; }
            respuestas = r.respuestas || {};
            uuids = r.uuids || {};
            ronda = r.ronda || null;
            envioFinalPendiente = !!r.envio_final;
            idCierre = r.id_cierre || null;
            confirmadosMrs = r.mrs_confirmados || {};
            sucio = true;
            bienvenidaOk = true;
            return Promise.all([
                idbSet('respuestas', respuestas), idbSet('uuids', uuids), idbSet('ronda', ronda),
                idbSet('envio_final', envioFinalPendiente), idbSet('id_cierre', idCierre),
                idbSet('mrs_confirmados', confirmadosMrs), idbSet('sucio', true), idbSet('bienvenida', true),
            ]).then(function () { return idbSet(clave, null); });
        });
    }

    // Aparta las respuestas locales sin enviar (copia inmediata) antes de empezar otra ronda.
    function archivarPendientes(motivo) {
        conflictos.push({
            motivo: motivo, ronda: ronda, fecha: new Date().toISOString(),
            respuestas: JSON.parse(JSON.stringify(respuestas)), uuids: JSON.parse(JSON.stringify(uuids)),
        });
        return idbSet('conflictos', conflictos);
    }

    // Otra pestaña cerró sesión (o se retiró): esta deja de mostrar y de guardar datos.
    function alCerrarseSesion() {
        sesionCerrada = true;
        llave = null;
        respuestas = {};
        uuids = {};
        cont.innerHTML = '<div class="tarjeta"><p class="errores">La sesión se cerró en este dispositivo. ' +
            'Para ver o enviar tus respuestas, vuelve a iniciar sesión.</p>' +
            '<p class="enlaces"><a href="/cuenta/ingresar/">Iniciar sesión</a></p></div>';
    }
    if (window.BroadcastChannel) {
        try {
            new BroadcastChannel('aw-sesion').onmessage = function (e) {
                if (e.data && (e.data.tipo === 'salida' || e.data.tipo === 'retiro') && e.data.cuenta === cuentaActual) {
                    alCerrarseSesion();
                }
            };
        } catch (err) { /* sin BroadcastChannel: la clave borrada impide igual leer y escribir */ }
    }

    // Fase 40: lo pendiente se envía con la participación para la que se preparó; si la
    // paciente se retiró después, el servidor lo rechaza (409 participacion_anterior).
    function fijarParticipacionPaciente() {
        return idbGet('participacion_paciente').then(function (guardada) {
            if (guardada && guardada !== participacionPagina && (sucio || envioFinalPendiente)) {
                participacionDatos = guardada;
                return;
            }
            participacionDatos = participacionPagina;
            return idbSet('participacion_paciente', participacionPagina);
        });
    }

    // «Salir» (sesion.js) ofrece enviar lo pendiente antes de cerrar la sesión.
    window.awEncuesta = {
        hayPendiente: function () { return !!(sucio || envioFinalPendiente); },
        enviarAhora: function () { return intentarSync(envioFinalPendiente); },
    };

    function iniciar() {
        obtenerLlave().then(function () { return Promise.all([
            idbGet('esquema'), idbGet('respuestas'), idbGet('uuids'), idbGet('bienvenida'),
            idbGet('envio_final'), idbGet('usuario'), idbGet('sucio'), idbGet('pendiente_envio'),
            idbGet('ronda'), idbGet('disponible_desde'),
            idbGet('id_cierre'), idbGet('mrs_confirmados'), idbGet('conflictos'),
            idbGet('versiones'), idbGet('sin_confirmar'),
        ]); })
            .then(function (vals) {
                esquema = vals[0];
                respuestas = vals[1] || {};
                uuids = vals[2] || {};
                bienvenidaOk = !!vals[3];
                envioFinalPendiente = !!vals[4];
                var usuarioGuardado = vals[5];
                sucio = !!vals[6] || !!vals[7];
                ronda = vals[8] || null;
                disponibleDesde = vals[9] || null;
                idCierre = vals[10] || null;
                confirmadosMrs = vals[11] || {};
                conflictos = vals[12] || [];
                versiones = vals[13] || {};
                sinConfirmar = vals[14] || {};

                var cambioDeUsuario = usuarioGuardado && usuarioGuardado !== usuarioActual;
                var promesa = cambioDeUsuario ? limpiarEstadoLocal(usuarioGuardado) : Promise.resolve();
                return promesa.then(function () {
                    return idbSet('usuario', usuarioActual);
                }).then(function () {
                    return cambioDeUsuario ? recuperarRespaldoPropio() : null;
                }).then(function () {
                    return MODO_PROF ? fijarParticipacionPaciente() : null;
                });
            })
            .then(function () {
                return traerEsquema();
            })
            .then(function () {
                if (!esquema) { throw new Error('sin-esquema'); }
                asegurarUuids();
                return traerRondaActual();
            })
            .then(function () {
                if (MODO_PROF && pacienteId && !respuestas.identificacion) {
                    throw new Error('sin-datos-paciente');
                }
                if (enEspera()) {
                    // Fase 31: dentro del plazo entre rondas no se muestra la encuesta.
                    cont.innerHTML = '<div class="tarjeta"><p class="burbuja-espera">' +
                        esc(textoEspera()) + '</p><p class="enlaces"><a href="/">Volver al menú</a></p></div>';
                    return;
                }
                var ident = esquema.secciones.filter(function (s) {
                    return s.tipo === 'identificacion';
                })[0];
                preguntarIdentificacion = !MODO_PROF && !!(bienvenidaOk && ident &&
                    respuestas.identificacion && seccionCompleta(ident));
                // Botones "ir a sección" (delegado: el bloque se reemplaza al actualizar el progreso).
                cont.addEventListener('click', function (e) {
                    var b = e.target.closest('[data-ir]');
                    if (!b || b.disabled) { return; }
                    indice = parseInt(b.getAttribute('data-ir'), 10);
                    render();
                    window.scrollTo(0, 0);
                });
                // Etapa 5B-3: un redibujo entre presionar y soltar haría perder ese clic.
                // En pantallas táctiles el navegador simula mousedown y clic después de soltar el dedo.
                var alPresionar = function () { punteroPresionado = true; };
                cont.addEventListener('pointerdown', alPresionar, true);
                cont.addEventListener('mousedown', alPresionar, true);
                window.addEventListener('pointerup', alSoltarPuntero, true);
                window.addEventListener('pointercancel', alSoltarPuntero, true);
                window.addEventListener('mouseup', alSoltarPuntero, true);
                render();
                mostrarConexion();
                window.addEventListener('online', alRecuperarConexion);
                window.addEventListener('offline', mostrarConexion);
                // Solo se envía al cargar si quedó algo pendiente: si no, se
                // sobrescribirían cambios hechos desde otro dispositivo.
                if (sucio || envioFinalPendiente) { intentarSync(envioFinalPendiente); }
            })
            .catch(function (err) {
                console.error(err);
                if (err && (err.codigo === 'sin-sesion' || err.codigo === 'sin-consentimiento')) {
                    cont.innerHTML = '<div class="tarjeta"><p class="errores" data-sin-llave>' + (err.codigo === 'sin-sesion'
                        ? 'Tu sesión no está iniciada en este dispositivo. Inicia sesión con conexión a internet ' +
                          'para ver y enviar tus respuestas; las que hayas dejado guardadas siguen protegidas aquí.'
                        : 'Necesitas aceptar el consentimiento informado para continuar.') +
                        '</p><p class="enlaces"><a href="/">Ir al inicio</a></p></div>';
                    return;
                }
                cont.innerHTML = '<div class="tarjeta"><p class="errores">' +
                    (err && err.message === 'sin-datos-paciente'
                        ? 'No se pudieron cargar las respuestas de la paciente. Necesitas conexión ' +
                          'a internet para abrir su encuesta la primera vez.'
                        : 'No se pudo cargar la encuesta. Necesitas conexión a internet al menos ' +
                          'la primera vez.') + '</p></div>';
            });
    }

    // ---------- Fase 29: precarga de la ronda en curso desde el servidor ----------
    // Así la encuesta se abre con lo ya guardado (por la usuaria o por el
    // personal de salud, desde cualquier dispositivo) y escribe en las mismas filas.
    function traerRondaActual() {
        if (!navigator.onLine || (MODO_PROF && !pacienteId)) { return Promise.resolve(); }
        var url = URL_RONDA + (MODO_PROF ? '?paciente=' + pacienteId : '');
        return fetch(url, { credentials: 'same-origin', headers: { 'X-Segundo-Plano': '1' } })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (srv) { if (srv) { return reconciliar(srv); } })
            .catch(function () { /* sin conexión: se sigue con lo local */ });
    }

    function reconciliar(srv) {
        if (!MODO_PROF) {
            disponibleDesde = srv.disponible_desde || null;
            idbSet('disponible_desde', disponibleDesde);
        }
        if (!srv.identificacion) { return; }  // la usuaria aún no tiene ficha
        identBloqueada = MODO_PROF && !!srv.identificacion.bloqueada;

        // Se cerró una ronda desde otro dispositivo (p. ej. la finalizó el
        // profesional): lo local pertenece a la ronda anterior.
        var cambioDeRonda = ronda !== null && srv.ronda_actual > ronda;
        if (cambioDeRonda) {
            // Fase 40B-2: lo que no se alcanzó a enviar no se descarta: se aparta antes.
            if (sucio || envioFinalPendiente) { archivarPendientes('ronda_cerrada_en_otro_lugar'); }
            iniciarRondaNueva();
            sucio = false;
            envioFinalPendiente = false;  // esa ronda ya quedó cerrada en el servidor
            idbSet('sucio', false);
            idbSet('pendiente_envio', false);
            idbSet('envio_final', false);
        }
        // Fase 40B-2: ceros de un MRS anterior a la 40B-2 que hay que confirmar. Si el
        // dispositivo los tenía guardados como respuesta y la persona no los eligió en
        // esta ronda, se quitan: pudieron ser el valor por defecto antiguo.
        mrsPorConfirmar = srv.mrs_por_confirmar || [];
        if (respuestas.mrs) {
            mrsPorConfirmar.forEach(function (item) {
                if (!confirmadosMrs[item] && String(respuestas.mrs[item]) === '0') { delete respuestas.mrs[item]; }
            });
        }
        var reemplazar = !sucio;  // sin cambios pendientes, manda el servidor
        if (reemplazar) { sinConfirmar = {}; idbSet('sin_confirmar', sinConfirmar); }
        adoptarVersion('identificacion', srv.identificacion, reemplazar);

        if (reemplazar || identBloqueada) {
            respuestas.identificacion = Object.assign({}, srv.identificacion.datos);
        }
        if (srv.identificacion.uuid_local) { uuids.identificacion = srv.identificacion.uuid_local; }
        bienvenidaOk = true;  // la ficha ya existe: la edad ya se validó

        esquema.secciones.forEach(function (s) {
            if (s.tipo === 'identificacion') { return; }
            var bloque = srv.secciones[claveSync(s)];
            if (reemplazar) {
                var datos = {};
                if (bloque) {
                    s.preguntas.forEach(function (p) {
                        if (bloque.datos[p.nombre] !== undefined) { datos[p.nombre] = bloque.datos[p.nombre]; }
                    });
                }
                respuestas[s.tipo] = datos;
            }
            if (bloque) { uuids[claveSync(s)] = bloque.uuid_local; }
            adoptarVersion(claveSync(s), bloque, reemplazar);
        });
        asegurarUuids();
        ronda = srv.ronda_actual;
        return Promise.all([
            idbSet('versiones', versiones),
            idbSet('respuestas', respuestas), idbSet('uuids', uuids),
            idbSet('bienvenida', true), idbSet('ronda', ronda),
        ]);
    }

    // Con cambios pendientes se conserva la versión sobre la que se hicieron: así se detecta
    // si el servidor cambió entretanto. Si no se conoce, se asume que no había nada.
    function adoptarVersion(clave, bloque, reemplazar) {
        if (reemplazar) { versiones[clave] = (bloque && bloque.version) || null; }
        else if (versiones[clave] === undefined) { versiones[clave] = null; }
    }

    function traerEsquema() {
        return fetch(URL_ESQUEMA, { headers: { 'Accept': 'application/json', 'X-Segundo-Plano': '1' } })
            .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
            .then(function (data) { esquema = data; return idbSet('esquema', data); })
            .catch(function () { /* sin conexión: se usa el esquema de IndexedDB si existe */ });
    }

    // Clave con la que se sincroniza una sección. Las secciones que comparten
    // `grupo` (las dos pantallas del MRS) van a un mismo registro.
    function claveSync(s) { return s.grupo || s.tipo; }

    function asegurarUuids() {
        var cambio = false;
        esquema.secciones.forEach(function (s) {
            var k = claveSync(s);
            if (!uuids[k]) { uuids[k] = crearUuid(); cambio = true; }
        });
        if (cambio) { idbSet('uuids', uuids); }
    }
    function crearUuid() {
        if (window.crypto && crypto.randomUUID) { return crypto.randomUUID(); }
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0;
            return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
        });
    }

    // ---------- Motor condicional (local, sin servidor) ----------

    // Meses entre una fecha escrita como texto libre y hoy. Réplica de
    // `meses_desde_texto_fecha` del servidor: acepta AAAA, AAAA-MM, MM/AAAA y
    // fecha completa; si solo hay año asume julio. null si no se puede leer.
    function mesesDesdeTexto(texto) {
        var txt = String(texto == null ? '' : texto).trim();
        if (!txt) { return null; }
        var anio = null, mes = null, m;
        if ((m = /^(\d{4})$/.exec(txt))) { anio = +m[1]; mes = 7; }
        else if ((m = /^(\d{4})[-/](\d{1,2})$/.exec(txt))) { anio = +m[1]; mes = +m[2]; }
        else if ((m = /^(\d{1,2})[-/](\d{4})$/.exec(txt))) { mes = +m[1]; anio = +m[2]; }
        else if ((m = /^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/.exec(txt))) { anio = +m[1]; mes = +m[2]; }
        else if ((m = /^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/.exec(txt))) { mes = +m[2]; anio = +m[3]; }
        if (anio === null || mes === null || mes < 1 || mes > 12) { return null; }
        var hoy = new Date();
        return (hoy.getFullYear() - anio) * 12 + (hoy.getMonth() + 1 - mes);
    }

    function listaContiene(valor, item) {
        return String(valor == null ? '' : valor).split(',')
            .map(function (s) { return s.trim(); })
            .indexOf(String(item)) !== -1;
    }

    function condicionCumplida(regla, datos) {
        if (!regla) { return true; }
        var actual = datos ? datos[regla.campo] : undefined;
        switch (regla.operador || 'igual') {
            case 'meses_desde_lt':
                var meses = mesesDesdeTexto(actual);
                return meses === null || meses < regla.valor;  // fecha ilegible: se muestra
            case 'contiene':
                return listaContiene(actual, regla.valor);
            default:
                return String(actual) === String(regla.valor);
        }
    }
    function seccionesAplicables() {
        return esquema.secciones.filter(function (s) {
            if (!s.mostrar_si) { return true; }
            return condicionCumplida(
                { campo: s.mostrar_si.campo, valor: s.mostrar_si.valor },
                respuestas[s.mostrar_si.seccion] || {}
            );
        });
    }
    // Ocultar en cadena: una pregunta se muestra si se cumple su regla Y, cuando
    // su disparador es otra pregunta de la misma sección, esa pregunta también
    // se muestra (ej. previsión ≠ Fonasa oculta "¿Ha consultado…?" y con ella
    // la evaluación de la atención, aunque antes se hubiera respondido "Sí").
    function preguntasVisibles(seccion) {
        var datos = respuestas[seccion.tipo] || {};
        var porNombre = {};
        seccion.preguntas.forEach(function (p) { porNombre[p.nombre] = p; });
        var memo = {};

        function visible(p) {
            if (memo[p.nombre] !== undefined) { return memo[p.nombre]; }
            memo[p.nombre] = true;  // corta ciclos accidentales en las reglas
            var ok = condicionCumplida(p.mostrar_si, datos);
            var madre = p.mostrar_si && porNombre[p.mostrar_si.campo];
            if (ok && madre) { ok = visible(madre); }
            memo[p.nombre] = ok;
            return ok;
        }
        return seccion.preguntas.filter(visible);
    }

    // Respuestas marcadas de antemano (ej. género Femenino): se guardan como
    // respuesta real solo si la pregunta todavía no tiene valor.
    function aplicarValoresIniciales(seccion) {
        var datos = respuestas[seccion.tipo] || {};
        var cambio = false;
        seccion.preguntas.forEach(function (p) {
            if (p.inicial === null || p.inicial === undefined) { return; }
            if (datos[p.nombre] === undefined || datos[p.nombre] === null || datos[p.nombre] === '') {
                datos[p.nombre] = p.inicial;
                cambio = true;
            }
        });
        if (cambio) {
            respuestas[seccion.tipo] = datos;
            idbSet('respuestas', respuestas);
        }
    }

    // ---------- Completitud ----------
    function seccionCompleta(seccion) {
        var datos = respuestas[seccion.tipo] || {};
        return preguntasVisibles(seccion).every(function (p) {
            if (!p.obligatoria) { return true; }
            var v = datos[p.nombre];
            return v !== undefined && v !== null && v !== '';
        });
    }

    // ---------- Pantalla de bienvenida: definiciones + filtro de edad ----------
    function edadDesde(iso) {
        if (!iso) { return null; }
        var d = new Date(iso + 'T00:00:00');
        if (isNaN(d.getTime())) { return null; }
        var hoy = new Date();
        var e = hoy.getFullYear() - d.getFullYear();
        if (hoy.getMonth() < d.getMonth() ||
            (hoy.getMonth() === d.getMonth() && hoy.getDate() < d.getDate())) { e--; }
        return e;
    }

    function renderBienvenida() {
        var defs = esquema.definiciones || [];
        var edadMin = esquema.edad_minima || 40;
        var edadMax = esquema.edad_maxima || 65;
        var rango = edadMin + ' a ' + edadMax + ' años';
        var excepciones = esquema.excepciones_edad || [];
        var fn = (respuestas.identificacion || {}).fecha_nacimiento || '';

        var html = '<div class="tarjeta bienvenida">';
        html += '<h1>Antes de empezar</h1>';
        if (defs.length) {
            html += '<div class="definiciones">';
            defs.forEach(function (d) {
                html += '<div class="definicion"><h2>' + esc(d.termino) + '</h2><p>' +
                    esc(d.texto) + '</p></div>';
            });
            html += '</div>';
        }
        html += '<div class="gate"><p>Esta encuesta está dirigida a personas de <strong>' +
            rango + '</strong>. ' + (MODO_PROF ? 'Ingresa la fecha de nacimiento de la paciente'
                : 'Ingresa tu fecha de nacimiento') + ' para continuar:</p>';
        html += '<label for="g_fn">Fecha de nacimiento</label>';
        html += '<input id="g_fn" type="date" value="' + esc(fn) + '">';
        html += '<div id="g_excepcion" hidden>' +
            '<p>Esta encuesta está dirigida a personas de ' + rango + '. Si ' +
            'ninguna de estas situaciones aplica en tu caso, no puedes continuar. Si alguna ' +
            'sí aplica, selecciónala para seguir:</p>';
        excepciones.forEach(function (op, i) {
            html += '<label class="opcion-excepcion"><input type="radio" name="g_exc" value="' +
                esc(op.valor) + '"> ' + esc(op.texto) + '</label>';
        });
        html += '<label class="opcion-excepcion"><input type="radio" name="g_exc" value="" checked> ' +
            'Ninguna de las anteriores</label></div>';
        html += '<p id="g_error" class="errores" hidden></p>';
        html += '<button type="button" id="g_ok">Comenzar</button></div></div>';
        cont.innerHTML = html;

        var input = document.getElementById('g_fn');
        var bloqueExcepcion = document.getElementById('g_excepcion');
        var err = document.getElementById('g_error');
        // Muestra el mensaje y lo lleva a la vista: si el texto no cambia entre
        // dos clics, sin esto parece que el botón "no hace nada".
        function mostrarError(texto) {
            err.textContent = texto;
            err.hidden = false;
            if (err.scrollIntoView) { err.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
        }
        input.addEventListener('input', function () {
            err.hidden = true;
            bloqueExcepcion.hidden = true;
        });
        cont.querySelectorAll('input[name="g_exc"]').forEach(function (radio) {
            radio.addEventListener('change', function () { err.hidden = true; });
        });
        document.getElementById('g_ok').addEventListener('click', function () {
            var edad = edadDesde(input.value);
            if (edad === null) {
                mostrarError('Ingresa tu fecha de nacimiento.'); return;
            }
            if (!respuestas.identificacion) { respuestas.identificacion = {}; }
            if (edad > edadMax) {
                bloqueExcepcion.hidden = true;
                mostrarError('No puedes continuar: esta encuesta está dirigida a personas de ' +
                    rango + '. Gracias por tu interés en participar.');
                return;
            }
            if (edad < edadMin) {
                var excepcionMarcada = cont.querySelector('input[name="g_exc"]:checked');
                var valorExcepcion = excepcionMarcada ? excepcionMarcada.value : '';
                if (!valorExcepcion) {
                    if (bloqueExcepcion.hidden) {
                        // Primer intento: ofrecer las excepciones.
                        bloqueExcepcion.hidden = false;
                        mostrarError('Esta encuesta está dirigida a personas de ' + rango +
                            '. Si alguna de las situaciones de arriba aplica en tu caso, ' +
                            'selecciónala y presiona Comenzar.');
                    } else {
                        // Ya vio las excepciones y eligió "Ninguna": rechazo definitivo.
                        mostrarError('No puedes continuar: esta encuesta está dirigida a ' +
                            'personas de ' + rango + ', salvo menopausia quirúrgica o ausencia ' +
                            'prolongada de menstruación. Gracias por tu interés en participar.');
                    }
                    return;
                }
                respuestas.identificacion.excepcion_edad = valorExcepcion;
            } else {
                // Dentro del rango la excepción no aplica (evita arrastrar una
                // marcada antes con otra fecha).
                respuestas.identificacion.excepcion_edad = '';
            }
            respuestas.identificacion.fecha_nacimiento = input.value;
            idbSet('respuestas', respuestas);
            bienvenidaOk = true;
            idbSet('bienvenida', true);
            indice = 0;
            render();
        });
    }

    // ---------- Render ----------
    function render() {
        if (!bienvenidaOk) { renderBienvenida(); return; }

        var secs = seccionesAplicables();
        indice = Math.max(0, Math.min(indice, secs.length - 1));
        var seccion = secs[indice];
        aplicarValoresIniciales(seccion);

        firmaVisible = firmaDeVisibles();
        var html = barraProgreso(secs);
        html += '<div class="tarjeta seccion">';
        html += '<p class="paso">Sección ' + (indice + 1) + ' de ' + secs.length + '</p>';
        html += '<h1>' + esc(seccion.titulo) + '</h1>';
        if (seccion.descripcion) {
            html += '<p class="seccion-intro">' + esc(seccion.descripcion) + '</p>';
        }
        if (seccion.aviso) {
            html += '<p class="seccion-aviso">' + esc(seccion.aviso) + '</p>';
        }
        if (esquema.mensaje_omitir) {
            html += '<p class="seccion-omitir">' + esc(esquema.mensaje_omitir) + '</p>';
        }
        if (seccion.tipo === 'identificacion' && preguntarIdentificacion) {
            html += '<div class="confirmar-datos">' +
                '<p>Ya tenemos tus datos de identificación. ¿Desea modificar algún dato?</p>' +
                '<div class="nav">' +
                '<button type="button" class="boton-guardar" data-nav="ident-si">Sí, modificar</button>' +
                '<button type="button" data-nav="ident-no">No, continuar</button>' +
                '</div></div>';
            html += navegacionSecciones(secs) + '</div>';
            cont.innerHTML = html;
            conectarEventos(seccion);
            return;
        }
        if (seccion.tipo === 'mrs') {
            html += avisoMrsPorConfirmar();
            html += burbujaPuntajeMrs(seccion);
        }
        if (seccion.tipo === 'identificacion' && identBloqueada) {
            html += renderIdentificacionBloqueada(seccion);
        } else {
            preguntasVisibles(seccion).forEach(function (p) { html += renderPregunta(seccion, p); });
        }

        html += '<div class="nav">';
        if (indice > 0) {
            html += '<button type="button" data-nav="prev">← ' + esc(tituloCorto(secs[indice - 1])) +
                '</button>';
        }
        html += '<button type="button" class="boton-guardar" data-nav="guardar">Guardar cambios</button>';
        if (indice < secs.length - 1) {
            html += '<button type="button" data-nav="next">' + esc(tituloCorto(secs[indice + 1])) +
                ' →</button>';
        } else {
            html += '<button type="button" data-nav="finalizar">Finalizar</button>';
        }
        html += '</div>';
        html += navegacionSecciones(secs) + '</div>';

        cont.innerHTML = html;
        conectarEventos(seccion);
    }

    function barraProgreso(secs) {
        var completas = secs.filter(seccionCompleta).length;
        var pct = secs.length ? Math.round(completas / secs.length * 100) : 0;
        var tramo = tramoProgreso(pct);
        return '<div class="progreso-bloque">' +
            '<div class="progreso" role="progressbar" aria-valuemin="0" aria-valuemax="100" ' +
            'aria-valuenow="' + pct + '">' +
            '<div class="progreso-barra progreso-' + tramo.clase + '" style="width:' + pct + '%"></div>' +
            '<span class="progreso-texto">' + completas + ' de ' + secs.length +
            ' secciones completas</span></div>' +
            '<p class="progreso-mensaje">' + esc(tramo.msg) + '</p></div>';
    }

    // Fase 29: la paciente se registró ella misma -> el profesional solo ve sus datos.
    function renderIdentificacionBloqueada(seccion) {
        var datos = respuestas[seccion.tipo] || {};
        var html = '<p class="seccion-aviso-bloqueo">La paciente se registró ella misma: ' +
            'solo ella puede modificar estos datos.</p><dl class="resumen-datos">';
        preguntasVisibles(seccion).forEach(function (p) {
            var v = datos[p.nombre];
            if (v === undefined || v === null || v === '') { return; }
            var texto = String(v);
            (p.opciones || []).forEach(function (op) {
                if (String(op.valor) === String(v)) { texto = op.texto; }
            });
            html += '<dt>' + esc(p.texto) + '</dt><dd>' + esc(texto) + '</dd>';
        });
        return html + '</dl>';
    }

    // Fase 27: botones para saltar a cualquier sección, al final de cada una.
    function navegacionSecciones(secs) {
        var ultima = indice === secs.length - 1;
        var html = '<nav class="secciones-nav" aria-label="Secciones de la encuesta">' +
            '<p class="secciones-nav-titulo">' +
            (ultima ? 'Revisa tus secciones antes de finalizar:' : 'Ir a otra sección:') + '</p>' +
            '<div class="secciones-botones">';
        secs.forEach(function (s, i) {
            var completa = seccionCompleta(s);
            var clase = 'ir-seccion ' + (completa ? 'completa' : 'pendiente');
            if (i === indice) {
                html += '<button type="button" class="' + clase + ' actual" disabled aria-current="step">' +
                    esc(tituloCorto(s)) + '</button>';
            } else {
                html += '<button type="button" class="' + clase + '" data-ir="' + i + '">' +
                    (completa ? '✓ ' : '') + esc(tituloCorto(s)) +
                    (completa ? '' : ' <small>pendiente</small>') + '</button>';
            }
        });
        return html + '</div></nav>';
    }

    function renderPregunta(seccion, p) {
        var datos = respuestas[seccion.tipo] || {};
        var v = datos[p.nombre];
        var id = 'c_' + seccion.tipo + '_' + p.nombre;
        var req = p.obligatoria ? ' <span class="req">*</span>' : '';
        var out = '<div class="pregunta' + (p.escala === 'mrs' ? ' pregunta-mrs' : '') +
            '" data-campo="' + p.nombre + '">';
        out += '<label for="' + id + '">' + esc(p.texto) + req + '</label>';
        if (p.nota) { out += '<p class="pregunta-nota">' + esc(p.nota) + '</p>'; }

        if (p.escala === 'mrs') {
            out += renderEscalaCalor(id, p, v);
        } else if (p.depende_de) {
            out += renderDependiente(seccion, p, id, v);
        } else if (p.chips) {
            out += renderChips(id, p, v);
        } else if (p.escala_horizontal) {
            out += renderEscalaHorizontal(id, p, v);
        } else if (p.tipo_campo === 'multiseleccion') {
            var marcados = String(v || '').split(',').map(function (s) { return s.trim(); })
                .filter(Boolean);
            (p.opciones || []).forEach(function (op) {
                var val = String(op.valor);
                var checked = marcados.indexOf(val) !== -1 ? ' checked' : '';
                out += '<label class="opcion"><input type="checkbox" name="' + id + '" value="' +
                    esc(val) + '"' + checked + '> ' + esc(op.texto) + '</label>';
            });
        } else if (p.tipo_campo === 'opciones' || p.tipo_campo === 'booleano') {
            var ops = p.opciones || [];
            if (p.escala !== 'mrs' && ops.length > 7) {
                out += '<select id="' + id + '"><option value="">—</option>';
                ops.forEach(function (op) {
                    var val = String(op.valor);
                    out += '<option value="' + esc(val) + '"' +
                        (String(v) === val ? ' selected' : '') + '>' + esc(op.texto) + '</option>';
                });
                out += '</select>';
            } else {
                ops.forEach(function (op) {
                    var val = String(op.valor);
                    var checked = String(v) === val ? ' checked' : '';
                    out += '<label class="opcion"><input type="radio" name="' + id + '" value="' +
                        esc(val) + '"' + checked + '> ' + esc(op.texto) + '</label>';
                });
            }
        } else if (p.tipo_campo === 'textarea') {
            out += '<textarea id="' + id + '" rows="3">' + esc(v || '') + '</textarea>';
        } else {
            var tipo = p.tipo_campo === 'numero' ? 'number'
                : (p.tipo_campo === 'date' ? 'date' : 'text');
            var extra = p.tipo_campo === 'numero' ? ' min="0"' : '';
            out += '<input id="' + id + '" type="' + tipo + '"' + extra +
                ' value="' + esc(v == null ? '' : v) + '">';
        }
        out += '</div>';
        return out;
    }

    // Escala de calor MRS (Sección 4.1): 5 niveles verde→rojo con caritas.
    function renderEscalaCalor(id, p, v) {
        var EMOJI = ['😀', '🙂', '😐', '😟', '😣'];
        var niveles = esquema.mrs_niveles || {};
        var out = '<div class="escala-calor">';
        (p.opciones || []).forEach(function (op) {
            var val = String(op.valor);
            var sel = String(v) === val;
            out += '<label class="calor calor-' + esc(val) + (sel ? ' sel' : '') + '">' +
                '<input type="radio" name="' + id + '" value="' + esc(val) + '"' +
                (sel ? ' checked' : '') + '>' +
                '<span class="calor-emoji">' + EMOJI[Number(op.valor)] + '</span>' +
                '<span class="calor-texto">' + esc(op.texto) + '</span></label>';
        });
        out += '</div>';
        var desc = (v !== undefined && v !== '' && niveles[String(v)])
            ? niveles[String(v)]
            : 'Elige la opción según cuánto te molesta este síntoma.';
        out += '<p class="calor-desc">' + esc(desc) + '</p>';
        return out;
    }

    // Escala horizontal con gradiente de color (regla de la profesora: toda
    // escala, no solo el MRS). Sin caritas: las caritas son exclusivas del MRS.
    // `polaridad === 'inversa'` invierte el gradiente (extremo alto = verde).
    function colorEscala(paso, inversa) {
        var t = inversa ? 1 - paso : paso;      // 0 = verde, 1 = rojo
        var hue = Math.round(120 * (1 - t));    // 120° verde -> 0° rojo
        return 'hsl(' + hue + ', 62%, 44%)';
    }

    function renderEscalaHorizontal(id, p, v) {
        var ops = p.opciones || [];
        var n = ops.length;
        var inversa = p.polaridad === 'inversa';
        var out = '<div class="escala-h">';
        ops.forEach(function (op, i) {
            var val = String(op.valor);
            var sel = String(v) === val;
            var color = colorEscala(n > 1 ? i / (n - 1) : 0, inversa);
            out += '<label class="escala-h-op' + (sel ? ' sel' : '') +
                '" style="background:' + color + '">' +
                '<input type="radio" name="' + id + '" value="' + esc(val) + '"' +
                (sel ? ' checked' : '') + '>' +
                '<span class="escala-h-txt">' + esc(op.texto) + '</span></label>';
        });
        return out + '</div>';
    }

    // Selección única categórica, horizontal, en "chips" cuadrados SIN color
    // (regla de la profesora: no es una escala ordenada, ej. "¿Quién prepara
    // sus comidas?"). Se resalta con el morado del tema, no con el gradiente.
    function renderChips(id, p, v) {
        var out = '<div class="chips">';
        (p.opciones || []).forEach(function (op) {
            var val = String(op.valor);
            var sel = String(v) === val;
            out += '<label class="chip' + (sel ? ' sel' : '') + '">' +
                '<input type="radio" name="' + id + '" value="' + esc(val) + '"' +
                (sel ? ' checked' : '') + '>' +
                '<span>' + esc(op.texto) + '</span></label>';
        });
        return out + '</div>';
    }

    // Campo cuyas opciones dependen del valor de otro campo (ej. comuna ← región).
    function renderDependiente(seccion, p, id, v) {
        var datos = respuestas[seccion.tipo] || {};
        var claveOrigen = datos[p.depende_de];
        var lista = (esquema.comunas_por_region || {})[claveOrigen];

        if (!claveOrigen) {
            return '<select id="' + id + '" disabled><option>Elige primero la región</option></select>';
        }
        if (!lista || !lista.length) {
            // Región sin lista (ej. "Fuera de Chile"): texto libre.
            return '<input id="' + id + '" type="text" value="' + esc(v || '') + '">';
        }
        var out = '<select id="' + id + '"><option value="">—</option>';
        lista.forEach(function (nombre) {
            out += '<option value="' + esc(nombre) + '"' + (v === nombre ? ' selected' : '') +
                '>' + esc(nombre) + '</option>';
        });
        return out + '</select>';
    }

    function conectarEventos(seccion) {
        cont.querySelectorAll('[data-nav]').forEach(function (b) {
            b.addEventListener('click', function () {
                var a = b.getAttribute('data-nav');
                if (a === 'prev') { indice--; render(); }
                else if (a === 'next') { indice++; render(); }
                else if (a === 'guardar') { guardarCambios(); }
                else if (a === 'ident-si') { preguntarIdentificacion = false; render(); }
                else if (a === 'ident-no') { preguntarIdentificacion = false; indice++; render(); }
                else if (a === 'finalizar') { finalizar(); }
            });
        });
        cont.querySelectorAll('.pregunta').forEach(function (div) {
            var campo = div.getAttribute('data-campo');
            var manejar = function (e) { capturar(seccion, campo, e.target, e.type); };
            div.addEventListener('input', manejar);
            div.addEventListener('change', manejar);
        });
    }

    function capturar(seccion, campo, el, tipoEvento) {
        if (!respuestas[seccion.tipo]) { respuestas[seccion.tipo] = {}; }
        var valor = el.value;
        if (el.type === 'radio') {
            if (valor === 'true') { valor = true; }
            else if (valor === 'false') { valor = false; }
        } else if (el.type === 'checkbox') {
            // Selección múltiple: se guarda como lista separada por comas.
            var marcados = [];
            var grupo = el.closest('.pregunta');
            if (grupo) {
                grupo.querySelectorAll('input[type="checkbox"]').forEach(function (chk) {
                    if (chk.checked) { marcados.push(chk.value); }
                });
            }
            valor = marcados.join(', ');
        }
        respuestas[seccion.tipo][campo] = valor;
        generacion++;
        sucio = true;
        idbSet('sucio', true);  // hay datos locales sin enviar al servidor
        if (esEscalaCalor(seccion, campo)) {
            // Fase 40B-2: la persona eligió este ítem MRS (incluido un 0 = «Ninguna»).
            confirmadosMrs[campo] = true;
            idbSet('mrs_confirmados', confirmadosMrs);
        }

        // Si de este campo depende otro (ej. comuna ← región), limpia el
        // dependiente cuando deja de ser válido para el nuevo valor.
        seccion.preguntas.forEach(function (p) {
            if (p.depende_de !== campo) { return; }
            var lista = (esquema.comunas_por_region || {})[valor] || [];
            var actual = respuestas[seccion.tipo][p.nombre];
            if (actual && lista.length && lista.indexOf(actual) === -1) {
                delete respuestas[seccion.tipo][p.nombre];
            }
        });

        idbSet('respuestas', respuestas);

        // En campos de texto libre no se re-renderiza en cada tecla (perdería el
        // foco): se espera al evento 'change' (al salir del campo).
        var esTextoLibre = (el.tagName === 'INPUT' &&
            ['text', 'number', 'date'].indexOf(el.type) !== -1) || el.tagName === 'TEXTAREA';
        if (esTextoLibre && tipoEvento === 'input') {
            actualizarProgreso();
            return;
        }

        // Etapa 5B-3: una condición solo obliga a redibujar si cambia lo que se ve.
        var cambiaLoVisible = afectaCondicionales(seccion, campo) && firmaDeVisibles() !== firmaVisible;
        redibujar(cambiaLoVisible || afectaDependencias(seccion, campo) ||
            esEscalaCalor(seccion, campo) || esEscalaHorizontal(seccion, campo));
    }

    function firmaDeVisibles() {
        return seccionesAplicables().map(function (s) {
            return s.tipo + ':' + preguntasVisibles(s).map(function (p) { return p.nombre; }).join(',');
        }).join(';');
    }

    function redibujar(completo) {
        if (punteroPresionado) {
            trasPuntero = (completo || trasPuntero === 'completo') ? 'completo' : 'progreso';
            return;
        }
        if (completo) { render(); } else { actualizarProgreso(); }
    }

    function alSoltarPuntero() {
        punteroPresionado = false;
        if (!trasPuntero) { return; }
        var completo = trasPuntero === 'completo';
        trasPuntero = null;
        // El clic llega justo después de soltar: se redibuja cuando ya se haya registrado.
        setTimeout(function () { if (!conflictoVersion) { redibujar(completo); } }, 0);
    }

    // Burbuja con la suma del MRS (11 ítems, 0 a 44). Se redibuja con cada
    // respuesta porque las preguntas MRS ya llaman a render().
    // Fase 40B-3: mientras se responde la ronda está abierta, así que la suma nunca es un
    // resultado definitivo: es parcial (faltan ítems) o provisional (los 11 respondidos).
    // No se muestra categoría de severidad: los cortes no están validados para la plataforma.
    function burbujaPuntajeMrs(seccion) {
        var datos = respuestas[seccion.tipo] || {};
        var items = seccion.preguntas.filter(function (p) { return p.escala === 'mrs'; });
        var total = 0, respondidas = 0;
        items.forEach(function (p) {
            var v = datos[p.nombre];
            if (v !== undefined && v !== null && v !== '') {
                total += Number(v);
                respondidas++;
            }
        });
        var completa = respondidas === items.length;
        var titulo = (completa ? 'Suma provisional: ' : 'Suma parcial: ') + total + ' / ' + (items.length * 4);
        var detalle = completa
            ? 'Se confirma al finalizar la encuesta.'
            : respondidas + ' de ' + items.length + ' preguntas respondidas.';
        return '<div class="burbuja-mrs" role="status" aria-live="polite"' +
            ' data-estado="' + (completa ? 'provisional' : 'parcial') + '">' +
            '<strong>' + esc(titulo) + '</strong><span>' + esc(detalle) + '</span></div>';
    }

    // Fase 40B-2: aviso para los ceros de un MRS guardado antes de la corrección.
    function avisoMrsPorConfirmar() {
        var pendientes = mrsPorConfirmar.filter(function (item) {
            var v = (respuestas.mrs || {})[item];
            return !confirmadosMrs[item] && (v === undefined || v === null || v === '');
        });
        if (!pendientes.length) { return ''; }
        return '<p class="seccion-aviso">Antes de una actualización de la encuesta, algunas preguntas sin ' +
            'responder pudieron guardarse como «Ninguna». Por favor, vuelve a elegir tu respuesta en las ' +
            pendientes.length + (pendientes.length === 1 ? ' pregunta' : ' preguntas') +
            ' que aparecen sin marcar.</p>';
    }

    function esEscalaCalor(seccion, campo) {
        return seccion.preguntas.some(function (p) {
            return p.nombre === campo && p.escala === 'mrs';
        });
    }

    function esEscalaHorizontal(seccion, campo) {
        return seccion.preguntas.some(function (p) {
            return p.nombre === campo && p.escala_horizontal;
        });
    }

    function afectaCondicionales(seccion, campo) {
        var disparaPregunta = seccion.preguntas.some(function (p) {
            return p.mostrar_si && p.mostrar_si.campo === campo;
        });
        var disparaSeccion = esquema.secciones.some(function (s) {
            return s.mostrar_si && s.mostrar_si.seccion === seccion.tipo &&
                s.mostrar_si.campo === campo;
        });
        return disparaPregunta || disparaSeccion;
    }

    function afectaDependencias(seccion, campo) {
        return seccion.preguntas.some(function (p) { return p.depende_de === campo; });
    }

    function actualizarProgreso() {
        var secs = seccionesAplicables();
        var barra = cont.querySelector('.progreso-bloque');
        if (barra) { barra.outerHTML = barraProgreso(secs); }
        var nav = cont.querySelector('.secciones-nav');
        if (nav) { nav.outerHTML = navegacionSecciones(secs); }
    }

    // ---------- Conexión / sincronización automática (Sección 5.1) ----------
    function estadoEl() { return document.getElementById('estado-sync'); }

    function mostrarConexion() {
        var el = estadoEl();
        if (!el) { return; }
        if (navigator.onLine) {
            el.hidden = true;
        } else {
            el.hidden = false;
            el.className = 'estado-sync offline';
            el.textContent = 'Sin conexión — tus respuestas se guardan en este dispositivo y ' +
                'se enviarán solas cuando vuelva internet.';
        }
    }

    function avisoSync(texto, clase) {
        var el = estadoEl();
        if (!el) { return; }
        el.hidden = false;
        el.className = 'estado-sync ' + (clase || '');
        el.textContent = texto;
        if (clase === 'ok') {
            setTimeout(function () { el.hidden = true; mostrarConexion(); }, 4000);
        }
    }

    function guardarCambios() {
        idbSet('respuestas', respuestas);
        avisoSync(navigator.onLine
            ? 'Cambios guardados. Sincronizando…'
            : 'Cambios guardados en este dispositivo.', 'ok');
        intentarSync(false);  // si hay conexión, sincroniza y muestra su propio aviso
    }

    function alRecuperarConexion() {
        mostrarConexion();
        intentarSync(envioFinalPendiente);
    }

    function finalizar() {
        var incompletas = seccionesAplicables().filter(function (s) {
            return !seccionCompleta(s);
        });
        if (incompletas.length) {
            alert('Faltan secciones por completar: ' +
                incompletas.map(function (s) { return s.titulo; }).join(', '));
            return;
        }
        envioFinalPendiente = true;
        idbSet('envio_final', true);
        if (!idCierre) {
            idCierre = crearUuid();
            idbSet('id_cierre', idCierre);
        }
        // Etapa 5B-3: lo que se cambiara durante el cierre ya no alcanzaría a la ronda que se cierra.
        cont.querySelectorAll('input, select, textarea, button').forEach(function (c) { c.disabled = true; });
        intentarSync(true);
    }

    function construirPayload(esFinal) {
        // Fase 40B-2: protocolo 2 (la ronda local; al finalizar, el id del cierre).
        var payload = { protocolo: PROTOCOLO, ronda: ronda, secciones: [] };
        // Fase 40 (P6): participación a la que pertenecen estas respuestas.
        if (!MODO_PROF && participacion) { payload.participacion = participacion; }
        if (esFinal) {
            payload.finalizar = true;
            if (!idCierre) { idCierre = crearUuid(); idbSet('id_cierre', idCierre); }
            payload.id_cierre = idCierre;
        }
        var bloques = {};   // clave de sync -> bloque (para fusionar grupos, p. ej. MRS)
        seccionesAplicables().forEach(function (s) {
            var datos = respuestas[s.tipo] || {};
            if (s.tipo === 'identificacion') {
                payload.identificacion = {
                    uuid_local: uuids['identificacion'],
                    datos: identBloqueada ? {} : datos,
                    version_base: versionBase('identificacion'),
                };
                agregarSinConfirmar(payload.identificacion, 'identificacion');
                if (MODO_PROF) {
                    if (pacienteId) { payload.identificacion.paciente_id = pacienteId; }
                    else { payload.identificacion.rut = rutNueva; }
                    if (participacionDatos) { payload.identificacion.participacion_paciente = participacionDatos; }
                }
                return;
            }
            var k = claveSync(s);
            if (!bloques[k]) {
                bloques[k] = { tipo: k, uuid_local: uuids[k], datos: {}, parcial: false, version_base: versionBase(k) };
                agregarSinConfirmar(bloques[k], k);
                payload.secciones.push(bloques[k]);
            }
            // Solo las preguntas visibles: las ocultas no se envían y el
            // servidor las deja vacías (ej. si cambió la previsión a Isapre,
            // se borran las respuestas que solo aplican con Fonasa).
            preguntasVisibles(s).forEach(function (p) {
                if (datos[p.nombre] !== undefined) { bloques[k].datos[p.nombre] = datos[p.nombre]; }
            });
            if (!seccionCompleta(s)) { bloques[k].parcial = true; }
        });
        if (bloques.mrs) {
            bloques.mrs.confirmados = Object.keys(confirmadosMrs).filter(function (c) {
                return bloques.mrs.datos[c] !== undefined;
            });
        }
        return payload;
    }

    function versionBase(clave) { return versiones[clave] === undefined ? null : versiones[clave]; }

    function agregarSinConfirmar(bloque, clave) {
        if (sinConfirmar[clave] && sinConfirmar[clave].length) { bloque.sin_confirmar = sinConfirmar[clave].slice(); }
    }

    // Antes de enviar se anota qué se envía: si la respuesta se pierde o la página se recarga,
    // el reintento le muestra al servidor que ese guardado era de este mismo dispositivo.
    function anotarEnvio(payload) {
        var bloques = payload.secciones.slice();
        if (payload.identificacion && Object.keys(payload.identificacion.datos || {}).length) {
            bloques.push({ tipo: 'identificacion', datos: payload.identificacion.datos });
        }
        bloques.forEach(function (b) {
            var lista = sinConfirmar[b.tipo] || [];
            var texto = JSON.stringify(b.datos);
            if (!lista.some(function (x) { return JSON.stringify(x) === texto; })) { lista = lista.concat([b.datos]); }
            sinConfirmar[b.tipo] = lista.slice(-MAX_SIN_CONFIRMAR);
        });
        return idbSet('sin_confirmar', sinConfirmar);
    }

    // Tras un "Finalizar" exitoso, la ronda queda sellada en el servidor
    // (Fase 13). Acá se limpia el estado local para que la próxima vez que se
    // abra la encuesta empiece una ronda nueva en blanco: se conservan los
    // datos de "Identificación" (perfil, no se repite por ronda) y se
    // regeneran los uuid_local de las demás secciones, así el servidor los
    // guarda como filas nuevas en vez de reescribir las de la ronda cerrada.
    function iniciarRondaNueva() {
        var identificacionGuardada = respuestas.identificacion;
        respuestas = identificacionGuardada ? { identificacion: identificacionGuardada } : {};
        idbSet('respuestas', respuestas);

        Object.keys(uuids).forEach(function (k) {
            if (k !== 'identificacion') { delete uuids[k]; }
        });
        asegurarUuids();

        // Fase 40B-2: lo confirmado y el id del cierre pertenecían a la ronda anterior.
        confirmadosMrs = {};
        mrsPorConfirmar = [];
        idCierre = null;
        idbSet('mrs_confirmados', confirmadosMrs);
        idbSet('id_cierre', null);

        // Etapa 5B-3: en la ronda nueva aún no hay nada guardado (la identificación continúa).
        var versionIdentificacion = versiones.identificacion;
        versiones = versionIdentificacion === undefined ? {} : { identificacion: versionIdentificacion };
        sinConfirmar = {};
        idbSet('versiones', versiones);
        idbSet('sin_confirmar', sinConfirmar);

        indice = 0;
    }

    // Sube al servidor lo que haya guardado localmente. `esFinal` = la usuaria
    // pulsó "Finalizar". Se puede llamar en cualquier momento (al recuperar
    // conexión, al cargar): si no hay identificación completa, no hace nada.
    // Etapa 5B-3: los envíos van de uno en uno; lo pedido durante uno sale al terminar este.
    function intentarSync(esFinal) {
        if (conflictoVersion) { return Promise.resolve(); }  // espera la decisión de la persona
        if (envioEnCurso) {
            otroEnvio = { final: !!esFinal || !!(otroEnvio && otroEnvio.final) };
            return envioEnCurso;
        }
        var alTerminar = function () {
            envioEnCurso = null;
            var siguiente = otroEnvio;
            otroEnvio = null;
            if (siguiente && (sucio || (siguiente.final && envioFinalPendiente))) {
                return intentarSync(siguiente.final && envioFinalPendiente);
            }
        };
        envioEnCurso = enviarAlServidor(esFinal).then(alTerminar, function (err) {
            console.error(err);
            return alTerminar();
        });
        return envioEnCurso;
    }

    function enviarAlServidor(esFinal) {
        var secs = seccionesAplicables();
        var ident = null;
        secs.forEach(function (s) { if (s.tipo === 'identificacion') { ident = s; } });

        if (!navigator.onLine) {
            if (esFinal) {
                mensajeFinal('Guardado en este dispositivo. Se enviará automáticamente ' +
                    'cuando haya conexión a internet.');
            }
            return Promise.resolve();
        }
        if (!ident || !seccionCompleta(ident)) {
            return Promise.resolve();  // aún no hay lo mínimo para sincronizar
        }

        var generacionEnviada = generacion;
        var payload = construirPayload(esFinal);
        return anotarEnvio(payload).then(function () {
            return fetch(URL_SYNC, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken(), 'X-Segundo-Plano': '1' },
                body: JSON.stringify(payload)
            });
        })
            .then(function (r) {
                // Si la respuesta no es JSON (p. ej. una página de error o de inicio de sesión),
                // r.json() falla y se cae al catch: todo queda pendiente en este dispositivo.
                return r.json().then(function (j) { return { ok: r.ok, status: r.status, cuerpo: j }; });
            })
            .then(function (res) {
                // Fase 40B-2: la ronda local ya no está abierta en el servidor (se cerró en otro
                // dispositivo o llegó tarde). No se escribió nada: se aparta lo local y se sigue.
                if (res.status === 409) {
                    otroEnvio = null;
                    if ((res.cuerpo || {}).codigo === 'version_desactualizada') {
                        idbSet('pendiente_envio', true);
                        mostrarConflictoVersion(res.cuerpo);
                        return;
                    }
                    return resolverConflicto(res.cuerpo || {});
                }
                if (res.status === 401) {
                    // Fase 40 E2: la sesión venció por inactividad. Nada se guardó; lo pendiente queda
                    // cifrado en este dispositivo y sesion.js cierra la sesión local.
                    idbSet('pendiente_envio', true);
                    avisarSesionVencida();
                    return;
                }
                if (res.status === 403) {
                    // Sin consentimiento vigente (40S-1): nada se guardó; todo sigue pendiente aquí.
                    idbSet('pendiente_envio', true);
                    var aviso = ((res.cuerpo && res.cuerpo.error) || 'No se pudieron enviar tus respuestas.') +
                        ' Tus respuestas siguen guardadas en este dispositivo.';
                    if (esFinal) { mensajeFinal(aviso, true); } else { avisoSync(aviso, 'error'); }
                    return;
                }
                adoptarRespuesta(res.cuerpo);
                var huboCambios = generacion !== generacionEnviada;  // se respondió durante el envío
                var cierre = res.cuerpo && res.cuerpo.cierre;
                if (res.ok && cierre && cierre.estado === 'rechazado') {
                    // Lo enviado quedó guardado como borrador; falta completar algo obligatorio.
                    sucio = !res.cuerpo.guardado || huboCambios;
                    idbSet('sucio', sucio);
                    idbSet('pendiente_envio', sucio);
                    envioFinalPendiente = false;
                    idbSet('envio_final', false);
                    idCierre = null;
                    idbSet('id_cierre', null);
                    mostrarFaltantes(cierre.faltantes || []);
                    return;
                }
                if (res.ok && res.cuerpo.ok) {
                    // Etapa 5B-3: lo respondido durante el envío sigue pendiente; no iba en este envío.
                    sucio = huboCambios && !esFinal;
                    idbSet('sucio', sucio);
                    idbSet('pendiente_envio', sucio);
                    if (esFinal) {
                        if (huboCambios) { archivarPendientes('cambios_durante_el_cierre'); }
                        envioFinalPendiente = false;
                        idbSet('envio_final', false);
                        iniciarRondaNueva();
                        ronda = res.cuerpo.ronda_actual;
                        idbSet('ronda', ronda);
                        if (MODO_PROF) {
                            mensajeFinal('¡Encuesta de la paciente enviada! La ronda quedó cerrada ' +
                                'y su ficha ya muestra estas respuestas.', false, false,
                                urlFicha || ('/profesional/paciente/' + pacienteId + '/'));
                        } else {
                            disponibleDesde = res.cuerpo.disponible_desde || null;
                            idbSet('disponible_desde', disponibleDesde);
                            mensajeFinal('¡Encuesta enviada! Gracias por participar. Puedes volver a ' +
                                'responderla más adelante para registrar cómo han cambiado tus síntomas.' +
                                (disponibleDesde ? ' ' + textoEspera() : ''),
                                false, true);
                        }
                    } else if (huboCambios) {
                        otroEnvio = otroEnvio || { final: false };
                        avisoSync('Guardando tus últimos cambios…');
                    } else {
                        avisoSync('Respuestas sincronizadas.', 'ok');
                    }
                } else {
                    console.warn(res.cuerpo);
                    idbSet('pendiente_envio', true);
                    if (esFinal) {
                        mensajeFinal('Algunas respuestas no se pudieron enviar. Quedaron ' +
                            'guardadas en este dispositivo.', true);
                    } else {
                        avisoSync('Hubo un problema al sincronizar. Tus respuestas están a salvo ' +
                            'en este dispositivo.', 'error');
                    }
                }
            })
            .catch(function (err) {
                console.error(err);
                idbSet('pendiente_envio', true);
                if (esFinal) {
                    mensajeFinal('Sin conexión al enviar. Se reintentará automáticamente.', true);
                } else {
                    avisoSync('No se pudo enviar. Tus respuestas siguen guardadas en este dispositivo ' +
                        'y se enviarán cuando vuelva la conexión.', 'error');
                }
            });
    }

    // Etapa 5B-3: esta página tiene una copia antigua. El servidor no escribió nada y aquí no se
    // borra nada; no se fusiona: decide la persona.
    function mostrarConflictoVersion(cuerpo) {
        conflictoVersion = cuerpo;
        var titulos = (cuerpo.secciones || []).map(function (clave) {
            var s = esquema.secciones.filter(function (x) { return claveSync(x) === clave; })[0];
            return esc(s ? tituloCorto(s) : clave);
        });
        cont.innerHTML = '<div class="tarjeta" data-conflicto-version>' +
            '<h2>Tus respuestas cambiaron en otro lugar</h2>' +
            '<p>Esta página tiene una copia anterior de tus respuestas, quizá porque usaste «Atrás» o ' +
            'tienes la encuesta abierta en otra pestaña o dispositivo. Para no borrar nada, ' +
            '<strong>no se guardó ningún cambio desde esta página</strong>.</p>' +
            (titulos.length ? '<p>Secciones afectadas: ' + titulos.join(', ') + '.</p>' : '') +
            '<p><button type="button" class="boton" data-conflicto="guardado">Ver lo último guardado</button></p>' +
            '<p class="ayuda">Recomendado. Los cambios hechos en esta página que no se guardaron se descartan.</p>' +
            '<p><button type="button" class="boton-secundario" data-conflicto="pagina">Guardar lo de esta página</button></p>' +
            '<p class="ayuda">Reemplaza lo guardado por lo que ves aquí. Las respuestas que esta página no tenga ' +
            'quedarán en blanco.</p></div>';
        cont.querySelectorAll('[data-conflicto]').forEach(function (b) {
            b.addEventListener('click', function () { decidirConflictoVersion(b.getAttribute('data-conflicto')); });
        });
    }

    function decidirConflictoVersion(decision) {
        var cuerpo = conflictoVersion;
        if (!cuerpo) { return Promise.resolve(); }
        conflictoVersion = null;
        sinConfirmar = {};
        if (decision === 'pagina') {
            Object.assign(versiones, cuerpo.versiones || {});
            sucio = true;
            render();
            return Promise.all([idbSet('versiones', versiones), idbSet('sin_confirmar', sinConfirmar)])
                .then(function () { return intentarSync(envioFinalPendiente); });
        }
        sucio = false;
        envioFinalPendiente = false;
        idCierre = null;
        versiones = {};
        return Promise.all([
            idbSet('sucio', false), idbSet('pendiente_envio', false), idbSet('envio_final', false),
            idbSet('id_cierre', null), idbSet('versiones', versiones), idbSet('sin_confirmar', sinConfirmar),
        ]).then(function () { window.location.reload(); });
    }

    // Fase 40B-2: respuesta 409. Lo local se aparta (no se borra), la encuesta pasa a la
    // ronda abierta del servidor y se cargan sus respuestas.
    function resolverConflicto(cuerpo) {
        if (cuerpo.codigo === 'participacion_anterior' && MODO_PROF) {
            // Fase 40 (retiro presencial): respuestas de una participación de la paciente que fue
            // retirada. No se envían ni se conservan: se borran solo los datos de esta paciente.
            conflictos = [];
            return Promise.all([limpiarEstadoLocal(null), idbSet('conflictos', [])]).then(function () {
                participacionDatos = participacionPagina;
                return idbSet('participacion_paciente', participacionPagina);
            }).then(function () {
                mensajeFinal('Estas respuestas eran de una participación de la paciente que fue retirada del ' +
                    'estudio. No se enviaron y se eliminaron de este dispositivo.', true, false, urlFicha || null);
            });
        }
        if (cuerpo.codigo === 'participacion_anterior') {
            // Fase 40 (P6): respuestas de una participación retirada. Por la decisión de retiro no
            // se envían ni se conservan: se borran de este dispositivo. Se cierra antes de borrar
            // para que una escritura aún en curso no deje nada después del borrado.
            sesionCerrada = true;
            return borrarEspacio(cuentaActual).then(function () {
                respuestas = {};
                mensajeFinal('Estas respuestas eran de una participación que retiraste del estudio. ' +
                    'No se enviaron y se eliminaron de este dispositivo. Recarga la página para empezar ' +
                    'tu participación actual.', true);
            });
        }
        if (cuerpo.codigo === 'consentimiento_paciente') {
            // Fase 40 (P7): la paciente no tiene consentimiento vigente. Nada se guardó; lo local se conserva.
            idbSet('pendiente_envio', true);
            mensajeFinal(cuerpo.error || 'La paciente no tiene un consentimiento vigente.', true, false,
                urlFicha || null);
            return Promise.resolve();
        }
        var habiaPendientes = sucio || envioFinalPendiente;
        var guardado = habiaPendientes ? archivarPendientes(cuerpo.codigo || 'conflicto') : Promise.resolve();
        return guardado.then(function () {
            if (cuerpo.codigo === 'cliente_desactualizado') {
                mensajeFinal(cuerpo.error || 'Recarga la página para continuar.', true);
                return;
            }
            iniciarRondaNueva();
            ronda = cuerpo.ronda_actual || null;
            sucio = false;
            envioFinalPendiente = false;
            return Promise.all([
                idbSet('ronda', ronda), idbSet('sucio', false), idbSet('pendiente_envio', false),
                idbSet('envio_final', false),
            ]).then(traerRondaActual).then(function () {
                mensajeFinal('Esta ronda ya estaba cerrada (por ejemplo, la finalizó otro dispositivo o el ' +
                    'personal de salud). ' + (habiaPendientes
                        ? 'Las respuestas que no alcanzaron a enviarse quedaron guardadas en este dispositivo.'
                        : ''), true, false, MODO_PROF ? (urlFicha || null) : null);
            });
        });
    }

    // Fase 40B-2: cierre rechazado por faltar respuestas obligatorias. Se vuelve a la
    // encuesta en la primera sección con pendientes y se dice cuáles son.
    function mostrarFaltantes(faltantes) {
        var secs = seccionesAplicables();
        var lineas = [];
        var primera = null;
        faltantes.forEach(function (f) {
            var tipoSeccion = f.seccion;
            var idx = -1;
            secs.forEach(function (s, i) { if (idx === -1 && s.tipo === tipoSeccion) { idx = i; } });
            var seccion = idx >= 0 ? secs[idx] : null;
            if (primera === null && idx >= 0) { primera = idx; }
            var textos = (f.preguntas || []).map(function (nombre) {
                var p = seccion && seccion.preguntas.filter(function (q) { return q.nombre === nombre; })[0];
                return p ? p.texto : nombre;
            });
            var titulo = seccion ? seccion.titulo : tipoSeccion;
            var motivo = f.motivo === 'por_confirmar' ? ' (confirma tu respuesta)' : '';
            lineas.push('• ' + titulo + motivo + (textos.length ? ': ' + textos.join('; ') : ''));
        });
        // Ceros por confirmar: se muestran sin marcar para que la persona elija de nuevo.
        faltantes.forEach(function (f) {
            if (f.motivo !== 'por_confirmar') { return; }
            (f.preguntas || []).forEach(function (n) {
                if (mrsPorConfirmar.indexOf(n) === -1) { mrsPorConfirmar.push(n); }
                if (respuestas.mrs && String(respuestas.mrs[n]) === '0' && !confirmadosMrs[n]) {
                    delete respuestas.mrs[n];
                }
            });
            idbSet('respuestas', respuestas);
        });
        indice = primera === null ? 0 : primera;
        render();
        window.scrollTo(0, 0);
        avisoSync('Tus respuestas quedaron guardadas, pero aún falta completar algunas preguntas.', 'error');
        alert('Para finalizar falta responder:\n' + lineas.join('\n'));
    }

    // Fase 29: el servidor puede devolver otro uuid_local para una sección (si
    // ya existía en la ronda, guardada desde otro dispositivo) y, al registrar
    // una paciente nueva, el número de su ficha.
    function adoptarRespuesta(cuerpo) {
        if (!cuerpo) { return; }
        var cambio = false;
        var versionNueva = false;
        (cuerpo.resultados || []).forEach(function (r) {
            if (r.uuid_local && r.seccion && r.seccion !== 'identificacion' &&
                uuids[r.seccion] !== r.uuid_local) {
                uuids[r.seccion] = r.uuid_local;
                cambio = true;
            }
            if (r.version && r.seccion) {   // Etapa 5B-3: guardado confirmado de esta sección
                versiones[r.seccion] = r.version;
                delete sinConfirmar[r.seccion];
                versionNueva = true;
            }
        });
        if (cambio) { idbSet('uuids', uuids); }
        if (versionNueva) { idbSet('versiones', versiones); idbSet('sin_confirmar', sinConfirmar); }
        if (ronda === null && cuerpo.ronda_actual) { ronda = cuerpo.ronda_actual; idbSet('ronda', ronda); }
        if (MODO_PROF && !pacienteId && cuerpo.paciente_id) { pacienteId = cuerpo.paciente_id; }
    }

    function mensajeFinal(texto, error, ofrecerEvaluacion, urlVolver) {
        var html = '<div class="tarjeta"><p class="' + (error ? 'errores' : '') + '">' +
            esc(texto) + '</p>';
        if (ofrecerEvaluacion) {
            // Fase 22: evaluación voluntaria de la plataforma, al final del sistema.
            html += '<p>¿Nos ayudas con 5 preguntas breves sobre la plataforma?</p>' +
                '<p><a class="boton" href="' + URL_EVALUACION + '">Evaluar la plataforma</a></p>';
        }
        cont.innerHTML = html + '<p class="enlaces"><a href="' + esc(urlVolver || '/') + '">' +
            (urlVolver ? 'Volver a la ficha de la paciente' : 'Volver al inicio') + '</a></p></div>';
    }

    // ---------- utilidades ----------
    function esc(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    // Fase 40B-2: acceso para las pruebas automáticas del cliente (apps/encuestas/pruebas_js).
    // Solo existe si el entorno de prueba define window.__PRUEBAS_ENCUESTA__ antes de cargar
    // este archivo; en el navegador real no hace nada.
    if (window.__PRUEBAS_ENCUESTA__) {
        window.__PRUEBAS_ENCUESTA__.interno = {
            estado: function () {
                return { respuestas: respuestas, uuids: uuids, ronda: ronda, sucio: sucio,
                    envioFinalPendiente: envioFinalPendiente, idCierre: idCierre, confirmadosMrs: confirmadosMrs,
                    mrsPorConfirmar: mrsPorConfirmar, conflictos: conflictos, indice: indice,
                    versiones: versiones, sinConfirmar: sinConfirmar, conflictoVersion: conflictoVersion };
            },
            decidirConflictoVersion: decidirConflictoVersion,
            capturar: function (tipo, campo, el, evento) {
                capturar(esquema.secciones.filter(function (s) { return s.tipo === tipo; })[0], campo, el, evento);
            },
            render: render,
            firmaVisible: function () { return firmaVisible; },
            responder: function (tipo, campo, valor) {
                var seccion = esquema.secciones.filter(function (s) { return s.tipo === tipo; })[0];
                capturar(seccion, campo, { value: String(valor), type: 'radio', tagName: 'INPUT' }, 'change');
            },
            finalizar: finalizar,
            guardarCambios: guardarCambios,
            intentarSync: intentarSync,
            construirPayload: construirPayload,
            // Fase 40B-3: HTML de la burbuja de suma del MRS con las respuestas actuales.
            burbujaMrs: function () {
                return burbujaPuntajeMrs(esquema.secciones.filter(function (s) { return s.tipo === 'mrs'; })[0]);
            },
        };
    }

    // Etapa 5B-3: al volver con «Atrás» el navegador puede restaurar esta página con sus datos
    // antiguos en memoria; se recarga para partir de lo último guardado.
    window.addEventListener('pageshow', function (e) {
        if (e.persisted) { window.location.reload(); }
    });

    iniciar();
})();
