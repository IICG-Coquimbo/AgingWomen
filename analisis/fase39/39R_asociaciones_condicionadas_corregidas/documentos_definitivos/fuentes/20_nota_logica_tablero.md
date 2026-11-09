> **Versión correctiva (Fase 39R).** Corrige la Fase 39 histórica, que heredaba de la Fase 38 histórica dos variables que las decisiones de las Fases 35 y 36 excluían del modelado: `prevision` y `usa_medicamentos_diabetes`. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Alcance

Esta nota resume qué puede y qué no puede trasladarse de estos análisis a la plataforma. **No implementa nada ni modifica Django.**

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. No hay validación externa y la utilidad clínica no está demostrada. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38 (versión histórica), y la 39R los repitió conociendo además la 38R.

**Estado de la plataforma:** lo que esta nota afirma sobre la plataforma se contrastó con la Fase 40B-3 (`src/apps/rondas/resultado_mrs.py`) y con el tablero vigente. Esta corrección documental no modificó Django. La Fase 40 sigue en revisión, así que estas descripciones valen para el estado actual de esa fase.

# Componente 1: asignación reproducible del segmento descriptivo

**Qué permiten los análisis 37 a 39:** si la profesora decide mostrar un segmento, solo como **etiqueta descriptiva del contexto**:
- **Cómo:** B1 es una regla de cuatro pasos sobre tres respuestas de la encuesta (ejercicio de 3 días o más; sin pareja; sin trabajo; con trabajo). Es trazable, determinista y no necesita modelos.
- **Por qué no A:** A requiere los artefactos de PCA y K-means de la Fase 37 y no aporta información adicional (el complemento de la 37C lo mostró). No se recomienda llevarla a producción.

**Qué no permiten:**
- presentar el segmento como un **perfil de riesgo**, ni decirle a una usuaria que «su grupo tiene más síntomas»;
- usar en el tablero las basales por estrato y grupo del informe 05. Vienen de datos sintéticos, son marginales y no ajustadas.

**Estado actual:** el tablero de la participante ya presenta su grupo descriptivo B1 (Fase 40D-H, en revisión), con el aviso de que es exploratorio, no es un diagnóstico ni un indicador de salud y no explica ni predice su resultado MRS. Esto no cambia lo que estos análisis permiten o no permiten.

**Requisitos para esa etiqueta:**
- función pura y probada que reciba las tres respuestas y devuelva la etiqueta;
- versión de la regla guardada junto a la asignación;
- recálculo si la usuaria cambia sus respuestas en otra ronda;
- texto neutro que describa la situación, no la severidad;
- aprobación de la profesora y, más adelante, confirmación con datos reales.

# Componente 2: cálculo y visualización individual del MRS

Esto **no depende** de ninguna asociación, porque es la escala misma. Conviene separar tres cosas distintas:

## Clasificación de severidad utilizada en el análisis estadístico

- **Definición:** el consecuente `severo_mrs` vale «sí» cuando el MRS total es 16 o más, y «no» en caso contrario.
- **Alcance:** es un criterio estadístico de las Fases 38R y 39R sobre datos sintéticos. Esta corrección no lo reinterpreta. No autoriza a afirmar que la plataforma muestre una categoría clínica de severidad.

## Información MRS que presenta actualmente la plataforma

Según la Fase 40B-3, todas las pantallas usan una sola regla de presentación, que depende del estado de la ronda:

| Estado | Cuándo | Qué muestra |
|---|---|---|
| Definitivo | Ronda cerrada, 11 ítems respondidos y sin ceros anteriores sin confirmar | «Puntaje MRS: X de 44» y las dimensiones somática (4 ítems), psicológica (4) y urogenital (3) |
| Provisional | Ronda abierta con los 11 ítems respondidos | «Suma provisional: X de 44 (la ronda no está cerrada)» |
| Parcial | Ronda abierta a la que le faltan ítems | «Suma parcial: X», con las preguntas respondidas y el aviso de que la ronda no está cerrada |
| No verificable | Ronda cerrada con ceros anteriores que nadie confirmó, o cuyo registro de ronda no dice cerrada | «Resultado histórico no verificable», sin ningún número |
| Incompleto | Ronda cerrada a la que le faltan ítems | «Resultado incompleto: N de 11 preguntas respondidas» |
| Sin datos | La ronda no tiene MRS | Ningún texto de resultado |


