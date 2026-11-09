# Fase 39: informe de pruebas

- **Pruebas:** 22 de 22 superadas.
- **Controles negativos:** 20 de 20 errores introducidos en memoria detectados.
- **Cómo funcionan:** cada prueba recalcula desde el código o desde los datos de origen. Cada control introduce un error, en los datos cargados o reemplazando una función, y exige que alguna prueba que antes pasaba falle.

| N.º | Prueba | Resultado | Detalle |
|---|---|---|---|
| p01 | Exactamente 529 identificadores originales | superada | 529 identificadores únicos; cada dimensión los reparte sin repetir |
| p02 | MRS severo correcto | superada | 281 severas y 248 no severas, recalculadas desde los 11 ítems de la limpieza |
| p03 | Tamaños de estratos, frecuencias basales y umbrales | superada | 17 estratos y grupos: tamaños, severas, basales y umbrales coinciden con el recuento y la fórmula del protocolo |
| p04 | Pertenencia correcta a los estratos | superada | pertenencia recalculada desde las respuestas crudas de la limpieza; discrepancias: {'trabajo': 0, 'pareja': 0, 'ejercicio': 0, 'cuidado': 0} |
| p05 | Codificación idéntica a la Fase 38 | superada | 94 ítems idénticos a la matriz principal de la Fase 38 |
| p06 | Sin ítems del MRS ni etiquetas entre los antecedentes | superada | ningún ítem del MRS, de los segmentos ni de A/B1 en los antecedentes; problemas: [] |
| p07 | Sin reglas contradictorias | superada | 65527 reglas sin dos estados de una misma variable y con un solo consecuente |
| p08 | Sin la variable del estrato ni condiciones constantes | superada | sin la variable del estrato ni ítems constantes dentro del estrato; problemas: [] |
| p09 | Soporte, confianza, lift y diferencias de riesgo | superada | 300 reglas recalculadas desde las matrices de los estratos; error máximo 4.44e-16 |
| p10 | Referencia nula dentro del estrato | superada | primeras 100 permutaciones del estrato «3 días o más» recalculadas: máximo /z/ igual; severas constantes (26) |
| p11 | Comparación entre estratos | superada | diferencias de riesgo, Q, Δ y z recalculados de forma independiente en hasta 150 antecedentes por dimensión; error máximo 3.55e-15; Q = z² con dos estratos |
| p12 | Referencia nula de la comparación | superada | 1.000 permutaciones solo dentro de los estratos, con las severas de cada estrato constantes; máximo Q de las primeras 100 recalculado |
| p13 | Calibración del estadístico de interacción | superada | simulación con asociación común no nula sin interacción: rechazo 0.055 (esperado ≈ 0,05); con interacción: potencia 0.971 |
| p14 | Control de la búsqueda múltiple | superada | p ajustados por máximo Q recalculados para todas las comparaciones; BH sobre todas las filas evaluadas; ajuste conjunto ≥ ajuste por dimensión o estrato |
| p15 | Tratamiento de imputaciones | superada | en S1 ninguna celda imputada o deducida genera ítem (0 casos) y diabetes y previsión quedan fuera |
| p16 | Reproducibilidad | superada | búsqueda y nula del estrato «3 días o más» repetidas desde cero: 43 reglas idénticas |
| p17 | Etiquetas A y B1 intactas | superada | etiquetas A y B1 iguales a los archivos históricos, con las mismas huellas y tamaños (150/76/132/171 y 150/79/126/174) |
| p18 | Fases anteriores sin cambios | superada | 3917 archivos de las Fases 34 a 38 comparados por huella; distintos: 0 |
| p19 | Django sin modificaciones | superada | sin cambios en src/ (0); HEAD 745d689 |
| p20 | Sello del protocolo previo a los resultados | superada | protocolo íntegro (sha 18f15f821635…), sellado antes de todos los resultados |
| p21 | Clasificación | superada | clases de reglas y comparaciones recalculadas con las reglas excluyentes del protocolo |
| p22 | Conclusión mecánica | superada | conclusión mecánica recalculada: 0 comparaciones H5, 0 consistentes, 0 reglas de clase 5 con nula conjunta → resultado C |


## Controles negativos

| Error introducido | Detectado | Pruebas que fallan |
|---|---|---|
| Corte del MRS en 15 en vez de 16 | sí | p02 |
| Identificador duplicado | sí | p01, p02, p04, p17 |
| Participante asignada al estrato equivocado | sí | p03, p04 |
| Umbral menor que el del protocolo | sí | p03 |
| Variable del estrato como antecedente | sí | p08, p14 |
| Ítem del MRS como antecedente | sí | p06, p07, p08, p14 |
| Regla contradictoria | sí | p07, p14 |
| Ítem constante no quitado | sí | p08, p10 |
| Confianza mal calculada | sí | p09 |
| Nula que permuta entre estratos | sí | p12 |
| Q sin ponderar | sí | p11, p14 |
| Signo de Δ invertido | sí | p11 |
| Varianza de la interacción subestimada | sí | p12, p13 |
| Ajuste aplicado solo a la regla seleccionada | sí | p14 |
| Imputados conservados en S1 | sí | p15 |
| Semilla distinta (no reproducible) | sí | p10, p12, p16 |
| Etiqueta A alterada | sí | p03, p17 |
| Archivo histórico modificado | sí | p17, p18 |
| Clase de comparación mal asignada | sí | p21, p22 |
| Conclusión forzada a A | sí | p22 |


## Notas

- **Pruebas lentas:** la 16 (reproducibilidad) y la 18 (manifiestos) se ejecutan en los controles negativos solo cuando corresponden: con la semilla distinta y con el archivo histórico modificado.
- **Primera ejecución:** la prueba 16 falló porque comparaba los p ajustados como texto y el último decimal cambia al releer el CSV. Ahora compara numéricamente (`protocolo/02_modificaciones_posteriores.md`).
