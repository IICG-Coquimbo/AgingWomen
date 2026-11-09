# Figuras e informes definitivos de las Fases 38R y 39R: inventario y validación

Fecha: 2026-11-08. Rama `datos-simulados`, HEAD `573d3a3`, sin commits ni pushes. No se reejecutaron modelos ni permutaciones.

**Ubicación:** `analisis/fase38/38R_reglas_asociacion_corregidas/documentos_definitivos/` y `analisis/fase39/39R_asociaciones_condicionadas_corregidas/documentos_definitivos/`. Cada una tiene `figuras/`, `fuentes/`, `word/`, `scripts/` y `validacion/`.

**Resultado de la validación (Etapa 2):** 1.349 de 1.349 comprobaciones superadas (`validacion/validacion_documentos.csv`). La Etapa 1 tenía 924 y no comparaba columnas, jerarquía de viñetas, maquetación ni tamaño efectivo de letra. Las secciones A a F describen la Etapa 1, con sus cifras vigentes; la sección G y la H recogen el estado final.

## A. Figuras 38R

Las ocho cambian: todas dependen de la matriz corregida (90 ítems, 9.761 reglas). Están en `figuras/`, con el mismo nombre que la histórica.

| Archivo | Fuente | Estado | Validación contra lo dibujado |
|---|---|---|---|
| f01_items_principal | `preparacion/diccionario_items.csv` | Cambia (94 → 90 ítems) | 90 barras con sus valores; 29 variables; sin ítems retirados |
| f02_confianza_frente_a_casos | `reglas/reglas_principal.csv`, `resumen_principal.json` | Cambia | Puntos por clase y consecuente; suma 9.761 |
| f03_referencia_nula | `referencia_nula/nula_principal.csv`, reglas | Cambia | 1.000 permutaciones; 971; media 543,56; máximo z y p95 |
| f04_estabilidad | reglas, `estabilidad/submuestras.csv` | Cambia | 971 marcadas; línea de clase 6; 200 submuestras |
| f05_exceso_frente_a_nula | `sensibilidades/resumen_sensibilidades.csv`, `sensibilidades/nula/*` | Cambia | 16 configuraciones, razón observada/nula en cada una |
| f06_lectura_sensibilidades | `sensibilidades/lectura_resumen.csv` | Cambia | Anchos iguales a la tabla; cada fila suma 971 |
| f07_reglas_mayor_z | `reglas/reglas_no_destacadas_mayor_z.csv` | Cambia | 10 reglas por consecuente; una sola de clase 6 |
| f08_umbrales | resumen principal y sensibilidades | Cambia | 23.025 / 9.761 / 4.938 reglas; 4.519 / 971 / 278 marcadas |

Cambios de texto, sin alterar los datos: indican «Versión correctiva 38R», la leyenda rotula la clase 6 como «Clase 6 del protocolo (no robusta)» y f03, f05 y f07 advierten que un exceso global no hace significativa una regla y que la clase 6 no está validada clínicamente. Se corrigieron solapes menores en f02, f04 y f08.

## B. Figuras 39R

| Archivo | Fuente | Estado | Validación |
|---|---|---|---|
| f01_tamanos_basales | `preparacion/diccionario_estratos.csv` | Datos idénticos a la histórica; se redibuja solo para sacar del gráfico una etiqueta que tapaba un punto | Igualdad exacta de 8 columnas; 17 basales |
| f02_marcadas_frente_a_nula | `reglas/resumen_estratos.csv`, `ab1/resumen_grupos_A_B1.csv` | Cambia | Marcadas y media nula por grupo; 9 estratos suman 47.912 y 9.085 |
| f03_heterogeneidad_frente_a_nula | `comparacion/comparacion_*.csv`, `nula_comparacion_*.csv` | Cambia | Q máximo y p95 de las 4 dimensiones; el observado queda bajo el p95 |
| f04_comparaciones_mayor_Q | `comparacion/comparacion_*.csv` | Cambia | p ajustados rotulados; ninguna supera la nula |
| f05_sensibilidades_comparaciones | `sensibilidades/lectura_comparaciones_principal.csv` | Cambia | Anchos iguales a la tabla |
| f06_estabilidad_comparaciones | `comparacion/comparacion_*.csv` | Cambia | Puntos de las marcadas no redundantes |

## C. Documentos Word

Los 30 superan: ZIP y XML válidos, apertura en Microsoft Word 16 (copias de solo lectura, `validacion/apertura_word.csv`), paginación y exportación a PDF, imágenes insertadas iguales a las de la fuente, filas de tablas iguales a la fuente y referencias entre informes.

