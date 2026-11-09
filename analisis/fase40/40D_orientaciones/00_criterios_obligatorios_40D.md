# Fase 40D — Criterios obligatorios para las recomendaciones personalizadas

> **Nota de actualización (2026-11-09):** B1 sí se muestra a la participante en su tablero, por decisión de la responsable para la revisión de la profesora guía (Fase 40D-H), con la advertencia de que es exploratorio y no es un diagnóstico. Sigue sin seleccionar ni modificar orientaciones (C-5) y no aparece en la ficha individual del profesional. La referencia de C-5 a no mostrar clústeres a la usuaria quedó reemplazada en ese punto; el resto de C-5 sigue vigente.

**Fecha de la decisión:** 2026-11-06 · **Estado:** criterios registrados; la Fase 40D **no se ha iniciado** y no hay código. Todo sigue local (sin commit ni push) hasta terminar la Fase 40.

## Alcance

Todas las recomendaciones personalizadas deben tener un enfoque **educativo y preventivo**. Esto incluye:
- las que se basan en respuestas individuales;
- las que algún día incorporen información de grupos de caracterización (40E).

Estos criterios son **requisitos de diseño y de aceptación** de la 40D: una orientación que no cumpla alguno no se publica, y una versión del catálogo que no los cumpla no pasa las pruebas.

## Criterios (C-1 a C-8) y cómo se comprobarán

| Criterio | Exigencia | Cómo se aplicará en el diseño | Prueba de aceptación prevista |
|---|---|---|---|
| **C-1 Aviso de no diagnóstico** | Aviso visible y siempre presente: las recomendaciones no son un diagnóstico médico ni reemplazan la evaluación, el tratamiento ni las indicaciones de profesionales de salud | Un texto único en un componente fijo de la sección de recomendaciones, no dentro de cada tarjeta, para que no dependa del contenido | El aviso aparece en el tablero cada vez que hay recomendaciones, también con 0 o 1 orientaciones y en móvil; un texto distinto o ausente hace fallar la prueba |
| **C-2 «¿Cuándo consultar a un profesional de salud?»** | Cada orientación tiene esa sección, adaptada al tema y con fuentes verificables | El esquema del catálogo la vuelve **obligatoria** en cada orientación, con al menos una fuente propia | La validación del catálogo rechaza una orientación sin esa sección, con la sección vacía o sin fuente; cada tarjeta mostrada la contiene |
| **C-3 Contenidos prohibidos** | Sin diagnósticos, pronósticos, tratamientos farmacológicos personalizados ni indicaciones para suspender medicamentos | Revisión del contenido por la responsable y una profesional de salud (dependencia ya prevista en la 40A). El motor solo elige orientaciones; nunca compone texto clínico | Lista de expresiones vetadas sobre todo el catálogo y las páginas generadas (p. ej., «usted tiene», «padece», «diagnóstico de», «pronóstico», «evolucionará», dosis o nombres de fármacos con indicación, «suspenda», «deje de tomar»). Revisión humana registrada por versión |
| **C-4 Señales de alerta** | Cuando haya señales de alerta respaldadas por evidencia, indicar con claridad cuándo buscar atención médica oportuna o urgente | Campo de señales de alerta en el catálogo, con su nivel (oportuna o urgente) y su fuente. Incluye el mensaje de apoyo del ítem 5 (ánimo depresivo, `pregunta_5`; T-26 y DR-6 de la 40A) con los números vigentes de MINSAL (DV-3) | Toda señal de alerta lleva nivel y fuente; el mensaje de apoyo aparece siempre y con prioridad cuando corresponde (T-26); los números de contacto se validan contra la fuente y su fecha |
| **C-5 Grupos de caracterización** | Nunca afirmar que pertenecer a un grupo determina necesidades clínicas individuales | Si algún día se usa un grupo (40E), solo como contexto descriptivo, con texto fijo de advertencia. Ninguna condición clínica se deriva del grupo (coherente con DT-7: no mostrar clústeres a la usuaria) | Ninguna orientación usa el grupo como condición única; en las páginas no hay frases que vinculen grupo con necesidad clínica; con la 40E apagada, no aparece ninguna referencia a grupos |
| **C-6 Fuentes confiables y trazables** | Cada orientación con su fuente sanitaria confiable, procedencia y fecha de consulta | En el catálogo, cada fuente lleva institución, título, URL o referencia y fecha de consulta. Fuentes candidatas: MINSAL, OMS, NICE y The Menopause Society (DV-4). El catálogo está versionado | La validación rechaza fuentes sin institución, referencia o fecha; se avisa de fuentes con fecha de consulta antigua (umbral a definir con la responsable); la ronda guarda la versión del catálogo usada (T-17) |
| **C-7 Lenguaje** | Cercano, respetuoso, comprensible y no alarmista | Guía de redacción para el contenido: trato de tú, coherente con la plataforma; frases breves; sin imperativos amenazantes; las alertas, claras pero sin dramatizar | Revisión humana del contenido por versión; prueba automática de términos alarmistas vetados (p. ej., «peligro», «grave» fuera de una alerta respaldada, exclamaciones) y de longitud de frase |
| **C-8 Advertencia sin confirmaciones repetitivas** | La advertencia general permanece visible en la sección, sin pedir confirmaciones repetidas | El aviso de C-1 es texto fijo: sin ventanas modales ni casillas «He leído» antes de cada consulta | Ninguna página de recomendaciones exige un clic o confirmación previa para ver su contenido; el aviso está presente sin interacción |

## Relación con decisiones anteriores

- **Severidad:** no se usan categorías de severidad del MRS mientras no se validen sus puntos de corte (DV-1; decisión de la 40B-3). Ninguna recomendación puede depender de esos cortes.
  - Corrige la expectativa «Sin síntomas o muy leves» del caso T-04 de la matriz 40A, que quedó superada.
- **Evolución:** tampoco se califica como mejoría o empeoramiento mientras no exista la diferencia mínima importante (DV-5; igual que en la 40C).
- **Datos de entrada:** solo resultados definitivos de rondas cerradas y verificables (regla única `resultado_mrs.py`). No se usan rondas abiertas, rondas no verificables ni datos actuales como si fueran históricos.
- **Bloqueo externo (40A):** el contenido debe escribirlo y aprobarlo la responsable junto con una profesional de salud. Sin ese contenido, la 40D no puede cerrarse.

## Pendientes antes de diseñar la 40D

1. Contenido de las orientaciones y sus secciones «¿Cuándo consultar…?» (responsable y profesional de salud).
2. Señales de alerta por tema y su nivel (oportuna o urgente), con su fuente.
3. Texto del mensaje de apoyo y si el profesional ve una marca (DR-6), y números vigentes (DV-3).
4. Umbral de antigüedad de las fuentes para revisarlas.
5. Texto exacto del aviso general (C-1).
