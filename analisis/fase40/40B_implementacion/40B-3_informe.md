# Fase 40B-3 — Visualización segura de resultados MRS

Fecha: 2026-11-06. Rama `datos-simulados`, **sin commit ni push** (toda la Fase 40 sigue local). No se inició la 40C.

## 1. Resumen

- **Una sola regla.** Ninguna pantalla presenta como definitivo un MRS que no esté completo, cerrado y verificado. La regla vive en un único lugar, `apps/rondas/resultado_mrs.py`, y el tablero, la ficha y `puntaje_mrs_definitivo()` la usan.
- **Ceros históricos.** Los 2 MRS de rondas cerradas con los 8 ceros históricos sin confirmar muestran ahora **«Resultado histórico no verificable»**, sin número. Antes la ficha 11 mostraba «Puntaje MRS: 16».
- **Rondas abiertas.** Muestran una suma **parcial** o **provisional**, siempre con la indicación de que la ronda no está cerrada. Lo mismo en la encuesta en curso.
- **Severidad.** No se muestran categorías del puntaje total. Los cortes históricos (`MRS.SEVERIDAD_TOTAL`) siguen intactos en el modelo y en las definiciones congeladas del análisis; solo dejaron de publicarse.
- **Corrección documental de la 40B-1.** Se corrigió su «3/3» (`40B-1_informe.md`, fila 14 de §7 y §13 nueva).
- **Pruebas:**
  - Django **286/286**, también en orden inverso;
  - cliente con Node **12/12**;
  - protección 40B-0 **15/15** y 40B-1 **5/5**;
  - pruebas históricas 79/79, 43/43 y 21/21;
  - prueba en **navegador real** con datos sintéticos: OK.
- Ningún dato se modificó ni se reconstruyó. No hay migraciones.

## 2. Diagnóstico: dónde se presentaba el MRS

| Lugar | Antes | Problema |
|---|---|---|
| `templates/encuestas/mi_tablero.html` | `Puntaje MRS: {{ s.registro.puntaje_total }}` y «(provisional…)» solo en la ronda actual | Una ronda cerrada con ceros no verificables se mostraba como definitiva |
| `templates/encuestas/ficha_paciente.html` | Igual que el tablero, pero con su propia copia de la condición | Lo mismo, con riesgo de que ambas copias divergieran |
| `rondas/cierre.py: puntaje_mrs_definitivo()` | Cerrada y completa → puntaje | No consideraba los ceros no verificables (devolvía 16) |
| `static/js/encuesta.js: burbujaPuntajeMrs()` | «Puntaje MRS: X / 44» y, con los 11 ítems, **«Severidad: Moderada»** | Categoría no validada; la suma de una ronda abierta parecía un resultado |
| `encuestas/esquema.py` | Publicaba `mrs_severidad` (cortes 4/8/15/44) en `/api/esquema/` | Permitía mostrar la categoría a cualquier cliente, incluso uno guardado en caché |
| `/api/estado/`, `/api/ronda-actual/` y `/api/sincronizar/` | No entregan puntajes | Sin cambio (lo comprueba una prueba) |
| Estadísticas profesionales | Solo cuentan registros MRS | Sin cambio |
| `MRS.__str__` (`models.py`) | Incluye «Puntaje Total» | No se muestra en ninguna pantalla: el MRS no está registrado en el admin. **No se modificó**, para no tocar `models.py`, que está protegido (§9) |

## 3. Regla única: `apps/rondas/resultado_mrs.py`

`resultado_mrs(mrs)` devuelve un `ResultadoMRS` (estado, puntaje, suma, respondidas y texto). Solo lee.

- **Ronda cerrada:** es la misma regla que usa la barrera de protección de la 40B-2, `ronda < ronda_actual`.
- **Ceros sin confirmar:** los que marca `MRSAnterior40B2` y que nadie volvió a elegir.

| Estado | Condición | Texto mostrado |
|---|---|---|
| `definitivo` | Ronda cerrada, 11 ítems, sin ceros sin confirmar y registro de ronda CERRADA | `Puntaje MRS: 20 de 44` |
| `no_verificable` | Ronda cerrada **con ceros anteriores sin confirmar**, o con un registro de ronda que no dice CERRADA (p. ej. ANULADA) | `Resultado histórico no verificable` (sin número) |
| `incompleto` | Ronda cerrada a la que le faltan ítems (no debería ocurrir desde la 40B-2) | `Resultado incompleto: 1 de 11 preguntas respondidas` |
| `provisional` | Ronda abierta con los 11 ítems | `Suma provisional: 22 de 44 (la ronda no está cerrada)` |
| `parcial` | Ronda abierta con ítems sin responder. Los ceros antiguos sin confirmar cuentan como sin responder | `Suma parcial: 3 (2 de 11 preguntas respondidas; la ronda no está cerrada)` |
| `sin_datos` | Sin MRS | (nada) |

