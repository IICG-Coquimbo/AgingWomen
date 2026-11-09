# Fase 39R: informe comparativo

Fecha: 2026-11-08. Rama `datos-simulados`, HEAD `573d3a3`. Sin commits ni pushes. Protocolo sellado antes de calcular: `protocolo/01_protocolo_39R.md`, SHA-256 `c17c5bf05cc8f8ce9346a91638a19381399011647571ce15fa722581d2d8bb4e`.

**Resultado final: C, igual que en la Fase 39 histórica.** Retirar las dos variables reduce el número de reglas y comparaciones, pero ninguna regla supera la referencia nula de su estrato y ninguna diferencia entre estratos supera los controles de su dimensión. Dos resultados de sensibilidad cambian de lado del umbral (sección V); no intervienen en la conclusión.

## I. Configuración metodológica

- **Matriz:** 529 participantes (281 severas, 248 no severas), 29 variables, 90 ítems, idéntica a la matriz validada de la 38R.
- **Exclusiones:** `prevision`, `usa_medicamentos_diabetes` y `doble_carga`, ausentes desde la construcción de las transacciones.
- **Dependencias revisadas:** `etapa_a_preparacion.py` recorre los scripts históricos; `preparacion/auditoria_dependencias.csv` da el destino de cada aparición de `N38.PRINCIPAL`, `N38.construir`, `N38.esquema`, `N38.matriz_items`, `N38.cargar`, las matrices de 94 ítems y `base_items`.
- **Código histórico:** `busqueda_39.py`, `heterogeneidad_39.py` y las funciones de estratos y umbrales se importan sin modificar. Solo cambia `base_items` (`scripts/nucleo_39r.py`).
- **Métodos, umbrales y semillas:** sin cambios (protocolo, secciones 2 y 3). FP-Growth; `n_A ≥ max(20, ⌈10 %⌉)`, `n_AC ≥ max(10, ⌈5 %⌉)`; largo 3, 2 o 1 según n; marcada 0,10; mejora 0,05; 1.000 permutaciones; 200 submuestras; semillas históricas.
- **Calibración del estadístico de interacción:** rechazo 0,055 bajo asociación común sin interacción (esperado ≈ 0,05); potencia 0,971.

| Dimensión | Estrato | n | Severas | Largo | n_A mín. | n_AC mín. | Ítems 39 → 39R |
|---|---|---:|---:|---:|---:|---:|---|
| Trabajo | Trabaja | 309 | 178 | 3 | 31 | 16 | 92 → 88 |
| Trabajo | No trabaja | 220 | 103 | 2 | 22 | 11 | 92 → 88 |
| Pareja | Tiene pareja | 356 | 181 | 3 | 36 | 18 | 92 → 88 |
| Pareja | No tiene pareja | 173 | 100 | 2 | 20 | 10 | 92 → 88 |
| Ejercicio | 0 días | 302 | 177 | 3 | 31 | 16 | 90 → 86 |
| Ejercicio | 1-2 días | 148 | 78 | 2 | 20 | 10 | 90 → 86 |
| Ejercicio | 3 días o más | 79 | 26 | 1 | 20 | 10 | 90 → 86 |
| Cuidado | Cuida | 251 | 141 | 3 | 26 | 13 | 90 → 86 |
| Cuidado | No cuida | 278 | 140 | 3 | 28 | 14 | 90 → 86 |

La pertenencia a los estratos y a A/B1 es idéntica a la histórica, y se recalculó desde las respuestas de la limpieza.

**Sensibilidades:** S1, S2a, S3-bajo, S3-alto, S4-1, S4-2, S5, S6, S7a, S7b y S9.

- **S7a:** módulo laboral en el estrato trabaja, 309 participantes; 287 con ítems laborales y 22 sin ellos. No se ejecutó S7a-263.
- **S7b:** sobrecarga en el estrato cuida, 251 participantes, 12 con sobrecarga imputada.

**Modificaciones posteriores al sello de la Fase 39, evaluadas por separado:**

