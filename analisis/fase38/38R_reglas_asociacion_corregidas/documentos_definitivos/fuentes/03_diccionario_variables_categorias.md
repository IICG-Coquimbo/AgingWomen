> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Alcance

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: es un análisis **exploratorio** y su utilidad clínica no está demostrada.

El diccionario describe las 29 variables del análisis principal y los 90 ítems que generan. Otras 4 variables solo entran en sensibilidades.

- **Significado de las respuestas:** viene de las definiciones de la Fase 36, del diccionario de la limpieza y del texto de cada pregunta en la encuesta. No se dedujo del nombre de las variables.
- **Detalle por ítem:** `preparacion/diccionario_items.csv`.

# Variables

| Variable | Bloque | Ítems | Ítems resultantes [n] | Uso | Advertencias |
|---|---|---|---|---|---|
| Trabaja actualmente | Contexto | 2 | no [220]; sí [309] | análisis principal | — |
| Tiene pareja | Contexto | 2 | no [173]; sí [356] | análisis principal | — |
| Personas a su cuidado | Contexto | 4 | no cuida [278]; 1 persona [136]; 2 personas [67]; 3 o más personas [48] | análisis principal | — |
| Días de ejercicio a la semana | Actividad física | 4 | 0 días [302]; 1-2 días [148]; 3-4 días [52]; 5-6 días o todos los días [27] | análisis principal | — |
| Frecuencia de ejercicio aeróbico | Actividad física | 3 | no realiza o nunca [424]; rara vez o a veces [59]; frecuentemente o siempre [46] | análisis principal | Redundante con días de ejercicio (excluida en S5) |
| Frecuencia de ejercicio de bajo impacto | Actividad física | 4 | no realiza o nunca [305]; rara vez [79]; a veces [89]; frecuentemente o siempre [56] | análisis principal | Redundante con días de ejercicio (excluida en S5) |
| Frecuencia de ejercicio de fuerza | Actividad física | 3 | no realiza o nunca [448]; rara vez o a veces [43]; frecuentemente o siempre [38] | análisis principal | Redundante con días de ejercicio (excluida en S5) |
| Horas sentada al día | Actividad física | 3 | menos de 6 [185]; 6-7 [189]; 8 o más [155] | análisis principal | — |
| Quién prepara las comidas | Alimentación e hidratación | 3 | ella prepara la mayoría [365]; ella y otras personas [86]; otra persona del hogar [49] | análisis principal | — |
| Carnes a la semana | Alimentación e hidratación | 3 | nunca o 1-2 veces por semana [187]; 3-4 veces por semana [234]; 5-6 veces por semana o diariamente [108] | análisis principal | — |
| La falta de tiempo influye en su alimentación | Alimentación e hidratación | 4 | nunca o casi nunca [59]; rara vez [144]; a veces [224]; frecuentemente o siempre [102] | análisis principal | — |
| Comidas fuera de casa | Alimentación e hidratación | 3 | nunca [157]; 1-2 veces por semana [247]; 3-4 veces por semana o 5-6 veces por semana [125] | análisis principal | — |
| Frutas al día | Alimentación e hidratación | 3 | no consumo [48]; 1-2 porciones [380]; 3-4 porciones o 5-6 porciones [101] | análisis principal | — |
| Golosinas a la semana | Alimentación e hidratación | 4 | nunca [78]; 1-2 veces por semana [222]; 3-4 veces por semana [165]; 5-6 veces por semana o diariamente [64] | análisis principal | — |
| Jugos o gaseosas al día | Alimentación e hidratación | 4 | no consumo [146]; 1-2 porciones [258]; 3-4 porciones [86]; 5-6 porciones [39] | análisis principal | — |
| Lácteos al día | Alimentación e hidratación | 3 | no consumo [78]; 1-2 porciones [351]; 3-4 porciones o 5-6 porciones [100] | análisis principal | — |
| Legumbres a la semana | Alimentación e hidratación | 3 | nunca [43]; 1-2 veces por semana [352]; 3-4 veces por semana [134] | análisis principal | — |
| Panes al día | Alimentación e hidratación | 3 | no consumo [59]; 1-2 porciones [356]; 3-4 porciones o 5-6 porciones [114] | análisis principal | — |
| Pescado a la semana | Alimentación e hidratación | 3 | nunca [164]; 1-2 veces por semana [299]; 3-4 veces por semana [66] | análisis principal | — |
| Platos de verduras al día | Alimentación e hidratación | 2 | no consumo o 1-2 porciones [446]; 3-4 porciones o 5-6 porciones [83] | análisis principal | — |
| Vasos de agua al día | Alimentación e hidratación | 4 | no consumo o 1-2 porciones [134]; 3-4 porciones [205]; 5-6 porciones [124]; 7 o más porciones [66] | análisis principal | — |
| Frecuencia de tabaco | Tabaco y alcohol | 3 | nunca [399]; 1-2 veces por semana a 5-6 veces por semana [48]; diariamente [82] | análisis principal | — |
| Frecuencia de alcohol | Tabaco y alcohol | 3 | nunca [190]; 1-2 veces por semana [268]; 3-4 veces por semana a diariamente [71] | análisis principal | — |
| Edad | Generales y salud | 3 | 36-44 [126]; 45-54 [230]; 55-65 [173] | análisis principal | — |
| Operada para no tener más hijos | Generales y salud | 2 | no [425]; sí [104] | análisis principal | — |
| Usa medicamentos para la presión | Generales y salud | 2 | no [440]; sí [89] | análisis principal | — |
| Tiene actividad sexual | Próximas a síntomas | 2 | no [278]; sí [251] | análisis principal | Próxima a síntomas (excluida en S6) |
| Distensión abdominal | Próximas a síntomas | 4 | nunca o casi nunca [184]; a veces [226]; frecuentemente [92]; siempre [27] | análisis principal | Próxima a síntomas (excluida en S6) |
| Evacuación intestinal | Próximas a síntomas | 4 | más de una vez al día [41]; 1 vez al día [300]; cada 2 días [128]; 3 o más días entre evacuaciones [60] | análisis principal | Próxima a síntomas (excluida en S6) |


