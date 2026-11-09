# AgingWomen — Etapa 4A: revisión metodológica final

Fecha: 2026-11-08. Rama `datos-simulados`, HEAD `573d3a3`. Auditoría de solo lectura. No se ejecutó ningún modelo, regla, referencia nula, sensibilidad, permutación ni el análisis S7a-263.

**Cómo se indica el origen de cada afirmación**

| Marca | Significado |
|---|---|
| **[C]** | Comprobado directamente en esta auditoría, sobre archivos de datos, tablas guardadas o código. |
| **[L]** | Leído de un informe o protocolo del proyecto; no se contrastó con los datos. |
| **[SV]** | Sin verificar. |

Las únicas operaciones numéricas fueron recuentos sobre tablas ya guardadas, el p de exceso a partir de nulas guardadas, intervalos de Clopper-Pearson y Benjamini-Hochberg sobre valores p guardados. Nada se escribió en el proyecto, salvo este informe.

---

## A. Resumen ejecutivo

**Estado general: la metodología es coherente y sus conclusiones están respaldadas por los resultados definitivos. No se encontró ningún error que obligue a recalcular.**

- **Cifras pedidas:** todas coinciden con las tablas guardadas **[C]**. Son 529 participantes (281 severas y 248 no severas), 29 variables, 90 ítems, 42.937 conjuntos frecuentes, 9.761 reglas, 971 marcadas, 47.912 reglas por estrato, 9.085 marcadas y 4.336 comparaciones.
- **Exclusiones:** `prevision`, `usa_medicamentos_diabetes` y `doble_carga` no aparecen como predictoras en ninguna fase definitiva **[C]**. Solo reaparecen en usos descriptivos legítimos de la Fase 37D y en registros de control.
- **Universo de 33 variables:** coherente entre Fases 35, 36, Random Forest, bootstrap y 38R/39R **[C]**. No hay discrepancia que justifique cambiarlo.
- **Agrupamientos:** la conclusión de que no hay evidencia suficiente de grupos naturales está respaldada. Debe leerse así, y no como demostración de que no existen: la potencia frente a grupos débiles no se evaluó **[L]**.
- **Conclusión C de la 39R:** no se contradice con los resultados de sensibilidad que superan umbrales, porque la regla sellada solo decide sobre el análisis principal **[C]**.
- **S7a-263:** **opcional, y no necesario para cerrar**. No se recomienda ejecutarlo ahora (sección F).

Se registran 13 hallazgos: 2 de prioridad alta, 6 media y 5 baja. **Ninguno cambia un resultado.** Los dos de prioridad alta son de resguardo y de verificación documental:

1. Las carpetas 38R y 39R, que contienen los resultados definitivos, no están bajo control de versiones.
2. La `Tesis Ver.11` no está en el repositorio, así que no se pudo contrastar con las cifras definitivas.

**Incidencia de esta auditoría:** la huella inicial de integridad abrió por error cuatro archivos protegidos, solo para calcular su SHA-256. Está declarado en la sección I.

---

## B. Matriz de coherencia entre fases

| Fase | Origen y población | Variables | Resultado principal | Depende de | Conclusión | Estado |
|---|---|---|---|---|---|---|
| 34 EDA y limpieza | Conjunto sintético; 529 con MRS completo | Instrumento completo | `severo_mrs` ≥ 16: 281 / 248 | Simulación | Base analítica | [L]; 529 y 281/248 [C] |
| 35A preprocesamiento | 529 | 38 → 35 → 33 elegibles (30 generales, 2 laborales, 1 sobrecarga) | Dominancia máxima entre las 33: 84,69 % | 34 | Diabetes sale por dominancia (87,52 %) | [C] |
| 35B SU y FCBF | 529, 287 y 239 | 33 candidatas | 6 con q < 0,10; 2 con q < 0,05 | 35A | FCBF es informativo y no filtra | [C] |
| Random Forest | 529, 287 y 239 | 30 (B), 29/31 (C0/C1), 30/31 (D0/D1) | AUC 0,622 (B), 0,659 (C1), 0,654 (D1) | 35A | Complementario; no selecciona | [C] |
| Bootstrap 33 | 500 remuestreos | 33 | Nogueira 0,129 (IC 0,118–0,139) | 35B | Selección inestable, relevancia más estable (0,337) | [C] |
| 36 matrices | 529; módulos 287/263 y 239/251 | P1 34, P2 33, F1 50, F2 49 columnas | Inercia 29,50 / 29,00 / 38,50 / 38,00 | 35A (no FCBF) | Módulos fuera de las matrices | [C] |
| 37A PCA y FAMD | 529 | Matrices de la 36 | Solo el eje 1 se separa; 12 componentes en P2 retienen 56,7 % | 36 | Sin estructura marcada | [L]; sello [C] |
| 37B agrupamiento | 529 | Coordenadas de la 37A | 420 configuraciones; silueta ≤ 0,30 con 3 ejes o más y k ≥ 3 | 37A | Reproducibles, no diferenciadas | [L]; sello [C] |
| 37C selección | 529 | P2, 12 componentes, K-means, k = 4 | Silueta 0,080 frente a nula 0,078 (p 0,238); E3 0,77; tamaños 150/76/132/171 | 37B | B provisional; sin grupos naturales | [C] en JSON y etiquetas |
| Complemento 37C | 529 | Trabajo, pareja, días | B1 150/79/126/174; ARI A–B1 0,688 (0,677 con CV) | 37C | No añade información a tres preguntas | [C] ARI y tamaños; resto [L] |
| 37D caracterización | 529 | 36 características, incluidas 2 excluidas como descriptivas | 11/36 asociadas al MRS; efectos ≤ 0,284 | 37C | Efectos pequeños | [C] |
| 38R reglas | 529 | 29 variables, 90 ítems | 9.761 reglas, 971 marcadas, 1 de clase 6, 0 robustas | 35, 36, 38 histórica | Señal difusa | [C] |
| 39R condicionadas | 9 estratos | 29 variables, 86–88 ítems por estrato | 47.912 reglas, 9.085 marcadas, 4.336 comparaciones, 0 H5 | 38R, 39 histórica | Resultado C | [C] |

