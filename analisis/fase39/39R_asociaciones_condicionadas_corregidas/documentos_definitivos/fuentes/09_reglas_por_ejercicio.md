<!-- apaisada -->

> **Versión correctiva (Fase 39R).** Corrige la Fase 39 histórica, que heredaba de la Fase 38 histórica dos variables que las decisiones de las Fases 35 y 36 excluían del modelado: `prevision` y `usa_medicamentos_diabetes`. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Resumen

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. No hay validación externa y la utilidad clínica no está demostrada. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38 (versión histórica), y la 39R los repitió conociendo además la 38R.

**A. Asociación dentro de cada estrato.** La búsqueda de reglas se hizo dentro de cada estrato, con su basal propia y una referencia nula que permuta la severidad solo dentro del estrato.

| Estrato | n | Basal | Largo | n_A / n_AC mínimos | Reglas | Marcadas | Marcadas bajo la nula: media | p de exceso | Superan la nula del estrato |
|---|---|---|---|---|---|---|---|---|---|
| 0 días de ejercicio | 302 | 58,6 % | 3 | 31 / 16 | 9.030 | 1.574 | 1.168 (p95 1.557) | 0,047 | 0 |
| 1-2 días de ejercicio | 148 | 52,7 % | 2 | 20 / 10 | 1.035 | 167 | 191 (p95 252) | 0,747 | 0 |
| 3 días o más de ejercicio | 79 | 32,9 % | 1 | 20 / 10 | 41 | 7 | 5 (p95 9) | 0,212 | 0 |


- **Ninguna regla de esta dimensión supera la referencia nula de su estrato.**
- **Marcadas frente a la nula:** la columna «p de exceso» indica si hay más reglas marcadas (≥ 10 puntos sobre la basal) de lo que produce el azar.

**Clases de las reglas:**

| Estrato | asociación débil | redundante | compatible con la nula del estrato |
|---|---|---|---|
| 0 días de ejercicio | 7.456 | 1.291 | 283 |
| 1-2 días de ejercicio | 868 | 69 | 98 |
| 3 días o más de ejercicio | 34 | 0 | 7 |


# Reglas más fuertes de cada estrato

Se muestran las 3 reglas no redundantes con mayor |z| por estrato y consecuente. **No son hallazgos:** todas son compatibles con la referencia nula de su estrato. Se muestran para que se vea qué hay.

