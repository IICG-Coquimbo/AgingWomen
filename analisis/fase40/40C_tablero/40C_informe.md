# Fase 40C — Tablero individual de resultados y evolución MRS

**Fecha:** 2026-11-06 · **Rama:** `datos-simulados` · **Estado:** implementada y probada, **sin commit ni push**, en espera de revisión.

No se modificaron las Fases 34–39, no se recalcularon modelos, no se incorporaron agrupamientos al tablero, no se implementaron cambios de privacidad ni de consentimiento y no se inició la 40D.

---

## 1. Qué información existe por ronda (revisión previa)

| Dato | ¿Existe por ronda? | Uso en 40C |
|---|---|---|
| 11 respuestas MRS (`pregunta_1`…`11`, con `ronda`) | Sí | Única fuente de los resultados |
| Estado del registro de ronda (`RondaEvaluacion`, 40B-1) | Sí | Lo usa la regla única `resultado_mrs` |
| Ceros anteriores a la 40B-2 sin confirmar (`MRSAnterior40B2`) | Sí | La ronda pasa a «Histórica no verificable» |
| Fecha real de cierre (`cerrada_en`) | Solo en cierres validados desde la 40B-2 | Se muestra solo en ese caso |
| `MRS.fecha_evaluacion` | Es la fecha en que se creó la fila (`auto_now_add`) | **No** se usa como fecha de la ronda |
| Instantánea sociodemográfica de cada ronda | No existe (`instantanea_disponible=False`) | No se reconstruye; los datos se rotulan «Datos actuales» |
| Versión del cuestionario | Desconocida en las retrocargadas | No se usa |

**No se puede reconstruir:**
- las fechas de finalización anteriores a la 40B-2;
- las respuestas reales detrás de ceros heredados sin confirmar;
- los datos sociodemográficos de rondas pasadas.

**Base de desarrollo** (comprobación de solo lectura, conteos sin valores):
- 5 fichas;
- rondas: 5 en curso, 2 finalizadas y verificables, 2 históricas no verificables;
- las 4 rondas cerradas no tienen fecha verificable (todas son retrocargadas);
- 2 fichas tienen gráfico y ninguna tiene tendencia, porque ninguna tiene dos rondas verificables seguidas.

## 2. Verificación de las dimensiones MRS (obligatoria antes de implementar)

Se comprobó **por el contenido de cada síntoma** (el `help_text` de cada campo de `models.py`, que es el texto que ve la participante en el formulario), no por el número ni por `nucleo_37d.py`.

| Ítem en la escala original (Heinemann) | Síntoma | Campo en AgingWomen | Dimensión |
|---|---|---|---|
| 1 | Bochornos, sudoración | `pregunta_1` | Somática |
| 2 | Molestias al corazón | `pregunta_2` | Somática |
| 11 | Molestias musculares y articulares | `pregunta_3` | Somática |
| 3 | Problemas de sueño | `pregunta_4` | Somática |
| 4 | Estado de ánimo depresivo | `pregunta_5` | Psicológica |
| 5 | Irritabilidad | `pregunta_6` | Psicológica |
| 6 | Ansiedad | `pregunta_7` | Psicológica |
| 7 | Cansancio físico y mental | `pregunta_8` | Psicológica |
| 8 | Problemas sexuales | `pregunta_9` | Urogenital |
| 9 | Problemas con la orina (vejiga) | `pregunta_10` | Urogenital |
| 10 | Sequedad vaginal | `pregunta_11` | Urogenital |

**Resultado:** el formulario de AgingWomen tiene un orden **distinto** al original: el ítem 11 original (musculares y articulares) es aquí `pregunta_3`, y los ítems originales 3–10 están desplazados un lugar. Aun así, al agrupar por contenido:

- **Somática** = `pregunta_1`–`4` (0–16);
- **Psicológica** = `pregunta_5`–`8` (0–16);
- **Urogenital** = `pregunta_9`–`11` (0–12).

Esto coincide con la definición de `nucleo_37d.py`. **No hay discrepancia**, así que se implementó.

Que queden en bloques seguidos se debe al orden del formulario, no a una suposición. La tabla quedó documentada en el docstring de `resultado_mrs.py`. La prueba 2 verifica la correspondencia buscando el texto del síntoma en el `help_text` de cada campo, y usa valores asimétricos para detectar cualquier campo mal asignado.