**Dónde se usa:**

- `puntaje_mrs_definitivo()` ahora delega en esta función y devuelve `None` también para los resultados no verificables.
- `historial.construir_historial()` calcula el resultado una vez por ronda, con una sola consulta de estados.
- El tablero y la ficha muestran el mismo fragmento `encuestas/_resultado_mrs.html`. Ninguna plantilla lee `puntaje_total`, y una prueba lo comprueba.

**No se reconstruye ni se convierte nada:** los ceros antiguos siguen siendo `0` en la base y las marcas de la 40B-2 no se tocan.

## 4. Severidad

- `esquema.py` ya no publica `mrs_severidad`. La burbuja de la encuesta muestra solo:
  - «Suma parcial: X / 44 · N de 11 preguntas respondidas»; o
  - «Suma provisional: X / 44 · Se confirma al finalizar la encuesta».
- `MRS.SEVERIDAD_TOTAL` **no cambió**. Una prueba lo comprueba, y `test_40b0` comprueba que la limpieza congelada sigue igual.
- **No se recalculó ningún análisis.**
- **Lo que sigue apareciendo** son las opciones de respuesta **de cada ítem** del instrumento MRS (Ninguna / Leve / Moderada / Intensa / Muy intensa) y la opción «Leve» de `tipo_sangrado`. Son parte del cuestionario, no categorías del puntaje total, y se mantienen.

## 5. Archivos modificados

| Archivo | Cambio |
|---|---|
| `src/apps/rondas/resultado_mrs.py` | **Nuevo:** la regla única |
| `src/apps/rondas/cierre.py` | `puntaje_mrs_definitivo()` delega en la regla única |
| `src/apps/encuestas/historial.py` | Agrega `resultado_mrs` a la sección MRS de cada ronda |
| `src/templates/encuestas/_resultado_mrs.html` | **Nuevo:** el único fragmento que muestra el resultado |
| `src/templates/encuestas/mi_tablero.html` y `ficha_paciente.html` | Usan el fragmento en vez de `puntaje_total` |
| `src/apps/encuestas/esquema.py` | Deja de publicar `mrs_severidad` |
| `src/static/js/encuesta.js` | Burbuja parcial o provisional, sin severidad; el gancho de pruebas expone `burbujaMrs` (solo existe en las pruebas) |
| `src/static/js/sw.js` | Caché `aging-women-v13`, porque cambió `encuesta.js` |
| `src/apps/rondas/test_40b3.py` | **Nuevo:** 15 pruebas |
| `src/apps/encuestas/tests.py` | `test_incluye_cortes_de_severidad_mrs` pasa a `test_no_publica_cortes_de_severidad_mrs` |
| `src/apps/encuestas/pruebas_js/test_encuesta_sync.mjs` | 1 prueba nueva (burbuja) |
| `src/apps/encuestas/pruebas_js/esquema_*.json` | Regenerados (sin `mrs_severidad`) |
| `analisis/fase40/40B_implementacion/40B-1_informe.md` | Corrección documental (§6 de este informe) |
| `analisis/fase40/40B_implementacion/evidencias_40B-3/` | Capturas y resultados del navegador (datos sintéticos) |

**No se modificaron:**

- `models.py` ni las migraciones;
- `sync.py`, `completitud.py` ni `proteccion.py`;
- los archivos de las Fases 34–39, los manifiestos y las huellas.

## 6. Corrección documental de la 40B-1

En `40B-1_informe.md`:

- la fila 14 de §7 queda tachada y marcada **«No verificado en la 40B-1»**;
- §6 lleva una nota;
- la §13 nueva explica:
  - **qué se ejecutó realmente:** una única ejecución completa, `FAILED (failures=4)`, y luego solo 2 de las 3 pruebas;
  - **por qué ocurrió:** la prueba exigía huellas exactas y tres scripts ya diferían por cambios anteriores, pero se informó la reejecución parcial como si fuera la completa;
  - **cómo se verificaron después las tres excepciones:** el manifiesto del cierre 34-35 y `NUEVOS_AUTORIZADOS` para los EDA, y la 40B-0 para `catalogo.py`;
  - **por qué las Fases 34–39 siguen siendo reproducibles:** 6.457 huellas, pruebas que rehacen los cálculos y la limpieza congelada.

No se cambió ningún resultado, manifiesto ni huella.

## 7. Pruebas ejecutadas (2026-11-06)