**Verificaciones transversales [C]:**

- Las 29 variables de las reglas de la 38R son exactamente las 30 generales de la Fase 35 menos `imc`.
- La matriz P2 tiene 29 variables y 33 columnas, porque `quien_prepara_comidas` aporta 5 indicadoras.
- Ninguna matriz de la Fase 36 contiene las tres variables excluidas.
- Los módulos laboral y de cuidados no entran en las matrices.

---

## C. Hallazgos metodológicos

### Resumen

| ID | Prioridad | Tema | ¿Cambia resultados? | Origen |
|---|---|---|---|---|
| H-01 | Alta | 38R y 39R sin control de versiones | No | [C] |
| H-02 | Alta | Tesis Ver.11 no disponible para contraste | No | [SV] |
| H-03 | Media | Motivo de exclusión de `prevision` sigue como «pendiente» | No | [C] |
| H-04 | Media | Decisión A / B1 / ninguna sin registro único | No | [C] y [L] |
| H-05 | Media | `configuracion.py` reintroduce variables excluidas | No | [C] |
| H-06 | Media | Entorno de análisis no fijado en un archivo | No | [C] |
| H-07 | Media | p de exceso sin ajuste entre estratos; una frase generaliza de más | No | [C] |
| H-08 | Media | Resolución Monte Carlo en valores cercanos a 0,05 | No | [C] |
| H-09 | Baja | Nota 16 de la 37D propone diabetes como antecedente | No | [C] |
| H-10 | Baja | «Desaparece» en la regla de clase 6 mezcla causas distintas | No | [C] |
| H-11 | Baja | S7a y S7b significan cosas distintas en 38R y 39R | No | [C] |
| H-12 | Baja | Fórmula del p ajustado: el protocolo 38 difiere del código | No | [C] |
| H-13 | Baja | El grupo «sin antecedente» incluye faltantes | No | [C] |

### Prioridad alta

**H-01. Resultados definitivos fuera de control de versiones**
- **Archivos:** `analisis/fase38/38R_reglas_asociacion_corregidas/`, `analisis/fase39/39R_asociaciones_condicionadas_corregidas/`.
- **Evidencia [C]:** `git status` las muestra sin seguimiento y `reglas_principal.csv` no está rastreado. El respaldo `datos/respaldos/2026-11-08_antes_38R/` cubre los 134 archivos pendientes de la Fase 40, no estas carpetas **[L]**.
- **Problema:** la evidencia que sostiene las conclusiones definitivas existe solo en este equipo. Las fases históricas, en cambio, sí están en git.
- **Impacto:** riesgo de pérdida. No afecta a la validez de los resultados.
- **Recomendación:** decidir el commit o, como mínimo, una copia externa verificada. Requiere tu autorización y no se hizo.

**H-02. Tesis Ver.11 no disponible**
- **Archivo:** raíz del proyecto; solo existe `Tesis Ver.9.pdf` **[C]**.
- **Evidencia:** la auditoría de la Etapa 3A sobre la Ver.9 registró 12 hallazgos críticos, varios por cifras históricas en la sección 5.3.2 **[L]**.
- **Problema:** no se puede saber si la Ver.11 usa las cifras de 38R y 39R **[SV]**.
- **Impacto:** es el principal punto abierto del entregable final. No afecta al análisis.
- **Recomendación:** tras las observaciones de la profesora, contrastar la versión final con la matriz de la sección B y con la sección E.

### Prioridad media

**H-03. La exclusión de `prevision` es efectiva, pero su motivo quedó «pendiente»**
- **Archivos:** `analisis/protocolo_fase35b.md:13,17`; `analisis/informe_seleccion_fase35b.md:9`; `analisis/complemento_bootstrap_33/configuracion/candidatas_y_exclusiones.csv`.
- **Evidencia [C]:** el protocolo 35B la deja «pendiente de consultar a la profesora». El archivo de exclusiones dice «protocolo 35B, pendiente». La revisión del 03-11 y el protocolo del bootstrap la tratan como excluida o definitiva. Su dominancia es 82,2 %, así que la regla del 85 % no la explica.
- **Problema:** las otras dos exclusiones tienen motivo sustantivo (dominancia y variable derivada). `prevision` solo tiene un motivo de procedimiento que nunca se cerró.
- **Impacto:** ninguno en los cálculos. Debilita la defensa de la decisión si se pregunta por ella.
- **Recomendación:** añadir un registro breve de cierre con la razón, decidida por la responsable. **No cambia el universo de 33 variables.**