## 3. Diseño implementado

No hay tablas nuevas ni migraciones (`makemigrations --check`: sin cambios), y `models.py` no se modificó. Los resultados se calculan al mostrarlos con la regla única. Esto se desvía del plan 40A (`InstantaneaRonda` / `ResultadoRonda`), con aprobación: el tablero solo necesita las respuestas MRS y el registro de rondas, que ya existen.

| Archivo | Cambio |
|---|---|
| `src/apps/rondas/resultado_mrs.py` | `DIMENSIONES` (con verificación de que reparten los 11 ítems sin repetir ni omitir), `Dimension`, y el campo `ResultadoMRS.dimensiones`, que se llena **solo** en DEFINITIVO. `como_dict()` incluye las dimensiones |
| `src/apps/encuestas/historial.py` | Cada ronda lleva `resultado_mrs`, `estado`, `estado_texto` y `fecha_cierre`. Constantes de estado. `fecha_cierre_verificable()` |
| `src/apps/encuestas/evolucion.py` (nuevo) | Series de evolución y geometría SVG a partir del historial, sin consultas propias. Tramos, huecos y avisos |
| `src/templates/encuestas/_evolucion_mrs.html` (nuevo) | Sección «Resultados MRS por ronda», común al tablero y a la ficha |
| `src/templates/encuestas/_grafico_mrs.html` (nuevo) | Un gráfico SVG accesible (`role="img"`, `<title>` y `<desc>`) |
| `src/templates/encuestas/_ronda_historial.html` (nuevo) | Tarjeta de una ronda del historial, común al tablero y a la ficha; reutiliza `_resultado_mrs.html` |
| `mi_tablero.html`, `ficha_paciente.html` | Incluyen los componentes. Los datos de identificación quedan bajo «Datos actuales» |
| `tablero.py`, `profesional.py` | Pasan `evolucion` al contexto. **Permisos sin cambios** |
| `src/static/css/tema.css` | Estilos 40C con la paleta violeta existente, adaptables al móvil |
| `src/static/js/sw.js` | `CACHE` v13 → v14 (cambió `tema.css`) |
| `src/apps/rondas/test_40c.py` (nuevo) | 18 pruebas |

### 3.1 Reglas aplicadas

- **Puntos del gráfico:** solo rondas **cerradas con resultado DEFINITIVO**. La regla es la misma de la 40B-3 y no se duplica.
- **Ronda en curso:** nunca entra en el gráfico. Su suma provisional o parcial aparece solo en el historial, con estilo distinto (cursiva y borde punteado) frente al definitivo (negrita y fondo violeta).
- **Ronda histórica no verificable:** aparece en el eje como **hueco**, con una línea vertical punteada y sin valor (ni cero). La línea se **corta** en ella. En las tablas figura como «Sin resultado verificable».
- **Tendencia:** solo con al menos dos rondas verificables **seguidas**.
  - Con una sola ronda verificable: un punto y el aviso «Hay una sola ronda con resultado verificable: todavía no se puede mostrar una evolución».
  - Con verificables no seguidas: puntos sin unir y un aviso.
  - Sin ninguna verificable: no hay gráfico y se muestra un mensaje.
- **Eje horizontal:** el número de ronda. No hay fechas dentro del SVG.
- **Estados del historial:**
  - «En curso» (con «Todavía puede seguir respondiéndose»);
  - «Finalizada y verificable»;
  - «Histórica no verificable».
- **Fecha de cierre:** solo si la ronda la cerró el **cierre validado de la 40B-2** (origen NORMAL, CERRADA, con `id_cierre` y con el rol de quien cerró). En los demás casos se muestra «Fecha no registrada».
  - Esta condición es más estricta que «origen NORMAL»: el cierre por la señal antigua copia `ultima_finalizacion_en`, que puede corresponder a una ronda anterior.
  - La columna de cada sección se renombró a «Fecha de registro», para que no se confunda con el cierre.
- **Presentación:**
  - primero el total, con su gráfico y una tabla equivalente visible;
  - las dimensiones van en una sección plegable («Ver las tres dimensiones…») con sus tres gráficos y una tabla única;
  - cada gráfico explica qué mide.
