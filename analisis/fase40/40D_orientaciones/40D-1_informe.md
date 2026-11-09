# Fase 40D-1 — Informe: investigación y borrador del catálogo de orientaciones

> **Nota de actualización (2026-11-09):** B1 sí se muestra a la participante en su tablero, por decisión de la responsable para la revisión de la profesora guía (Fase 40D-H), con la advertencia de que es exploratorio y no es un diagnóstico. Sigue sin seleccionar ni modificar orientaciones (C-5) y no aparece en la ficha individual del profesional. Las frases «no para las participantes» y «solo en la vista profesional» quedaron reemplazadas. Se mantiene la advertencia sobre su uso con datos reales.

**Fecha:** 2026-11-06 · **Rama:** `datos-simulados` · **Estado:** borrador entregado para revisión. Sin código, sin commit ni push.

No se modificaron Django, modelos, migraciones, encuestas, datos ni resultados de las Fases 34–39. No se implementó la personalización ni el tablero de recomendaciones. No se iniciaron otras fases.

## 1. Entregables

| Documento | Contenido |
|---|---|
| `00_criterios_obligatorios_40D.md` | Criterios C-1 a C-8 (aprobados, sin cambios) |
| `40D-1_fuentes.md` | 22 fuentes verificadas (F01–F22), 5 no verificadas y adaptaciones a Chile |
| `40D-1_catalogo_borrador.md` | Aviso general, 11 orientaciones (O-01 a O-11) y matriz de trazabilidad |
| `40D-1_reglas_personalizacion.md` | Reglas R-1 a R-8, pseudocódigo y casos de prueba para la 40D-2 |
| `40D-1_informe.md` | Este informe |

## 2. Investigación documental

### 2.1 Método

- **Prioridad:** organismos oficiales (OMS, MINSAL, NHS) y una sociedad científica especializada (The Menopause Society).
- **Lectura directa:** cada fuente se abrió y se leyó, nunca solo el resumen de un buscador.
  - Los PDF de The Menopause Society se descargaron de su sitio.
  - Su texto se extrajo localmente, porque el entorno no tiene lector de PDF.
- **Fecha de consulta:** 2026-11-06, la misma para todas.
- **Fuentes no verificadas:** quedan registradas como tales y **no se citan**.

### 2.2 Resultado

- **22 fuentes verificadas:**
  - OMS (1);
  - NHS (15);
  - The Menopause Society (3);
  - MINSAL (3: \*4141, Salud Responde y SAMU 131).
- **Fuentes clave no verificadas:**
  - **la guía NICE NG23** (el sitio rechazó la lectura automatizada);
  - **las Orientaciones técnicas de climaterio del MINSAL (2014)**: el PDF conocido ya no existe en esa dirección.

  La segunda es una ausencia importante: es la fuente nacional más pertinente.

### 2.3 Hallazgo metodológico: las fuentes no coinciden en las medidas para los bochornos

- **NHS (F03):** sugiere ropa liviana, enfriarse, evitar desencadenantes, ejercicio y peso saludable.
- **The Menopause Society (F17):** su revisión de evidencia de 2023 **no recomienda** el enfriamiento, evitar desencadenantes, el ejercicio ni el yoga *como tratamiento de los bochornos*, por evidencia insuficiente o negativa. Sí recomienda:
  - la terapia cognitivo-conductual;
  - la hipnosis clínica;
  - la pérdida de peso.

**Decisión del borrador:** mantener las medidas de comodidad del NHS, pero aclarar en el texto que pueden ayudar a sentirse más cómoda y que no está demostrado que reduzcan los bochornos. Además, destacar las intervenciones con mejor evidencia (TCC e hipnosis). Esta formulación debe revisarla una profesional.

### 2.4 Otras decisiones de redacción

- **Medicamentos:**
  - el catálogo no nombra fármacos, dosis ni tratamientos hormonales concretos;
  - solo dice que existen tratamientos que un profesional puede evaluar (F01, F19);
  - se omitió la indicación de analgésicos de F15;
  - en articulaciones solo se sugiere preguntar antes de tomar un analgésico (F06).