**38R (`word/`, 14):** 01_protocolo_38R, 03_diccionario_variables_categorias, 04_agrupacion_categorias_escasas, 05_matriz_transaccional_trazabilidad, 06_equivalencia_apriori_fpgrowth, 07_reglas_generales, 08_soporte_confianza_lift_cobertura, 09_redundancia, 10_estabilidad, 11_referencia_nula, 12_sensibilidades, 13_figuras_tablas, 16_informe_cierre_38R, 17_nota_fase_39R.

**39R (`word/`, 16):** 02_protocolo_39R, 04_diccionario_estratos, 05_tamanos_frecuencias_basales, 06_preparacion_matrices_condicionadas, 07_reglas_por_trabajo, 08_reglas_por_pareja, 09_reglas_por_ejercicio, 10_reglas_por_cuidado, 11_referencias_nulas_estrato, 12_comparacion_formal_estratos, 13_redundancia, 14_sensibilidades, 15_comparacion_exploratoria_A_B1, 16_figuras_tablas, 19_informe_cierre_39R, 20_nota_logica_tablero.

Las explicaciones pedidas están en `12_sensibilidades` (S2b, clase 6 sin robustez, poblaciones S7a/S7b observadas y ampliadas) y `14_sensibilidades` (S3-alto 0,04995, S3-bajo 0,048, S7b, estratos pequeños).

## D. Coherencia numérica

Cada valor se recalculó desde los CSV y se comparó con el informe comparativo.

| 38R | Valor | 39R | Valor |
|---|---:|---|---:|
| Reglas | 9.761 | Reglas en 9 estratos | 47.912 |
| Severo / no severo | 5.319 / 4.442 | Severo / no severo | 25.807 / 22.105 |
| Marcadas | 971 | Marcadas | 9.085 |
| Marcadas no redundantes | 184 | Marcadas no redundantes | 1.998 |
| Nula media / p95 | 543,56 / 811,25 | Comparaciones | 4.336 |
| p del exceso | 0,0130 | Superan la nula principal | 0 |
| Clases 2 / 3 / 4 / 6 | 8.790 / 787 / 183 / 1 | Menor p de estrato | 0,0549 |
| Estables | 480 | Diferencias consistentes | 0 |
| Robustas | 0 | Conclusión | C |

También coinciden las 15 sensibilidades de la 38R y las 10 de la 39R (reglas, marcadas y superan la nula). El 4.336 no aparece literal en el informe comparativo: es la suma de 1.348, 1.129, 363 y 1.496, que sí aparecen.

## E. Impacto en la tesis

El capítulo 5 no está en el repositorio, así que la correspondencia es por contenido; la numeración debe cotejarse con el texto. No se modificó la tesis.

| Elemento a reemplazar | Equivalente corregido |
|---|---|
| Ítems del análisis principal | 38R `f01`, tabla del informe 03 |
| Confianza frente a casos | 38R `f02`, informe 08 |
| Referencia nula de reglas generales | 38R `f03`, tabla del informe 11 |
| Estabilidad | 38R `f04`, informe 10 |
| Exceso por configuración y tabla de sensibilidades | 38R `f05`, informe 12 |
| Lectura en sensibilidades | 38R `f06`, informe 12 |
| Reglas con mayor z y clase 6 | 38R `f07`, tablas del informe 07 |
| Umbrales | 38R `f08`, informe 08 |
| Tamaños y basales por estrato | 39R `f01`, informe 05 (cifras sin cambios) |
| Exceso dentro de estratos | 39R `f02`, informes 07 a 11 |
| Heterogeneidad frente a la nula | 39R `f03`, informe 11 |
| Comparaciones con mayor Q | 39R `f04`, informe 12 |
| Sensibilidades de comparaciones | 39R `f05`, informe 14 |
| Estabilidad de comparaciones | 39R `f06`, informe 12 |
| Texto de método | 29 variables y 90 ítems; las variables retiradas no pueden figurar como predictoras |

## F. Integridad

Control propio (`validacion/control_inicial.json` y `control_final.json`), que excluye únicamente las carpetas `documentos_definitivos`.

| Control | Resultado |
|---|---|
| Archivos del proyecto (8.578): cambiados, nuevos, desaparecidos | 0 / 0 / 0 |
| Contra las huellas finales de la 39R (6.537) | 0 distintas |
| Protocolos sellados 38R y 39R | SHA-256 coinciden |
| 134 pendientes de la Fase 40 | 0 distintos |
| Git | Igual al inicio: 88 líneas, HEAD 573d3a3, stash vacío |
| `__pycache__` en Fases 36 a 39 | 0 |

