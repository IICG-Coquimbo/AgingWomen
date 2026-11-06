# Fase 40A: revisión correctiva del diseño

*06-11-2026. Complementa `informe_fase40A.md` (SHA-256 `185c83ae…a2aee017a`), que **no se modifica**. Si este documento contradice al informe original, prevalece este. Fase de solo lectura: no se modificó Django, datos, migraciones ni modelos analíticos. Sin commit ni push.*

**Convenciones:**
- **[D]** = demostrado en el código.
- **[H]** = hipotético.
- **RC-n** = corrección de esta revisión.

---

## Resumen de cambios al plan

| N.º | Qué cambia respecto del informe original | Por qué |
|---|---|---|
| RC-1 | La validación del cierre y el MRS con nulos **se despliegan juntos** en una sola versión (40B-2). La 40B-1 ya no cambia el comportamiento del cierre | Un validador sin el cambio del MRS aceptaría los ceros fantasma como válidos |
| RC-2 | Se agrega la **confirmación del MRS** para rondas abiertas heredadas. El servidor no devuelve al cliente los ítems de filas no verificables | Sin esto, el cliente reenvía los ceros fantasma y el servidor los daría por buenos |
| RC-3 | El servidor debe **aceptar clientes antiguos** durante la transición; nunca les responde algo que los haga borrar datos | `sw.js` sirve primero el `encuesta.js` guardado en caché: el primer arranque tras un despliegue usa el cliente antiguo |
| RC-4 | Reglas obligatorias para IndexedDB: nunca borrar ni recrear el almacén, migraciones de datos solo aditivas, y ninguna limpieza borra respuestas pendientes sin una decisión expresa | El código actual crea el almacén sin comprobar si existe; subir `DB_VERSION` tal como está puede romper el cliente |
| RC-5 | Se agrega un incremento previo, **40B-0**, para separar el análisis de `models.py` | `analisis/limpieza/catalogo.py` lee `MRS.SEVERIDAD_TOTAL` y todas las clases de opciones de `models.py` mediante su árbol sintáctico. Cambiar `models.py` cambia la reproducción de la Fase 34 |
| RC-6 | Las medidas de seguridad pasan a ser **lo primero** (40S-1), separadas de la rotación, que depende de si hay datos reales (40S-2) | Lo antes posible y sin tocar secretos |
| RC-7 | Se corrigen los ejemplos y textos del MRS: 18 de 44 es **severa** con el criterio vigente y también con el de 17 o más | Inconsistencia interna |
| RC-8 | El plazo se comprueba **dentro** del bloqueo y después de la idempotencia; la semántica de error del cierre queda unificada | El diagrama original tenía una carrera y dos comportamientos contradictorios |
| RC-9 | La migración histórica no asigna fechas ni características: todo dato desconocido queda **nulo y marcado** | Evita inventar historia |

---

## 1. Coordinar el cierre de rondas con el cambio del MRS

### 1.1 El problema

- El validador de completitud del informe (Documento 3, §3.3) exige «los 11 ítems MRS con valores de 0 a 4 confirmados».
- Hoy no hay forma de saber si un ítem fue confirmado. Los ítems omitidos ya se guardan como 0, y el servidor los devuelve al cliente como respondidos (H-02).
- Si la 40B-1 se desplegara sola, como decía el plan original:
  1. Una sincronización parcial deja en 0 los ítems 6 a 11.
  2. El cliente los recibe como «Ninguna» y la usuaria finaliza.
  3. El validador ve 11 valores entre 0 y 4 y **cierra la ronda con ceros falsos**, ahora con el aval del servidor.
- Es decir: **la 40B-1 original aumenta la confianza en un resultado que puede ser falso.**

### 1.2 La solución: una sola versión para la integridad del MRS y el cierre

Estos cambios se despliegan **juntos e inseparables** (40B-2):

1. **Modelo:** los 11 ítems pasan a `null=True` y `default=None`. Campos nuevos:
   - `mrs_verificable` (booleano): `False` en las filas existentes y `True` solo cuando se cumple el punto 3;
   - `mrs_confirmado_en` (fecha y hora, nulo).
2. **Guardado:** el formulario parcial deja como nulo cualquier ítem que no venga, en las filas nuevas.
   - Si un ítem llega como `null` o `""`, se guarda `NULL`; nunca da error 500.
   - Un ítem que ya tenía valor **no se borra** porque no venga en un guardado parcial: así se conserva la semántica actual de enviar la sección completa.