- **Medicamentos y deseo sexual:** si un medicamento podría influir en el deseo sexual, se indica explícitamente no suspenderlo por cuenta propia (C-3).
- **Niveles de atención del NHS:** se tradujeron a vías chilenas: centro de salud, Salud Responde 600 360 7777, SAMU 131 y Línea \*4141. Es una adaptación propia y requiere revisión.
- **Pregunta 2:** la `pregunta_2` del formulario incluye «presión al pecho». Por eso O-02 destaca la emergencia cardíaca (F04, F05), y O-01 y O-07 remiten a ella para no atribuir un dolor de pecho a un bochorno o a la ansiedad.
- **Vida sexual:** el texto de O-09 aclara que solo es relevante si a la participante le preocupa, porque no todas desean o tienen actividad sexual.

## 3. Aviso general

El texto propuesto está al inicio del catálogo y cubre los cinco puntos pedidos:
- su propósito educativo;
- que no es un diagnóstico;
- que no sustituye la atención profesional;
- que conviene consultar si las molestias persisten, son intensas o afectan la vida diaria;
- que algunas señales de alerta requieren atención más pronta.

Se muestra como texto fijo, sin casillas ni ventanas emergentes (C-1, C-8).

## 4. Selección por respuestas (resumen)

El detalle está en `40D-1_reglas_personalizacion.md`.
- **Base:** solo la última ronda **cerrada con resultado DEFINITIVO** (regla única de la 40B-3).
- **No intervienen:**
  - la severidad total;
  - el puntaje total ni el de las dimensiones;
  - la comparación entre rondas.
- **Regla de selección:** la orientación de la pregunta *i* se destaca si la respuesta es 2 o más. Se ordenan por respuesta y se muestran como máximo 3; el resto queda en la biblioteca.
- **Mensaje de apoyo:** con ánimo decaído alto (`pregunta_5` ≥ 3) aparece primero un mensaje de apoyo. Su texto, su umbral y la marca para el profesional dependen de DR-6.
- **Determinismo y trazabilidad:** con las mismas respuestas y la misma versión del catálogo, el resultado es siempre el mismo. Cada orientación dice por qué aparece y la selección registra la versión del catálogo.

## 5. Grupos de caracterización (Fases 36–39)

Revisión **solo de lectura** de los informes existentes. No se recalculó nada.

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| ¿Hay un procedimiento reproducible para asignar nuevas participantes? | **Sí, técnicamente:** la regla B1 es determinista, con 4 pasos y 20 celdas. El segmento A requeriría los artefactos de PCA y K-means y no se recomienda llevarlo a la plataforma | `fase37/37C_complemento_tres_preguntas/definiciones/definicion_B1_B2.json`; nota 20 de la Fase 39 |
| ¿Qué variables requiere? | `trabaja_actualmente`, `tiene_pareja`, `dias_ejercicio_semana` | `definicion_B1_B2.json` |
| ¿Qué limitaciones tiene? | 1) **Datos sintéticos** (529 participantes simuladas), no mujeres reales. 2) Sin grupos naturales: es la segmentación de un continuo (37B y 37C). 3) B1 es una aproximación a A, no una validación independiente: coincide un 84 % fuera de muestra. Su estabilidad es en gran parte estructural, porque tríos de variables al azar dan una estabilidad similar. 4) Usa respuestas que pueden cambiar entre rondas | Memorias e informes de 37B, 37C y su complemento |
| ¿Aportan información educativa distinta de las respuestas individuales? | **No.** Los grupos difieren muy poco en el MRS: ε² del total 0,008 (A) y 0,027 (B1). Entre el 96,8 % y el 98,7 % de la variación queda **dentro** de los grupos. El análisis individual conserva más información que los segmentos | `fase37/37D_caracterizacion/informes/fuentes/10_comparacion_tres_perspectivas.md` |
| ¿Hay evidencia suficiente para usarlos como contexto descriptivo? | **No para las participantes.** Fase 38: una sola regla de la clase más marcada, y frágil. Fase 39: nada supera la nula ni dentro de los estratos ni entre ellos. La nota 20 de la Fase 39 dice que ningún resultado de 37D–39 debe convertirse en regla de orientación | `fase39/.../fuentes/20_nota_logica_tablero.md`; cierres de las Fases 38 y 39 |

