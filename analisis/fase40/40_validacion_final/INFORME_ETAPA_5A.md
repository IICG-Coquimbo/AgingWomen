# Etapa 5A — Diagnóstico y plan de validación final de la plataforma

**Fecha:** 2026-11-09 · **Rama:** `datos-simulados` · **HEAD:** `573d3a31100c03519d47e220f4a065df3e9caf9a`
**Alcance:** revisión de solo lectura de la Fase 40. No se ejecutaron pruebas, no se modificó código y no se consultaron registros en esta etapa.

**Evidencia usada en todo el informe**

| Marca | Significado |
|---|---|
| **V** | Verificado directamente en el código actual, sin ejecutarlo |
| **D** | Documentado en un informe de la Fase 40; no se repitió aquí |
| **NV** | No verificado |

Las rutas de código son relativas a `src/`, salvo que se indique otra cosa.

---

## A. Resumen ejecutivo

**La Fase 40 está funcionalmente construida, pero no está lista para cerrarse.** Hay cuatro asuntos que deben atenderse antes de la validación final:

1. **Posible pérdida de respuestas en la encuesta (prioridad máxima).** En una prueba con cuenta sintética, las 12 primeras preguntas del «Cuestionario complementario» quedaron vacías, incluida la de pareja, aunque la responsable indica haberla respondido. Las 4 últimas se guardaron. Por eso apareció «Grupo aún no disponible». La causa sigue sin identificarse (sección E.3).
2. **Dos pruebas de integridad abren un archivo protegido.** Las pruebas 40B-0 y 40B-1 leen `datos/sintetico/dataset_usuaria_sucio.csv`. No pueden ejecutarse tal como están sin vulnerar la restricción vigente (sección C.3).
3. **Todo el trabajo sigue solo en este equipo.** La Fase 40 completa está sin commit: 34 archivos modificados y 58 entradas nuevas, entre ellas la app `rondas` y sus migraciones (sección B.4).
4. **Faltan las pruebas integrales finales.** El último recorrido integral en Chrome es del 2026-11-06, anterior al tablero profesional, a la Etapa 2 y al retiro presencial, que nunca se probó en navegador.

**Lo que sí está en buen estado:**

- Existen 387 pruebas Django y 21 de JavaScript (recuento V). Su último resultado informado es 386 aprobadas, 1 omitida y 0 fallidas (D, 2026-11-07).
- Ningún archivo de `src/` cambió después de ese informe (V, por fecha de modificación).
- B1 ya cumple la decisión vigente: es visible, tiene advertencias, conserva los promedios profesionales y no interviene en las orientaciones (V).

**La revisión documental de seguridad encontró cuatro puntos que los informes de la Fase 40 no recogían** (sección F.2). El más relevante para el uso con personas reales es que el ingreso con RUT y contraseña no tiene límite de intentos.

**El principal requisito para usar la plataforma con participantes reales sigue siendo externo:** validación clínica del catálogo, validación ético-jurídica y rotación de secretos.

---

## B. Inventario de funcionalidades

### B.1 Implementadas

| Funcionalidad | Evidencia | Dónde |
|---|---|---|
| Registro con código por correo y límite de intentos | V | `apps/usuarios/views.py:66-155` |
| Ingreso por RUT; RUT guardado solo como hash | V | `apps/usuarios/backends.py`, `rut.py:55` |
| Perfiles usuaria, profesional y superusuario | V | `decorators.py`, `administracion.py:29-138` |
| Consentimiento en línea y control en la API | V | `decorators.py:9-47`, `api.py:89` |
| Consentimiento presencial con folio, custodia y declaración | V | `apps/usuarios/presencial.py:69-73`, migración `usuarios/0004` |
| Retiro propio: borrado y comprobante firmado | V / D | `apps/encuestas/retiro.py:34,54` |
| Retiro presencial sin cuenta | V / D | `retiro.py:108-111` |
| Encuesta por esquema y por rol, con condicionales | V | `esquema.py:280`, `condicionales.py` |
| Almacenamiento local cifrado por cuenta | V / D | `encuesta.js`, `apps/usuarios/privacidad.py` |
| Sincronización protocolo 2 con conflictos 409 | V | `sync.py:380-488` |
| Cierre validado, transaccional e idempotente | V | `apps/rondas/cierre.py:87-127` |
| MRS con ítems nulos y regla única de resultado | V | `apps/rondas/resultado_mrs.py:126-158` |
| Protección de rondas cerradas | V / D | `apps/rondas/proteccion.py`, `sync.py:271` |
| Tablero con evolución MRS | V | `tablero.py:26-43`, `evolucion.py` |
| **Visualización de B1 con nombres y advertencias** | V | `contexto_participante.py:45-92`, `_mi_grupo.html` |
| Estadísticas profesionales con k = 5 | V / D | `estadisticas.py`, `profesional.py:115-124` |
| Búsqueda por RUT solo por POST | V | `profesional.py:28-30` |
| Cierre de sesión por inactividad | V | `apps/usuarios/inactividad.py:45-66` |
| Límite de intentos de contraseña en flujos presenciales | V / D | `apps/usuarios/intentos.py` |
| Secretos obligatorios por entorno | V | `settings.py:42,66,132,170` |
| Comandos de solo lectura `verificar_rondas` y `registros_sin_consentimiento` | V / D | `management/commands/` |

