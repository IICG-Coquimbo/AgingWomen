# AgingWomen: Etapa 3A. Auditoría integral de la Tesis Versión 9

Fecha: 2026-11-08 · Rama `datos-simulados` · HEAD `573d3a3` · Solo lectura, comparación y diagnóstico.

**Documento auditado:** `Tesis Ver.9.pdf`, en la raíz de AgingWomen. 105 páginas. Portada «Coquimbo, 8 de noviembre de 2026». SHA-256 `f9709d1e3052817047f4e0d66b5c15f36768370e5655d954965cf610b35a8b28`, 5.992.124 bytes. No está versionado en Git.

Las páginas citadas son **páginas del PDF**. En el cuerpo con numeración arábiga, la página del PDF es la impresa más 8.

**Abreviaturas de rutas**

| Abreviatura | Ruta dentro de `analisis/` |
|---|---|
| `R38` | `fase38/38R_reglas_asociacion_corregidas` |
| `R39` | `fase39/39R_asociaciones_condicionadas_corregidas` |
| `H38` | `fase38/38_reglas_asociacion_generales` (solo para explicar errores) |
| `R33` | `reunion_2026-11-03/revision_33_variables` |
| `RF33` | `random_forest_revision_35b_33_variables` |
| `BOOT` | `complemento_bootstrap_33` |
| `F37` | `fase37` |

**Cómo se verificó cada dato**

| Código | Significado |
|---|---|
| [R] | Reproducido aplicando filtros o conteos a los CSV definitivos. No se recalculó ningún modelo ni referencia nula. |
| [L] | Leído directamente del archivo de resultados o del informe definitivo. |
| [C] | Leído en el código actual de `src/`, incluidos los cambios sin commit. |
| [V] | Revisión visual de la página renderizada. |
| [D] | Dato documentado en un informe de Fase 40. Las pruebas no se volvieron a ejecutar en esta auditoría. |

---

## A. Resumen ejecutivo

**La tesis V9 es sólida en su mayor parte, y el problema principal está localizado.** El OB2 coincide con sus fuentes definitivas, salvo detalles. La parte inicial del OB3 (5.3.1) ya usa las cifras corregidas de la 38R y la 39R. La sección 5.3.2 quedó a medio actualizar: dice «9.761 reglas», pero sus tablas, cifras y figuras de evaluación siguen siendo las de las Fases 38 y 39 históricas, que incluían `prevision` y `usa_medicamentos_diabetes`.

**Las conclusiones no cambian.** Con las cifras corregidas sigue habiendo una sola regla destacada y frágil, ninguna regla robusta y resultado C en la 39R. Los capítulos 6 y 7 pueden conservarse casi completos.

**Hallazgos por prioridad** (matriz de la sección «Matriz de hallazgos»)

| Prioridad | Filas |
|---|---|
| Crítica | 12 |
| Alta | 14 |
| Media | 14 |
| Baja | 20 |
| **Total** | **60** |

De las 60 filas, 10 registran contenido correcto («conservar»). Las otras 50 son: 22 para sustituir, 14 para aclarar, 10 para ampliar y 4 para verificar. La evidencia está verificada en 56 filas y pendiente en 4 (H-38, H-39, H-45 y H-53).

**Hallazgos por área**

| Área | Filas | Situación |
|---|---|---|
| OB3 y metodología del OB3 (H-01 a H-27) | 27 | Concentra las 12 críticas |
| OB1 y OB2 (H-30 a H-45) | 16 | Sin críticas; dos altas (Tabla 5.10 y lenguaje de la PDF 53) |
| Plataforma (H-50 a H-62) | 12 | Cuatro altas, todas de texto |
| Objetivos, conclusiones y presentación (H-70 a H-74) | 5 | Una alta: precisar la tensión entre objetivo y cumplimiento |

**Los cinco errores más importantes**

1. **Figura 5.20 equivocada (PDF 70).** Su título anuncia la confianza de cada regla según el número de participantes, pero la imagen es la frecuencia basal por estrato, igual que la Figura 5.22.
2. **Tablas 5.19, 5.20 y 5.21 con cifras históricas (PDF 69, 70 y 72).** Se reproducen exactamente sobre las 12.201 reglas históricas, y no sobre las 9.761 vigentes que el mismo párrafo anuncia.
3. **Reglas marcadas: 1.119 frente a 650 (PDF 69).** Lo vigente es 971 frente a 544.
4. **«No se mantuvo con otros umbrales» (PDF 71).** Confunde permanencia con significancia: con umbrales bajos la regla se mantiene igual, pero no supera su referencia nula.
5. **Figuras 5.21 y 5.23 históricas (PDF 71 y 73).** Muestran 1.119 y 650, y marcadas por estrato que ya no son vigentes.

**Plataforma (5.3.3).** La descripción general es correcta, con cuatro diferencias relevantes respecto del código: la personalización no usa «únicamente» la MRS, la sección 5.1.1 aún dice que se calcula el nivel de severidad, no se describen los estados de ronda provisional, parcial y no verificable, y las cifras de pruebas son de una versión anterior.

**Lo que esta auditoría no modificó.** No se tocó la tesis, los análisis 34–39R, los protocolos, el conjunto limpio ni Django. La comprobación de integridad está en la sección I.

---

## B. Hallazgos prioritarios que afectan la validez del OB3

**B.1. Mezcla de dos versiones del análisis en 5.3.2.** El párrafo inicial de la PDF 69 habla de «las 9.761 reglas», y luego entrega 372, 38, 5 y 1, que solo se reproducen con las 12.201 históricas. El lector ve un único análisis, pero son dos universos distintos: el histórico incluía dos variables que las decisiones de las Fases 35 y 36 excluían (`prevision`, `usa_medicamentos_diabetes`). Es el defecto de mayor peso, porque toca la evaluación central del OB3 (H-01 a H-04, H-06, H-09, H-11).

**B.2. La figura de la evaluación central no corresponde (H-05).** La Figura 5.20 debe mostrar la nube de reglas según su confianza y casos. Ahora duplica la información basal de la Figura 5.22.

**B.3. Lectura de la regla destacada (H-07, H-08, H-24).** La regla es correcta en sus 46 de 57 casos, 80,7 %, lift 1,519, convicción 2,429 y diferencia de 27,6 puntos. Lo que debe corregirse es su evaluación:

| Medida | V9 | Vigente 38R |
|---|---|---|
| z de la regla | 4,17 (figura) | 4,173 |
| Percentil 95 nulo del máximo z | 4,11 (figura) | 4,085 |
| Percentil 95 nulo de la diferencia máxima | 26,7 pts | 26,5 pts |
| p de Fisher | no citado | 0,000008 |
| p ajustado por la búsqueda | no citado | 0,0330 (histórico 0,038) |
| q de Benjamini-Hochberg | no citado | 0,0768, el mínimo de todas las reglas, no alcanza q < 0,05 |
| IC 95 % de la confianza | no citado | 68,7 % a 88,9 % |
| Diferencia de riesgo | no citada | 30,9 pts (18,1 a 40,2) |
| Reaparece en submuestras | no citado | 88,5 %, siempre con la misma dirección |

**B.4. Estabilidad de la regla en las 15 sensibilidades** (`R38` informe 38R-12):

| Situación | Sensibilidades | Detalle |
|---|---|---|
| Se mantiene (4) | S2a; S3-bajo; S7b; S7b-251 | En S2a además supera su nula (p 0,036). En S3-bajo mantiene n_A 57, 80,7 % y 27,6 pts, pero no supera su nula. En S7b y S7b-251 es compatible con la nula. |
| Desaparece (4) | S1; S3-alto; S8a; S8b | S1 baja a n_A 52, bajo el umbral de 53. S3-alto por falta de casos. S8b, n_A 23. |
| No evaluable (7) | S2b; S4-1; S4-2; S5; S6; S7a; S7a-309 | Su definición cambia o retira algún componente de la regla. |