3. **Verificación:** una fila pasa a `mrs_verificable = True` solo si el payload trae los **11 ítems de forma explícita** y además una de dos cosas:
   - **(a)** la fila se creó después de la migración y nunca tuvo un 0 por omisión; esto se comprueba porque todos sus ítems no nulos llegaron de forma explícita;
   - **(b)** el payload trae `"mrs_confirmacion": true`, que el cliente nuevo envía solo después de que la usuaria revisa la pantalla del MRS.
4. **Lo que el servidor envía al cliente** (`estado_ronda` y `_datos_de`):
   - de una fila **no verificable** de una ronda abierta, no se envía **ningún** ítem del MRS; se envía `mrs_requiere_confirmacion: true`;
   - los valores se conservan en la base, sin tocarlos, pero el cliente no los ve como respondidos;
   - de una fila verificable, se envían los valores no nulos, como hoy.
5. **Validador del cierre:** exige los 11 ítems **no nulos** y `mrs_verificable = True`. Si no se cumple, responde 409 `incompleta` con `{seccion: "mrs", motivo: "confirmar"}` o con la lista de ítems faltantes.
6. **Cálculo del resultado:** solo a partir de filas verificables con los 11 ítems.

**Por qué no basta solo con los nulos:** las filas existentes conservan sus 0 (RC-9). Si el servidor los siguiera devolviendo, el cliente los reenviaría como respuestas «explícitas». El punto 4 corta ese camino.

**Costo para la usuaria:** quien tenga una ronda abierta empezada antes de la versión nueva deberá volver a revisar o contestar las 11 preguntas del MRS. Es un costo pequeño y evita resultados falsos.

**Riesgo que queda:** que la usuaria confirme sin leer. Se mitiga con un texto claro («Revisa tus respuestas: algunas pueden haberse marcado automáticamente como "Ninguna"»), sin valores marcados de antemano en los ítems.

### 1.3 Compatibilidad con clientes antiguos durante la transición

| El cliente antiguo… | Respuesta del servidor nuevo | Efecto en el cliente antiguo |
|---|---|---|
| guarda sin cerrar, con el MRS parcial | 200; los ítems omitidos quedan nulos | Sin cambios |
| finaliza sin `id_cierre` | 409 `{"estado": "cliente_desactualizado"}`. No cierra, pero guarda las secciones válidas | `encuesta.js:1069-1079`: con `ok` falso conserva todo y marca el envío pendiente; **no borra nada**. Al recargar con el cliente nuevo, el cierre se rehace con `id_cierre` |
| reconcilia con una fila no verificable | Recibe el MRS sin ítems | Quedan sin responder: la usuaria debe contestarlos. Es seguro |

Ninguna respuesta del servidor nuevo cumple `res.ok && cuerpo.ok` en un cierre de un cliente antiguo, que es la única condición que hace llamar a `iniciarRondaNueva()`. Por eso **un cliente antiguo nunca borra datos por culpa del servidor nuevo**. Hay una prueba que lo verifica (P-14).

---

## 2. Seguridad: lo que va antes de cualquier dato real

### 2.1 Medidas inmediatas, independientes de que haya datos reales (40S-1)

No muestran, cambian ni rotan ningún secreto.

