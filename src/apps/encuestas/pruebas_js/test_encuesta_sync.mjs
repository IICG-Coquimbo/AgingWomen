// Fase 40B-2: pruebas del cliente offline (static/js/encuesta.js) sin navegador ni dependencias.
//
//   node --test src/apps/encuestas/pruebas_js/
//
// encuesta.js se ejecuta en un contexto aislado (vm) con dobles mínimos de DOM, IndexedDB,
// fetch y navigator.onLine. El esquema es el real (esquema_*.json, exportado de construir_esquema;
// una prueba de Django comprueba que siga igual). Se verifica el protocolo 2, que nada pendiente
// en IndexedDB se borre ante fallos, y el manejo de 403, 409 y cierre rechazado.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';
import { randomUUID, webcrypto, createHash } from 'node:crypto';

const AQUI = dirname(fileURLToPath(import.meta.url));
const CODIGO = readFileSync(join(AQUI, '..', '..', '..', 'static', 'js', 'encuesta.js'), 'utf-8');
const ESQUEMA = JSON.parse(readFileSync(join(AQUI, 'esquema_usuaria.json'), 'utf-8'));
const ITEMS = Array.from({ length: 11 }, (_, i) => `pregunta_${i + 1}`);
const IDENT = {
    fecha_nacimiento: '1975-05-20', genero: 'F', nivel_educacion: 'M_COM', origen_procedencia: 'CL',
    pueblo_originario_afro: 'NINGUNO', region_residencia: '13', comuna: 'Santiago',
};

const copia = (v) => (v === undefined ? undefined : JSON.parse(JSON.stringify(v)));
// Fase 40: el cifrado (WebCrypto) termina fuera del ciclo de setImmediate: se espera también tiempo real.
const esperar = async (n = 30) => {
    for (let i = 0; i < n; i++) { await new Promise((r) => setImmediate(r)); await new Promise((r) => setTimeout(r, 1)); }
};