| Punto | Decisión |
|---|---|
| Lectura estricta de S9 | Rige el texto sellado; la estricta se calcula aparte. No hubo diferencia: 0 comparaciones H5 |
| Tabla de significación nominal | Exploratoria, en `exploratorio_posterior_al_sello/`; no interviene en nada |
| Tolerancia numérica de la prueba de reproducibilidad | Adoptada, declarada |
| Leyendas de figuras | No aplica; no se generaron figuras |

## II. Verificación de exclusiones

- **Barreras:** 106/106 controles correctos, 81 de ellos negativos que detienen el proceso.
- **Matrices:** en las 7 configuraciones con matriz propia, la corregida es exactamente la histórica sin los ítems retirados (4 ítems; 7 en S2a; 0 en S1, que ya los excluía).
- **Tablas de modelado verificadas:** 85 de reglas y 35 de comparación, por variable y por antecedente.
- **Barrido de texto:** 195 archivos, 0 apariciones en resultados. Las 40 apariciones están en `preparacion/verificacion_configuraciones.csv`, el registro de lo retirado.
- **Independencia:** una lista histórica alterada no cambia la construcción (prueba p24). El control negativo que reinstala el `base_items` histórico se detecta.

## III. Resultados por estrato

### Totales de los 9 estratos

| Indicador | Fase 39 | Fase 39R |
|---|---:|---:|
| Reglas | 59.672 | 47.912 |
| Hacia severo / no severo | 30.600 / 29.072 | 25.807 / 22.105 |
| Marcadas | 10.739 | 9.085 |
| Marcadas no redundantes | 2.129 | 1.998 |
| Estables | 5.525 | 4.739 |
| Clase 1, débil | 48.933 | 38.827 |
| Clase 2, redundante | 8.610 | 7.087 |
| Clase 3, compatible con la nula | 2.129 | 1.998 |
| Clases 4 y 5 | 0 y 0 | 0 y 0 |
| Superan la nula del estrato | 0 | 0 |
| Superan la nula conjunta | 0 | 0 |
| Menor p ajustado del estrato | 0,0579 | 0,0549 |
| Menor p ajustado conjunto | 0,2807 | 0,2527 |
| Percentil 95 del máximo z, 9 estratos | 4,304 | 4,279 |

### Por estrato (Fase 39 → Fase 39R)

| Estrato | Reglas | Marcadas | No redundantes | Nula media | p exceso | Superan nula |
|---|---|---|---|---|---|---|
| Trabaja | 10.849 → 8.611 | 2.162 → 1.842 | 362 → 339 | 1.421,9 → 1.168,0 | 0,007 → 0,006 | 0 → 0 |
| No trabaja | 1.453 → 1.302 | 264 → 243 | 133 → 128 | 217,7 → 201,3 | 0,142 → 0,148 | 0 → 0 |
| Tiene pareja | 10.985 → 8.709 | 1.922 → 1.617 | 296 → 283 | 1.149,9 → 946,9 | 0,004 → 0,002 | 0 → 0 |
| Sin pareja | 1.254 → 1.116 | 183 → 164 | 98 → 92 | 211,9 → 194,8 | 0,768 → 0,809 | 0 → 0 |
| 0 días | 11.232 → 9.030 | 1.874 → 1.574 | 307 → 283 | 1.399,1 → 1.167,6 | 0,049 → 0,047 | 0 → 0 |
| 1-2 días | 1.167 → 1.035 | 182 → 167 | 100 → 98 | 208,3 → 191,2 | 0,744 → 0,747 | 0 → 0 |
| 3 o más días | 43 → 41 | 7 → 7 | 7 → 7 | 4,9 → 4,9 | 0,212 → 0,212 | 0 → 0 |
| Cuida | 11.161 → 8.878 | 2.553 → 2.169 | 453 → 431 | 1.804,0 → 1.493,7 | 0,013 → 0,006 | 0 → 0 |
| No cuida | 11.528 → 9.190 | 1.592 → 1.302 | 373 → 337 | 1.687,9 → 1.389,6 | 0,590 → 0,595 | 0 → 0 |

Detalle, incluidas todas las clases y referencias nulas: `comparacion_historica/comparacion_por_estrato.csv`. El p del exceso de marcadas es informativo y no interviene en la clasificación.

### Reglas conservadas