| Antecedente | Consecuente | n (con / antecedente) | Confianza (IC 95 %) | Basal del estrato | Lift | Diferencia de riesgo | p ajustado (estrato) | Reaparece | Clase |
|---|---|---|---|---|---|---|---|---|---|
| Pescado a la semana: 1-2 veces por semana y Quién prepara las comidas: ella prepara la mayoría y Trabaja actualmente: no | no severos | 34 de 54 | 63,0 % (50-75) | 41,4 % | 1,52 | +26,3 pts | 0,692 | 100 % | compatible con la nula del estrato |
| Carnes a la semana: nunca o 1-2 veces por semana y Tiene pareja: sí y Frecuencia de tabaco: nunca | no severos | 37 de 60 | 61,7 % (49-73) | 41,4 % | 1,49 | +25,3 pts | 0,717 | 100 % | compatible con la nula del estrato |
| Carnes a la semana: nunca o 1-2 veces por semana y Lácteos al día: 1-2 porciones y Frecuencia de tabaco: nunca | no severos | 34 de 55 | 61,8 % (49-73) | 41,4 % | 1,49 | +25,0 pts | 0,847 | 100 % | compatible con la nula del estrato |
| Comidas fuera de casa: 1-2 veces por semana y La falta de tiempo influye en su alimentación: a veces y Trabaja actualmente: sí | severos | 31 de 36 | 86,1 % (71-94) | 58,6 % | 1,47 | +31,2 pts | 0,519 | 94 % | compatible con la nula del estrato |
| Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | severos | 32 de 38 | 84,2 % (70-93) | 58,6 % | 1,44 | +29,3 pts | 0,713 | 100 % | compatible con la nula del estrato |
| Golosinas a la semana: 1-2 veces por semana y Tiene pareja: no | severos | 29 de 34 | 85,3 % (70-94) | 58,6 % | 1,46 | +30,1 pts | 0,745 | 88 % | compatible con la nula del estrato |
| Distensión abdominal: a veces y Trabaja actualmente: no | no severos | 15 de 21 | 71,4 % (50-86) | 47,3 % | 1,51 | +28,1 pts | 0,993 | 78 % | compatible con la nula del estrato |
| Distensión abdominal: a veces y Frecuencia de tabaco: nunca | no severos | 31 de 50 | 62,0 % (48-74) | 47,3 % | 1,31 | +22,2 pts | 0,997 | 92 % | compatible con la nula del estrato |
| Carnes a la semana: 3-4 veces por semana y Distensión abdominal: a veces | no severos | 17 de 25 | 68,0 % (48-83) | 47,3 % | 1,44 | +24,9 pts | 0,998 | 97 % | compatible con la nula del estrato |
| Frecuencia de ejercicio aeróbico: no realiza o nunca y Frecuencia de tabaco: diariamente | severos | 18 de 22 | 81,8 % (61-93) | 52,7 % | 1,55 | +34,2 pts | 0,646 | 88 % | compatible con la nula del estrato |
| Carnes a la semana: nunca o 1-2 veces por semana y Panes al día: 1-2 porciones | severos | 27 de 37 | 73,0 % (57-85) | 52,7 % | 1,38 | +27,0 pts | 0,923 | 100 % | compatible con la nula del estrato |
| Comidas fuera de casa: 3-4 veces por semana o 5-6 veces por semana y Panes al día: 1-2 porciones | severos | 18 de 23 | 78,3 % (58-90) | 52,7 % | 1,48 | +30,3 pts | 0,931 | 94 % | compatible con la nula del estrato |
| Frecuencia de ejercicio aeróbico: no realiza o nunca | no severos | 20 de 24 | 83,3 % (64-93) | 67,1 % | 1,24 | +23,3 pts | 0,643 | 97 % | compatible con la nula del estrato |
| Vasos de agua al día: 3-4 porciones | no severos | 25 de 31 | 80,6 % (64-91) | 67,1 % | 1,20 | +22,3 pts | 0,733 | 91 % | compatible con la nula del estrato |
| Frecuencia de ejercicio de bajo impacto: frecuentemente o siempre | no severos | 28 de 36 | 77,8 % (62-88) | 67,1 % | 1,16 | +19,6 pts | 0,941 | 54 % | compatible con la nula del estrato |
| Frecuencia de ejercicio aeróbico: frecuentemente o siempre | severos | 18 de 38 | 47,4 % (32-63) | 32,9 % | 1,44 | +27,9 pts | 0,427 | 96 % | compatible con la nula del estrato |
| Evacuación intestinal: cada 2 días | severos | 11 de 24 | 45,8 % (28-65) | 32,9 % | 1,39 | +18,6 pts | 0,959 | 73 % | compatible con la nula del estrato |
| Edad: 55-65 | severos | 12 de 27 | 44,4 % (28-63) | 32,9 % | 1,35 | +17,5 pts | 0,967 | 64 % | compatible con la nula del estrato |


# B. Diferencia de asociación entre estratos

- **Antecedentes comparados:** 363 antecedentes comparables de 1 o 2 condiciones, de 3.645 posibles. Son comparables los que tienen al menos 20 participantes con y sin el antecedente en cada estrato.
- **Diferencias marcadas:** 234 tienen un rango de diferencias de riesgo de al menos 0,10 entre estratos. Bajo la referencia nula aparecen 257 en promedio (p de exceso 0,898). **No hay más diferencias marcadas de las que produce el azar.**
- **Ninguna diferencia supera la nula de la dimensión.** El mayor Q observado es 9,4; el percentil 95 del máximo Q bajo la nula es 20,5. El menor p ajustado es 0,905.

**Comparaciones con mayor heterogeneidad** (no redundantes):

