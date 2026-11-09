> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Contenido

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: es un análisis **exploratorio** y su utilidad clínica no está demostrada.

Cada participante es una transacción, identificada con su código original y en el orden de la Fase 36. Archivos:

- **Matriz principal:** `preparacion/matriz_transaccional_principal.csv`, una fila por participante y una columna 0/1 por ítem, más los dos consecuentes.
- **Lista de ítems:** `preparacion/transacciones_principal.txt`, la misma información como lista de ítems por participante.
- **Trazabilidad:** `preparacion/trazabilidad_transformaciones.csv`, que indica de qué códigos sale cada ítem, con qué regla y a cuántas participantes alcanza.
- **Sensibilidades:** `preparacion/sensibilidades/matriz_*.csv`, matrices separadas de la principal.

# Resumen por configuración

| Configuración | Participantes | Severas | Basal | Variables | Ítems | Ítems por transacción | Umbral antecedente / conjunto | Pares determinados |
|---|---|---|---|---|---|---|---|---|
| principal | 529 | 281 | 53,1 % | 29 | 90 | 28,9 | 53 / 27 | 0 |
| S1 | 529 | 281 | 53,1 % | 29 | 90 | 27,5 | 53 / 27 | 0 |
| S2a | 529 | 281 | 53,1 % | 29 | 113 | 29,0 | 53 / 27 | 8 |
| S2b | 529 | 281 | 53,1 % | 29 | 60 | 28,9 | 53 / 27 | 0 |
| S3-bajo | 529 | 281 | 53,1 % | 29 | 90 | 28,9 | 27 / 14 | 0 |
| S3-alto | 529 | 281 | 53,1 % | 29 | 90 | 28,9 | 80 / 40 | 0 |
| S4-1 | 529 | 281 | 53,1 % | 29 | 90 | 28,9 | 53 / 27 | 0 |
| S4-2 | 529 | 281 | 53,1 % | 29 | 90 | 28,9 | 53 / 27 | 0 |
| S5 | 529 | 281 | 53,1 % | 26 | 80 | 25,9 | 53 / 27 | 0 |
| S6 | 529 | 281 | 53,1 % | 26 | 80 | 25,9 | 53 / 27 | 0 |
| S7a | 287 | 166 | 57,8 % | 30 | 94 | 29,9 | 29 / 15 | 3 |
| S7a-309 | 309 | 178 | 57,6 % | 30 | 94 | 29,8 | 31 / 16 | 1 |
| S7b | 239 | 136 | 56,9 % | 30 | 92 | 29,9 | 24 / 12 | 4 |
| S7b-251 | 251 | 141 | 56,2 % | 30 | 92 | 29,9 | 26 / 13 | 3 |
| S8a | 267 | 141 | 52,8 % | 29 | 90 | 28,9 | 27 / 14 | 2 |
| S8b | 267 | 141 | 52,8 % | 30 | 93 | 29,9 | 27 / 14 | 2 |


# Verificaciones

- **Participantes:** 529 únicas, con los identificadores de la Fase 36.
- **Consecuente:** `severo_mrs` se recalcula desde los 11 ítems y coincide con la limpieza y con la Fase 35: 281 severas (53,1 %) y 248 no severas (46,9 %).
- **Contradicciones:** ninguna transacción tiene dos estados de la misma variable ni los dos consecuentes.
- **Antecedentes:** ningún ítem del MRS ni de los segmentos.
- **Participantes sin ítem en una variable:** solo por faltantes reales (en la principal, ninguno) o por la regla R3: 29 en quién prepara las comidas.
- **Ítems constantes:** en las subpoblaciones se quitan los ítems que todas o ninguna cumplen (por ejemplo, «no cuida» en S7b).
- **Pares determinados:** se excluyen los antecedentes con dos ítems en que uno implica al otro. En la principal no hay ninguno.