- 47.912 conservadas, 0 perdidas, 0 nuevas; 11.760 retiradas por contener una variable excluida.
- 0 diferencias en 29 métricas propias de cada regla, estabilidad incluida.
- 0 reglas cambian de clase.
- p ajustado del estrato: 47.493 iguales, 419 bajan (máximo 0,041), ninguno sube. p ajustado conjunto: 47.871 iguales, 41 bajan (máximo 0,033), ninguno sube. Ocurre porque se busca entre menos reglas.

**La regla más cercana al umbral**, en cuida: `dias_ejercicio=0_dias & frutas=1-2_porciones & horas_sentada=6-7` → severo (n 36, confianza 0,889, z 3,956). Su p ajustado del estrato pasa de 0,0579 a 0,0549 y sigue sin superar el umbral de 0,05. Su p ajustado conjunto es 0,2527.

## IV. Comparaciones entre estratos

| Indicador | Trabajo | Pareja | Ejercicio | Cuidado |
|---|---|---|---|---|
| Comparables | 1.500 → 1.348 | 1.265 → 1.129 | 436 → 363 | 1.672 → 1.496 |
| Retiradas por variable excluida | 152 | 136 | 73 | 176 |
| Marcadas (rango de DR ≥ 0,10) | 620 → 569 | 491 → 435 | 286 → 234 | 637 → 582 |
| Nula media de marcadas | 574,3 → 520,9 | 484,9 → 436,1 | 307,1 → 256,6 | 644,6 → 579,7 |
| p exceso de marcadas | 0,218 → 0,178 | 0,455 → 0,509 | 0,834 → 0,898 | 0,541 → 0,483 |
| H1 sin diferencia apreciable | 880 → 779 | 774 → 694 | 150 → 129 | 1.035 → 914 |
| H2 redundante | 404 → 362 | 342 → 295 | 185 → 158 | 398 → 356 |
| H3 compatible con la nula | 216 → 207 | 149 → 140 | 101 → 76 | 239 → 226 |
| H4 y H5 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| Marcadas estables | 408 → 372 | 302 → 265 | 15 → 9 | 382 → 351 |
| Composición distinta (marcadas) | 9 → 7 | 7 → 6 | 13 → 11 | 0 → 0 |
| Mayor Q | 14,06 → 14,06 | 14,80 → 14,80 | 10,89 → 9,38 | 10,65 → 10,65 |
| Percentil 95 del máximo Q nulo | 19,94 → 19,77 | 19,24 → 19,16 | 20,81 → 20,45 | 19,78 → 19,62 |
| Menor p ajustado de la dimensión | 0,343 → 0,336 | 0,235 → 0,226 | 0,785 → 0,905 | 0,777 → 0,757 |
| Menor p ajustado conjunto | 0,729 → 0,707 | 0,635 → 0,615 | 1,000 → 1,000 | 0,994 → 0,992 |
| Menor q de BH | 0,149 → 0,133 | 0,096 → 0,086 | 0,642 → 0,895 | 0,963 → 0,944 |
| Superan la nula (dimensión / conjunta) | 0 / 0 → 0 / 0 | 0 / 0 → 0 / 0 | 0 / 0 → 0 / 0 | 0 / 0 → 0 / 0 |

En las comparaciones conservadas no cambia ninguna DR, Q ni medida de estabilidad, y ninguna cambia de clase. Tampoco hay comparaciones nuevas ni perdidas fuera de las retiradas.

**Mayor Q de cada dimensión en la 39R** (rango de DR, Q, p ajustado de dimensión, clase):

- Trabajo: `dias_ejercicio=0_dias & distension=nunca_o_casi_nunca`; 0,384; 14,06; 0,336; H3.
- Pareja: `frutas=1-2_porciones & panes=3-4_porciones_o_5-6_porciones`; 0,452; 14,80; 0,226; H3.
- Ejercicio: `cuida=no_cuida`; 0,324; 9,38; 0,905; H3. La mayor Q histórica contenía `prevision=FONASA` y fue retirada, por eso cambia el antecedente y sube el menor p.
- Cuidado: `dias_ejercicio=0_dias & edad=36-44`; 0,375; 10,65; 0,757; H3.

