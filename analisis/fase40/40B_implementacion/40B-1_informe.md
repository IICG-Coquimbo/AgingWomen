# Fase 40B-1 — Infraestructura del historial de rondas

**Fecha:** 2026-11-06 · **Rama:** `datos-simulados` · **HEAD:** `573d3a3` (sin commit ni push: todos los cambios de la Fase 40 quedan locales hasta cerrarla completa).

**Resumen.** La plataforma tiene ahora un registro de rondas (`RondaEvaluacion`) y una bitácora de eventos de solo inserción (`EventoRonda`). Ese registro dice qué ronda está abierta, cuáles están cerradas, qué historia existe y qué historia no puede reconstruirse. El comportamiento visible no cambió:

- el cierre, la sincronización, el cálculo MRS y las pantallas funcionan igual;
- el validador de completitud solo **observa**: nunca rechaza;
- la base de desarrollo se migró después de un respaldo verificado. Se recuperaron **9 rondas históricas** (4 cerradas y 5 abiertas, ninguna con fechas inventadas);
- no se modificó ni una respuesta;
- se encontró **1 par duplicado** (Hábitos de vida). Quedó intacto y excluido de la restricción de unicidad, a la espera de una decisión humana.

---

## 1. Verificaciones previas

| Verificación | Resultado |
|---|---|
| Estado de Git | Rama `datos-simulados`, HEAD `573d3a3`. Al empezar había 11 cambios locales de 40S-1; se conservaron todos. |
| Migraciones | `encuestas` hasta 0019, `usuarios` hasta 0003, sin migraciones pendientes ni ramas de migración. |
| `origin/valeAW` (solo lectura, sin cambiar de rama ni fusionar) | `1ba0c9e`, del 2026-09-24. No tiene commits desde antes de la integración del PR #2. Tiene migraciones propias (`encuestas` 0014–0018 y `usuarios` 0002–0003) que **ya** chocan por número con las de `main`. La 40B-1 no agrava ese choque, porque sus migraciones están en una app nueva. El riesgo DR-8 sigue abierto. |
| Dependencias de las Fases 35–39 en `models.py` | `preprocesamiento/test_revision_35b.py:245` (lee el texto con expresiones regulares), `revision_35b_reunion_1103.py` (ORIENTACION), `fase38/.../integridad_38.py` (huella de `models.py`), `fase37D integridad_37d.py`, `fase39 integridad_39.py` y `pruebas_39.py:323`. Las cuatro últimas exigen HEAD == `745d689` y ningún cambio en `src/`, así que ya no se cumplen desde `44bfe0b`. |
| Inventario de la base de desarrollo (solo lectura, solo conteos) | 7 cuentas, 5 fichas, 7 filas por sección (8 en Hábitos de vida), ninguna ronda fuera de rango, ningún uuid faltante, `ultima_finalizacion_en` coherente. |
| Indicios de datos reales | **Sí, hay indicios.** 6 de los 7 correos están en dominios que no son de prueba, y existe `datos/reales/respuestas_reales.json`, que **no se abrió**. No se abrió ninguna respuesta personal; el informe solo contiene conteos. |
| Huellas de integridad iniciales | 898 archivos protegidos (modelos, `sync.py`, `rut.py`, `backends.py`, migraciones, `.env`, `datos/`) y huellas de contenido de las 18 tablas, guardadas fuera del repositorio. |

## 2. Respaldo

- `pg_dump -Fc` de la base de desarrollo **antes** de migrar, guardado fuera del repositorio en `C:/Users/scarl/Respaldos_AgingWomen/`. Pesa 79.927 bytes y tiene al lado un archivo `.sha256`. Los permisos son SYSTEM, Administradores y la cuenta de la usuaria. No se publicó.
- **Restauración verificada dos veces** en un contenedor PostgreSQL aislado, en una red interna sin salida:
  - antes de migrar: contenido idéntico en las 18 tablas;
  - después de migrar la base real: restaurado de nuevo en una base limpia, otra vez idéntico en las 18 tablas (prueba 15).
