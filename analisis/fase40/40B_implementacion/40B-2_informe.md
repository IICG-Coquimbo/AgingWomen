# Fase 40B-2 — Corrección del MRS y cierre seguro de las encuestas

**Fecha:** 2026-11-06 · **Rama:** `datos-simulados` · **HEAD:** `573d3a3`. Sin commit, sin push y sin cambios de rama: todo lo de la Fase 40 sigue local hasta cerrarla completa.

**Resumen.**

- **MRS:** los 11 ítems distinguen ahora entre un 0 elegido («Ninguna»), una respuesta ausente (nulo) y un valor de 1 a 4.
- **Cierre:** una ronda solo se cierra si están completas las respuestas obligatorias que le corresponden. El cierre es transaccional, idempotente y registra quién cerró.
- **Rechazos:** un cierre incompleto se rechaza sin perder lo guardado, y una solicitud que llega tarde no escribe nada.
- **Cliente offline:** nunca descarta respuestas pendientes de IndexedDB; si no puede enviarlas, las aparta.
- **Datos existentes:** ninguna respuesta histórica se modificó. Los 30 ceros guardados antes de esta fase quedaron marcados como no verificables:
  - 8 son de rondas cerradas y quedan como historia no verificable;
  - 22 son de rondas abiertas y deben confirmarse en la encuesta antes de cerrarlas.
- **Base de desarrollo:** se migró tras un respaldo restaurado y verificado.
- **Pruebas:** Django 266/266, cliente 11/11 y todas las pruebas históricas en verde.

> **Para revisar con atención (§9):** la prueba de protección de las Fases 34–39 **ya fallaba antes de esta fase** por 3 archivos de análisis cambiados con anterioridad. Eso contradice el «3/3 OK» que declara el informe 40B-1. No toqué ninguno de esos archivos: los dejé registrados como excepciones con su huella exacta, a la espera de revisión.

---

## 1. Diagnóstico previo

| Punto revisado | Hallazgo |
|---|---|
| `default=0` del MRS | Los 11 ítems (`pregunta_1`…`pregunta_11`, `models.py`) tenían `default=IntensidadMolestia.NINGUNA` y `NOT NULL`. En la base **no había valor por defecto**: el 0 lo ponía Django al crear la fila. Un ítem omitido en un guardado parcial quedaba en 0 y volvía al cliente como respondido. |
| Puntaje | `MRS.puntaje_total` sumaba los 11 ítems siempre, así que los ceros fantasma «completaban» el puntaje. El tablero y la ficha profesional lo mostraban también para la ronda en curso. |
| Cierre (`finalizar: true`) | `sync.py` avanzaba `ronda_actual` si no había errores de validación, **sin revisar la completitud**: bastaba un MRS de un ítem (lo exigía `tests.py:303`). No había transacción ni bloqueo, ni idempotencia. La 40B-1 solo observaba el cierre por medio de una señal. |
| Solicitudes tardías | Un guardado tardío con `uuid_local` nuevo caía en la ronda **nueva** (`_guardar_seccion` busca por `ronda_actual`). Así, respuestas de la ronda 1 podían terminar en la ronda 2. |
| Cliente offline | `reconciliar()` descartaba las respuestas pendientes al detectar un cambio de ronda. `limpiarEstadoLocal()` borraba lo pendiente de la persona anterior y no reiniciaba la ronda local. El 403 de la 40S-1 se trataba como un error genérico (los datos se conservaban). Los fallos de escritura en IndexedDB quedaban sin manejar. |
| Pruebas que dependían del defecto | 19 llamadas de prueba usaban el cierre incompleto como paso previo. Además, `test_mrs_en_dos_bloques…` afirmaba que un ítem omitido «conserva el default 0». |
| Dependencias del análisis en `models.py` | `test_revision_35b` (expresiones regulares sobre clases de opciones), `catalogo.leer_*_plataforma` (lectura AST, solo para auditoría), `test_40b0 test_plataforma_sin_cambios` y `test_40b1_no_modifica_models`. La limpieza congelada (40B-0) no lee `models.py`. |
| Duplicado en Hábitos de vida | Sigue 1 par (ronda abierta). **No se tocó** y sigue fuera del índice único. |
| Base de desarrollo | Se trató como sensible (DR-1 sigue abierto). Solo se leyeron conteos agregados y no se abrió ninguna respuesta individual. Ninguna prueba destructiva se ejecutó sobre ella: las pruebas usan la base temporal de Django. |