### B.2 Parcialmente implementadas

| Funcionalidad | Qué falta | Evidencia |
|---|---|---|
| Orientaciones educativas | Catálogo `borrador_no_validado`; apagadas por defecto y limitadas a `DEBUG` (`orientaciones.py:65-69`). Faltan revisión clínica y decisiones R-1, R-2 y R-4 | V / D |
| Constancia de retiro | El comprobante no se guarda en el servidor. Falta base legal y plazo; un mismo folio de revocación puede usarse dos veces | D |
| Perfil de producción | Falta HTTPS real, registro de errores, servidor de estáticos y caché compartida para el límite de intentos | V / D |
| Gestión de secretos | Ya están por entorno, pero no se han rotado; siguen en el historial de GitHub | D |
| Respuestas apartadas en conflictos | Se conservan en el dispositivo, sin pantalla para recuperarlas | D |
| Etapa menopáusica en estadísticas | Se muestra como no disponible; la plataforma no la registra | D |
| Trazabilidad de orientaciones (R-8) | La versión del catálogo solo queda en la página | D |

### B.3 Pendientes

| Pendiente | Tipo |
|---|---|
| Causa de la pérdida de respuestas (E.3) | Defecto por investigar |
| Pruebas integrales finales y Chrome del retiro presencial | Validación |
| Rotación de `SECRET_KEY` con `SECRET_KEY_FALLBACKS` | Seguridad |
| Commit de la Fase 40 | Requiere autorización |
| Informe de la Fase 40D-H (no existe) | Documental |
| Actualización de documentos sobre B1 (E.4) | Documental |
| Validación clínica y ético-jurídica | Externa |
| Despliegue (Fase 18) | Externa |
| Repetir B1 con datos reales antes de su uso real | Metodológica |

### B.4 Archivos pendientes de incorporación a Git (V)

Total: 92 entradas en `git status`: 34 modificadas y 58 nuevas.

| Grupo | Entradas | Observación |
|---|---|---|
| `src/` modificados | 30 | Código y plantillas de la Fase 40 |
| `src/` nuevos | 35 | Incluye toda `src/apps/rondas/`, `contexto_participante.py`, `estadisticas.py`, `orientaciones*`, migraciones `encuestas/0020` y `usuarios/0004` |
| `analisis/fase40/` | 18 | 1 modificado y 17 nuevos: informes, pruebas y evidencias |
| Raíz, modificados | 3 | `.env.example`, `README.md`, `docker-compose.yml` |
| Otros, nuevos | 6 | Fuera de la Fase 40 |

**Fuera de cualquier commit de la Fase 40:** `analisis/fase38/38R_…`, `analisis/fase39/39R_…`, `auditoria_*`, `cierre_metodologico_4B/` y `Tesis Ver.9.pdf`. No se incorporan sin autorización.

---

## C. Estado de las pruebas existentes

### C.1 Recuento y último resultado

| Conjunto | Pruebas (V) | Último resultado (D) | Fecha |
|---|---|---|---|
| Django, 14 archivos | 387 | 386 aprobadas, 1 omitida, 0 fallidas | 2026-11-07 |
| JavaScript, `pruebas_js/test_encuesta_sync.mjs` | 21 | 21/21 | 2026-11-07 |
| 40B-0 y 40B-1 | 20 (D) | 20/20; 6.457 artefactos | 2026-11-07 |
| `makemigrations --check` | — | Sin cambios | 2026-11-07 |
| Chrome integral | 30 | 30/30 | 2026-11-06 |
| Chrome privacidad | 26 | 26/26 | 2026-11-06 |
| Chrome orientaciones | 17 | 17/17 | 2026-11-06 |
| Chrome tablero profesional | 10 | 10/10 | 2026-11-07 |
| Chrome Etapa 2 | 23 | 23/23 | 2026-11-07 |

**Detalle de los archivos Django (V):** `encuestas/tests.py` 133; `usuarios/tests.py` 49; `rondas/test_40b2.py` 41; `encuestas/test_contexto_participante.py` 21; `rondas/tests.py` 20; `rondas/test_40c.py` 19; `usuarios/test_pendientes_consentimiento.py` 17; `encuestas/test_orientaciones.py` 16; `rondas/test_40b3.py` 15; `usuarios/test_privacidad.py` 13; `usuarios/test_seguridad_config.py` 13; `encuestas/test_consentimiento_api.py` 12; `usuarios/test_etapa2.py` 10; `encuestas/test_estadisticas.py` 8.

La prueba omitida es `test_mapa_identico_a_la_definicion_documentada`: `analisis/` no está montado en Docker, porque el servicio solo monta `./src`. Por eso, **en la ejecución normal no se compara el mapa de B1 con su definición** (V).

### C.2 Dónde se ejecutan y qué pueden afectar

| Clase | Conjuntos | Efecto sobre datos |
|---|---|---|
| **Sin base de datos** | Node (`pruebas_js`) | Ninguno |
| **Base temporal** | Suite Django | Django crea y destruye una base `test_…`. No toca la base de desarrollo |
| **Entorno aislado** | Chrome con contenedores `aw_nav_*`, puerto 8010, base nueva y cuentas `@ficticio.cl` | Ninguno sobre desarrollo. Crea y elimina contenedores |
| **Base persistente** | `verificar_rondas`, `registros_sin_consentimiento`, pruebas manuales en `localhost:8000` | Los comandos solo leen, pero acceden a una base que **puede contener datos reales (DR-1)**. Las pruebas manuales escriben |