**B.5. Los resultados particulares de la 39R que cruzaron el umbral están ausentes (H-18).** La V9 solo dice que ninguna regla superó la nula. Eso es exacto para el análisis principal, pero faltan las excepciones en sensibilidades y la razón por la que no cambian el resultado C (sección C.6).

**B.6. Transparencia sobre la repetición correctiva (H-20).** La V9 afirma que el protocolo se selló antes de calcular ninguna regla. El protocolo 38R (SHA-256 `32a64ec8…b601e867`, sellado el 2026-11-08 a las 10:30:52) se selló antes de ejecutar la 38R, pero **después de conocer la Fase 38 histórica**. La 39R, además, se ejecutó conociendo la 38R. Debe declararse, porque es parte del carácter exploratorio.

---

## C. Correcciones estadísticas: lo escrito frente a lo definitivo

### C.1. Tabla 5.19 (PDF 69)

Filtros: confianza mínima, lift > 1 y convicción > 1 sobre `R38/reglas/reglas_principal.csv` [R]. Las 9.761 reglas cumplen lift > 1 y convicción > 1.

| Confianza mínima | V9 (histórica, 12.201 reglas: reproducida exacta) | Vigente 38R (9.761 reglas) |
|---|---|---|
| 65 % | 372 (365 hacia severidad + 7 hacia no severidad) | **354** (349 + 5) |
| 70 % | 38 | **35** |
| 75 % | 5 | 5 |
| 80 % | 1 | 1 |

Nota propuesta: «De las 9.761 reglas del análisis principal; todas las reglas con confianza de 65 % o más tienen consecuente de severidad, salvo cinco.»

### C.2. Reglas marcadas (PDF 69)

| Medida | V9 | Vigente 38R |
|---|---|---|
| Marcadas | 1.119 | **971** |
| Hacia severidad / no severidad | 674 / 445 | **629 / 342** |
| Media bajo la referencia nula | 650 | **543,56** (≈ 544) |
| Percentil 95 nulo | no citado | 811,25 |
| p de exceso | no citado | 0,013 |

Fuentes: `R38/reglas/reglas_principal.csv` [R], `R38/reglas/resumen_principal.json` y `R38/referencia_nula/nula_principal.csv` [L].

### C.3. Tabla 5.20 (PDF 70)

| Clase | V9 | Vigente 38R |
|---|---|---|
| Redundantes | 926 | **787** |
| Compatibles con la referencia nula | 192 | **183** |
| Cumplen los criterios | 1 | 1 |
| Total | 1.119 | **971** |

Las tres categorías son excluyentes y suman el total (787 + 183 + 1 = 971). Fuente: `R38/reglas/clases_principal.csv` y `reglas_principal.csv` [R].

### C.4. Tabla 5.21 (PDF 72), propuesta desde `R39/reglas/resumen_estratos.csv` [L]

Los tamaños y las frecuencias de severidad de la V9 son correctos.

| Dimensión | Estrato | n | Severa (%) | Marcadas V9 → vigente | Esperadas V9 → vigente | p V9 → vigente | Percentil 95 nulo |
|---|---|---|---|---|---|---|---|
| Trabajo | Trabaja | 309 | 57,6 | 2.162 → **1.842** | 1.422 → **1.168** | 0,007 → **0,006** | 1.531 |
| Trabajo | No trabaja | 220 | 46,8 | 264 → **243** | 218 → **201** | 0,142 → **0,148** | 265 |
| Pareja | Tiene pareja | 356 | 50,8 | 1.922 → **1.617** | 1.150 → **947** | 0,004 → **0,002** | 1.305 |
| Pareja | No tiene pareja | 173 | 57,8 | 183 → **164** | 212 → **195** | 0,768 → **0,809** | 256 |
| Ejercicio | 0 días | 302 | 58,6 | 1.874 → **1.574** | 1.399 → **1.168** | 0,049 → **0,047** | 1.557 |
| Ejercicio | 1-2 días | 148 | 52,7 | 182 → **167** | 208 → **191** | 0,744 → **0,747** | 252 |
| Ejercicio | 3 días o más | 79 | 32,9 | 7 → 7 | 5 → 5 | 0,212 → 0,212 | 9 |
| Cuidado | Cuida | 251 | 56,2 | 2.553 → **2.169** | 1.804 → **1.494** | 0,013 → **0,006** | 1.903 |
| Cuidado | No cuida | 278 | 50,4 | 1.592 → **1.302** | 1.688 → **1.390** | 0,590 → **0,595** | 1.809 |

**Advertencia de lectura.** El exceso global de reglas marcadas en un estrato no equivale a la significancia de una regla individual. En los nueve estratos, ninguna regla superó la referencia nula de su estrato (`supera_nula_estrato` = 0), aunque cuatro estratos muestren exceso global con p < 0,05 sin ajuste por los nueve estratos.

La nota de la tabla debe decir «0,047» en lugar de «0,049».

### C.5. Sensibilidades de la 38R, desde `R38/sensibilidades/resumen_sensibilidades.csv` [L]

| Código | Población n | Reglas | Marcadas | Nula media | Superan nula |
|---|---|---|---|---|---|
| S1, sin imputados | 529 | 7.542 | 889 | 459,5 | 0 |
| S2a, categorías originales | 529 | 9.269 | 853 | 508,9 | 1 |
| S2b, agrupación gruesa | 529 | 13.639 | 1.386 | 549,5 | 2 |
| S3-bajo, umbrales 27/14 | 529 | 23.025 | 4.519 | 3.363,7 | 0 |
| S3-alto, umbrales 80/40 | 529 | 4.938 | 278 | 100,8 | 0 |
| S4-1, una condición | 529 | 77 | 3 | 1,5 | 0 |
| S4-2, hasta dos condiciones | 529 | 1.401 | 91 | 57,5 | 0 |
| S5, sin frecuencias de ejercicio | 529 | 6.955 | 657 | 409,1 | 0 |
| S6, sin próximas a síntomas | 529 | 7.072 | 716 | 384,8 | 0 |
| S7a, laboral observada | **287** | 10.435 | 2.700 | 1.555,8 | 0 |
| S7a-309, laboral ampliada | **309** | 10.178 | 2.568 | 1.434,7 | 0 |
| S7b, sobrecarga observada | **239** | 11.315 | 3.249 | 2.044,5 | 1 |
| S7b-251, sobrecarga ampliada, 12 imputadas | **251** | 10.747 | 2.942 | 1.823,5 | 1 |
| S8a, IMC observado, sin IMC | 267 | 9.808 | 2.359 | 1.569,9 | 0 |
| S8b, IMC observado, con IMC | 267 | 10.798 | 2.855 | 1.761 | 0 |

El exceso de marcadas tiene p < 0,05 en 13 de las 15; las excepciones son S4-1 y S4-2.

**Reglas que superan la nula solo en alguna sensibilidad:**

- **S2a:** la regla de clase 6 (p 0,036).
- **S2b, dos reglas:** comida fuera «nunca o 1-2» y 3 días o más de ejercicio → no severos (n_A 60, p 0,031); bajo impacto «rara vez a siempre», sin medicamentos para la presión y tabaco nunca → no severos (n_A 134, p 0,049, redundante).
- **S7b y S7b-251, la misma regla:** sin ejercicio aeróbico, 3-4 vasos de agua y sobrecarga frecuente o siempre → severos (n_A 34, 91,2 %; p 0,038 en S7b y 0,027 en S7b-251). La sobrecarga puede ser consecuencia de los síntomas.

Los códigos S7a y S7b **no designan las mismas poblaciones en ambas fases**:

| Fase | Código | Población |
|---|---|---|
| 38R | S7a | 287, con información laboral |
| 38R | S7a-309 | 309, todas quienes trabajan; 22 sin ítems laborales |
| 38R | S7b | 239, con sobrecarga observada |
| 38R | S7b-251 | 251, todas quienes cuidan; 12 con sobrecarga imputada |
| 39R | S7a | 309 |
| 39R | S7b | 251 |

