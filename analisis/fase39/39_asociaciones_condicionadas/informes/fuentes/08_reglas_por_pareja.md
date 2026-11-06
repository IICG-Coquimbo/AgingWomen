# Resumen

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38.

**A. Asociación dentro de cada estrato.** La búsqueda de reglas se hizo dentro de cada estrato, con su basal propia y una referencia nula que permuta la severidad solo dentro del estrato.

| Estrato | n | Basal | Largo | n_A / n_AC mínimos | Reglas | Marcadas | Marcadas bajo la nula: media | p de exceso | Superan la nula del estrato |
|---|---|---|---|---|---|---|---|---|---|
| Tiene pareja | 356 | 50,8 % | 3 | 36 / 18 | 10.985 | 1.922 | 1.150 (p95 1.573) | 0,004 | 0 |
| No tiene pareja | 173 | 57,8 % | 2 | 20 / 10 | 1.254 | 183 | 212 (p95 279) | 0,768 | 0 |


- **Ninguna regla de esta dimensión supera la referencia nula de su estrato.**
- **Marcadas frente a la nula:** la columna «p de exceso» indica si hay más reglas marcadas (≥ 10 puntos sobre la basal) de lo que produce el azar.

**Clases de las reglas:**

| Estrato | asociación débil | redundante | compatible con la nula del estrato |
|---|---|---|---|
| Tiene pareja | 9.063 | 1.626 | 296 |
| No tiene pareja | 1.071 | 85 | 98 |


# Reglas más fuertes de cada estrato

Se muestran las 3 reglas no redundantes con mayor |z| por estrato y consecuente. **No son hallazgos:** todas son compatibles con la referencia nula de su estrato. Se muestran para que se vea qué hay.

| Antecedente | Consecuente | n (con / antecedente) | Confianza (IC 95 %) | Basal del estrato | Lift | Diferencia de riesgo | p ajustado (estrato) | Reaparece | Clase |
|---|---|---|---|---|---|---|---|---|---|
| Golosinas a la semana: 1-2 veces por semana y Operada para no tener más hijos: no y Trabaja actualmente: no | no severos | 37 de 50 | 74,0 % (60-84) | 49,2 % | 1,51 | +28,9 pts | 0,354 | 100 % | compatible con la nula del estrato |
| Distensión abdominal: a veces y Horas sentada al día: menos de 6 y Frecuencia de tabaco: nunca | no severos | 33 de 45 | 73,3 % (59-84) | 49,2 % | 1,49 | +27,7 pts | 0,696 | 100 % | compatible con la nula del estrato |
| Golosinas a la semana: 1-2 veces por semana y Quién prepara las comidas: ella prepara la mayoría y Trabaja actualmente: no | no severos | 33 de 45 | 73,3 % (59-84) | 49,2 % | 1,49 | +27,7 pts | 0,696 | 100 % | compatible con la nula del estrato |
| Frecuencia de ejercicio de bajo impacto: no realiza o nunca y Distensión abdominal: nunca o casi nunca y Trabaja actualmente: sí | severos | 31 de 38 | 81,6 % (67-91) | 50,8 % | 1,60 | +34,4 pts | 0,118 | 82 % | compatible con la nula del estrato |
| Días de ejercicio a la semana: 0 días y Distensión abdominal: nunca o casi nunca y Trabaja actualmente: sí | severos | 33 de 42 | 78,6 % (64-88) | 50,8 % | 1,55 | +31,4 pts | 0,258 | 99 % | compatible con la nula del estrato |
| Distensión abdominal: nunca o casi nunca y Pescado a la semana: 1-2 veces por semana y Trabaja actualmente: sí | severos | 34 de 44 | 77,3 % (63-87) | 50,8 % | 1,52 | +30,2 pts | 0,361 | 100 % | compatible con la nula del estrato |
| Edad: 45-54 y Panes al día: 3-4 porciones o 5-6 porciones | no severos | 15 de 21 | 71,4 % (50-86) | 42,2 % | 1,69 | +33,3 pts | 0,756 | 79 % | compatible con la nula del estrato |
| Frutas al día: 1-2 porciones y Panes al día: 3-4 porciones o 5-6 porciones | no severos | 21 de 32 | 65,6 % (48-80) | 42,2 % | 1,56 | +28,7 pts | 0,765 | 100 % | compatible con la nula del estrato |
| Edad: 45-54 y Pescado a la semana: 1-2 veces por semana | no severos | 27 de 44 | 61,4 % (47-74) | 42,2 % | 1,45 | +25,7 pts | 0,864 | 100 % | compatible con la nula del estrato |
| Días de ejercicio a la semana: 0 días y Golosinas a la semana: 1-2 veces por semana | severos | 29 de 34 | 85,3 % (70-94) | 57,8 % | 1,48 | +34,2 pts | 0,175 | 100 % | compatible con la nula del estrato |
| Frecuencia de ejercicio de bajo impacto: no realiza o nunca y Golosinas a la semana: 1-2 veces por semana | severos | 27 de 33 | 81,8 % (66-91) | 57,8 % | 1,42 | +29,7 pts | 0,632 | 100 % | compatible con la nula del estrato |
| Frecuencia de ejercicio aeróbico: no realiza o nunca y Quién prepara las comidas: ella y otras personas | severos | 19 de 22 | 86,4 % (67-95) | 57,8 % | 1,49 | +32,7 pts | 0,734 | 89 % | compatible con la nula del estrato |


