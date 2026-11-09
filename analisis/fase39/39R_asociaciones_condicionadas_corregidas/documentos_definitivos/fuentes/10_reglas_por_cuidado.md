<!-- apaisada -->

> **Versión correctiva (Fase 39R).** Corrige la Fase 39 histórica, que heredaba de la Fase 38 histórica dos variables que las decisiones de las Fases 35 y 36 excluían del modelado: `prevision` y `usa_medicamentos_diabetes`. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Resumen

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. No hay validación externa y la utilidad clínica no está demostrada. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38 (versión histórica), y la 39R los repitió conociendo además la 38R.

**A. Asociación dentro de cada estrato.** La búsqueda de reglas se hizo dentro de cada estrato, con su basal propia y una referencia nula que permuta la severidad solo dentro del estrato.

| Estrato | n | Basal | Largo | n_A / n_AC mínimos | Reglas | Marcadas | Marcadas bajo la nula: media | p de exceso | Superan la nula del estrato |
|---|---|---|---|---|---|---|---|---|---|
| Cuida a una o más personas | 251 | 56,2 % | 3 | 26 / 13 | 8.878 | 2.169 | 1.494 (p95 1.903) | 0,006 | 0 |
| No cuida | 278 | 50,4 % | 3 | 28 / 14 | 9.190 | 1.302 | 1.390 (p95 1.809) | 0,595 | 0 |


- **Ninguna regla de esta dimensión supera la referencia nula de su estrato.**
- **Marcadas frente a la nula:** la columna «p de exceso» indica si hay más reglas marcadas (≥ 10 puntos sobre la basal) de lo que produce el azar.

**Clases de las reglas:**

| Estrato | asociación débil | redundante | compatible con la nula del estrato |
|---|---|---|---|
| Cuida a una o más personas | 6.709 | 1.738 | 431 |
| No cuida | 7.888 | 965 | 337 |


# Reglas más fuertes de cada estrato

Se muestran las 3 reglas no redundantes con mayor |z| por estrato y consecuente. **No son hallazgos:** todas son compatibles con la referencia nula de su estrato. Se muestran para que se vea qué hay.

| Antecedente | Consecuente | n (con / antecedente) | Confianza (IC 95 %) | Basal del estrato | Lift | Diferencia de riesgo | p ajustado (estrato) | Reaparece | Clase |
|---|---|---|---|---|---|---|---|---|---|
| Frecuencia de ejercicio de bajo impacto: frecuentemente o siempre | no severos | 22 de 31 | 71,0 % (53-84) | 43,8 % | 1,62 | +31,0 pts | 0,870 | 98 % | compatible con la nula del estrato |
| Frecuencia de alcohol: nunca y Panes al día: 1-2 porciones y Pescado a la semana: 1-2 veces por semana | no severos | 22 de 31 | 71,0 % (53-84) | 43,8 % | 1,62 | +31,0 pts | 0,870 | 96 % | compatible con la nula del estrato |
| Días de ejercicio a la semana: 3-4 días | no severos | 19 de 26 | 73,1 % (54-86) | 43,8 % | 1,67 | +32,6 pts | 0,927 | 60 % | compatible con la nula del estrato |
| Días de ejercicio a la semana: 0 días y Frutas al día: 1-2 porciones y Horas sentada al día: 6-7 | severos | 32 de 36 | 88,9 % (75-96) | 56,2 % | 1,58 | +38,2 pts | 0,055 | 100 % | compatible con la nula del estrato |
| Comidas fuera de casa: 1-2 veces por semana y Días de ejercicio a la semana: 0 días y Trabaja actualmente: sí | severos | 34 de 40 | 85,0 % (71-93) | 56,2 % | 1,51 | +34,3 pts | 0,210 | 100 % | compatible con la nula del estrato |
| Frecuencia de ejercicio de bajo impacto: no realiza o nunca y Operada para no tener más hijos: no y Pescado a la semana: nunca | severos | 32 de 38 | 84,2 % (70-93) | 56,2 % | 1,50 | +33,0 pts | 0,355 | 100 % | compatible con la nula del estrato |
| Edad: 45-54 y La falta de tiempo influye en su alimentación: rara vez y Quién prepara las comidas: ella prepara la mayoría | no severos | 23 de 30 | 76,7 % (59-88) | 49,6 % | 1,54 | +30,3 pts | 0,947 | 78 % | compatible con la nula del estrato |
| La falta de tiempo influye en su alimentación: rara vez y Jugos o gaseosas al día: 1-2 porciones y Pescado a la semana: 1-2 veces por semana | no severos | 23 de 30 | 76,7 % (59-88) | 49,6 % | 1,54 | +30,3 pts | 0,947 | 74 % | compatible con la nula del estrato |
| Pescado a la semana: 1-2 veces por semana y Quién prepara las comidas: ella prepara la mayoría y Trabaja actualmente: no | no severos | 33 de 47 | 70,2 % (56-81) | 49,6 % | 1,41 | +24,8 pts | 0,984 | 100 % | compatible con la nula del estrato |
| Distensión abdominal: nunca o casi nunca y Pescado a la semana: 1-2 veces por semana y Trabaja actualmente: sí | severos | 29 de 39 | 74,4 % (59-85) | 50,4 % | 1,48 | +27,9 pts | 0,933 | 100 % | compatible con la nula del estrato |
| Frecuencia de ejercicio aeróbico: no realiza o nunca y Legumbres a la semana: 1-2 veces por semana y Usa medicamentos para la presión: sí | severos | 22 de 28 | 78,6 % (60-90) | 50,4 % | 1,56 | +31,4 pts | 0,946 | 48 % | compatible con la nula del estrato |
| Comidas fuera de casa: 3-4 veces por semana o 5-6 veces por semana y Edad: 45-54 | severos | 27 de 37 | 73,0 % (57-85) | 50,4 % | 1,45 | +26,1 pts | 0,994 | 100 % | compatible con la nula del estrato |