| N.º | Medida | Archivos | Nota |
|---|---|---|---|
| S-1 | `SECRET_KEY`, `DEBUG`, `RUT_HASH_PEPPER` y las credenciales se leen **solo del entorno** y se eliminan los valores literales por defecto del código. En desarrollo, el `.env` local (que no está en Git) recibe **los mismos valores actuales**, que la usuaria copia sin que se muestren en ningún mensaje | `settings.py`, `.env.example` (solo nombres), `docker-compose.yml` | Mueve los valores, no los rota: las sesiones y los hashes siguen funcionando. Los valores anteriores siguen en el historial de Git (§2.2) |
| S-2 | Si falta una variable obligatoria con `DEBUG` desactivado, la aplicación no arranca | `settings.py` | Evita un despliegue con valores de desarrollo |
| S-3 | `DEBUG` desactivado por defecto; activado solo si `DEBUG=1` en el entorno | `settings.py` | Hoy está fijo en `True` |
| S-4 | Perfil de producción: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`, HSTS (con un valor corto al inicio) y `SECURE_CONTENT_TYPE_NOSNIFF` | `settings.py` | Se activa solo sin `DEBUG`; no afecta al desarrollo |
| S-5 | Exigir el consentimiento en la API de escritura (H-11): 403 en JSON | `api.py` y decorador | Cambio pequeño, con prueba |
| S-6 | Registros sin datos de salud: confirmar que ningún `logger` ni `print` escribe payloads. Con `DEBUG` desactivado, las páginas de error 500 no muestran variables | Revisión + prueba | Hoy no hay registros de payloads en el servidor; en el cliente hay `console.warn(res.cuerpo)` (`encuesta.js:1070`), que solo contiene errores de validación |
| S-7 | Agregar `manage.py check --deploy` a la lista de comprobaciones | Documentación | Sin cambios de código |
| S-8 | Revisar las otras ramas remotas (`valeAW`, `Scarleth29`, `ronda3`) en busca de otros secretos. Solo se revisa si existen, sin mostrar valores | Solo lectura | Para saber si hay más que rotar |

Las medidas S-1 a S-5 cambian `settings.py` y `api.py`, que son parte de Django. **Requieren tu autorización** para la fase en que se implementen.

### 2.2 Medidas que dependen de saber si hay cuentas o registros reales (40S-2)

| Pregunta | Si **no** hay datos reales | Si **sí** los hay |
|---|---|---|
| ¿Hay alguna base (servidor, Docker de alguna integrante, respaldo) con cuentas o respuestas de personas reales? ¿Qué contiene `datos/reales/respuestas_reales.json`, que no se abrió? | Antes del primer despliegue real, generar un **`SECRET_KEY` y un pepper nuevos** y empezar con la base vacía. Las bases de desarrollo siguen con los valores anteriores, que se declaran «solo desarrollo» | Rotación con **doble hash** (`rut_hash_v2`, migración al iniciar sesión y al buscar), según el Documento 3, §3.9 del informe, y `SECRET_KEY_FALLBACKS` para la clave |
| ¿Quién tuvo acceso al repositorio y a sus clones? | Basta con rotar | Además, evaluar si hay que notificar según el protocolo de ética y la Ley 19.628 |
| ¿Hay algún servidor desplegado con estos valores? | — | Rotar en ese servidor primero, con respaldo |

**Reescribir el historial de Git** para borrar los valores no es necesario si se rotan. Además exige push forzado a todas las ramas y que cada persona vuelva a clonar. No se recomienda.

**Respaldo del pepper:** el pepper nuevo debe guardarse cifrado y fuera del servidor. Si se pierde, todas las cuentas pierden su asociación con el RUT.

---

## 3. Interpretación del MRS: inconsistencias encontradas

### 3.1 Dentro del informe de la 40A

| N.º | Dónde (informe original) | Inconsistencia | Corrección |
|---|---|---|---|
| I-1 | Documento 5, §5.1, ejemplo del componente A | «18 de 44 (moderada)». Con el criterio vigente (16 o más = severa), 18 es **severa**. También lo es con el criterio de 17 o más | El ejemplo debe decir 12 de 44 (moderada) o 18 de 44 (severa) |
| I-2 | Documento 6, §6.1, maqueta | «18 / 44 – Nivel: Moderada» | Lo mismo. Además, la maqueta usa «Nivel», que debe decir «Intensidad de las molestias que reportaste» |
| I-3 | Documento 6, §6.1, evolución | «R1 22 → R2 18»: ambas severas, y el texto «Reportaste menos molestias» no dice que siguen en el mismo tramo | La evolución debe mostrar también el tramo de cada ronda («ambas en el tramo más alto») sin calificar el cambio |
| I-4 | Documento 6, §6.3 | Dice que las diferencias de 1 o 2 puntos se muestran «sin cambios importantes» y, a la vez, que «mientras no exista [umbral], no se califican las diferencias» | Vale la segunda: **no se califica ninguna diferencia** hasta tener una fuente de diferencia mínima importante. Solo se informan la cifra y la dirección |
| I-5 | Documento 3, §3.4 | Dice que los cortes «coinciden con los indicados» y luego que parte de la literatura cita 9–16 y 17 o más. No deja claro cuál se usará en la plataforma | Ver §3.3: el criterio de la plataforma queda **sin fijar** hasta verificarlo |
| I-6 | Documento 3, §3.4 | El texto de ejemplo «Intensidad… moderada» no muestra el número | Mostrar siempre el número y el tramo juntos |

### 3.2 Entre documentos y código del proyecto

| N.º | Dónde | Lo que dice |
|---|---|---|
| I-7 | `src/apps/encuestas/models.py:375-376` | «cortes habituales del MRS; **pendiente de confirmación** de la profesora» |
| I-8 | `analisis/limpieza/informe.py:112` | «cortes de `MRS.SEVERIDAD_TOTAL` (**confirmados por la profesora el 20-10**)» |
| I-9 | `analisis/preprocesamiento/configuracion.py:21` | `CORTE_SEVERO = 16  # … (corte "severa" de Heinemann 2004)` |
| I-10 | Informe 40A, Documento 3, §3.4 | «parte de la literatura cita … 17 o más» |