### C.6. Por qué los resultados particulares de la 39R no cambian la conclusión C

Fuente: `R39/documentos_definitivos/fuentes/14_sensibilidades.md` y `R39/resultados/conclusion_39R.json` [L].

**Análisis principal:** 0 reglas superan la nula de su estrato, 0 la nula conjunta, 0 comparaciones superan la nula de su dimensión, 0 diferencias H5 y 0 reglas de clase 5. Comparaciones evaluables: 1.348 trabajo, 1.129 pareja, 363 ejercicio y 1.496 cuidado, en total 4.336. Marcadas: 569, 435, 234 y 582. Resultado: C.

**Lo que cruzó el umbral, solo en sensibilidades:** siete reglas superan la nula de su estrato.

| Sensibilidad | Estrato | Regla (consecuente) | n | p estrato | p conjunto |
|---|---|---|---|---|---|
| S1 | Cuida | Sin bajo impacto, frutas 1-2, horas 6-7 (severos) | 27/29 | 0,033 | 0,184 |
| S3-alto | Trabaja | Alcohol nunca, sin medicamentos para la presión, tabaco nunca (no severos) | 54/87 | 0,04995 | 0,271 |
| S4-1 | Trabaja | Bajo impacto frecuente o siempre (no severos) | 24/35 | 0,020 | 0,124 |
| S4-1 | Cuida | Bajo impacto frecuente o siempre (no severos) | 22/31 | 0,024 | 0,185 |
| S4-1 | Cuida | Ejercicio 3-4 días (no severos) | 19/26 | 0,033 | 0,215 |
| S6 | Cuida | 0 días, frutas 1-2, horas 6-7 (severos) | 32/36 | 0,045 | 0,205 |
| S7b | Cuida | Sin aeróbico, agua 3-4, sobrecarga frecuente (severos) | 31/34 | 0,031 | 0,031 |

Una sola diferencia entre estratos supera la nula de su dimensión, en S3-bajo y ejercicio: sin aeróbico y frutas 1-2 (0 días 122/203; 1-2 días 49/86; 3 días o más 0/18), con p de dimensión 0,011 y p conjunto 0,048.

**Por qué no modifican C:**

1. C se define sobre el análisis principal, en el que no hay ninguna regla ni diferencia que supere su referencia.
2. Cada regla aparece en una sola configuración y no se repite en la principal ni en otra sensibilidad.
3. Solo la regla de S7b supera la nula conjunta, porque S7b tiene un único estrato y ambas nulas coinciden. Se apoya en 34 participantes y usa la sobrecarga, que puede ser consecuencia de los síntomas.
4. La diferencia de S3-bajo no cumple la comparabilidad mínima principal (18 participantes frente a un mínimo de 20) y depende de 0 severas en ese grupo.
5. Son resultados exploratorios de muchas búsquedas sobre datos sintéticos.

### C.7. Otras correcciones numéricas de OB3

| Dato (PDF) | V9 | Vigente | Fuente |
|---|---|---|---|
| Categorías originales agrupadas (67) | 40 | **37**: 27 con 1 a 26 casos y 10 con n = 0 | `R38/preparacion/trazabilidad_transformaciones.csv` [R]; informe 38R-04 |
| Categorías nominales sin ítem (67) | cinco | **dos**: «compró comida» (22) y «otro» (7) | Misma fuente. Las tres restantes de la histórica eran de `prevision` (NINGUNA 15, FFAA 7, NS 2) |
| Percentil 95 de diferencia máxima (71) | 26,7 | **26,5** | `R38/referencia_nula/nula_principal.csv` [L] |

---

## D. Metodología: exclusiones, poblaciones, sensibilidades y protocolos

**Exclusiones: correctas en la V9.** `prevision`, `usa_medicamentos_diabetes` y `doble_carga` no aparecen como candidatas en ningún punto donde su exclusión fuera obligatoria. Sí aparecen en el EDA descriptivo (Tablas 5.6, 5.9 y 5.11, Figuras 5.8 a 5.11), donde se explicita su exclusión. Esto no es un error. La Tabla 5.18 y la Tabla A.1 están limpias. Se comprobó además que `relevancia_33.csv` no las contiene.

**Imputación, tamaños y definiciones: correctos.** 550 → 565 → 546 → 529; 281/248; IMC imputado en 262 (49,5 %); trabajo en 22; cuidado en 21; 43 filas de doble carga; 75 ceros de ejercicio heredados.

**Universos distintos dentro del OB2: se comprobó antes de opinar.** Una cifra de OB2 no cambia por la 38R. La Tabla 5.12 es el caso ilustrativo: el archivo `reunion_2026-11-03/informe_integrado/comparacion_10000_50000.csv` contiene valores q del universo de 34 variables (0,0561, 0,0473…), y **no debe usarse**. La V9 usa correctamente los del universo de 33 (0,054, 0,046…), en `R33`.

**Sensibilidades y poblaciones.** Las 15 sensibilidades de la V9 están completas en número, pero la PDF 68 no distingue poblaciones (H-13) y la PDF 71 omite parte de los resultados (H-15, H-16).

**Protocolos.** Se describen correctamente sus criterios centrales: umbrales 10 % y 5 % (53 y 27), antecedentes de 1 a 3 condiciones, 1.000 permutaciones y 200 submuestras del 80 %. Faltan el carácter correctivo de la 38R (H-20) y aclarar que la convicción es solo un anexo descriptivo y que no interviene en los criterios del protocolo (H-21).

**Metodología del Capítulo 4.** 4.3.1 a 4.3.3 describen el plan original, incluida la confianza de 80 %, y su última frase prevé el caso sin reglas. Es coherente que 5.3.2 declare la desviación, pero 4.3.2 debería anticipar que la evaluación usó reglas marcadas y referencia nula.

---

## E. Mapa de figuras y tablas

Regla general: **no sustituir automáticamente.** De las 14 figuras definitivas de la 38R y la 39R, solo cuatro corresponden a figuras de la tesis (f02 y f03 de la 38R; f01 y f02 de la 39R). Las otras diez no tienen equivalente y solo servirían como anexo opcional. Se conserva la numeración de la tesis.

En «archivo fuente», el origen de las figuras se determinó por su contenido y su nombre. No se hizo una comparación píxel a píxel, porque el PDF incrusta las imágenes reprocesadas. Cuando dice «probable», la correspondencia no está confirmada.

### Tablas

