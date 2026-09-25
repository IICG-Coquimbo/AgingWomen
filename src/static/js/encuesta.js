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
    var URL_RETIRO = '/api/retirarse/';

    var cont = document.getElementById('encuesta');

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
    var consentimiento = null;

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
                r.onsuccess = function () {
                    var valor = r.result ? r.result.valor : null;
                    db.close();
                    resolve(valor);
                };
                r.onerror = function () { reject(r.error); };
            });
        });
    }
    function idbSet(clave, valor) {
        return abrirDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction('estado', 'readwrite');
                tx.objectStore('estado').put({ clave: clave, valor: valor });
                tx.oncomplete = function () { db.close(); resolve(); };
                tx.onerror = function () { reject(tx.error); };
            });
        });
    }

    // ---------- Carga inicial ----------
    function iniciar() {
        Promise.all([
            idbGet('esquema'), idbGet('respuestas'), idbGet('uuids'),
            idbGet('bienvenida'), idbGet('consentimiento')
        ])
            .then(function (vals) {
                esquema = vals[0];
                respuestas = vals[1] || {};
                uuids = vals[2] || {};
                bienvenidaOk = !!vals[3];
                consentimiento = vals[4];
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

    // ---------- Consentimiento, definiciones y filtro de edad ----------
    function renderConsentimiento() {
        var html = '<div class="tarjeta consentimiento">';
        html += '<h1>Consentimiento Informado</h1>';
        html += '<p class="consentimiento-intro"><strong>Observatorio Integral de la Mujer en peri y menopausia:</strong> Caracterización de síntomas y factores de riesgo.</p>';
        html += '<div class="consentimiento-bloques">';
        html += '<div class="consentimiento-bloque"><h2>Propósito</h2><p>Conocer los síntomas de la peri y menopausia y los factores que pueden relacionarse con la salud integral de las mujeres.</p></div>';
        html += '<div class="consentimiento-bloque"><h2>¿En qué consiste?</h2><p>Es un estudio observacional. Responder el cuestionario toma aproximadamente 20 a 25 minutos y no incluye una intervención experimental.</p></div>';
        html += '<div class="consentimiento-bloque"><h2>Riesgos y beneficios</h2><p>Los riesgos son mínimos y pueden incluir incomodidad al responder alguna pregunta. No hay un beneficio directo garantizado; la información podrá contribuir a mejorar la atención y el conocimiento sobre esta etapa.</p></div>';
        html += '<div class="consentimiento-bloque"><h2>Participación y confidencialidad</h2><p>Participar es voluntario. Puedes no responder o retirarte en cualquier momento, sin consecuencias. Tus respuestas serán tratadas de forma confidencial y anónima en los resultados del estudio.</p></div>';
        html += '</div>';
        html += '<div class="contactos"><p><strong>Investigadoras:</strong> Scarleth Martínez, Valeska Zambra y Carolina Naranjo.</p>';
        html += '<p><strong>Investigadora Responsable:</strong> Dra. Vannessa Duarte Correa, UCN Sede Coquimbo.</p>';
        html += '<p><strong>Aprobación ética:</strong> Comité Ético Científico (CEC UCN).</p>';
        html += '<p><strong>Contacto CEC:</strong> <a href="mailto:cec.coquimbo@ucn.cl">cec.coquimbo@ucn.cl</a></p></div>';
        html += '<div class="consentimiento-opciones">';
        html += '<label><input type="checkbox" id="consentimiento-leido"> He leído y comprendido la información del estudio.</label>';
        html += '<label><input type="radio" name="consentimiento" value="acepto"> Acepto participar voluntariamente en esta investigación.</label>';
        html += '<label><input type="radio" name="consentimiento" value="no-acepto"> No acepto participar en esta investigación.</label>';
        html += '<label><input type="radio" name="consentimiento" value="desisto"> Desisto de participar en esta investigación.</label>';
        html += '<p id="consentimiento-error" class="errores" hidden></p>';
        html += '<button type="button" id="consentimiento-continuar" disabled>Continuar a validación de edad</button>';
        html += '</div></div>';
        cont.innerHTML = html;

        var continuar = document.getElementById('consentimiento-continuar');
        var error = document.getElementById('consentimiento-error');
        var leido = document.getElementById('consentimiento-leido');
        function actualizarContinuar() {
            var opcion = cont.querySelector('input[name="consentimiento"]:checked');
            continuar.disabled = !leido.checked || !opcion || opcion.value !== 'acepto';
        }
        leido.addEventListener('change', actualizarContinuar);
        cont.querySelectorAll('input[name="consentimiento"]').forEach(function (radio) {
            radio.addEventListener('change', function () {
                error.hidden = true;
                actualizarContinuar();
                if (radio.value === 'no-acepto') {
                    registrarDecisionConsentimiento('no-acepto');
                } else if (radio.value === 'desisto') {
                    registrarDecisionConsentimiento('desisto');
                }
            });
        });
        continuar.addEventListener('click', function () {
            var ahora = new Date().toISOString();
            consentimiento = {
                aceptado: true,
                decision: 'acepto',
                leido_en: ahora,
                aceptado_en: ahora
            };
            idbSet('consentimiento', consentimiento);
            render();
        });
    }

    function registrarDecisionConsentimiento(decision) {
        var ahora = new Date().toISOString();
        consentimiento = {
            aceptado: false,
            decision: decision,
            leido_en: ahora,
            decidido_en: ahora
        };
        idbSet('consentimiento', consentimiento).then(function () {
            cont.innerHTML = '<div class="tarjeta consentimiento-bloqueado"><h1>Participación no iniciada</h1>' +
                '<p>Agradecemos tu tiempo e interés. No avanzarás a la validación ni a la encuesta.</p>' +
                '<p>Esta pantalla permanecerá disponible para que puedas cerrar la sesión cuando lo desees.</p></div>';
        });
    }

    function limpiarEstadoLocal() {
        return new Promise(function (resolve) {
            var req = indexedDB.deleteDatabase(DB_NOMBRE);
            req.onsuccess = req.onerror = req.onblocked = function () { resolve(); };
        });
    }

    function retirarseDelEstudio(confirmar) {
        if (confirmar && !window.confirm('¿Deseas retirarte del estudio? Se eliminarán las respuestas no finalizadas.')) {
            return;
        }
        var body = JSON.stringify({ uuid_local: uuids.identificacion || null });
        var envio = navigator.onLine ? fetch(URL_RETIRO, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
            body: body
        }).catch(function () {}) : Promise.resolve();
        envio.then(function () {
            return limpiarEstadoLocal();
        }).then(function () {
            window.location.href = '/';
        });
    }

    // Pantalla de definiciones + validación inicial de inclusión.
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
        var edadMax = esquema.edad_maxima || 60;
        var ident = respuestas.identificacion || {};
        var fn = ident.fecha_nacimiento || '';
        var fupm = ident.fecha_ultimo_periodo_menstrual || '';
        var quirurgica = String(ident.menopausia_quirurgica_inducida) === 'true';
        var fupmNoAplica = String(ident.fupm_no_aplica_por_cirugia) === 'true';

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
        html += '<div class="gate"><p>Para verificar si cumples el perfil del estudio, completa estos datos:</p>';
        html += '<label for="g_fn">Fecha de nacimiento</label>';
        html += '<input id="g_fn" type="date" value="' + esc(fn) + '">';
        html += '<fieldset><legend>Inducción o cirugía</legend><p>¿Te has sometido a una histerectomía, extirpación de ovarios, o menopausia quirúrgica/inducida por tratamiento médico?</p>';
        html += '<label class="opcion"><input type="radio" name="g_quirurgica" value="true"' +
            (quirurgica ? ' checked' : '') + '> Sí</label>';
        html += '<label class="opcion"><input type="radio" name="g_quirurgica" value="false"' +
            (!quirurgica ? ' checked' : '') + '> No</label></fieldset>';
        html += '<label for="g_fupm">Fecha del último periodo menstrual</label>';
        html += '<input id="g_fupm" type="date" value="' + esc(fupm) + '"' +
            (fupmNoAplica ? ' disabled' : '') + '>';
        html += '<label class="opcion"><input id="g_fupm_na" type="checkbox"' +
            (fupmNoAplica ? ' checked' : '') + '> No aplica por cirugía/menopausia quirúrgica</label>';
        html += '<p id="g_error" class="errores" hidden></p>';
        html += '<button type="button" id="g_ok">Comenzar encuesta</button></div></div>';
        cont.innerHTML = html;

        var input = document.getElementById('g_fn');
        var fupmInput = document.getElementById('g_fupm');
        var fupmNoAplicaInput = document.getElementById('g_fupm_na');
        var err = document.getElementById('g_error');
        function limpiarError() { err.hidden = true; }
        input.addEventListener('input', limpiarError);
        fupmInput.addEventListener('input', limpiarError);
        cont.querySelectorAll('input[name="g_quirurgica"]').forEach(function (radio) {
            radio.addEventListener('change', limpiarError);
        });
        fupmNoAplicaInput.addEventListener('change', function () {
            fupmInput.disabled = fupmNoAplicaInput.checked;
            if (fupmNoAplicaInput.checked) { fupmInput.value = ''; }
            limpiarError();
        });
        document.getElementById('g_ok').addEventListener('click', function () {
            var edad = edadDesde(input.value);
            var cirugia = document.querySelector('input[name="g_quirurgica"]:checked').value === 'true';
            var noAplica = fupmNoAplicaInput.checked;
            if (edad === null) {
                err.textContent = 'Ingresa tu fecha de nacimiento.'; err.hidden = false; return;
            }
            if (noAplica && !cirugia) {
                err.textContent = 'Marca Sí en menopausia quirúrgica o inducida para indicar que la FUPM no aplica.';
                err.hidden = false; return;
            }
            if (!noAplica && !fupmInput.value) {
                err.textContent = 'Ingresa la fecha del último periodo menstrual o marca que no aplica por cirugía.';
                err.hidden = false; return;
            }
            if (!((edad >= edadMin && edad <= edadMax) || cirugia || noAplica)) {
                err.textContent = 'No cumples con el perfil objetivo del estudio. La edad debe estar entre ' +
                    edadMin + ' y ' + edadMax + ' años, salvo menopausia quirúrgica o inducida.';
                err.hidden = false;
                return;
            }
            if (!respuestas.identificacion) { respuestas.identificacion = {}; }
            respuestas.identificacion.fecha_nacimiento = input.value;
            respuestas.identificacion.edad_calculada = edad;
            respuestas.identificacion.menopausia_quirurgica_inducida = cirugia;
            respuestas.identificacion.fecha_ultimo_periodo_menstrual = noAplica ? '' : fupmInput.value;
            respuestas.identificacion.fupm_no_aplica_por_cirugia = noAplica;
            respuestas.identificacion.validacion_inicial_en = new Date().toISOString();
            idbSet('respuestas', respuestas);
            bienvenidaOk = true;
            idbSet('bienvenida', true);
            indice = 0;
            render();
        });
    }

    // ---------- Render ----------
    function render() {
        if (!consentimiento || !consentimiento.aceptado) { renderConsentimiento(); return; }
        if (!bienvenidaOk) { renderBienvenida(); return; }

        var secs = seccionesAplicables();
        indice = Math.max(0, Math.min(indice, secs.length - 1));
        var seccion = secs[indice];

        var html = barraProgreso(secs);
        html += '<div class="tarjeta seccion">';
        html += '<p class="paso">Sección ' + (indice + 1) + ' de ' + secs.length + '</p>';
        html += '<h1>' + esc(seccion.titulo) + '</h1>';
        if (seccion.descripcion) {
            html += '<p class="seccion-intro">' + esc(seccion.descripcion) + '</p>';
        }
        if (esquema.mensaje_omitir) {
            html += '<p class="seccion-omitir">' + esc(esquema.mensaje_omitir) + '</p>';
        }
        preguntasVisibles(seccion).forEach(function (p) { html += renderPregunta(seccion, p); });

        html += '<div class="nav">';
        if (indice > 0) { html += '<button type="button" data-nav="prev">Anterior</button>'; }
        html += '<button type="button" class="boton-guardar" data-nav="guardar">Guardar cambios</button>';
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
                else { finalizar(); }
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
        respuestas.envio_uuid = respuestas.envio_uuid || crearUuid();
        renderEvaluacionSatisfaccion();
    }

    function renderEvaluacionSatisfaccion() {
        var evaluacion = respuestas.evaluacion_satisfaccion || {};
        var html = '<div class="modal-cierre"><div class="tarjeta evaluacion-cierre">';
        html += '<h1>Antes de finalizar</h1><p>Responde estas cinco preguntas breves para completar tu participación.</p>';
        html += preguntaCierre('facilidad_uso', '¿Cómo evalúas la facilidad para responder el cuestionario?', [
            ['1', '😡 Muy difícil'], ['2', '😕 Difícil'], ['3', '😐 Normal'], ['4', '🙂 Fácil'], ['5', '😍 Muy fácil']
        ], evaluacion.facilidad_uso);
        html += preguntaCierre('fatiga_mental', '¿Sentiste fatiga o cansancio mental al responder la encuesta?', [
            ['1', '🟢 Ninguno'], ['2', '🟡 Poco'], ['3', '🟠 Moderado'], ['4', '🔴 Mucho']
        ], evaluacion.fatiga_mental);
        html += preguntaCierre('comodidad_diseno', '¿Qué tan cómodo te pareció el diseño y la navegación de la plataforma?', [
            ['1', '1 estrella'], ['2', '2 estrellas'], ['3', '3 estrellas'], ['4', '4 estrellas'], ['5', '5 estrellas']
        ], evaluacion.comodidad_diseno);
        html += preguntaCierre('recomendaria', '¿Recomendarías este Observatorio a otras mujeres en etapa de peri o menopausia?', [
            ['SI', 'Definitivamente sí'], ['TAL_VEZ', 'Tal vez'], ['NO', 'No']
        ], evaluacion.recomendaria);
        html += preguntaCierre('incomodidad', '¿Hubo alguna pregunta que te generara incomodidad o confusión?', [
            ['NO', 'No, ninguna'], ['SI', 'Sí']
        ], evaluacion.incomodidad);
        html += '<label id="comentario-cierre-label">Si respondiste Sí, especifica cuál o por qué (opcional)</label>';
        html += '<textarea id="comentario-cierre" rows="3">' + esc(evaluacion.comentario_incomodidad || '') + '</textarea>';
        html += '<p id="cierre-error" class="errores" hidden></p><button type="button" id="enviar-evaluacion">Enviar evaluación y finalizar</button>';
        html += '</div></div>';
        cont.innerHTML = html;
        document.getElementById('enviar-evaluacion').addEventListener('click', guardarEvaluacionSatisfaccion);
        cont.querySelectorAll('input[name="cierre_incomodidad"]').forEach(function (input) {
            input.addEventListener('change', function () {
                document.getElementById('comentario-cierre').disabled = input.value !== 'SI';
            });
        });
    }

    function preguntaCierre(nombre, texto, opciones, valor) {
        var html = '<fieldset class="pregunta-cierre"><legend>' + esc(texto) + '</legend>';
        opciones.forEach(function (opcion) {
            html += '<label><input type="radio" name="cierre_' + nombre + '" value="' + esc(opcion[0]) + '"' +
                (String(valor) === opcion[0] ? ' checked' : '') + '> ' + esc(opcion[1]) + '</label>';
        });
        return html + '</fieldset>';
    }

    function guardarEvaluacionSatisfaccion() {
        var evaluacion = {};
        ['facilidad_uso', 'fatiga_mental', 'comodidad_diseno', 'recomendaria', 'incomodidad'].forEach(function (nombre) {
            var opcion = cont.querySelector('input[name="cierre_' + nombre + '"]:checked');
            evaluacion[nombre] = opcion ? opcion.value : '';
        });
        evaluacion.comentario_incomodidad = document.getElementById('comentario-cierre').value;
        var error = document.getElementById('cierre-error');
        if (Object.keys(evaluacion).some(function (nombre) {
            return nombre !== 'comentario_incomodidad' && !evaluacion[nombre];
        })) {
            error.textContent = 'Responde todas las preguntas para finalizar.';
            error.hidden = false;
            return;
        }
        if (evaluacion.incomodidad === 'SI' && !evaluacion.comentario_incomodidad.trim()) {
            error.textContent = 'Describe brevemente la pregunta que te generó incomodidad o confusión.';
            error.hidden = false;
            return;
        }
        respuestas.evaluacion_satisfaccion = evaluacion;
        idbSet('respuestas', respuestas).then(function () {
            idbSet('envio_final', true);
            intentarSync(true);
        });
    }

    function construirPayload(esFinal) {
        var payload = {
            secciones: [],
            envio_final: !!esFinal,
            envio_uuid: respuestas.envio_uuid || null
        };
        payload.evaluacion_satisfaccion = respuestas.evaluacion_satisfaccion || null;
        var bloques = {};   // clave de sync -> bloque (para fusionar grupos, p. ej. MRS)
        seccionesAplicables().forEach(function (s) {
            var datos = respuestas[s.tipo] || {};
            if (s.tipo === 'identificacion') {
                payload.identificacion = {
                    uuid_local: uuids['identificacion'], datos: datos,
                    consentimiento: consentimiento
                };
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
        if (!ident || !seccionCompleta(ident) || !consentimiento || !consentimiento.aceptado) {
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