### C.3 Pruebas que no se deben ejecutar tal como están

| Prueba | Problema (V) |
|---|---|
| `analisis/fase40/40B_implementacion/pruebas/test_40b1_proteccion_historica.py` | Excluye por nombre solo `verdad` y `bitacora` (`NO_LEER`, línea 39). `dataset_usuaria_sucio.csv` figura en dos manifiestos y se abriría para calcular su huella |
| `analisis/fase40/40B_implementacion/pruebas/test_40b0_definiciones.py` | El caso `usuaria` (línea 37) procesa ese mismo archivo para comparar las salidas de limpieza |

Para ejecutarlas hace falta autorización expresa o una versión que excluya ese archivo. Sus resultados anteriores (20/20) se obtuvieron abriéndolo.

### C.4 Otras limitaciones de la cobertura

- **Los scripts de Chrome no se conservaron.** Solo quedan sus resultados en JSON y capturas (V). Hay que reescribirlos.
- **Las pruebas de B1 no usan la interfaz real:** llaman directamente a `sincronizar_payload` con el contenido ya armado (`test_contexto_participante.py:35-51`).
- **El JavaScript no prueba el «Cuestionario complementario»:** `test_encuesta_sync.mjs` no menciona esa sección (V).
- **`test_participante_no_ve_grupo_ni_estadistica_y_avisos_se_mantienen`** (`test_contexto_participante.py:173`) solo revisa la sección de orientaciones. Su nombre induce a error.
- **`test_40c.py:373-374`** quita la sección de B1 antes de buscar términos prohibidos. Es correcto, pero esa sección no pasa por este control.

---

## D. Matriz de pruebas integrales pendientes

**Riesgo sobre registros:** *Nulo* = sin base de datos · *Temporal* = base de prueba · *Aislado* = entorno desechable · *Persistente* = base de desarrollo.

**Estado:** *Cubierta* = existe prueba, con resultado D · *Parcial* = cubre solo parte · *Sin cubrir* · *Externa*.

**Datos sintéticos:** todas usan cuentas ficticias. La columna indica lo que necesita cada caso.

### D.1 Registro, autenticación y perfiles

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-01 | Registro | Código correcto crea la cuenta; se limitan intentos | `usuarios/tests.py` `RegistroTest` | RUT y correo ficticios | Temporal | Cubierta | Media |
| PI-02 | Ingreso | RUT y contraseña; redirección según rol | `LoginPorRutTest`, `LoginYMenuTest` | Una cuenta por rol | Temporal | Cubierta | Media |
| PI-03 | Separación de perfiles | Cada rol solo entra a lo suyo | `AccesoRestringidoTest`, `AdministracionSistemaTest`, `AdminGestionCuentasTest` | Tres roles | Temporal | Cubierta | Alta |
| PI-04 | Intentos de ingreso repetidos | Hoy no hay límite; decidir el comportamiento esperado | Ninguno | Una cuenta | Temporal | Sin cubrir | Alta |

### D.2 Consentimiento informado

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-05 | Consentimiento en línea | Sin él no hay encuesta ni API (403) | `ConsentimientoInformadoTest`, `ConsentimientoApiTest` | Cuenta sin aceptar | Temporal | Cubierta | Alta |
| PI-06 | Consentimiento presencial | Exige folio, custodia y declaración; con cuenta, su contraseña | `test_etapa2`; Chrome 23/23 | Con y sin cuenta | Temporal / Aislado | Cubierta | Alta |
| PI-07 | Retiro propio | Borra todo y entrega comprobante verificable | `RetiroDelEstudioTest`, `test_etapa2` | Ficha con rondas | Temporal / Aislado | Cubierta | Alta |
| PI-08 | Retiro presencial | Exige folio, declaración, confirmación y contraseña | `RetiroPresencialTest` | Persona sin cuenta | Temporal / Aislado | **Parcial: sin Chrome** | **Máxima** |
| PI-09 | Registros antiguos | Excluidos, bloqueados y conservados | `RegistroAntiguoSinConstanciaTest` | Ficha sin consentimiento | Temporal | Cubierta | Media |

### D.3 Encuesta y condicionales

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-10 | Esquema por rol | Campos según rol; condicionales en cadena | `EsquemaTest`, `PaginaEncuestaTest` | Dos roles | Temporal | Cubierta | Media |
| PI-11 | Filtro de edad | 40 a 65 años; excepciones | `IdentificacionFormEdadTest`, `SincronizacionEdadTest` | Fechas límite | Temporal | Cubierta | Media |
| PI-12 | Sección condicional «Trabajo» | Solo aparece si la persona trabaja | `EsquemaTest` | Ambos casos | Temporal | Cubierta | Media |