**Impacto de pasar los MRS a nulo** (auditoría agregada, solo lectura):

| | Filas MRS | Con algún 0 | Todo en 0 | Ítems en 0 |
|---|---|---|---|---|
| Rondas abiertas | 3 | 2 | 2 | 22 |
| Rondas cerradas | 4 | 2 | 0 | 8 |

Las 2 filas abiertas enteramente en 0 son, muy probablemente, ceros fantasma de un guardado del cuestionario complementario. Aun así no se adivina: ningún 0 se convierte.

**Conclusión del diagnóstico:** se podía continuar sin riesgo de perder datos. La migración del esquema solo quita `NOT NULL` (no reescribe filas), y lo nuevo vive en tablas nuevas.

## 2. Respaldo y restauración

| Paso | Resultado |
|---|---|
| Respaldo `pg_dump -Fc` antes de migrar | `C:/Users/scarl/Respaldos_AgingWomen/django_db_antes_40B-2_20261106_104334.dump` (92.413 bytes) más `.sha256` (`220357ed…`). Fuera del repositorio, con permisos para SYSTEM, Administradores y la cuenta de la usuaria. |
| Restauración en un entorno aislado | Contenedor PostgreSQL 15 sin red y luego en una red interna sin salida: **22/22 tablas idénticas** al original (huella `md5` del contenido por tabla). |
| Ensayo de las migraciones sobre la copia | Hacia adelante: OK. Reversa: se niega, como estaba previsto (§4). Sobre la copia solo cambian `auth_permission`, `django_content_type` y `django_migrations`, y aparece `rondas_mrsanterior40b2` (7). Las 16 tablas de respuestas y cuentas quedan idénticas. |
| Base real | Se comprobó idéntica al respaldo justo antes de migrar y se migró. El resultado es igual al de la copia ensayada (salvo la hora de registro de las marcas). `verificar_rondas`: **problemas: 0**. Filas MRS con nulos: 0. MRS: 7; marcas: 7. |
| Limpieza | Se eliminaron los contenedores, la red y los 2 volúmenes anónimos de las copias (creados hoy a las 10:44 y 11:11). Quedan solo `agingwomen-web-1`, `agingwomen-db-1` y el volumen del proyecto. |

**Vuelta atrás:** las migraciones nuevas se niegan a revertirse si eso borraría información (§4). La vuelta atrás segura es **restaurar el respaldo anterior a la 40B-2**.

## 3. Archivos

### Nuevos

| Archivo | Contenido |
|---|---|
| `src/apps/encuestas/migrations/0020_mrs_items_sin_respuesta_nulos.py` | Los 11 ítems pasan a `null=True, default=None`. La reversa se niega si hay nulos. |
| `src/apps/rondas/migrations/0004_mrs_anterior_40b2.py` | Tabla `MRSAnterior40B2` y una marca por cada MRS existente. La reversa se niega si hay marcas. |
| `src/apps/rondas/cierre.py` | Servicio de cierre validado e idempotente; puntaje definitivo. |
| `src/apps/rondas/proteccion.py` | Barrera `pre_save`: las rondas cerradas no se modifican. |
| `src/apps/rondas/pruebas_comunes.py` | Ayuda para pruebas: completa lo obligatorio y usa el protocolo 2 (no es código de la plataforma). |
| `src/apps/rondas/test_40b2.py` | 36 pruebas nuevas (§7). |
| `src/apps/encuestas/pruebas_js/test_encuesta_sync.mjs` | 11 pruebas del cliente con Node (`node --test`), sin dependencias externas. |
| `src/apps/encuestas/pruebas_js/esquema_usuaria.json`, `esquema_profesional.json` | Esquema real exportado de `construir_esquema`. Una prueba de Django exige que siga al día. |
| `analisis/fase40/40B_implementacion/40B-2_informe.md` | Este informe. |

### Modificados