Las diferencias de riesgo, los intervalos de Newcombe y Δ están en `comparacion/comparacion_<dimensión>.csv`. La tabla de diferencias de significación está vacía porque ninguna regla superó la nula de su estrato. No se interpreta como interacción que una regla destaque en un estrato y no en otro.

## V. Sensibilidades

Suma sobre los estratos de cada configuración (Fase 39 → Fase 39R).

| Config. | Reglas | Marcadas | Nula media | Superan nula del estrato |
|---|---|---|---|---|
| S1 | 37.913 → 37.913 | 7.903 → 7.903 | 5.789,1 → 5.789,1 | 1 → 1 |
| S2a | 56.455 → 45.275 | 9.621 → 8.162 | 7.536,8 → 6.287,3 | 0 → 0 |
| S3-bajo | 86.663 → 70.715 | 20.008 → 16.852 | 16.258,6 → 13.675,9 | 0 → 0 |
| S3-alto | 32.621 → 25.091 | 3.797 → 3.152 | 2.407,1 → 1.945,4 | 0 → **1** |
| S4-1 | 651 → 619 | 69 → 63 | 50,9 → 48,0 | 3 → 3 |
| S4-2 | 11.111 → 9.918 | 1.624 → 1.497 | 1.386,4 → 1.274,1 | 0 → 0 |
| S5 | 43.638 → 33.833 | 7.967 → 6.523 | 6.195,9 → 5.034,6 | 0 → 0 |
| S6 | 44.033 → 34.624 | 7.977 → 6.647 | 5.876,7 → 4.801,8 | 1 → 1 |
| S7a (trabaja, 309) | 12.772 → 10.178 | 3.041 → 2.568 | 1.736,3 → 1.434,5 | 0 → 0 |
| S7b (cuida, 251) | 12.256 → 9.785 | 3.150 → 2.666 | 1.992,0 → 1.655,5 | 1 → 1 |

Comparaciones entre estratos en cada sensibilidad: `comparacion_historica/sensibilidades_comparacion.csv`.

**Explicación de los cambios.**

- **Patrón general:** menos ítems producen menos reglas, y con ello baja también la referencia nula. Cada resultado se calculó con su propia nula.
- **S1:** idéntica byte a byte a la histórica en sus 13 tablas (9 de reglas y 4 de comparación), porque la S1 histórica ya excluía ambas variables.
- **Dos cruces de umbral**, ambos solo en sensibilidades y provocados porque la nula baja:
  - **S3-alto:** `alcohol=nunca & med_presion=NO & tabaco=nunca` → no severo, en trabaja (n 87, confianza 0,621), pasa a p ajustado 0,04995. Es redundante y con p conjunto 0,2707, por lo que no alcanza ninguna clase destacada.
  - **S3-bajo, ejercicio:** `aerobico=no_lo_realiza_o_nunca & frutas=1-2_porciones` ya superaba la nula de su dimensión (p 0,013 → 0,011); su p conjunto pasa de 0,0539 a 0,048. No es comparable en el análisis principal porque el estrato de 3 días o más solo tiene 18 participantes con el antecedente y el mínimo es 20. Además, está ligada a la variable del estrato y tiene composición distinta entre estratos. **No interviene en la conclusión**, que exige H5 en la principal.
- **Reglas que superan su nula en la 39R:** además de la de S3-alto,
  - S1, cuida: `bajo_impacto=no_lo_realiza & frutas=1-2 & horas_sentada=6-7` → severo (p 0,033).
  - S4-1: `bajo_impacto=frecuentemente_o_siempre` → no severo, en trabaja (p 0,020) y en cuida (p 0,024); `dias_ejercicio=3-4` → no severo, en cuida (p 0,033).
  - S6, cuida: `dias_ejercicio=0_dias & frutas=1-2 & horas_sentada=6-7` → severo (p 0,045), la misma regla cercana al umbral de la principal.
  - S7b, cuida: `aerobico=no & agua=3-4 & sobrecarga=frecuente_o_siempre` → severo (n 34, confianza 0,912; p 0,031). Incluye el módulo de sobrecarga, marcado como potencialmente circular.

  Ninguna se presenta como hallazgo: dependen de la configuración y la conclusión no se basa en sensibilidades.

**Lectura de las diferencias marcadas de la principal en cada sensibilidad (39R):**