// Fase 40: claves de prueba por cuenta y participación (el servidor real las deriva de SECRET_KEY).
const BYTES_CLAVE = (cuenta, participacion) => createHash('sha256').update(`${cuenta}|${participacion}`).digest();
const b64 = (buf) => Buffer.from(buf).toString('base64');
const llaveHost = (cuenta, participacion) =>
    webcrypto.subtle.importKey('raw', BYTES_CLAVE(cuenta, participacion), { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
async function cifrarHost(cuenta, participacion, valor) {
    const iv = webcrypto.getRandomValues(new Uint8Array(12));
    const datos = await webcrypto.subtle.encrypt({ name: 'AES-GCM', iv }, await llaveHost(cuenta, participacion),
        new TextEncoder().encode(JSON.stringify(valor)));
    return { iv, datos };
}
async function descifrarHost(cuenta, participacion, reg) {
    try {
        const b = await webcrypto.subtle.decrypt({ name: 'AES-GCM', iv: reg.iv }, await llaveHost(cuenta, participacion), reg.datos);
        return JSON.parse(new TextDecoder().decode(b));
    } catch (e) { return undefined; }
}

// IndexedDB en memoria con los dos almacenes de encuesta.js ('estado' cifrado y 'llaves').
// `dispositivo.crudo` guarda lo que de verdad queda en el navegador (cifrado); `almacen` es
// una vista descifrada de la cuenta cargada, para que las pruebas lean los valores.
function crearIndexedDB(dispositivo, almacen, cuenta, opciones) {
    const prefijo = `${cuenta}|`;
    const enRango = (k, r) => (typeof r === 'object' ? k >= r.a && k <= r.b : k === r);
    return {
        open() {
            const req = {};
            setImmediate(() => {
                const db = {
                    objectStoreNames: { contains: () => dispositivo.creada },
                    createObjectStore() {},
                    transaction() {
                        const pendientes = [];
                        const tx = {};
                        const terminar = () => setImmediate(async () => {
                            try { await Promise.all(pendientes); } catch (e) { tx.error = e; tx.onerror && tx.onerror(); return; }
                            tx.oncomplete && tx.oncomplete();
                        });
                        tx.objectStore = (nombre) => ({
                            get(clave) {
                                const r = {};
                                setImmediate(() => {
                                    if (nombre === 'llaves') { r.result = dispositivo.llaves.get(clave); }
                                    else { r.result = dispositivo.crudo.get(clave); }
                                    r.onsuccess && r.onsuccess();
                                });
                                return r;
                            },
                            put(obj) {
                                if (nombre === 'llaves') { dispositivo.llaves.set(obj.cuenta, { ...obj }); terminar(); return; }
                                if (opciones.fallarEscritura) {
                                    setImmediate(() => { tx.error = new Error('cuota'); tx.onerror && tx.onerror(); });
                                    return;
                                }
                                dispositivo.crudo.set(obj.clave, { iv: obj.iv, datos: obj.datos });
                                if (obj.clave.startsWith(prefijo)) {
                                    const reg = dispositivo.llaves.get(cuenta);
                                    pendientes.push(descifrarHost(cuenta, reg && reg.participacion, obj)
                                        .then((v) => { almacen.set(obj.clave.slice(prefijo.length), v); }));
                                }
                                terminar();
                            },
                            delete(rango) {
                                const mapa = nombre === 'llaves' ? dispositivo.llaves : dispositivo.crudo;
                                for (const k of [...mapa.keys()]) {
                                    if (enRango(k, rango)) {
                                        mapa.delete(k);
                                        if (nombre === 'estado' && k.startsWith(prefijo)) { almacen.delete(k.slice(prefijo.length)); }
                                    }
                                }
                                terminar();
                            },
                        });
                        return tx;
                    },
                };
                req.result = db;
                if (!dispositivo.creada) { dispositivo.creada = true; req.onupgradeneeded && req.onupgradeneeded({ oldVersion: 0 }); }
                req.onsuccess && req.onsuccess();
            });
            return req;
        },
    };
}

function respuestaJson(status, cuerpo) {
    return { ok: status >= 200 && status < 300, status, json: () => Promise.resolve(copia(cuerpo)) };
}

// Servidor simulado: devuelve el esquema, la ronda actual y lo que diga `alSincronizar`.
function crearServidor({ ronda = 1, secciones = {}, porConfirmar = [], alSincronizar }) {
    const envios = [];
    const estado = { ronda, secciones, porConfirmar, participacion: 'p1', sesion: true };
    const fetch = (url, opciones = {}) => {
        if (url.startsWith('/api/clave-local/')) {
            if (!estado.sesion) { return Promise.resolve(respuestaJson(401, { ok: false, codigo: 'sin_sesion' })); }
            const cuenta = estado.cuentaDe;
            return Promise.resolve(respuestaJson(200, {
                ok: true, cuenta, clave: b64(BYTES_CLAVE(cuenta, estado.participacion)),
                participacion: estado.participacion, expira: '2999-01-01T00:00:00+00:00',
            }));
        }
        if (url.startsWith('/api/esquema/')) { return Promise.resolve(respuestaJson(200, ESQUEMA)); }
        if (url.startsWith('/api/ronda-actual/')) {
            return Promise.resolve(respuestaJson(200, {
                protocolo: 2, paciente_id: 7, ronda_actual: estado.ronda, disponible_desde: null, bloqueada: false,
                mrs_por_confirmar: estado.porConfirmar,
                identificacion: { uuid_local: 'ident-uuid', datos: IDENT, bloqueada: false },
                secciones: estado.secciones,
            }));
        }
        if (url.startsWith('/api/sincronizar/')) {
            const cuerpo = JSON.parse(opciones.body);
            envios.push(cuerpo);
            return alSincronizar(cuerpo, estado, envios.length);
        }
        return Promise.reject(new Error('url inesperada ' + url));
    };
    return { fetch, envios, estado };
}

function exito(cuerpo, estado) {
    if (cuerpo.finalizar) { estado.ronda += 1; }
    return Promise.resolve(respuestaJson(200, {
        ok: true, guardado: true, protocolo: 2, ronda_actual: estado.ronda, paciente_id: 7,
        resultados: [], disponible_desde: null,
        cierre: cuerpo.finalizar ? { estado: 'cerrada', ronda: estado.ronda - 1, id_cierre: cuerpo.id_cierre } : null,
    }));
}

// Un «dispositivo» por almacén: lo cifrado y las claves persisten entre cargas de la página.
const DISPOSITIVOS = new WeakMap();
async function cargar({ servidor, almacen = new Map(), enLinea = true, usuario = 'u1', fallarEscritura = false,
    dispositivo = null, conLlave = true, dataset = {}, cuentaFija = null, retrasoCifrado = 0 }) {
    const opciones = { fallarEscritura, retrasoCifrado };
    const cuenta = cuentaFija || `c-${usuario}`;
    servidor.estado.cuentaDe = cuenta;
    if (!dispositivo) {
        dispositivo = DISPOSITIVOS.get(almacen);
        if (!dispositivo) { dispositivo = { crudo: new Map(), llaves: new Map(), creada: false }; DISPOSITIVOS.set(almacen, dispositivo); }
    }
    // Lo que la prueba deja preparado en `almacen` estaba guardado (cifrado) en este dispositivo,
    // por una visita anterior con conexión: también estaba su clave.
    if (conLlave && !dispositivo.llaves.has(cuenta)) {
        dispositivo.llaves.set(cuenta, { cuenta, llave: await llaveHost(cuenta, servidor.estado.participacion),
            participacion: servidor.estado.participacion, expira: '2999-01-01T00:00:00+00:00', pendientes: {} });
    }
    const reg = dispositivo.llaves.get(cuenta);
    for (const [k, v] of almacen) {
        const clave = `${cuenta}|${k}`;
        if (!dispositivo.crudo.has(clave) && reg) {
            dispositivo.crudo.set(clave, await cifrarHost(cuenta, reg.participacion, v));
        }
    }
    dispositivo.creada = true;
    const alertas = [];
    const cont = {
        dataset: { usuario, cuenta, ...dataset }, innerHTML: '',
        addEventListener(tipo, f) { (cont.__oyentes[tipo] = cont.__oyentes[tipo] || []).push(f); },
        __oyentes: {}, querySelector() { return null; }, querySelectorAll() { return []; },
    };
    const estadoSync = { hidden: true, className: '', textContent: '' };
    const navegador = { onLine: enLinea };
    const contexto = {
        __PRUEBAS_ENCUESTA__: {},
        document: { cookie: 'csrftoken=prueba', getElementById: (id) => (id === 'encuesta' ? cont : id === 'estado-sync' ? estadoSync : null) },
        navigator: navegador,
        indexedDB: crearIndexedDB(dispositivo, almacen, cuenta, opciones),
        IDBKeyRange: { bound: (a, b) => ({ a, b }) },
        fetch: (url, ...resto) => (url.startsWith('/api/clave-local/') && !navegador.onLine
            ? Promise.reject(new TypeError('Failed to fetch')) : servidor.fetch(url, ...resto)),
        alert: (t) => alertas.push(t),
        console: { error() {}, warn() {}, log() {} },
        crypto: { randomUUID, getRandomValues: (a) => webcrypto.getRandomValues(a), subtle: {
            // Etapa 5B-3: `retrasoCifrado` simula un cifrado lento (CPU ocupada) de forma determinista.
            encrypt: (...x) => (opciones.retrasoCifrado
                ? new Promise((r) => setTimeout(r, opciones.retrasoCifrado)).then(() => webcrypto.subtle.encrypt(...x))
                : webcrypto.subtle.encrypt(...x)),
            decrypt: (...x) => webcrypto.subtle.decrypt(...x),
            importKey: (...x) => webcrypto.subtle.importKey(...x),
        } },
        atob: (t) => Buffer.from(t, 'base64').toString('binary'),
        TextEncoder, TextDecoder,
        __canales: [],
        BroadcastChannel: function () { contexto.__canales.push(this); },
        setTimeout: (f) => setImmediate(f),
        __oyentes: {},
        __recargas: 0,
        location: { reload: () => { contexto.__recargas += 1; } },
        addEventListener(tipo, f) { (contexto.__oyentes[tipo] = contexto.__oyentes[tipo] || []).push(f); },
        scrollTo() {},
        Promise, JSON, Object, Array, String, Number, Math, Date, parseInt, isNaN, decodeURIComponent,
        URL, Error,
    };
    contexto.window = contexto;
    vm.createContext(contexto);
    vm.runInContext(CODIGO, contexto, { filename: 'encuesta.js' });
    await esperar(80);
    return { api: contexto.__PRUEBAS_ENCUESTA__.interno, almacen, alertas, cont, navegador, opciones, estadoSync,
        dispositivo, cuenta, contexto };
}

// Dispositivo que ya abrió la encuesta antes con conexión (sin conexión no se baja la ronda).
function almacenPrevio() {
    return new Map([['bienvenida', true], ['ronda', 1], ['usuario', 'u1'],
        ['respuestas', { identificacion: { ...IDENT } }], ['uuids', { identificacion: 'ident-uuid' }]]);
}

async function responderMrs(api, valor = 1) {
    for (const item of ITEMS) { api.responder('mrs', item, valor); }
    await esperar();
}

test('el payload usa el protocolo 2: ronda local, id_cierre estable y confirmados del MRS', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { api } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_1', 0);
    const p = api.construirPayload(true);
    assert.equal(p.protocolo, 2);
    assert.equal(p.ronda, 1);
    assert.match(p.id_cierre, /^[0-9a-f-]{36}$/);
    assert.equal(api.construirPayload(true).id_cierre, p.id_cierre, 'el id_cierre no cambia entre reintentos');
    const mrs = p.secciones.find((b) => b.tipo === 'mrs');
    assert.deepEqual(mrs.confirmados, ['pregunta_1']);
    assert.equal(mrs.datos.pregunta_1, '0', 'el 0 elegido se envía como respuesta');
    assert.equal(mrs.datos.pregunta_2, undefined, 'lo no respondido no se envía');
});

test('sin conexión: finalizar no envía y deja todo pendiente en IndexedDB; al volver la red se cierra', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { api, almacen, navegador } = await cargar({ servidor, enLinea: false, almacen: almacenPrevio() });
    await responderMrs(api);
    api.finalizar();
    await esperar();
    assert.equal(servidor.envios.length, 0);
    assert.equal(almacen.get('envio_final'), true);
    assert.equal(almacen.get('sucio'), true);
    assert.equal(almacen.get('respuestas').mrs.pregunta_11, '1');
    const id = almacen.get('id_cierre');
    assert.ok(id);

    navegador.onLine = true;
    await api.intentarSync(true);
    await esperar();
    assert.equal(servidor.envios.length, 1);
    assert.equal(servidor.envios[0].id_cierre, id);
    assert.equal(almacen.get('ronda'), 2);
    assert.equal(almacen.get('envio_final'), false);
    assert.equal(almacen.get('id_cierre'), null);
    assert.deepEqual(Object.keys(almacen.get('respuestas')), ['identificacion'], 'ronda nueva en blanco tras el cierre confirmado');
});