- **Sin severidad ni interpretación:** no hay categorías ni conclusiones clínicas. La nota fija dice: «Los gráficos describen lo informado en cada ronda: no son un diagnóstico ni indican mejoría o empeoramiento».
  - `MRS.SEVERIDAD_TOTAL` queda intacta.
- **Datos actuales:** edad, región y comuna se muestran bajo «Datos actuales», con la aclaración de que no corresponden a una ronda en particular. Se aplica igual en el tablero y en la ficha.

### 3.2 Decisiones aprobadas y cómo se cumplieron

| Decisión | Cumplimiento |
|---|---|
| 1. SVG generado en el servidor, sin bibliotecas ni CDN | Sí. La prueba 15 verifica que los componentes no tienen `<script>` ni `http` |
| 2. Tablero y ficha con el mismo componente y permisos existentes | Sí. La sección es idéntica byte a byte en el navegador y en la prueba 12 |
| 3. Fecha real solo si es verificable; si no, «Fecha no registrada» | Sí, con la condición estricta del §3.1 |
| 4. «Datos actuales» | Sí, en las dos pantallas |

### 3.3 Desviaciones del diseño propuesto

1. **Criterio de fecha verificable más estricto** (§3.1). Exige además `id_cierre` y el rol de quien cerró, por la fecha posiblemente arrastrada del cierre por señal.
2. **Componente de historial compartido** (`_ronda_historial.html`). No se había anunciado. Elimina el bloque duplicado entre las dos plantillas, así la coherencia no depende de mantener dos copias.
3. **Estilos para `resultado-mrs--*`.** No existían en `tema.css`; antes de la 40C, definitivo y provisional solo se distinguían por el texto. Se agregaron para cumplir «definitivos y provisionales visualmente distintos».

## 4. Privacidad

- **Datos de la ficha:** el tablero sigue leyendo solo la ficha propia (`usuario=request.user`).
- **Ficha profesional:** sigue exigiendo `@requiere_profesional`. Una usuaria recibe 403, comprobado en el navegador.
- **URL nuevas:** no se agregaron URL ni endpoints. No hay identificadores ni valores en las URL.
- **Registros y mensajes de error:** no se agregó ningún registro (`logger`) ni mensaje con valores.
- **Service worker:** sigue sin guardar en caché ni el tablero ni la ficha (solo `/encuesta/` y los estáticos). Solo cambió la versión de la caché.
- **Datos mostrados:** los gráficos muestran los mismos puntajes que el historial ya mostraba (40B-3), más las dimensiones.

**Conclusión:** no detecté una exposición nueva atribuible al tablero. Los riesgos P1–P7 documentados en la 40B-2 y la 40B-3 siguen pendientes, sin cambios.

## 5. Pruebas (todas ejecutadas el 2026-11-06)

### 5.1 Pruebas 40C (`apps.rondas.test_40c`): 18/18 OK

| N.º | Prueba | Resultado |
|---|---|---|
| 1 | Puntaje total (17 de 44, igual en tablero y ficha) | OK |
| 2 | Tres dimensiones por contenido; 8 + 3 + 6 = 17; máximos 16/16/12 | OK |
| 3 | Coherencia con `resultado_mrs` y `puntaje_mrs_definitivo`; sin dimensiones fuera de DEFINITIVO | OK |
| 4 | Una ronda: un punto, sin línea, con aviso | OK |
| 5 | Varias rondas: una línea en orden ascendente; dimensiones por ronda | OK |
| 6 | Ronda abierta (44 provisional) fuera del gráfico, con aviso y estado «en curso» | OK |
| 7 | Ronda no verificable entre verificables: hueco y dos tramos (1–2 y 4–5, nunca 2–4), sin su valor | OK |
| 7b | Verificables no seguidas: sin unir | OK |
| 7c | Solo rondas no verificables: sin gráfico, con mensaje | OK |
| 8 | Fechas: cierre validado = fecha real; retrocargada y señal antigua = «Fecha no registrada»; `fecha_evaluacion` nunca usada; sin fechas en el SVG | OK |
| 9 | Sin ficha y sin rondas finalizadas: mensajes claros, sin SVG ni tablas | OK |
| 10 | Separación entre participantes (tablero, ficha y 403 para una usuaria) | OK |
| 11 | Adaptable y accesible: `viewBox` sin ancho ni alto fijos, `role`, `title`/`desc`, tablas con `caption`, dimensiones plegadas | OK |
| 12 | Tablero y ficha idénticos (sección de evolución, estados y resultados) | OK |
| 13 | Sin severidad ni conclusiones clínicas (44, 11 y 0 puntos); cortes históricos intactos | OK |
| 14 | Compatibilidad 40B-2/40B-3; mostrar las páginas no escribe nada | OK |
| 15 | Componentes sin dependencias externas ni cálculos propios; caché v14 | OK |
| 16 | La plataforma no importa nada del análisis | OK |

