# Alcance

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38.

Hay cuatro dimensiones. Cada una divide a las 529 en estratos que no se superponen. Las dimensiones sí se superponen entre sí: una participante pertenece a un estrato de cada dimensión.

- **A y B1:** se agregan solo como comparación secundaria, con sus etiquetas históricas sin reajustar.
- **Pertenencia:** se recalcula desde los códigos de la Fase 36. La prueba 4 la vuelve a calcular desde las respuestas crudas de la limpieza, sin discrepancias.

| Dimensión | Estrato | Definición | Participantes | Variables excluidas dentro del estrato | Uso |
|---|---|---|---|---|---|
| Trabajo | Trabaja | trabaja_actualmente = 1 | 309 | trabaja_actualmente | principal |
| Trabajo | No trabaja | trabaja_actualmente = 0 | 220 | trabaja_actualmente | principal |
| Pareja | Tiene pareja | tiene_pareja = 1 | 356 | tiene_pareja | principal |
| Pareja | No tiene pareja | tiene_pareja = 0 | 173 | tiene_pareja | principal |
| Ejercicio | 0 días de ejercicio | dias_ejercicio_semana = 1 (0 días) | 302 | dias_ejercicio_semana | principal |
| Ejercicio | 1-2 días de ejercicio | dias_ejercicio_semana = 2 (1-2 días) | 148 | dias_ejercicio_semana | principal |
| Ejercicio | 3 días o más de ejercicio | dias_ejercicio_semana ≥ 3 (3-4, 5-6 o todos los días) | 79 | dias_ejercicio_semana | principal |
| Cuidado | Cuida a una o más personas | cantidad_personas_cuida ≥ 1 | 251 | cantidad_personas_cuida | principal |
| Cuidado | No cuida | cantidad_personas_cuida = 0 | 278 | cantidad_personas_cuida | principal |
| A | A 0 | etiqueta histórica A = 0 | 150 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente | exploratorio secundario |
| A | A 1 | etiqueta histórica A = 1 | 76 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente | exploratorio secundario |
| A | A 2 | etiqueta histórica A = 2 | 132 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente | exploratorio secundario |
| A | A 3 | etiqueta histórica A = 3 | 171 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente | exploratorio secundario |
| B1 | B1 0 | etiqueta histórica B1 = 0 | 150 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente | exploratorio secundario |
| B1 | B1 1 | etiqueta histórica B1 = 1 | 79 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente | exploratorio secundario |
| B1 | B1 2 | etiqueta histórica B1 = 2 | 126 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente | exploratorio secundario |
| B1 | B1 3 | etiqueta histórica B1 = 3 | 174 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente | exploratorio secundario |


# Reglas de construcción

- **Ítems:** son los de la Fase 38 (94 ítems y reglas R1 a R7), con las agrupaciones fijadas con las 529 y sin el MRS. La matriz de las 529 es idéntica a la de la Fase 38 (prueba 5).
- **Ítems quitados en cada estrato:** los de la variable que define la dimensión, y los que todas o ninguna participantes del estrato cumplen.
- **Ejercicio de 3 días o más:** reúne 3-4 días (52), 5-6 días (15) y todos los días (12). La agrupación se fija por el significado de las respuestas, como en B1 y en la sensibilidad S2b de la Fase 38, sin mirar el MRS.
- **Cuidado:** compara a quienes cuidan a una o más personas con quienes no cuidan, sin separar por número de personas. Los grupos de 2 personas (67) y de 3 o más (48) serían demasiado pequeños.
- **Módulos:** el laboral (que menciona los síntomas) y la sobrecarga solo entran en las sensibilidades S7a y S7b, dentro del único estrato donde existen.
- **A y B1:** se excluyen trabajo, pareja y días de ejercicio, porque esas tres preguntas determinan casi por completo los grupos.

# Superposición entre dimensiones

| Dimensión 1 | Estrato | Dimensión 2 | Estrato | Participantes |
|---|---|---|---|---|
| Pareja | Tiene pareja | Trabajo | No trabaja | 151 |
| Pareja | Tiene pareja | Trabajo | Trabaja | 205 |
| Pareja | No tiene pareja | Trabajo | No trabaja | 69 |
| Pareja | No tiene pareja | Trabajo | Trabaja | 104 |
| Ejercicio | 0 días de ejercicio | Trabajo | No trabaja | 130 |
| Ejercicio | 0 días de ejercicio | Trabajo | Trabaja | 172 |
| Ejercicio | 1-2 días de ejercicio | Trabajo | No trabaja | 57 |
| Ejercicio | 1-2 días de ejercicio | Trabajo | Trabaja | 91 |
| Ejercicio | 3 días o más de ejercicio | Trabajo | No trabaja | 33 |
| Ejercicio | 3 días o más de ejercicio | Trabajo | Trabaja | 46 |
| Ejercicio | 0 días de ejercicio | Pareja | Tiene pareja | 200 |
| Ejercicio | 0 días de ejercicio | Pareja | No tiene pareja | 102 |
| Ejercicio | 1-2 días de ejercicio | Pareja | Tiene pareja | 100 |
| Ejercicio | 1-2 días de ejercicio | Pareja | No tiene pareja | 48 |
| Ejercicio | 3 días o más de ejercicio | Pareja | Tiene pareja | 56 |
| Ejercicio | 3 días o más de ejercicio | Pareja | No tiene pareja | 23 |
| Cuidado | Cuida a una o más personas | Trabajo | No trabaja | 104 |
| Cuidado | Cuida a una o más personas | Trabajo | Trabaja | 147 |
| Cuidado | No cuida | Trabajo | No trabaja | 116 |
| Cuidado | No cuida | Trabajo | Trabaja | 162 |
| Cuidado | Cuida a una o más personas | Pareja | Tiene pareja | 171 |
| Cuidado | Cuida a una o más personas | Pareja | No tiene pareja | 80 |
| Cuidado | No cuida | Pareja | Tiene pareja | 185 |
| Cuidado | No cuida | Pareja | No tiene pareja | 93 |
| Cuidado | Cuida a una o más personas | Ejercicio | 0 días de ejercicio | 140 |
| Cuidado | Cuida a una o más personas | Ejercicio | 1-2 días de ejercicio | 77 |
| Cuidado | Cuida a una o más personas | Ejercicio | 3 días o más de ejercicio | 34 |
| Cuidado | No cuida | Ejercicio | 0 días de ejercicio | 162 |
| Cuidado | No cuida | Ejercicio | 1-2 días de ejercicio | 71 |
| Cuidado | No cuida | Ejercicio | 3 días o más de ejercicio | 45 |
