# Fase 38: informe de pruebas

- **Pruebas:** 20 de 20 superadas.
- **Controles negativos:** 18 de 18 errores introducidos en memoria detectados.
- **Cómo funcionan:** cada prueba recalcula desde el código, no solo desde las tablas. Cada control reemplaza una función o un dato por una versión con un error y exige que alguna prueba falle.

| N.º | Prueba | Resultado | Detalle |
|---|---|---|---|
| 1 | 529 participantes únicas e identificadores | superada | 529 únicas, en el orden de la Fase 36 |
| 2 | Correspondencia con las fuentes históricas | superada | ítems coinciden con la limpieza y con la matriz guardada |
| 3 | MRS severo correcto | superada | 281 severas; coincide con los ítems, la limpieza y la Fase 35 |
| 4 | Sin variables MRS ni segmentos entre los antecedentes | superada | ningún ítem del MRS ni de segmentos; 31 variables del protocolo |
| 5 | Sin condiciones contradictorias | superada | ninguna transacción con dos estados de una variable |
| 6 | Categorías originales y agrupadas | superada | todos los ítems ≥ 27; R2 y R3 aplicadas; cada participante tiene ítem salvo faltantes y R3 |
| 7 | Tratamiento de imputaciones (S1) | superada | S1 quita 28 celdas imputadas de pareja; principal las conserva |
| 8 | Módulos parciales (S7) | superada | S7a: 309 que trabajan; S7b: 251 que cuidan; módulos fuera de la principal |
| 9 | Soporte, confianza, lift, leverage | superada | 60 reglas al azar: recuentos, soporte, confianza, lift, leverage, diferencia de riesgo y Wilson correctos |
| 10 | Equivalencia Apriori / FP-Growth / exhaustiva | superada | Apriori = FP-Growth = exhaustiva en la principal y en 2 permutaciones |
| 11 | Evaluador matricial equivalente | superada | evaluador matricial = FP-Growth en 2 permutaciones y en una submuestra |
| 12 | Reproducibilidad | superada | reglas, q y primer lote de la referencia nula se reproducen exactamente |
| 13 | Estabilidad sin fuga de información | superada | las agrupaciones no dependen del consecuente; umbrales de submuestra 43 y 22 (proporcionales) |
| 14 | Referencia nula | superada | permutación conserva 281; p ajustado verificado; una permutación nueva da 322 marcadas (nula: media 650) |
| 15 | Comparaciones múltiples reconocidas | superada | BH sobre las 12201 reglas evaluadas; control de búsqueda por máximo /z/; declarado en el protocolo |
| 16 | Sin reglas triviales | superada | antecedentes de 1-3 variables distintas, sin consecuente; en S2a se excluyen 29 pares determinados |
| 17 | Fases anteriores intactas | superada | 3642 archivos protegidos iguales a sus manifiestos (34 a 37D) |
| 18 | Django, datos y git sin cambios | superada | HEAD 745d689; sin cambios en src/, datos/ ni fuera de analisis/ |
| 19 | Protocolo sellado antes de los resultados | superada | protocolo íntegro; todas las reglas y permutaciones son posteriores al sello |
| 20 | Clasificación y redundancia coherentes | superada | clasificación reproducida; 1 en clase 6, con todos los criterios; redundancia verificada en 80 reglas |


## Controles negativos

| Error introducido | Detectado | Pruebas que fallan | Motivo |
|---|---|---|---|
| Lift calculado con la basal equivocada | sí | 9 | AssertionError: lift |
| Wilson sin corrección | sí | 9 | AssertionError: Wilson distinto de statsmodels |
| R2 desactivada (sin unir categorías escasas) | sí | 6 | AssertionError: ítem con menos de 27: lacteos=5-6_porciones (9) |
| Severidad del MRS como antecedente | sí | construcción | KeyError: 'severidad_mrs' |
| Dos estados de una variable en la transacción | sí | 5 | AssertionError: dos estados de una misma variable |
| Corte de severidad en 15 | sí | 3 | AssertionError: severo_mrs no reproduce MRS total ≥ 16 |
| Identificadores en otro orden | sí | 1, 2 | AssertionError: identificadores u orden distintos de la Fase 36 |
| S1 sin quitar imputados | sí | 7 | AssertionError: S1: las celdas imputadas de pareja conservan ítem |
| S7a sin restringir a quienes trabajan | sí | 8 | AssertionError: S7a no es la población que trabaja |
| FP-Growth pierde un conjunto frecuente | sí | 10 | AssertionError: algoritmos distintos con consecuente permutado |
| Evaluador matricial con recuento desplazado | sí | 11, 12 | AssertionError: evaluador matricial distinto de FP-Growth |
| BH aplicado solo a las reglas seleccionadas | sí | 12, 15 | AssertionError: q no se reproduce |
| Sin excluir pares determinados | sí | 16 | AssertionError: el filtro deja pasar pares determinados |
| Mejora mínima de redundancia en 0 | sí | 20 | AssertionError: la clasificación no se reproduce |
| Reglas compatibles con la nula pasadas a la clase 6 | sí | 20 | AssertionError: la clasificación no se reproduce |
| Agrupación que usa el consecuente (fuga) | sí | 13 | AssertionError:  |
| Consecuente permutado (sin relación real) | sí | 3, 12 | AssertionError: severo_mrs no reproduce MRS total ≥ 16 |
| Pares determinados nunca detectados | sí | 16 | AssertionError: S2a debería tener pares determinados |


## Notas

- **«Severidad del MRS como antecedente»:** se detecta en la construcción. El ítem agregado no corresponde a ninguna variable conocida y la búsqueda se detiene antes de llegar a la prueba 4.
- **Prueba 16:** se reforzó para comprobar el filtro de pares determinados con soporte mínimo 1. En S2a, esos pares solo aparecen con categorías de menos de 27 participantes, que nunca alcanzan el umbral, así que la versión anterior no podía detectar el error.
- **Primera ejecución:** fallaron dos pruebas por errores de las propias pruebas, no del análisis:
  - **Prueba 2:** la limpieza guarda «trabaja» como `True` y `False`, no como `SI` y `NO`.
  - **Prueba 14:** exigía que una permutación nueva quedara entre los percentiles 1 y 99 nulos. Dio 322 reglas marcadas, apenas bajo el percentil 1 (327). Se cambió al rango completo de las 1.000 permutaciones.