- Ese contenedor también sirvió de ensayo de las migraciones: hacia adelante, en reversa y de nuevo hacia adelante, todo limpio.
- El contenedor, su red y su volumen anónimo (que tenía una copia de la base) se **eliminaron** al terminar.
- La base de desarrollo no se borró ni se sobrescribió.

## 3. Archivos

### Nuevos

| Archivo | Contenido |
|---|---|
| `src/apps/rondas/__init__.py`, `apps.py` | App `apps.rondas`. `ready()` conecta la señal. |
| `src/apps/rondas/models.py` | `RondaEvaluacion` y `EventoRonda` (§4). |
| `src/apps/rondas/senales.py` | Mantiene el registro al día cuando se guarda la ficha (§4.3). |
| `src/apps/rondas/completitud.py` | Validador de completitud en modo observación (§4.4). |
| `src/apps/rondas/migrations/0001_initial.py` | Tablas y restricciones. |
| `src/apps/rondas/migrations/0002_retrocarga.py` | Carga histórica (§5). |
| `src/apps/rondas/migrations/0003_unicidad_secciones.py` | Detección de duplicados e índices únicos (§5). |
| `src/apps/rondas/management/commands/verificar_rondas.py` | Verificación de solo lectura (`--json` opcional). Termina con código 1 si alguna invariante falla. |
| `src/apps/rondas/tests.py` | 20 pruebas (§7). |
| `analisis/fase40/40B_implementacion/pruebas/test_40b1_proteccion_historica.py` | Protección de las Fases 34–39 (§6). |
| `analisis/fase40/40B_implementacion/40B-1_informe.md` | Este informe. |

### Modificados

| Archivo | Cambio |
|---|---|
| `src/Encuesta_integral/settings.py` | Se agregó `'apps.rondas'` a `INSTALLED_APPS`, con un comentario. Es el único cambio sobre 40S-1. |
| `src/apps/encuestas/tests.py` | En `PropiedadesModeloTest.test_perdida_talla`, la segunda EMPA usa una ficha propia (`self._ident()`). Antes creaba dos EMPA para la misma participante y ronda, un caso que el nuevo índice único prohíbe y que la plataforma real nunca genera, porque `sync.py` hace *upsert*. Lo que la prueba verifica no cambia. |

**Sin cambios:**

- `apps/encuestas/models.py`, `sync.py`, `api.py` (fuera de lo que cambió 40S-1) y `views.py`;
- el cálculo MRS y los valores por defecto de sus 11 ítems;
- el procedimiento de cierre, la sincronización sin conexión y el tablero;
- los resultados individuales, el catálogo educativo, el consentimiento y la reincorporación;
- las Fases 34–39 y la limpieza 40B-0.

El archivo temporal `src/inventario_40b1_tmp.py` (inventario de solo lectura) se eliminó.

## 4. Modelos

### 4.1 `RondaEvaluacion`

| Campo | Uso |
|---|---|
| `participante` | FK a `encuestas.Identificacion`, con CASCADE. El retiro borra el registro junto con el resto de la ficha, igual que hoy. |
| `numero` | Número de ronda, desde 1. |
| `estado` | `ABIERTA`, `CERRADA` o `ANULADA` (esta última reservada; no se usa). |
| `origen` | `NORMAL` (registrada en vivo) o `RETROCARGA` (reconstruida al migrar). |
| `abierta_en`, `cerrada_en` | Fechas. **Nulas en la retrocarga**: no se conocen. |
| `cerrada_por`, `cerrada_por_rol` | Quién cerró. En vivo vale `NO_REGISTRADO`, porque hoy el cierre no informa el actor (lo hará la 40B-2); en retrocarga vale `DESCONOCIDO`. |
| `id_cierre` | UUID único, reservado para la idempotencia del cierre en la 40B-2. |
| `version_cuestionario` | `2026-10-01` para las rondas nuevas, `DESCONOCIDA_ANTERIOR_40B` para la retrocarga. |
| `observaciones` | JSON con el estado de la historia (§5). Nunca contiene valores de respuestas. |

**Restricciones en la base:**

- número único por participante;
- **como máximo una ronda `ABIERTA` por participante** (índice único parcial);
- número ≥ 1;
- una ronda abierta no tiene fecha de cierre.

### 4.2 `EventoRonda`