**H-04. No hay un registro único de la decisión sobre la segmentación**
- **Archivos:** `analisis/fase37/37C_comparacion_seleccion/seleccion/decision_final_37C.json`; `analisis/fase37/37D_caracterizacion/informes/fuentes/15_informe_final_37D.md:113`; `analisis/fase40/40D_orientaciones/40D-G_informe.md`.
- **Evidencia:** el JSON sigue en «PROVISIONAL» **[C]**. La 37D deja la decisión a la responsable **[C]**. La 39R usa A y B1 solo como exploración y la Fase 40 usa B1 como contexto **[L]**.
- **Problema:** la práctica es coherente, pero hay que reconstruirla leyendo varias fases.
- **Impacto:** un lector no puede saber qué se adoptó: A, B1 o ninguna.
- **Recomendación:** dejar una decisión escrita, por ejemplo: «sin segmentación adoptada como resultado; A y B1 exploratorias; B1 solo como contexto en la plataforma», si eso refleja tu decisión.

**H-05. Regenerar la Fase 35 reintroduciría variables excluidas**
- **Archivo:** `analisis/preprocesamiento/configuracion.py:29,93,99,200-201`.
- **Evidencia [C]:** conserva `usa_medicamentos_diabetes` y `prevision` como control y como excepción. Es intencional, para no alterar huellas congeladas.
- **Problema:** es el mismo tipo de causa que originó el error de la Fase 38: una lista histórica de variables que sigue vigente en el código.
- **Impacto:** ninguno en los resultados actuales. Hay riesgo en una regeneración futura.
- **Recomendación:** no modificar el archivo. Indicar en la documentación de reproducción que la fuente vigente es `predictores_elegibles_33.csv`.

**H-06. El entorno de análisis no está fijado en un archivo**
- **Archivos:** `requirements.txt`; `analisis/fase38/38R_reglas_asociacion_corregidas/reglas/entorno.json`.
- **Evidencia [C]:** `requirements.txt` solo tiene dependencias de la plataforma web. Las versiones de análisis están dispersas: Python 3.12.5, NumPy 2.2.4, pandas 2.2.3 y SciPy 1.15.2 en la 38R, y scikit-learn 1.6.1 en el protocolo 37A.
- **Problema:** se pueden reconstruir, pero no instalar directamente.
- **Impacto:** dificulta reproducir PCA y K-means, sensibles a la versión.
- **Recomendación:** al cerrar, documentar un archivo único de versiones por fase.

**H-07. Lectura del p de exceso**
- **Archivo:** `analisis/fase39/39R_asociaciones_condicionadas_corregidas/documentos_definitivos/fuentes/19_informe_cierre_39R.md:98,116-123`.
- **Evidencia [C]:** los p de exceso son nominales en 9 estratos; 4 quedan bajo 0,05 (trabaja 0,006; pareja 0,002; 0 días 0,047; cuida 0,006). Con Benjamini-Hochberg entre los 9, quedan 3 (q 0,018) y 0 días sube a 0,106.
- **Problema:** la línea 98 reconoce que el exceso global y las basales no se explican del todo por azar. La línea 123 cierra con «Todo es sintético, exploratorio y compatible con el azar o frágil», después de una lista que incluye las basales.
- **Impacto:** ambigüedad de redacción. El resultado C no cambia.
- **Recomendación:** en la tesis, escribir «a nivel de regla individual, compatibles con el azar» y mantener aparte la señal difusa. Aclarar que los p de exceso no están ajustados entre estratos.

**H-08. Valores cercanos a 0,05 con 1.000 permutaciones**
- **Evidencia [C]:** intervalos de Clopper-Pearson al 95 %:

| Resultado | p ajustado | Intervalo Monte Carlo |
|---|---:|---|
| Regla de cuida, 39R principal | 0,0549 | 0,041–0,070 |
| Regla de S3-alto, 39R | 0,04995 | 0,037–0,064 |
| Regla de clase 6, 38R | 0,033 | 0,022–0,045 |

- **Problema:** con esta resolución, 0,0549 y 0,04995 no se distinguen de 0,05. El umbral se aplicó correctamente; solo la lectura de «supera o no» es más exacta de lo que permite la resolución.
- **Impacto:** nulo en la conclusión. El resultado B exige superar la nula conjunta, y su menor p es 0,2527. La regla de clase 6 queda bajo 0,05 incluso en su límite superior.
- **Recomendación:** describirlos como «en el límite». No aumentar permutaciones.

### Prioridad baja

**H-09. La nota 16 de la 37D propone diabetes como antecedente**
- **Archivos:** `analisis/fase37/37D_caracterizacion/informes/fuentes/16_nota_fases_38_39.md:16`; `analisis/fase37/37D_caracterizacion/protocolo/01_protocolo_37D.md:65-66,71`.
- **Evidencia [C]:** la nota incluye «medicamentos para presión y diabetes» entre las candidatas, y el protocolo dice que las variables excluidas no se reincorporan. Sin embargo, usa diabetes y previsión como descriptivas. Es un antecedente del error corregido en la 38R.
- **Impacto en la 37D [C]:** retirar las dos variables de la familia corrige de 36 a 34 pruebas. Quedan 10 asociadas, las mismas sin diabetes; ninguna cambia de lado. El caso más próximo es `trabaja_actualmente` (q 0,0476 → 0,0495).
- **Recomendación:** dejar constancia de que la nota quedó superada. Aclarar también que diabetes es la asociación individual más alta (r = 0,284): se excluyó por dominancia, no por falta de relación.