# B. Diferencia de asociación entre estratos

- **Antecedentes comparados:** 1.496 antecedentes comparables de 1 o 2 condiciones, de 3.645 posibles. Son comparables los que tienen al menos 20 participantes con y sin el antecedente en cada estrato.
- **Diferencias marcadas:** 582 tienen un rango de diferencias de riesgo de al menos 0,10 entre estratos. Bajo la referencia nula aparecen 580 en promedio (p de exceso 0,483). **No hay más diferencias marcadas de las que produce el azar.**
- **Ninguna diferencia supera la nula de la dimensión.** El mayor Q observado es 10,6; el percentil 95 del máximo Q bajo la nula es 19,6. El menor p ajustado es 0,757.

**Comparaciones con mayor heterogeneidad** (no redundantes):

| Antecedente | Cuida a una o más personas: severas/n_A (confianza) · DR [IC 95 %] | No cuida: severas/n_A (confianza) · DR [IC 95 %] | Rango DR | Q | p sin ajuste | p ajustado (dimensión) | Clase |
|---|---|---|---|---|---|---|---|
| Días de ejercicio a la semana: 0 días y Edad: 36-44 | 33/46 (72 %) · DR 0,19 [0,03; 0,32] | 12/35 (34 %) · DR −0,18 [−0,33; −0,01] | 0,37 | 10,6 | 0,001 | 0,757 | diferencia compatible con la nula |
| Días de ejercicio a la semana: 0 días y Evacuación intestinal: cada 2 días | 30/37 (81 %) · DR 0,29 [0,13; 0,41] | 14/32 (44 %) · DR −0,07 [−0,24; 0,11] | 0,37 | 9,5 | 0,002 | 0,879 | diferencia compatible con la nula |
| Frecuencia de ejercicio de fuerza: no realiza o nunca y Frecuencia de tabaco: diariamente | 29/36 (81 %) · DR 0,28 [0,12; 0,40] | 14/32 (44 %) · DR −0,07 [−0,24; 0,11] | 0,36 | 9,0 | 0,003 | 0,919 | diferencia compatible con la nula |
| Días de ejercicio a la semana: 0 días y Horas sentada al día: 6-7 | 38/48 (79 %) · DR 0,28 [0,13; 0,40] | 29/59 (49 %) · DR −0,02 [−0,15; 0,13] | 0,30 | 8,9 | 0,003 | 0,929 | diferencia compatible con la nula |
| Tiene pareja: sí y Frecuencia de tabaco: diariamente | 21/25 (84 %) · DR 0,31 [0,11; 0,42] | 13/29 (45 %) · DR −0,06 [−0,24; 0,12] | 0,37 | 8,4 | 0,004 | 0,956 | diferencia compatible con la nula |
| Golosinas a la semana: 3-4 veces por semana y Legumbres a la semana: 1-2 veces por semana | 23/48 (48 %) · DR −0,10 [−0,25; 0,05] | 41/64 (64 %) · DR 0,18 [0,04; 0,30] | 0,28 | 7,0 | 0,008 | 0,995 | diferencia compatible con la nula |
| Comidas fuera de casa: 3-4 veces por semana o 5-6 veces por semana y Pescado a la semana: 1-2 veces por semana | 14/30 (47 %) · DR −0,11 [−0,28; 0,08] | 29/42 (69 %) · DR 0,22 [0,06; 0,35] | 0,33 | 6,9 | 0,009 | 0,996 | diferencia compatible con la nula |
| Días de ejercicio a la semana: 0 días | 94/140 (67 %) · DR 0,25 [0,12; 0,36] | 83/162 (51 %) · DR 0,02 [−0,10; 0,14] | 0,23 | 6,9 | 0,009 | 0,996 | diferencia compatible con la nula |


**Cómo leer la tabla:**
- **DR:** la diferencia de riesgo, es decir, el porcentaje de severas con el antecedente menos el porcentaje sin él, dentro de cada estrato.
- **Rango DR:** cuánto difiere esa asociación entre estratos.
- **Lectura de las primeras filas:** en varias, el antecedente va con más síntomas severos en un estrato y con menos en otro. Pero diferencias de este tamaño aparecen igual al permutar la severidad dentro de los estratos, así que **no hay evidencia de que la asociación cambie según cuidado**.