### D.4 Guardado y recuperación

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-13 | Unión de las dos pantallas MRS | Un solo registro con ambos bloques | `SincronizacionTest` (`tests.py:203-219`) | Payload directo | Temporal | Cubierta en servidor | Alta |
| **PI-14** | **Cuestionario complementario desde la interfaz real** | **Las 16 preguntas persisten tras «Guardar cambios» y tras «Finalizar»** | Ninguno | Cuenta nueva; todas respondidas | Aislado | **Sin cubrir** | **Máxima** |
| PI-15 | Recarga, volver al tablero y regresar | No se pierde nada sin enviar | Node, parcial | Encuesta a medio responder | Aislado | Parcial | **Máxima** |
| PI-16 | Respuesta durante un guardado | Lo respondido durante el envío no se da por enviado (`encuesta.js:1406`) | Ninguno | Respuesta lenta simulada | Nulo | Sin cubrir | Alta |
| PI-17 | Precarga de la ronda en curso | Se abre con lo ya guardado | `EncuestaPorProfesionalTest`; Chrome | Dos dispositivos | Temporal / Aislado | Cubierta | Media |

### D.5 Sin conexión y sincronización

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-18 | Finalizar sin conexión | Queda pendiente; reintento con el mismo `id_cierre` | Node | Ninguno | Nulo | Cubierta | Alta |
| PI-19 | Errores 401, 403, 409 y 500 | Nada se pierde; se informa | Node; `test_consentimiento_api` | Ninguno | Nulo / Temporal | Cubierta | Alta |
| PI-20 | Local cifrado y «Salir» | Sin clave no se ve nada; lo pendiente se conserva | Node; `ClaveLocalTest`; Chrome | Dos cuentas | Aislado | Cubierta | Alta |
| PI-21 | Service Worker actualizado (v20) | Reemplazo sin servir datos antiguos | `test_40c` (versión) | Dos versiones | Aislado | Parcial | Media |

### D.6 Cierre y verificabilidad de rondas

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-22 | Cierre completo o rechazado | Solo cierra con lo obligatorio; informa faltantes | `CierreTest` | Completa e incompleta | Temporal | Cubierta | Alta |
| PI-23 | Idempotencia y concurrencia | Un solo cierre; reintentos seguros | `IdempotenciaYTardiasTest`, `ConcurrenciaCierreTest` | Dos envíos | Temporal | Cubierta | Alta |
| PI-24 | **Cerrada y definitiva** | Puntaje definitivo; estado «Finalizada y verificable» | `test_40b3` `CerradaVerificableTest` | 11 ítems | Temporal | Cubierta | **Máxima** |
| PI-25 | **Cerrada y no verificable** | Sin número; «Histórica no verificable» | `HistoricaNoVerificableTest`, `MRSAnteriorTest` | Ceros antiguos | Temporal | Cubierta | **Máxima** |
| PI-26 | **Definitiva sin cierre validado** | Retrocargada: resultado definitivo, sin fecha y sin B1 | `test_40c` `FechasTest` | Ronda retrocargada | Temporal | Parcial: falta B1 | Alta |
| PI-27 | **Abierta** | Provisional o parcial, nunca definitiva | `RondaAbiertaTest` | Parcial y completa | Temporal | Cubierta | Alta |
| PI-28 | Protección de rondas cerradas | No se reescriben | `HistoricoProtegidoTest`, `HistoricoRondaTest` | Ronda cerrada | Temporal | Cubierta | Alta |
| PI-29 | Plazo entre rondas | 15 días para la usuaria | `PlazoEntreRondasTest` | Fecha simulada | Temporal | Cubierta | Media |

### D.7 MRS y tablero

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-30 | Puntaje y dimensiones | Suma de 0 a 44; dimensiones correctas | `PuntajesTest`, `ConsistenciaTest` | Valores calculados a mano | Temporal | Cubierta | Alta |
| PI-31 | Sin severidad | No se muestran categorías | `SinSeveridadTest`, `SinSeveridadNiInterpretacionTest` | Valores extremos | Temporal | Cubierta | Media |
| PI-32 | Evolución | Solo rondas definitivas | `RondasTest`, `ExclusionesTest`, `AdaptableTest` | Varias rondas | Temporal | Cubierta | Alta |
| PI-33 | Separación entre cuentas | Nadie ve datos ajenos | `SeparacionTest`, `test_acceso_entre_usuarias` | Dos cuentas | Temporal | Cubierta | Alta |

### D.8 Visualización de B1

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-34 | Grupo con nombre y aviso | Nombre, descripción, advertencia y MRS aparte | `MiGrupoTest` | Tres respuestas válidas | Temporal | Cubierta | Alta |
| PI-35 | Regla y mapa | Igual a la definición de la 37C | `ReglaB1Test` | Las 20 celdas | Temporal | Parcial: el mapa se omite en Docker | Alta |
| PI-36 | Sin grupo | Ronda abierta, dato ausente o cierre sin foto | `test_grupo_ausente`, `test_no_infiere_de_datos_actuales` | Cada caso | Temporal | Cubierta | Alta |
| PI-37 | «No sabe» en pareja | «Grupo aún no disponible» | Solo función (`:79`) | Pareja `NS` | Temporal | Sin cubrir en tablero | Media |
| PI-38 | Última ronda incompleta | No se usa la anterior | Observado en Chrome el 2026-11-06 | Dos rondas | Temporal | Sin cubrir | Media |
| PI-39 | Independencia de orientaciones | Misma selección con y sin B1 | `test_seleccion_igual_con_y_sin_contexto` | Dos cuentas | Temporal | Cubierta | Alta |
| **PI-40** | **Recorrido completo por la interfaz** | **Con las tres respuestas, el grupo aparece** | Chrome 30/30 (anterior) | Cuenta nueva | Aislado | **Repetir** | **Máxima** |

