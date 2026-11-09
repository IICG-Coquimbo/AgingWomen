# Conclusión

Con esta comprobación ya se puede decidir, pero **la Fase 37D no se inició** y necesita una instrucción expresa. Antes hace falta elegir la base de la caracterización. Los puntos de abajo son decisiones de la responsable del proyecto.

Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.

# Decisiones pendientes

| Decisión | Opciones | Observación |
|---|---|---|
| 1. Base de la Fase 37D | A: `P2_c12_km_k4`. B: regla de cuatro pasos. C: variables directamente | Recomendación no vinculante: B, con C igual de defendible |
| 2. ¿Hay un uso concreto de los grupos? | Sí: reglas desde grupos o plataforma. No: seguir con variables | Si no lo hay, C es más simple |
| 3. ¿El plan exige PCA + K-means? | Sí: mantener A e informar B como comparación. No: puede usarse B | El plan de la reunión del 16-10 incluía PCA y K-means o aglomerativo; conviene confirmarlo |
| 4. Imputación de `tiene_actividad_sexual` | Mantener la moda de 546 o revisar la limpieza | Solo importa si se mantiene A |


# Qué implica cada camino

| Camino | Qué se haría en la Fase 37D | Riesgo principal |
|---|---|---|
| A | Caracterizar cuatro segmentos con las notas de la Fase 37C | Describir como hallazgo lo que ya entró al modelo |
| B | Caracterizar cuatro segmentos definidos por tres respuestas | Equivale a comparar por trabajo, pareja y ejercicio; no presentar como un descubrimiento |
| C | Describir por variables, sin grupos | Muchas comparaciones; hay que controlarlas de antemano |


# Advertencias para cualquier camino

- Trabajo, pareja, ejercicio y actividades relacionadas no pueden usarse como evidencia externa de grupos construidos con ellas.
- Si la Fase 37D compara síntomas o el MRS entre grupos, será la primera vez que aparezca un criterio externo. Esa comparación no debería usarse para reelegir la segmentación con los mismos datos sin declararlo.
- Todo sigue siendo sintético. Se necesita un conjunto real e independiente para hacer cualquier afirmación sobre mujeres.

# Lo que queda disponible

`asignaciones/etiquetas_alternativas.csv` (A, B1, B2 y B2-C por participante), `definiciones/` (tabla de celdas y centros) y `comparacion_final/` (ventajas, desventajas y recomendación). Todo es provisional.
