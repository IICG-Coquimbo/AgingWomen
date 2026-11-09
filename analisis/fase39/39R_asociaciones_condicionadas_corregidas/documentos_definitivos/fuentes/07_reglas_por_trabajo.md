<!-- apaisada -->

> **Versión correctiva (Fase 39R).** Corrige la Fase 39 histórica, que heredaba de la Fase 38 histórica dos variables que las decisiones de las Fases 35 y 36 excluían del modelado: `prevision` y `usa_medicamentos_diabetes`. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Resumen

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. No hay validación externa y la utilidad clínica no está demostrada. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38 (versión histórica), y la 39R los repitió conociendo además la 38R.

**A. Asociación dentro de cada estrato.** La búsqueda de reglas se hizo dentro de cada estrato, con su basal propia y una referencia nula que permuta la severidad solo dentro del estrato.

| Estrato | n | Basal | Largo | n_A / n_AC mínimos | Reglas | Marcadas | Marcadas bajo la nula: media | p de exceso | Superan la nula del estrato |
|---|---|---|---|---|---|---|---|---|---|
| Trabaja | 309 | 57,6 % | 3 | 31 / 16 | 8.611 | 1.842 | 1.168 (p95 1.531) | 0,006 | 0 |
| No trabaja | 220 | 46,8 % | 2 | 22 / 11 | 1.302 | 243 | 201 (p95 265) | 0,148 | 0 |


- **Ninguna regla de esta dimensión supera la referencia nula de su estrato.**
- **Marcadas frente a la nula:** la columna «p de exceso» indica si hay más reglas marcadas (≥ 10 puntos sobre la basal) de lo que produce el azar.

**Clases de las reglas:**

| Estrato | asociación débil | redundante | compatible con la nula del estrato |
|---|---|---|---|
| Trabaja | 6.769 | 1.503 | 339 |
| No trabaja | 1.059 | 115 | 128 |


# Reglas más fuertes de cada estrato

Se muestran las 3 reglas no redundantes con mayor |z| por estrato y consecuente. **No son hallazgos:** todas son compatibles con la referencia nula de su estrato. Se muestran para que se vea qué hay.

| Antecedente | Consecuente | n (con / antecedente) | Confianza (IC 95 %) | Basal del estrato | Lift | Diferencia de riesgo | p ajustado (estrato) | Reaparece | Clase |
|---|---|---|---|---|---|---|---|---|---|
| Distensión abdominal: a veces y Frutas al día: 3-4 porciones o 5-6 porciones | no severos | 18 de 22 | 81,8 % (61-93) | 53,2 % | 1,54 | +31,8 pts | 0,818 | 54 % | compatible con la nula del estrato |
| Frecuencia de ejercicio aeróbico: rara vez o a veces y Quién prepara las comidas: ella prepara la mayoría | no severos | 19 de 24 | 79,2 % (60-91) | 53,2 % | 1,49 | +29,2 pts | 0,929 | 86 % | compatible con la nula del estrato |
| Pescado a la semana: 1-2 veces por semana y Quién prepara las comidas: ella prepara la mayoría | no severos | 56 de 84 | 66,7 % (56-76) | 53,2 % | 1,25 | +21,8 pts | 0,960 | 96 % | compatible con la nula del estrato |
| Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | severos | 21 de 28 | 75,0 % (57-87) | 46,8 % | 1,60 | +32,3 pts | 0,468 | 100 % | compatible con la nula del estrato |
| Frecuencia de ejercicio aeróbico: no realiza o nunca y Jugos o gaseosas al día: no consumo | severos | 34 de 52 | 65,4 % (52-77) | 46,8 % | 1,40 | +24,3 pts | 0,851 | 100 % | compatible con la nula del estrato |
| Personas a su cuidado: no cuida y Pescado a la semana: nunca | severos | 23 de 33 | 69,7 % (53-83) | 46,8 % | 1,49 | +26,9 pts | 0,863 | 100 % | compatible con la nula del estrato |
| Frecuencia de alcohol: nunca y Usa medicamentos para la presión: no y Tiene pareja: sí | no severos | 42 de 66 | 63,6 % (52-74) | 42,4 % | 1,50 | +27,0 pts | 0,392 | 100 % | compatible con la nula del estrato |
| Frecuencia de alcohol: nunca y Personas a su cuidado: no cuida y Usa medicamentos para la presión: no | no severos | 34 de 53 | 64,2 % (51-76) | 42,4 % | 1,51 | +26,3 pts | 0,756 | 100 % | compatible con la nula del estrato |
| Frecuencia de alcohol: nunca y Usa medicamentos para la presión: no | no severos | 58 de 100 | 58,0 % (48-67) | 42,4 % | 1,37 | +23,1 pts | 0,810 | 100 % | compatible con la nula del estrato |
| Vasos de agua al día: no consumo o 1-2 porciones y Frecuencia de ejercicio de bajo impacto: no realiza o nunca y Usa medicamentos para la presión: no | severos | 32 de 37 | 86,5 % (72-94) | 57,6 % | 1,50 | +32,8 pts | 0,331 | 97 % | compatible con la nula del estrato |
| Frecuencia de ejercicio de bajo impacto: no realiza o nunca y Distensión abdominal: nunca o casi nunca | severos | 46 de 57 | 80,7 % (69-89) | 57,6 % | 1,40 | +28,3 pts | 0,347 | 100 % | compatible con la nula del estrato |
| Comidas fuera de casa: 1-2 veces por semana y Días de ejercicio a la semana: 0 días y La falta de tiempo influye en su alimentación: a veces | severos | 31 de 36 | 86,1 % (71-94) | 57,6 % | 1,49 | +32,3 pts | 0,442 | 99 % | compatible con la nula del estrato |


