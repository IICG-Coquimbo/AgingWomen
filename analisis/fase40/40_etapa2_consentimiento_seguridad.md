# Fase 40, Etapa 2 — Consentimiento y seguridad complementaria (informe único)

Fecha: 2026-11-07 · Rama `datos-simulados` · Sin commit ni push · `SECRET_KEY` sin rotar · Fases 34–39 intactas.

**La base de desarrollo no se modificó, pero la migración nueva no está aplicada en ella** (detalle en §4).

## 1. Consentimiento presencial verificable — implementado

**Modelo nuevo:** `ConsentimientoPresencial` (app `usuarios`, migración `0004`). Hay una fila por persona, identificada por `rut_hash` único, con:

- fecha y hora de la aceptación;
- **versión** del consentimiento: huella SHA-256 del texto mostrado;
- modalidad `PRESENCIAL`;
- profesional responsable (FK `PROTECT`);
- **folio** del documento firmado (único);
- **custodia** del documento;
- tipo de verificación.

No se guardan fotografías, documentos, datos clínicos ni la contraseña.

**Qué acredita la aceptación** (`/profesional/consentimiento-presencial/`, solo por POST, solo profesionales y sin caché):

- **siempre:** folio válido y no usado antes, lugar de custodia y la declaración de la profesional de que la participante leyó, aclaró sus dudas y firmó en su presencia;
- **si la persona tiene cuenta:** además, **su propia contraseña**, escrita por ella. Esto impide que una profesional reactive sola un consentimiento retirado.

**Al registrar el consentimiento de una persona con cuenta:**

- cambia `consentimiento_aceptado_en`, así que se crea una **participación nueva**: no se recupera nada de la anterior;
- los envíos que quedaron en cola de la participación retirada siguen rechazados (409 `participacion_anterior`).

**Una sola regla:** `sin_consentimiento_vigente(rut_hash, usuario_id)` en `privacidad.py`.

- Con cuenta: vale su consentimiento vigente, dado en línea o presencialmente.
- Sin cuenta: hace falta el consentimiento presencial registrado.
- La usan la sincronización (409 `consentimiento_paciente`), `nueva_paciente`, `encuesta_paciente`, `/api/ronda-actual/` y el buscador.
  - El buscador ofrece «Registrar consentimiento presencial» y ya no ofrece registrar la ficha sin él.

**Sin fichas duplicadas:** la ficha sigue siendo única por `rut_hash`.

**Tablero 40C-P:** incluye registros presenciales sin cuenta solo si tienen su consentimiento presencial registrado. La agregación y el umbral k = 5 no cambian.

**Cambio de comportamiento:** desde ahora, la profesional ya **no** puede registrar respuestas de una persona sin cuenta sin antes registrar su consentimiento presencial. Antes podía (Fase 29).

## 2. Constancia mínima del retiro — implementado lo seguro; persistencia pendiente

**Lo que se revisó:**
- La adenda de la 40S-1 (retiro = borrar todo + «constancias mínimas sin datos de salud») **no fija un plazo ni una base legal de conservación**.
- La 40A tampoco. Solo menciona evaluar la Ley 19.628.

Por eso **no se creó ninguna tabla de constancias** ni se guardan identificadores después del retiro.

**Implementado:**
- **El retiro sigue igual:** borra la ficha y, en cascada, respuestas, rondas, resultados y eventos. Además borra el consentimiento presencial de la persona.
- **Comprobante para la participante:** al retirarse recibe un **comprobante firmado** (`django.core.signing`) que el servidor **no guarda**.
  - **Contiene:** código aleatorio, fecha y hora, versión del consentimiento y una huella con clave del RUT pseudonimizado. Ningún dato de salud.
  - **Verificación:** `python manage.py verificar_constancia_retiro <comprobante> --rut <RUT>`.
  - **Rotación de claves (Etapa 4):** dejar la clave anterior en `SECRET_KEY_FALLBACKS`, o los comprobantes ya emitidos dejan de poder verificarse.
- **Se mantiene** la protección contra sincronizaciones de una participación retirada.

**Pendiente de aprobación:** guardar la constancia en el servidor. Hay que decidir qué campos, por cuánto tiempo y con qué base legal. Si se aprueba, basta con persistir en una tabla aparte los mismos campos que hoy lleva el comprobante.

## 3. Cierre de sesión por inactividad — implementado

**Servidor** (`apps/usuarios/inactividad.py`, middleware):

- **Límite:** `SESION_INACTIVIDAD_SEGUNDOS`, 1800 por defecto y configurable por entorno (documentado en `.env.example`).
- **Al vencer:** la sesión se cierra en el servidor antes de atender la solicitud.
  - páginas: redirigen a `/cuenta/ingresar/?inactividad=1`;
  - API: responde 401 `sesion_vencida`.
- **Qué cuenta como actividad:** la carga de páginas, los formularios y el aviso `/cuenta/actividad/`, que se envía **solo ante interacción real** (teclado, toque o clic), como mucho una vez por minuto.
- **Qué no cuenta:** las solicitudes automáticas de la encuesta (clave, esquema, ronda y sincronización) llevan `X-Segundo-Plano: 1` y no extienden la sesión.
- **Abandono:** una sesión abandonada vence aunque el navegador esté cerrado.