### D.9 Orientaciones educativas y referencias

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-41 | Activación y protección | Apagada por defecto; borrador solo con `DEBUG` | `ActivacionTest` | Configuraciones | Temporal | Cubierta | Alta |
| PI-42 | Selección R-1 a R-7 | Solo por respuestas MRS | `ReglasTest` | Perfiles de síntomas | Temporal | Cubierta | Media |
| PI-43 | Catálogo y fuentes | C-1 a C-8; fuentes con fecha | `CatalogoTest` | Catálogo actual | Temporal | Cubierta | Media |
| PI-44 | Validación clínica | Aprobación profesional registrada | No automatizable | — | Ninguno | Externa | Alta |

### D.10 Vista profesional y estadísticas

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-45 | Búsqueda y ficha | RUT fuera de la URL; solo profesionales | `PanelProfesionalTest`, `BusquedaSinRutEnUrlTest` | Fichas ficticias | Temporal | Cubierta | Alta |
| PI-46 | Registro por profesional | Exige consentimiento vigente | `EncuestaPorProfesionalTest`, `ProfesionalYConsentimientoTest` | Con y sin él | Temporal | Cubierta | Alta |
| PI-47 | Estadísticas y k = 5 | Sin cifras con menos de 5; supresión | `test_estadisticas` | Grupos de 5 o más y de menos de 5 | Temporal / Aislado | Cubierta | Alta |
| PI-48 | MRS promedio por grupo | Solo con 5 o más; aviso descriptivo | `GruposTest` | Grupos grandes y pequeños | Temporal | Cubierta | Alta |
| PI-49 | Ronda de referencia distinta | Estadística usa la última verificable; participante, la última cerrada | Ninguno | Última ronda no verificable | Temporal | Sin cubrir | Media |

### D.11 Seguridad, privacidad y permisos

| Id | Funcionalidad | Comportamiento esperado | Conjunto existente | Datos sintéticos | Riesgo | Estado | Prioridad |
|---|---|---|---|---|---|---|---|
| PI-50 | Configuración | Falla sin secretos; producción estricta | `test_seguridad_config` | Valores de prueba | Temporal | Cubierta | Alta |
| PI-51 | Inactividad | Vence en servidor y navegador | `InactividadTest`; Chrome | Límite corto | Temporal / Aislado | Cubierta | Alta |
| PI-52 | Límite en flujos presenciales | Bloqueo a los 5 y 10 fallos | `LimiteIntentosTest` | Dos profesionales | Temporal | Cubierta | Media |
| PI-53 | Participación anterior | 409 sin escribir | `ParticipacionTest`; Node | Retiro y reingreso | Temporal / Nulo | Cubierta | Alta |
| PI-54 | Errores sin datos sensibles | Sin datos en respuestas de error | `ErroresSinDatosSensiblesTest` | Errores forzados | Temporal | Cubierta | Media |
| PI-55 | Botón «Atrás» tras salir | El tablero y la ficha no reaparecen | Ninguno | Dos cuentas | Aislado | Sin cubrir | Alta |
| PI-56 | Rotación de `SECRET_KEY` | Sesiones y borradores según lo previsto; comprobantes válidos | Ninguno | Comprobantes emitidos | Aislado | Sin cubrir | Alta |
| PI-57 | Integridad de las Fases 34–39 | Sin cambios | 40B-0 y 40B-1 | Ninguno | Lectura | **Bloqueada (C.3)** | Alta |

---

## E. Diagnóstico de B1 y discrepancias documentales

### E.1 Decisión vigente: estado en el código (V)

| Elemento a conservar | Estado | Dónde |
|---|---|---|
| Nombres de los cuatro grupos | Presente | `contexto_participante.py:45-58` |
| Advertencias exploratorias | Presente | `_mi_grupo.html:10,14` |
| B1 en el tablero | Presente | `tablero.py:38`, `mi_tablero.html:42` |
| Promedios MRS por grupo | Presente | `estadisticas.py:95,161-173`, `estadisticas.html:75-94` |
| Independencia de orientaciones | Presente | `orientaciones.py:94`, `contexto_participante.py:137-144` |

### E.2 Cerrada, verificable, definitiva y elegible para B1 (V)

Estos términos no significan lo mismo.

| Nivel | Significado | Regla |
|---|---|---|
| **Abierta** | Es la ronda actual | `historial.py:57` |
| **Cerrada** | Su número es menor que la ronda actual | `historial.py:57`, `resultado_mrs.py:140` |
| **MRS definitivo** | Cerrada, 11 ítems, sin ceros antiguos sin confirmar y registro no contradictorio | `resultado_mrs.py:147-155` |
| **Verificable** | Cerrada con MRS definitivo. **A nivel de ronda equivale a definitiva** | `historial.py:59-60` |
| **Con fecha verificable** | Cerrada por el cierre validado (tiene `id_cierre`) | `historial.py:48-52` |
| **Elegible para B1** | Es la **última** cerrada, verificable, con foto de «trabaja» y las tres respuestas válidas | `contexto_participante.py:66-73,102-118` |

**Punto de atención:** una ronda retrocargada puede mostrarse como «Finalizada y verificable» aunque no haya pasado por el cierre validado, no tenga fecha y no tenga B1. «Verificable» se refiere al resultado MRS, no a cómo se cerró.