I-7 e I-8 se contradicen sobre si la profesora confirmó los cortes. I-9 e I-10 se contradicen sobre qué dice Heinemann (2004). **No se puede resolver sin leer la fuente original.**

### 3.3 Decisión provisional

1. **Los umbrales históricos de las Fases 35 a 39 no cambian.** `CORTE_SEVERO = 16` y las cuatro categorías que usó el análisis quedan como **criterio del análisis**, con nombre y versión propios (`AW-ANALISIS-2026-10`).
2. **La plataforma no muestra categorías de severidad hasta verificar la fuente.** Mientras tanto, el tablero muestra el puntaje, su máximo y las dimensiones, sin tramo. El criterio de la plataforma (`CRITERIO_MRS`) queda **pendiente**, como verificación documental (§7.2).
3. Al decidir:
   - si la fuente original da 17 o más, la plataforma puede usar el criterio de la fuente y el análisis conserva 16, con la diferencia documentada en la tesis;
   - si da 16 o más, se unifican;
   - en cualquier caso, cada resultado guarda el criterio con el que se calculó.
4. **Las dimensiones** (somática, psicológica y urogenital) se muestran sin categorías hasta tener cortes con fuente.

### 3.4 El análisis depende de `models.py` (RC-5)

- `analisis/limpieza/catalogo.py:34-60` (`leer_modelos`) lee `models.py` con `ast`: obtiene `MRS.SEVERIDAD_TOTAL`, todas las clases de opciones y los campos.
- Consecuencias:
  - Si en la Fase 40 se cambia `SEVERIDAD_TOTAL`, al volver a ejecutar la limpieza de la Fase 34 cambiaría `mrs_severidad`.
  - Si en la 40B se agrega otra clase de opciones con un nombre repetido (por ejemplo, dos clases `Estado` en `RondaEvaluacion` y `ResultadoRonda`), `leer_modelos` lanza `ValueError('Clase de opciones repetida…')` y **la limpieza deja de ejecutarse**.
- **Incremento 40B-0:** fijar la entrada del análisis a la versión de `models.py` del commit `745d689`, o a una copia congelada con su huella. Toca `analisis/limpieza`, así que requiere autorización.
- **Regla mientras tanto:** toda clase de opciones nueva en `models.py` debe tener un nombre único en todo el archivo (por ejemplo, `EstadoRonda` o `EstadoResultado`).
- **Antes de cada versión de la 40B**, se ejecutan las pruebas de la limpieza (`test_*` de `analisis/preprocesamiento`), que son livianas.

---

## 4. Migración de los datos históricos

**Principio:** se conserva todo lo existente tal cual, y todo lo que no se puede saber queda **nulo y marcado**. No se deduce nada.