Los archivos del simulador no se abrieron: se comparó solo su tamaño y fecha.

## G. Incidencias de la Etapa 1 y estado

1. **Maquetación sin revisión visual:** resuelta. Las 108 páginas se exportaron con Word y se revisaron en imagen.
2. **Informes 03 y 04 de la 38R más breves:** resuelta. Tablas reincorporadas y contrastadas con las matrices 38R.
3. **Protocolos sin nota de versión:** resuelta. Nota fuera del texto sellado; las huellas SHA-256 no cambian.
4. **Secciones retiradas:** resuelta en la nota 20 (estado de la plataforma según la Fase 40B-3). «Decisiones para la responsable» sigue fuera de los cierres, por desactualizada.
5. **Informes históricos en Markdown no regenerados:** se mantiene; no eran Word.
6. **Dependencia de `docx` en carpeta temporal:** resuelta (`herramientas_word/`).
7. **S7a con 263:** se mantiene; no se ejecutó porque no fue solicitada.

## H. Etapa 2: corrección documental definitiva

Autorización limitada a contenido documental, presentación, validación y reproducibilidad. No se recalcularon modelos ni permutaciones, y no se tocaron matrices, resultados, protocolos sellados, `src/` ni la tesis.

**Regenerado.** Word y fuentes: los 30 (el conversor y los avisos de versión afectan a todos). Figuras 38R: las 8. Figuras 39R: f03 y f04; f01, f02, f05 y f06 se conservan sin cambios.

| Control | Resultado |
|---|---|
| Comprobaciones documentales | 1.349 / 1.349 |
| Cifras contra CSV y columnas de cada tabla, Word 38R y 39R | 569 y 553 superadas |
| Tabla 39R-11 | 10 encabezados; valores de 9 estratos bajo su columna |
| Tablas 38R-03 y 38R-04 contra matrices | 17 superadas |
| Maquetación (Word real, 30 documentos, 108 páginas) | 0 títulos separados, 0 filas finales aisladas, 0 cabeceras separadas, 0 imágenes fuera de margen |
| Inserciones de figuras | 27 (15 + 12); las 14 figuras iguales por SHA-256 a su archivo; deformación menor que 1 % |
| Tamaño efectivo de letra en figuras | Igual o mayor que 5 pt en las 14 |
| Revisión visual | 108 de 108 páginas, sobre los Word finales (SHA-256 igual a la copia renderizada) |
| Control negativo de columnas | Una fila con `\|` sin escapar detiene la generación y no crea el Word |
| Reproducibilidad | `npm ci` desde cero instala `docx` 9.15.2; sin el paquete el generador se detiene con mensaje claro; `node_modules/` excluida de Git |
| Integridad | 8.578 archivos sin cambios, 6.537 huellas iguales, sellos iguales, 134 pendientes de la Fase 40 iguales, Git igual (88 líneas, `573d3a3`, stash vacío) |

**Ajuste del propio validador.** La comprobación «variables retiradas nunca como vigentes» falló en 38R-04 porque buscaba también en la nota de versión, que nombra `prevision` para explicar su retiro. Ahora ignora solo las notas y amplía la búsqueda a «diabetes» en todo lo demás del documento.

**Incidencias abiertas (ninguna requiere cambiar un resultado estadístico):**

1. Cinco páginas finales con ocupación entre 24 % y 30 %: 38R-03 p6, 38R-17 p2, 39R-04 p3, 39R-13 p3 y 39R-19 p5. Son finales de documento o de sección; se aceptan.
2. El resumen numérico de edad y horas sentada de 38R-03 (mínimo, mediana, máximo) viene del diccionario histórico, declarado en el documento; sus cortes se contrastaron con S2a.
3. `validacion/apertura_word.csv` es de la Etapa 1. La apertura de los Word actuales consta en `validacion/control_maquetacion.csv`.
4. El control de maquetación requiere Microsoft Word; el resto se reproduce con `herramientas_word/LEEME.md`.
5. Fuera de alcance, sin tocar: la documentación de `contexto_participante.py` dice «nunca visible», pero `_mi_grupo.html` muestra el grupo (Fase 40D-H).
6. El capítulo 5 de la tesis no está en el repositorio: la correspondencia de la sección E debe cotejarse con su numeración.
