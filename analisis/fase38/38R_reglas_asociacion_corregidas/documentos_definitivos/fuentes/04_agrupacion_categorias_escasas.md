> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Regla

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: es un análisis **exploratorio** y su utilidad clínica no está demostrada.

El umbral es el 5 % de las participantes, es decir, 27. Las reglas se fijaron en el protocolo antes de calcular ninguna regla, y usan **solo frecuencias marginales**, sin el MRS:

- **R1. Se conserva:** una categoría con 27 participantes o más queda tal cual.
- **R2. Unión con la vecina:** una categoría ordinal con menos de 27 se une a su vecina adyacente de menor frecuencia. Si las dos vecinas tienen la misma frecuencia, se une hacia el centro de la escala. Se repite hasta que todas tengan al menos 27.
- **R3. Sin ítem:** una categoría nominal con menos de 27 y sin vecina compatible no genera ítem.
- **R5. Numéricas:** se cortan de antemano según su significado (edad, horas sentada e IMC).

Ningún corte se eligió para aumentar el soporte, la confianza ni el lift.

# Categorías originales con menos del 5 %

Son 27 categorías con entre 1 y 26 participantes. El porcentaje se calcula sobre las 529 y cada n se contrastó con la matriz S2a de la 38R. No incluye variables retiradas.

| Variable | Categoría original | n | % | Destino |
|---|---|---|---|---|
| Días de ejercicio a la semana | 5-6 días | 15 | 2,8 % | Días de ejercicio a la semana: 5-6 días o todos los días |
| Días de ejercicio a la semana | Todos los días | 12 | 2,3 % | Días de ejercicio a la semana: 5-6 días o todos los días |
| Frecuencia de ejercicio aeróbico | Rara vez | 19 | 3,6 % | Frecuencia de ejercicio aeróbico: rara vez o a veces |
| Frecuencia de ejercicio aeróbico | Frecuentemente | 26 | 4,9 % | Frecuencia de ejercicio aeróbico: frecuentemente o siempre |
| Frecuencia de ejercicio aeróbico | Siempre | 20 | 3,8 % | Frecuencia de ejercicio aeróbico: frecuentemente o siempre |
| Frecuencia de ejercicio de bajo impacto | Siempre | 16 | 3,0 % | Frecuencia de ejercicio de bajo impacto: frecuentemente o siempre |
| Frecuencia de ejercicio de fuerza | Rara vez | 13 | 2,5 % | Frecuencia de ejercicio de fuerza: rara vez o a veces |
| Frecuencia de ejercicio de fuerza | Frecuentemente | 26 | 4,9 % | Frecuencia de ejercicio de fuerza: frecuentemente o siempre |
| Frecuencia de ejercicio de fuerza | Siempre | 12 | 2,3 % | Frecuencia de ejercicio de fuerza: frecuentemente o siempre |
| Quién prepara las comidas | Compro comida preparada | 22 | 4,2 % | Sin ítem (R3: nominal escasa, sin vecina compatible) |
| Quién prepara las comidas | Otro | 7 | 1,3 % | Sin ítem (R3: nominal escasa, sin vecina compatible) |
| Carnes a la semana | Nunca | 22 | 4,2 % | Carnes a la semana: nunca o 1-2 veces por semana |
| Carnes a la semana | Diariamente | 22 | 4,2 % | Carnes a la semana: 5-6 veces por semana o diariamente |
| La falta de tiempo influye en su alimentación | Siempre | 16 | 3,0 % | La falta de tiempo influye en su alimentación: frecuentemente o siempre |
| Comidas fuera de casa | 5-6 veces por semana | 19 | 3,6 % | Comidas fuera de casa: 3-4 veces por semana o 5-6 veces por semana |
| Frutas al día | 5-6 porciones | 23 | 4,3 % | Frutas al día: 3-4 porciones o 5-6 porciones |
| Golosinas a la semana | Diariamente | 24 | 4,5 % | Golosinas a la semana: 5-6 veces por semana o diariamente |
| Lácteos al día | 5-6 porciones | 9 | 1,7 % | Lácteos al día: 3-4 porciones o 5-6 porciones |
| Panes al día | 5-6 porciones | 10 | 1,9 % | Panes al día: 3-4 porciones o 5-6 porciones |
| Platos de verduras al día | No consumo | 19 | 3,6 % | Platos de verduras al día: no consumo o 1-2 porciones |
| Platos de verduras al día | 5-6 porciones | 20 | 3,8 % | Platos de verduras al día: 3-4 porciones o 5-6 porciones |
| Vasos de agua al día | No consumo | 24 | 4,5 % | Vasos de agua al día: no consumo o 1-2 porciones |
| Frecuencia de tabaco | 1-2 veces por semana | 21 | 4,0 % | Frecuencia de tabaco: 1-2 veces por semana a 5-6 veces por semana |
| Frecuencia de tabaco | 3-4 veces por semana | 9 | 1,7 % | Frecuencia de tabaco: 1-2 veces por semana a 5-6 veces por semana |
| Frecuencia de tabaco | 5-6 veces por semana | 18 | 3,4 % | Frecuencia de tabaco: 1-2 veces por semana a 5-6 veces por semana |
| Frecuencia de alcohol | 5-6 veces por semana | 14 | 2,6 % | Frecuencia de alcohol: 3-4 veces por semana a diariamente |
| Frecuencia de alcohol | Diariamente | 11 | 2,1 % | Frecuencia de alcohol: 3-4 veces por semana a diariamente |


