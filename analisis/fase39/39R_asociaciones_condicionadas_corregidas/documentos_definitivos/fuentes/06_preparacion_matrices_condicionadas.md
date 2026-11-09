> **Versión correctiva (Fase 39R).** Corrige la Fase 39 histórica, que heredaba de la Fase 38 histórica dos variables que las decisiones de las Fases 35 y 36 excluían del modelado: `prevision` y `usa_medicamentos_diabetes`. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Contenido

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. No hay validación externa y la utilidad clínica no está demostrada. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38 (versión histórica), y la 39R los repitió conociendo además la 38R.

**Archivos:**
- **Matrices por estrato:** `preparacion/matrices/matriz_<grupo>_<estrato>.csv`, con una fila por participante del estrato, su identificador original, una columna 0/1 por ítem admisible y los dos consecuentes.
- **Pertenencia:** `preparacion/pertenencia_estratos.csv` asigna cada participante a su estrato en cada dimensión y a sus grupos A y B1.
- **Prevalencia por estrato:** `preparacion/items_por_estrato.csv`.
- **Trazabilidad:** `preparacion/trazabilidad_items.csv` indica de qué códigos sale cada ítem.

# Verificaciones

- **Identificadores:** las 529 participantes, sin duplicados: sí.
- **Ítems y matriz:** los mismos 90 ítems y la misma matriz que la Fase 38R: sí.
- **Severidad:** recalculada desde los 11 ítems, con 281 severas y 248 no severas, igual a la Fase 38R: sí.
- **B1:** la etiqueta histórica es igual a la regla de cuatro pasos: sí.

# Ítems por estrato

| Grupo | Estrato | Ítems admisibles | Constantes quitados | Variables excluidas |
|---|---|---|---|---|
| Trabajo | Trabaja | 88 | 0 | trabaja_actualmente |
| Trabajo | No trabaja | 88 | 0 | trabaja_actualmente |
| Pareja | Tiene pareja | 88 | 0 | tiene_pareja |
| Pareja | No tiene pareja | 88 | 0 | tiene_pareja |
| Ejercicio | 0 días de ejercicio | 86 | 0 | dias_ejercicio_semana |
| Ejercicio | 1-2 días de ejercicio | 86 | 0 | dias_ejercicio_semana |
| Ejercicio | 3 días o más de ejercicio | 86 | 0 | dias_ejercicio_semana |
| Cuidado | Cuida a una o más personas | 86 | 0 | cantidad_personas_cuida |
| Cuidado | No cuida | 86 | 0 | cantidad_personas_cuida |
| A | A 0 | 82 | 0 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente |
| A | A 1 | 82 | 0 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente |
| A | A 2 | 82 | 0 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente |
| A | A 3 | 82 | 0 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente |
| B1 | B1 0 | 82 | 0 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente |
| B1 | B1 1 | 82 | 0 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente |
| B1 | B1 2 | 82 | 0 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente |
| B1 | B1 3 | 82 | 0 | dias_ejercicio_semana, tiene_pareja, trabaja_actualmente |


- **Sin reagrupar:** dentro de cada estrato no se reagrupa ninguna categoría. Una categoría con pocos casos en el estrato simplemente no alcanza el umbral.
- **Estados de las celdas:** se conservan los estados observado, imputado, deducido y no aplica. La sensibilidad S1 quita las celdas imputadas y deducidas.