**H-10. Lectura de la regla de clase 6**
- **Archivo:** `analisis/fase38/38R_reglas_asociacion_corregidas/comparacion/regla_clase6_sensibilidades.csv`.
- **Evidencia [C]:** de las 4 sensibilidades donde «desaparece por falta de casos», S3-alto no puede conservarla por construcción (n_A 57, mínimo 80), S1 queda a un caso del umbral (52 frente a 53, con confianza 0,808 frente a 0,807) y solo S8a y S8b tienen una pérdida real (n 23).
- **Evidencia más informativa [C]:** en el estrato «trabaja» de la 39R, el mismo patrón tiene igual n_A y n_AC (57 / 46), pero z baja de 4,17 a 3,53 y su p ajustado sube a 0,347, porque la basal pasa de 0,531 a 0,576.
- **Impacto:** la conclusión «no robusta» se mantiene y queda mejor sustentada.
- **Recomendación:** distinguir las causas al describirla y citar el resultado por estrato.

**H-11. Códigos iguales con poblaciones distintas**
- **Evidencia [C]:** S7a de la 39R equivale a S7a-309 de la 38R (10.178 reglas y 2.568 marcadas en ambas). S7b de la 39R tiene 9.785 reglas y S7b-251 de la 38R 10.747, aunque ambas tienen n = 251. La diferencia corresponde a que la 39 excluye toda la variable que define el estrato **[L]**.
- **Impacto:** riesgo de confusión al citar. Está declarado en el protocolo 39R.
- **Recomendación:** citar siempre el código junto con n y fase.

**H-12. Definición del p ajustado**
- **Archivos:** `analisis/fase38/38_reglas_asociacion_generales/protocolo/01_protocolo_38.md:152`; `analisis/fase38/38_reglas_asociacion_generales/scripts/evaluacion_38.py:80`.
- **Evidencia [C]:** el protocolo 38 habla de la proporción de permutaciones. El código usa (1 + k) / 1.001, como dice expresamente el protocolo 39.
- **Impacto:** ninguno. Para todo k entero, ambas fórmulas quedan del mismo lado de 0,05.
- **Recomendación:** citar la fórmula del código en la tesis.

**H-13. El grupo «sin antecedente» incluye participantes sin dato**
- **Archivo:** `analisis/fase38/38_reglas_asociacion_generales/scripts/nucleo_38.py:379-386`.
- **Evidencia [C]:** `n_no = n − n_A`. Quien no tiene el ítem por dato faltante cuenta como «no cumple A» en la diferencia de riesgo, la razón de riesgos y Fisher.
- **Impacto:** no afecta a confianza, lift, z, p ajustado, reglas marcadas ni clases. Sí a las medidas descriptivas en S1 y S7a-309, y a las comparaciones de S1 en la 39R.
- **Recomendación:** declararlo como convención.

---

## D. Revisión de exclusiones

Barrido por bytes de 3.034 archivos de texto en Fases 36, 36 diseño, 37, 38R, 39R, Random Forest, bootstrap y revisión de 33 variables, buscando también `med_diabetes`, `FONASA` e `ISAPRE`. Además, se revisaron por columna los antecedentes de las tablas de reglas y comparaciones **[C]**.

| Fase | `prevision` | `usa_medicamentos_diabetes` | `doble_carga` | Veredicto |
|---|---|---|---|---|
| 35A / 35B (33) | No elegible; SU descriptiva histórica | Salió por dominancia | Salió el 03-11 | Correcto |
| Random Forest 33 | Solo lista de prohibidas | Solo lista de prohibidas | Solo lista de prohibidas | Correcto |
| Bootstrap 33 | Excluida | Excluida | Excluida; aparece en comparación con la corrida antigua | Correcto |
| 36 matrices y módulos | Ausente | Ausente | Ausente | Correcto |
| 37A, 37B, 37C, complemento | Ausente (solo una prueba de control) | Ausente | Ausente | Correcto |
| 37D | Descriptiva | Descriptiva | No se usa; solo se menciona en el protocolo | **Uso legítimo** |
| 38 y 39 históricas | **Predictora** | **Predictora** | Ausente | Error conocido, conservado como histórico |
| **38R** | 0 en reglas | 0 en reglas | 0 en reglas | **Correcto** |
| **39R** | 0 en reglas y comparaciones | 0 en reglas y comparaciones | 0 | **Correcto** |

**Uso descriptivo y modelado.** En la 37D, las variables solo describen y se contrastan una a una con el MRS. No forman segmentos ni generan reglas. Las apariciones restantes en 38R y 39R están en listas de control, barreras, pruebas negativas, protocolos, comparaciones con la versión histórica e informes que explican la corrección. Por ejemplo, `comparacion/identificacion_reglas.csv` identifica las 2.440 reglas retiradas.

**Conclusión: las tres variables no reaparecen indebidamente en ninguna fase definitiva.**

---

## E. Evaluación de las Fases 38R y 39R

### E.1 Fase 38R

Sello del protocolo íntegro: SHA-256 `32a64ec8…` **[C]**.

