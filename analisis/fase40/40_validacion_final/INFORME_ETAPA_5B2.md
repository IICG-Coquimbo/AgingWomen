# Etapa 5B-2 — Diagnóstico de respuestas y validación funcional

**Fecha:** 2026-11-09 · **Rama:** `datos-simulados` · **HEAD:** `573d3a31100c03519d47e220f4a065df3e9caf9a`

**Marcas usadas:** **Reproducido** = ocurrió en la prueba · **Confirmado en código** = se ve en el código, sin ejecutar un ataque · **Hipótesis** = compatible, sin confirmar · **Limitación** = lo que la prueba no permite afirmar.

---

## A. Resumen ejecutivo

**Se encontró y reprodujo un mecanismo que genera exactamente el patrón observado.** El problema no está en B1 ni en la captura de respuestas.

Una página de la encuesta con contenido antiguo puede borrar en el servidor lo que se guardó después. Basta con volver con el botón «Atrás» del navegador, o tener una segunda pestaña abierta. En la prueba, la secuencia fue:

1. La persona abre la encuesta y sale de ella con el cuestionario complementario vacío.
2. Vuelve a entrar, responde las 12 primeras preguntas y guarda. El servidor las tiene.
3. Pulsa «Atrás». El navegador restaura la página anterior, que sigue con el cuestionario vacío en memoria.
4. Responde las 4 últimas preguntas y finaliza. Esa página envía solo esas 4, y el servidor deja en blanco las demás.

**Resultado, igual en las dos repeticiones del recorrido completo:** ronda cerrada, MRS definitivo, 12 preguntas vacías, 4 con valor, condición faltante `tiene_pareja` y «Grupo aún no disponible». Es el mismo estado de la cuenta de prueba de la ficha 14.

**Lo que no se puede afirmar:** que esto fue lo que ocurrió en la ficha 14. No se consultó esa cuenta y no hay registro de cómo se navegó. Es la explicación mejor respaldada, pero sigue siendo una **hipótesis para ese caso**.

| Tema | Resultado |
|---|---|
| Recorrido normal: guardar, recargar, navegar, cerrar | **Correcto.** Las 16 respuestas persisten y B1 aparece |
| Defectos reproducidos | **3** (sección H): sobrescritura desde página antigua, guardado lento y clic perdido |
| Django | 387 ejecutadas: 386 aprobadas, 1 omitida, 0 fallidas |
| JavaScript | 21/21, con 1 prueba intermitente (sección E.2) |
| Condiciones de B1 | Correctas en las 8 pruebas adicionales |
| Integridad histórica, versiones seguras | 40B-0: 15/15 · 40B-1: 5/5, con 6.455 huellas correctas |
| Seguridad | 2 defectos confirmados en código, 2 riesgos por decidir, permisos correctos |
| Código de producción y base de desarrollo | Sin cambios |

**Se necesita una decisión sobre B1** (sección F.3): hoy los profesionales ven B1 solo en las estadísticas agregadas, y no en la ficha individual.

---

## B. Entorno aislado utilizado

| Elemento | Detalle |
|---|---|
| Código | Copia desechable de `src/`, idéntica al original según `diff` (0 diferencias) |
| Aplicación | Contenedor `aw_nav_web`, solo en `127.0.0.1:8010` |
| Base de datos | Contenedor `aw_nav_db`, PostgreSQL en memoria (`tmpfs`), sin puertos publicados, vacía al inicio |
| Secretos | Generados al azar para esta prueba y sin imprimirse. No se usó `.env` |
| Correo | Solo consola; ningún envío real |
| Conexión con desarrollo | Ninguna. La red `aw_nav_net` era propia |
| Archivos protegidos | Inaccesibles para la aplicación: solo se montó la copia de `src/` |
| Navegador | Chrome real, sin interfaz, perfil nuevo y un contexto separado por cuenta |
| Datos | Cuentas `@ficticio.cl` y RUT sintéticos |