# Distribución de categorías originales

Número de participantes en cada categoría antes de agrupar, de las 529. Cada conteo se contrastó con la matriz S2a de la 38R, que conserva las categorías originales. En las dos variables numéricas, el resumen viene del diccionario de la Fase 38 histórica (no cambia al retirar las dos variables excluidas) y sus cortes se contrastaron con S2a.

| Variable | Categorías originales (n) |
|---|---|
| Trabaja actualmente | No (220); Sí (309) |
| Tiene pareja | No (173); Sí (356) |
| Personas a su cuidado | No cuida (278); 1 persona (136); 2 personas (67); 3 o más personas (48) |
| Días de ejercicio a la semana | 0 días (302); 1-2 días (148); 3-4 días (52); 5-6 días (15); Todos los días (12) |
| Frecuencia de ejercicio aeróbico | No lo realiza o Nunca (424); Rara vez (19); A veces (40); Frecuentemente (26); Siempre (20) |
| Frecuencia de ejercicio de bajo impacto | No lo realiza o Nunca (305); Rara vez (79); A veces (89); Frecuentemente (40); Siempre (16) |
| Frecuencia de ejercicio de fuerza | No lo realiza o Nunca (448); Rara vez (13); A veces (30); Frecuentemente (26); Siempre (12) |
| Horas sentada al día | Numérica: mín. 1, mediana 6, máx. 14. Cortes (R5): menos de 6 (185); 6-7 (189); 8 o más (155) |
| Quién prepara las comidas | Ella prepara la mayoría (365); Ella y otras personas (86); Otra persona del hogar (49); Compro comida preparada (22); Otro (7) |
| Carnes a la semana | Nunca (22); 1-2 veces por semana (165); 3-4 veces por semana (234); 5-6 veces por semana (86); Diariamente (22) |
| La falta de tiempo influye en su alimentación | Nunca o casi nunca (59); Rara vez (144); A veces (224); Frecuentemente (86); Siempre (16) |
| Comidas fuera de casa | Nunca (157); 1-2 veces por semana (247); 3-4 veces por semana (106); 5-6 veces por semana (19); Diariamente (0) |
| Frutas al día | No consumo (48); 1-2 porciones (380); 3-4 porciones (78); 5-6 porciones (23); 7 o más porciones (0) |
| Golosinas a la semana | Nunca (78); 1-2 veces por semana (222); 3-4 veces por semana (165); 5-6 veces por semana (40); Diariamente (24) |
| Jugos o gaseosas al día | No consumo (146); 1-2 porciones (258); 3-4 porciones (86); 5-6 porciones (39); 7 o más porciones (0) |
| Lácteos al día | No consumo (78); 1-2 porciones (351); 3-4 porciones (91); 5-6 porciones (9); 7 o más porciones (0) |
| Legumbres a la semana | Nunca (43); 1-2 veces por semana (352); 3-4 veces por semana (134); 5-6 veces por semana (0); Diariamente (0) |
| Panes al día | No consumo (59); 1-2 porciones (356); 3-4 porciones (104); 5-6 porciones (10); 7 o más porciones (0) |
| Pescado a la semana | Nunca (164); 1-2 veces por semana (299); 3-4 veces por semana (66); 5-6 veces por semana (0); Diariamente (0) |
| Platos de verduras al día | No consumo (19); 1-2 porciones (427); 3-4 porciones (63); 5-6 porciones (20); 7 o más porciones (0) |
| Vasos de agua al día | No consumo (24); 1-2 porciones (110); 3-4 porciones (205); 5-6 porciones (124); 7 o más porciones (66) |
| Frecuencia de tabaco | Nunca (399); 1-2 veces por semana (21); 3-4 veces por semana (9); 5-6 veces por semana (18); Diariamente (82) |
| Frecuencia de alcohol | Nunca (190); 1-2 veces por semana (268); 3-4 veces por semana (46); 5-6 veces por semana (14); Diariamente (11) |
| Edad | Numérica: mín. 36, mediana 50, máx. 65. Cortes (R5): 36-44 (126); 45-54 (230); 55-65 (173) |
| Operada para no tener más hijos | No (425); Sí (104) |
| Usa medicamentos para la presión | No (440); Sí (89) |
| Tiene actividad sexual | No (278); Sí (251) |
| Distensión abdominal | Nunca o casi nunca (184); A veces (226); Frecuentemente (92); Siempre (27) |
| Evacuación intestinal | Más de una vez al día (41); 1 vez al día (300); Cada 2 días (128); 3 o más días entre evacuaciones (60) |


