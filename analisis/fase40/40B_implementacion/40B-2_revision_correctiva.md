# Fase 40B-2 — Revisión correctiva

Fecha: 2026-11-06. Estado: **sin commit ni push** (toda la Fase 40 sigue local). No se iniciaron la 40B-3 ni la 40C.

Este documento tiene dos partes:

- **Parte A:** el ajuste del EMPA complementario (§1–6).
- **Parte B:** el cierre de la revisión correctiva (§7–13):
  - discrepancias históricas;
  - privacidad offline;
  - pruebas en navegador;
  - confirmación del estado de la 40B-2;
  - conclusión.

---

# Parte A — EMPA complementario

## 1. Decisión

Las mediciones del EMPA son **complementarias**. No son obligatorias para finalizar una ronda, **tampoco cuando las registra una profesional**.

| Regla | Antes (informe 40B-2, §4.3 regla 3) | Ahora |
|---|---|---|
| EMPA al cerrar una profesional | Exigía talla, peso, presión sistólica y diastólica | No bloquea el cierre: puede ir completo, parcial, vacío o ausente |
| EMPA al cerrar una usuaria | No obligatorio | Sin cambio |
| 11 preguntas del MRS | Obligatorias | **Sin cambio**: siguen obligatorias para ambos roles |
| Otras preguntas obligatorias aplicables y sus condiciones | Se exigen | **Sin cambio** |
| Mediciones no registradas | Nulas | **Sin cambio**: siguen nulas (dato no registrado). No se imputan ceros ni otros valores |

Esta revisión reemplaza tres puntos del informe `40B-2_informe.md`: la regla 3 de §4.3, la fila 13 de §7 y la fila «Rol con que se evalúa el cierre» de los riesgos. Los tres quedaron anotados allí con un enlace a este documento.

## 2. Cambio realizado

El EMPA era obligatorio para la profesional por una sola razón: el diccionario `REQUERIDOS_PROFESIONAL` de `src/apps/encuestas/campos_por_rol.py`. Ese diccionario alimenta, en cadena:

1. la marca `required` de `SegmentoEMPAForm`;
2. el campo `obligatoria` del esquema `/api/esquema/`;
3. `seccionCompleta()` en el cliente;
4. la completitud del servidor en modo obligatorio, que usa el esquema del rol de quien cierra.

**Único cambio de la plataforma:** `REQUERIDOS_PROFESIONAL` quedó vacío (`{}`), con un comentario que registra la decisión. La regla deja de aplicarse a la vez en el servidor y en el cliente.

**Lo que no se cambió:**

- `SOLO_PROFESIONAL` y `OPCIONALES_USUARIA`.
- Los modelos: los campos del EMPA ya eran `null=True, blank=True`. No hay migración.
- `sync.py`, `cierre.py`, `completitud.py`, `encuesta.js` y `sw.js`.

## 3. Datos existentes

- No se borró ni modificó ninguna respuesta, y no se escribió nada en la base de desarrollo.
- Hay 7 registros EMPA en desarrollo, todos autorreportados (`origen_registro = AUTO`). En los 4 campos que eran obligatorios para la profesional no hay ceros; los valores ausentes ya eran nulos.
- La limpieza congelada (40B-0) solo lee `SOLO_PROFESIONAL` de `campos_por_rol.py`, y ese diccionario no cambió.

## 4. Pruebas del ajuste

**En `src/apps/rondas/test_40b2.py` (prueba 13):**

| Prueba | Verifica |
|---|---|
| `test_13_la_profesional_cierra_con_empa_completo` | Cierra; los 4 valores se guardan tal cual |
| `test_13_la_profesional_cierra_con_empa_parcial` | Cierra; talla, diastólica y glicemia quedan nulas |
| `test_13_la_profesional_cierra_sin_empa` | Cierra; no se crea ningún registro EMPA |
| `test_13_la_profesional_cierra_con_empa_vacio` | Cierra; los campos del EMPA quedan nulos |
| `test_13_el_empa_completo_no_reemplaza_al_mrs_obligatorio` | Con el EMPA completo y el MRS sin `pregunta_11`: **rechazo**, el único faltante es `mrs: [pregunta_11]` y la ronda sigue abierta |
| `test_13_el_esquema_profesional_no_marca_obligatorio_el_empa` | El EMPA no tiene preguntas obligatorias, sus campos siguen visibles y las 11 del MRS siguen obligatorias |