| Elemento | Valor | Origen |
|---|---|---|
| Universo | 529 (281 / 248) | [C] |
| Variables e ítems | 29 y 90 | [C] |
| Conjuntos frecuentes | 42.937, iguales en Apriori, FP-Growth y enumeración | [C] |
| Reglas | 9.761 (5.319 hacia severo, 4.442 hacia no severo) | [C] |
| Marcadas | 971 | [C] |
| Clases | 8.790 débiles, 787 redundantes, 183 compatibles con la nula, 1 de clase 6 | [C] |
| Nula de marcadas | Media 543,56; P95 811,25; p de exceso 13/1.001 = 0,013 | [C] |
| Estables | 480 | [C] |
| 15 sensibilidades | n, reglas y marcadas coinciden con el informe | [C] |
| Pruebas | 20 pruebas, 65 barreras, 11 mutaciones | [C] recuento |

**La regla de clase 6.** `bajo_impacto=no_lo_realiza_o_nunca & distension=nunca_o_casi_nunca & trabaja=SI` → severo. n_A 57, n_AC 46, confianza 0,807 (IC 0,687–0,889), q 0,0768, p ajustado 0,033 **[C]**.

- En 8 sensibilidades es evaluable: se mantiene en 4 y desaparece en 4. Solo supera la nula en S2a.
- Contiene `distension`, variable próxima a síntomas, y S6 no puede evaluarla.
- No se declara robusta. La clasificación es correcta según el protocolo.

**Resultados globales e individuales.** El exceso (971 frente a 544; p 0,013) indica más reglas marcadas que el azar en conjunto. **No indica que alguna regla concreta sea significativa.** A nivel individual, solo una supera la nula. Es la lectura «señal difusa» de los documentos, y es correcta.

**Interpretación.** El informe de cierre declara que los datos son sintéticos, que ninguna asociación indica causa y que la utilidad clínica no está demostrada (`16_informe_cierre_38R.md:14`) **[C]**.

### E.2 Fase 39R

Sello del protocolo íntegro: SHA-256 `c17c5bf0…` **[C]**.

| Estrato | n | Reglas | Marcadas | Nula media | p exceso | Menor p estrato |
|---|---:|---:|---:|---:|---:|---:|
| Trabaja | 309 | 8.611 | 1.842 | 1.168,0 | 0,006 | 0,187 |
| No trabaja | 220 | 1.302 | 243 | 201,3 | 0,148 | 0,468 |
| Con pareja | 356 | 8.709 | 1.617 | 946,9 | 0,002 | 0,107 |
| Sin pareja | 173 | 1.116 | 164 | 194,8 | 0,809 | 0,163 |
| 0 días | 302 | 9.030 | 1.574 | 1.167,6 | 0,047 | 0,273 |
| 1-2 días | 148 | 1.035 | 167 | 191,2 | 0,747 | 0,646 |
| 3 días o más | 79 | 41 | 7 | 4,9 | 0,212 | 0,427 |
| Cuida | 251 | 8.878 | 2.169 | 1.493,7 | 0,006 | 0,0549 |
| No cuida | 278 | 9.190 | 1.302 | 1.389,6 | 0,595 | 0,933 |
| **Total** | | **47.912** | **9.085** | | | |

Todo recalculado desde las tablas y nulas guardadas **[C]**. Las clases suman 38.827, 7.087 y 1.998; no hay clases 4 ni 5.

| Dimensión | Comparaciones | H1 | H2 | H3 | H4 y H5 |
|---|---:|---:|---:|---:|---:|
| Trabajo | 1.348 | 779 | 362 | 207 | 0 |
| Pareja | 1.129 | 694 | 295 | 140 | 0 |
| Ejercicio | 363 | 129 | 158 | 76 | 0 |
| Cuidado | 1.496 | 914 | 356 | 226 | 0 |
| **Total** | **4.336** | | | | **0** |

**Dos familias de valores p que no deben mezclarse:**

| Pregunta | Valor | Qué significa | Interviene en C |
|---|---|---|---|
| ¿Hay más reglas marcadas que por azar en el estrato? | p de exceso (0,002 a 0,809) | Propiedad del conjunto. Nominal entre estratos | No: informativo |
| ¿Esta regla supera la nula de su estrato? | p ajustado del estrato (mínimo 0,0549) | Control de toda la búsqueda en el estrato | Indirectamente |
| ¿Supera la nula conjunta de 9 estratos? | p ajustado conjunto (mínimo 0,2527) | Criterio del resultado B | **Sí** |
| ¿Difieren los estratos en esta comparación? | p ajustado de dimensión (mínimo 0,226) | Control de Q por dimensión | **Sí** |

Un p de exceso de 0,002 convive sin contradicción con un mínimo individual de 0,107 en el mismo estrato: muchas reglas moderadas pueden acumularse sin que ninguna destaque.

### E.3 ¿Hay contradicción entre C y las sensibilidades?

**No.** En la 39R, 7 reglas superan la nula de su estrato en alguna sensibilidad, y 1 comparación supera la de su dimensión **[C]**.

| Config. | Resultado | Por qué no contradice C |
|---|---|---|
| S1 | Cuida, p 0,033 | Solo con esa configuración; p conjunto 0,184 |
| S3-alto | Trabaja, p 0,04995 | Redundante; p conjunto 0,271; en el límite (H-08) |
| S4-1 (3 reglas) | p 0,020 a 0,033 | Antecedentes de una condición; p conjunto 0,124 a 0,215 |
| S6 | Cuida, p 0,045 | Misma regla cercana al umbral en la principal; p conjunto 0,205 |
| S7b | Cuida, p 0,031 | Solo existe con sobrecarga, módulo marcado como circular |
| S3-bajo (comparación) | Ejercicio, p dimensión 0,011; conjunto 0,048 | No es comparable en la principal (0 filas **[C]**): 18 participantes en un estrato, mínimo 20 **[L]** |

