/* ==========================================================================
   App cliente de la encuesta (Fase 7C)
   --------------------------------------------------------------------------
   - Descarga el esquema (/api/esquema/) y lo guarda en IndexedDB para uso offline.
   - Renderiza una sección a la vez desde el esquema.
   - Guarda cada respuesta en IndexedDB al instante.
   - Motor de preguntas/secciones condicionales, 100% local (Sección 5.2).
   La sincronización robusta offline se completa en la Fase 7E; aquí se envía
   si hay conexión y se marca "pendiente" si no.
   ========================================================================== */
(function () {
    'use strict';

    var DB_NOMBRE = 'encuesta_agingwomen';
    var DB_VERSION = 1;
    var URL_ESQUEMA = '/api/esquema/';
    var URL_SYNC = '/api/sincronizar/';

    var cont = document.getElementById('encuesta');
    var metaCsrf = document.querySelector('meta[name="csrf-token"]');
    var csrf = metaCsrf ? metaCsrf.content : '';

    var esquema = null;
    var respuestas = {};   // { seccion: { campo: valor } }
    var uuids = {};        // { seccion: uuid }
    var indice = 0;        // índice dentro de las secciones aplicables

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
    function idbGet(clave) {
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var r = db.transaction('estado', 'readonly').objectStore('estado').get(clave);
                r.onsuccess = function () { resolve(r.result ? r.result.valor : null); };
                r.onerror = function () { reject(r.error); };
            });
        });
    }
    function idbSet(clave, valor) {
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
    function iniciar() {
        Promise.all([idbGet('esquema'), idbGet('respuestas'), idbGet('uuids')])
            .then(function (vals) {
                esquema = vals[0];
                respuestas = vals[1] || {};
                uuids = vals[2] || {};
                return traerEsquema();
            })
            .then(function () {
                if (!esquema) { throw new Error('sin-esquema'); }
                asegurarUuids();
                render();
                mostrarConexion();
                window.addEventListener('online', alRecuperarConexion);
                window.addEventListener('offline', mostrarConexion);
                intentarSync(false);  // envía lo pendiente si hay conexión
            })
            .catch(function (err) {
                console.error(err);
                cont.innerHTML = '<div class="tarjeta"><p class="errores">No se pudo cargar la ' +
                    'encuesta. Necesitas conexión a internet al menos la primera vez.</p></div>';
            });
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
    function condicionCumplida(regla, datos) {
        if (!regla) { return true; }
        if (regla.operador && regla.operador !== 'igual') {
            // Operadores avanzados (p. ej. 'meses_desde_lt') se implementan en la
            // Fase 7. Hasta entonces la pregunta se muestra (nunca se oculta por error).
            return true;
        }
        var actual = datos ? datos[regla.campo] : undefined;
        return String(actual) === String(regla.valor);
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
    function preguntasVisibles(seccion) {
        var datos = respuestas[seccion.tipo] || {};
        return seccion.preguntas.filter(function (p) {
            return condicionCumplida(p.mostrar_si, datos);
        });
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

    // ---------- Render ----------
    function render() {
        var secs = seccionesAplicables();
        indice = Math.max(0, Math.min(indice, secs.length - 1));
        var seccion = secs[indice];

        var html = barraProgreso(secs);
        html += '<div class="tarjeta seccion">';
        html += '<p class="paso">Sección ' + (indice + 1) + ' de ' + secs.length + '</p>';
        html += '<h1>' + esc(seccion.titulo) + '</h1>';
        preguntasVisibles(seccion).forEach(function (p) { html += renderPregunta(seccion, p); });

        html += '<div class="nav">';
        if (indice > 0) { html += '<button type="button" data-nav="prev">Anterior</button>'; }
        if (indice < secs.length - 1) {
            html += '<button type="button" data-nav="next">Siguiente</button>';
        } else {
            html += '<button type="button" data-nav="finalizar">Finalizar</button>';
        }
        html += '</div></div>';

        cont.innerHTML = html;
        conectarEventos(seccion);
    }

    function barraProgreso(secs) {
        var completas = secs.filter(seccionCompleta).length;
        var pct = secs.length ? Math.round(completas / secs.length * 100) : 0;
        return '<div class="progreso"><div class="progreso-barra" style="width:' + pct + '%"></div>' +
            '<span class="progreso-texto">' + completas + ' de ' + secs.length +
            ' secciones completas</span></div>';
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
                else { finalizar(); }
            });
        });
        cont.querySelectorAll('.pregunta').forEach(function (div) {
            var campo = div.getAttribute('data-campo');
            var manejar = function (e) { capturar(seccion, campo, e.target); };
            div.addEventListener('input', manejar);
            div.addEventListener('change', manejar);
        });
    }

    function capturar(seccion, campo, el) {
        if (!respuestas[seccion.tipo]) { respuestas[seccion.tipo] = {}; }
        var valor = el.value;
        if (el.type === 'radio') {
            if (valor === 'true') { valor = true; }
            else if (valor === 'false') { valor = false; }
        }
        respuestas[seccion.tipo][campo] = valor;
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

        if (afectaCondicionales(seccion, campo) || afectaDependencias(seccion, campo) ||
            esEscalaCalor(seccion, campo)) {
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
        var barra = cont.querySelector('.progreso');
        if (barra) { barra.outerHTML = barraProgreso(seccionesAplicables()); }
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
            setTimeout(function () { if (navigator.onLine) { el.hidden = true; } }, 4000);
        }
    }

    function alRecuperarConexion() {
        mostrarConexion();
        intentarSync(false);
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
        idbSet('envio_final', true);
        intentarSync(true);
    }

    function construirPayload() {
        var payload = { secciones: [] };
        var bloques = {};   // clave de sync -> bloque (para fusionar grupos, p. ej. MRS)
        seccionesAplicables().forEach(function (s) {
            var datos = respuestas[s.tipo] || {};
            if (s.tipo === 'identificacion') {
                payload.identificacion = { uuid_local: uuids['identificacion'], datos: datos };
                return;
            }
            var k = claveSync(s);
            if (!bloques[k]) {
                bloques[k] = { tipo: k, uuid_local: uuids[k], datos: {}, parcial: false };
                payload.secciones.push(bloques[k]);
            }
            Object.keys(datos).forEach(function (campo) { bloques[k].datos[campo] = datos[campo]; });
            if (!seccionCompleta(s)) { bloques[k].parcial = true; }
        });
        return payload;
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
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify(construirPayload())
        })
            .then(function (r) {
                return r.json().then(function (j) { return { ok: r.ok, cuerpo: j }; });
            })
            .then(function (res) {
                if (res.ok && res.cuerpo.ok) {
                    idbSet('sucio', false);
                    idbSet('pendiente_envio', false);
                    if (esFinal) {
                        idbSet('envio_final', false);
                        mensajeFinal('¡Encuesta enviada! Gracias por participar.');
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

    function mensajeFinal(texto, error) {
        cont.innerHTML = '<div class="tarjeta"><p class="' + (error ? 'errores' : '') + '">' +
            esc(texto) + '</p><p class="enlaces"><a href="/">Volver al inicio</a></p></div>';
    }

    // ---------- utilidades ----------
    function esc(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    iniciar();
})();