| N.º y título | PDF | Fase de datos | Archivo fuente | Estado | Acción | Definitiva posible |
|---|---|---|---|---|---|---|
| 4.1 Criterios de diseño del sintético | 22 | Diseño 34 | `supuestos_simulacion.md` | Cualitativa, coherente; sin cifras que contrastar | Conservar | — |
| 4.2 Bloques de generación | 23 | Diseño 34 | `supuestos_simulacion.md` | Cualitativa, coherente; sin cifras que contrastar | Conservar | — |
| 5.1 Observaciones de usabilidad | 38 | OB1 | Sin archivo fuente identificado | No verificable | Conservar | — |
| 5.2 Composición del sintético | 39 | 34 | `informe_conjunto_usuaria.md` | Correcta | Conservar; aclarar 14 frente a 10 (H-39) | — |
| 5.3 Errores agregados | 40 | 34 | `informe_conjunto_usuaria.md` | Correcta, suma 3.533 | Conservar | — |
| 5.4 Depuración | 41 | 34 | `informe_limpieza_usuaria.md` | Correcta, suma 546 | Conservar | — |
| 5.5 Valores perdidos | 41 | 34 | `informe_limpieza_usuaria.md` | Porcentajes correctos; «63» no verificado | Conservar; verificar la nota (H-38) | — |
| 5.6 Tipos de variables | 42 | 34 | `informe_conjunto_usuaria.md` | Correcta, suma 101 | Conservar | — |
| 5.7 Estadística descriptiva | 43 | 34 | `informe_conjunto_usuaria.md`, `informe_eda_usuaria.md` | Correcta | Conservar | — |
| 5.8 Caracterización | 44 | 34 | `informe_limpieza_usuaria.md` | Correcta | Conservar | — |
| 5.9 Baja variabilidad | 47 | 35A | `cierre_fases_34_35/informes/informe_preprocesamiento_fase35_revisado.md` | Correcta | Conservar | — |
| 5.10 Variables elegibles | 49 | 35A | `R33`, Tabla A.1 | **Incompleta**: 32 de 33 | Agregar medicamentos para la presión (H-30) | — |
| 5.11 Correlación significativa | 50 | 34 | `informe_eda_usuaria.md` líneas 982–991 | Correcta | Conservar | — |
| 5.12 q < 0,10 | 54 | 35B | `R33`, `relevancia_33.csv` | Correcta (universo 33) | Conservar | — |
| 5.13 Random Forest | 56 | 35B | `RF33/resultados/rendimiento_modelos.csv`, `pruebas_azar.csv` | Correcta | Conservar | — |
| 5.14 Codificación | 61 | 36 | `fase36/informes` | Correcta | Conservar | — |
| 5.15 Matrices | 62 | 36 | `fase36/matrices/resumen_matrices.json` | Correcta | Conservar | — |
| 5.16 Inercia acumulada | 63 | 37A | `F37/37A_reduccion/tablas` | Correcta: las 24 celdas coinciden con `valores_propios.csv` | Conservar | — |
| 5.17 Cuatro segmentos | 66 | 37D | `F37/37D_caracterizacion/informes/fuentes/08_mrs_por_segmento_A.md` | Correcta | Conservar | — |
| 5.18 Variables OB3 | 68 | 38R | `R38` protocolo y preparación | Correcta, suma 29 | Conservar | — |
| **5.19** Reglas por confianza | 69 | **Histórica** | Debe ser `R38/reglas/reglas_principal.csv` | **Desactualizada** | Sustituir (H-01, H-02) | Valores de C.1 |
| **5.20** Clasificación de marcadas | 70 | **Histórica** | Debe ser `R38/reglas/clases_principal.csv` | **Desactualizada** | Sustituir (H-04) | Valores de C.3 |
| **5.21** Estratos | 72 | **Histórica** | Debe ser `R39/reglas/resumen_estratos.csv` | **Desactualizada** (n y basal correctos) | Sustituir (H-09, H-10) | Valores de C.4 |
| 5.22 Componentes plataforma | 74 | 40 | `src/`, informes Fase 40 | Incompleta | Ampliar (H-52, H-56) | — |
| A.1 Selección de 33 variables | 101–102 | 35B | `R33`, `RF33/resultados/shannon_vs_rf.csv` | Correcta | Conservar | — |

### Figuras del cuerpo

| N.º y título | PDF | Fase de datos | Archivo fuente | Estado | Acción | Definitiva posible |
|---|---|---|---|---|---|---|
| 5.1–5.2 Pantallas de identificación y cuidado | 33–34 | Captura | Plataforma | No verificable en fecha; coherente [V] | Conservar | — |
| 5.3 Sección MRS | 35 | Captura | Plataforma | Correcta: «Puntaje MRS: 0 / 44», sin severidad [V][C] | Conservar | — |
| 5.4 Evaluación voluntaria | 37 | Captura | Plataforma | No verificable en fecha; coherente | Conservar | — |
| 5.5 Variables continuas | 44 | 34 | `figuras/eda_usuaria/distribucion_continuas.png` (probable) | Incompleta en un rótulo: horas sentada n = 546 incluye imputadas | Aclarar en nota (H-36) | — |
| 5.6–5.7 MRS y severidad | 45 | 34 | `figuras/eda_usuaria` | Correcta [V] | Conservar | — |
| 5.8 Correlación Spearman | 46 | 34 | `figuras/eda_usuaria` | Correcta [V] | Conservar | — |
| 5.9 Variables > 85 % | 48 | 35A | `cierre_fases_34_35` (probable) | Correcta [V] | Conservar | — |
| 5.10 Correlación con severidad | 51 | 34 | `figuras/eda_usuaria/asociacion_severidad.png` (probable) | Correcta [V] | Conservar | — |
| 5.11 Distribuciones significativas | 52 | 34 | `figuras/eda_usuaria/frecuencias` (probable) | Correcta [V] | Conservar | — |
| 5.12 Incertidumbre simétrica | 55 | 35B | `R33` (probable) | Correcta [V]; **no usar** `su_34_variables.png` | Conservar | — |
| 5.13 Aporte al RF | 57 | 35B | `RF33/figuras/importancia_B.png` (probable) | Correcta [V] | Conservar | — |
| 5.14 Estabilidad | 59 | Bootstrap 33 | `BOOT/figuras/f01_estabilidad_33_variables_finales.png` | Correcta [V] | Conservar | — |
| 5.15 Shannon frente a RF | 60 | 35B | `RF33/figuras/shannon_vs_rf.png` | Correcta [V] | Conservar | — |
| 5.16 Inercia acumulada | 63 | 37A | `F37/37A_reduccion/figuras/f02_inercia_acumulada.png` | Correcta [V] | Conservar | — |
| 5.17 Silueta | 64 | 37B | `F37/37B_clustering/figuras/f01_silueta.png` (probable) | Correcta [V] | Conservar | — |
| 5.18 Estabilidad congelada y repetida | 65 | 37C | `F37/37C_comparacion_seleccion/figuras/f03_estabilidad_anterior_nueva.png` (probable) | Correcta [V] | Conservar | — |
| 5.19 Severidad en segmentos | 66 | 37D | `F37/37D_caracterizacion/figuras/f14_severidad_segmentos.png` (probable) | Correcta: V 0,124 (q 0,008) y 0,144 (q 0,001), confirmadas en `resumen_37D.json` | Conservar | — |
| **5.20** Confianza según n | 70 | **Imagen equivocada** | — | **Errónea** | Sustituir (H-05) | `R38/documentos_definitivos/figuras/f02_confianza_frente_a_casos.png` |
| **5.21** Referencia nula | 71 | **Histórica** | — | **Desactualizada** | Sustituir (H-06) | `R38/documentos_definitivos/figuras/f03_referencia_nula.png` |
| **5.22** Basal por estrato | 72 | Histórica en versión; datos iguales | — | Datos correctos | Sustitución opcional (H-19) | `R39/documentos_definitivos/figuras/f01_tamanos_basales.png` |
| **5.23** Marcadas frente a azar | 73 | **Histórica** | — | **Desactualizada** | Sustituir (H-11) | `R39/documentos_definitivos/figuras/f02_marcadas_frente_a_nula.png` |
| 5.24 Tablero y orientaciones | 75 | Captura Fase 40 | Plataforma | Coherente con el código [V][C] | Conservar | — |

### Figuras de anexos

| N.º y título | PDF | Estado | Acción |
|---|---|---|---|
| A.1 Escala MRS; A.2 EMPA | 87–88 | Instrumento; sin discrepancias | Conservar |
| A.3 Flujo de la participante | 89 | Incompleta: sin la vía presencial | Baja prioridad (H-59) |
| A.4 Reglas condicionales | 90 | Coherente | Conservar |
| A.5 Arquitectura; A.6 Modelo de datos | 91 | **Desactualizadas**: sin `apps.rondas`, ni `RondaEvaluacion`, ni `ConsentimientoPresencial` | Actualizar o indicar que corresponde a una versión simplificada (H-59) |
| A.7–A.14 Pantallas | 92–99 | No verificable en fecha; coherente | Conservar |
| A.15 Proceso de selección | 100 | Coherente con 33 variables | Conservar |
| A.16 Rondas finalizadas; A.17 Caracterización; A.18 Señales de alerta | 103–105 | Coherentes con el código. A.17 muestra «Grupo 4 — Entre múltiples actividades» [C] | Conservar |