| Archivo | Cambio |
|---|---|
| `src/apps/encuestas/models.py` | Solo dos cosas: los 11 ítems MRS (`null=True, default=None`, siguen `blank=False`), y `puntaje_total` devuelve `None` si falta un ítem, con la nueva propiedad `items_sin_responder`. Las clases de opciones, los cortes `SEVERIDAD_TOTAL` y el resto del archivo no cambian (lo comprueba §6). |
| `src/apps/encuestas/sync.py` | Protocolo 2 (§5), transacción con bloqueo de la ficha, control de ronda, reintento idempotente, cierre por medio de `apps.rondas.cierre`, un punto de guardado por sección, confirmación de ceros antiguos y `estado_ronda` con `mrs_por_confirmar`. |
| `src/apps/encuestas/api.py` | `ConflictoRonda` → **409** en JSON. |
| `src/static/js/encuesta.js` | Protocolo 2, `id_cierre` persistente, manejo de 409, 403 y cierre rechazado, conflictos apartados en IndexedDB, respaldo por cuenta, aviso de ceros por confirmar, aviso si IndexedDB falla y «suma parcial» en la burbuja MRS. |
| `src/static/js/sw.js` | Caché `v11` → `v12`, para que los dispositivos dejen de usar el `encuesta.js` antiguo. |
| `src/templates/encuestas/mi_tablero.html`, `ficha_paciente.html` | El puntaje de la ronda en curso se marca «(provisional: la ronda no está cerrada)». Es lo mínimo exigido; el tablero en sí es de la 40B-3. |
| `src/apps/rondas/models.py` | Modelo `MRSAnterior40B2`. |
| `src/apps/rondas/completitud.py` | Modo **obligatorio**, además del de observación (§4.3). |
| `src/apps/rondas/senales.py` | `_abrir` registra al actor. La rama de cierre de la señal queda como respaldo, marcada `via='senal_fuera_del_servicio'`. |
| `src/apps/rondas/apps.py` | Conecta la protección de rondas cerradas. |
| `src/apps/rondas/tests.py`, `src/apps/encuestas/tests.py` | 19 llamadas de cierre pasan por `_sync()`, que completa lo obligatorio y envía la ronda. Hay 3 ajustes explícitos: `test_mrs_en_dos_bloques` (ahora el ítem omitido debe ser **nulo**), `test_puntaje_total_mrs` (sin los 11 ítems no hay puntaje) y la prueba de observación de la 40B-1, que ahora observa el cierre por la señal de respaldo. Lo que comprueba cada prueba no cambió, salvo en esos 3 casos, donde el comportamiento esperado es justo el defecto corregido. |
| `analisis/fase40/40B_implementacion/pruebas/test_40b1_proteccion_historica.py` | Control de `models.py` acotado a los cambios previstos, con control negativo. Lectura del análisis idéntica. Excepciones conocidas de los manifiestos (§9). |
| `analisis/fase40/40B_implementacion/pruebas/test_40b0_definiciones.py` | `test_plataforma_sin_cambios` acotado de nuevo (§6). `SHA_MODELS_ARBOL` se reemplazó por una comprobación de que la prueba no modifica el archivo. |
| `analisis/fase40/40S_seguridad/40S-1_propuesta_consentimiento.md` | Adenda con la decisión sobre retiro y reincorporación (§8). |

**Sin cambios:** las Fases 34–39 (ningún archivo de `analisis/` fuera de `fase40/` ni de `datos/` se modificó en esta sesión; comprobado por fecha de modificación). También quedan sin cambios `retiro.py`, el consentimiento, el catálogo educativo, el tablero (salvo la etiqueta «provisional») y los modelos analíticos (no se recalculó nada).

## 4. Esquema MRS, migraciones y reglas de validación

### 4.1 Representación del MRS

| Estado | En la base | En el cliente | ¿Cuenta como respondida? |
|---|---|---|---|
| Eligió «Ninguna» | `0` | `'0'` | Sí |
| Eligió 1 a 4 | `1`…`4` | `'1'`…`'4'` | Sí |
| No respondió | `NULL` | ausente | No |
| 0 guardado **antes** de la 40B-2 | `0`, con marca `MRSAnterior40B2` | ausente, en `mrs_por_confirmar` | Solo si se confirma |

