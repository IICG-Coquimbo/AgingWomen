# Fase 37D: informe de pruebas

- **Pruebas:** 15 de 15 superadas.
- **Controles negativos:** 20 de 20 errores introducidos detectados. Cada control reemplaza una función por una versión con un error y exige que alguna prueba falle.
- **Archivos:** `pruebas/resultados_pruebas.csv` y `pruebas/control_mutaciones.csv`.

## Pruebas

| N.º | Prueba | Resultado | Detalle |
|---|---|---|---|
| 1 | 529 identificadores únicos, alineados en todas las fuentes | superada | 529 en procedencia, Fase 35, limpieza, A y B1 |
| 2 | Etiquetas de A idénticas a las históricas, con sus tamaños | superada | idénticas en 3 fuentes; tamaños (150, 76, 132, 171) |
| 3 | Etiquetas de B1 idénticas a las históricas y a la regla | superada | idénticas a la columna guardada, a la regla y al mapa; tamaños (150, 79, 126, 174) |
| 4 | MRS: ítems, dimensiones, total, severidad y severo correctos | superada | recalculado desde los ítems; coincide con la limpieza y la Fase 35; cortes 4/5, 8/9, 15/16 |
| 5 | Faltantes, no aplica e imputadas tratados según el protocolo | superada | no aplica = 0 en ejercicio y cuidado; módulos solo en su población; IMC solo observado (267); S-OBS quita imputadas, deducida y heredadas |
| 6 | Ninguna lectura del simulador ni escritura fuera de la carpeta | superada | 3405 archivos leídos, ninguno del simulador; 0 escrituras fuera; el gancho bloquea |
| 7 | Prueba estadística apropiada para cada tipo de variable, con valores correctos | superada | Spearman, Mann-Whitney, Kruskal-Wallis y χ² según el tipo; valores iguales a scipy |
| 8 | Control de comparaciones múltiples (Benjamini-Hochberg y Holm) | superada | BH y Holm iguales a statsmodels; F1 a F5 con el número de pruebas del protocolo |
| 9 | Resultados reproducibles | superada | efectos, p e IC bootstrap recalculados iguales a los guardados |
| 10 | Sin selección retrospectiva por MRS | superada | todos los resultados son posteriores al sello; las 36 variables son las del protocolo; ninguna elección guardada |
| 11 | Fases anteriores intactas | superada | 3532 archivos iguales a sus manifiestos; 4 del simulador sin abrir |
| 12 | Django, datos versionados y git sin cambios | superada | HEAD 745d689; sin cambios en src/, datos/ ni fuera de analisis/ |
| 13 | Caracterización de A reproduce los efectos de la Fase 37C | superada | 10 de 10 variables con el mismo η² que la 37C |
| 14 | Agrupaciones de etapa y previsión fijadas en el protocolo | superada | etapa: 5 categorías (22 indeterminadas); previsión: 3 categorías (24 otra o ninguna) |
| 15 | Tamaños efectivos informados y coherentes | superada | n por prueba y por grupo según el protocolo |


## Controles negativos

| Error introducido | Detectado | Pruebas que fallan | Motivo |
|---|---|---|---|
| Etiquetas de A desalineadas (permutadas) | sí | 2, 9 | AssertionError: A distinta del artefacto de la 37C |
| Se filtra una participante | sí | 1, 2, 3, 4, 5, 9 | AssertionError: no son 529 únicos |
| B1 con validación cruzada en lugar de B1 | sí | 3, 9 | AssertionError: B1 distinta de la guardada |
| Regla B1 con corte de 2 días | sí | 3 | AssertionError: B1 no sigue la regla de cuatro pasos |
| MRS total sin el ítem 11 | sí | 4, 9 | AssertionError: total distinto de la suma de 11 ítems |
| Severidad con corte en 15 | sí | 4 | AssertionError: corte en 15 |
| No aplica como faltante en ejercicio | sí | 5 | AssertionError: frecuencia_fuerza: no aplica no es 0 estructural |
| IMC imputado por la media incluido | sí | 5, 9 | AssertionError: IMC con imputados |
| S-OBS sin quitar las heredadas | sí | 5 | AssertionError: S-OBS mal en frecuencia_aerobico |
| Binaria analizada con Spearman | sí | 7, 9 | AssertionError: binaria |
| Bonferroni en lugar de Benjamini-Hochberg | sí | 8 | AssertionError: BH distinto de statsmodels |
| q de F4 corregida con otro método | sí | 8 | AssertionError: individual/F4_items.csv: q mal corregida |
| Bootstrap con otra semilla | sí | 9 | AssertionError: trabaja_actualmente: IC distinto |
| Se lee la verdad del simulador | sí | 6 | AssertionError: lecturas prohibidas: ['datos/sintetico/dataset_usuaria_verdad.csv'] |
| Una variable fuera de F1 | sí | 7, 8, 9, 10 | KeyError: 'edad' |
| Una variable externa agregada después | sí | 10 | AssertionError: variables distintas del protocolo: ['usa_antidepresivos'] |
| Un archivo protegido cambia | sí | 11 | AssertionError: archivos distintos: ['seleccion/artefactos_provisionales/P2_c08_km_k4/etiquetas.csv; seleccion/artefacto |
| Cambio en la plataforma Django | sí | 12 | AssertionError: cambios en la plataforma: [' M src/apps/encuestas/models.py'] |
| Etapa sin agrupar las indeterminadas | sí | 14 | AssertionError: etapa mal agrupada |
| A distinta en la 37B | sí | 2 | AssertionError: A distinta de la 37B |


«Una variable fuera de F1» se detecta primero con un error de clave en la prueba 7, porque la variable quitada se busca ahí. La prueba 10 también la detecta por su propio motivo.
