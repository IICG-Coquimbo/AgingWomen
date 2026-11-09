> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Método

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: es un análisis **exploratorio** y su utilidad clínica no está demostrada.

- **Submuestras:** 200 del 80 % (423 participantes), sin reemplazo y con semilla 42.
- **Redescubrimiento:** en cada una se buscan de nuevo las reglas, con los mismos ítems y agrupaciones y con umbrales proporcionales: n_A ≥ 43 y n_AC ≥ 22.
- **Sin fuga:** las agrupaciones se fijaron con las 529 y sin el MRS, y no se reajustan.
- **Regla estable:** reaparece marcada en al menos el 70 % de las submuestras y mantiene la dirección en al menos el 95 %.

# Resultados

- **Reglas estables:** 480 de 971 reglas marcadas son estables.
- **La regla de la clase 6:** reaparece marcada en el 88 % de las submuestras y siempre en la misma dirección. Su confianza varía entre 76 % y 85 % (percentiles 2,5 y 97,5) y su lift entre 1,43 y 1,61.
- **Familias:** de 944 familias con reglas marcadas, 513 reaparecen en al menos el 70 % de las submuestras.
- **Recambio en cada submuestra:**
  - En promedio aparecen 1.212 reglas marcadas (entre 731 y 1.706).
  - De ellas, 530 son nuevas: no estaban marcadas en las 529.
  - Desaparecen en promedio 289 de las 971.
  - Las reglas marcadas cambian mucho de una submuestra a otra.


![Figura 4. Estabilidad en 200 submuestras.](../figuras/f04_estabilidad.png)


# Lectura

**La estabilidad no separa la señal del ruido en este diseño.**

- **Reglas compatibles con el azar:** las 183 reglas no redundantes compatibles con la referencia nula reaparecen en promedio en el 75 % de las submuestras, y 111 cumplen el criterio de estabilidad.
- **Motivo:** las submuestras del 80 % comparten la mayor parte de las participantes. Una regla que aparece por azar en las 529 tiende a reaparecer en submuestras que contienen casi los mismos datos.
- **Consecuencia:** la estabilidad es una condición necesaria, no suficiente. **No demuestra validez y menos validez clínica.** El control principal contra las reglas casuales es la referencia nula (informe 11).