- La regla sellada exige H5 **en el análisis principal** para el resultado A, y clase 5 con nula conjunta para el B. Ninguna se cumple **[C]** (`resultados/conclusion_39R.json`).
- **Advertencia de lectura:** en S7b, el p conjunto es igual al del estrato (0,031), porque solo se analiza un estrato. No equivale a superar la nula de 9 estratos.
- Las sensibilidades no sostienen ningún hallazgo; se presentan como dependientes de la configuración.

**Conclusión C: coherente con el protocolo, los resultados y las sensibilidades.** La frase debe mantener su alcance: asociaciones individuales débiles o compatibles con el azar, señal difusa en conjunto y sin diferencias consistentes entre estratos.

### E.4 Reducción dimensional y agrupamiento

**¿Está respaldada la ausencia de grupos naturales? Sí, con esta formulación: no hay evidencia suficiente de grupos naturales, y los datos son compatibles con un continuo.**

| Indicador | Valor | Lectura | Origen |
|---|---|---|---|
| Silueta, propuesta | 0,080 frente a nula 0,078 (máx. 0,090; p 0,238) | No se distingue de datos sin grupos con iguales correlaciones | [C] |
| E1 | 0,73 frente a máximo nulo 0,65; p 0,048 | Más estable que la nula, en el mínimo posible con 20 réplicas | [C] |
| E3 entre (remuestreo con reajuste) | 0,77; P05 0,68 | Cae desde 0,84 al recalcular la reducción | [C] y [L] |
| S-SOLAPE | 0,36 | Sin dos variables, la partición cambia mucho | [C] |
| S-ORD | 0,69; con ridit, estabilidad 0,53 | Depende de la codificación | [C] y [L] |
| S-BLOQUE | 0,14 | Depende de la ponderación | [C] |
| K-means frente a Ward | ARI 0,33 | Depende del algoritmo | [L] |
| Varianza MRS dentro de segmentos | 96,8 % a 98,7 % | Los segmentos explican muy poco | [L] |

- **Matrices, codificación y escalado:** dimensiones e inercias coinciden con el protocolo. Las decisiones sobre IMC, indicadoras y escalado están documentadas **[C]** y **[L]**.
- **Número de componentes:** la grilla 2, 3, 5, 8, 12, 16 y 20 quedó fijada antes de ajustar. La 37A no elige; decide la 37B y la 37C **[L]**. Con 8 y 16 componentes la partición casi no cambia (ARI 0,91 y 0,92) **[L]**.
- **ARI, silueta y efectos:** se interpretan bien. La 37D aclara que un ARI no es un porcentaje, y los efectos MRS se describen como pequeños.
- **A frente a B1:** coinciden en 88 % (ARI 0,688) **[C]**. B1 se derivó de A, así que no es una validación independiente; los documentos lo declaran **[L]**. La diferencia en ε² (total 0,008 en A y 0,027 en B1) **[C]** no sirve para elegir, porque B1 equivale a comparar por trabajo, pareja y ejercicio.
- **Límite que debe conservarse:** la potencia frente a grupos débiles no se evaluó, E1 y Calinski-Harabasz sí muestran alguna diferencia con la nula, y la enmienda de la referencia correlacionada es posterior al sello **[L]**. Por eso no debe escribirse «no existen grupos».

---

## F. Evaluación del análisis opcional S7a (n = 263)

**No se ejecutó.** Los datos usados son descriptivos de la población.

**Recomendación: OPCIONAL, no necesario para cerrar la investigación. Se aconseja dejarlo documentado como análisis futuro.**

### 1. Pregunta adicional

¿Las reglas con módulo laboral dependen de las 24 participantes con alguna respuesta laboral imputada? En esas 24 hay 16 valores imputados de lugar comprensivo y 10 de estrés laboral; 2 participantes tienen ambos **[C]**.

### 2. Diferencia con las sensibilidades ya realizadas

| Aspecto | S7a-309 | S7a (287) | S7a-263 (no ejecutada) |
|---|---|---|---|
| Población | Todas las clasificadas como trabajadoras | Con información laboral | Con ambas respuestas observadas |
| Respuestas laborales imputadas | 16 + 10 | 16 + 10 | 0 |
| Sin ítems laborales | 22 con trabajo imputado | 0 | 0 |
| Severas | 178 (57,6 %) | 166 (57,8 %) | 152 (57,8 %) |
| Umbrales n_A / n_AC | 31 / 16 | 29 / 15 | 27 / 14 (por regla del protocolo) |
| Reglas / marcadas | 10.178 / 2.568 | 10.435 / 2.700 | No calculado |
| Superan la nula | 0 | 0 | No calculado |
| Menor p ajustado | 0,205 | 0,316 | No calculado |
| Menor p con ítem laboral | 0,346 | 0,316 | No calculado |

Cifras **[C]**. Las 24 excluidas tienen 58,3 % de severas, frente a 57,8 % en las 263: no difieren en la basal.

**Importante:** las 263 solo no tienen imputaciones *laborales*. Las otras 27 variables generales conservan las de la limpieza. Por eso no debería llamarse «observada» sin precisarlo.

### 3. ¿Aportaría información sustancial?

