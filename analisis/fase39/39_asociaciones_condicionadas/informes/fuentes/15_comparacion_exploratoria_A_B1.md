# Alcance

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38.

**Uso:** A (P2_c12_km_k4, K-means sobre PCA sin IMC) y B1 (regla de cuatro pasos sobre trabajo, pareja y ejercicio) se usan **solo como comparación exploratoria secundaria**:
- con sus etiquetas históricas, sin reajustar;
- sin presentarlas como segmentaciones naturales ni clínicamente validadas;
- sin elegir entre ellas.

**Variables excluidas:** dentro de los grupos se excluyen trabajo, pareja y días de ejercicio, porque casi determinan los grupos.

# Tamaños, basales y búsqueda dentro de cada grupo

| Grupo | n | Severas | Basal (IC 95 %) | Largo | Reglas | Marcadas | Nula: media | p de exceso | Superan la nula del grupo |
|---|---|---|---|---|---|---|---|---|---|
| A 0 | 150 | 87 | 58,0 % (50 %-66 %) | 2 | 958 | 138 | 164 | 0,789 | 0 |
| A 1 | 76 | 29 | 38,2 % (28 %-49 %) | 1 | 42 | 5 | 5 | 0,501 | 0 |
| A 2 | 132 | 65 | 49,2 % (41 %-58 %) | 2 | 849 | 194 | 142 | 0,065 | 0 |
| A 3 | 171 | 100 | 58,5 % (51 %-66 %) | 2 | 1.108 | 223 | 195 | 0,217 | 0 |
| B1 0 | 150 | 92 | 61,3 % (53 %-69 %) | 2 | 922 | 146 | 161 | 0,655 | 0 |
| B1 1 | 79 | 26 | 32,9 % (24 %-44 %) | 1 | 40 | 7 | 4 | 0,172 | 0 |
| B1 2 | 126 | 58 | 46,0 % (38 %-55 %) | 2 | 813 | 177 | 135 | 0,110 | 0 |
| B1 3 | 174 | 105 | 60,3 % (53 %-67 %) | 2 | 1.123 | 234 | 208 | 0,238 | 0 |


- **A1 y B1-1 (76 y 79 participantes):** solo admiten antecedentes de una condición y casi no tienen reglas posibles.
- **Ningún grupo** tiene reglas que superen su nula.
- **Ningún grupo** tiene más reglas marcadas que por azar (p ≥ 0,065).

# Composición: A y B1 dependen de trabajo, pareja y ejercicio

| Grupo | Trabaja | Tiene pareja | 0 días | 1-2 días | 3 días o más |
|---|---|---|---|---|---|
| A 0 | 60 % | 9 % | 69 % | 29 % | 2 % |
| A 1 | 58 % | 70 % | 4 % | 8 % | 88 % |
| A 2 | 9 % | 97 % | 68 % | 30 % | 2 % |
| A 3 | 95 % | 95 % | 61 % | 35 % | 4 % |
| B1 0 | 59 % | 0 % | 68 % | 32 % | 0 % |
| B1 1 | 58 % | 71 % | 0 % | 0 % | 100 % |
| B1 2 | 0 % | 100 % | 71 % | 29 % | 0 % |
| B1 3 | 100 % | 100 % | 63 % | 37 % | 0 % |


**Coincidencia entre A y B1:** 463 de 529 participantes (88 %) caen en el grupo correspondiente de ambas.

**Qué son los grupos de B1:**
- **B1-1** son exactamente quienes hacen 3 días o más de ejercicio, igual que el estrato de la dimensión ejercicio.
- **B1-0** son quienes no tienen pareja y hacen menos de 3 días.
- **B1-2** son quienes tienen pareja, no trabajan y hacen menos de 3 días.
- **B1-3** son quienes tienen pareja, trabajan y hacen menos de 3 días.

Por eso, comparar por A o B1 repite en gran parte las comparaciones por trabajo, pareja y ejercicio.

# Comparación entre los 4 grupos

| Clasificación | Comparables | Marcadas | Nula: media | p de exceso | p95 del máximo Q nulo | Superan la nula |
|---|---|---|---|---|---|---|
| A | 294 | 251 | 259 | 0,828 | 22,6 | 0 |
| B1 | 333 | 297 | 292 | 0,342 | 24,0 | 0 |


**Ninguna diferencia de asociación entre los grupos de A o de B1 supera la referencia nula.**

# Qué aporta

- **Basales:** confirma descriptivamente que hay grupos con basales muy distintas. A1 tiene 38 % de severas y B1-1 33 %, frente a 58-61 % en A0, A3, B1-0 y B1-3. Ese contraste es esencialmente el del ejercicio.
- **Asociaciones:** no aporta evidencia de que las asociaciones de los hábitos con la severidad cambien de un grupo a otro.
- **Valor:** como descripción del contexto, no como base de reglas.