**Navegador** (`sesion.js`):

- **Aviso previo** «¿Sigues ahí?» (`SESION_AVISO_SEGUNDOS`, 120 por defecto) con el botón «Seguir conectada».
- **Al vencer:**
  - se borran la clave local y la copia sin conexión;
  - lo pendiente **queda cifrado**, nunca se descarta;
  - se avisa a las otras pestañas, que dejan de mostrar datos;
  - se va al ingreso con un aviso.
- **Recuperación:** al ingresar de nuevo con la misma cuenta, lo pendiente se envía.
- **Varias pestañas:** comparten la marca de actividad.
- **Sin conexión:**
  - la interacción cuenta solo en el dispositivo;
  - al vencer, se bloquea localmente;
  - al volver la red, el servidor aplica su propio límite.
- **Margen:** el navegador vence 45 s antes que el servidor, para no mostrar una sesión que el servidor ya cerró.
- **«Salir»:** el diálogo voluntario no cambió.
- **Caché:** el Service Worker pasa a v19.

## 4. Migraciones

| Migración | Contenido | Estado |
|---|---|---|
| `usuarios/0004_consentimiento_presencial` | Crea la tabla `ConsentimientoPresencial`. No modifica tablas ni datos existentes | **Aplicada y probada solo en bases aisladas**: la de pruebas de Django y la del navegador. **No aplicada en desarrollo** |

**Hasta que se aplique en desarrollo**, con un respaldo verificado y autorización, en el servidor de desarrollo:
- **dejan de funcionar** el buscador profesional, el registro presencial, las estadísticas, el retiro y la sincronización de la profesional, porque la tabla no existe;
- el resto sigue igual.

**Efecto en los datos al aplicarla:**
- los registros presenciales sin cuenta que ya existen **no se modifican**;
- para registrar respuestas nuevas de esas personas, o para que entren al tablero, hay que registrar su consentimiento presencial.

## 5. Pruebas

| Conjunto | Resultado |
|---|---|
| Django, suite completa | **370/370 OK** (1 omitida, ya existente) |
| Nuevas, `apps/usuarios/test_etapa2.py` | 10/10 (incluidas en las 370) |
| JavaScript, `pruebas_js` | 18/18 |
| Integridad 40B-0 y protección histórica 40B-1 | 20/20 (Fases 34–39 intactas) |
| **Chrome real**, entorno aislado | **23/23** (`evidencias_etapa2/resultados_navegador_etapa2.json`) |

**Qué cubren las 10 pruebas nuevas:**
- consentimiento sin folio, custodia o declaración → rechazado;
- folio inválido o repetido → rechazado;
- registro válido;
- sin fichas duplicadas;
- permisos: anónima, usuaria común y solo POST;
- retiro: borra los datos de salud y entrega un comprobante verificable;
- la profesional no reactiva un retiro sin la contraseña de ella;
- participación nueva y 409 para la anterior;
- la contraseña no se guarda;
- inactividad: la marca al ingresar; el vencimiento en páginas y en la API; que el segundo plano no extiende y la actividad sí; el límite configurable.

**Entorno de Chrome:**
- base PostgreSQL nueva, migración aplicada solo allí, secretos aleatorios y cuentas `@ficticio.cl`;
- límite de 100 s y aviso a los 40 s;
- se eliminó al terminar.

**Comprobado en Chrome:**
- consentimiento presencial:
  - con cuenta (contraseña incorrecta rechazada; correcta registrada);
  - sin cuenta, seguido de la encuesta profesional;
  - el RUT nunca aparece en la URL;
- inactividad:
  - aviso a los 14 s;
  - «Seguir conectada»;
  - el segundo plano no extiende la sesión;
  - vencimiento a los 59 s: ingreso, pestaña sin conexión bloqueada, clave y copia borradas, 9 registros cifrados conservados y 401 en el servidor;
  - sesión abandonada cerrada por el servidor;
- otra cuenta en el mismo dispositivo sin ver datos ajenos;
- **borrador recuperado y enviado** al volver a ingresar (valor 4 en el servidor);
- retiro con comprobante verificable;
- consola sin errores.

**Pruebas antiguas ajustadas:** las que registraban personas sin cuenta ahora registran antes un consentimiento presencial ficticio (`pruebas_comunes.consentimiento_presencial`). La prueba «registro presencial sin cuenta sigue permitido» pasa a verificar que **exige** el consentimiento. No se relajó ninguna aserción.

## 6. Decisiones pendientes

1. **Aplicar `usuarios/0004` en desarrollo:** requiere respaldo verificado y autorización.
2. **Persistir la constancia del retiro:** campos, plazo y base legal.
3. **Retiro de una persona sin cuenta:** hoy no existe un flujo para que la profesional lo registre. Hay que definirlo (por ejemplo, con un documento de revocación).
4. **Registros presenciales anteriores:** su consentimiento debe registrarse con su folio, si existe.
5. **Validación ético-jurídica:** del formulario presencial y del texto del comprobante.
6. **Etapa 4:** rotar `SECRET_KEY` con `SECRET_KEY_FALLBACKS`.
7. **Límite de intentos:** no se agregó uno para la contraseña en el formulario presencial (limitación conocida).