### E.3 Diagnóstico de «Grupo aún no disponible»

**Cuenta sintética de prueba, confirmada como tal por la responsable. Consulta de solo lectura, sin ver respuestas, realizada antes de esta etapa.**

| Condición | Resultado |
|---|---|
| Última ronda cerrada verificable | Sí (ronda 1) |
| MRS definitivo | Sí |
| Foto de `trabaja_actualmente` | Existe y tiene valor |
| Días de ejercicio | Válido |
| Pareja | **Ausente** |
| **Condición fallida** | **`PAREJA_AUSENTE`** |

**Observación adicional:** de las 16 preguntas visibles del «Cuestionario complementario», las 12 primeras están vacías, incluida la de pareja. Las 4 últimas tienen valor. La responsable indica haber respondido la pregunta de pareja.

**Revisión del código (V):**

- La pregunta se muestra siempre y es opcional: no figura en `condicionales.py` y el campo admite vacío (`models.py:539`).
- El envío incluye las dos pantallas del MRS y el servidor las une (`encuesta.js:1282-1308`, `sync.py:99-123`).
- La prueba `tests.py:203-219` confirma que el servidor guarda el dato.
- `encuesta.js:1406` marca todo como enviado al recibir la confirmación, aunque se haya respondido algo mientras tanto. **No explica bien este caso:** perdería las respuestas posteriores, y aquí faltan las primeras.

**Conclusión:** la condición fallida está identificada, pero **su causa no**. Puede ser una pérdida real al guardar o un bloque que no quedó respondido. No se ha reproducido. **No se debe modificar el cálculo de B1.** Las pruebas PI-14, PI-15 y PI-40 están diseñadas para resolverlo.

**Otras causas por las que B1 no aparece (V):**

- ronda sin cerrar;
- última ronda no verificable;
- pareja «No sabe»;
- ronda cerrada antes de la Fase 40D-G (sin foto);
- última ronda incompleta, aunque una anterior esté completa.

**Texto mejorable (`_mi_grupo.html:18`):** dice que el grupo aparecerá al finalizar una ronda con las preguntas respondidas, lo que no siempre es cierto. Se propone aclararlo sin cambiar el cálculo.

### E.4 Documentos que afirman incorrectamente que B1 no es visible

**Propuesta; no se modificó nada.**

| Documento | Línea | Texto | Propuesta |
|---|---|---|---|
| `analisis/fase40/40D_orientaciones/40D-G_informe.md` | 10, 22 | «no se muestra»; «no aparece en la página de la participante» | Nota: la 40D-H lo hizo visible; sigue sin intervenir en orientaciones |
| `analisis/fase40/40D_orientaciones/40D-1_informe.md` | 96, 100 | «No para las participantes»; «solo en la vista profesional» | Nota con la decisión vigente; conservar la advertencia sobre datos reales |
| `analisis/fase40/40D_orientaciones/40D-1_reglas_personalizacion.md` | 104 | «no recomendado por ahora» | Nota: se aprobó su visualización, y sigue sin seleccionar orientaciones |
| `analisis/fase40/40A_auditoria/informe_fase40A.md` | 654, 984 | «No mostrar grupos a las usuarias» | Conservar como historia; agregar nota |
| `analisis/fase40/40A_auditoria/01_revision_correctiva_40A.md` | 281 | DT-7, decisión provisional | Marcar como reemplazada |
| `src/apps/encuestas/contexto_participante.py` | 7 | «nunca visible para la participante» | Corregir el comentario |
| `src/apps/encuestas/orientaciones.py` | 21 | «no se muestra» | Precisar: no se muestra dentro de las orientaciones |
| `src/apps/encuestas/tablero.py` | 4-5 | grupo «queda pendiente» | Actualizar |
| `src/apps/encuestas/test_contexto_participante.py` | 173 | Nombre de la prueba | Renombrar; indicar que se refiere a orientaciones |

**También falta un informe de la Fase 40D-H**, que documente la autorización y las pruebas. Hoy esa fase solo consta en comentarios del código (`tablero.py:38`, `contexto_participante.py:43`).

**No se propone tocar** `39R/…/20_nota_logica_tablero.md`, que dice «solo si la profesora lo decide». Pertenece a la 39R. La decisión vigente de mantener B1 visible para la revisión de la profesora guía debe constar en el informe 40D-H.

### E.5 Otras contradicciones documentales

| Documento | Afirma | Situación |
|---|---|---|
| `40_etapa2_consentimiento_seguridad.md` línea 5 y §4 | `usuarios/0004` no aplicada en desarrollo | La memoria de trabajo registra que se aplicó el 2026-11-07. **NV en esta etapa** |
| `40_etapa2…` §6.3 y §6.7 | No existe retiro sin cuenta ni límite de intentos | Implementados después (V) |
| `40_privacidad_informe.md` líneas 40 y 113 | Registro presencial sin cuenta permitido; consentimiento presencial sin registrar | Ahora exige consentimiento (V) |
| `40C-P_tablero_profesional_informe.md` §2 y §5 | Registros presenciales excluidos | La Etapa 2 los incluye si tienen consentimiento (D) |
| `40_pruebas_integrales_informe.md` | 354 pruebas; tablero «40E» pendiente | Superado: 387 pruebas; el tablero es la 40C-P |
| `40S-1_informe.md` §8 | R-2 (RUT en URL) abierto | Corregido (V) |
| `40B-3_informe.md` §10.1 y `40C_informe.md` | Riesgos P1–P7 abiertos | Resueltos según `40_privacidad_informe.md` (D) |

