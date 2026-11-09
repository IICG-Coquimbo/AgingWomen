# Fase 40 — Privacidad, consentimiento y seguridad offline (informe único)

Fecha: 2026-11-06 · Rama `datos-simulados` · Sin commit ni push · Sin migraciones · Base de desarrollo no modificada.

## 1. Cambios

### 1.1 Dispositivo: cierre de sesión e IndexedDB (P1, P2, P3, P5)

| Cambio | Dónde |
|---|---|
| Todo lo que la encuesta guarda en IndexedDB va **cifrado con AES-GCM** (WebCrypto), en un espacio por cuenta. En modo profesional hay además un espacio por paciente | `static/js/encuesta.js` (IndexedDB versión 2) |
| La clave la entrega el servidor **solo con sesión iniciada** (`/api/clave-local/`, `no-store`, 401 sin sesión). Se deriva de `SECRET_KEY`, la cuenta y su participación. En el navegador se guarda como clave no exportable y vence con la sesión | `apps/usuarios/privacidad.py`, `apps/encuestas/api.py` |
| **«Salir»** sin pendientes: borra la clave y la copia offline de `/encuesta/`, avisa a las otras pestañas y cierra la sesión en el servidor | `static/js/sesion.js` (nuevo), `base.html` |
| **«Salir» con pendientes**: diálogo con cuatro opciones: «Enviarlas ahora», «Salir y conservarlas protegidas», «Descartarlas y salir» (pide confirmación y advierte que no se pueden recuperar) y «Cancelar». Nunca se borra en silencio | `sesion.js` |
| Lo conservado queda **cifrado y sin clave** en el dispositivo. Nadie lo puede leer ni editar hasta que esa misma cuenta vuelva a entrar; entonces se envía | — |
| **Sin conexión:** la salida se completa en el dispositivo y queda anotada (con la cuenta) para cerrar la sesión en el servidor apenas vuelva la red | `sesion.js` |
| Si una página llega del servidor, se borran las claves de cuentas sin sesión (por ejemplo, una sesión vencida). Sin sesión, también se borra la copia de `/encuesta/` | `sesion.js` |
| El Service Worker ya no sirve la encuesta de la persona anterior. Sin conexión y sin copia responde «Sin conexión…». Caché v17 | `static/js/sw.js` |
| **Retiro en el dispositivo:** borra solo los datos de esa cuenta (no los de otras) y avisa a las otras pestañas. Ya no se bloquea con otra pestaña abierta (P5) | `encuestas/retirado.html` |

La versión 1 de IndexedDB guardaba todo en claro. Al actualizarse, ese contenido se **vacía una sola vez**. En este momento solo había datos de prueba.

### 1.2 Retiro y nueva participación (P6)

- **Identificador de participación:** es el momento en que se aceptó el consentimiento (`consentimiento_aceptado_en`, que ya existía). El retiro lo borra y un consentimiento nuevo crea otro valor. No se guarda nada nuevo ni datos de salud.
- **El cliente** envía `participacion` en cada sincronización. El servidor rechaza sin escribir nada:
  - un envío sin participación → 409 `cliente_desactualizado`;
  - un envío con la participación anterior → 409 `participacion_anterior`.
- **Al detectarlo** (409, o un cambio de participación al cargar), el cliente borra de ese dispositivo lo de la participación retirada. Además, la clave cambia, así que lo cifrado con la anterior queda ilegible.
- **El retiro en el servidor** sigue igual: borra la ficha y, en cascada, las respuestas, las rondas y los resultados. La reincorporación exige un consentimiento nuevo y parte sin ficha, desde la ronda 1.

### 1.3 Acceso profesional y consentimiento (P7, R-2)

- Si el RUT o la ficha corresponden a una **cuenta de usuaria sin consentimiento vigente** (retirada o que nunca aceptó), la profesional no puede registrar ni modificar. Esto se revisa en:
  - la sincronización (409 `consentimiento_paciente`);
  - `nueva_paciente` y `encuesta_paciente` (403);
  - `/api/ronda-actual/?paciente=` (403).

  La consulta de la ficha existente no cambia.
- **Registro presencial sin cuenta:** sigue permitido, como en la Fase 29.
- **Búsqueda por RUT** en `/profesional/buscar/` y en `/administracion/`:
  - pasa a **POST con CSRF** y con `autocomplete="off"`;
  - por GET el RUT se ignora;
  - el resultado enlaza por el id de la ficha o de la cuenta.

  Las vistas de destino conservan sus permisos (profesional o superusuario), y ahora también se revisa el consentimiento.

### 1.4 Pruebas existentes ajustadas

Las pruebas que envían como usuaria con consentimiento ahora incluyen la participación vigente, igual que el cliente real. Para eso usan `con_participacion` y `sincronizar_como_cliente`, en `apps/rondas/pruebas_comunes.py`.

Las búsquedas por RUT de las pruebas pasan a POST. En los casos en que la profesional escribe por una paciente con cuenta, esa paciente tiene consentimiento. La versión del Service Worker que verifica `test_40c` pasa a v17. No se relajó ninguna aserción de comportamiento.