### Figuras definitivas sin equivalente en la tesis

Posible anexo, decisión de la autora; no son necesarias para corregir el manuscrito: 38R `f01_items_principal`, `f04_estabilidad`, `f05_exceso_frente_a_nula`, `f06_lectura_sensibilidades`, `f07_reglas_mayor_z`, `f08_umbrales`; 39R `f03_heterogeneidad_frente_a_nula`, `f04_comparaciones_mayor_Q`, `f05_sensibilidades_comparaciones`, `f06_estabilidad_comparaciones`.

---

## F. Plataforma: estado real frente a la sección 5.3.3

### F.1. Situación por función

| Función | Implementada en código | Pruebas técnicas | Aprobación de la profesora | Validación clínica | Despliegue real |
|---|---|---|---|---|---|
| Tablero MRS, total y dimensiones 0–16, 0–16, 0–12 | Sí [C] `apps/rondas/resultado_mrs.py` | Sí [D] | Sin documento | No | No |
| Estados de ronda | Sí [C]: definitivo, provisional, parcial, no verificable, incompleto, sin datos | Sí [D] | Sin documento | No | No |
| Evolución | Sí [C] `evolucion.py`: dos rondas verificables seguidas; hueco en la no verificable | Sí [D] | Sin documento | No | No |
| Sin categoría de severidad | Sí [C]; `SEVERIDAD_TOTAL` sigue definida en `models.py` sin uso | Sí [D] | Corte «pendiente de confirmación» | No | No |
| Caracterización B1, visible a la participante | Sí [C] `_mi_grupo.html` | Unitarias de los cuatro grupos; en Chrome solo Grupo 4 | Sin documento | No | No |
| Orientaciones | Sí, **apagadas por defecto** [C] | Sí [D] | Sin documento | **No**, «borrador_no_validado» | No |
| Tablero profesional | Sí [C] `estadisticas.py`, `UMBRAL = 5` | Sí [D] | Sin documento | No aplica | No |
| Privacidad: AES-GCM, inactividad 30 min, comprobante firmado | Sí [C] | Sí [D] | Sin documento | No aplica | No |
| Consentimiento y retiro presencial, límite de intentos | Sí [C][D] | Sí [D], sin Chrome final | Sin documento | Validación ético-jurídica pendiente | No |

Toda la Fase 40, salvo 40A y 40B-0, existe solo como cambios sin commit en `datos-simulados`. Debe respaldarse antes de citarla como versión estable.

### F.2. Comprobado como correcto

Catálogo de 11 orientaciones y 22 fuentes, todas con fecha de consulta; estado `borrador_no_validado`; umbral de 2 de 4; ánimo decaído primero con 3 de 4 o más; solo última ronda cerrada y verificable; sin puntaje total, severidad ni grupos en la selección; orientaciones activadas solo con `DEBUG=True` y dos variables explícitas; `UMBRAL = 5`; depuración desactivada por defecto; producción con cookies seguras y rechazo de configuraciones inseguras; AES-GCM en el navegador; cierre tras 1.800 s; comprobante firmado; constancia de retiro aún no conservada en el servidor, por lo que la Recomendación 4 sigue vigente.

### F.3. Diferencias entre el código y la tesis o los documentos

| Punto | Tesis o documento | Código actual | Hallazgo |
|---|---|---|---|
| Personalización | «únicamente con las respuestas de la MRS» (PDF 74) | Con 0 días de ejercicio se destaca la actividad física en cinco tarjetas | H-50 |
| Severidad | «calcula el puntaje y el nivel de severidad» (PDF 31) | Sin categoría; solo puntaje | H-51 |
| Máximo de tres | «como máximo tres» (PDF 74) | Tres principales; la de apoyo va fuera del máximo; el resto, plegado en «Otros temas» | H-54 |
| Grupo visible | PDF 74 correcta | El docstring de `contexto_participante.py` dice «nunca visible» | Comentario desactualizado; no afecta la tesis |
| Grupo en tablero | — | El docstring de `tablero.py` dice que la caracterización está pendiente | Comentario desactualizado; no afecta la tesis |
| Pruebas | 354, 18, 20, 30 (PDF 75) | Documentado después: 387 ejecutadas, 386 OK y 1 omitida; JS 21/21; integridad 20/20; Chrome 23/23 en la Etapa 2 | H-53 |

**Pruebas integrales finales:** siguen pendientes. Las cifras de 386/387 y 21/21 son de la última regresión documentada (`40_pendientes_consentimiento_informe.md`), que no incluyó Chrome. La V9 acierta al declararlo pendiente.

---

## G. Conclusiones: conservar, matizar y reformular

**Conservar sin cambios**

- Cumplimiento parcial del objetivo general (PDF 2 y 77).
- Ninguna regla robusta; ausencia de grupos naturales; baja estabilidad de la selección.
- Separación entre reglas y orientaciones educativas (PDF 79).
- Carácter sintético; ausencia de causalidad, generalización y recomendaciones sanitarias derivadas de reglas.
- Recomendaciones 1 a 8 (PDF 81–82).

**Matizar**

- PDF 53, lenguaje «protectoras», «de riesgo» y «es lo que se necesita para formular recomendaciones» (H-31).
- PDF 58, promesa de contrastar entropía y reglas (H-42).
- PDF 80, añadir que la 38R y la 39R se repitieron conociendo los resultados históricos (H-20).

**Tensión entre objetivo y cumplimiento (H-70)**

- *Objetivo:* «Implementar un modelo digital de recomendaciones… vinculando hábitos de vida y vida laboral con la sintomatología» (PDF 12).
- *Cumplimiento:* se implementó la plataforma y se evaluó el modelo, pero no se obtuvo un modelo seleccionado ni recomendaciones derivadas de los datos; las orientaciones provienen de fuentes sanitarias.
- *Solución sin modificar los objetivos:* mantenerlos intactos y conservar el «cumplimiento parcial», precisando en la primera conclusión que lo no cumplido es la derivación de recomendaciones desde datos, y que esto resulta de la evaluación exigida por el OB3, no de un fallo de ejecución.

---

## H. Plan de actualización para la Etapa 3B

Orden pensado para minimizar los cambios. No iniciar sin autorización.

1. **Obtener la fuente editable.** En la carpeta no hay archivos LaTeX ni Word de la tesis, y es imprescindible para corregir sin rehacer.
2. **Sustituir las tres tablas:** 5.19, 5.20 y 5.21 (C.1, C.3, C.4).
3. **Actualizar el texto de la PDF 69–70:** cifras de reglas marcadas (C.2).
4. **Reemplazar las figuras:** 5.20, 5.21 y 5.23. La 5.22 es opcional.
5. **Reescribir el párrafo de la PDF 71** (regla, sensibilidades y estratos), con los textos propuestos en la matriz.
6. **Añadir el párrafo de resultados de la 39R** y por qué no cambian C (C.6).
7. **Corregir la PDF 67–68:** categorías (37 y 2) y poblaciones S7.
8. **Revisar metodología:** repetición correctiva y anticipación de la evaluación en 4.3.1–4.3.2.
9. **Plataforma:** PDF 31, 74–76 y Tabla 5.22.
10. **OB2:** Tabla 5.10, lenguaje de la PDF 53, ARI y patrón de B1, y promesa de la PDF 58.
11. **Presentación:** erratas, agradecimientos, portada y diagramas A.3, A.5 y A.6.
12. **Decisión final:** ejecutar las pruebas integrales finales antes de citar cifras de pruebas como definitivas.
13. **Cierre:** comparar la nueva versión con esta matriz, hallazgo por hallazgo.

---

## I. Comprobación de integridad y límites

Se tomó una línea base antes de la auditoría y se repitió al terminar, con SHA-256 de todo el proyecto, excepto `.git`, `node_modules`, `__pycache__` y entornos virtuales.