- Es una bitácora de **solo inserción**: `save()` sobre una fila existente y `delete()` lanzan `EventoRondaInmutable`.
- Tipos en uso: `APERTURA`, `CIERRE`, `RETROCARGA` e `INCOHERENCIA`.
- Tipos reservados para la 40B-2: `GUARDADO`, `CIERRE_RECHAZADO`, `REINTENTO_IDEMPOTENTE`, `ESCRITURA_RECHAZADA` y `CORRECCION_ADMIN`.
- `datos` guarda conteos, nombres de sección y el resultado de completitud. **Nunca guarda contenido de salud.**

### 4.3 Mantenimiento del registro

Una señal `post_save` sobre `Identificacion` compara `ronda_actual` con la ronda abierta del registro, bloqueándola con `select_for_update`:

- **si no hay ronda abierta**, abre la ronda `ronda_actual`;
- **si `ronda_actual` coincide con la abierta**, no hace nada (es un guardado normal);
- **si `ronda_actual` es la abierta + 1**, la cierra:
  - `cerrada_en = ultima_finalizacion_en`;
  - evento `CIERRE` con la completitud observada;
  - abre la siguiente ronda;
- **cualquier otro salto** registra un evento `INCOHERENCIA` y **no modifica nada**.

La señal se ejecuta dentro de su propio `atomic` y con captura de errores: **un fallo del registro nunca impide guardar la encuesta**. El error queda en el log. `ronda_actual` sigue siendo la fuente que usa toda la plataforma (compatibilidad).

### 4.4 Validador de completitud (observación)

`completitud.evaluar(participante, ronda)`:

- usa el mismo esquema y las mismas condiciones de visibilidad que el cliente (`encuesta.js`). Por ejemplo, Trabajo es obligatorio solo si la participante trabaja;
- informa qué secciones faltan o qué preguntas obligatorias quedaron sin responder;
- se guarda en el evento `CIERRE` y **nunca bloquea el cierre**.

Limitación registrada: los ceros por defecto de los 11 ítems MRS no se distinguen de una omisión.

## 5. Migraciones y retrocarga

| Migración | Qué hace |
|---|---|
| `rondas.0001_initial` | Crea las dos tablas y sus restricciones. |
| `rondas.0002_retrocarga` | Para cada ficha crea las rondas 1 a `ronda_actual−1` como `CERRADA` y la ronda `ronda_actual` como `ABIERTA`, todas con origen `RETROCARGA` y un evento `RETROCARGA` por ronda. La reversa borra solo las filas `RETROCARGA`. |
| `rondas.0003_unicidad_secciones` | Busca duplicados (participante, ronda) **antes** de imponer la restricción. Si los hay en una tabla protegida, se detiene con un informe de conteos y no cambia nada. Si no los hay, crea índices únicos en 6 secciones. |

**La retrocarga no inventa nada:**

- deja nulas las fechas de apertura y cierre, el actor y el `id_cierre`;
- la versión queda `DESCONOCIDA_ANTERIOR_40B`;
- no reconstruye características pasadas a partir de los valores actuales;
- no modifica respuestas, no borra rondas y no corrige duplicados.

**Qué registra en `observaciones`:**

- las secciones presentes en cada ronda;
- si la ronda está vacía o no tiene MRS;
- las secciones duplicadas;
- `instantanea_disponible: false`;
- la lista de limitaciones.

`ultima_finalizacion_en` solo se anota como **referencia** en la ronda `ronda_actual−1`, porque es la fecha del último cierre y no de cada ronda.

**Por qué los índices se crean con SQL.** Se crean con `RunSQL` y no en el `Meta` de los modelos para no tocar `encuestas/models.py` (§6). Django no los conoce en su estado; la 40B-2 podrá pasarlos al `Meta` con `SeparateDatabaseAndState`.

### Resultado en la base de desarrollo

```
Retrocarga 40B-1: fichas 5, cerradas 4, abiertas 5, omitidas 0, secciones fuera de rango 0, pares duplicados 1
Unicidad 40B-1: sin duplicados en 6 tablas; fuera de la restricción: encuestas_habitosdevida (1 par)
verificar_rondas: 9 rondas (4 CERRADA, 5 ABIERTA, 9 RETROCARGA), 2 vacías, 2 sin MRS,
                  0 incoherencias, 6 índices únicos, problemas: 0
```