Los resultados registran solo qué campos tienen dato, nunca sus valores. Al terminar se eliminaron los contenedores, la red, el perfil y la copia del código.

**Condiciones previas confirmadas:** informes 5A y 5B-1 leídos; respaldo de 2.034 archivos registrado como verificado (0 errores); rama, HEAD y estado de Git esperados.

---

## C. Diagnóstico de las 12 preguntas

### C.1 Recorrido de las respuestas

| Paso | Resultado | Evidencia |
|---|---|---|
| 1. Presentación | Correcto: 16 preguntas visibles | Chrome E1 |
| 2. Captura con JavaScript | Correcta con clics reales | Chrome E1 |
| 3. Almacenamiento local | Correcto, también sin conexión y tras recargar | E6 |
| 4. Envío | Correcto: 27 campos del bloque MRS (11 + 16) | E1 |
| 5. Validación en Django | Correcta, sin errores | E1 |
| 6. Persistencia | Correcta: 16 de 16 | E1 |
| 7. Recuperación al reabrir | Correcta: 16 de 16 | E2, E3 |
| 8. Conservación al cerrar | Correcta: 16 de 16 | E4 |

### C.2 ¿Las 12 primeras comparten algo?

**No comparten ninguna condición, componente ni ruta de guardado propia.** Las 18 preguntas pertenecen a la misma sección, usan la misma captura y se guardan en el mismo registro.

Tres de ellas (`menstruacion_llega`, `tipo_sangrado`, `usa_metodo_anticonceptivo`) dependen de la fecha de última menstruación, pero eso no explica las otras nueve.

**El corte entre «12» y «4» no proviene del formulario.** Lo define en qué punto de la encuesta la persona pasó a usar la página antigua. Con otro punto de corte, el patrón sería distinto.

### C.3 Causa del mecanismo reproducido

Combina dos comportamientos:

1. **Cliente.** La encuesta guarda las respuestas en la memoria de la página y no se actualiza cuando el navegador la restaura con «Atrás», porque no atiende `pageshow` (`encuesta.js:472-476`). Tampoco se entera de lo guardado desde otra pestaña. Al enviar, incluye solo lo que tiene en memoria (`encuesta.js:1304-1306`).
2. **Servidor.** Cada guardado reemplaza el registro completo: una pregunta que no viene en el envío queda en blanco (`sync.py:277-291`). Solo se comprueba la ronda (`sync.py:442-458`), así que no se detecta que el envío parte de una versión antigua.

### C.4 Hipótesis probadas

| Id | Situación | Resultado |
|---|---|---|
| D1 | Salir al menú sin guardar y volver | **Descartada:** se conserva todo |
| D2 | Guardar, recargar y seguir | **Descartada:** 16 de 16 |
| D3 | Sesión eliminada a mitad de la encuesta | **Descartada como causa:** lo local se conserva y se envía al volver a ingresar |
| D4 | Dos pestañas | **Reproducida:** quedan 4 de 16 |
| D5 | Botón «Atrás» | **Reproducida:** quedan 4 de 16 |
| D8 | «Atrás» y cierre completo | **Reproducida, 2 de 2:** mismo estado final que la ficha 14 |
| D6 | Responder mientras un guardado lento sigue en curso | **Reproducida, con otro patrón:** se pierden las últimas |
| D7 | Clic justo después de escribir la fecha | **Reproducida:** se pierde ese clic |

**Para cerrar el caso de la ficha 14** bastaría saber si durante esa prueba se usó «Atrás», otra pestaña u otro dispositivo.

---

## D. Resultados de las pruebas Chrome