**Otras pruebas actualizadas:**

- `encuestas/tests.py`: `test_profesional_empa_no_obligatorio` y `test_profesional_puede_enviar_empa_vacio`.
- `pruebas_comunes.protocolo2()`: ya no completa el EMPA.
- `pruebas_js/esquema_*.json`: regenerados.
- `test_40b0_definiciones.py`: excluye `campos_por_rol.py` de la comparación byte a byte. `SOLO_PROFESIONAL` sigue cubierto por la comparación con lo congelado.

## 5. Impacto

- **Esquema antiguo sin conexión.** Un dispositivo que siga sin conexión con el esquema anterior seguirá marcando el EMPA como incompleto en pantalla hasta que vuelva la red. El servidor ya no lo exige y no se pierde nada. En el paso 8 (§10) se comprobó que el esquema se reemplaza al volver la red.
- **Lectura de los datos.** Un EMPA ausente o con campos nulos significa «no registrado».
  - Cuando la profesional omite el EMPA se crea **un registro EMPA con todos sus campos nulos** (observado en el paso 6, §10).
  - Que exista un registro EMPA no significa que hubo mediciones.

## 6. Archivos tocados en esta revisión

**Parte A:**

- `src/apps/encuestas/campos_por_rol.py`
- `src/apps/encuestas/tests.py`
- `src/apps/rondas/test_40b2.py`
- `src/apps/rondas/pruebas_comunes.py`
- `src/apps/encuestas/pruebas_js/esquema_*.json`
- `analisis/fase40/40B_implementacion/pruebas/test_40b0_definiciones.py`
- `40B-2_informe.md`: solo notas que remiten a este documento.

**Parte B:** solo el **texto** de justificación de las 3 excepciones en `pruebas/test_40b1_proteccion_historica.py` (§7.4). Sus huellas no se cambiaron.

---

# Parte B — Cierre de la revisión correctiva

## 7. Discrepancias históricas (solo lectura)

### 7.1 Qué difiere y desde cuándo

Todas las huellas son SHA-256 del archivo en el disco (CRLF). «Git» indica con qué commit coincide el contenido, ignorando el fin de línea.

| Archivo | Huella actual | Manifiesto que la registra | Commit con el mismo contenido |
|---|---|---|---|
| `analisis/eda/univariado.py` | `026087e0…` | `cierre_fases_34_35/integridad/manifiesto_despues.csv` | `44bfe0b` (sin cambios desde entonces) |
| `analisis/eda_usuaria.py` | `9c58cc64…` | el mismo | `44bfe0b` (sin cambios desde entonces) |
| `analisis/limpieza/catalogo.py` | `c9889590…` | ninguno: todos registran `680ea9e3…` | `573d3a3` (Fase 40B-0) |

**Historia de los dos archivos EDA** (fechas de modificación y manifiestos):

| Momento | `univariado.py` | `eda_usuaria.py` |
|---|---|---|
| Commit `745d689` (02-11), igual a `manifiesto_antes`/`correccion_antes` de la revisión correctiva 34 | `0a1280a1` | `d07d3d4e` |
| Revisión correctiva 34 (04-11 ~23:11, `manifiesto_correccion_despues`, cambio H10) | `f83d518d` | `ecbddf92` |
| Cierre de las Fases 34-35 (04-11 23:41–23:43, `manifiesto_despues` del cierre, cambios H11 y H13) | **`026087e0`** | **`9c58cc64`** |
| Commit `44bfe0b` (06-11 00:51) y estado actual | `026087e0` | `9c58cc64` |

`catalogo.py` cambió el 06-11 a las 01:54. Es el cambio de la Fase 40B-0, que pasó a leer las definiciones congeladas, y quedó en el commit `573d3a3`.

**Las tres diferencias son anteriores a la 40B-2.** Ninguna se introdujo en la 40B-2 ni en esta revisión: la diferencia con git es 0 líneas y la fecha de modificación es anterior.