| Qué se puede saber | Qué no se puede reconstruir |
|---|---|
| Cuántas rondas tuvo cada ficha y cuál está abierta. | Cuándo se abrió o cerró cada ronda histórica. |
| Qué secciones tiene cada ronda (todas las cerradas tienen las 7). | Quién cerró cada ronda. |
| Qué rondas están vacías o sin MRS (las 2 abiertas que aún no tienen respuestas). | Con qué versión del cuestionario se respondió. |
| Desde ahora: aperturas, cierres, completitud observada e incoherencias. | Los valores originales si una sección se editó después (no había instantánea). |
| | Si un 0 en MRS fue respuesta o valor por defecto. |

### Duplicado encontrado

| Sección | Pares | Ronda | Estado de la ronda | Detalle (sin contenido) | Decisión |
|---|---|---|---|---|---|
| Hábitos de vida | 1 | 1 | ABIERTA (ficha con cuenta) | 2 filas con id consecutivo, sincronizadas con unos 17 días de diferencia, uuid distintos, 4 campos distintos | **No se tocó.** La tabla quedó fuera del índice único. Una persona debe decidir qué fila es la válida (con respaldo), y después una migración posterior podrá agregar el índice. |

## 6. Protección de la reproducibilidad de las Fases 34–39

Hay dos medidas:

1. **No tocar `apps/encuestas/models.py`.** Los modelos nuevos viven en `apps/rondas` y los índices se crean con SQL. Así siguen intactos:
   - el catálogo de campos que congeló la 40B-0;
   - las expresiones regulares de `test_revision_35b`;
   - la huella de `models.py` que registran las Fases 38 y 39.
2. **Una prueba nueva que no depende de HEAD ni de `src/`:** `test_40b1_proteccion_historica.py`. Reemplaza a los controles que exigían HEAD == `745d689`, sin modificarlos. Comprueba que:
   - cada archivo de los 10 manifiestos finales (cierre 34–35, revisión correctiva 34, 36, 37A, 37B, 37C, complemento 37C, 37D, 38 y 39) conserve su SHA-256: 6.457 artefactos recorridos. *[Corrección documental: en la 40B-1 esta comprobación **no pasó**; ver §13.]* Los 5 de verdad o bitácora del simulador solo se comprueban por existencia y **no se leen**;
   - las 12 clases de opciones que lee el análisis sigan **textualmente iguales** a las de `44bfe0b`, usando el mismo patrón que `test_revision_35b`. Así, si la 40B-2 cambia `models.py`, la prueba avisa si eso afecta al análisis. Un control negativo con una etiqueta alterada en memoria lo detecta;
   - `encuestas/models.py` no cambió respecto de `44bfe0b`.

No se modificó ningún archivo de las Fases 34–39. No se recalcularon modelos.

## 7. Pruebas obligatorias

Las pruebas de Django corrieron en **PostgreSQL 15**, en el contenedor `web` del proyecto (`manage.py test`). Las de migración y concurrencia usan `TransactionTestCase`.