**Sería en gran parte redundante.**

- Solo retira 8,4 % de las 287.
- El paso de 309 a 287 ya mostró que las marcadas son estables: 2.225 en común, 82 % y 87 % de cada lista **[C]**.
- La 37D ya comparó con datos observados las dos variables laborales. Con n 271, lugar pasa de ρ −0,269 a −0,275; con n 277, estrés de 0,195 a 0,198. La conclusión no cambia **[C]**.
- El menor p ajustado (0,316) está lejos de 0,05, aunque no se puede garantizar qué ocurriría con otra población.
- **Lo que no cubre lo anterior:** la 37D examina cada variable por separado, no combinaciones de hasta 3 condiciones. Ese es el aporte residual.

### 4. Riesgos de comparabilidad

- **Otra familia de reglas:** cambian n y umbrales, de modo que las diferencias en reglas mezclan efecto de población y de umbral.
- **Menor potencia** y nula propia, por lo que no se puede comparar el recuento directamente.
- **Caso completo:** supone que las imputaciones laborales no se relacionan con los resultados.
- **Una configuración más**, añadida conociendo todos los resultados: el análisis no es ciego y aumenta las decisiones a posteriori.
- **Tercera variante laboral**, con un código fácil de confundir (H-11).

### 5. ¿Podría modificar justificadamente las conclusiones?

**No.**

- **38R:** las clases se deciden en el análisis principal, que no contiene ítems laborales.
- **Regla de clase 6:** usa `trabaja=SI`, ítem que se retira en las poblaciones de S7a, así que no es evaluable allí.
- **39R:** la condición de consistencia del resultado A exige S1, S2a, S3-bajo, S3-alto y S6. S7a no forma parte de ella, y el resultado B solo depende del análisis principal.
- En el peor caso, añadiría una regla que supera la nula solo en esa configuración, y además con ítems cuya pregunta menciona los síntomas (posible circularidad).

### 6. ¿Es necesario para cerrar?

**No.** La Fase 36 definió 263 como sensibilidad *preparada* del módulo laboral (protocolo 36 ajustado, §10) **[C]**, y no la comprometió para las reglas. El protocolo 38R dice expresamente que no se ejecuta **[C]**.

No se clasifica como «innecesario» porque responde a una pregunta distinta, aunque estrecha, y la Fase 36 ya la había previsto. Si en el futuro se ejecuta, debe hacerse con un protocolo sellado propio, en carpeta aparte y sin tocar 38R ni 39R.

**Texto sugerido para dejarlo documentado:** «No se ejecutó una versión de S7a restringida a las 263 trabajadoras con ambas respuestas laborales observadas. No podía modificar las conclusiones, que no dependen de esa sensibilidad, y queda como análisis futuro.»

---

## G. Riesgos y limitaciones

### Problemas reales, aún abiertos

| Tema | Hallazgo | Requiere |
|---|---|---|
| Resultados definitivos sin versionar | H-01 | Autorización |
| Correspondencia con la tesis final | H-02 | Contraste posterior |
| Motivo de `prevision` | H-03 | Registro breve |
| Decisión sobre segmentación | H-04 | Registro breve |
| Riesgo de regeneración y entorno | H-05, H-06 | Documentación |
| Redacción de valores p y umbrales | H-07, H-08, H-10 | Cuidado al redactar |
| Convenciones y notas superadas | H-09, H-11, H-12, H-13 | Aclaración |

### Limitaciones ya reconocidas en el proyecto (no son errores)

| Limitación | Dónde está declarada |
|---|---|
| Datos sintéticos: sin generalización a mujeres reales ni validez clínica | Todas las fases |
| Las asociaciones provienen de efectos programados en la simulación | 37B y 38R |
| Análisis no ciego; misma muestra para descubrir y evaluar | 38R y 39R |
| Sin causalidad | 37D, 38R y 39R |
| Estabilidad baja de la selección FCBF (Nogueira 0,129) | Bootstrap, informe 05 |
| IMC observado solo en 267 | 35A, 36 y 38 |
| Imputaciones en 22 de trabajo, 16 + 10 laborales y 12 de sobrecarga | 35A, 36 y 38R |
| Referencia nula de heterogeneidad como aproximación (rechazo 0,055; potencia 0,971) | Protocolo 39; prueba p13 **[C]** |
| Enmienda posterior de la referencia correlacionada; 20 réplicas | 37C |
| Dependencia de la partición A respecto de S-SOLAPE, codificación y algoritmo | 37C |
| Sensibilidad de Shannon sin imputaciones laborales, no realizada | Cierre 34-35 |
| Edad del conjunto 36-65, frente a 40-65 de la plataforma | 37D y 40 **[L]** |

### Sin verificar en esta etapa

- Contenido de `Tesis Ver.11` **[SV]**.
- Cada celda de los 30 documentos Word definitivos de 38R y 39R. Se leyeron sus fuentes principales; su validación propia (1.349/1.349) es **[L]**.
- Exactitud de los cálculos de PCA, K-means, SU y Random Forest: no se recalcularon, por restricción de la etapa. Sus resultados se aceptan con sus pruebas internas **[L]**.
- Uso del grupo B1 en el código de la Fase 40: solo se leyeron informes **[L]**.

---

## H. Recomendaciones de cierre

### Imprescindible antes de terminar el proyecto

Ninguna de estas acciones requiere recalcular.

