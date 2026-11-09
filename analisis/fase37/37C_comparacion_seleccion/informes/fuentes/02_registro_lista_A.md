# Qué es este registro

La Lista A reúne las configuraciones que la Fase 37B señaló con su regla previa, sin ningún cambio. Se conserva completa en `candidatos/lista_A_completa.csv`, leída de sus originales.

Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.

# Composición

- Configuraciones: **108**.
- Con señal de que un solo eje las domina: 57.
- Con repeticiones inestables según la Fase 37B: 52.
- Evaluadas en estabilidad del procedimiento completo, contando Lista B, referencias y comparaciones: 127.
- En el conjunto priorizado de 50, que recibe referencia nula, descomposición de S-ORD e interpretabilidad: 31 de la Lista A.

| k | K-means | Aglomerativo (Ward) |
|---|---|---|
| 2 | 30 | 27 |
| 3 | 24 | 0 |
| 4 | 12 | 0 |
| 5 | 6 | 1 |
| 6 | 3 | 0 |
| 7 | 1 | 0 |
| 8 | 4 | 0 |


# Qué le ocurrió al recalcular todo

| Nivel | Media ≥ 0,65 | Media ≥ 0,65 y p05 ≥ 0,50 | Media > 0,80 |
|---|---|---|---|
| E0 | 108 | 88 | 58 |
| E1 | 79 | 57 | 31 |
| E2 | 79 | 56 | 30 |
| E3 | 73 | 53 | 30 |


E0 es la evaluación de la Fase 37B, con todo congelado salvo el agrupamiento. E3 reajusta imputación, escalado, reducción y agrupamiento.

# Límite del cribado

14 configuraciones de la Lista A pasan el cribado de estabilidad, asignación, codificación y población, pero no están en el conjunto priorizado: `P1_c08_km_k3`, `P1_c08_km_k4`, `P1_c12_km_k3`, `P1_c16_km_k3`, `P1_c16_km_k4`, `P1_c20_km_k3`, `P2_c08_km_k3`, `P2_c12_km_k3`, `P2_c16_km_k3`, `P2_c16_km_k4`, `P2_c20_km_k3`, `F2_c02_km_k2`, `F2_c12_ward_k2`, `R0P2_cTodas_km_k2`. No recibieron referencia nula, descomposición de S-ORD ni interpretabilidad, tal como fijó el protocolo. Por eso no pudieron ser finalistas. La sección «Familia» del informe de comparación indica cuánto se parecen a las elegibles.

Tabla completa: `seleccion/cribado_lista_A.csv`.