| Antecedente | 0 días de ejercicio: severas/n_A (confianza) · DR [IC 95 %] | 1-2 días de ejercicio: severas/n_A (confianza) · DR [IC 95 %] | 3 días o más de ejercicio: severas/n_A (confianza) · DR [IC 95 %] | Rango DR | Q | p sin ajuste | p ajustado (dimensión) | Clase |
|---|---|---|---|---|---|---|---|---|
| Personas a su cuidado: no cuida | 83/162 (51 %) · DR −0,16 [−0,26; −0,05] | 39/71 (55 %) · DR 0,04 [−0,12; 0,20] | 18/45 (40 %) · DR 0,16 [−0,04; 0,35] | 0,32 | 9,4 | 0,009 | 0,905 | diferencia compatible con la nula |
| Frutas al día: 1-2 porciones y Vasos de agua al día: 3-4 porciones | 52/85 (61 %) · DR 0,04 [−0,09; 0,15] | 18/34 (53 %) · DR 0,00 [−0,18; 0,18] | 2/20 (10 %) · DR −0,31 [−0,45; −0,07] | 0,34 | 9,2 | 0,010 | 0,913 | diferencia compatible con la nula |
| Trabaja actualmente: sí y Comidas fuera de casa: 1-2 veces por semana | 56/78 (72 %) · DR 0,18 [0,05; 0,29] | 21/45 (47 %) · DR −0,09 [−0,25; 0,09] | 7/27 (26 %) · DR −0,11 [−0,29; 0,12] | 0,28 | 8,8 | 0,012 | 0,942 | diferencia compatible con la nula |
| Comidas fuera de casa: 1-2 veces por semana y Edad: 45-54 | 33/51 (65 %) · DR 0,07 [−0,08; 0,21] | 15/32 (47 %) · DR −0,07 [−0,26; 0,12] | 3/22 (14 %) · DR −0,27 [−0,42; −0,04] | 0,34 | 7,5 | 0,023 | 0,985 | diferencia compatible con la nula |
| Platos de verduras al día: no consumo o 1-2 porciones y Evacuación intestinal: cada 2 días | 36/58 (62 %) · DR 0,04 [−0,10; 0,17] | 13/30 (43 %) · DR −0,12 [−0,30; 0,08] | 11/20 (55 %) · DR 0,30 [0,05; 0,51] | 0,41 | 6,6 | 0,037 | 0,999 | diferencia compatible con la nula |
| Frecuencia de alcohol: 1-2 veces por semana y Edad: 45-54 | 44/65 (68 %) · DR 0,12 [−0,02; 0,24] | 18/33 (55 %) · DR 0,02 [−0,16; 0,20] | 4/22 (18 %) · DR −0,20 [−0,37; 0,03] | 0,32 | 6,5 | 0,039 | 0,999 | diferencia compatible con la nula |
| Evacuación intestinal: cada 2 días | 44/69 (64 %) · DR 0,07 [−0,07; 0,19] | 14/35 (40 %) · DR −0,17 [−0,34; 0,02] | 11/24 (46 %) · DR 0,19 [−0,04; 0,40] | 0,35 | 6,3 | 0,043 | 1,000 | diferencia compatible con la nula |
| Legumbres a la semana: 1-2 veces por semana y Edad: 45-54 | 53/88 (60 %) · DR 0,02 [−0,10; 0,14] | 21/45 (47 %) · DR −0,09 [−0,25; 0,09] | 3/22 (14 %) · DR −0,27 [−0,42; −0,04] | 0,29 | 6,1 | 0,047 | 1,000 | diferencia compatible con la nula |


**Cómo leer la tabla:**
- **DR:** la diferencia de riesgo, es decir, el porcentaje de severas con el antecedente menos el porcentaje sin él, dentro de cada estrato.
- **Rango DR:** cuánto difiere esa asociación entre estratos.
- **Lectura de las primeras filas:** en varias, el antecedente va con más síntomas severos en un estrato y con menos en otro. Pero diferencias de este tamaño aparecen igual al permutar la severidad dentro de los estratos, así que **no hay evidencia de que la asociación cambie según ejercicio**.