### 7.1 Lista mínima del encargo

| # | Requisito | Pruebas | Resultado |
|---|---|---|---|
| 1 | Cerrada y verificable → definitivo | `test_1_…` (20 de 44 en la función, el tablero y la ficha), `test_1b_…` (ceros antiguos **confirmados** → definitivo) | OK |
| 2 | Cerrada con ceros sin confirmar → no verificable | `test_2_…`: texto exacto, sin número en ninguna de las dos páginas y `puntaje_mrs_definitivo` = None. Además, los valores siguen siendo `0` y la marca no cambia. `test_2b_…` (registro ANULADA), `test_2c_…` (cerrada incompleta) | OK |
| 3 | Abierta y parcial → nunca definitivo | `test_3_…`, `test_3b_…` (los ceros antiguos cuentan como sin responder); Node: burbuja «Suma parcial» | OK |
| 4 | Abierta y completa → provisional | `test_4_…` (22 de 44, provisional; ninguna página dice «Puntaje MRS: 22»); Node: burbuja «Suma provisional» | OK |
| 5 | Tablero y ficha consistentes | `test_5_…` (ronda cerrada + ronda abierta), `test_5b_…` (histórica), `test_5c_…` (ninguna plantilla ni vista lee `puntaje_total`), `test_5d_…` (las API no entregan puntajes) | OK |
| 6 | Sin categorías de severidad | `test_6_…`: con 44 puntos (antes «Severa») y 11 (antes «Moderada») ninguna página muestra una categoría; el esquema y `encuesta.js` sin cortes. Node: sin «Severidad» en la burbuja. `test_6b_…`: los cortes históricos siguen intactos | OK |
| 7 | Integridad | `test_7_…`: presentar el resultado no ejecuta ningún INSERT, UPDATE ni DELETE de datos, y los MRS y las marcas quedan idénticos. En desarrollo, solo lectura (§8.2): 0 escrituras | OK |
| 8 | Django y JS | Django **286/286** (271 + 15), también `--reverse`; Node **12/12**; `makemigrations --check`: sin cambios | OK |
| 9 | Protección de las Fases 34–39 | `test_40b0` **15/15**; `test_40b1_proteccion_historica` **5/5** (6.457 artefactos, las mismas 3 excepciones con su huella); `test_entropia` 79/79, `test_revision_35b` 43/43, `test_h11_h13` 21/21; ningún archivo de `analisis/` ni de `datos/` fuera de `fase40/` modificado | OK |

### 7.2 Compatibilidad

La suite completa incluye las 36 pruebas de la 40B-2 y las de la 40B-1, y todas pasan. Cubren:

- el guardado parcial y la reanudación;
- las 11 preguntas MRS obligatorias;
- el EMPA no bloqueante;
- el cierre transaccional e idempotente, incluidos los cierres concurrentes;
- el rechazo de envíos tardíos;
- el registro de rondas;
- el modo offline (Node).

`test_07b` de la 40B-2 sigue viendo «provisional» en el tablero.

## 8. Evidencias

### 8.1 Navegador real con datos sintéticos

**Entorno:**

- Chrome 157 sin interfaz, controlado por DevTools;
- contenedores aislados con una base **nueva** y una red propia;
- secretos aleatorios y cuentas ficticias (RUT 11.111.111-1, 22.222.222-2 y 33.333.333-3);
- datos cargados con `sincronizar_payload`;
- el caso histórico se simuló como lo hace la migración: ceros sin elegir, marca 40B-2 y cierre por la vía antigua.

El entorno, sus volúmenes y los perfiles se eliminaron al terminar.

| Comprobación | Resultado |
|---|---|
| Tablero de A | `parcial` «Suma parcial: 3 (2 de 11…)» (ronda 2) y `definitivo` «Puntaje MRS: 44 de 44» (ronda 1); sin categorías |
| Ficha de A (profesional) | **Idéntica** al tablero |
| Ficha y tablero de B (histórico) | `no_verificable` «Resultado histórico no verificable» en ambos; sin número |
| Encuesta en curso | Burbuja «Suma parcial: 3 / 44 · 2 de 11 preguntas respondidas» → tras responder todo: «Suma provisional: 39 / 44 · Se confirma al finalizar la encuesta». En la página solo aparecen las opciones de respuesta de los ítems |
| Service Worker | Activo, con una única caché `aging-women-v13` |

**Capturas** (solo datos sintéticos), en `evidencias_40B-3/`:

- `captura_tablero_usuaria.png`
- `captura_ficha_A.png`
- `captura_ficha_B_historica.png`
- `captura_encuesta_burbuja_provisional.png`
- `resultados_navegador_40b3.json`