- **Sin categoría de severidad:** la plataforma no muestra ninguna. Los cortes de `MRS.SEVERIDAD_TOTAL` son los históricos de las Fases 34 a 39 y no están validados para mostrarse en ella (decisión de la Fase 40B-3).
- **Evolución:** el tablero presenta la evolución entre rondas de la misma participante (Fase 40C), sin compararla con promedios sintéticos.

## Aspectos de visualización pendientes de validación clínica

- **Categoría de severidad:** mostrar una categoría a la participante o al profesional, con el corte ≥ 16 o con otros cortes.
- **Textos interpretativos:** cualquier mensaje que indique qué significa clínicamente un puntaje.
- **Requisito:** ninguno de estos elementos debe activarse sin validación clínica y sin la decisión de la profesora.

# Componente 3: selección de orientaciones educativas personalizadas

**Ningún resultado de las Fases 37D, 38R y 39R debe transformarse en una regla de orientación.**

- **Fase 38R:** solo dejó una regla en la clase de asociación relativamente más marcada, y era frágil.
- **Fase 39R:** ninguna regla supera la nula dentro de los estratos, y no hay diferencias de asociación entre estratos.
- **Las asociaciones encontradas son débiles, sintéticas, no causales** y en parte dependen de imputaciones y de variables próximas a los síntomas.

**Recomendación para el futuro motor:**
1. **Criterios explícitos:** un catálogo de orientaciones educativas en que cada entrada tenga una condición de activación clara, basada en respuestas de la encuesta (por ejemplo, «no realiza actividad física» o «consume menos de 2 vasos de agua»), y **no** en asociaciones estadísticas.
2. **Fuentes trazables:** cada orientación cita una fuente sanitaria confiable (guías del Ministerio de Salud de Chile, OMS u otras que la profesora indique), con fecha y versión.
3. **Revisión obligatoria** de la profesora antes de activar cada orientación, y registro de quién la aprobó.
4. **Tono educativo:** no clínico, sin prometer efectos sobre los síntomas, con la indicación de consultar a un profesional de salud ante síntomas severos.
5. **Separación:** el puntaje MRS puede decidir **cuándo** sugerir consultar, según los cortes de la escala aprobados. No debe decidir **qué hábito cambiar** a partir de asociaciones sintéticas.
6. **Trazabilidad técnica:** registrar qué orientación se mostró, por qué regla del catálogo y con qué versión, para poder auditarlo.
7. **Validación futura:** si se obtienen datos reales, repetir las Fases 38R y 39R con un protocolo sellado antes de considerar asociaciones como contexto, nunca como prescripción.

# Resumen

| Resultado del análisis | ¿Puede mostrarse en el tablero? | Condición |
|---|---|---|
| Puntaje MRS total y por dimensión, y su evolución | Sí, según el estado de la ronda (Fase 40B-3) | Escala estándar; sin categoría de severidad hasta su validación clínica |
| Etiqueta descriptiva B1 (trabajo, pareja, ejercicio) | Solo si la profesora lo decide | Texto neutro, sin implicar riesgo; regla versionada |
| Basales por estrato o grupo | No | Datos sintéticos; no individuales |
| Reglas de asociación (Fases 38R y 39R) | No | Débiles o compatibles con el azar; no causales |
| Diferencias entre estratos | No | No hay evidencia de que existan |
| Orientaciones educativas | Sí, desde un catálogo explícito | Criterios de fuentes sanitarias y revisión de la profesora |