### 5.2 Suites completas

| Suite | Resultado |
|---|---|
| Django completo (`manage.py test`) | **304/304 OK** (286 anteriores + 18 de la 40C) |
| Django en orden inverso (`--reverse`) | **304/304 OK** |
| `makemigrations --check --dry-run` | Sin cambios |
| Node `test_encuesta_sync.mjs` | **12/12 OK** |
| 40B-0 `test_40b0_definiciones.py` | **15/15 OK** |
| 40B-1 `test_40b1_proteccion_historica.py` (integridad de las Fases 34–39) | **5/5 OK**: 6.457 artefactos por huella, 3 excepciones conocidas con su huella sin cambios |
| `analisis.preprocesamiento.test_entropia` | **79/79 OK** |
| `analisis.preprocesamiento.test_revision_35b` | **43/43 OK** |
| `cierre_fases_34_35/scripts/test_h11_h13.py` | **21/21 OK** |

### 5.3 Navegador (Chrome 157 sin interfaz, entorno aislado): 23/23 OK

**Entorno:**
- contenedores `aw_nav_db` (PostgreSQL 15 **nuevo y vacío**) y `aw_nav_web`, en una red propia, puerto `127.0.0.1:8010`;
- secretos aleatorios, distintos de los de desarrollo;
- **solo cuentas y datos sintéticos**: comuna «Santiago», correos `@ficticio.cl`.

**Al terminar** se eliminaron los contenedores, el volumen, la red, el archivo de secretos y los perfiles del navegador. No se usó la base de desarrollo.

**Escenarios:**
- **A:** rondas 1, 2, 4 y 5 verificables (17, 22, 11 y 33), ronda 3 histórica no verificable y ronda 6 en curso (44 provisional);
- **B:** una sola ronda (11);
- **C:** sin rondas finalizadas;
- **una cuenta profesional.**

**Comprobado:**
- puntos solo de las rondas verificables;
- dimensiones correctas y que suman el total;
- 2 tramos que no cruzan la ronda 3;
- ronda 6 fuera del gráfico;
- los 6 estados del historial;
- provisional y no verificable distintos del definitivo;
- «Fecha no registrada» y «Datos actuales»;
- ausencia de severidad;
- dimensiones plegadas al inicio y que se abren;
- **móvil a 390 px sin desplazamiento horizontal** (el SVG ocupa 300 px);
- 403 de la usuaria en la ficha;
- consola sin errores;
- ficha profesional **idéntica** al tablero;
- B con un solo punto y su aviso, sin datos de A;
- C con mensaje claro.

**Observación de la herramienta:** dentro de un `<details>` cerrado, Chrome conserva el tamaño interno del contenido. Para medir la visibilidad se usó `checkVisibility()`; el primer intento con `getBoundingClientRect` dio un falso negativo.

**Evidencia:** `evidencias_40C/` contiene 6 capturas (tablero de A en escritorio con y sin dimensiones, tablero de A en móvil, ficha profesional, B en móvil y C) y `resultados_navegador_40c.json`.

## 6. Limitaciones y pendientes

- Hoy en desarrollo no hay ninguna fecha de cierre verificable ni ninguna tendencia, porque todas las rondas cerradas son retrocargadas. Las fechas aparecerán con los cierres validados nuevos.
- Una ronda retrocargada con MRS completo y sin ceros pendientes sigue siendo DEFINITIVA (regla 40B-3) y aporta al gráfico, aunque no tenga fecha.
- Siguen pendientes, fuera de la 40C:
  - DV-1, puntos de corte;
  - DV-5, diferencia mínima importante; sin ella no se califica la evolución;
  - DR-5, comuna en la instantánea;
  - los riesgos de privacidad P1–P7;
  - el nuevo flujo de retiro y consentimiento.
- Todo permanece local: sin commit, sin push y sin cambio de rama.
