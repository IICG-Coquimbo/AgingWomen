# Fase 40C-P — Tablero estadístico profesional (informe único)

Fecha: 2026-11-07 · Rama `datos-simulados` · Sin commit ni push · Sin migraciones · Base de desarrollo, fichas, rondas, orientaciones y análisis 34–39 sin cambios.

## 1. Funcionalidades

La página `/profesional/estadisticas/` («Estadísticas generales») reemplaza los indicadores básicos de la Fase 17. Muestra:

- **Indicadores generales:**
  - participantes incluidas;
  - rondas cerradas y verificables;
  - promedio y mediana del MRS total.
- **Cinco visualizaciones:**
  1. distribución del MRS total, en tramos de 5 puntos;
  2. promedio de las dimensiones somática, psicológica y urogenital;
  3. participantes por tramo de edad;
  4. participantes por etapa menopáusica;
  5. participantes por grupo B1, con los nombres amigables.

  Son barras HTML/CSS generadas en el servidor, sin bibliotecas nuevas ni JavaScript. Cada una tiene título, unidad, denominador y una explicación.
- **Caracterización por grupos:** tabla con el tamaño y el MRS promedio de cada grupo, y la cantidad de participantes sin grupo verificable. Incluye el aviso de que es descriptiva: no son categorías clínicas, no explican causas y no generan recomendaciones.
- **Registros no incluidos:** cuántos se excluyen y por qué.
- **Mensajes sin datos:** con menos de 5 participantes, un mensaje claro reemplaza todas las cifras.

**Archivos:**
- nuevos: `apps/encuestas/estadisticas.py`, `templates/encuestas/_barras_estadisticas.html` y `apps/encuestas/test_estadisticas.py`;
- modificados: `profesional.py` (vista), `estadisticas.html`, los textos de los enlaces en `home.html` y `buscar_paciente.html`, `tema.css`, `sw.js` (caché v18) y la versión de caché que verifica `test_40c`;
- en `tests.py`, se quitaron tres pruebas de los indicadores de la Fase 17 que ya no existen.

## 2. Población, cálculos y denominadores

| Regla | Decisión |
|---|---|
| Base de consentimiento | Ficha de una **cuenta de usuaria con `consentimiento_aceptado_en`**. Los **registros presenciales sin cuenta se excluyen**, porque el consentimiento presencial aún no se registra (DC pendiente). Las retiradas no existen: el retiro borra la ficha |
| Una ronda por mujer | La **última ronda cerrada y verificable** (`FINALIZADA_VERIFICABLE`: resultado MRS definitivo de la regla única 40B-3). Si una participante no tiene ninguna, queda excluida. Nunca se cuenta dos veces |
| Rondas verificables | Se suman todas las rondas cerradas y verificables de las incluidas |
| MRS y dimensiones | Se toman tal cual de `resultado_mrs` (somática 0–16, psicológica 0–16, urogenital 0–12). Promedio y mediana, con n = participantes incluidas |
| Edad | Edad cumplida **al cierre** de la ronda de referencia, solo si ese cierre tiene fecha verificable. Si no la tiene, queda «Sin edad verificable». Nunca se usa la edad de hoy. Tramos: menos de 40, 40–44, …, 60–65 y más de 65 |
| Etapa menopáusica | **No disponible.** La plataforma no la registra: solo existe como variable descriptiva de los análisis (decisión del 2026-11-01). No se recalcula |
| Grupo B1 | `contexto_de_ronda` de la misma ronda de referencia (regla 37C, sin cambios). Si falta alguna variable, queda «Sin grupo verificable». No se imputa |

Denominador de cada gráfico: las participantes incluidas (se muestra en pantalla).

**Diferencia con las orientaciones:** las orientaciones usan la *última ronda cerrada* solo si es verificable. Aquí, como pide el alcance, se usa la *última cerrada y verificable*.

## 3. Privacidad

- **Permiso en el servidor:** `@login_required` + `@requiere_profesional`. La usuaria común recibe 403 y la persona anónima es redirigida al ingreso. La respuesta va con `Cache-Control: no-store`.
- **Solo agregados:** nada de RUT, correos, nombres, enlaces a fichas ni respuestas individuales. La página no escribe en la base (comprobado en una prueba).
- **Umbral de publicación k = 5:**
  - Con menos de 5 incluidas no se publica ninguna cifra.
  - En cada distribución se ocultan las celdas de 1 a 4.
  - **Supresión complementaria:** se ocultan además las celdas visibles más pequeñas hasta que las ocultas sean al menos 2, sumen 5 o más y no puedan ser todas de 1. Si no se logra, se oculta la distribución entera. Los ceros sí se muestran.
  - El promedio de un grupo solo se publica si su celda se publica y tiene al menos 5 participantes.
  - Los conteos de exclusión menores que 5 se muestran como «menos de 5».
- **Protecciones que no cambian:** sesión, IndexedDB cifrado y offline. La página no se guarda en la caché offline.

## 4. Pruebas

| Conjunto | Resultado |
|---|---|
| Nuevas (`test_estadisticas`) + acceso de la Fase 17 | 10/10 |
| Django, suite completa | **360/360 OK** (1 omitida, ya existente) |
| JavaScript (`pruebas_js`) | 18/18 |
| Integridad 40B-0 + protección histórica 40B-1 | OK (6.457 artefactos; Fases 34–39 intactas) |
| Chrome real sin interfaz, entorno aislado | 10/10 comprobaciones funcionales (detalle abajo) |

**Qué cubren las pruebas nuevas:**
- acceso: profesional, usuaria común y anónima;
- sin datos suficientes;
- exclusión de cuentas sin consentimiento, registros presenciales, rondas abiertas y rondas cerradas no verificables;
- una participante con 2 rondas cuenta una vez, con la última;
- promedio 12,5, mediana 10,5 y dimensiones 4,2, calculados a mano;
- ronda sin fecha de cierre → «Sin edad verificable»;
- grupos B1, grupo vacío y sin grupo;
- supresión complementaria: prueba exhaustiva de 4.096 combinaciones, ninguna celda oculta se puede deducir;
- sin identificadores ni escrituras.

**Chrome real sin interfaz** (base PostgreSQL nueva, secretos aleatorios, 19 cuentas `@ficticio.cl`, puerto 8010; se eliminó al terminar):
- sin datos: mensaje y ninguna cifra;
- con datos: 4 indicadores y 5 gráficos;
- Grupo 3 (2 participantes) oculto, y Grupo 1 oculto por supresión complementaria;
- sin identificadores;
- móvil de 390 px sin desborde horizontal;
- usuaria común rechazada y anónima enviada al ingreso.

El único mensaje de consola fue el 403 esperado de la usuaria común. Evidencia en `evidencias_40C-P/` (capturas de escritorio, móvil y sin datos, y `resultados_navegador.json`). Después de las capturas solo se alineó a la izquierda el título de la tabla de grupos (CSS).

## 5. Limitaciones

- Los **registros presenciales quedan fuera** hasta decidir y registrar el consentimiento presencial (DC).
- La **etapa menopáusica** no se puede mostrar sin una regla validada para la plataforma.
- Las **rondas retrocargadas sin fecha** no tienen edad verificable. Con datos históricos, ese tramo puede ser grande.
- El cálculo recorre el historial de cada ficha; para cientos de participantes es suficiente.
- Con pocas participantes, la supresión puede ocultar buena parte de las distribuciones (es lo esperado).
- Ya no aparecen la «presión alta» ni la edad promedio de la Fase 17. Eran métricas sobre todas las fichas, sin filtro de consentimiento.