| # | Verificación | Evidencia | Resultado |
|---|---|---|---|
| 1 | Las migraciones se ejecutan correctamente | `MigracionesTest` (hacia adelante y en reversa con `MigrationExecutor`); ensayo en la copia aislada (adelante, reversa y adelante); migración real de la base de desarrollo | OK |
| 2 | Las rondas existentes se conservan | `test_retrocarga_sin_inventar_y_sin_tocar_respuestas`; base real: 9 rondas, coherentes con `ronda_actual` de las 5 fichas | OK |
| 3 | No se inventan fechas históricas | La misma prueba (fechas y actor nulos); `verificar_rondas`: 0 `retrocarga_con_fecha` | OK |
| 4 | No se modifican respuestas | Huella de las secciones antes y después en la prueba de migración; base real: huellas idénticas en las 14 tablas de encuestas y usuarios | OK |
| 5 | No se eliminan participantes | Base real: `encuestas_identificacion` y `usuarios_usuario` con la misma huella y cantidad; la reversa borra solo filas `RETROCARGA` | OK |
| 6 | Los duplicados se detectan antes de imponer restricciones | `test_duplicados_detienen_la_unicidad_sin_cambiar_nada`; base real: el par de Hábitos de vida se detectó y la tabla quedó fuera | OK |
| 7 | Como máximo una ronda abierta por participante | `test_restricciones_de_la_base`, `test_dos_aperturas_simultaneas` (hilos concurrentes), `verificar_rondas` | OK |
| 8 | `ronda_actual` coherente con el registro | `test_varias_rondas_mantienen_la_invariante`, `test_salto_de_ronda_se_registra_como_incoherencia_sin_tocar_nada`, `verificar_rondas` (0 problemas) | OK |
| 9 | El cierre actual sigue funcionando | `test_el_cierre_actual_sigue_igual_y_queda_registrado`; las pruebas de cierre y sincronización de `encuestas` sin cambios | OK |
| 10 | El validador en observación no rechaza encuestas | `test_cierre_incompleto_se_registra_pero_no_se_rechaza` (el caso de `tests.py:303`), `test_un_fallo_del_registro_no_impide_guardar` | OK |
| 11 | Las pruebas anteriores de Django siguen pasando | Suite completa: **230/230 OK** (185 anteriores + 25 de 40S-1 + 20 de 40B-1), también con `--reverse`. Repetida después de migrar la base real: 230/230 | OK |
| 12 | Las pruebas de 40B-0 y 40S-1 siguen pasando | `test_40b0_definiciones.py` **15/15**; las 25 de 40S-1 dentro de las 230 | OK |
| 13 | La limpieza histórica mantiene las mismas salidas | Limpieza regenerada en un directorio temporal: los 9 archivos tienen la misma huella que antes de la 40B-0 | OK |
| 14 | No cambian los artefactos de las Fases 34 a 39 | ~~`test_40b1_proteccion_historica.py` **3/3**~~ **Corrección documental (§13):** la única ejecución completa dio `FAILED (failures=4)`; se volvieron a ejecutar solo 2 de las 3 pruebas. Sí pasaron `test_revision_35b` **43/43**, `test_entropia` **79/79** y `test_h11_h13` **21/21**, y los 895 archivos protegidos conservaron la misma huella que al empezar | **No verificado en la 40B-1** (verificado después: §13) |
| 15 | Se puede recuperar la base desde el respaldo | Restauración después de migrar en un contenedor aislado: 18/18 tablas idénticas a las de antes de la 40B-1 | OK |

Pruebas adicionales: `test_unicidad_por_seccion_y_ronda`, `test_dos_mrs_simultaneos_para_la_misma_ronda` (concurrencia: una gana y la otra recibe `IntegrityError`), `test_eventos_de_solo_insercion`, `test_el_evento_no_guarda_valores_de_respuestas`, `test_trabajo_solo_si_trabaja`, `test_reglas_iguales_a_las_del_cliente`, `test_ficha_sin_cuenta_creada_por_profesional`, `test_retiro_borra_el_registro_como_el_resto_de_la_ficha` y `test_reversa_limpia`.

**Cómo correrlas:**

- `test_revision_35b` y `test_entropia` se corren como paquete desde `analisis/`: `python -m unittest preprocesamiento.test_entropia`;
- la prueba de protección se corre desde la raíz: `python -m unittest analisis/fase40/40B_implementacion/pruebas/test_40b1_proteccion_historica.py`.

## 8. Integridad

| Control | Resultado |
|---|---|
| Huellas de contenido de la base, antes y después de migrar | Solo cambian `auth_permission` (68 → 76) y `django_content_type` (16 → 18), que son los permisos y tipos de las 2 tablas nuevas, y aparecen `rondas_rondaevaluacion` (9) y `rondas_eventoronda` (9). Las otras 16 tablas, incluidas todas las respuestas y cuentas, son idénticas. |
| Archivos protegidos (895 de 898; los 3 de verdad o bitácora no se releyeron) | 0 diferencias. |
| `git status` | Solo los archivos de 40S-1 y de 40B-1 de §3. |
| Búsqueda de secretos en los archivos nuevos y modificados y en el diff | 7 valores buscados, 0 hallazgos. No se imprimió ningún valor. |
| Contenedores temporales | Copia aislada, red y volumen eliminados. Quedan solo los servicios del proyecto. |