| Id | Escenario | Comprobación | Resultado |
|---|---|---|---|
| E1 | Completar el complementario y guardar | Envío 200; servidor 16 de 16 | **Aprobado** |
| E2 | Recargar antes de cerrar | Pantalla 16 de 16; servidor igual | **Aprobado** |
| E3 | Navegar entre secciones y regresar | Pantalla 16 de 16 | **Aprobado** |
| E4 | Cerrar la ronda con todo válido | `cerrada`; `finalizada_verificable`; MRS definitivo; servidor 16 de 16 | **Aprobado** |
| E4 | Tablero con MRS y B1 | «Grupo 4 — Entre múltiples actividades», descripción, aviso y MRS aparte | **Aprobado** |
| E5 | Opcionales vacías | Cierra; MRS definitivo; «Grupo aún no disponible» | **Aprobado** |
| E6 | Interrupción de conexión | Sin envío durante el corte; 16 de 16 tras recargar sin conexión; al volver, envío 200 y servidor 16 de 16 | **Aprobado** |
| D1-D8 | Hipótesis | Ver sección C.4 | Según se indica |
| P | Permisos por perfil | Ver sección G.5 | **Aprobado** |
| F | Estadísticas profesionales con B1 | Tabla de 4 grupos; promedio solo donde la protección lo permite | **Aprobado** |
| S | «Atrás» tras salir | Vuelve al ingreso; el tablero no reaparece | **No concluyente** (sección G.2) |

**Sin errores de JavaScript ni diálogos inesperados en E1-E4.**

**Limitaciones**

- Chrome se ejecutó sin interfaz. En ese modo, la caché de «Atrás» no se activaba por un control de memoria, así que D5 y D8 se ejecutaron con `--enable-features=BackForwardCache --disable-features=BackForwardCacheMemoryControls`. **No se verificó en Chrome con interfaz, celulares ni otros navegadores.**
- La lista desplegable y la fecha de nacimiento se completaron por programa. Los demás controles usaron clics y texto reales.
- D3 eliminó la sesión en el servidor. Es distinto del cierre por inactividad, que cubren las pruebas `InactividadTest`.
- **No se ejecutó en Chrome el retiro presencial (PI-08),** porque no está entre los escenarios de esta etapa.

---

## E. Resultados de las pruebas Django y JavaScript

### E.1 Django, en base temporal desechable

| Control | Resultado |
|---|---|
| `manage.py check` | Sin problemas |
| `makemigrations --check --dry-run` | Sin cambios |
| Suite completa | **387 ejecutadas: 386 aprobadas, 1 omitida, 0 fallidas** (206 s) |

La suite incluye rondas, MRS, guardado y recuperación, B1 y orientaciones.

**Omitida:** `test_mapa_identico_a_la_definicion_documentada`, porque necesita `analisis/`, que no se montó.

**Adicionales de esta etapa, solo en la copia aislada:** 8 pruebas de condiciones de B1, 8 aprobadas.

### E.2 JavaScript

21 pruebas. La primera ejecución dio **20 aprobadas y 1 fallida**, y las tres siguientes 21 de 21.

La prueba intermitente es «P6: la participación viaja en cada envío…» (`test_encuesta_sync.mjs:491,494`). Tras una espera fija de 120 ms exige que no quede ninguna clave local.

- Falló en la ejecución completa y en 2 de 8 ejecuciones aisladas, todas mientras corría la suite Django.
- No volvió a fallar en 16 ejecuciones aisladas ni en 36 en paralelo, ya sin la suite.
- **Hipótesis:** es una dependencia de tiempos bajo carga. No se identificó la clave restante, así que no se puede descartar un borrado local incompleto en ese caso.

### E.3 Integridad histórica

Los originales de 40B-0 y 40B-1 **no se ejecutaron ni se modificaron**. Se usaron copias en el área aislada, con una barrera que impide abrir los cuatro archivos protegidos. No se activó en ninguna ejecución.

| Prueba | Resultado | Diferencia con el original |
|---|---|---|
| 40B-0 segura | 15 de 15 | El caso `usuaria` se reemplazó por el caso `profesora` |
| 40B-1 segura | 5 de 5; 6.455 huellas correctas; 3 excepciones ya documentadas | Excluye también el archivo protegido; no comprueba ni la existencia de los omitidos |