| Config. | Se mantiene | Se debilita | Cambia de dirección | No evaluable |
|---|---:|---:|---:|---:|
| S1 | 1.316 | 237 | 55 | 212 |
| S2a | 1.428 | 0 | 0 | 392 |
| S3-bajo | 1.820 | 0 | 0 | 0 |
| S3-alto | 995 | 0 | 0 | 825 |
| S4-1 | 109 | 0 | 0 | 1.711 |
| S5 | 1.571 | 0 | 0 | 249 |
| S6 | 1.444 | 0 | 0 | 376 |
| S9 (solo ejercicio) | 132 | 102 | 0 | 0 |

## VI. Comparaciones A/B1 (exploratorias)

Etiquetas históricas sin reajustar: A 150/76/132/171 y B1 150/79/126/174. No se recalculó PCA, K-means ni FAMD. Sin trabajo, pareja ni días de ejercicio.

| Grupo | n | Reglas | Marcadas | Nula media | p exceso | Superan nula |
|---|---:|---|---|---|---|---|
| A_0 | 150 | 958 → 840 | 138 → 113 | 164,0 → 149,0 | 0,789 → 0,894 | 0 → 0 |
| A_1 | 76 | 42 → 40 | 5 → 5 | 4,7 → 4,7 | 0,501 → 0,501 | 0 → 0 |
| A_2 | 132 | 849 → 746 | 194 → 179 | 142,5 → 130,4 | 0,065 → 0,063 | 0 → 0 |
| A_3 | 171 | 1.108 → 972 | 223 → 206 | 194,8 → 175,2 | 0,217 → 0,180 | 0 → 0 |
| B1_0 | 150 | 922 → 808 | 146 → 129 | 160,7 → 145,5 | 0,655 → 0,701 | 0 → 0 |
| B1_1 | 79 | 40 → 38 | 7 → 7 | 4,4 → 4,4 | 0,172 → 0,172 | 0 → 0 |
| B1_2 | 126 | 813 → 713 | 177 → 163 | 135,1 → 123,6 | 0,110 → 0,101 | 0 → 0 |
| B1_3 | 174 | 1.123 → 985 | 234 → 213 | 207,5 → 187,0 | 0,238 → 0,225 | 0 → 0 |

| Comparación | Comparables | Marcadas | Nula media | p exceso | Superan nula |
|---|---|---|---|---|---|
| A | 294 → 234 | 251 → 199 | 258,5 → 205,9 | 0,828 → 0,849 | 0 → 0 |
| B1 | 333 → 271 | 297 → 240 | 291,7 → 237,7 | 0,342 → 0,444 | 0 → 0 |

Las etiquetas A y B1 no son antecedentes ni perfiles clínicos. Esta comparación no elige entre ellas.

## VII. Conclusión: resultado C

Se decidió de forma mecánica, con las condiciones de la sección 13 del protocolo histórico:

1. **Resultado A, no se cumple.** Exige al menos una comparación H5 que además sea consistente. Hay 0 comparaciones H5 en las cuatro dimensiones: ninguna supera la nula de su dimensión (menor p ajustado 0,226). Las condiciones de nula conjunta, sensibilidades y S9 no llegan a aplicarse.
2. **Resultado B, no se cumple.** Exige una regla de clase 5 que supere la nula conjunta de los 9 estratos. Hay 0 reglas de clase 5, 0 superan la nula del estrato (menor p ajustado 0,0549) y 0 superan la nula conjunta (menor p ajustado 0,2527).
3. **Resultado C, se cumple.** Las asociaciones son débiles o compatibles con el azar, y no se identifican diferencias suficientemente consistentes entre subpoblaciones.

La lectura estricta de S9 da el mismo resultado. La conclusión se mantiene dentro del alcance exploratorio de datos sintéticos, sin causalidad, validación clínica ni recomendaciones.

## VIII. Impacto en la tesis (identificado, no modificado)

No hay borrador de tesis en el repositorio. Si el texto externo cita la Fase 39, debe revisarse:

- Descripción de la matriz: 31 → 29 variables, 94 → 90 ítems; `prevision` y `usa_medicamentos_diabetes` no deben figurar como antecedentes.
- Resultados: 59.672 → 47.912 reglas; 10.739 → 9.085 marcadas; 8.610 → 7.087 redundantes; comparables y clases según las secciones III y IV.
- Las tablas por estrato, de comparación, de sensibilidades y de A/B1 según este informe.
- La redacción de la conclusión se mantiene: resultado C.
- Si se citan resultados de sensibilidad, los dos cruces de umbral de la sección V.

Documentos del proyecto con cifras antiguas, sin tocar:

- Fase 39: Word 02 y 04 a 16, 19 y 20 (y sus fuentes), y las figuras f01 a f06. **La 39R no regeneró figuras ni documentos Word.**
- `fase40/40D_orientaciones/40D-1_informe.md:96`: sus afirmaciones sobre las Fases 38 y 39 siguen siendo válidas con 38R y 39R. La referencia a la nota 20 remite a un documento histórico.

## IX. Integridad

| Control | Resultado |
|---|---|
| Huellas de `analisis/` (incluida la 38R, salvo la 39R), datos y `src/`: 6.537 archivos | 0 cambiados, 0 nuevos |
| Manifiestos de las Fases 34 a 39: 6.462 archivos | Fases 36 a 39 sin diferencias. Fases 34-35: las 4 diferencias en 3 rutas ya existentes antes de la 38R |
| Diferencias no documentadas | 0 |
| Sello de la 38R (protocolo y código) | Íntegro |
| `test_40b1_proteccion_historica.py` | 5/5 OK |
| Respaldo previo a la 38R y 134 archivos pendientes de la Fase 40 | 0 distintos |
| `git status` sin la carpeta 39R | 87 líneas, igual al inicial |
| Rama, HEAD y stash | `datos-simulados`, `573d3a3`, vacío |
| `__pycache__` en Fases 36 a 39 | Ninguno |
| Escrituras fuera de la 39R | 0 |
| Pruebas metodológicas | 27/27 |
| Controles negativos | 30/30 detectados |
| Barreras | 106/106 |
| Reproducibilidad | Reglas y nula de «3 días o más», y comparación completa de trabajo, repetidas desde cero: idénticas |

**Controles históricos incompatibles.** `integridad_39.py` y las pruebas p18 y p19 exigen HEAD `745d689` y `src/` sin cambios, por lo que ya no pueden cumplirse. No se desactivaron ni se modificaron; los reemplaza un control correctivo independiente (`scripts/integridad_39r.py`, y p18 y p19 adaptadas en `pruebas_39r.py`).

## X. Incidencias

### Resultados verificados

- Exclusiones cumplidas en todas las configuraciones.
- Conclusión C obtenida después de todos los controles.
- Reglas y comparaciones conservadas sin cambios en sus métricas ni en su clase.
- Históricos, 38R y trabajo pendiente intactos.

### Limitaciones

- Datos sintéticos, análisis no ciego y misma muestra para descubrir y evaluar.
- La regla más cercana al umbral queda en 0,0549: no lo supera y el umbral no se ajustó. Es la misma regla que supera la nula en S6.
- La referencia nula de heterogeneidad es una aproximación a la ausencia de interacción (protocolo histórico, sección 9), controlada por calibración.
- La tabla de significación nominal es exploratoria y posterior al sello histórico.
- `comparar_39r.py`, `pruebas_39r.py` y `pruebas_barreras_39r.py` se escribieron después del sello; solo comparan y verifican (`protocolo/02_modificaciones_posteriores.md`).
- Antes del sello se ejecutó una prueba de humo con severidad permutada, en una carpeta temporal fuera del proyecto. No produce resultados del análisis.

### Requieren autorización

1. **S7a con 263**, a decidir por separado; tampoco se ejecutó aquí.
2. **Generar figuras y Word corregidos** de las Fases 38R y 39R.
3. **Actualizar la tesis** y `40D-1_informe.md`, si corresponde.
4. **Commit de las carpetas 38R y 39R**, hoy sin seguimiento.
5. **Pendientes de la Fase 40, ajenos a la 39R:** pruebas integrales finales, rotación de `SECRET_KEY` y commit.
6. La Fase 37D sigue usando las dos variables de forma descriptiva; no se revisó aquí.