test('error de red al finalizar: se conserva todo y el reintento usa el mismo id_cierre', async () => {
    let caida = true;
    const servidor = crearServidor({
        alSincronizar: (c, e) => (caida ? Promise.reject(new TypeError('Failed to fetch')) : exito(c, e)),
    });
    const { api, almacen } = await cargar({ servidor });
    await responderMrs(api, 2);
    api.finalizar();
    await esperar();
    assert.equal(almacen.get('pendiente_envio'), true);
    assert.equal(almacen.get('envio_final'), true);
    assert.equal(almacen.get('respuestas').mrs.pregunta_3, '2');
    caida = false;
    await api.intentarSync(true);
    await esperar();
    assert.equal(servidor.envios[0].id_cierre, servidor.envios[1].id_cierre);
    assert.equal(almacen.get('ronda'), 2);
});

test('respuesta que no es JSON (error 500 o página de inicio de sesión): todo sigue pendiente', async () => {
    const servidor = crearServidor({
        alSincronizar: () => Promise.resolve({ ok: false, status: 500, json: () => Promise.reject(new SyntaxError('html')) }),
    });
    const { api, almacen } = await cargar({ servidor });
    await responderMrs(api);
    api.finalizar();
    await esperar();
    assert.equal(almacen.get('pendiente_envio'), true);
    assert.equal(almacen.get('envio_final'), true);
    assert.equal(almacen.get('respuestas').mrs.pregunta_1, '1');
    assert.equal(almacen.get('ronda'), 1);
});

test('403 sin consentimiento: no se borra nada y se informa', async () => {
    const servidor = crearServidor({
        alSincronizar: () => Promise.resolve(respuestaJson(403, {
            ok: false, codigo: 'consentimiento_requerido', error: 'Debes aceptar el consentimiento informado.' })),
    });
    const { api, almacen, cont } = await cargar({ servidor });
    await responderMrs(api);
    api.finalizar();
    await esperar();
    assert.equal(almacen.get('pendiente_envio'), true);
    assert.equal(almacen.get('envio_final'), true);
    assert.equal(almacen.get('respuestas').mrs.pregunta_1, '1');
    assert.match(cont.innerHTML, /consentimiento/);
});

test('cierre rechazado por incompleto: queda como borrador, se informa qué falta y se puede reintentar', async () => {
    const servidor = crearServidor({
        alSincronizar: (c, e) => Promise.resolve(respuestaJson(200, {
            ok: false, guardado: true, protocolo: 2, ronda_actual: e.ronda, paciente_id: 7, resultados: [],
            cierre: { estado: 'rechazado', ronda: 1, motivo: 'incompleta',
                faltantes: [{ seccion: 'mrs', motivo: 'obligatorias_sin_responder', preguntas: ['pregunta_4'] }] },
        })),
    });
    const { api, almacen, alertas } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_1', 3);
    await esperar();
    await api.intentarSync(true);
    await esperar();
    assert.equal(almacen.get('envio_final'), false, 'no se reintenta solo un cierre que no puede pasar');
    assert.equal(almacen.get('id_cierre'), null, 'el próximo intento es un cierre nuevo');
    assert.equal(almacen.get('respuestas').mrs.pregunta_1, '3', 'lo respondido se conserva');
    assert.equal(almacen.get('ronda'), 1);
    assert.equal(alertas.length, 1);
    assert.match(alertas[0], /Dificultades en el sueño/);
    assert.equal(api.estado().indice, ESQUEMA.secciones.findIndex((s) => s.tipo === 'mrs') - 1,
        'vuelve a la sección MRS (índice entre las aplicables: Trabajo no aplica)');
});