| Dato | Qué se hace | Lo que **no** se hace |
|---|---|---|
| Ítems del MRS existentes (con 0 posiblemente por omisión) | Se conservan sus valores; `mrs_verificable = False`; `mrs_confirmado_en = NULL` | No se convierten 0 en nulos ni se marcan como respuestas explícitas |
| Resultados de rondas cerradas con MRS no verificable | `ResultadoRonda.estado = NO_VERIFICABLE`; en el tablero, «registro anterior, no comparable» | No se calcula una categoría de severidad. No entran en la evolución |
| `RondaEvaluacion` de las rondas anteriores | Rondas 1 a `ronda_actual − 1` → `CERRADA`, `origen = RETROCARGA`. **`cerrada_en = NULL` en todas**, también en la última. `ultima_finalizacion_en` se copia a `observaciones_retrocarga.ultima_finalizacion_registrada` como dato **referencial** | No se asigna `ultima_finalizacion_en` como fecha de cierre de una ronda concreta (corrige el informe, §3.10, paso 2) |
| Quién cerró | `cerrada_por = NULL`, `cerrada_por_rol = "DESCONOCIDO"` | No se deduce de `origen_registro` |
| Ronda en curso | `ABIERTA`, `origen = RETROCARGA`; sus filas del MRS son no verificables y piden confirmación (§1.2) | — |
| Instantáneas de rondas anteriores | **No se crean.** `instantanea_disponible = False` | No se reconstruyen con la Identificación actual |
| Características anteriores (trabajo, región) | Desconocidas | No se copian los valores actuales hacia atrás |
| `version_cuestionario` de rondas anteriores | `"DESCONOCIDA_ANTERIOR_40B"` | No se asigna la versión actual |
| Rondas vacías o sin MRS | Se marcan en las observaciones (`vacia`, `sin_mrs`); quedan `CERRADA`, con una marca que la vista usa para no mostrar resultados | No se anulan ni borran automáticamente. Si se anulan después, lo decide una persona y queda un evento auditado |
| Secciones duplicadas por (participante, ronda) | La migración de verificación **se detiene** con un informe | No se elige ni se borra ninguna automáticamente |
| Fichas sin dueña (creadas por un profesional) | Igual que las demás | — |

**Antes de migrar:**
1. Respaldo completo con `pg_dump` y comprobación de que se puede restaurar.
2. Un **inventario de solo lectura** de la base: participantes, rondas, filas del MRS, duplicados, rondas vacías y cuántas filas del MRS tienen algún 0.
3. Revisión del inventario con la usuaria.
4. Migración.
5. El mismo inventario después, para comparar.

**Reversión:** las tablas nuevas se pueden quitar. El paso de los ítems a nulos solo se puede revertir mientras no exista ningún nulo; después, solo hacia adelante o restaurando el respaldo. La versión 40B-2 se despliega con el respaldo recién verificado.

---

## 5. Protección de las respuestas guardadas sin conexión

### 5.1 Reglas obligatorias del cliente

| N.º | Regla | Corrige |
|---|---|---|
| O-1 | **Ninguna operación borra respuestas pendientes** (`sucio`, `pendiente_envio`, `envio_final`) sin una decisión expresa de la usuaria en pantalla | H-07; los cambios de usuario; el cierre de sesión |
| O-2 | Si la ronda cambió en el servidor, lo pendiente se mueve a `no_enviadas[ronda]` y se avisa; nunca se reescribe la ronda cerrada | H-07 |
| O-3 | **IndexedDB:** `DB_VERSION` solo sube si hace falta una estructura nueva. `onupgradeneeded` crea los almacenes solo si no existen (`if (!db.objectStoreNames.contains('estado'))`) y **nunca** los borra | Hoy `encuesta.js:94-96` crea el almacén sin comprobar si existe: si se sube la versión tal como está, la apertura falla |
| O-4 | Los datos locales llevan `version_local` (por ejemplo, 2). Un cliente nuevo que encuentra datos de la versión 1 los **traduce sin perder nada**; si no sabe traducir un campo, lo conserva tal cual | Actualizaciones del cliente |
| O-5 | Cambio de usuario en el mismo navegador con pendientes de la cuenta anterior: no se borran. Se avisa: «Hay respuestas sin enviar de otra cuenta en este dispositivo. Inicia sesión con esa cuenta para enviarlas, o elimínalas». Mientras tanto se guardan aparte | `encuesta.js:165-166` (`limpiarEstadoLocal`) hoy las borra |
| O-6 | Al cerrar sesión: si hay pendientes, se avisa y se ofrece enviarlas primero. Si no hay, se limpian las respuestas locales | H-13, sin perder datos |
| O-7 | Al retirarse del estudio: se limpia todo lo local de esa cuenta, porque la usuaria pidió borrar sus datos | H-13 |
| O-8 | El **`id_cierre`** se genera **una sola vez** por ronda, se guarda en IndexedDB **antes** del primer envío y se reutiliza en cada reintento. Se descarta solo cuando el servidor confirma el cierre (200 `cerrada` o `repetida`) | Reintentos seguros |
| O-9 | Respuestas del servidor: 200 `cerrada` o `repetida` → nueva ronda; 409 `incompleta` → mostrar lo que falta y conservar todo; 409 `ronda_ya_cerrada` → O-2; 409 `en_espera` → conservar y mostrar la fecha; 5xx o error de red → conservar y reintentar con espera creciente | H-06 |
| O-10 | El service worker sube su versión con cada cambio. Su `activate` borra solo las **cachés de recursos** antiguas, nunca IndexedDB. Esto se documenta en el propio archivo | Actualizaciones |