**Categorías con n = 0** (10): están en el formulario, pero ninguna participante las eligió.

| Variable | Categoría original | n | Tratamiento |
|---|---|---|---|
| Comidas fuera de casa | Diariamente | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 5 de «Comidas fuera de casa: 3-4 veces por semana o 5-6 veces por semana» (códigos 3,4,5), sin aportarle casos. |
| Frutas al día | 7 o más porciones | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 5 de «Frutas al día: 3-4 porciones o 5-6 porciones» (códigos 3,4,5), sin aportarle casos. |
| Jugos o gaseosas al día | 7 o más porciones | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 5 de «Jugos o gaseosas al día: 5-6 porciones» (códigos 4,5), sin aportarle casos. |
| Lácteos al día | 7 o más porciones | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 5 de «Lácteos al día: 3-4 porciones o 5-6 porciones» (códigos 3,4,5), sin aportarle casos. |
| Legumbres a la semana | 5-6 veces por semana | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 4 de «Legumbres a la semana: 3-4 veces por semana» (códigos 3,4,5), sin aportarle casos. |
| Legumbres a la semana | Diariamente | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 5 de «Legumbres a la semana: 3-4 veces por semana» (códigos 3,4,5), sin aportarle casos. |
| Panes al día | 7 o más porciones | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 5 de «Panes al día: 3-4 porciones o 5-6 porciones» (códigos 3,4,5), sin aportarle casos. |
| Pescado a la semana | 5-6 veces por semana | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 4 de «Pescado a la semana: 3-4 veces por semana» (códigos 3,4,5), sin aportarle casos. |
| Pescado a la semana | Diariamente | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 5 de «Pescado a la semana: 3-4 veces por semana» (códigos 3,4,5), sin aportarle casos. |
| Platos de verduras al día | 7 o más porciones | 0 | Ninguna participante la eligió y S2a no tiene columna. Figura como código 5 de «Platos de verduras al día: 3-4 porciones o 5-6 porciones» (códigos 3,4,5), sin aportarle casos. |


# Ítems resultantes