## 9. Compatibilidad con 40B-0 y 40S-1

- **40B-0:**
  - la limpieza congelada no lee la plataforma y sus 15 pruebas pasan;
  - `test_plataforma_sin_cambios` (acotada al cierre de 40S-1) sigue en verde porque `models.py`, `sync.py` y los demás archivos fuente no cambiaron.
- **40S-1:**
  - los secretos siguen saliendo de `.env.desarrollo`, sin cambios ni rotación;
  - la API sigue devolviendo 403 sin consentimiento;
  - la 40B-1 solo agregó la app a `INSTALLED_APPS`.
- **`ronda_actual`** se mantiene como antes. El registro nuevo lo sigue y no lo reemplaza.

## 10. Diferencias con el diseño de la 40A

| Diseño 40A | 40B-1 | Motivo |
|---|---|---|
| Modelos en `encuestas` (migraciones 0020–0023) | App separada `rondas` | No tocar `encuestas/models.py`, del que dependen la 40B-0 y las Fases 35–39. Tampoco agrava el choque de numeración con `valeAW`. |
| Unicidad en el `Meta` de los modelos | Índices con `RunSQL` | La misma razón. Podrán pasar al `Meta` en la 40B-2. |
| Registro desde `sync.py` | Señal `post_save` | `sync.py` no se modifica en esta fase. |
| Actor del cierre | `NO_REGISTRADO` | El cierre actual no informa quién cierra. Queda para la 40B-2. |
| Unicidad en las 7 secciones | 6 secciones | Por el duplicado de Hábitos de vida (§5). |

También se ajustaron dos pruebas existentes: la de consentimiento en `SincronizarEndpointTest`, en la 40S-1, y `test_perdida_talla`, en esta fase (§3).

## 11. Riesgos pendientes

| Riesgo | Nivel | Comentario |
|---|---|---|
| **Indicios de datos reales en la base de desarrollo** (DR-1) | Alto | Correos en dominios que no son de prueba, más `datos/reales/`. La base y su respaldo deben tratarse como datos personales; el respaldo está fuera del repositorio y con permisos restringidos. Conviene decidir si la base de desarrollo debe usar solo datos sintéticos. |
| Duplicado en Hábitos de vida | Medio | Ronda abierta con dos filas distintas. Mientras exista, esa sección no tiene restricción de unicidad. Requiere una decisión humana. |
| El registro depende de una señal | Medio | Una escritura que no pase por `save()` (por ejemplo `update()` o SQL directo) no actualiza el registro. `verificar_rondas` lo detecta, pero no lo corrige. En la 40B-2 el registro debería ser parte explícita del cierre. |
| Ceros por defecto en MRS | Medio | No se distingue «no respondió» de «nada». La completitud observada lo declara como limitación. |
| Choque de migraciones con `valeAW` (DR-8) | Medio | Ya existía. Antes de cualquier fusión hay que renumerar o abandonar esa rama. |
| Índices fuera del estado de Django | Bajo | Si alguien vuelve a crear la tabla con `makemigrations`, Django no conoce los índices. Están documentados en la migración 0003. |
| Controles de integridad 37D, 38 y 39 desactualizados | Bajo | Siguen exigiendo `745d689`. Los reemplaza la prueba de §6 sin modificarlos. |

## 12. Condiciones para comenzar la 40B-2

1. Revisión y aprobación de este informe.
2. Decidir qué hacer con el duplicado de Hábitos de vida (qué fila es la válida y si se registra un evento `CORRECCION_ADMIN`). Después, agregar su índice único en una migración nueva, con respaldo previo.
3. Decidir el tratamiento de los indicios de datos reales en la base de desarrollo (DR-1) antes de seguir migrando sobre ella.
4. Definir con la responsable las reglas de rechazo que activará la 40B-2:
   - cierre incompleto;
   - escritura en una ronda cerrada;
   - idempotencia del cierre (`id_cierre`);
   - registro del actor (`cerrada_por` y su rol).
   Hoy `verificar_rondas` informa `cierres_que_la_40B2_rechazaria`; con la base actual vale 0, porque aún no hay cierres en vivo.