---

## F. Revisión de seguridad y privacidad

Revisión documental y de código. No se abrió ningún `.env`, no se imprimieron credenciales y no se hicieron pruebas intrusivas.

### F.1 Estado por tema

| Tema | Estado | Evidencia |
|---|---|---|
| Control de acceso por rol | Correcto. Decoradores en todas las vistas revisadas | V: `profesional.py`, `administracion.py`, `retiro.py`, `presencial.py` |
| API | Correcto. Exige sesión; sin `csrf_exempt` | V: `api.py`; búsqueda sin coincidencias |
| Datos personales | RUT solo como hash; búsqueda por POST | V |
| Escritura | Validada en servidor; rondas cerradas protegidas | V |
| Sesiones | 30 minutos de inactividad; cookies `HttpOnly` y `SameSite=Lax`; `Secure` en producción | V: `settings.py:235-242,272-273` |
| Sincronización | Comprueba participación y ronda; 409 sin escribir | V: `sync.py:319-377,442-458` |
| Errores | JSON genéricos; registros solo con número de ficha | V: `senales.py:79,97` |
| Tablero | Solo datos propios | V: `tablero.py:30` |
| Variables de entorno | Secretos obligatorios; producción validada | V: `settings.py:42,66,132,170,257` |
| Administración de Django | Solo el modelo de cuentas; RUT y clave de solo lectura | V: `usuarios/admin.py:10-16` |

### F.2 Hallazgos sin antecedente en los informes de la Fase 40

| Id | Hallazgo | Severidad | Propuesta |
|---|---|---|---|
| S-N1 | **El ingreso por RUT y contraseña no tiene límite de intentos.** `intentos.py` solo cubre flujos presenciales; no se encontró control en `LoginRutForm`, en el backend ni en la ruta | Alta antes de usar datos reales | Aplicar un límite similar |
| S-N2 | **El tablero y la ficha profesional no llevan `no-store`** (`tablero.py:33`, `profesional.py:105`). Estadísticas y retiro sí. En un equipo compartido podrían quedar en la caché del navegador | Media | Añadir la cabecera y probar con PI-55 |
| S-N3 | **Los datos de salud se guardan sin cifrado de campo.** `django-fernet-encrypted-fields` está en `requirements.txt`, pero no se usa en los modelos | Media; depende del despliegue | Cifrado de disco y respaldos, o decisión expresa |
| S-N4 | **La contraseña temporal de profesionales se envía por correo** y solo se *recomienda* cambiarla (`views.py:18-33`) | Media | Enlace de creación o cambio obligatorio |

**Decisión institucional:** toda profesional puede ver cualquier ficha, porque no hay asignación por paciente (`profesional.py:103`). Debe confirmarse si es aceptable.

### F.3 Riesgos conocidos que siguen abiertos

| Riesgo | Situación | Evidencia |
|---|---|---|
| R-1 Secretos antiguos en el historial de GitHub | Abierto. Crítico antes de datos reales | D |
| Rotación de `SECRET_KEY`: falta `SECRET_KEY_FALLBACKS` en `settings.py`, necesario para no invalidar los comprobantes de retiro | Abierto; previsto en `40_etapa2…:57` | V / D |
| R-3 `mi_tablero` y `mi_evaluacion` sin revisar consentimiento | Abierto, baja. `tablero.py:25-26,46-47` | V |
| R-5 HTTPS y HSTS apagados por defecto | Abierto hasta el despliegue | V |
| R-6 El contenedor `db` recibe también secretos de la aplicación | Abierto, baja. `docker-compose.yml:8-9` | V |
| R-7 `docker compose config` imprime secretos | Vigente: no usarlo | D |
| R-8 PostgreSQL publicado en todas las interfaces | Abierto. `docker-compose.yml:14` | V |
| R-9 Sin registro de errores (`LOGGING`) | Abierto | V |
| R-11 `console.warn` muestra errores de validación | Abierto, baja. `encuesta.js:1431` | V |
| Límite de intentos con caché por proceso | Requiere caché compartida al desplegar | D |
| Respuestas apartadas en equipos compartidos | Cifradas, pero permanecen en el dispositivo | D |

---

## G. Riesgos y prioridades

| # | Riesgo | Impacto | Prioridad | Acción |
|---|---|---|---|---|
| 1 | Posible pérdida de respuestas del cuestionario complementario | Datos incompletos; B1 no disponible | **Máxima** | PI-14, PI-15, PI-40 |
| 2 | Fase 40, 38R y 39R solo en este equipo | Pérdida del trabajo | **Máxima** | Autorizar respaldo y commits por separado |
| 3 | Pruebas de integridad abren un archivo protegido | Vulnerar una restricción | **Máxima** | Decidir antes de 5B |
| 4 | DR-1: la base de desarrollo puede contener datos reales | Exposición | Alta | No usarla para pruebas; confirmar su contenido |
| 5 | Chrome sin repetir después de los últimos cambios | Fallos no detectados | Alta | Reescribir scripts y ejecutar en aislado |
| 6 | Ingreso sin límite de intentos | Ataque de fuerza bruta | Alta antes de datos reales | Corregir tras autorizar |
| 7 | Secretos sin rotar y sin `SECRET_KEY_FALLBACKS` | Compromiso de sesiones | Alta antes de datos reales | Etapa propia |
| 8 | Catálogo sin validación clínica | Orientaciones no validadas | Alta antes de datos reales | Revisión externa |
| 9 | Migraciones sin commit y choque con `valeAW` (DR-8) | Fallos al integrar | Media | Resolver al preparar el commit |
| 10 | Documentos contradictorios | Confusión en la revisión | Media | Actualizar según E.4 y E.5 |
| 11 | B1 proviene de datos sintéticos | Interpretación excesiva | Media | Mantener advertencias; reanálisis con datos reales |
| 12 | `core.autocrlf=true` sin `.gitattributes` | Huellas alteradas en un clon | Media | Plan del documento 03 de la Etapa 4B |