test('409 ronda cerrada: lo pendiente se aparta en IndexedDB (no se borra) y se pasa a la ronda abierta', async () => {
    const servidor = crearServidor({
        alSincronizar: (c, e) => { e.ronda = 2; return Promise.resolve(respuestaJson(409, {
            ok: false, codigo: 'ronda_cerrada', error: 'La ronda 1 ya está cerrada.', ronda_actual: 2 })); },
    });
    const { api, almacen } = await cargar({ servidor });
    await responderMrs(api, 4);
    api.finalizar();
    await esperar(120);
    const conflictos = almacen.get('conflictos');
    assert.equal(conflictos.length, 1);
    assert.equal(conflictos[0].motivo, 'ronda_cerrada');
    assert.equal(conflictos[0].ronda, 1);
    assert.equal(conflictos[0].respuestas.mrs.pregunta_5, '4');
    assert.equal(almacen.get('ronda'), 2);
    assert.equal(almacen.get('envio_final'), false);
    assert.equal(servidor.envios.length, 1, 'no se reintenta en bucle');
});

test('al cargar con una ronda cerrada en otro dispositivo y cambios sin enviar, se apartan antes de empezar la nueva', async () => {
    const almacen = new Map();
    const servidor = crearServidor({ ronda: 1, alSincronizar: () => Promise.reject(new TypeError('red')) });
    const primera = await cargar({ servidor, almacen });
    await responderMrs(primera.api, 2);
    assert.equal(almacen.get('sucio'), true);
    servidor.estado.ronda = 2;  // otro dispositivo cerró la ronda 1
    const segunda = await cargar({ servidor, almacen });
    assert.equal(almacen.get('ronda'), 2);
    const conflictos = almacen.get('conflictos');
    assert.equal(conflictos.length, 1);
    assert.equal(conflictos[0].respuestas.mrs.pregunta_1, '2');
    assert.equal((segunda.api.estado().respuestas.mrs || {}).pregunta_1, undefined, 'la ronda nueva parte en blanco');
});

test('cambio de cuenta en el mismo dispositivo: cada cuenta tiene su espacio cifrado y nada se mezcla', async () => {
    const dispositivo = { crudo: new Map(), llaves: new Map(), creada: false };
    const servidor = crearServidor({ alSincronizar: () => Promise.reject(new TypeError('red')) });
    const a = await cargar({ servidor, dispositivo, almacen: new Map(), usuario: 'A' });
    await responderMrs(a.api, 3);
    const b = await cargar({ servidor, dispositivo, almacen: new Map(), usuario: 'B' });
    assert.equal((b.api.estado().respuestas.mrs || {}).pregunta_1, undefined, 'B no ve nada de A');
    // Lo de A está cifrado con la clave de A: con la de B no se puede leer.
    const regA = dispositivo.crudo.get('c-A|respuestas');
    assert.ok(regA && regA.iv && regA.datos);
    assert.equal(await descifrarHost('c-B', 'p1', regA), undefined);
    assert.ok(!JSON.stringify([...dispositivo.crudo.values()].map((r) => Buffer.from(r.datos).toString('latin1'))).includes('pregunta_1'));
    const otra = await cargar({ servidor, dispositivo, almacen: new Map(), usuario: 'A' });
    assert.equal(otra.api.estado().respuestas.mrs.pregunta_1, '3', 'A recupera lo suyo al volver');
    assert.equal(otra.api.estado().sucio, true);
});

test('ceros de un MRS anterior a la 40B-2: se muestran sin marcar y solo valen si se eligen de nuevo', async () => {
    const almacen = new Map([['respuestas', { mrs: { pregunta_2: 0, pregunta_3: 2 } }], ['sucio', true],
        ['ronda', 1], ['bienvenida', true], ['usuario', 'u1']]);
    const servidor = crearServidor({
        secciones: { mrs: { uuid_local: 'mrs-uuid', datos: { pregunta_3: 2 } } },
        porConfirmar: ['pregunta_2'],
        alSincronizar: (c, e) => exito(c, e),
    });
    const { api } = await cargar({ servidor, almacen });
    assert.equal(api.estado().respuestas.mrs.pregunta_2, undefined, 'el 0 antiguo no cuenta como respuesta');
    assert.deepEqual(api.estado().mrsPorConfirmar, ['pregunta_2']);
    api.responder('mrs', 'pregunta_2', 0);
    const mrs = api.construirPayload(false).secciones.find((b) => b.tipo === 'mrs');
    assert.deepEqual(mrs.confirmados, ['pregunta_2']);
});

test('si IndexedDB no puede escribir, se avisa y no se pierde lo ya guardado', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { api, almacen, opciones, estadoSync } = await cargar({ servidor, enLinea: false, almacen: almacenPrevio() });
    await responderMrs(api);
    const antes = copia(almacen.get('respuestas'));
    opciones.fallarEscritura = true;
    api.finalizar();
    await esperar();
    assert.deepEqual(almacen.get('respuestas'), antes, 'lo ya guardado sigue intacto');
    assert.equal(servidor.envios.length, 0);
    assert.match(estadoSync.textContent, /No se pudo guardar en este dispositivo/);
});

