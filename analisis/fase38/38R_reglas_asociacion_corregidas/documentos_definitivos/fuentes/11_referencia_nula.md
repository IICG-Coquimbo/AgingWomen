> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Método

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: es un análisis **exploratorio** y su utilidad clínica no está demostrada.

- **Permutaciones:** 1.000 de la severidad entre las participantes (semilla 42). Cada una conserva todas las características de cada participante y la frecuencia basal (281 severas), y rompe cualquier relación entre ambas.
- **Búsqueda completa en cada permutación:** las mismas 9.865 combinaciones y los mismos umbrales.
- **Valor p ajustado de cada regla:** la proporción de permutaciones en que **la regla más fuerte de toda la búsqueda** iguala o supera a la regla observada. Es el método de máximo estadístico de Westfall-Young, que corrige por haber buscado entre miles de reglas.
- **Cuándo se supera la nula:** con un p ajustado menor que 0,05.

# Resultados

|  | Observado | Referencia nula: media | Percentil 95 | p |
|---|---|---|---|---|
| Reglas marcadas | 971 | 544 | 811 | 0,013 |
| Mayor \|z\| de la búsqueda | 4,17 | 3,47 | 4,09 | 0,033 |
| Mayor diferencia respecto de la basal | 27,6 pts | 22,2 pts | 26,5 pts | — |



![Figura 3. Referencia nula.](../figuras/f03_referencia_nula.png)


**Lectura:**
- **Exceso global no es significancia individual.** El exceso de reglas marcadas no convierte en significativa a ninguna regla concreta; cada regla se juzga por su p ajustado.
- **En conjunto, hay más reglas que por azar.** Sin relación real aparecen unas 544 reglas marcadas; en los datos hay 971. La diferencia indica una asociación real en la simulación, pero repartida y débil.
- **Ninguna regla puntual sobresale con claridad.** La mayor diferencia observada (27,6 puntos) es parecida a la que el azar produce en el 5 % de las búsquedas (26,5 puntos). Solo una regla supera el umbral, y por poco (p = 0,033).
- **Reglas que aparecen fácilmente bajo la nula:** las 183 reglas marcadas no redundantes de la clase 4, más todas las débiles y las redundantes. Su fuerza está dentro de lo que el azar produce al buscar entre 9.761 reglas.

**Valores p y Benjamini-Hochberg:**
- **p de Fisher:** cada regla tiene uno, pero es ordinario. La regla se descubrió con los mismos datos, así que ese p no confirma nada.
- **Benjamini-Hochberg:** se aplicó a **todas** las reglas evaluadas, no solo a las seleccionadas. Ninguna queda con q < 0,05.