- Fuera de 0–4 (`5`, `-1`, `'x'`, `2.5`) se rechaza por validación de opciones.
- En un envío **completo** (`parcial: false`) los 11 ítems siguen siendo obligatorios (`blank=False`).
- En un guardado **parcial**, un ítem que no viene **no borra** lo que ya estaba guardado (por ejemplo, si lo respondió otro dispositivo); en una fila nueva queda nulo.
- `puntaje_total` es `None` mientras falte un ítem.
- `cierre.puntaje_mrs_definitivo(mrs)` solo devuelve el puntaje si están los 11 ítems **y** la ronda está cerrada.

### 4.2 Migraciones

| Migración | Qué hace en la base | Reversa |
|---|---|---|
| `encuestas.0020_mrs_items_sin_respuesta_nulos` | `ALTER COLUMN … DROP NOT NULL` en 11 columnas. **No reescribe ninguna fila** (comprobado: la huella de `encuestas_mrs` es idéntica antes y después). | Se niega si hay ítems nulos: volver a `NOT NULL` obligaría a inventar un 0. |
| `rondas.0004_mrs_anterior_40b2` | Crea `rondas_mrsanterior40b2` y una marca por cada MRS existente (7). Guarda solo el id del MRS y una lista de nombres de ítems confirmados (vacía); nunca valores. | Se niega si hay marcas: borrarlas haría pasar ceros no verificables por respuestas reales, sin rastro. |

**Compatibilidad con la 40B-1:** `verificar_rondas` da 0 problemas, los 6 índices únicos siguen y las 9 rondas, 4 cerradas y 5 abiertas, siguen coherentes con `ronda_actual`. Hábitos de vida sigue fuera del índice único.

### 4.3 Reglas de cierre (completitud en modo obligatorio)

Una ronda se cierra solo si:

1. **Identificación** tiene sus 7 preguntas obligatorias.
2. Los **11 ítems MRS** están respondidos (0 a 4) y, si el MRS es anterior a la 40B-2, todos sus ceros fueron confirmados.
3. Si cierra una **profesional**, el **EMPA** tiene sus 4 campos obligatorios (talla, peso, presión sistólica y diastólica). Se usa el esquema del **rol de quien cierra**, igual que hace el cliente. *[Reemplazado por `40B-2_revision_correctiva.md`: el EMPA ya no es obligatorio para cerrar, tampoco para la profesional.]*
4. **Condicionales:** una sección que no corresponde no se exige (por ejemplo, Trabajo si no trabaja). Una pregunta oculta tampoco se exige, ni aunque estuviera marcada obligatoria; esto incluye la ocultación en cadena, con las mismas reglas que `encuesta.js`. Una sección sin preguntas obligatorias visibles no se exige aunque no tenga fila.

**Cuando el cierre se rechaza:**

- las secciones del mismo envío **quedan guardadas como borrador**;
- la respuesta es `ok: false`, `guardado: true` y `cierre: {estado: 'rechazado', faltantes: [{seccion, motivo, preguntas}]}`, con `motivo` igual a `obligatorias_sin_responder` o `por_confirmar`;
- se registra el evento `CIERRE_RECHAZADO`, con nombres de preguntas y sin valores;
- `ronda_actual` no avanza y el plazo de 15 días no empieza.

**Cuando el cierre se acepta:**

- la ronda queda `CERRADA` con `cerrada_en`, `cerrada_por`, `cerrada_por_rol` e `id_cierre`;
- se registra el evento `CIERRE` (`via='cierre_validado_40B2'`) y se abre la ronda siguiente, con su `APERTURA` y su actor;
- recién entonces avanza `ronda_actual`.

Todo ocurre en la misma transacción.

### 4.4 Protección de las respuestas históricas

- **Barrera `pre_save` en las 7 secciones.** Impide modificar una fila de una ronda cerrada, moverla de ronda o de participante, y crear filas en una ronda cerrada, desde cualquier camino que use `save()`. La sincronización ya lo impedía por el `uuid_local`; esta es la segunda barrera. Solo `proteccion.correccion_administrativa()` la levanta, y hoy no se usa.
- **El borrado no se bloquea:** el retiro sigue funcionando igual.
- **Los ceros antiguos nunca se convierten.** En una ronda abierta, el servidor no los presenta como respondidos (`estado_ronda` los omite y los informa en `mrs_por_confirmar`) hasta que la persona los elige de nuevo. Al elegirlos, el cliente los envía en `confirmados` y se anotan en la marca.