### 7.2 ¿Son legítimas?

**Sí, las tres, con evidencia concreta:**

- **`univariado.py` y `eda_usuaria.py`:**
  - `cierre_fases_34_35/scripts/verificar_integridad_cierre.py:24` declara `NUEVOS_AUTORIZADOS = {'analisis/eda/univariado.py', 'analisis/eda_usuaria.py'}`, el control 9: «Los cambios de código del cierre se limitan a H11 y H13».
  - El manifiesto posterior de ese mismo cierre registra exactamente la huella actual.
  - El cambio solo agrega:
    - el recuento de imputados por población de la figura (H11);
    - el rótulo de salida «descriptiva» de la etapa menopáusica (H13: `ROLES_DESCRIPTIVOS` y `TITULOS_INFORME`).
  - El cambio no modifica la familia FDR ni el orden de las pruebas.
  - La revisión correctiva 34 registra una versión **intermedia** (`f83d518d`/`ecbddf92`) que el cierre de las Fases 34-35 reemplazó de forma autorizada.
- **`catalogo.py`:** es el cambio declarado de la 40B-0.
  - `test_40b0_definiciones.py` (15/15) comprueba que la limpieza regenerada da salidas idénticas a las históricas.
  - También comprueba que las definiciones congeladas coinciden con los commits de las Fases 34 y 35.

### 7.3 ¿Afectan los análisis de las Fases 34–39?

**No.**

- Los 6.457 artefactos de los 10 manifiestos finales conservan su huella: tablas, figuras, informes y matrices de las Fases 34 a 39. Los únicos distintos son estos 3 scripts.
- `test_h11_h13` (21/21) rehace en memoria H11 y H13 y los compara con los CSV históricos.
- `test_revision_35b` (43/43) y `test_entropia` (79/79) pasan.
- No se recalculó nada.

### 7.4 Por qué la 40B-1 informó «3/3»

La prueba no está en git, así que lo comprobé en el registro de la sesión de la 40B-1 (06-11, 06:17–06:25):

1. **06:18:32** — primera y única ejecución **completa** de `test_40b1_proteccion_historica.py`: `Ran 3 tests … FAILED (failures=4)`.
   - En ese momento la prueba exigía la huella exacta del manifiesto y no tenía excepciones.
   - `catalogo.py` (01:54) y los dos EDA (04-11) ya diferían. Por lo tanto, la comprobación de manifiestos tenía que fallar.
   - La salida se recortó con `tail`, así que no quedó la lista de fallos. Sí quedó la línea final «FAILED (failures=4)».
2. **06:20:45** — tras corregir otra prueba, se volvió a ejecutar **solo** la clase `EntradasDeDjango` (2 pruebas): `OK`.
3. **06:25:52** — el informe 40B-1 declaró «3/3 (6.457 artefactos)».

**Conclusión:** el «3/3» de la 40B-1 **no está respaldado por ninguna ejecución**. La prueba de manifiestos nunca pasó en la 40B-1, y la cifra de 6.457 venía de la ejecución que falló. Es un error del informe 40B-1, no un problema de los datos. Desde la 40B-2 la prueba exige la huella **actual** de esas 3 excepciones, así que cualquier cambio posterior vuelve a fallar.

En esta revisión solo cambié el texto de justificación de las excepciones, que antes decía «origen sin documentar». Las huellas no se tocaron.

**Pendiente:** ninguno. Se recomienda corregir la fila 14 de §7 del informe 40B-1, a decisión de ustedes; no la modifiqué.

## 8. Privacidad de las respuestas offline

Revisé el código (`encuesta.js`, `sw.js`, `retirado.html`, `retiro.py`, `sync.py` y `decorators.py`) y probé cada caso en el navegador o en el servidor aislado (§10).

