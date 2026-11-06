# Contenido

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa.

Cada participante es una transacción, identificada con su código original y en el orden de la Fase 36. Archivos:

- **Matriz principal:** `preparacion/matriz_transaccional_principal.csv`, una fila por participante y una columna 0/1 por ítem, más los dos consecuentes.
- **Lista de ítems:** `preparacion/transacciones_principal.txt`, la misma información como lista de ítems por participante.
- **Trazabilidad:** `preparacion/trazabilidad_transformaciones.csv`, que indica de qué códigos sale cada ítem, con qué regla y a cuántas participantes alcanza.
- **Sensibilidades:** `preparacion/sensibilidades/matriz_*.csv`, matrices separadas de la principal.

# Resumen por configuración

| Configuración | Participantes | Severas | Basal | Variables | Ítems | Ítems por transacción | Umbral antecedente / conjunto | Pares determinados |
|---|---|---|---|---|---|---|---|---|
| principal | 529 | 281 | 53,1 % | 31 | 94 | 30,9 | 53 / 27 | 0 |
| S1 | 529 | 281 | 53,1 % | 29 | 90 | 27,5 | 53 / 27 | 0 |
| S2a | 529 | 281 | 53,1 % | 31 | 120 | 31,0 | 53 / 27 | 29 |
| S2b | 529 | 281 | 53,1 % | 31 | 64 | 30,9 | 53 / 27 | 0 |
| S5 | 529 | 281 | 53,1 % | 28 | 84 | 27,9 | 53 / 27 | 0 |
| S6 | 529 | 281 | 53,1 % | 28 | 84 | 27,9 | 53 / 27 | 0 |
| S7a | 309 | 178 | 57,6 % | 32 | 98 | 31,8 | 31 / 16 | 3 |
| S7b | 251 | 141 | 56,2 % | 32 | 96 | 31,9 | 26 / 13 | 4 |
| S8a | 267 | 141 | 52,8 % | 31 | 94 | 30,9 | 27 / 14 | 2 |
| S8b | 267 | 141 | 52,8 % | 32 | 97 | 31,9 | 27 / 14 | 2 |


# Verificaciones

- **Participantes:** 529 únicas, con los identificadores de la Fase 36.
- **Consecuente:** `severo_mrs` se recalcula desde los 11 ítems y coincide con la limpieza y con la Fase 35: 281 severas (53,1 %) y 248 no severas (46,9 %).
- **Contradicciones:** ninguna transacción tiene dos estados de la misma variable ni los dos consecuentes.
- **Antecedentes:** ningún ítem del MRS ni de los segmentos.
- **Participantes sin ítem en una variable:** solo por faltantes reales (en la principal, ninguno) o por la regla R3: 29 en quién prepara las comidas y 24 en previsión.
- **Ítems constantes:** en las subpoblaciones se quitan los ítems que todas o ninguna cumplen (por ejemplo, «no cuida» en S7b).
- **Pares determinados:** se excluyen los antecedentes con dos ítems en que uno implica al otro. En la principal no hay ninguno.