## 5. Sincronización (protocolo 2)

**Campos nuevos del payload** (compatibles con el anterior):

| Campo | Uso |
|---|---|
| `ronda` | La ronda a la que pertenecen las respuestas locales (`null` si el dispositivo aún no la conoce). |
| `id_cierre` | UUID que el cliente genera al pulsar Finalizar. Se guarda en IndexedDB y se reutiliza en cada reintento. |
| `confirmados` (en el bloque `mrs`) | Ítems que la persona eligió en esta ronda. Solo cuentan si vienen con valor en `datos`. |

**Respuestas del servidor:**

| Situación | HTTP | Qué se escribe | Qué hace el cliente |
|---|---|---|---|
| Guardado normal | 200 `ok: true` | Las secciones | Marca sincronizado |
| Cierre aceptado | 200 `cierre.estado = 'cerrada'` | Secciones y cierre | Ronda nueva en blanco y mensaje final |
| **Mismo `id_cierre` repetido** (reintento, doble clic, red que se cortó tras cerrar) | 200 `cierre.estado = 'repetido'` | **Nada** (solo el evento `REINTENTO_IDEMPOTENTE`) | Igual que un cierre aceptado |
| Cierre incompleto | 200 `ok: false`, `cierre.estado = 'rechazado'` | Las secciones (borrador) | Vuelve a la primera sección con pendientes, dice cuáles faltan, desactiva el reintento automático y renueva el `id_cierre` |
| `ronda` distinta de la abierta (tardía, de otro dispositivo, o la ronda la cerró la profesional) | **409** `ronda_cerrada` / `ronda_inexistente` | **Nada** (solo el evento `ESCRITURA_RECHAZADA`) | **Aparta** lo pendiente en IndexedDB (`conflictos`), pasa a la ronda abierta, carga lo del servidor e informa |
| La ficha existe y `ronda: null` | 409 `ronda_desconocida` | Nada | Igual que la fila anterior |
| `finalizar` **sin** `ronda` (cliente antiguo) | 409 `cliente_desactualizado` | Nada | «Recarga la página» (los datos siguen en el dispositivo) |
| Sin consentimiento (40S-1) | 403 | Nada | Conserva todo pendiente e informa |
| Plazo de 15 días (Fase 31) | 400 | Nada | Conserva pendiente (sin cambios) |
| Sin red, respuesta HTML o error 500 | — | — | Conserva todo pendiente; reintento al volver la red o al cargar |

**Concurrencia.** La ficha se bloquea con `SELECT … FOR UPDATE`, así que dos solicitudes de la misma participante se ordenan:

- con dos cierres de dispositivos distintos, uno cierra y el otro recibe 409;
- con el mismo cierre enviado dos veces a la vez, uno cierra y el otro responde «repetido».

Un conflicto de unicidad en una sección revierte solo esa sección (punto de guardado), no las demás.

**IndexedDB nunca se borra con datos pendientes:**

- **cambio de ronda detectado al cargar:** lo pendiente pasa a `conflictos` antes de empezar la ronda nueva;
- **409:** lo mismo, sin reintentos en bucle;
- **cambio de cuenta en el mismo dispositivo:** lo pendiente de la cuenta anterior se aparta en `respaldo_de|<cuenta>` y se le devuelve cuando vuelve a entrar. Ya se guardaba en ese dispositivo; solo cambia de clave. Además, ahora se reinicia la ronda local, que antes quedaba de la persona anterior;
- **si IndexedDB no puede escribir** (almacenamiento lleno, modo privado): se avisa «No se pudo guardar en este dispositivo…» en lugar de fallar en silencio.

**Clientes antiguos:**

- siguen pudiendo guardar borradores sin `ronda`, con el comportamiento anterior;
- no pueden cerrar hasta recargar la página;
- el cambio de caché a `v12` reemplaza `encuesta.js` en la siguiente carga.

## 6. Protección de las Fases 34–39 frente al cambio de `models.py`