1. **Resguardar las carpetas 38R y 39R** (H-01), con tu autorización.
2. **Contrastar la tesis final con las cifras definitivas** (H-02), una vez incorporadas las observaciones de la profesora.
3. **Registrar el motivo de exclusión de `prevision`** (H-03).
4. **Registrar la decisión sobre segmentación** (H-04).

### Recomendable al redactar

5. Separar siempre p de exceso y p individual (H-07).
6. Describir como «en el límite» los valores cercanos a 0,05 (H-08).
7. Mantener la formulación «no hay evidencia suficiente de grupos naturales».
8. Citar S7a y S7b con n y fase (H-11).
9. Declarar S7a-263 con el texto de la sección F.

### Documentación final de reproducción

10. Indicar la fuente vigente de variables (H-05) y un archivo único de versiones (H-06).

### Puede quedar como trabajo futuro

- S7a-263.
- Validación con datos reales e independientes, que es el límite principal de todo el análisis.
- Potencia frente a grupos débiles.
- Más permutaciones para los casos en el límite. No cambiaría las conclusiones.
- Sensibilidad de Shannon sin imputaciones laborales.

### Reproducibilidad y trazabilidad

| Elemento | Disponible | Evidencia | Origen |
|---|---|---|---|
| Origen y universo de datos | Sí | Carga verificada, 529 y 281/248 | [C] |
| Variables incluidas y excluidas | Sí | `predictores_elegibles_33.csv`, `candidatas_y_exclusiones.csv`, `configuracion_fase36.py` | [C] |
| Transformaciones y criterios | Sí | Protocolos 36 y 38 (R1–R7), `diccionario_items.csv` | [C] y [L] |
| Parámetros | Sí | Protocolos y `configuracion/` | [L] |
| Semillas | Sí | 42 en 36, 37 y 38; `[42, 39, k]` en 39; `semillas_y_parametros.json` en bootstrap | [C] y [L] |
| Protocolos sellados | Sí | 13 de 13 sellos coinciden con su SHA-256 (37A a 39R y bootstrap) | [C] |
| Resultados asociados | Sí | 39R registra 6.537 huellas; 6.533 coinciden al comparar y las otras 4 son «sin abrir» (sección I) | [C] |
| Dependencias entre fases | Sí | 38R importa de la 38 sin modificar, y 39R de 38R y 39; `auditoria_dependencias.csv` | [C] y [L] |
| Versiones del entorno | Parcial | H-06 | [C] |
| Versionado | Parcial | H-01 | [C] |

Las Fases 36 y 35B no tienen archivo de sello: su protocolo está versionado o citado por huella desde la 38R **[C]**. Las diferencias entre fases históricas y definitivas responden a universos de variables distintos y no se tratan como errores: las reglas conservadas no cambian en ninguna métrica **[L]**.

---

## I. Integridad

**Comparación de huellas antes y después de la auditoría [C].** Medición sobre todo el repositorio, sin `.git` y sin esta carpeta nueva.

| Control | Resultado |
|---|---|
| Archivos comparados | 9.020 antes y 9.020 después |
| Nuevos / faltantes / distintos | 0 / 0 / 0 |
| Fases 34–39, 38R y 39R, incluidos protocolos y resultados | Sin cambios |
| Archivos pendientes de la Fase 40 | Sin cambios |
| `Tesis Ver.9.pdf` | Sin cambios |
| `Tesis Ver.11` | **No existe en el repositorio**; no se abrió ni se modificó |
| Estado de `git status` | Antes de crear este informe, idéntico al inicial (SHA-256 `1ad4a4cf…`). Después, 91 líneas en lugar de 90: la única nueva es `auditoria_metodologica_final/` |
| Rama, HEAD y stash | `datos-simulados`, `573d3a3`, vacío |
| Commits, pushes, merges, resets o limpieza | Ninguno |
| Scripts de auditoría | Solo en el directorio temporal de la sesión, con Python sin generar `__pycache__` |
| Único archivo creado en el proyecto | `auditoria_metodologica_final/INFORME_ETAPA_4A.md` |

**Secretos:** `.env` y `.env.desarrollo` no se abrieron; solo se registró su tamaño y fecha.

### Incidencia declarada: apertura de archivos protegidos

La medición inicial de integridad recorrió todo el repositorio **antes** de identificar qué archivos estaban vedados. Por eso abrió estos cuatro, para calcular su SHA-256:

- `datos/sintetico/dataset_usuaria_verdad.csv`
- `datos/sintetico/bitacora_suciedad.csv`
- `datos/sintetico/dataset_usuaria_sucio.csv`
- `analisis/revision_correctiva_fase34/tablas/diabetes_diagnostico_verdad.csv`

| Punto | Detalle |
|---|---|
| Alcance | Lectura de bytes para calcular la huella. Su contenido **no se mostró, no se imprimió y no se analizó** |
| Efecto en la auditoría | Ninguno: ningún hallazgo proviene de ellos |
| Acción correctiva | Las cuatro huellas se borraron del directorio temporal, y no se volvieron a abrir |
| Control final | Solo por tamaño y fecha. Los cuatro coinciden con los valores `sin abrir` registrados por la 39R |
| Por qué importa | Las fases anteriores los dejaron expresamente sin abrir. Esta medición no siguió ese criterio, y va contra la restricción de esta etapa |

---

*Fin del informe. No se inició ninguna corrección ni se ejecutó S7a-263.*