# Variables observadas e imputadas

| Variable | Observadas | Imputadas | Deducidas | Heredadas de la pregunta madre | Con ítem en la principal | Con ítem en S1 | Pierden el ítem en S1 |
|---|---|---|---|---|---|---|---|
| Trabaja actualmente | 506 | 22 | 1 | 0 | 529 | 506 | 23 |
| Tiene pareja | 501 | 28 | 0 | 0 | 529 | 501 | 28 |
| Personas a su cuidado | 244 | 7 | 0 | 21 | 529 | 501 | 28 |
| Días de ejercicio a la semana | 493 | 36 | 0 | 0 | 529 | 493 | 36 |
| Frecuencia de ejercicio aeróbico | 98 | 7 | 0 | 29 | 529 | 493 | 36 |
| Frecuencia de ejercicio de bajo impacto | 209 | 15 | 0 | 22 | 529 | 492 | 37 |
| Frecuencia de ejercicio de fuerza | 79 | 2 | 0 | 28 | 529 | 499 | 30 |
| Horas sentada al día | 502 | 27 | 0 | 0 | 529 | 502 | 27 |
| Quién prepara las comidas | 505 | 24 | 0 | 0 | 500 | 476 | 24 |
| Carnes a la semana | 498 | 31 | 0 | 0 | 529 | 498 | 31 |
| La falta de tiempo influye en su alimentación | 500 | 29 | 0 | 0 | 529 | 500 | 29 |
| Comidas fuera de casa | 495 | 34 | 0 | 0 | 529 | 495 | 34 |
| Frutas al día | 505 | 24 | 0 | 0 | 529 | 505 | 24 |
| Golosinas a la semana | 512 | 17 | 0 | 0 | 529 | 512 | 17 |
| Jugos o gaseosas al día | 499 | 30 | 0 | 0 | 529 | 499 | 30 |
| Lácteos al día | 500 | 29 | 0 | 0 | 529 | 500 | 29 |
| Legumbres a la semana | 505 | 24 | 0 | 0 | 529 | 505 | 24 |
| Panes al día | 499 | 30 | 0 | 0 | 529 | 499 | 30 |
| Pescado a la semana | 510 | 19 | 0 | 0 | 529 | 510 | 19 |
| Platos de verduras al día | 496 | 33 | 0 | 0 | 529 | 496 | 33 |
| Vasos de agua al día | 505 | 24 | 0 | 0 | 529 | 505 | 24 |
| Frecuencia de tabaco | 512 | 17 | 0 | 0 | 529 | 512 | 17 |
| Frecuencia de alcohol | 500 | 29 | 0 | 0 | 529 | 500 | 29 |
| Edad | 529 | 0 | 0 | 0 | 529 | 529 | 0 |
| Operada para no tener más hijos | 511 | 18 | 0 | 0 | 529 | 511 | 18 |
| Usa medicamentos para la presión | 499 | 30 | 0 | 0 | 529 | 499 | 30 |
| Tiene actividad sexual | 499 | 30 | 0 | 0 | 529 | 499 | 30 |
| Distensión abdominal | 512 | 17 | 0 | 0 | 529 | 512 | 17 |
| Evacuación intestinal | 497 | 32 | 0 | 0 | 529 | 497 | 32 |