| Control | Antes | Ahora |
|---|---|---|
| `test_40b1 … test_40b1_no_modifica_models_de_encuestas` | `models.py` idéntico a `44bfe0b` | `test_models_solo_cambia_lo_previsto_en_la_40b2`: el árbol AST es idéntico a `44bfe0b` salvo los 2 cambios previstos. Los 11 ítems quedan con `null=True, default=None` y sin `blank`. Un **control negativo** (cambiar una etiqueta, un corte de severidad u otro campo) debe ser detectado. |
| nuevo | — | `test_el_analisis_lee_lo_mismo_de_la_plataforma`: lo que `catalogo.leer_modelos_plataforma()` extrae hoy es idéntico a lo congelado en la 40B-0. |
| `test_40b0 … test_plataforma_sin_cambios` | 4 archivos idénticos al origen | 3 archivos idénticos al origen, `models.py` debe dar las **mismas definiciones** que lo congelado, y las huellas del commit de origen siguen verificables en git. |
| Clases de opciones (`test_clases_de_opciones_que_lee_el_analisis`) | idénticas | Sin cambios: siguen idénticas. |

## 7. Pruebas

Django corrió en PostgreSQL 15, en el contenedor `web` del proyecto, sobre la base temporal de pruebas. Todas las pruebas de esta tabla se ejecutaron realmente.

| # | Prueba obligatoria | Evidencia | Resultado |
|---|---|---|---|
| 1 | Cero explícito distinto de ausente | `test_01_…`, `test_01b_…` (un parcial no borra lo de otro dispositivo), `test_02b_…` | OK |
| 2 | MRS válido de 0 a 4 | `test_02_valores_validos_de_0_a_4` (0–4 aceptados; 5, −1, 'x' y 2.5 rechazados) | OK |
| 3 | Rechazo de cierre incompleto | `test_03_…`, `test_03b_…` (API: 200 con detalle) | OK |
| 4 | Aceptación de cierre completo | `test_04_…` (actor, rol, `id_cierre` y eventos), `test_04b_…` | OK |
| 5 | Condicionales respetadas | `test_05_…` (Trabajo), `test_05b_…` (obligatoria condicional solo si se muestra) | OK |
| 6 | Borradores conservados | `test_06_…` (rechazo, luego cierre sobre la misma fila sin duplicar); cliente: «cierre rechazado…» | OK |
| 7 | Puntaje definitivo solo completo | `test_07_…` (None → provisional → definitivo al cerrar), `test_07b_…` (etiqueta en el tablero) | OK |
| 8 | Cierre repetido sin duplicar | `test_08_…` (el reintento con valores distintos no escribe), `test_08b_…` (dentro del plazo), `test_08c_…` (`id_cierre` ajeno) | OK |
| 9 | Dos cierres concurrentes | `ConcurrenciaCierreTest` (`TransactionTestCase`, hilos y conexiones reales): ids distintos → `cerrada` + `ronda_cerrada`; mismo id → `cerrada` + `repetido`; 1 solo `CIERRE` y 1 sola ronda abierta | OK |
| 10 | Solicitudes tardías | `test_10_…` (no escribe en la ronda nueva; evento de rechazo), `test_10b_…` (409), `test_10c_…`, `test_10d_…` (cliente antiguo), `test_10e_…` (formato) | OK |
| 11 | Sincronización offline y recuperación | Node: «sin conexión…», «error de red…» (mismo `id_cierre`), «respuesta que no es JSON…», «el payload usa el protocolo 2…» | OK (11/11 del cliente) |
| 12 | IndexedDB pendiente ante fallos | Node: «403…», «409…», «al cargar con una ronda cerrada…», «cambio de cuenta…», «si IndexedDB no puede escribir…» | OK |
| 13 | Usuarias comunes y profesionales | `test_13_…` (la profesional también completa el EMPA; *reemplazada en `40B-2_revision_correctiva.md` por cierres con EMPA completo, parcial y ausente*), `test_13b_…`, `test_13c_…` (la profesional cierra la ronda de una paciente con cuenta; el envío posterior de la usuaria se rechaza sin pisar nada) | OK |
| 14 | Sin cambios silenciosos en lo histórico | `test_14_…` (`save()`, crear y mover), `test_14b_…`, `test_14c_…` (el retiro sigue igual), `test_14d/e/f_…` (ceros antiguos), migraciones: `test_las_migraciones_no_cambian_ningun_valor…`; base real: huella de `encuestas_mrs` idéntica | OK |
| 15 | Integridad de las rondas de la 40B-1 | `test_15_…` (3 rondas con rechazos intermedios; `verificar_rondas` sin problemas), `test_15b_…` (esquema del cliente al día); base real: problemas 0 | OK |
| 16 | Suite completa de Django | **266/266** (230 anteriores + 36 nuevas), también con `--reverse` | OK |
| 17 | 40B-0 y Fases 34–39 | `test_40b0_definiciones` **15/15**; `test_40b1_proteccion_historica` **5/5** (6.457 artefactos, con 3 excepciones conocidas, §9); `preprocesamiento.test_entropia` **79/79**; `preprocesamiento.test_revision_35b` **43/43**; `test_h11_h13` **21/21** | OK |
| 18 | Archivos protegidos conservados | Ningún archivo de `analisis/` ni `datos/` con fecha de modificación posterior al inicio de la sesión; manifiestos de las Fases 34–39 verificados; respaldos fuera del repositorio | OK |