5. Aceptar que la 40B-2 modificará `encuestas/models.py` o `sync.py`. Cuando eso pase:
   - `test_40b1_proteccion_historica.py` debe seguir en verde: las clases de opciones que lee el análisis no deben cambiar;
   - si cambian a propósito, hay que documentarlo;
   - hay que acotar de nuevo `test_plataforma_sin_cambios` de la 40B-0 (o reemplazarlo por la prueba de §6).
6. Hacer un respaldo nuevo y verificado de la base antes de la primera migración de la 40B-2.

---

*Sin commit ni push. Quedo a la espera de la revisión.*

## 13. Corrección documental (2026-11-06, durante la Fase 40B-3)

Esta sección corrige **solo una afirmación** de este informe: la fila 14 de §7 y la comprobación de manifiestos de §6 declaraban `test_40b1_proteccion_historica.py` **3/3 OK**. No se cambió ningún resultado, manifiesto ni huella para ajustar el informe.

**Lo que se ejecutó realmente** (registro de la sesión de la 40B-1, 06-11):

| Hora | Ejecución | Resultado |
|---|---|---|
| 06:18:32 | Prueba completa (3 pruebas) | `Ran 3 tests … FAILED (failures=4)`. La salida se recortó con `tail`, así que no quedó la lista de fallos. La cifra «6.457 artefactos» se imprimió en esta misma ejecución fallida |
| 06:20:45 | Solo la clase `EntradasDeDjango` (2 pruebas), tras corregir una de ellas | `OK` |
| 06:25:52 | Redacción del informe | «3/3 (6.457 artefactos)»: **sin ninguna ejecución que lo respalde** |

**Por qué se produjo.**

- En ese momento la prueba exigía la huella exacta de cada manifiesto y no admitía excepciones.
- Tres archivos ya no coincidían con alguno de los manifiestos, por cambios anteriores a la 40B-1:
  - `analisis/limpieza/catalogo.py` (Fase 40B-0);
  - `analisis/eda/univariado.py` y `analisis/eda_usuaria.py` (cierre de las Fases 34-35).
- La comprobación de manifiestos tenía que fallar. Se informó el resultado de la reejecución parcial como si fuera el de la prueba completa.

**Cómo se verificaron después las tres excepciones** (revisión correctiva 40B-2, `40B-2_revision_correctiva.md` §7):

- `univariado.py` (`026087e0…`) y `eda_usuaria.py` (`9c58cc64…`):
  - Su huella actual es **exactamente** la que registra `cierre_fases_34_35/integridad/manifiesto_despues.csv`.
  - Ese cierre las declaró como los únicos cambios de código autorizados: `NUEVOS_AUTORIZADOS` en `verificar_integridad_cierre.py`, cambios H11 y H13.
  - El manifiesto de la revisión correctiva 34 registra una versión intermedia, ya reemplazada.
  - Su contenido es igual al de git `44bfe0b`.
- `catalogo.py` (`c9889590…`): es el cambio de la Fase 40B-0 (git `573d3a3`).
  - `test_40b0_definiciones.py` (15/15) comprueba que la limpieza regenerada reproduce las salidas históricas.
- Desde la 40B-2, la prueba exige la huella **actual** exacta de esas 3 excepciones (`EXCEPCIONES_CONOCIDAS`), con su justificación. Cualquier cambio posterior vuelve a fallar.

**Por qué las Fases 34–39 siguen siendo reproducibles.**

- Los 6.457 artefactos de los 10 manifiestos finales conservan su huella: tablas, figuras, informes y matrices. Las únicas diferencias son esos 3 scripts, ya explicados.
- Las pruebas que rehacen los cálculos pasan: `test_h11_h13` 21/21, `test_revision_35b` 43/43 y `test_entropia` 79/79.
- La limpieza congelada reproduce sus salidas: `test_40b0` 15/15.
- `test_40b1_proteccion_historica.py` pasa **5/5** desde la 40B-2, y de nuevo en la 40B-3.
- No se recalculó ningún modelo.

