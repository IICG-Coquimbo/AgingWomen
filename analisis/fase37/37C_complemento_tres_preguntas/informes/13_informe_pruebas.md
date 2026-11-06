# Complemento de la Fase 37C: informe de pruebas

**Resultado:** 23 de 23 pruebas superadas y 25 de 25 errores introducidos detectados.

Durante el desarrollo, la prueba 14 falló por un error de la propia prueba: su caso sintético tenía 4 participantes no usadas y la función exige 5. Mientras estuvo así, sus dos controles negativos se contaban como detectados sin mérito. Se corrigió la prueba y se repitió todo; luego se revisó el motivo de detección de cada control.

| Núm. | Prueba | Resultado | Detalle |
|---|---|---|---|
| 1 | Archivos protegidos: manifiestos de 34-35, 36, 37A, 37B y 37C | superada | 3348 archivos iguales a sus manifiestos |
| 2 | Sin carpetas __pycache__ nuevas en fases protegidas | superada | ninguna |
| 3 | Conservación e identificadores: 529 únicos en el mismo orden | superada | 529 en etiquetas, A y las 30 repeticiones |
| 4 | Etiquetas históricas del Modelo A reproducidas exactamente | superada | 150, 76, 132 y 171; K-means y centroides iguales |
| 5 | Las 30 repeticiones de A coinciden con los lotes E3 de la Fase 37C | superada | 30 de 30; E3 entre 0.771 |
| 6 | ARI exploratorio de 0,677: reproducción y procedencia | superada | ARI 0.6768, igual al guardado |
| 7 | B1 y B2 usan solo las tres preguntas autorizadas | superada | celdas y B2 dependen solo del trío |
| 8 | B2 no usa etiquetas de A: permutarlas no lo cambia, y B1 sí depende de ellas | superada | B1 usa A por definición; B2 no recibe etiquetas |
| 9 | Sin fuga: alterar las participantes de evaluación no cambia nada ajustado | superada | A, escalado y B1 iguales |
| 10 | Separación entre entrenamiento y evaluación | superada | 423 y 106; los 30 mapas salen solo del entrenamiento |
| 11 | Reproducibilidad: rehacer la repetición 0 da lo mismo | superada | etiquetas e información idénticas |
| 12 | Alineación correcta y calculada en el entrenamiento | superada | permutación conocida recuperada; evaluación no influye |
| 13 | ARI correcto: frente a la fórmula y sin depender de los nombres; no es un porcentaje | superada | ARI 0.677 y coincidencia 87.0 % |
| 14 | Estabilidad con participantes compartidas | superada | ambas máscaras correctas |
| 15 | R² fuera de muestra: medias del entrenamiento y controles positivo y negativo | superada | equivale a medias; detecta señal y no ruido |
| 16 | ΔR² puede detectar información adicional cuando existe | superada | información inyectada detectada: ΔR² 0.70 |
| 17 | Los bloques reparten las 29 variables de P2 sin solapamiento | superada | 29 variables en 9 bloques |
| 18 | Búsqueda anidada exhaustiva y solo con entrenamiento | superada | trío plantado recuperado; el trío evaluado salió en 30 de 30 |
| 19 | Sin MRS ni datos de origen: ni en lecturas ni en variables | superada | 27 archivos leídos, ninguno prohibido |
| 20 | Sensibilidades de A leídas de la Fase 37C sin recalcular | superada | 8 valores iguales |
| 21 | La conclusión B de la Fase 37C sigue intacta | superada | B. Segmentación operativa condicionada |
| 22 | Imputación: la moda de 529 solo cambia actividad sexual; las celdas no cambian | superada | 30 celdas de esa variable; sin efecto en las tres preguntas |
| 23 | Git y alcance: sin commit, sin push, sin Django, sin escrituras fuera y sin Fase 37D | superada | HEAD 745d689; sin cambios fuera de analisis/ |


## Controles negativos

Cada uno introduce un error en memoria, sin tocar archivos, y exige que falle la prueba indicada.

| Error introducido | Prueba | Detectado |
|---|---|---|
| Un archivo protegido cambia | 1 | Sí |
| Etiquetas desordenadas | 3 | Sí |
| Etiquetas oficiales alteradas | 4 | Sí |
| Lote de A cambiado | 5 | Sí |
| El 0,677 no se reproduce | 6 | Sí |
| Otra variable entra en las celdas | 7 | Sí |
| Una pregunta se ignora | 7 | Sí |
| Variable no autorizada en el trío | 7 | Sí |
| B1 elige la minoría | 8 | Sí |
| Coincidencia en vez de ARI | 13 | Sí |
| Sin alinear | 12 | Sí |
| Alineación ignorada | 12 | Sí |
| Estabilidad con todas las filas | 14 | Sí |
| Fuera de muestra con filas usadas | 14 | Sí |
| R² ajustado también con evaluación | 15 | Sí |
| R² con celdas imputadas | 15 | Sí |
| Bloques con solapamiento | 17 | Sí |
| Lectura de datos de origen | 19 | Sí |
| Lectura de MRS | 19 | Sí |
| Sensibilidad de A recalculada | 20 | Sí |
| La conclusión de 37C cambia | 21 | Sí |
| HEAD cambia (commit) | 23 | Sí |
| Rama publicada (push) | 23 | Sí |
| Cambio en Django | 23 | Sí |
| Escritura fuera de la carpeta | 23 | Sí |


## No cubierto

Los Word se comprobaron por su estructura (`scripts/verificar_informes_complemento.py`), pero no se revisaron como página porque el equipo no tiene LibreOffice. Las figuras sí se revisaron visualmente. Las pruebas históricas de fases anteriores no se reejecutaron; esas fases se verificaron por huellas.