# B. Diferencia de asociación entre estratos

- **Antecedentes comparados:** 1.265 antecedentes comparables de 1 o 2 condiciones, de 4.175 posibles. Son comparables los que tienen al menos 20 participantes con y sin el antecedente en cada estrato.
- **Diferencias marcadas:** 491 tienen un rango de diferencias de riesgo de al menos 0,10 entre estratos. Bajo la referencia nula aparecen 485 en promedio (p de exceso 0,455). **No hay más diferencias marcadas de las que produce el azar.**
- **Ninguna diferencia supera la nula de la dimensión.** El mayor Q observado es 14,8; el percentil 95 del máximo Q bajo la nula es 19,2. El menor p ajustado es 0,235.

**Comparaciones con mayor heterogeneidad** (no redundantes):

| Antecedente | Tiene pareja: severas/n_A (confianza) · DR [IC 95 %] | No tiene pareja: severas/n_A (confianza) · DR [IC 95 %] | Rango DR | Q | p sin ajuste | p ajustado (dimensión) | Clase |
|---|---|---|---|---|---|---|---|
| Frutas al día: 1-2 porciones y Panes al día: 3-4 porciones o 5-6 porciones | 35/54 (65 %) · DR 0,16 [0,02; 0,29] | 11/32 (34 %) · DR −0,29 [−0,45; −0,10] | 0,45 | 14,8 | < 0,001 | 0,235 | diferencia compatible con la nula |
| Frutas al día: 1-2 porciones y Lácteos al día: 3-4 porciones o 5-6 porciones | 20/50 (40 %) · DR −0,13 [−0,26; 0,02] | 21/25 (84 %) · DR 0,31 [0,10; 0,43] | 0,43 | 14,3 | < 0,001 | 0,278 | diferencia compatible con la nula |
| Días de ejercicio a la semana: 0 días y Golosinas a la semana: 1-2 veces por semana | 47/94 (50 %) · DR −0,01 [−0,13; 0,10] | 29/34 (85 %) · DR 0,34 [0,17; 0,46] | 0,35 | 13,4 | < 0,001 | 0,384 | diferencia compatible con la nula |
| Trabaja actualmente: no y Golosinas a la semana: 1-2 veces por semana | 22/67 (33 %) · DR −0,22 [−0,34; −0,09] | 16/21 (76 %) · DR 0,21 [−0,02; 0,36] | 0,43 | 12,6 | < 0,001 | 0,457 | diferencia compatible con la nula |
| Golosinas a la semana: 1-2 veces por semana y Frecuencia de tabaco: nunca | 49/119 (41 %) · DR −0,15 [−0,25; −0,04] | 32/44 (73 %) · DR 0,20 [0,03; 0,34] | 0,35 | 12,5 | < 0,001 | 0,468 | diferencia compatible con la nula |
| Lácteos al día: 3-4 porciones o 5-6 porciones y Tiene actividad sexual: no | 6/23 (26 %) · DR −0,26 [−0,41; −0,05] | 20/28 (71 %) · DR 0,16 [−0,04; 0,32] | 0,43 | 9,9 | 0,002 | 0,803 | diferencia compatible con la nula |
| Pescado a la semana: 1-2 veces por semana y Edad: 45-54 | 52/94 (55 %) · DR 0,06 [−0,06; 0,17] | 17/44 (39 %) · DR −0,26 [−0,41; −0,09] | 0,32 | 9,4 | 0,002 | 0,874 | diferencia compatible con la nula |
| Lácteos al día: 3-4 porciones o 5-6 porciones | 28/67 (42 %) · DR −0,11 [−0,24; 0,02] | 25/33 (76 %) · DR 0,22 [0,04; 0,36] | 0,33 | 9,3 | 0,002 | 0,881 | diferencia compatible con la nula |


**Cómo leer la tabla:**
- **DR:** la diferencia de riesgo, es decir, el porcentaje de severas con el antecedente menos el porcentaje sin él, dentro de cada estrato.
- **Rango DR:** cuánto difiere esa asociación entre estratos.
- **Lectura de las primeras filas:** en varias, el antecedente va con más síntomas severos en un estrato y con menos en otro. Pero diferencias de este tamaño aparecen igual al permutar la severidad dentro de los estratos, así que **no hay evidencia de que la asociación cambie según pareja**.