test('40B-3: la suma del MRS en la encuesta es parcial o provisional, nunca un resultado ni una severidad', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { api } = await cargar({ servidor, almacen: almacenPrevio() });
    api.responder('mrs', 'pregunta_1', 0);
    api.responder('mrs', 'pregunta_2', 3);
    let html = api.burbujaMrs();
    assert.match(html, /data-estado="parcial"/);
    assert.match(html, /Suma parcial: 3 \/ 44/);
    assert.match(html, /2 de 11 preguntas respondidas/);
    for (const item of ITEMS.slice(2)) { api.responder('mrs', item, 4); }
    html = api.burbujaMrs();
    assert.match(html, /data-estado="provisional"/);
    assert.match(html, /Suma provisional: 39 \/ 44/);
    assert.match(html, /Se confirma al finalizar/);
    for (const prohibido of ['Severidad', 'Severa', 'Moderada', 'Leve', 'Sin síntomas', 'Puntaje MRS']) {
        assert.ok(!html.includes(prohibido), prohibido);
    }
    assert.equal(ESQUEMA.mrs_severidad, undefined, 'el esquema ya no publica cortes de severidad');
});


// ---------------------------------------------------------------- Fase 40: privacidad del dispositivo
test('P1: sin clave (sesión cerrada) y sin conexión, la copia offline no muestra ni deja editar nada', async () => {
    const servidor = crearServidor({ alSincronizar: () => Promise.reject(new TypeError('red')) });
    const dispositivo = { crudo: new Map(), llaves: new Map(), creada: false };
    const primera = await cargar({ servidor, dispositivo, almacen: new Map() });
    await responderMrs(primera.api, 2);
    assert.ok(dispositivo.crudo.get('c-u1|respuestas'));
    dispositivo.llaves.delete('c-u1');   // «Salir» borra la clave (sesion.js)
    const despues = await cargar({ servidor, dispositivo, almacen: new Map(), enLinea: false, conLlave: false });
    assert.match(despues.cont.innerHTML, /sesión no está iniciada/);
    assert.equal(despues.api.estado().respuestas.mrs, undefined);
    assert.ok(dispositivo.crudo.get('c-u1|respuestas'), 'lo pendiente sigue guardado (cifrado), no se borra');
});

test('P1: con conexión y sin sesión, el servidor no entrega la clave (401) y la clave local se elimina', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const dispositivo = { crudo: new Map(), llaves: new Map(), creada: false };
    await cargar({ servidor, dispositivo, almacen: new Map() });
    servidor.estado.sesion = false;
    const sinSesion = await cargar({ servidor, dispositivo, almacen: new Map(), conLlave: false });
    assert.match(sinSesion.cont.innerHTML, /sesión no está iniciada/);
    assert.equal(dispositivo.llaves.has('c-u1'), false);
});

test('P1: tras «Salir» en otra pestaña, esta deja de mostrar y de guardar datos', async () => {
    const servidor = crearServidor({ alSincronizar: () => Promise.reject(new TypeError('red')) });
    const { api, dispositivo, contexto, cont } = await cargar({ servidor });
    await responderMrs(api, 1);
    const antes = dispositivo.crudo.get('c-u1|respuestas');
    contexto.__canales[0].onmessage({ data: { tipo: 'salida', cuenta: 'c-u1' } });
    assert.match(cont.innerHTML, /sesión se cerró/);
    assert.equal(api.estado().respuestas.mrs, undefined, 'nada queda en memoria');
    api.responder('mrs', 'pregunta_1', 4);
    await esperar();
    assert.equal(dispositivo.crudo.get('c-u1|respuestas'), antes, 'no se escribió nada después de salir');
});

test('P6: la participación viaja en cada envío y un 409 participacion_anterior borra lo local sin reenviarlo', async () => {
    const servidor = crearServidor({
        alSincronizar: () => Promise.resolve(respuestaJson(409, { ok: false, codigo: 'participacion_anterior',
            error: 'Participación anterior.' })),
    });
    const { api, dispositivo, cont } = await cargar({ servidor });
    await responderMrs(api, 2);
    assert.equal(api.construirPayload(false).participacion, 'p1');
    api.finalizar();
    await esperar(120);
    assert.equal(servidor.envios.length, 1, 'no se reintenta');
    assert.equal(servidor.envios[0].participacion, 'p1');
    assert.equal([...dispositivo.crudo.keys()].filter((k) => k.startsWith('c-u1|')).length, 0);
    assert.match(cont.innerHTML, /participación que retiraste/);
});

test('P6: con una participación nueva (retiro y consentimiento nuevo) lo guardado de la anterior se elimina al cargar', async () => {
    const servidor = crearServidor({ alSincronizar: () => Promise.reject(new TypeError('red')) });
    const dispositivo = { crudo: new Map(), llaves: new Map(), creada: false };
    const vieja = await cargar({ servidor, dispositivo, almacen: new Map() });
    await responderMrs(vieja.api, 4);
    servidor.estado.participacion = 'p2';
    const nueva = await cargar({ servidor, dispositivo, almacen: new Map() });
    assert.equal((nueva.api.estado().respuestas.mrs || {}).pregunta_1, undefined, 'no se recupera nada de la participación retirada');
    assert.equal(nueva.api.construirPayload(false).participacion, 'p2');
    assert.equal(dispositivo.llaves.get('c-u1').participacion, 'p2');
});

test('P7: 409 consentimiento_paciente en modo profesional conserva lo local e informa', async () => {
    const servidor = crearServidor({
        alSincronizar: () => Promise.resolve(respuestaJson(409, { ok: false, codigo: 'consentimiento_paciente',
            error: 'Esta persona tiene una cuenta sin consentimiento vigente.' })),
    });
    const { api, almacen, cont } = await cargar({ servidor });
    await responderMrs(api, 1);
    await api.intentarSync(false);
    await esperar(120);
    assert.equal(almacen.get('pendiente_envio'), true);
    assert.equal(almacen.get('respuestas').mrs.pregunta_1, '1');
    assert.match(cont.innerHTML, /consentimiento vigente/);
});

// Fase 40 (retiro presencial): en modo profesional, lo que se envía por una paciente lleva la
// participación de ella para la que se preparó; si se retiró, el servidor lo rechaza y se borra.
const PROF = (participacion, paciente = '7') => ({ modo: 'profesional', paciente, participacionPaciente: participacion });

test('profesional: la participación de la paciente viaja en el bloque de identificación', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { api } = await cargar({ servidor, usuario: 'prof:h:pac:7', cuentaFija: 'c-prof', dataset: PROF('pA') });
    await responderMrs(api, 2);
    assert.equal(api.construirPayload(false).identificacion.participacion_paciente, 'pA');
    assert.equal(api.construirPayload(false).identificacion.paciente_id, 7);
    assert.equal(api.construirPayload(false).participacion, undefined);
});