**Limitación:** la reproducción de la limpieza del conjunto `usuaria` queda sin verificar en esta etapa. La cifra 6.455 frente a las 6.457 documentadas se explica por las dos apariciones del archivo excluido en los manifiestos.

---

## F. Validación de MRS y B1

### F.1 Condiciones de B1

| Condición | Resultado | Comportamiento | Evidencia |
|---|---|---|---|
| Todas válidas | Grupo visible | Nombre, descripción, advertencia y MRS aparte | E4; prueba de los 4 grupos |
| Ronda abierta | Sin grupo | «Grupo aún no disponible» | `test_grupo_ausente` |
| Cerrada no verificable | Sin grupo | Igual | Adicional |
| MRS no definitivo | Sin grupo | Igual | Adicional |
| Trabajo ausente | Sin grupo | Igual | Adicional |
| Pareja ausente | Sin grupo | Igual | Adicional; E5 |
| Pareja «No sabe» | Sin grupo | Igual | Adicional |
| Días de ejercicio ausentes | Sin grupo | Igual | Adicional; E5 |
| Última ronda incompleta y anterior completa | Sin grupo; **no usa la anterior** | Igual | Adicional |
| Ronda sin dato de trabajo al cierre | Sin grupo; **no infiere** | Igual | `test_no_infiere_de_datos_actuales` |
| Independencia de orientaciones | Se cumple | Misma selección con y sin B1 | `test_seleccion_igual_con_y_sin_contexto` |

El algoritmo no se modificó y no se imputó ninguna respuesta.

### F.2 MRS

Las pruebas de puntaje, dimensiones, estados y ausencia de severidad están aprobadas dentro de la suite. En Chrome, el cierre con 11 ítems queda como `finalizada_verificable` y MRS definitivo, y el tablero muestra el resultado.

### F.3 Observaciones sobre B1

| Observación | Detalle |
|---|---|
| **Vista profesional: requiere decisión** | Tu instrucción indica que B1 será visible también para profesionales. Hoy lo ven **solo como agregado** en «Estadísticas generales». La ficha individual no lo muestra, y una prueba exige que así sea (`test_acceso_entre_usuarias`). Hay que decidir si eso basta o si debe aparecer en la ficha |
| Explicación incompleta | «Grupo aún no disponible» no indica qué falta. Además, dice que aparecerá al finalizar una ronda con esas preguntas (`_mi_grupo.html:18`), pero una ronda ya cerrada no se puede completar: la persona tendría que responder una ronda nueva |
| Protección en estadísticas | Con pocas personas sin grupo, la supresión complementaria oculta también el grupo siguiente. En la prueba se publicó 1 promedio de 4 filas. Es el comportamiento previsto |

---

## G. Hallazgos de seguridad

Revisión no intrusiva. No se hicieron ataques, pruebas de fuerza bruta ni envíos de correo.

| # | Tema | Clasificación | Evidencia | ¿Antes de participantes reales? |
|---|---|---|---|---|
| 1 | Ingreso sin límite de intentos | **Defecto confirmado en código** | `usuarios/urls.py:14-22` usa `LoginView` y `LoginRutForm` (`forms.py:109`) sin control. `intentos.py` cubre solo flujos presenciales | **Sí** |
| 2 | Salud en caché del navegador | **Riesgo potencial** | `Cache-Control` ausente en `/mi-tablero/` y en la ficha (observado; `tablero.py:33`, `profesional.py:105`). Las estadísticas sí llevan `no-store` | **Sí**, por ser una corrección pequeña |
| 3 | Protección de datos almacenados | **Riesgo por decidir** | Sin cifrado de campo en los modelos, aunque la librería está en `requirements.txt`. Los volcados de base no están cifrados. En el navegador, lo local sí va cifrado | **Sí:** cifrado de disco y respaldos, o cifrado de campo |
| 4 | Contraseña temporal por correo | **Defecto confirmado en código** | `usuarios/views.py:18-32` la envía en claro y solo *recomienda* cambiarla | **Sí** |
| 5 | Separación de permisos | **Correcta** | Matriz G.5 | Decidir el acceso amplio a fichas |