**Cómo correrlas:**

```
docker compose exec web python manage.py test                     # Django (266)
node --test src/apps/encuestas/pruebas_js/test_encuesta_sync.mjs   # cliente (11)
python -m unittest analisis/fase40/40B_implementacion/pruebas/test_40b0_definiciones.py
python -m unittest analisis/fase40/40B_implementacion/pruebas/test_40b1_proteccion_historica.py
cd analisis && python -m unittest preprocesamiento.test_entropia preprocesamiento.test_revision_35b
cd analisis && python -m unittest cierre_fases_34_35/scripts/test_h11_h13.py
```

**Lo que NO se probó:** el flujo en un navegador real. Las pruebas del cliente ejecutan el `encuesta.js` real con dobles de DOM, IndexedDB y red. Cubren la lógica de sincronización, pero no la interfaz (alertas, pantallas ni el Service Worker). Recomiendo una prueba manual (§11).

## 8. Consentimiento y retiro (solo documentado)

La decisión quedó como adenda en `40S-1_propuesta_consentimiento.md`:

- el consentimiento vigente sirve para varias rondas;
- la profesional podrá registrar un consentimiento presencial;
- el retiro elimina las respuestas, las rondas y los resultados (reemplaza a C-4 y cierra DC-1);
- la reincorporación es una aceptación nueva con un historial nuevo desde la ronda 1 (cierra DC-6);
- no se recupera nada;
- solo se conservan constancias administrativas mínimas, sin datos de salud.

**No se implementó nada y `retiro.py` no cambió.**

- Hoy el retiro ya borra en cascada la ficha, sus rondas, sus eventos y sus marcas MRS (`test_14c`).
- Pero **no deja ninguna constancia**. Eso lo tendrá que resolver la etapa que implemente esta decisión.

## 9. Integridad de los datos y problemas históricos que no se pudieron corregir

| Problema | Estado |
|---|---|
| **30 ceros MRS anteriores a la 40B-2** | No se pueden verificar y no se convierten. 8 (rondas cerradas): historia no verificable para siempre. 22 (rondas abiertas): se pedirá confirmarlos antes de cerrar. |
| **Discrepancia con el informe 40B-1** | `test_40b1_proteccion_historica` **falló al empezar esta fase**, antes de cualquier cambio, por 3 archivos cuya huella ya no coincide con los manifiestos de cierre: (a) `analisis/limpieza/catalogo.py`, cambiado a propósito en la **40B-0** (commit `573d3a3`, 02:04); (b) `analisis/eda/univariado.py` y `analisis/eda_usuaria.py`, modificados el **2026-11-04 a las 23:41–23:43**, unos 30 minutos **después** del manifiesto de la revisión correctiva 34 (23:11) y ya incluidos en `44bfe0b`. La prueba de la 40B-1 se escribió a las 03:20, después del cambio (a), así que su «3/3 OK» no cuadra con estos archivos. No sé cómo se obtuvo. No modifiqué ninguno: quedaron como `EXCEPCIONES_CONOCIDAS` con su huella **actual exacta**, de modo que cualquier cambio posterior vuelve a fallar. **Falta que alguien revise** qué cambió en los dos archivos de EDA y si afecta lo publicado de la Fase 34. |
| Duplicado en Hábitos de vida | Sin cambios (1 par en una ronda abierta). Falta decidir qué fila es válida. |
| Rondas de la retrocarga | Siguen sin fechas, sin actor y sin versión conocida (40B-1). |
| Indicios de datos reales (DR-1) | Siguen. Esta fase solo leyó conteos. |
| Controles `integridad_37d/38/39` y `pruebas_39` | Siguen exigiendo `HEAD == 745d689`; los reemplaza `test_40b1_proteccion_historica` sin modificarlos. |
| Secretos | Revisé los 42 archivos cambiados o nuevos y el diff completo contra los 4 valores de `.env.desarrollo`. **Ningún archivo actual los contiene.** Las 4 coincidencias del diff son líneas **eliminadas** por la 40S-1 (los literales antiguos de `settings.py` y `docker-compose.yml`, que ya están en el historial de GitHub; su rotación es la 40S-2). |