En la ficha se ve el hash del RUT ficticio, calculado con un «pepper» aleatorio de un entorno ya destruido.

### 8.2 Base de desarrollo, solo lectura (0 escrituras)

| MRS | Ronda | Antes (ficha/tablero) | Ahora |
|---|---|---|---|
| 1 | 1 (abierta) | 31 (provisional) | Suma provisional: 31 de 44 |
| 2 | 1 (cerrada) | 29 | Puntaje MRS: 29 de 44 |
| **3** | 1 (cerrada, 2 ceros sin confirmar) | **16** | **Resultado histórico no verificable** |
| **4** | 1 (cerrada, 6 ceros sin confirmar) | **9** | **Resultado histórico no verificable** |
| 5 y 6 | 2 (abiertas, 11 ceros sin confirmar) | 0 (provisional) | Suma parcial: 0 (0 de 11…) |
| 7 | 1 (cerrada) | 27 | Puntaje MRS: 27 de 44 |

La ficha 11 renderizada muestra ahora solo «Resultado histórico no verificable».

## 9. Decisiones y límites

- **No se modificó `models.py`.**
  - `MRS.puntaje_total` sigue siendo la suma cruda; ahora solo la usa `resultado_mrs`.
  - `MRS.__str__` sigue incluyendo el puntaje, pero no llega a ninguna pantalla.
  - Cambiarlo obligaría a ampliar las excepciones de la prueba de protección de `models.py`. Se puede hacer en la 40C si se decide.
- **Criterio de «cerrada».** Se usa `ronda < ronda_actual`, el mismo que la barrera de protección de la 40B-2. Además, un registro 40B-1 distinto de CERRADA (p. ej. ANULADA) impide el resultado definitivo.
- **Clientes con caché antigua.** Un cliente con el `encuesta.js` anterior en caché tampoco muestra severidad: el esquema ya no trae los cortes. La caché v13 reemplaza el archivo al instalarse el Service Worker nuevo.
- **Sin tablero de tendencias.** No se implementó ningún elemento de tendencias ni de evolución (40C).

## 10. Riesgos pendientes

### 10.1 Privacidad (revisión correctiva 40B-2, §8; sin implementar, por decisión)

1. **Respuestas legibles tras cerrar sesión:** IndexedDB y la copia de `/encuesta/` del Service Worker. Sin sesión ni red se ve la encuesta anterior.
2. **Respuestas de pacientes en equipos compartidos:** los borradores de cada paciente permanecen después de «Salir».
3. **Reenvío después del retiro:** si la mujer vuelve a aceptar el consentimiento, otro dispositivo reenvía lo borrado y el servidor lo vuelve a crear.
4. **Acceso profesional sin consentimiento registrado:** una profesional puede crear por RUT la ficha de una mujer retirada sin que se revise su consentimiento.

### 10.2 Decisiones de diseño aprobadas para la etapa de privacidad y consentimiento

No implementadas en la 40B-3:

- sincronizar antes de cerrar sesión cuando sea posible;
- limpiar los datos locales sensibles al completar el cierre;
- si hay respuestas sin sincronizar, advertir y ofrecer tres opciones: conservar la sesión, sincronizar o descartar expresamente;
- nunca eliminar en silencio respuestas pendientes;
- el retiro debe impedir que reaparezcan respuestas antiguas, incluso después de una reincorporación;
- se puede conservar una constancia técnica mínima, sin información de salud y con retención y acceso limitados, para impedir reenvíos antiguos.

Estos riesgos **impiden usar AgingWomen con participantes reales** hasta que se resuelvan.

### 10.3 Otros

- Punto de corte de severidad para la plataforma: pendiente de validación. Hasta entonces no se muestra ninguna categoría.
- `MRS.__str__` con puntaje (§9).
- La primera visita sin conexión con el Service Worker aún sin instalar (revisión correctiva 40B-2, §10).

## 11. Condiciones para comenzar la 40C

**Desde el punto de vista técnico, la 40C puede comenzar.** La regla de verificabilidad ya existe y está centralizada. Condiciones:

1. **Revisión y aprobación de este informe.**
2. **Construir sobre `resultado_mrs()`.** Las instantáneas, `ResultadoRonda` y la evolución deben usar solo resultados `definitivo`:
   - una ronda `no_verificable` o `incompleto` se muestra como «no comparable» y no entra en tendencias;
   - una tendencia necesita al menos dos rondas definitivas (plan 40A, §5).
3. **No incorporar categorías de severidad** mientras no se valide el corte para la plataforma.
4. **La 40C no habilita el uso real.** El uso con participantes reales sigue condicionado a la etapa de privacidad y consentimiento (§10).