test('profesional: 409 participacion_anterior borra solo los datos de esa paciente y no reenvía', async () => {
    const servidor = crearServidor({
        alSincronizar: () => Promise.resolve(respuestaJson(409, { ok: false, codigo: 'participacion_anterior',
            error: 'Participación anterior.' })),
    });
    const dispositivo = { crudo: new Map(), llaves: new Map(), creada: false };
    // Otra paciente con algo guardado en el mismo dispositivo y la misma cuenta profesional.
    const otra = await cargar({ servidor: crearServidor({ alSincronizar: () => Promise.reject(new TypeError('red')) }),
        dispositivo, usuario: 'prof:h:pac:8', cuentaFija: 'c-prof', dataset: PROF('pZ', '8') });
    await responderMrs(otra.api, 3);
    const { api, cont, almacen } = await cargar({ servidor, dispositivo, usuario: 'prof:h:pac:7', cuentaFija: 'c-prof',
        dataset: PROF('pA') });
    await responderMrs(api, 2);
    await api.intentarSync(false);
    await esperar(120);
    assert.equal(servidor.envios.length, 1, 'no se reintenta');
    assert.equal(servidor.envios[0].identificacion.participacion_paciente, 'pA');
    assert.deepEqual(almacen.get('prof:h:pac:7|respuestas'), {});
    assert.equal(almacen.get('prof:h:pac:7|sucio'), false);
    assert.match(cont.innerHTML, /participación de la paciente que fue retirada/);
    assert.ok(dispositivo.llaves.get('c-prof'), 'la clave de la profesional se conserva');
    const deOtra = await descifrarHost('c-prof', 'p1', dispositivo.crudo.get('c-prof|prof:h:pac:8|respuestas'));
    assert.equal(deOtra.mrs.pregunta_1, '3', 'otra paciente intacta');
});

test('profesional: lo pendiente se envía con la participación con que se guardó, no con la de la página nueva', async () => {
    const dispositivo = { crudo: new Map(), llaves: new Map(), creada: false };
    const sinRed = crearServidor({ alSincronizar: () => Promise.reject(new TypeError('red')) });
    const vieja = await cargar({ servidor: sinRed, dispositivo, usuario: 'prof:h:pac:7', cuentaFija: 'c-prof',
        dataset: PROF('pA') });
    await responderMrs(vieja.api, 4);
    await vieja.api.intentarSync(false);
    await esperar(60);
    // La paciente se retiró y volvió a consentir: la página trae otra participación.
    const servidor = crearServidor({
        alSincronizar: (c) => Promise.resolve(c.identificacion.participacion_paciente === 'pB'
            ? respuestaJson(200, { ok: true, guardado: true, protocolo: 2, ronda_actual: 1, paciente_id: 7, resultados: [] })
            : respuestaJson(409, { ok: false, codigo: 'participacion_anterior', error: 'Participación anterior.' })),
    });
    const nueva = await cargar({ servidor, dispositivo, usuario: 'prof:h:pac:7', cuentaFija: 'c-prof',
        dataset: PROF('pB') });
    await esperar(120);
    assert.equal(servidor.envios.length, 1);
    assert.equal(servidor.envios[0].identificacion.participacion_paciente, 'pA', 'nunca se re-etiqueta lo antiguo');
    assert.equal((nueva.api.estado().respuestas.mrs || {}).pregunta_1, undefined);
    assert.equal(nueva.api.construirPayload(false).identificacion.participacion_paciente, 'pB');
});

// ---------- Etapa 5B-3: respuestas concurrentes, página antigua y clics ----------
const conVersion = (version) => ({ resultados: [{ seccion: 'mrs', estado: 'actualizado', version }] });
function guardadoCon(version, cuerpo, estado) {
    return respuestaJson(200, { ok: true, guardado: true, protocolo: 2, ronda_actual: estado.ronda, paciente_id: 7,
        disponible_desde: null, cierre: null, ...conVersion(version) });
}
const conflicto = (versiones = { mrs: 'v-servidor' }) => Promise.resolve(respuestaJson(409, {
    ok: false, codigo: 'version_desactualizada', error: 'Cambió.', ronda_actual: 1, secciones: ['mrs'], versiones,
}));
function diferido() {
    let resolver;
    const promesa = new Promise((r) => { resolver = r; });
    return { promesa, resolver };
}
const MRS_GUARDADO = { uuid_local: 'mrs-uuid', version: 'v1', datos: { pregunta_1: 1 } };
const bloqueMrs = (payload) => payload.secciones.find((b) => b.tipo === 'mrs');

test('5B-3: cada envío usa la versión leída y luego la que devolvió el servidor', async () => {
    let n = 0;
    const servidor = crearServidor({ secciones: { mrs: MRS_GUARDADO },
        alSincronizar: (c, e) => Promise.resolve(guardadoCon(`v${++n + 1}`, c, e)) });
    const { api } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_2', 2);
    await esperar();
    await api.intentarSync(false);
    await esperar();
    await api.intentarSync(false);
    await esperar();
    assert.equal(bloqueMrs(servidor.envios[0]).version_base, 'v1');
    assert.equal(bloqueMrs(servidor.envios[1]).version_base, 'v2');
});

test('5B-3: una página antigua recibe 409, conserva lo local, no reintenta sola y no pierde nada', async () => {
    const servidor = crearServidor({ secciones: { mrs: MRS_GUARDADO }, alSincronizar: () => conflicto() });
    const { api, almacen, cont, navegador } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_2', 3);
    await esperar();
    await api.intentarSync(false);
    await esperar();
    assert.match(cont.innerHTML, /data-conflicto-version/);
    assert.match(cont.innerHTML, /no se guardó ningún cambio/);
    assert.equal(api.estado().sucio, true);
    assert.equal(almacen.get('respuestas').mrs.pregunta_2, '3', 'lo local sigue guardado');
    assert.equal(api.estado().conflictos.length, 0, 'no se archiva ni se decide solo');
    navegador.onLine = true;
    await api.intentarSync(false);
    await esperar();
    assert.equal(servidor.envios.length, 1, 'sin decisión de la persona no se envía de nuevo');
});

