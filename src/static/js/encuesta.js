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
    var DB_VERSION = 1;
    var URL_ESQUEMA = '/api/esquema/';
    var URL_SYNC = '/api/sincronizar/';
    var URL_EVALUACION = '/mi-evaluacion/';
    var URL_RONDA = '/api/ronda-actual/';

    var cont = document.getElementById('encuesta');

    // Fase 29: el personal de salud completa la encuesta de una paciente
    // existente (data-paciente) o registra una nueva (data-rut).
    var MODO_PROF = cont.dataset.modo === 'profesional';
    var pacienteId = cont.dataset.paciente ? parseInt(cont.dataset.paciente, 10) : null;
    var rutNueva = cont.dataset.rut || '';
    var urlFicha = cont.dataset.urlFicha || '';
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

    // ---------- IndexedDB ----------
    function abrirDB() {
        return new Promise(function (resolve, reject) {
            var req = indexedDB.open(DB_NOMBRE, DB_VERSION);
            req.onupgradeneeded = function () {
                req.result.createObjectStore('estado', { keyPath: 'clave' });
            };
            req.onsuccess = function () { resolve(req.result); };
            req.onerror = function () { reject(req.error); };
        });
    }
    // En modo profesional cada paciente tiene su propio estado local (no se
    // mezclan si el profesional atiende a varias, aunque esté sin conexión).
    function claveIdb(clave) { return MODO_PROF ? usuarioActual + '|' + clave : clave; }

    function idbGet(clave) {
        clave = claveIdb(clave);
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var r = db.transaction('estado', 'readonly').objectStore('estado').get(clave);
                r.onsuccess = function () { resolve(r.result ? r.result.valor : null); };
                r.onerror = function () { reject(r.error); };
            });
        });
    }
    function idbSet(clave, valor) {
        clave = claveIdb(clave);
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction('estado', 'readwrite');
                tx.objectStore('estado').put({ clave: clave, valor: valor });
                tx.oncomplete = function () { resolve(); };
                tx.onerror = function () { reject(tx.error); };
            });
        });
    }

    // ---------- Carga inicial ----------
    // IndexedDB es por navegador, no por cuenta: si en este dispositivo antes
    // respondió otra persona (u otro paciente, en el caso de un profesional)
    // sin cerrar sesión primero, hay que descartar ese estado — si no, se
    // arrastran uuid_local ajenos y el servidor rechaza el guardado (o peor,
    // se mezclan respuestas de otra persona).
    var usuarioActual = cont.dataset.usuario || '';

    function limpiarEstadoLocal() {
        respuestas = {};
        uuids = {};
        bienvenidaOk = false;
        envioFinalPendiente = false;
        return Promise.all([
            idbSet('respuestas', respuestas),
            idbSet('uuids', uuids),
            idbSet('bienvenida', false),
            idbSet('envio_final', false),
        ]);
    }

    function iniciar() {
        Promise.all([
            idbGet('esquema'), idbGet('respuestas'), idbGet('uuids'), idbGet('bienvenida'),
            idbGet('envio_final'), idbGet('usuario'), idbGet('sucio'), idbGet('pendiente_envio'),
            idbGet('ronda'),
        ])
            .then(function (vals) {
                esquema = vals[0];
                respuestas = vals[1] || {};
                uuids = vals[2] || {};
                bienvenidaOk = !!vals[3];
                envioFinalPendiente = !!vals[4];
                var usuarioGuardado = vals[5];
                sucio = !!vals[6] || !!vals[7];
                ronda = vals[8] || null;

                var cambioDeUsuario = usuarioGuardado && usuarioGuardado !== usuarioActual;
                var promesa = cambioDeUsuario ? limpiarEstadoLocal() : Promise.resolve();
                return promesa.then(function () {
                    return idbSet('usuario', usuarioActual);
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
        return fetch(url, { credentials: 'same-origin' })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (srv) { if (srv) { return reconciliar(srv); } })
            .catch(function () { /* sin conexión: se sigue con lo local */ });
    }

    function reconciliar(srv) {
        if (!srv.identificacion) { return; }  // la usuaria aún no tiene ficha
        identBloqueada = MODO_PROF && !!srv.identificacion.bloqueada;

        // Se cerró una ronda desde otro dispositivo (p. ej. la finalizó el
        // profesional): lo local pertenece a la ronda anterior.
        var cambioDeRonda = ronda !== null && srv.ronda_actual > ronda;
        if (cambioDeRonda) {
            iniciarRondaNueva();
            sucio = false;
            idbSet('sucio', false);
            idbSet('pendiente_envio', false);
        }
        var reemplazar = !sucio;  // sin cambios pendientes, manda el servidor

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
        });
        asegurarUuids();
        ronda = srv.ronda_actual;
        return Promise.all([
            idbSet('respuestas', respuestas), idbSet('uuids', uuids),
            idbSet('bienvenida', true), idbSet('ronda', ronda),
        ]);
    }

    function traerEsquema() {
        return fetch(URL_ESQUEMA, { headers: { 'Accept': 'application/json' } })
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
        sucio = true;
        idbSet('sucio', true);  // hay datos locales sin enviar al servidor

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

        if (afectaCondicionales(seccion, campo) || afectaDependencias(seccion, campo) ||
            esEscalaCalor(seccion, campo) || esEscalaHorizontal(seccion, campo)) {
            render();
        } else {
            actualizarProgreso();
        }
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
        intentarSync(true);
    }

    function construirPayload(esFinal) {
        var payload = { secciones: [] };
        if (esFinal) { payload.finalizar = true; }
        var bloques = {};   // clave de sync -> bloque (para fusionar grupos, p. ej. MRS)
        seccionesAplicables().forEach(function (s) {
            var datos = respuestas[s.tipo] || {};
            if (s.tipo === 'identificacion') {
                payload.identificacion = {
                    uuid_local: uuids['identificacion'],
                    datos: identBloqueada ? {} : datos,
                };
                if (MODO_PROF) {
                    if (pacienteId) { payload.identificacion.paciente_id = pacienteId; }
                    else { payload.identificacion.rut = rutNueva; }
                }
                return;
            }
            var k = claveSync(s);
            if (!bloques[k]) {
                bloques[k] = { tipo: k, uuid_local: uuids[k], datos: {}, parcial: false };
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
        return payload;
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

        indice = 0;
    }

    // Sube al servidor lo que haya guardado localmente. `esFinal` = la usuaria
    // pulsó "Finalizar". Se puede llamar en cualquier momento (al recuperar
    // conexión, al cargar): si no hay identificación completa, no hace nada.
    function intentarSync(esFinal) {
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

        return fetch(URL_SYNC, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
            body: JSON.stringify(construirPayload(esFinal))
        })
            .then(function (r) {
                return r.json().then(function (j) { return { ok: r.ok, cuerpo: j }; });
            })
            .then(function (res) {
                adoptarRespuesta(res.cuerpo);
                if (res.ok && res.cuerpo.ok) {
                    sucio = false;
                    idbSet('sucio', false);
                    idbSet('pendiente_envio', false);
                    if (esFinal) {
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
                            mensajeFinal('¡Encuesta enviada! Gracias por participar. Puedes volver a ' +
                                'responderla más adelante para registrar cómo han cambiado tus síntomas.',
                                false, true);
                        }
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
                }
            });
    }

    // Fase 29: el servidor puede devolver otro uuid_local para una sección (si
    // ya existía en la ronda, guardada desde otro dispositivo) y, al registrar
    // una paciente nueva, el número de su ficha.
    function adoptarRespuesta(cuerpo) {
        if (!cuerpo) { return; }
        var cambio = false;
        (cuerpo.resultados || []).forEach(function (r) {
            if (r.uuid_local && r.seccion && r.seccion !== 'identificacion' &&
                uuids[r.seccion] !== r.uuid_local) {
                uuids[r.seccion] = r.uuid_local;
                cambio = true;
            }
        });
        if (cambio) { idbSet('uuids', uuids); }
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

    iniciar();
})();