| # | Caso | Comportamiento comprobado | Riesgo |
|---|---|---|---|
| P0 | Borrador y desconexión | Queda en IndexedDB y se envía al volver la red (paso 7) | Ninguno |
| P1 | **«Salir» en un dispositivo** | Después de cerrar sesión, IndexedDB conserva en claro las respuestas de la cuenta: fecha de nacimiento, comuna, salud, etc. Además, el Service Worker conserva la última copia de `/encuesta/`. **Sin sesión y sin red, abrir `/encuesta/` muestra la encuesta de la persona anterior** («8 de 9 secciones completas»), editable | **Alto en un equipo compartido**: exposición sin contraseña |
| P2 | Cambio de cuenta en el mismo dispositivo | La cuenta nueva **no** ve los datos anteriores. Lo pendiente de la anterior se aparta en `respaldo_de|<hash>` y se le devuelve cuando vuelve a entrar | Medio: lo apartado queda legible en IndexedDB y no vence |
| P3 | Computador compartido de una profesional | Tras «Salir» quedan 18 claves `prof:<hash>:nueva:<hash>\|…`, con el borrador de cada paciente (fecha de nacimiento y respuestas). El RUT **no** queda en claro | **Alto**: datos de salud de varias pacientes en un equipo común |
| P4 | Conflictos apartados (`conflictos`, `respaldo_de`) | No se borran nunca solos; solo los borra el retiro en ese mismo dispositivo | Medio: se acumulan |
| P5 | Retiro en el dispositivo 1 | La página de retiro borra la base `encuesta_agingwomen` de ese navegador. **Con otra pestaña abierta, el borrado queda bloqueado hasta cerrarla, y aun así la página dice «Este dispositivo tampoco guarda ya tus respuestas»** | Bajo: mensaje prematuro |
| P6 | **Sincronizar después del retiro desde otro dispositivo** | El dispositivo 2 recibe 403 y lo guarda todo como pendiente. **Si ella vuelve a aceptar el consentimiento, el dispositivo 2 reenvía lo pendiente y el servidor vuelve a crear su ficha, el MRS y el EMPA**, contra la decisión de que la reincorporación parte con un historial nuevo | **Alto**: reaparecen datos eliminados |
| P7 | Retiro y equipo de una profesional | Un borrador con `paciente_id` borrado se rechaza («La paciente indicada no existe»), pero queda pendiente en ese equipo. Un borrador de «paciente nueva» con el RUT de una mujer retirada **se acepta sin revisar el consentimiento**: crea una ficha sin dueña, que se le asocia a ella si vuelve | **Alto**: reaparición o creación sin consentimiento |

**¿Hay un riesgo de privacidad inmediato?** Sí, para P1, P3, P6 y P7, **si la plataforma se usa con participantes reales antes de corregirlos**. Mientras se use solo en desarrollo con cuentas ficticias no hay exposición. No implementé nada, porque P6 y P7 dependen del flujo de retiro y consentimiento, que está pendiente.

**Correcciones mínimas propuestas** (sin implementar; requieren su autorización):

1. **P1 y P3, al pulsar «Salir»:**
   - Si no hay nada pendiente, borrar las claves de esa cuenta en IndexedDB y la copia de `/encuesta/` del Service Worker.
   - Si hay algo pendiente, **no borrar en silencio**: avisar que hay respuestas sin enviar y ofrecer esperar a la conexión o descartarlas de forma explícita.
   - Además, el Service Worker no debería servir la copia de `/encuesta/` después de un cierre de sesión. Por ejemplo, el cierre de sesión borra esa entrada de la caché.
   - *Decisión que les corresponde:* qué hacer con lo pendiente en un equipo compartido, porque choca con la regla de la 40B-2 de no borrar nunca IndexedDB con datos pendientes.
2. **P6 y P7, en el servidor:** guardar como constancia mínima los identificadores aleatorios (`uuid_local`) de lo borrado en el retiro, sin datos de salud, y rechazar con 409/410 cualquier envío que los reutilice.
   - El cliente debe apartar ese envío y no reenviarlo.
   - Para la profesional: revisar el retiro antes de crear una ficha por RUT, coherente con el futuro consentimiento presencial (DC de la 40S-1).
   - Esto encaja en la adenda de retiro de `40S-1_propuesta_consentimiento.md` («solo constancias mínimas sin datos de salud»).
3. **P5:** que `retirado.html` diga «se borrará cuando cierres las otras pestañas» cuando el borrado quede bloqueado, y que `encuesta.js` cierre su conexión ante `versionchange`.
4. **P2 y P4:** plazo de vencimiento o aviso visible para lo apartado.