test('5B-3: «Guardar lo de esta página» reenvía con la versión del conflicto; es una acción explícita', async () => {
    let primero = true;
    const servidor = crearServidor({ secciones: { mrs: MRS_GUARDADO }, alSincronizar: (c, e) => {
        if (primero) { primero = false; return conflicto(); }
        return Promise.resolve(guardadoCon('v9', c, e));
    } });
    const { api } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_2', 3);
    await esperar();
    await api.intentarSync(false);
    await esperar();
    assert.equal(servidor.envios.length, 1);
    await api.decidirConflictoVersion('pagina');
    await esperar();
    assert.equal(servidor.envios.length, 2);
    assert.equal(bloqueMrs(servidor.envios[1]).version_base, 'v-servidor');
    assert.equal(api.estado().sucio, false);
});

test('5B-3: «Ver lo último guardado» limpia lo pendiente y recarga sin enviar', async () => {
    const servidor = crearServidor({ secciones: { mrs: MRS_GUARDADO }, alSincronizar: () => conflicto() });
    const { api, almacen, contexto } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_2', 3);
    await esperar();
    await api.intentarSync(false);
    await esperar();
    await api.decidirConflictoVersion('guardado');
    await esperar();
    assert.equal(contexto.__recargas, 1);
    assert.equal(almacen.get('sucio'), false);
    assert.equal(almacen.get('pendiente_envio'), false);
    assert.equal(servidor.envios.length, 1);
});

test('5B-3: lo respondido durante un envío sigue pendiente y se envía después (encuesta.js:1406)', async () => {
    const d = diferido();
    let n = 0;
    const servidor = crearServidor({ alSincronizar: (c, e) => {
        n += 1;
        return n === 1 ? d.promesa.then(() => guardadoCon('v1', c, e)) : Promise.resolve(guardadoCon('v2', c, e));
    } });
    const { api, almacen } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_1', 1);
    await esperar();
    const envio = api.intentarSync(false);
    await esperar();
    api.responder('mrs', 'pregunta_2', 4);                 // durante el envío
    await esperar();
    assert.equal(bloqueMrs(servidor.envios[0]).datos.pregunta_2, undefined);
    d.resolver();
    await envio;
    await esperar();
    assert.equal(servidor.envios.length, 2, 'lo nuevo se envía sin esperar otra acción');
    assert.equal(bloqueMrs(servidor.envios[1]).datos.pregunta_2, '4');
    assert.equal(bloqueMrs(servidor.envios[1]).version_base, 'v1', 'parte de lo recién guardado');
    assert.equal(api.estado().sucio, false);
    assert.equal(almacen.get('sucio'), false);
});

test('5B-3: si falla el envío siguiente, lo respondido durante el primero queda pendiente', async () => {
    const d = diferido();
    let n = 0;
    const servidor = crearServidor({ alSincronizar: (c, e) => {
        n += 1;
        return n === 1 ? d.promesa.then(() => guardadoCon('v1', c, e)) : Promise.reject(new TypeError('red'));
    } });
    const { api, almacen, estadoSync } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_1', 1);
    await esperar();
    const envio = api.intentarSync(false);
    await esperar();
    api.responder('mrs', 'pregunta_2', 4);
    await esperar();
    d.resolver();
    await envio;
    await esperar();
    assert.equal(api.estado().sucio, true);
    assert.equal(almacen.get('sucio'), true);
    assert.equal(almacen.get('pendiente_envio'), true);
    assert.equal(almacen.get('respuestas').mrs.pregunta_2, '4');
    assert.match(estadoSync.textContent, /siguen guardadas en este dispositivo/);
});

test('5B-3: solicitudes consecutivas salen de una en una, sin competir por la misma versión', async () => {
    const d = diferido();
    let n = 0, enVuelo = 0, maximo = 0;
    const servidor = crearServidor({ alSincronizar: (c, e) => {
        n += 1; enVuelo += 1; maximo = Math.max(maximo, enVuelo);
        const v = `v${n}`;
        return (n === 1 ? d.promesa : Promise.resolve()).then(() => { enVuelo -= 1; return guardadoCon(v, c, e); });
    } });
    const { api } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_1', 1);
    await esperar();
    const a = api.intentarSync(false);
    await esperar();
    api.responder('mrs', 'pregunta_1', 2);
    api.intentarSync(false); api.intentarSync(false); api.guardarCambios();
    await esperar();
    assert.equal(servidor.envios.length, 1);
    d.resolver();
    await a;
    await esperar();
    assert.equal(maximo, 1);
    assert.equal(servidor.envios.length, 2, 'las peticiones repetidas se agrupan en un solo envío');
    assert.equal(bloqueMrs(servidor.envios[1]).datos.pregunta_1, '2');
});

test('5B-3: corte de red: lo enviado sin respuesta viaja en el reintento y se limpia al confirmar', async () => {
    let caida = true;
    const servidor = crearServidor({ secciones: { mrs: MRS_GUARDADO }, alSincronizar: (c, e) => (
        caida ? Promise.reject(new TypeError('Failed to fetch')) : Promise.resolve(guardadoCon('v2', c, e))) });
    const { api, almacen } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_2', 2);
    await esperar();
    await api.intentarSync(false);
    await esperar();
    assert.equal(api.estado().sucio, true);
    assert.equal(almacen.get('sin_confirmar').mrs.length, 1);
    api.responder('mrs', 'pregunta_3', 3);
    await esperar();
    caida = false;
    await api.intentarSync(false);
    await esperar();
    const b = bloqueMrs(servidor.envios[1]);
    assert.equal(b.version_base, 'v1', 'sigue partiendo de lo último confirmado');
    assert.equal(b.sin_confirmar[0].pregunta_2, '2');
    assert.equal(b.sin_confirmar[0].pregunta_3, undefined);
    assert.equal(api.estado().sucio, false);
    assert.equal(almacen.get('sin_confirmar').mrs, undefined);
    assert.equal(almacen.get('versiones').mrs, 'v2');
});