### 5.2 Reintentos seguros en el servidor

1. Se busca el `id_cierre` **antes que nada**. Si ya existe para esa participante, responde 200 `repetida` con el mismo cuerpo, sin comprobar el plazo ni volver a guardar.
2. `BEGIN` y `SELECT … FOR UPDATE` sobre la Identificación.
3. **Dentro del bloqueo:** se vuelve a buscar el `id_cierre` (por si otra petición lo cerró mientras se esperaba), se comprueba el plazo, que `ronda_cliente` sea la ronda abierta, se guardan las secciones, se valida y se cierra.
4. `id_cierre` es único en la base: si dos peticiones intentan lo mismo, una gana y la otra recibe el error de unicidad y responde `repetida`.

**Semántica de error unificada** (corrige R4 y R5 del diagrama original): en una petición con `finalizar`, las secciones válidas **se guardan siempre**, como en un guardado normal. La ronda se cierra solo si no hubo errores de validación y el validador de completitud aprueba. Nunca se deshacen secciones válidas.

---

## 6. Plan corregido de la Fase 40B

### 6.1 Los incrementos

Cada uno termina con sus pruebas aprobadas y tu revisión antes de seguir.

| Inc. | Contenido | Toca Django | Cambia el comportamiento visible | Se despliega con |
|---|---|---|---|---|
| **40B-0** | Separar el análisis de `models.py` (§3.4): la limpieza lee una versión congelada; nombres únicos de clases de opciones | No (solo `analisis/limpieza`, con autorización) | No | Solo |
| **40S-1** | Seguridad inmediata S-1 a S-7 | Sí (`settings.py`, `api.py`) | Solo S-5 (consentimiento en la API) | Solo |
| **40B-1** | **Infraestructura sin cambio de comportamiento:** tablas `RondaEvaluacion` y `EventoRonda`, retrocarga (§4), verificación de duplicados, restricción única por sección (si no hay duplicados), módulo `completitud.py` **en modo observación** (registra lo que rechazaría, sin rechazar) y la invariante `ronda_actual == ronda ABIERTA` | Sí (modelos, migraciones 0020 a 0023) | **No**: el cierre sigue igual | Solo |
| **40B-2** | **Integridad del MRS y el cierre**, inseparable: §1.2 completo; validador en modo **obligatorio**; transacción, bloqueo e idempotencia (§5.2); compatibilidad con clientes antiguos (§1.3); el cliente nuevo con O-1 a O-10, `id_cierre` y pantalla de confirmación del MRS; versión 12 de la caché del service worker | Sí (modelo MRS, migración 0024, `sync.py`, `encuesta.js`, `sw.js`) | Sí | **Todo junto** |
| **40B-3** | Tablero y ficha: dejar de mostrar puntajes de rondas abiertas o no verificables (H-03); mostrar el puntaje sin categoría (§3.3) | Sí (plantillas, `historial.py`) | Sí | Solo, después de la 40B-2 |
| **40C** | Instantáneas, `ResultadoRonda` y evolución | Sí | Sí | Después de la 40B-3 |
| **40S-2** | Rotación de secretos según §2.2 | Sí | Depende | Antes del primer dato real |

**Lo que no se puede separar:** el modelo MRS con nulos, la verificación y la confirmación, el validador obligatorio, el filtro de ítems no verificables en `estado_ronda` y el cliente que envía `id_cierre` y la confirmación. Separarlos deja abierta una de dos cosas: cerrar con ceros falsos o hacer que el cliente pierda datos.

**Lo que sí puede ir por separado:** 40B-0, 40S-1, 40B-1 (porque no cambia el comportamiento) y 40B-3.

### 6.2 Pruebas para pasar de cada incremento al siguiente