| Control | Inicial | Final |
|---|---|---|
| Archivos con huella | 8.683 | 8.683 |
| Archivos cambiados, nuevos o desaparecidos | — | 0, 0 y 0 |
| Archivos vedados: solo tamaño y fecha, sin abrir | 4 | 4, sin cambios |
| `Tesis Ver.9.pdf`, SHA-256 | `f9709d1e…35a8b28` | `f9709d1e…35a8b28` |
| HEAD | `573d3a3` | `573d3a3` |
| Líneas de `git status --porcelain` | 89 | 90 |
| Entradas de stash | 0 | 0 |

La única diferencia de Git es `?? auditoria_tesis_v9/`, la carpeta de este informe, que es el único archivo escrito en el proyecto. No se hicieron commits ni pushes. Los scripts auxiliares de la auditoría están fuera del proyecto, en el directorio temporal de la sesión.

**No se pudo verificar**

- Aprobación del Comité Ético Científico, de la profesora y validación clínica: no hay documentos en el proyecto. La tesis los declara pendientes, y es coherente.
- Prueba de usabilidad con tres mujeres (Tabla 5.1): sin archivo fuente.
- Citas bibliográficas de los Capítulos 1, 3 y 8: leídas, sin contrastar con las fuentes externas.
- «115 preguntas: 109 + 6» (PDF 31): sin fuente directa en los informes consultados.
- «Otras 63 variables» (Tabla 5.5).
- Correspondencia exacta de archivo para las figuras marcadas «probable».
- Estado actual de las pruebas: no se ejecutaron, por la restricción de esta etapa.

**Documentos que faltan**

- Fuente LaTeX o Word de la tesis.
- Acta o constancia del Comité Ético y de la profesora, si se desea citar su estado.
- Informe de pruebas integrales finales de la Fase 40.

---

## Matriz de hallazgos

Las filas con tipo «conservar» registran lo comprobado como correcto.