## 9. Herramienta de prueba en navegador

No había Playwright ni Selenium. Usé **Chrome 157.0.8103.38 instalado, sin interfaz**, controlado por el protocolo de DevTools con un script propio de Node, sin instalar nada.

- **Perfiles:** cada «dispositivo» tuvo un perfil temporal propio.
- **Entorno aislado:**
  - contenedores `aw_nav_db` (PostgreSQL 15 **nuevo y vacío**) y `aw_nav_web` (misma imagen y mismo código);
  - una red propia y el puerto `127.0.0.1:8010`;
  - secretos aleatorios distintos de los de desarrollo y correo solo a consola.
- **Cuentas:** solo cuentas ficticias (RUT 11.111.111-1, 22.222.222-2, …, contraseña de prueba) y pacientes ficticias.
- **Lo que no se usó:** ni la base de desarrollo ni sus respaldos.
- **Desconexión:** se simuló de dos formas: la página sin red (`Network.emulateNetworkConditions`) y el servidor detenido (`docker stop`).
- **Al terminar** se eliminaron los contenedores, la red, el volumen y los perfiles. Los guiones y los resultados (JSON) quedan en el scratchpad de la sesión, fuera del repositorio.

## 10. Resultados en navegador (ejecutados)

| Paso | Resultado | Evidencia |
|---|---|---|
| 1. Guardar respuestas parciales | **OK** | El servidor guarda `pregunta_1 = 0` y `pregunta_3 = 0` elegidos, deja `pregunta_6–11 = null`, puntaje `null` y la ronda ABIERTA |
| 2. Salir y volver | **OK** | Tras salir e ingresar, la pantalla del MRS muestra marcados los 5 ítems guardados |
| 3. Finalizar con el MRS incompleto | **OK** | Aviso «Faltan secciones por completar: Escala de Evaluación de la Menopausia (MRS)» y la ronda sigue ABIERTA. El cliente lo impide antes de enviar; el rechazo en el servidor está cubierto por `test_40b2` |
| 4. Completar las 11 del MRS | **OK** | 11 ítems en el servidor, 5 de ellos con 0 elegido; puntaje 10; ronda aún abierta |
| 5. Finalizar | **OK** | «¡Encuesta enviada!…»; ronda 1 CERRADA por USUARIA y ronda 2 abierta |
| 6. Profesional sin EMPA | **OK** | Paciente nueva ficticia, EMPA sin tocar (0 campos): «¡Encuesta de la paciente enviada!», ronda 1 CERRADA por PROFESIONAL y EMPA con todos sus campos nulos |
| 7. Interrupción y recuperación | **OK** | Sin red y con el servidor detenido se respondió «Trabajo» (5 campos): queda `sucio=true` en el dispositivo y la recarga sin red muestra la encuesta. Al volver la red: «Respuestas sincronizadas.», los 5 valores en el servidor y `sucio=false` |
| 8. Service Worker y reglas del EMPA | **OK** | SW activo y caché `aging-women-v12`. El EMPA tiene 0 obligatorias en la red, en la caché y en IndexedDB. Un esquema antiguo **simulado** en la caché (con los 4 obligatorios) quedó reemplazado por el actual con 0 obligatorias al volver la red |

**Observaciones de las pruebas:**

- **Primera visita.** En un dispositivo nuevo, si la red se corta segundos después de la primera visita, antes de que el Service Worker termine de instalarse, la recarga sin red no carga la página (`ERR_INTERNET_DISCONNECTED`). Ocurrió una vez en la prueba. Con unos segundos de conexión (≈2,5 s) el SW ya guarda la copia desde la primera visita. Es una limitación conocida del modo offline, no una regresión.
- **P2 en la primera corrida.** Dio un resultado no concluyente: el guion no logró cambiar de sesión. Se repitió aislado, con cuentas ficticias nuevas y registro paso a paso, y el comportamiento fue el de §8.
- **Pruebas de servidor de P6 y P7.** Se ejecutaron en la base aislada con `sincronizar_payload`.

## 11. Estado de la 40B-2 (punto 4 del encargo)