# B. Diferencia de asociación entre estratos

- **Antecedentes comparados:** 1.348 antecedentes comparables de 1 o 2 condiciones, de 3.815 posibles. Son comparables los que tienen al menos 20 participantes con y sin el antecedente en cada estrato.
- **Diferencias marcadas:** 569 tienen un rango de diferencias de riesgo de al menos 0,10 entre estratos. Bajo la referencia nula aparecen 521 en promedio (p de exceso 0,178). **No hay más diferencias marcadas de las que produce el azar.**
- **Ninguna diferencia supera la nula de la dimensión.** El mayor Q observado es 14,1; el percentil 95 del máximo Q bajo la nula es 19,8. El menor p ajustado es 0,336.

**Comparaciones con mayor heterogeneidad** (no redundantes):

| Antecedente | Trabaja: severas/n_A (confianza) · DR [IC 95 %] | No trabaja: severas/n_A (confianza) · DR [IC 95 %] | Rango DR | Q | p sin ajuste | p ajustado (dimensión) | Clase |
|---|---|---|---|---|---|---|---|
| Días de ejercicio a la semana: 0 días y Distensión abdominal: nunca o casi nunca | 49/63 (78 %) · DR 0,25 [0,12; 0,36] | 16/44 (36 %) · DR −0,13 [−0,28; 0,03] | 0,38 | 14,1 | < 0,001 | 0,336 | diferencia compatible con la nula |
| Tiene pareja: sí y Usa medicamentos para la presión: sí | 29/37 (78 %) · DR 0,24 [0,07; 0,35] | 5/20 (25 %) · DR −0,24 [−0,39; −0,01] | 0,48 | 13,7 | < 0,001 | 0,369 | diferencia compatible con la nula |
| Frutas al día: 1-2 porciones y Distensión abdominal: nunca o casi nunca | 60/84 (71 %) · DR 0,19 [0,07; 0,30] | 21/59 (36 %) · DR −0,15 [−0,29; −0,00] | 0,34 | 13,1 | < 0,001 | 0,436 | diferencia compatible con la nula |
| Personas a su cuidado: no cuida y Pescado a la semana: nunca | 21/46 (46 %) · DR −0,14 [−0,29; 0,01] | 23/33 (70 %) · DR 0,27 [0,08; 0,42] | 0,41 | 11,9 | < 0,001 | 0,576 | diferencia compatible con la nula |
| Pescado a la semana: 1-2 veces por semana y Distensión abdominal: nunca o casi nunca | 49/65 (75 %) · DR 0,23 [0,09; 0,33] | 17/44 (39 %) · DR −0,10 [−0,25; 0,06] | 0,33 | 10,0 | 0,002 | 0,821 | diferencia compatible con la nula |
| Comidas fuera de casa: 1-2 veces por semana y Jugos o gaseosas al día: no consumo | 18/39 (46 %) · DR −0,13 [−0,29; 0,03] | 19/27 (70 %) · DR 0,27 [0,07; 0,42] | 0,40 | 9,7 | 0,002 | 0,851 | diferencia compatible con la nula |
| Frecuencia de tabaco: diariamente y Operada para no tener más hijos: no | 28/34 (82 %) · DR 0,28 [0,11; 0,39] | 12/31 (39 %) · DR −0,09 [−0,26; 0,09] | 0,37 | 9,7 | 0,002 | 0,858 | diferencia compatible con la nula |
| Platos de verduras al día: 3-4 porciones o 5-6 porciones y Operada para no tener más hijos: no | 26/39 (67 %) · DR 0,10 [−0,06; 0,24] | 6/26 (23 %) · DR −0,27 [−0,41; −0,07] | 0,37 | 9,3 | 0,002 | 0,900 | diferencia compatible con la nula |


**Cómo leer la tabla:**
- **DR:** la diferencia de riesgo, es decir, el porcentaje de severas con el antecedente menos el porcentaje sin él, dentro de cada estrato.
- **Rango DR:** cuánto difiere esa asociación entre estratos.
- **Lectura de las primeras filas:** en varias, el antecedente va con más síntomas severos en un estrato y con menos en otro. Pero diferencias de este tamaño aparecen igual al permutar la severidad dentro de los estratos, así que **no hay evidencia de que la asociación cambie según trabajo**.