### G.2 Caché y botón «Atrás»

Tras salir, «Atrás» llevó al ingreso y el tablero no reapareció. **No es concluyente:** en esa prueba la caché de «Atrás» no se activó. El mecanismo de la sección C sí demuestra que esa caché restaura páginas de esta plataforma, así que el riesgo sigue vigente.

**Lo que el Service Worker guarda:** solo la estructura de `/encuesta/`, el esquema y los archivos estáticos. No guarda respuestas (`sw.js`).

### G.5 Matriz de permisos (observada en Chrome)

| Ruta | Sin sesión | Participante | Profesional | Superusuario |
|---|---|---|---|---|
| `/mi-tablero/` | Redirige | 200 | Redirige | 200 |
| `/profesional/buscar/` | Redirige | 403 | 200 | 403 |
| `/profesional/estadisticas/` | Redirige | 403 | 200 | 403 |
| Ficha de otra persona | Redirige | 403 | 200 | 403 |
| `/administracion/` | Redirige | 403 | 403 | 200 |
| API con ficha de otra persona | Redirige | 403 | 200 | 403 |

**Decisión institucional pendiente:** cualquier profesional puede abrir cualquier ficha (`profesional.py:103`), porque no hay asignación por paciente.

---

## H. Defectos reproducidos, con rutas y líneas

| Id | Defecto | Rutas y líneas | Reproducción | Efecto | Severidad |
|---|---|---|---|---|---|
| **DF-1** | Un guardado desde una página con contenido antiguo borra lo guardado después | `src/static/js/encuesta.js:472-476` (sin atención a `pageshow`), `:1304-1306`; `src/apps/encuestas/sync.py:277-291`, `:442-458` | D4, D5, D8 (2 de 2) | **Pérdida silenciosa de respuestas** y B1 no disponible | **Crítica** |
| **DF-2** | Lo respondido durante un guardado en curso se marca como enviado | `src/static/js/encuesta.js:1406-1408`, `:539` | D6: pantalla 16, servidor 12, tras recargar 12 | **Pérdida silenciosa** de lo respondido en ese intervalo | **Alta** |
| **DF-3** | El primer clic después de escribir la fecha se pierde | `src/static/js/encuesta.js:1131-1133`, `:1190-1198` | D7 | Una respuesta queda sin marcar | Media |

**Observaciones sin pérdida de datos**

| Id | Observación | Ruta |
|---|---|---|
| OB-1 | Si el servidor redirige al ingreso, un guardado manual no avisa del fallo tras mostrar «Cambios guardados. Sincronizando…». Las respuestas se conservan y se envían después | `encuesta.js:1242-1244`, `:1442-1447` |
| OB-2 | Prueba JavaScript intermitente | `test_encuesta_sync.mjs:491,494` |
| OB-3 | Explicación de B1 incompleta | `_mi_grupo.html:18` |

### Hipótesis no confirmadas

- Que DF-1 sea lo que ocurrió en la ficha 14.
- Que la prueba intermitente se deba solo a tiempos.

---

## I. Correcciones mínimas recomendadas y prioridades

**Ninguna se aplicó.** Requieren la autorización de la siguiente subetapa.