test('5B-3: recargar tras un guardado sin respuesta conserva lo pendiente, su versión y lo enviado', async () => {
    const colgado = new Promise(() => {});
    const servidor = crearServidor({ secciones: { mrs: MRS_GUARDADO }, alSincronizar: () => colgado });
    const { api, almacen } = await cargar({ servidor });
    api.responder('mrs', 'pregunta_2', 2);
    await esperar();
    api.intentarSync(false);
    await esperar();
    const servidor2 = crearServidor({ secciones: { mrs: { ...MRS_GUARDADO, version: 'v-guardada-por-ese-envio' } },
        alSincronizar: (c, e) => Promise.resolve(guardadoCon('v3', c, e)) });
    const segunda = await cargar({ servidor: servidor2, almacen });
    await esperar();
    assert.equal(servidor2.envios.length, 1, 'lo pendiente se reenvía al cargar');
    const b = bloqueMrs(servidor2.envios[0]);
    assert.equal(b.version_base, 'v1', 'con la versión sobre la que se respondió');
    assert.equal(b.sin_confirmar[0].pregunta_2, '2');
    assert.equal(b.datos.pregunta_2, '2');
    assert.equal(segunda.api.estado().sucio, false);
});

test('5B-3: sin pendientes, recargar adopta lo del servidor y su versión', async () => {
    const servidor = crearServidor({ secciones: { mrs: MRS_GUARDADO }, alSincronizar: (c, e) => exito(c, e) });
    const { api, almacen } = await cargar({ servidor });
    assert.equal(api.estado().versiones.mrs, 'v1');
    const servidor2 = crearServidor({ secciones: { mrs: { ...MRS_GUARDADO, version: 'v7', datos: { pregunta_1: 3 } } },
        alSincronizar: (c, e) => exito(c, e) });
    const segunda = await cargar({ servidor: servidor2, almacen });
    assert.equal(segunda.api.estado().versiones.mrs, 'v7');
    assert.equal(segunda.api.estado().respuestas.mrs.pregunta_1, 3);
    assert.equal(servidor2.envios.length, 0);
});

test('5B-3: una página restaurada por «Atrás» se recarga; una carga normal no', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { contexto } = await cargar({ servidor });
    const [alMostrar] = contexto.__oyentes.pageshow;
    alMostrar({ persisted: false });
    assert.equal(contexto.__recargas, 0);
    alMostrar({ persisted: true });
    assert.equal(contexto.__recargas, 1);
});

test('5B-3: escribir una fecha que no cambia las preguntas visibles no redibuja', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { api, cont } = await cargar({ servidor });
    // De un año antiguo a otro año antiguo las tres preguntas condicionadas siguen igual.
    api.capturar('mrs_complementario', 'fecha_ultima_menstruacion', { value: '2018', type: 'text', tagName: 'INPUT' }, 'change');
    api.render();
    cont.innerHTML = 'SIN-REDIBUJAR';
    const fecha = { value: '2017', type: 'text', tagName: 'INPUT' };
    api.capturar('mrs_complementario', 'fecha_ultima_menstruacion', fecha, 'input');
    api.capturar('mrs_complementario', 'fecha_ultima_menstruacion', fecha, 'change');
    assert.equal(cont.innerHTML, 'SIN-REDIBUJAR');
    assert.equal(api.estado().respuestas.mrs_complementario.fecha_ultima_menstruacion, '2017');
});

test('5B-3: si la fecha sí cambia lo visible, el redibujo espera a que termine el clic', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { api, cont, contexto } = await cargar({ servidor });
    api.render();
    const fecha = { value: '2018', type: 'text', tagName: 'INPUT' };   // oculta las tres preguntas condicionadas
    const presiona = cont.__oyentes.pointerdown[0];
    const suelta = contexto.__oyentes.pointerup[0];
    presiona({});
    cont.innerHTML = 'SIN-REDIBUJAR';
    api.capturar('mrs_complementario', 'fecha_ultima_menstruacion', fecha, 'change');
    assert.equal(cont.innerHTML, 'SIN-REDIBUJAR', 'con el botón presionado no se reemplaza el formulario');
    suelta({});
    await esperar();
    assert.notEqual(cont.innerHTML, 'SIN-REDIBUJAR', 'al soltar se muestran las preguntas nuevas');
    assert.doesNotMatch(api.firmaVisible(), /menstruacion_llega/);
});

test('en pantallas táctiles el redibujo también espera al clic que se simula tras soltar el dedo', async () => {
    const servidor = crearServidor({ alSincronizar: (c, e) => exito(c, e) });
    const { api, cont, contexto } = await cargar({ servidor });
    api.render();
    cont.__oyentes.pointerdown[0]({});
    contexto.__oyentes.pointerup[0]({});                    // el dedo ya se levantó
    cont.__oyentes.mousedown[0]({});                        // llega el mousedown simulado y provoca el blur
    cont.innerHTML = 'SIN-REDIBUJAR';
    api.capturar('mrs_complementario', 'fecha_ultima_menstruacion', { value: '2018', type: 'text', tagName: 'INPUT' }, 'change');
    assert.equal(cont.innerHTML, 'SIN-REDIBUJAR');
    contexto.__oyentes.mouseup[0]({});
    await esperar();
    assert.notEqual(cont.innerHTML, 'SIN-REDIBUJAR');
});

test('5B-3 (P6): una escritura local en curso no sobrevive al borrado por retiro', async () => {
    const servidor = crearServidor({
        alSincronizar: () => Promise.resolve(respuestaJson(409, { ok: false, codigo: 'participacion_anterior', error: 'x' })),
    });
    const { api, dispositivo, opciones } = await cargar({ servidor });
    await responderMrs(api, 2);
    opciones.retrasoCifrado = 40;                          // CPU ocupada: cifrar tarda más que el borrado
    api.finalizar();
    await esperar(120);
    await new Promise((r) => setTimeout(r, 200));
    assert.deepEqual([...dispositivo.crudo.keys()].filter((k) => k.startsWith('c-u1|')), []);
});