**Imputaciones heredadas de preguntas madre:**
- **Preguntas condicionadas:** en cuidado y en las tres frecuencias de ejercicio, observadas e imputadas cuentan solo las celdas con respuesta sustantiva. Por eso no suman 529: «no cuida» y «no lo realiza» conservan su ítem (R6) y no se incluyen.
- **Heredadas:** la celda de la pregunta condicionada existe, pero su pregunta madre (si cuida, si hace ese ejercicio) fue imputada. La lista corresponde a 4 variables.
- **Sensibilidad S1:** quita el ítem cuando la celda es imputada o deducida y también cuando su pregunta madre fue imputada. La última columna coincide en las 29 variables con imputadas + deducidas + heredadas; la generación del documento se detiene si no coincide.
- **Quién prepara las comidas:** observadas e imputadas suman 529, pero solo 500 tienen ítem, porque «compro comida preparada» y «otro» no lo generan (R3).

# Variables reservadas para sensibilidades

No pertenecen al análisis principal. Los ítems se leyeron de las matrices de la 38R; observadas, imputadas y heredadas se contrastaron con esas mismas matrices.

| Variable | Población | Observadas / imputadas / heredadas | Categorías originales (n) | Ítems en la matriz 38R [n] | Motivo de la reserva |
|---|---|---|---|---|---|
| IMC | S8a y S8b: 267 con IMC observado | 267 / 262 / 0 | Numérica: mín. 18,2, mediana 28,5, máx. 45,7 (n = 267) | menos de 25 (63); 25-29,9 (101); 30 o más (103) | Solo 267 valores observados; las 262 imputaciones no se usan. |
| Lugar de trabajo comprensivo | S7a: 287. S7a-309: 309; las 22 añadidas tienen el trabajo imputado y no tienen ítem laboral | 271 / 16 / 22 | Muy en desacuerdo (19); En desacuerdo (53); Neutral (108); De acuerdo (71); Muy de acuerdo (36) | desacuerdo (72); neutral (108); acuerdo (107) | Solo quienes trabajan. La pregunta menciona los síntomas («frente a estos síntomas»): riesgo de circularidad. |
| Estrés del entorno laboral | S7a: 287. S7a-309: 309; las 22 añadidas tienen el trabajo imputado y no tienen ítem laboral | 277 / 10 / 22 | Nada de estrés (24); Estrés leve (67); Estrés moderado (107); Estrés alto (57); Estrés extremo (32) | nada o leve (91); moderado (107); alto o extremo (89) | Solo quienes trabajan. La pregunta menciona los síntomas («que intensifiquen sus síntomas»): riesgo de circularidad. |
| Sobrecarga física o emocional por cuidar | S7b: 239 con sobrecarga observada. S7b-251: 251, incluye las 12 imputadas | 239 / 12 / 21 | Nunca o casi nunca (10); Rara vez (34); A veces (106); Frecuentemente (69); Siempre (32) | nunca o rara vez (44); a veces (94); frecuente o siempre (101) | Solo quienes cuidan. Puede ser consecuencia de los síntomas: riesgo de circularidad. |


# Advertencias metodológicas

- **Frecuencias de ejercicio:** son redundantes con los días de ejercicio; la sensibilidad S5 las quita.
- **Próximas a síntomas:** actividad sexual, distensión abdominal y evacuación intestinal pueden formar parte de la propia experiencia de síntomas; la sensibilidad S6 las quita.
- **Módulos laboral y de cuidado:** solo existen en subpoblaciones y pueden ser circulares, por lo que no entran en la matriz principal.
- **Imputaciones:** la sensibilidad S1 indica cuánto se apoya cada regla en ellas.
- **Conjunto sintético:** nada de este diccionario describe a mujeres reales.

# Condiciones de aplicación

- **«No aplica» en ejercicio y cuidado** («no realiza», «no cuida»): es una respuesta sustantiva y conserva su ítem (R6).
- **Módulo laboral:** solo para quienes trabajan.
- **Sobrecarga:** solo para quienes cuidan.
- **Sin ítem de «no aplica»:** nunca se crea, porque solo repetiría la pregunta de entrada.
- **Faltantes:** un faltante no genera ítem y nunca se confunde con una respuesta negativa (R7).
- **Preguntas que mencionan los síntomas:** lugar de trabajo comprensivo («frente a estos síntomas») y estrés laboral («que intensifiquen sus síntomas»). Por eso quedan fuera del análisis principal.

# Variables excluidas de los antecedentes

| Variable | Motivo |
|---|---|
| prevision | Exclusión definitiva (decisiones de las Fases 35 y 36). No es predictora autorizada: motivo de esta corrección. |
| usa_medicamentos_diabetes | Exclusión definitiva (decisiones de las Fases 35 y 36). No es predictora autorizada: motivo de esta corrección. |
| doble_carga | Exclusión definitiva en toda configuración. |
| Ítems y puntaje del MRS | Definen el consecuente; nunca son antecedentes. |
| Segmentos y etiquetas de agrupamiento | Resultado de fases anteriores; no son antecedentes. |
| Etapa menopáusica | Solo descriptiva. |