| Prioridad | Id | Corrección mínima | Defecto |
|---|---|---|---|
| **P0** | C-1 | Recargar la encuesta cuando el navegador la restaura desde «Atrás» (`pageshow` con `persisted`) | DF-1 |
| **P0** | C-2 | Control de versión: el cliente envía la versión que conoce y el servidor responde 409 si está desactualizada, conservando lo local. Cubre pestañas y dispositivos, que C-1 no cubre | DF-1 |
| **P0** | C-3 | Marcar como enviado solo si no hubo cambios desde que comenzó el envío | DF-2 |
| P1 | C-4 | Volver a dibujar solo si cambian las preguntas visibles, sin interrumpir el clic | DF-3 |
| P1 | C-5 | Límite de intentos en el ingreso, reutilizando `intentos.py` | Seguridad 1 |
| P1 | C-6 | `no-store` en tablero y ficha | Seguridad 2 |
| P1 | C-7 | Cambio obligatorio de la contraseña temporal, o enlace de creación | Seguridad 4 |
| P2 | C-8 | Agregar pruebas permanentes de DF-1 a DF-3 y corregir la prueba intermitente | OB-2 |
| P2 | C-9 | Precisar el mensaje de B1 | OB-3 |

**No se recomienda hacer que el servidor ignore los campos ausentes.** El cliente depende de ese comportamiento para vaciar las respuestas de preguntas que quedaron ocultas (`encuesta.js:1301-1303`).

**Decisiones necesarias**

| Id | Decisión |
|---|---|
| D-1 | ¿B1 en la ficha profesional individual, o basta el agregado? |
| D-2 | ¿Se usó «Atrás», otra pestaña u otro dispositivo en la prueba de la ficha 14? |
| D-3 | Cifrado de datos almacenados y acceso de profesionales a todas las fichas |
| D-4 | ¿Se repite el caso `usuaria` de 40B-0 con autorización para ese archivo? |

**Sobre los datos ya registrados:** el borrado no deja rastro, así que las respuestas perdidas no se pueden recuperar ni identificar con certeza, y tampoco deben imputarse.

---

## J. Control de integridad

| Control | Inicio | Final | Resultado |
|---|---|---|---|
| Rama | `datos-simulados` | `datos-simulados` | Igual |
| HEAD | `573d3a31…f9a` | `573d3a31…f9a` | Igual |
| Stash | 0 | 0 | Igual |
| Índice | Vacío | Vacío | Igual |
| `git status --porcelain` | 93 líneas | 93 líneas | Idéntico |
| Metadatos, frente al control de la Etapa 5A | 7.022 archivos | 7.024 archivos | 0 cambiados, 0 retirados; 2 nuevos: los informes 5A y 5B-1 |
| Contenedores de desarrollo | En ejecución | En ejecución | Sin intervenir |
| Volúmenes Docker | 5 | 5 | Igual |
| Entorno de prueba | — | Eliminado | 0 contenedores y redes `aw_nav` |

Este informe queda en `40_validacion_final/`, carpeta que ya figuraba como no rastreada, así que no agrega líneas al estado de Git. Después de escribirlo, `git status --porcelain` sigue idéntico al inicial.

**Restricciones cumplidas**

- No se modificó código de producción, las Fases 34–39R ni las tesis.
- No se usó la base de desarrollo. No se consultaron ni alteraron registros reales.
- No se abrieron los cuatro archivos protegidos ni archivos `.env`.
- No se ejecutaron 40B-0 ni 40B-1 originales, ni análisis estadísticos. La versión segura de 40B-0 repite en memoria la limpieza del caso `profesora` para compararla con la salida histórica; no genera resultados nuevos.
- No hubo migraciones en bases persistentes, envíos de correo, ataques, commits, pushes ni resets.

**Evidencia de esta etapa**, sin valores de respuestas, en:
`C:\Users\scarl\AppData\Local\Temp\claude\c9607f9123dc8896\19178f78-df2e-430a-a94a-e019ba58bb39\scratchpad\5b2\`

Es una carpeta temporal. Las cifras de los escenarios E5, E6, D1-D4, D6 y D7 constan en este informe, porque sus archivos JSON se sobrescribieron en ejecuciones posteriores.