**Conclusión:** se mantiene la personalización **solo por respuestas individuales**. Usar los grupos para orientar se documenta como **no recomendado**.

Mostrar la etiqueta B1 como dato descriptivo, solo en la vista profesional, queda como decisión **pendiente** de la Fase 40E. Si se aprueba, no podría activar ni ordenar orientaciones (C-5). Antes de cualquier uso con participantes haría falta repetir el análisis con datos reales y un protocolo sellado.

## 6. Aspectos que requieren revisión humana especializada

El catálogo **no está aprobado clínicamente**. Antes de usarlo con participantes reales, deben revisarse:

1. **Exactitud clínica de cada orientación**, con revisión firmada por una profesional de salud. Prioridad alta: O-02, O-05, O-10 y O-11, que tienen señales de alerta.
2. **Formulación de los bochornos** (§2.3): cómo presentar las medidas de comodidad frente a la evidencia de F17.
3. **Adaptación al sistema de salud chileno:**
   - si «centro de salud» es la vía correcta de consulta no urgente;
   - cuándo corresponde el SAMU 131 frente a un servicio de urgencia (SAPU, SAR u hospital);
   - el uso de Salud Responde para orientación urgente.
4. **Números de contacto vigentes:**
   - \*4141: verificado en una página de 2023; falta saber si funciona desde teléfonos fijos;
   - SAMU 131: verificado solo en noticias de 2018;
   - Salud Responde: el horario viene de una página secundaria.

   Conviene definir quién los revisa y cada cuánto.
5. **Fuente nacional:** conseguir y revisar las Orientaciones técnicas de climaterio del MINSAL (o la versión vigente) y la guía NICE NG23. Luego, ajustar el catálogo si discrepan.
6. **Fuentes con revisión vencida:** F08, F09, F12 y F14 (NHS) tienen su fecha de revisión institucional vencida. Conviene confirmarlas o reemplazarlas.
7. **Lenguaje y comprensión:** probar los textos con mujeres de 40 a 65 años, en particular la lectura sencilla, el tono no alarmista y el tratamiento respetuoso de la sexualidad.
8. **Mensaje de apoyo (DR-6):** su texto, su umbral, la participación de salud mental o del comité de ética, y si el profesional ve una marca.
9. **Umbrales de selección** (R-2 y R-4): son decisiones de diseño, no clínicas, y deben aprobarse.
10. **Traducciones:** todas las citas del NHS y de The Menopause Society se tradujeron en este borrador y deben revisarse.
11. **Productos sin receta** (hidratantes y lubricantes vaginales): confirmar que mencionarlos de forma genérica es aceptable según los criterios del proyecto.

## 7. Limitaciones

- Gran parte del autocuidado proviene del NHS (Reino Unido), porque las fuentes chilenas específicas no se pudieron verificar.
- El borrador no cubre otros síntomas de la menopausia que el MRS no pregunta, como cefalea o cambios en la piel.
- El MRS no pregunta por pensamientos suicidas: el mensaje de apoyo no puede presumirlos.
- Los resultados de las Fases 36–39 provienen de datos sintéticos.

## 8. Pendientes antes de la 40D-2

- La revisión del contenido (§6) y las decisiones marcadas **[decidir]** en las reglas: R-1, R-2 y R-4.
- El formato del archivo versionado del catálogo, que el plan 40A sugiere en YAML con esquema de validación.
- Autorización expresa para iniciar la 40D-2.
