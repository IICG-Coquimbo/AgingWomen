# Alcance

Esta nota prepara la siguiente fase de implementación. **No implementa nada ni modifica Django.**

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38.

**Estado actual de la plataforma** (revisado sin modificarlo):
- **Tablero:** `src/apps/encuestas/tablero.py` muestra a la usuaria sus datos, el historial de rondas y el **puntaje MRS crudo** de cada una.
- **MRS:** el modelo `MRS` ya suma los 11 ítems (`puntaje_total`) y define cortes de severidad (`SEVERIDAD_TOTAL`: hasta 4 sin síntomas o muy leves, hasta 8 leve, hasta 15 moderada, 16 o más severa). El código anota que esos cortes están **pendientes de confirmación de la profesora**.
- **Pendiente:** el «grupo de caracterización» está pendiente del algoritmo del equipo de investigación (decisión del 2026-09-24).
- **Sin motor:** no hay un motor de orientaciones.

# Componente 1: asignación reproducible del segmento descriptivo

**Qué permiten los análisis 37 a 39:** si la profesora decide mostrar un segmento, solo como **etiqueta descriptiva del contexto**:
- **Cómo:** B1 es una regla de cuatro pasos sobre tres respuestas de la encuesta (ejercicio de 3 días o más; sin pareja; sin trabajo; con trabajo). Es trazable, determinista y no necesita modelos.
- **Por qué no A:** A requiere los artefactos de PCA y K-means de la Fase 37 y no aporta información adicional (el complemento de la 37C lo mostró). No se recomienda llevarla a producción.

**Qué no permiten:**
- presentar el segmento como un **perfil de riesgo**, ni decirle a una usuaria que «su grupo tiene más síntomas»;
- usar las basales de la Tabla 5 en el tablero. Vienen de datos sintéticos, son marginales y no ajustadas.

**Requisitos si se implementa:**
- función pura y probada que reciba las tres respuestas y devuelva la etiqueta;
- versión de la regla guardada junto a la asignación;
- recálculo si la usuaria cambia sus respuestas en otra ronda;
- texto neutro que describa la situación, no la severidad;
- aprobación de la profesora y, más adelante, confirmación con datos reales.

# Componente 2: cálculo y visualización individual del MRS

Esto **no depende** de ninguna asociación. Es directamente utilizable, porque es la escala misma.

- **Cálculo:** el puntaje total ya está implementado.
- **Dimensiones:** se pueden agregar la somática (ítems 1-4), la psicológica (5-8) y la urogenital (9-11), con la misma definición que el análisis.
- **Severidad:** mantener los cortes del MRS, cuando la profesora los confirme. El umbral «severo ≥ 16» del análisis coincide con la categoría «Severa» de la plataforma.
- **Visualización:** la evolución entre rondas de la misma usuaria; sin compararla con promedios sintéticos.

# Componente 3: selección de orientaciones educativas personalizadas

**Ningún resultado de las Fases 37D, 38 y 39 debe transformarse en una regla de orientación.**

- **Fase 38:** solo dejó una regla en la clase de asociación relativamente más marcada, y era frágil.
- **Fase 39:** ninguna regla supera la nula dentro de los estratos, y no hay diferencias de asociación entre estratos.
- **Las asociaciones encontradas son débiles, sintéticas, no causales** y en parte dependen de imputaciones y de variables próximas a los síntomas.

**Recomendación para el futuro motor:**
1. **Criterios explícitos:** un catálogo de orientaciones educativas en que cada entrada tenga una condición de activación clara, basada en respuestas de la encuesta (por ejemplo, «no realiza actividad física» o «consume menos de 2 vasos de agua»), y **no** en asociaciones estadísticas.
2. **Fuentes trazables:** cada orientación cita una fuente sanitaria confiable (guías del Ministerio de Salud de Chile, OMS u otras que la profesora indique), con fecha y versión.
3. **Revisión obligatoria** de la profesora antes de activar cada orientación, y registro de quién la aprobó.
4. **Tono educativo:** no clínico, sin prometer efectos sobre los síntomas, con la indicación de consultar a un profesional de salud ante síntomas severos.
5. **Separación:** el puntaje MRS puede decidir **cuándo** sugerir consultar, según los cortes de la escala aprobados. No debe decidir **qué hábito cambiar** a partir de asociaciones sintéticas.
6. **Trazabilidad técnica:** registrar qué orientación se mostró, por qué regla del catálogo y con qué versión, para poder auditarlo.
7. **Validación futura:** si se obtienen datos reales, repetir las Fases 38 y 39 con un protocolo sellado antes de considerar asociaciones como contexto, nunca como prescripción.

# Resumen

| Resultado del análisis | ¿Puede mostrarse en el tablero? | Condición |
|---|---|---|
| Puntaje MRS total y por dimensión, y su evolución | Sí | Escala estándar; cortes de severidad confirmados por la profesora |
| Etiqueta descriptiva B1 (trabajo, pareja, ejercicio) | Solo si la profesora lo decide | Texto neutro, sin implicar riesgo; regla versionada |
| Basales por estrato o grupo | No | Datos sintéticos; no individuales |
| Reglas de asociación (Fases 38 y 39) | No | Débiles o compatibles con el azar; no causales |
| Diferencias entre estratos | No | No hay evidencia de que existan |
| Orientaciones educativas | Sí, desde un catálogo explícito | Criterios de fuentes sanitarias y revisión de la profesora |