## 10. Riesgos pendientes

| Riesgo | Nivel | Comentario |
|---|---|---|
| Sin prueba en un navegador real | Medio | La lógica está probada con dobles. Falta ver alertas y pantallas, el reemplazo del Service Worker y el modo profesional. |
| Conflictos apartados sin interfaz | Medio | Las respuestas apartadas (`conflictos`, `respaldo_de|…`) quedan en el dispositivo, pero hoy nadie puede verlas ni exportarlas. No se pierden, pero tampoco se aprovechan. Hay que decidir si hace falta una pantalla para recuperarlas. |
| Respaldo por cuenta en un dispositivo compartido | Medio | Lo pendiente de una persona queda en el navegador bajo otra clave (antes se borraba). Es lo que se pidió (no borrar), pero en un equipo compartido es un dato de salud que permanece en el dispositivo. |
| Cliente antiguo en caché | Bajo | Puede guardar borradores, pero no cerrar hasta recargar. El 409 `cliente_desactualizado` lo explica. |
| Escrituras fuera de `save()` | Bajo | `update()` y SQL directo saltan la barrera de rondas cerradas y la señal del registro. `verificar_rondas` detecta las incoherencias del registro. |
| Rama de cierre de la señal | Bajo | Si un camino ajeno al servicio avanza `ronda_actual`, la señal registra el cierre sin validarlo (`via='senal_fuera_del_servicio'`). Hoy ningún camino de la plataforma lo hace. |
| Rol con que se evalúa el cierre | Bajo | Es el de quien cierra (como el cliente). Una ronda que abre la usuaria y cierra la profesional exige el EMPA clínico. *[Reemplazado por `40B-2_revision_correctiva.md`: el EMPA ya no es obligatorio para cerrar, tampoco para la profesional.]* |
| Bitácora de rechazos | Bajo | Cada solicitud tardía agrega un evento `ESCRITURA_RECHAZADA` (sin datos de salud). El cliente no reintenta en bucle. |
| Índices únicos fuera del `Meta` | Bajo | Siguen con `RunSQL` (40B-1). No se pasaron al `Meta` para no tocar más `models.py`. |
| Choque de migraciones con `valeAW` (DR-8) | Medio | Sin cambios. La `encuestas.0020` agrega un número más que choca. |

## 11. Condiciones para comenzar la 40B-3

1. Revisar y aprobar este informe, en especial §5 (protocolo y mensajes) y el texto del aviso de ceros por confirmar.
2. **Revisar la discrepancia de §9**: qué cambió en `analisis/eda/univariado.py` y `analisis/eda_usuaria.py` después del manifiesto. Además, aprobar o rechazar las `EXCEPCIONES_CONOCIDAS`.
3. Hacer una prueba manual en el navegador con la base de desarrollo (usuaria y profesional, con y sin conexión, y cierre incompleto). Recomiendo una copia restaurada o una cuenta sintética, dado DR-1.
4. Decidir qué mostrará el tablero (40B-3):
   - las rondas cerradas con ceros no verificables;
   - el puntaje provisional;
   - las categorías de severidad, que siguen pendientes de verificar el corte 16+/17+ (Heinemann 2004).
5. Siguen pendientes de la 40B-1: el duplicado de Hábitos de vida y DR-1.
6. Hacer un respaldo nuevo y verificado antes de la primera migración de la 40B-3.

---

*Sin commit ni push. Quedo a la espera de la revisión antes de comenzar la 40B-3.*