| ID | Prioridad | Capítulo y sección | Pág. PDF | Tabla o figura | Texto o cifra actual V9 | Fuente definitiva | Texto, cifra o cambio propuesto | Justificación metodológica | Tipo | Estado de evidencia |
|---|---|---|---|---|---|---|---|---|---|---|
| H-01 | crítica | 5.3.2 | 69 | Tabla 5.19 y texto | «372 reglas alcanzaron el 65 %, 38 el 70 %, 5 el 75 % y solo una el 80 %» | `R38/reglas/reglas_principal.csv` [R] | «354 reglas alcanzaron el 65 %, 35 el 70 %, 5 el 75 % y solo una el 80 %» | Las cifras V9 se reproducen sobre las 12.201 reglas históricas, con variables excluidas | sustituir | verificado |
| H-02 | crítica | 5.3.2 | 69 | Nota Tabla 5.19 | «De las 12.201 reglas… salvo siete» | Igual [R] | «De las 9.761 reglas… salvo cinco» | Mismo universo que el texto | sustituir | verificado |
| H-03 | crítica | 5.3.2 | 69 | Texto | «1.119 reglas fueron marcadas, 674 hacia la severidad y 445 hacia la no severidad, más de las 650» | `R38/reglas/resumen_principal.json`, `referencia_nula/nula_principal.csv` [R][L] | «971 reglas fueron marcadas, 629 hacia la severidad y 342 hacia la no severidad, más de las 544 que el azar produce en promedio (percentil 95: 811; p de exceso = 0,013)» | Cifras históricas | sustituir | verificado |
| H-04 | crítica | 5.3.2 | 69–70 | Tabla 5.20 y texto | 926 / 192 / 1 / 1.119 | `R38/reglas/clases_principal.csv` [R] | 787 / 183 / 1 / 971 | Categorías excluyentes que suman el total | sustituir | verificado |
| H-05 | crítica | 5.3.2 | 70 | Figura 5.20 | Imagen de frecuencia basal por estrato, con título de confianza según n | `R38/documentos_definitivos/figuras/f02_confianza_frente_a_casos.png` [V] | Sustituir la imagen, sin cambiar número ni título | La imagen no corresponde a su título y duplica la Figura 5.22 | sustituir | verificado |
| H-06 | crítica | 5.3.2 | 71 | Figura 5.21 | Muestra 4,17, p95 4,11, 1.119 y media 650 | `R38/documentos_definitivos/figuras/f03_referencia_nula.png` [V] | Sustituir | Figura histórica | sustituir | verificado |
| H-07 | crítica | 5.3.2 | 71 | Texto | «los 26,7 que el azar produce en el 5 % de las búsquedas» | `R38/referencia_nula/nula_principal.csv` [L] | «los 26,5»; añadir z = 4,17 frente a percentil 95 de 4,09, p ajustado por búsqueda 0,033 y q = 0,077 | 26,7 es histórico (0,26704) | sustituir | verificado |
| H-08 | crítica | 5.3.2 | 71 | Texto | «descendió a 52 participantes sin los valores imputados y no se mantuvo con otros umbrales» | Informe 38R-12; `R38/sensibilidades` [L] | «sin los valores imputados bajó a 52 participantes con el antecedente, por debajo del umbral de 53, y desapareció; con umbrales más bajos se mantuvo con los mismos valores, aunque ya no superó su referencia nula, y con umbrales más altos desapareció por falta de casos. De las 15 sensibilidades, fue evaluable en 8: se mantuvo en 4 y desapareció en 4» | Confunde permanencia con significancia frente a la nula | sustituir | verificado |
| H-09 | crítica | 5.3.2 | 72 | Tabla 5.21 | Marcadas, esperadas y p históricos | `R39/reglas/resumen_estratos.csv` [L] | Valores de C.4; n y basal se conservan | Cifras históricas | sustituir | verificado |
| H-10 | crítica | 5.3.2 | 72 | Nota Tabla 5.21 | «el más cercano al umbral (0,049)» | Igual [L] | «(0,047)» | Valor de 0 días en 39R | sustituir | verificado |
| H-11 | crítica | 5.3.2 | 73 | Figura 5.23 | Barras históricas (≈ 2.160…) | `R39/documentos_definitivos/figuras/f02_marcadas_frente_a_nula.png` [V] | Sustituir | Figura histórica | sustituir | verificado |
| H-12 | crítica | 5.3.1 | 67 | Texto | «resolvió 40 categorías originales, y cinco categorías nominales no generaron ítem» | `R38/preparacion/trazabilidad_transformaciones.csv` [R]; 38R-04 | «resolvió 37 categorías originales (27 con entre 1 y 26 participantes y 10 sin ninguna), y dos categorías nominales no generaron ítem» | Las 3 categorías extra eran de `prevision` | sustituir | verificado |
| H-13 | alta | 5.3.1 | 68 | Texto | «entre quienes trabajan (309), con la sobrecarga entre quienes cuidan (239)» | `R38/sensibilidades/resumen_sensibilidades.csv` [L] | «con las variables laborales entre quienes trabajan (287 con información laboral y 309 en la versión ampliada), con la sobrecarga entre quienes cuidan (239 con la sobrecarga observada y 251 en la versión ampliada, 12 con el dato imputado)» | Mezcla una población ampliada con una principal; el mismo código no implica igual población | aclarar | verificado |
| H-14 | alta | 5.3.2 | 71 | Texto | «sin los valores imputados ninguna regla cambió de dirección y la señal global se mantuvo (889 marcadas frente a 460 esperadas)» | `R38/sensibilidades/lectura_resumen.csv` [L] | Conservar; añadir que de las 971 marcadas, 474 se mantienen, 124 se debilitan y 373 desaparecen por falta de casos | La frase es correcta pero incompleta | ampliar | verificado |
| H-15 | alta | 5.3.2 | 71 | Texto | «una agrupación más gruesa hizo aparecer reglas de tres o más días de ejercicio» | `R38/sensibilidades/superan_nula_sensibilidades.csv` [L] | «con una agrupación más gruesa, dos reglas superaron la referencia nula solo en esa configuración, una de ellas con tres o más días de ejercicio» | Solo una de las dos tiene ese antecedente | sustituir | verificado |
| H-16 | alta | 5.3.2 | 71 | Texto | No menciona S2a ni S7b/S7b-251 | Igual [L] | Añadir: «la regla destacada superó su referencia con categorías originales (p = 0,036), y una regla con la sobrecarga superó la suya entre quienes cuidan (p = 0,038 con 239 y 0,027 con 251), con 34 participantes y una variable que puede ser consecuencia de los síntomas» | Omisión de resultados que superan la nula | ampliar | verificado |
| H-17 | alta | 5.3.2 | 71 | Texto | «en los estratos grandes hubo más reglas marcadas que las esperadas por azar» | `R39/reglas/resumen_estratos.csv` [L] | «en cuatro estratos (trabaja, tiene pareja, 0 días y cuida) hubo un exceso global de reglas marcadas (p < 0,05, sin ajuste), pero ninguna regla superó su referencia; en el estrato de quienes no cuidan, también grande, hubo menos que las esperadas (1.302 frente a 1.390)» | Impreciso; exceso global no es significancia individual | sustituir | verificado |
| H-18 | alta | 5.3.2 | 71–73 | Texto | No se incluyen los resultados 39R que cruzaron el umbral | `R39/documentos_definitivos/fuentes/14_sensibilidades.md` [L] | Añadir un párrafo breve con el contenido de C.6 | Debe explicarse por qué no cambian C | ampliar | verificado |
| H-19 | media | 5.3.2 | 72 | Figura 5.22 | Versión histórica con etiqueta «basal general» | `R39/documentos_definitivos/figuras/f01_tamanos_basales.png` [V] | Sustitución opcional; datos iguales | Coherencia con las demás figuras | verificar | verificado |
| H-20 | alta | 4.3.1 y 5.3.2 | 29, 69 | Texto | «El protocolo se sella con una huella criptográfica antes de calcular ninguna regla» | `R38/protocolo/sello_protocolo.json`, `01_protocolo_38R.md` [L] | Añadir: «Tras detectar que el análisis inicial incluía dos variables excluidas por decisiones previas, se repitió con un protocolo correctivo sellado antes de su ejecución, pero con conocimiento de los resultados iniciales» | Transparencia; la repetición ocurre con resultados conocidos | ampliar | verificado |
| H-21 | media | 4.3.2 | 29 | Texto | Solo describe confianza 80 %, lift y convicción | `R38/protocolo/01_protocolo_38R.md` [L] | Anticipar reglas marcadas, redundancia, nula y estabilidad; aclarar que la convicción es descriptiva | El protocolo no usa la convicción como criterio | ampliar | verificado |
| H-22 | media | 4.3.1 | 29 | Texto | «(valores imputados, agrupación de categorías, umbrales, largo del antecedente y variables incluidas)» | `R38/sensibilidades/resumen_sensibilidades.csv` [L] | Añadir «y poblaciones restringidas» | Faltan S7 y S8 | ampliar | verificado |
| H-23 | baja | 4.3.3 | 30 | Texto | «antes de dejar el sistema disponible para su uso institucional» | Texto de 5.3.3 | Conservar; está condicionado por la frase final | Plan original, coherente con su salvedad | conservar | verificado |
| H-24 | media | 5.3.2 | 69–70 | Tabla 5.20 | «Cumplen todos los criterios» | `R38/reglas/reglas_principal.csv` [R] | Mantener el rótulo y añadir en texto «q = 0,077, sin alcanzar q < 0,05» | Evita sobreinterpretar la regla | aclarar | verificado |
| H-25 | baja | 5.3.2 | 69 | Texto | «46 de 57 casos (80,7 %, lift de 1,52 y convicción de 2,43…)» | `R38/reglas/reglas_principal.csv` [R] | Sin cambio | Correcto | conservar | verificado |
| H-26 | baja | 5.3.1 | 67–68 | Tabla 5.18 y texto | 529; 281/248; 29 variables; 90 ítems; 42.937; 9.761; 5.319; 4.442; 53/27; 47.912; rangos por estrato | `R38` y `R39` [R][L] | Sin cambio | Correcto; también la equivalencia de algoritmos | conservar | verificado |
| H-27 | baja | 5.3.2 | 73 | Texto | «no se encontró un conjunto de reglas que cumpliera los umbrales y resistiera la evaluación…» | `R38`, `R39` [L] | Sin cambio | Conclusión vigente | conservar | verificado |
| H-30 | alta | 5.2.1 | 49 | Tabla 5.10 | Lista 32 variables; falta «medicamentos para la presión» | `R33/…/relevancia_33.csv` [R]; Tablas A.1 y 5.18 | Añadir «medicamentos para la presión» en el bloque Salud | El texto declara 33 | sustituir | verificado |
| H-31 | alta | 5.2.2 | 53 | Texto | «las protectoras…», «de riesgo…», «que es lo que se necesita para formular recomendaciones: reforzar… atenuar…» | PDF 53, 73; Fases 37D–39R | «variables asociadas a menos o a más síntomas»; suprimir la frase de formulación de recomendaciones | Con asociaciones débiles no se justifica ese lenguaje, y contradice 5.3.2 | sustituir | verificado |
| H-32 | media | 5.2.4 | 64, 65 | Texto | ARI 0,68 (PDF 64), ARI 0,69 y 88 % (PDF 65) | `F37/37D_caracterizacion/resultados/resumen_37D.json` [L] | Indicar 0,68 y 87 % con validación cruzada; 0,69 y 88 % con asignación completa | No son errores, son cálculos distintos sin rotular | aclarar | verificado |
| H-33 | baja | 5.2.4 | 64 | Texto | «(similitud de 0,36)» | `F37/37C_comparacion_seleccion/informes/fuentes/03_registro_lista_B.md` [L] | «(ARI de 0,36)» | Es ARI de S-SOLAPE, no similitud de subespacio | aclarar | verificado |
| H-34 | media | 5.2.4 | 65 | Texto | «reprodujo el mismo patrón» | `resumen_37D.json` [L] | Añadir que con B1 sí fue significativa la diferencia del total (q = 0,002), con efecto pequeño (ε² = 0,027) | Con A no lo fue (q = 0,088); el patrón general se parece pero no es igual | aclarar | verificado |
| H-35 | baja | 5.2.4 | 65 | Texto | «más del 98 % de la variación quedó dentro de los grupos» | `F37/37D_caracterizacion/informes/fuentes/10_comparacion_tres_perspectivas.md` [L] | «del puntaje total (98,7 %)» | Con B1 es 96,8 % | aclarar | verificado |
| H-36 | baja | 5.2.1 | 44 | Figura 5.5 | Horas sentada n = 546 | Tabla 5.7 de la tesis [V] | Nota: incluye 27 imputadas; 519 observadas | Coherencia entre figura y tabla | aclarar | verificado |
| H-37 | baja | 5.2.2 | 52 | Texto | «fercuencia de ejerccicio» | — | «frecuencia de ejercicio» | Errata | sustituir | verificado |
| H-38 | baja | 5.2.1 | 41 | Tabla 5.5 y nota | «Otras 63 variables»; la suma de la nota da 102 frente a 101 | Sin fuente directa | Revisar el recuento | Puede ser un solapamiento de categorías | verificar | pendiente |
| H-39 | baja | 5.1.3 y 5.2.1 | 39, 41, 42 | Tablas 5.2 y 5.6 | «14 campos» y «10 son del personal de salud» | `informe_conjunto_usuaria.md` [L] | Aclarar que 14 son columnas y 10 variables de análisis | Dos cifras sin explicación | aclarar | pendiente |
| H-40 | baja | 5.2.1 | 41–50 | Tablas 5.4–5.11 | 3.533; 83 %; 41,6 %; 3.518; 7 atípicos; 8 de 42; p 0,429; 24 de 25; 0,801; ρ 0,250 a 0,192 | `informe_limpieza_usuaria.md`, `informe_eda_usuaria.md`, `revision_correctiva_fase34`, `resultados/usuaria/validacion_patrones_simulacion.csv` [L] | Sin cambio | Correcto | conservar | verificado |
| H-41 | baja | 5.2.2 | 52–58 | Tablas 5.12, 5.13, A.1 | SU 0,0004–0,0205; 0,046; 0,054; 0,0284; 0,084 (0,016–0,152); 5, 1, 6 y 21; Nogueira 0,129 y 0,128; 39,0, 35,2, 32,6 y 31,4; 15,3 % | `R33`, `RF33/resultados`, `BOOT/resultados` [R][L]; `datos/limpio_usuaria` (81/529) | Sin cambio | Correcto en universo 33 | conservar | verificado |
| H-42 | media | 4.2.2, 5.2.2 y 5.3 | 26, 58 | Texto | «se contrastarán con las reglas de asociación, que mostrarán si las mismas variables…» | Lectura de 5.3 | Añadir una lectura descriptiva breve o retirar la promesa | Se anuncia y no se cumple en 5.3 | aclarar | verificado |
| H-43 | media | 4.2.2 | 26 | Texto | «distinguir las variables protectoras de las de riesgo» | H-31 | «describir la dirección de cada asociación» | Coherencia con H-31 | sustituir | verificado |
| H-44 | baja | 5.2.3–5.2.4 | 60–66 | Tablas 5.14–5.17 | 29,50; 29,00; 38,50; 38,00; 420; 108; 57; 52; 73; 0,238; 0,84 a 0,77; 0,60; 17 y 22 componentes; 150/76/132/171 | `fase36/matrices/resumen_matrices.json`, `F37/*` [L] | Sin cambio | Correcto | conservar | verificado |
| H-45 | baja | 5.1.3 | 39 | Tabla 5.2 y texto | «23 mujeres menores de 40 años… (13 por menopausia quirúrgica y 10 por ausencia prolongada…)» | `informe_conjunto_usuaria.md` línea 135 [L]: 22 (13 + 9) tras la depuración | Confirmar que 23 se refiere a las 550 y 22 a las 546; indicar la base | La diferencia es compatible con la depuración, pero confirmarla exige abrir el conjunto sin errores, vedado en esta auditoría | verificar | pendiente |
| H-50 | alta | 5.3.3 | 74 | Texto | «que se personaliza únicamente con las respuestas de la MRS» | `src/apps/encuestas/contexto_participante.py`, `orientaciones.py` [C] | «que selecciona los temas únicamente con las respuestas de la MRS; además, si la participante indica 0 días de ejercicio, se destaca la actividad física ya presente en cinco tarjetas, sin agregar consejo nuevo» | El código usa un dato de actividad física | sustituir | verificado |
| H-51 | alta | 5.1.1 | 31 | Texto | «la plataforma calcula el puntaje y el nivel de severidad de la MRS» | `src/apps/rondas/resultado_mrs.py`, `esquema.py`, `encuesta.js` [C] | «la plataforma calcula el puntaje de la MRS (los cortes de severidad se usaron solo en el análisis)» | Contradice 5.3.3 y el código | sustituir | verificado |
| H-52 | alta | 5.3.3 | 73–74 | Texto y Tabla 5.22 | Solo «ronda cerrada y verificable» | `resultado_mrs.py`, `evolucion.py` [C] | Añadir: «una ronda en curso muestra una suma provisional o parcial, nunca como resultado; una ronda histórica no verificable no muestra puntaje y queda como hueco en la evolución» | Función implementada y relevante | ampliar | verificado |
| H-53 | alta | 5.3.3 | 75 | Texto | 354 (353 + 1), 18, 20, 30 | `analisis/fase40/40_pendientes_consentimiento_informe.md`, `40_etapa2_consentimiento_seguridad.md` [D] | Actualizar a la última regresión documentada (387 ejecutadas, 386 aprobadas y 1 omitida; 21 de JavaScript; 20 de integridad), manteniendo que las pruebas integrales finales están pendientes; o ejecutarlas antes | Cifras correctas pero de una versión anterior | sustituir | pendiente |
| H-54 | media | 5.3.3 | 74 | Texto | «se muestran como máximo tres» | `orientaciones.py`, `_orientaciones.html` [C] | «se destacan como máximo tres; la de ánimo decaído va aparte y las demás quedan plegadas en “Otros temas”» | Impreciso | aclarar | verificado |
| H-55 | media | 5.3.3 | 74 | Texto | «una intensidad alta de ánimo decaído» | `orientaciones.py` [C] | «una intensidad de 3 de 4 o más»; indicar que los umbrales son propuestas pendientes de validación | Criterio explícito | aclarar | verificado |
| H-56 | media | 5.3.3 | 74 | Tabla 5.22 | «Implementado y probado» | Sección F.1 | Añadir nota: pruebas técnicas con datos ficticios; sin aprobación clínica, ni despliegue | Distinguir los cinco estados | ampliar | verificado |
| H-57 | baja | 5.3.3 | 74 | Texto | Caracterización de tres respuestas | `contexto_participante.py`, `_mi_grupo.html`, `tablero.py` [C] | Sin cambio; opcional: «si falta una respuesta, aparece “Grupo aún no disponible”» | Correcto | conservar | verificado |
| H-58 | baja | 5.3.3 | 75 | Texto | No menciona retiro presencial ni límite de intentos | `40_pendientes_consentimiento_informe.md` [D][C] | Mención opcional | Implementados después de la redacción | ampliar | verificado |
| H-59 | media | Anexos | 89, 91 | Figuras A.3, A.5, A.6 | Sin `apps.rondas`, `RondaEvaluacion`, `ConsentimientoPresencial` ni vía presencial | `src/apps/rondas`, `src/apps/usuarios` [C][V] | Actualizar los diagramas o añadir «versión simplificada» | Desactualizados | verificar | verificado |
| H-61 | media | 5.3.3 | 76 | Texto | «falta completar pruebas específicas con casos representativos de cada grupo» | `src/apps/encuestas/test_contexto_participante.py` [C] | Precisar: los cuatro grupos tienen pruebas unitarias; en navegador solo se recorrió el Grupo 4 | Precisión | aclarar | verificado |
| H-62 | baja | 5.3.3 | 73–76 | Tabla 5.22 y texto | 11 y 22; 2 de 4; 5 participantes; AES-GCM; 30 min; comprobante; borrador; apagadas | `orientaciones_catalogo.json`, `estadisticas.py`, `settings.py`, `inactividad.py`, `encuesta.js`, `retiro.py` [C] | Sin cambio | Correcto | conservar | verificado |
| H-70 | alta | Resumen, 2.1 y 6 | 2, 12, 77 | Texto | Objetivo «Implementar un modelo digital de recomendaciones» y «cumplimiento parcial» | Sección G | No modificar el objetivo; precisar en 6 qué parte no se cumplió y por qué | Tensión entre objetivo y resultado | aclarar | verificado |
| H-71 | baja | 6 | 78 | Texto | «cumplió el criterio… y las seis identificadas… no alcanzaron…, y la selección…» | — | Dividir la frase | Redacción | aclarar | verificado |
| H-72 | media | 6 | 80 | Texto | «la definición de los estratos después de conocer resultados previos» | H-20 | Añadir la repetición correctiva | Coherencia con H-20 | ampliar | verificado |
| H-73 | baja | Preliminares | 1, 3 | Texto | «Preparación de Seminario Superior» y «Agradecer acá» | [V] | Completar antes de la entrega | Marcadores de borrador | sustituir | verificado |
| H-74 | baja | Resumen, 6 y 7 | 2, 77–82 | Texto | Resultados débiles, sin reglas robustas, resultado equivalente a C, sin causalidad ni generalización | `R38`, `R39`, informes de Fase 37 [L] | Sin cambio | Respaldado | conservar | verificado |