| Requisito | Estado | Evidencia |
|---|---|---|
| Respuesta ausente ≠ cero elegido | **Cumple** | Navegador, pasos 1 y 4 (`0` elegido frente a `null`); `test_40b2` 01–05; Node 11/11 |
| Los 8 ceros históricos de rondas cerradas no se muestran como resultado definitivo verificable | **Cumple en los datos; no cumple en la pantalla (le corresponde a la 40B-3)** | Ver el detalle abajo |
| El EMPA no impide finalizar una encuesta profesional | **Cumple** | Navegador, paso 6; `test_40b2` 13 (6 pruebas) |
| La sincronización conserva los borradores ante errores | **Cumple** | Navegador, paso 7 (sin red o servidor caído) y P6 (403: «Tus respuestas siguen guardadas en este dispositivo»); Node 11/11; `test_40b2` |
| No se modificó ningún resultado de las Fases 34–39 | **Cumple** | `test_40b1` 5/5 (6.457 artefactos); ningún archivo de `analisis/` ni de `datos/` fuera de `fase40/` modificado desde el 06-11 10:00; `test_h11_h13`, `test_revision_35b` y `test_entropia` OK |

**Detalle de los ceros históricos:**

- **En los datos se cumple.** Consulta de solo lectura en desarrollo, 0 escrituras: los MRS 3 y 4 son de rondas cerradas y tienen 2 y 6 ceros sin confirmar (8 en total). Los dos están marcados y `ronda_es_historica_no_verificable()` es `True`.
- **En la pantalla no se cumple.** Al renderizar la ficha de la participante 11 se muestra «Puntaje MRS: 16» **sin advertencia**, y `puntaje_mrs_definitivo()` también devuelve 16. Ninguna vista ni plantilla usa todavía la marca de no verificable.
- **Por qué le corresponde a la 40B-3.** El plan 40A (`01_revision_correctiva_40A.md:226,242`) asigna a la 40B-3: «Tablero y ficha: dejar de mostrar puntajes de rondas abiertas o no verificables (H-03)… una ronda no verificable muestra «no comparable»».
  - La 40B-3 debe combinar las dos funciones: `puntaje_mrs_definitivo()` aún no considera los ceros no verificables.
  - Hasta la 40B-3 se sigue mostrando además la categoría de severidad (p. ej. «Moderada»), que el plan elimina en esa fase.

## 12. Pruebas realmente ejecutadas en esta revisión (2026-11-06)

| Conjunto | Resultado |
|---|---|
| Django completo (PostgreSQL de desarrollo, base de pruebas) | **271/271 OK** (también 271/271 con `--reverse` en la Parte A) |
| Cliente con Node (`test_encuesta_sync.mjs`) | 11/11 OK |
| `test_40b0_definiciones.py` | 15/15 OK |
| `test_40b1_proteccion_historica.py` | 5/5 OK (6.457 artefactos; 3 excepciones, ya justificadas) |
| `test_entropia` / `test_revision_35b` / `test_h11_h13` | 79/79, 43/43 y 21/21 OK |
| Navegador real, entorno aislado | Pasos 1–8 OK; casos de privacidad P1–P7 comprobados (§8) |
| Solo lectura en desarrollo | Ceros históricos y renderizado de la ficha (0 escrituras); 7 registros EMPA |

## 13. Conclusión

**Sí puede iniciarse la 40B-3.** Lo que queda pendiente de la 40B-2 es justamente su contenido: no mostrar como definitivos los puntajes de rondas abiertas o no verificables. Las discrepancias históricas quedaron explicadas y no hay ningún bloqueo técnico de la 40B-2.

**Impedimento concreto, pero no para la 40B-3:** antes de usar la plataforma con **participantes reales** hay que resolver P1, P3, P6 y P7 (§8). La exposición en equipos compartidos y la reaparición de datos tras el retiro son riesgos de privacidad, y su corrección necesita dos decisiones de ustedes:

1. qué hacer con las respuestas pendientes al cerrar sesión en un equipo compartido;
2. autorizar la constancia mínima de identificadores borrados como parte de la implementación del retiro.

Se recomienda programarlo junto con la implementación del consentimiento y el retiro, o como una fase propia antes de cualquier despliegue.