## 2. Pruebas ejecutadas

| Conjunto | Resultado |
|---|---|
| Django, suite completa | **354/354 OK** (1 omitida, ya existente: `analisis/` no está montado en Docker) |
| Nuevas de servidor, `apps/usuarios/test_privacidad.py` | 13/13 (incluidas en las 354) |
| JavaScript, `pruebas_js` | **18/18**, 5 ejecuciones seguidas. Hay 6 pruebas nuevas: sin clave offline, 401, otra pestaña, 409 de participación, participación nueva y 409 de la paciente. La de cambio de cuenta se reescribió |
| Integridad 40B-0 | 15/15 |
| Protección histórica 40B-1 | OK: 6.457 artefactos por huella; Fases 34–39 sin cambios |
| **Chrome real sin interfaz** | **26/26 OK** (`evidencias_privacidad/resultados_navegador_privacidad.json`) |

**Entorno del navegador:**
- base PostgreSQL nueva y vacía, en el puerto 127.0.0.1:8010;
- secretos aleatorios, solo en variables del contenedor;
- cuentas `@ficticio.cl`.

Al terminar se eliminaron los contenedores, el volumen, la red y el perfil del navegador.

**Comprobado en Chrome:**
- IndexedDB cifrado, sin texto en claro;
- salir con conexión: clave y copia offline borradas, y sesión cerrada en el servidor (401);
- otra pestaña deja de mostrar los datos;
- diálogo con pendientes:
  - «enviar» sin red avisa y no borra;
  - «conservar» deja los datos cifrados y sin clave;
- con el servidor detenido, `/encuesta/` no muestra nada de la cuenta anterior;
- al volver la red, la sesión se cierra en el servidor;
- al volver a entrar, lo conservado se envía (valor 4 en el servidor);
- cambio de cuenta sin datos ajenos;
- «descartar» borra solo los datos de esa cuenta;
- en móvil (390 px), el tablero y el diálogo no desbordan;
- retiro:
  - limpia el dispositivo;
  - el servidor queda con 0 fichas y 0 MRS;
  - el consentimiento nuevo queda aceptado;
  - el dispositivo 2 desactualizado no recrea nada (0 en el servidor) y abre la participación nueva vacía;
- búsqueda profesional sin RUT en la URL;
- registro rechazado para una cuenta sin consentimiento;
- tablero con grupo («Grupo 4 — Entre múltiples actividades»), MRS, orientaciones con aviso de borrador y evolución;
- consola sin errores.

**Corrección hecha durante la prueba:** una salida sin red de la cuenta B dejaba una marca que, al entrar A, cerraba la sesión de A. Ahora la marca guarda la cuenta.

En la primera versión del script, dos comprobaciones de reingreso pasaban **sin haber aceptado realmente** el consentimiento. Se corrigió el script, se agregaron verificaciones explícitas y se repitió todo desde una base limpia.

## 3. Riesgos

| Riesgo | Estado |
|---|---|
| P1 Datos legibles o editables tras «Salir» y copia offline | **Resuelto** |
| P2 Datos apartados en claro al cambiar de cuenta | **Resuelto**: espacio por cuenta y cifrado |
| P3 Borradores de pacientes en el equipo de la profesional | **Resuelto**: cifrados con la clave de la profesional, que se borra al salir |
| P5 Mensaje del retiro con otra pestaña abierta | **Resuelto** |
| P6 Dispositivo desactualizado recrea datos retirados | **Resuelto** (servidor y cliente) |
| P7 Ficha de una retirada creada por la profesional | **Resuelto** |
| R-2 RUT en la URL | **Resuelto** en las dos búsquedas |

**Pendientes:**
1. **Constancia mínima del retiro** (sin datos de salud, según la adenda): no está implementada, porque requiere una migración y definir qué exige la ley conservar. El mecanismo de participación no la necesita.
2. **Consentimiento presencial:** no queda registrado (DC pendiente). Por eso una mujer **con cuenta** que nunca aceptó en línea tampoco puede ser registrada por la profesional. Hay que decidir si eso es lo correcto.
3. **Lo conservado tras «Salir»** solo lo puede recuperar la misma cuenta y en ese dispositivo. Si la sesión vence, se conserva cifrado hasta que vuelva a entrar.
4. **Al cerrar el navegador sin «Salir»** la sesión sigue vigente (dos semanas, como antes), y con ella la clave local. Es el mismo nivel de acceso que tiene la cuenta abierta. El vencimiento depende del reloj del dispositivo.
5. **Rotar `SECRET_KEY` (40S-2)** deja ilegibles los borradores locales que no se hayan enviado. Hay que avisarlo antes de rotarla.
6. **Clientes ya cacheados** con el `encuesta.js` antiguo reciben 409 `cliente_desactualizado` hasta que recargan. No escriben nada.
7. **Una salida sin red seguida del ingreso de otra cuenta** deja la sesión anterior vigente en el servidor hasta que vence. Ya no está en ese dispositivo.