| Inc. | Pruebas mínimas |
|---|---|
| 40B-0 | Las pruebas de la limpieza y la reproducción de la Fase 34 dan resultados idénticos, con la misma huella de las salidas. Cambiar `models.py` (por ejemplo, agregar una clase) no altera la limpieza |
| 40S-1 | El arranque falla sin las variables obligatorias y sin `DEBUG`; con `.env`, el desarrollo funciona igual; las sesiones existentes siguen válidas; la API rechaza escrituras sin consentimiento con 403; `check --deploy` sin advertencias críticas en el perfil de producción |
| 40B-1 | Retrocarga sobre una copia con datos: invariante en el 100 % de las fichas; sin fechas inventadas (`cerrada_en` siempre nulo en la retrocarga); la verificación de duplicados se detiene con un informe si los hay; **todas las pruebas actuales pasan sin cambios**; el modo observación registra el rechazo de `tests.py:303` sin bloquearlo; reversa limpia hasta la 0019 |
| 40B-2 | Las de la matriz original (T-01 a T-12, T-24, T-25), más las de abajo (P-1 a P-16). **Las 10 pruebas antiguas que finalizan con datos parciales se reescriben con datos completos**, y se agrega una prueba que comprueba que el payload antiguo de `tests.py:303` **ahora es rechazado** |
| 40B-3 | Una ronda abierta no muestra puntaje; una ronda no verificable muestra «no comparable»; no hay tendencia con una sola ronda; no hay categoría de severidad |

**Pruebas nuevas de esta revisión:**

| ID | Caso | Tipo |
|---|---|---|
| P-1 | MRS parcial nuevo (5 ítems) → los ítems 6 a 11 quedan `NULL`, no 0 | I |
| P-2 | `estado_ronda` sobre una fila no verificable → sin ítems del MRS y con `mrs_requiere_confirmacion` | I |
| P-3 | Cierre con una fila no verificable sin confirmación → 409 `confirmar` | I |
| P-4 | Cierre con los 11 ítems explícitos y la confirmación → 200; `mrs_verificable` verdadero | I |
| P-5 | Los 11 ítems en 0 explícitos en una fila nueva → verificable, total 0 | I |
| P-6 | Un guardado parcial no borra un ítem que ya tenía valor | I |
| P-7 | Un ítem `null` o `""` se guarda como `NULL`, sin error 500 | U/I |
| P-8 | Un cliente antiguo finaliza sin `id_cierre` → 409 `cliente_desactualizado`; las secciones válidas se guardan; no cierra | I |
| P-9 | El mismo `id_cierre` en dos peticiones simultáneas → un `cerrada` y un `repetida` | C |
| P-10 | Un `id_cierre` repetido dentro del plazo → `repetida` (no `en_espera`) | I |
| P-11 | La migración 0024 conserva todos los valores existentes (comparación fila a fila antes y después) | I |
| P-12 | Retrocarga: ninguna `cerrada_en` deducida; `version_cuestionario` desconocida | I |
| P-13 | IndexedDB: un cliente nuevo abre datos de la versión 1 sin perder nada; subir `DB_VERSION` no borra el almacén | E2E |
| P-14 | Un cliente antiguo (con la caché anterior del service worker) frente al servidor nuevo: guarda, finaliza (recibe 409), recarga y cierra con el cliente nuevo, **sin perder ninguna respuesta** | E2E |
| P-15 | Cambio de usuario y cierre de sesión con pendientes → aviso; nada se borra sin una decisión | E2E |
| P-16 | Cambiar `models.py` no altera la limpieza de la Fase 34 (40B-0) | U |

Las pruebas E2E son manuales, con una lista documentada, porque el proyecto no tiene framework de pruebas para JavaScript. Las pruebas de concurrencia (C) necesitan PostgreSQL real y `TransactionTestCase`.

---

## 7. Decisiones pendientes

### 7.1 Decisiones técnicas que recomiendo con fundamento

| N.º | Recomendación | Fundamento |
|---|---|---|
| DT-1 | Arquitectura híbrida: tablas relacionales + instantánea JSON inmutable | Informe, Documento 3, §3.5 |
| DT-2 | El MRS con nulos, verificación y confirmación, desplegado junto con el validador | §1 |
| DT-3 | Idempotencia con `id_cierre` y el plazo comprobado dentro del bloqueo | §5.2 |
| DT-4 | Retrocarga sin fechas ni características deducidas | §4 |
| DT-5 | Clientes antiguos rechazados con 409, sin perder datos | §1.3 |
| DT-6 | El catálogo educativo como archivo versionado en el repositorio | Informe, Documento 5 |
| DT-7 | No integrar el modelo A; no mostrar grupos (A ni B1) a la usuaria (**decisión provisional vigente**) | Informe, Documento 4 |
| DT-8 | Medidas de seguridad 40S-1 antes de la 40B | §2.1 |
| DT-9 | Separar el análisis de `models.py` antes de tocar los modelos (40B-0) | §3.4 |
| DT-10 | Mostrar el MRS sin categoría de severidad hasta verificar la fuente | §3.3 |