---

## H. Plan propuesto para la Etapa 5B

**Ninguna de estas etapas se ha ejecutado.**

| Paso | Qué se hace | Efecto en los datos | ¿Requiere autorización? |
|---|---|---|---|
| **5B-0** | `manage.py check` y `makemigrations --check` | Ninguno | Autorización general de 5B |
| **5B-1** | JavaScript: `node --test` sobre `pruebas_js` | Ninguno | Autorización general de 5B |
| **5B-2** | Suite Django completa en base temporal | Base temporal que se destruye | Autorización general de 5B |
| **5B-3** | Chrome en entorno aislado: PI-14, PI-15, PI-40, PI-08 y PI-55, más el recorrido integral | Contenedores desechables; cuentas `@ficticio.cl` | **Sí, específica:** crea contenedores y reescribe scripts en el scratchpad |
| **5B-4** | Según resultado de 5B-3, diagnóstico y propuesta de corrección de la pérdida de respuestas | Ninguno | Corrección con **autorización aparte** |
| **5B-5** | Integridad histórica 40B-0 y 40B-1 | Solo lectura, pero abre un archivo protegido | **Sí, expresa:** ejecutar con exclusión o autorizar la lectura |
| **5B-6** | Comandos de solo lectura en desarrollo | Lee una base con posibles datos reales | **Sí, expresa,** tras aclarar DR-1 |

**Requieren autorización separada y quedan fuera de 5B salvo que se indique:**

- correcciones de código, incluidos los hallazgos S-N1 a S-N4;
- nuevas pruebas (PI-04, PI-16, PI-37, PI-38, PI-49, PI-56);
- actualización de documentos (E.4 y E.5) y creación del informe 40D-H;
- rotación de `SECRET_KEY`;
- migraciones en desarrollo;
- commits, pushes y respaldo de 38R y 39R;
- pruebas manuales en `localhost:8000`.

**Decisiones que se necesitan antes de 5B:**

| Id | Decisión | Recomendación |
|---|---|---|
| D-1 | ¿Se autoriza 5B-0 a 5B-2? | Sí |
| D-2 | ¿Se autoriza el entorno aislado de Chrome? | Sí; es el único modo seguro de resolver E.3 |
| D-3 | ¿Cómo tratar las pruebas 40B-0 y 40B-1? | Crear una versión que excluya ese archivo, o saltarlas y controlar por metadatos |
| D-4 | ¿Contiene datos reales la base de desarrollo (DR-1)? | Confirmarlo; mientras tanto, tratarla como sensible |
| D-5 | ¿Se respalda antes de intervenir? | Sí, antes de cualquier corrección |

---

## I. Control de integridad

| Control | Inicio | Antes de escribir este informe | Resultado |
|---|---|---|---|
| Rama | `datos-simulados` | `datos-simulados` | Igual |
| HEAD | `573d3a31…f9a` | `573d3a31…f9a` | Igual |
| Stash | 0 | 0 | Igual |
| Índice | Vacío | Vacío | Igual |
| `git status --porcelain` | 92 líneas | 92 líneas | Sin diferencias |
| Metadatos (tamaño y fecha) | 7.022 archivos | 7.022 archivos | 0 nuevos, 0 retirados, 0 cambiados |

**Después de escribir este informe (comprobado):** `git status --porcelain` tiene 93 líneas y su única diferencia con el inicio es `?? analisis/fase40/40_validacion_final/`. HEAD sigue igual, el índice está vacío y hay 0 stash. La carpeta contiene solo este archivo.

**Restricciones cumplidas:**

- No se ejecutaron pruebas ni análisis, y no se modificó código.
- No se consultaron registros durante esta etapa. Los resultados de E.3 provienen de la consulta autorizada anterior.
- No se abrieron los cuatro archivos protegidos ni archivos `.env`. El control por metadatos los excluye.
- No hubo commits, pushes, resets ni limpiezas de Git.
- No se modificaron las Fases 34–39R, sus protocolos sellados ni las tesis.

**No verificado:**

| Aspecto | Motivo |
|---|---|
| Que las pruebas sigan pasando hoy | No se ejecutaron |
| Estado de las migraciones en la base de desarrollo | Requiere consultarla |
| Contenido real de la base (DR-1) | Fuera de alcance |
| Identidad byte a byte de los archivos | Control solo por metadatos |
| Estado de los cuatro archivos protegidos | Excluidos por instrucción |
| Causa de la ausencia de respuestas en la cuenta sintética | No reproducida |