| Variable | Ítem | Códigos unidos | Participantes | Regla |
|---|---|---|---|---|
| Días de ejercicio a la semana | Días de ejercicio a la semana: 5-6 días o todos los días | 4,5 | 27 | R2 unión de escasas |
| Frecuencia de ejercicio aeróbico | Frecuencia de ejercicio aeróbico: rara vez o a veces | 1,2 | 59 | R2 unión de escasas |
| Frecuencia de ejercicio aeróbico | Frecuencia de ejercicio aeróbico: frecuentemente o siempre | 3,4 | 46 | R2 unión de escasas |
| Frecuencia de ejercicio de bajo impacto | Frecuencia de ejercicio de bajo impacto: frecuentemente o siempre | 3,4 | 56 | R2 unión de escasas |
| Frecuencia de ejercicio de fuerza | Frecuencia de ejercicio de fuerza: rara vez o a veces | 1,2 | 43 | R2 unión de escasas |
| Frecuencia de ejercicio de fuerza | Frecuencia de ejercicio de fuerza: frecuentemente o siempre | 3,4 | 38 | R2 unión de escasas |
| Carnes a la semana | Carnes a la semana: nunca o 1-2 veces por semana | 1,2 | 187 | R2 unión de escasas |
| Carnes a la semana | Carnes a la semana: 5-6 veces por semana o diariamente | 4,5 | 108 | R2 unión de escasas |
| La falta de tiempo influye en su alimentación | La falta de tiempo influye en su alimentación: frecuentemente o siempre | 4,5 | 102 | R2 unión de escasas |
| Comidas fuera de casa | Comidas fuera de casa: 3-4 veces por semana o 5-6 veces por semana | 3,4,5 | 125 | R2 unión de escasas |
| Frutas al día | Frutas al día: 3-4 porciones o 5-6 porciones | 3,4,5 | 101 | R2 unión de escasas |
| Golosinas a la semana | Golosinas a la semana: 5-6 veces por semana o diariamente | 4,5 | 64 | R2 unión de escasas |
| Jugos o gaseosas al día | Jugos o gaseosas al día: 5-6 porciones | 4,5 | 39 | R2 unión de escasas |
| Lácteos al día | Lácteos al día: 3-4 porciones o 5-6 porciones | 3,4,5 | 100 | R2 unión de escasas |
| Legumbres a la semana | Legumbres a la semana: 3-4 veces por semana | 3,4,5 | 134 | R2 unión de escasas |
| Panes al día | Panes al día: 3-4 porciones o 5-6 porciones | 3,4,5 | 114 | R2 unión de escasas |
| Pescado a la semana | Pescado a la semana: 3-4 veces por semana | 3,4,5 | 66 | R2 unión de escasas |
| Platos de verduras al día | Platos de verduras al día: no consumo o 1-2 porciones | 1,2 | 446 | R2 unión de escasas |
| Platos de verduras al día | Platos de verduras al día: 3-4 porciones o 5-6 porciones | 3,4,5 | 83 | R2 unión de escasas |
| Vasos de agua al día | Vasos de agua al día: no consumo o 1-2 porciones | 1,2 | 134 | R2 unión de escasas |
| Frecuencia de tabaco | Frecuencia de tabaco: 1-2 veces por semana a 5-6 veces por semana | 2,3,4 | 48 | R2 unión de escasas |
| Frecuencia de alcohol | Frecuencia de alcohol: 3-4 veces por semana a diariamente | 3,4,5 | 71 | R2 unión de escasas |
| Quién prepara las comidas | Sin ítem: compro comida preparada | Compro comida preparada (código COMPRO) | 22 | R3 sin ítem (nominal escasa, sin vecina compatible) |
| Quién prepara las comidas | Sin ítem: otro | Otro (código OTRO) | 7 | R3 sin ítem (nominal escasa, sin vecina compatible) |


# Decisiones

- **Quién prepara las comidas:** «compro comida preparada» (22) y «otro» (7) no se mezclan con ninguna otra categoría, porque sus significados son distintos. Esas 29 participantes no tienen ítem en esta variable.
- **Distensión «siempre»:** tiene exactamente 27 (5,1 %), así que se conserva por R1.
- **Días de ejercicio:** «5-6 días» y «todos los días» suman 27, también justo el mínimo.
- **Sensibilidad con categorías originales:** S2a conserva las categorías sin agrupar. Las de menos de 27 no alcanzan el umbral de 53 de ningún antecedente.