### 7.2 Lo que requiere verificar documentos

| N.º | Qué verificar | Fuente | Bloquea |
|---|---|---|---|
| DV-1 | Los cortes del MRS total (16 o más frente a 17 o más) y los de cada dimensión | Heinemann et al. (2004) y el manual del MRS, en la versión original | Las categorías en el tablero (no la 40B) |
| DV-2 | Si la profesora confirmó los cortes el 20-10 (I-8) o siguen pendientes (I-7) | Actas o correos de la reunión del 20-10 | DV-1 |
| DV-3 | Números vigentes de Salud Responde y de la línea de prevención del suicidio | MINSAL | El mensaje de apoyo (40D) |
| DV-4 | Las fuentes candidatas del catálogo y su vigencia | MINSAL, OMS, NICE y The Menopause Society | 40D |
| DV-5 | Si existe una diferencia mínima importante para el MRS | Literatura del MRS | La calificación de la evolución (se mantiene desactivada) |

### 7.3 Lo que requiere información real del proyecto

| N.º | Pregunta | Quién responde | Bloquea |
|---|---|---|---|
| DR-1 | ¿Hay bases con cuentas o respuestas reales? ¿Qué contiene `datos/reales/`? | Tú o la responsable | 40S-2 (estrategia de rotación) y el riesgo de la migración |
| DR-2 | ¿Hay algún servidor desplegado? ¿Dónde se alojará (pendiente desde la Fase 18)? | Tú o la profesora | 40S-2 y el despliegue |
| DR-3 | ¿Quién tiene acceso a la organización `IICG-Coquimbo` y a sus clones? | Tú | La evaluación de la exposición |
| DR-4 | ¿Se acepta que las rondas abiertas heredadas pidan volver a confirmar el MRS? | Tú o la responsable | 40B-2 |
| DR-5 | ¿Entra la comuna en la instantánea? | La responsable (y el comité de ética) | 40C |
| DR-6 | El texto del mensaje de apoyo y si el profesional ve una marca | La responsable, salud mental y el comité de ética | 40D |
| DR-7 | ¿Se autoriza la 40B-0 (cambia `analisis/limpieza`)? | Tú | 40B-1 |
| DR-8 | ¿Hay otra integrante trabajando en `valeAW` que vaya a cambiar `models.py` o `sync.py`? | Tú | El orden de las migraciones (choques con la 0020) |

---

## 8. Riesgos que quedan después de esta revisión

| Riesgo | Situación | Mitigación |
|---|---|---|
| La usuaria confirma el MRS sin revisarlo | Queda | Texto claro, sin respuestas marcadas de antemano, y el evento de confirmación registrado |
| Una persona no vuelve a abrir la encuesta y su cliente antiguo queda con un cierre pendiente para siempre | Queda | Al volver a abrirla se actualiza; los datos no se pierden; se puede contar desde el servidor |
| Las pruebas E2E del cliente son manuales | Queda | Lista documentada; se puede evaluar Playwright más adelante |
| Valores de secretos en el historial de Git | Queda hasta la rotación (40S-2) | Rotar antes de los datos reales; no reescribir el historial |
| Los cortes del MRS siguen sin fuente verificada | Queda | La plataforma no muestra categorías hasta DV-1 |
| Choques de migraciones con la rama `valeAW` | Queda | DR-8 antes de crear la 0020 |
| Rondas antiguas no verificables, que nunca serán comparables | Aceptado | Se informan como «no comparables»; no se reconstruyen |

---

## 9. Integridad

- Solo se creó este archivo (`analisis/fase40/40A_auditoria/01_revision_correctiva_40A.md`).
- `informe_fase40A.md` no se modificó: su SHA-256 se comprueba al cerrar esta revisión.
- No se tocaron Django, datos, migraciones, scripts ni artefactos analíticos.
- No se ejecutaron análisis ni pruebas. Solo hubo lecturas y búsquedas de texto.
- Sin commit ni push.
