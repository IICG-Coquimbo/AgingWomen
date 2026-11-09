# Protocolo de la Fase 37D: caracterización de segmentos y análisis descriptivo del MRS

Versión 1. Redactado y sellado el 5 de noviembre de 2026, antes de calcular cualquier asociación entre una característica o un segmento y el MRS. Su huella SHA-256 queda en `sello_protocolo.json`. Cualquier cambio posterior irá en una nota aparte, con su propia huella, y quedará rotulado como «posterior al sellado».

## 1. Objetivos

1. Describir a las 529 participantes sintéticas: características generales y síntomas del MRS.
2. Estudiar las relaciones entre cada característica individual y el MRS, sin segmentar. Es el análisis principal.
3. Caracterizar los cuatro segmentos de `P2_c12_km_k4` (Modelo A) con todas las variables pertinentes y describir el MRS en cada uno.
4. Hacer lo mismo con los cuatro segmentos de la regla de tres preguntas (B1).
5. Comparar las tres perspectivas de forma descriptiva y preparar una nota para las Fases 38 y 39.

La fase no descubre grupos nuevos, no reajusta PCA, FAMD ni K-means, no modifica la regla B1 ni elige una segmentación. Las comparaciones entre A y B1 son exploratorias y **no se usarán para cambiar la selección de la Fase 37C ni para escoger un ganador**. Ninguna asociación se interpretará como causal.

## 2. Lo que ya se conocía antes de sellar

Para no presentar como ciego lo que no lo es:

- **Fases 34C, 35A y 35B:** ya examinaron asociaciones entre características individuales y el MRS (Spearman con `mrs_total`, incertidumbre simétrica y FCBF con `severo_mrs`, bosque aleatorio). Esos resultados son conocidos. Este protocolo incluye **todas** las variables pertinentes, sin elegirlas por esos resultados, y los resultados nuevos no se usarán para seleccionar variables.
- **Revisión inicial de esta fase:** se comprobó que el MRS está completo en las 529 participantes, que los once ítems toman valores de 0 a 4 y que la severidad se reparte en 56, 74, 118 y 281 participantes (53,1 % con 16 puntos o más, cifra ya informada en la Fase 35A). No se calculó ninguna asociación con características ni con segmentos.
- **Segmentos y MRS:** las Fases 37A, 37B, 37C y el complemento no usaron el MRS. La comparación de segmentos frente al MRS es nueva en esta fase.

## 3. Población

Las 529 participantes del conjunto sintético con MRS completo (`mrs_completo = 1`), en el orden de `fase36/matrices/identificadores.csv`. No se excluye a nadie del análisis principal. Las variables que solo aplican a una parte de la población se analizan en esa parte (sección 4).

## 4. Variables

### 4.1 Fuentes

| Contenido | Archivo, solo lectura |
|---|---|
| Valores y estado de cada celda (observada, imputada, no aplicable, faltante, deducida) de las 29 variables de A, del IMC y de los módulos laboral y de cuidados | `fase36/procedencia/procedencia_celdas.csv` |
| Codificación de cada variable | `fase36/artefactos/P2/` y `fase36/artefactos/diccionario_codificacion_36B.csv` |
| Ítems del MRS, dimensiones, total, severidad, etapa menopáusica, previsión y diabetes | `datos/limpio_usuaria/dataset_usuaria_limpio.csv` |
| `severo_mrs` y comprobación de alineación | `datos/analitico/dataset_fase35.csv` |
| Etiquetas oficiales de A | `fase37/37C_comparacion_seleccion/seleccion/artefactos_provisionales/P2_c12_km_k4/etiquetas.csv` |
| Etiquetas de B1, regla, márgenes de A y B1 con validación cruzada | `fase37/37C_complemento_tres_preguntas/asignaciones/etiquetas_alternativas.csv` y `definiciones/definicion_B1_B2.json` |
| Particiones existentes para sensibilidad | `fase37/37B_clustering/etiquetas/etiquetas_principales.csv` y `37B_clustering/sensibilidades/etiquetas/` |

Nunca se abren `dataset_usuaria_verdad.csv`, `bitacora_suciedad.csv`, `dataset_usuaria_sucio.csv` ni ningún archivo con «verdad» en el nombre. Un gancho de auditoría registra cada archivo leído y detiene la ejecución si ocurre.

### 4.2 Características usadas por A (29)

Agrupadas por los bloques del complemento:

| Bloque | Variables |
|---|---|
| Las tres preguntas | `trabaja_actualmente`, `tiene_pareja`, `dias_ejercicio_semana` |
| Actividad física adicional | `frecuencia_aerobico`, `frecuencia_bajo_impacto`, `frecuencia_fuerza` |
| Sedentarismo | `horas_sedentarismo` |
| Cuidados | `cantidad_personas_cuida` |
| Alimentación | `quien_prepara_comidas` y 12 frecuencias de consumo |
| Tabaco y alcohol | `tabaco_frecuencia`, `alcohol_frecuencia` |
| Otras generales | `edad`, `operada_no_mas_hijos`, `usa_medicamentos_presion` |
| Actividad sexual | `tiene_actividad_sexual` |
| Digestión | `distension_abdominal`, `evacuacion_intestinal` |

### 4.3 Características externas a A (7)

| Variable | Población | Tratamiento |
|---|---|---|
| `imc` | 267 con IMC observado | Solo valores observados; la imputación por la media no se usa |
| `etapa_menopausica` | 529 | Descriptiva. En las pruebas, «indeterminada» e «indeterminada (histerectomía)» se agrupan (22) |
| `usa_medicamentos_diabetes` | 529 | 23 imputadas por la moda en la limpieza, sin marca por participante |
| `prevision` | 529 | En las pruebas: FONASA, ISAPRE y «otra o ninguna» (NINGUNA, FFAA y NS) |
| `lugar_trabajo_comprensivo` | Solo quienes trabajan | Sin «no aplica»; 22 faltantes excluidas |
| `estres_entorno_laboral` | Solo quienes trabajan | Igual que la anterior |
| `sobrecarga_fisica_emocional` | Solo quienes cuidan | Sin «no aplica» |

`doble_carga` no se incluye porque es una combinación de trabajo y cuidado, que ya están. Las variables excluidas en las Fases 35 y 36 (dominancia, decisión o redundancia) no se reincorporan.

### 4.4 Codificación

Se usan los códigos del instrumento, como en la interpretabilidad de la Fase 37C: valores numéricos en cuantitativas; 0 y 1 en binarias; el código ordinal en ordinales, y el texto en las nominales. En las tres frecuencias de ejercicio y en `cantidad_personas_cuida`, «no realiza» o «no cuida» toman el valor estructural 0, como en la Fase 36. Ese 0 se informa aparte como «no aplica (0 estructural)» en la descripción.

### 4.5 Resultados del MRS

Según la limpieza del proyecto (`limpieza/reglas.py`) y el modelo de la plataforma (solo lectura):

- Ítems 1 a 11, de 0 (ninguna) a 4 (muy intensa).
- Dimensión somática: ítems 1 a 4 (0 a 16). Psicológica: ítems 5 a 8 (0 a 16). Urogenital: ítems 9 a 11 (0 a 12). Es el orden de ítems del proyecto.
- `mrs_total`: suma de los 11 ítems (0 a 44).
- Severidad en 4 clases: 0 a 4 sin síntomas o muy leves; 5 a 8 leve; 9 a 15 moderada; 16 o más severa.
- `severo_mrs`: total de 16 o más (decisión del 27-10).

Antes de analizar, se recalculan dimensiones, total y severidad desde los ítems y se exige que coincidan con los guardados.

## 5. Datos faltantes, imputados y no aplicables

- **MRS:** completo en las 529; no hay tratamiento de faltantes.
- **Análisis principal:** valores históricos de la Fase 36, observados más imputados en la limpieza. No se imputa nada de nuevo.
- **No aplica:** 0 estructural en ejercicio y cuidado; exclusión de la subpoblación en módulos laboral y de cuidados.
- **Faltantes:** se excluyen de cada prueba. Cada resultado informa su n efectivo.
- **Sensibilidad S-OBS:** repite el análisis individual con las celdas imputadas como faltantes. Las celdas cuya pregunta madre fue imputada, también.
- Cada descripción indica n observado, imputado, no aplicable y faltante.

## 6. Análisis

### 6.1 Descripción general

Cuantitativas y ordinales: media, desviación estándar, mediana, rango intercuartílico, mínimo y máximo. Binarias, nominales y ordinales: frecuencias y porcentajes. MRS: lo mismo para total, dimensiones e ítems, más la distribución de la severidad.

### 6.2 Características individuales frente al MRS (análisis principal)

La prueba depende del tipo de pregunta, no solo de que la variable sea numérica:

| Característica | Resultado continuo (total o dimensión) | `severo_mrs` |
|---|---|---|
| Cuantitativa u ordinal con 3 niveles o más | Spearman; efecto ρ | Mann-Whitney de la característica según severo; efecto r biserial de rangos |
| Binaria | Mann-Whitney; efecto r biserial de rangos (positivo: mayor MRS en «Sí») | χ² 2 × 2; efecto V de Cramér y diferencia de proporciones |
| Nominal | Kruskal-Wallis; efecto ε² | χ²; efecto V de Cramér |

Si en una tabla χ² más del 20 % de las frecuencias esperadas es menor que 5, se usa la prueba exacta de Fisher (2 × 2) o se informa la advertencia.

### 6.3 Segmentos A y B1

**Caracterización:** para cada segmentación y cada una de las 36 características, se informa la descripción por grupo y un efecto entre grupos: η² sobre los códigos en cuantitativas, ordinales y binarias, y V² de Cramér en nominales (las medidas de la Fase 37C). Las pruebas son Kruskal-Wallis para cuantitativas y ordinales, y χ² para binarias y nominales. Las variables usadas por A se informan separadas de las externas. En A, que difieran es esperable y no valida nada. En B1, que difieran trabajo, pareja y ejercicio es una consecuencia de su definición.

**MRS por segmento:** n, media, desviación estándar, mediana, rango intercuartílico e intervalos bootstrap de la media y la mediana por grupo, más el porcentaje con `severo_mrs` y su intervalo de Wilson. Entre grupos: Kruskal-Wallis con ε² para total y dimensiones, y χ² con V de Cramér para severidad en 4 clases y `severo_mrs`. Como análisis secundario, Mann-Whitney por pares para el total, con Holm dentro de cada segmentación.

**Correspondencia:** tabla A × B1, ARI y porcentaje de coincidencia con alineación de etiquetas.

### 6.4 Información que se pierde al segmentar

- Proporción de la varianza del MRS que queda dentro de los segmentos (1 − η²), para A, B1 y las 20 celdas de las tres preguntas.
- Para cada característica: asociación marginal con `mrs_total` frente a la asociación dentro de los segmentos. Es la media de las asociaciones dentro de cada grupo, ponderada por n, con el mismo tipo de efecto.

### 6.5 Ítems

Asociación de cada característica con cada ítem, con las mismas pruebas. Es exploratoria y se presenta como mapa.

## 7. Familias y control de comparaciones múltiples

Benjamini-Hochberg (FDR) dentro de cada familia, con q < 0,05. Las familias están fijadas aquí:

| Familia | Contenido | Pruebas | Carácter |
|---|---|---|---|
| F1 | 36 características × `mrs_total` | 36 | Principal |
| F2 | 36 características × 3 dimensiones | 108 | Secundaria |
| F3 | 36 características × `severo_mrs` | 36 | Secundaria |
| F4 | 36 características × 11 ítems | 396 | Exploratoria |
| F5 | {A, B1} × {total, somática, psicológica, urogenital, severidad 4 clases, `severo_mrs`} | 12 | Principal para segmentos |
| F6-A y F6-B1 | 36 características entre los grupos de cada segmentación | 36 + 36 | Descriptiva |
| F7 | Pares de grupos en `mrs_total`, por segmentación | 6 + 6 | Secundaria, con Holm |

Las sensibilidades no forman familia: son descriptivas y se comparan con el resultado principal.

## 8. Magnitudes de efecto

Los valores p no bastan; cada resultado lleva su efecto y su n.

| Medida | Despreciable | Pequeña | Moderada | Grande |
|---|---|---|---|---|
| ρ de Spearman, r biserial de rangos, V de Cramér (tablas 2 × 2) | < 0,10 | 0,10 a 0,29 | 0,30 a 0,49 | ≥ 0,50 |
| η², V², ε², V² de tablas mayores | < 0,01 | 0,01 a 0,059 | 0,06 a 0,139 | ≥ 0,14 |

- **Asociación destacada:** q < 0,05 y efecto al menos pequeño.
- **Diferencia importante entre segmentos:** efecto de al menos 0,06, el umbral de la Fase 37C.
- **Distribución semejante:** efecto menor que 0,01.

**Incertidumbre:**

- Intervalos bootstrap percentil del 95 % con 2.000 remuestreos y semilla 42, para los efectos de F1 y F5 y para medias y medianas por grupo.
- Intervalos de Wilson para proporciones.

## 9. Sensibilidades (fijadas de antemano)

| Código | Qué cambia | Se aplica a |
|---|---|---|
| S-MARGEN | Excluye a quienes tienen margen de A menor que 0,10. Además, serie con cortes 0,05, 0,10, 0,15 y 0,20 | F5, A y B1 sobre el mismo subconjunto |
| S-OBS | Celdas imputadas como faltantes (sección 5) | F1 y caracterización |
| S-SIN-IMP3 | Excluye a quienes tienen imputada alguna de las tres preguntas | F5 |
| S-SIN-IMP29 | Solo participantes sin ninguna imputación en las 29 variables de A | F5 de A (n pequeño, se informa así) |
| S-PARTICIONES | Particiones ya guardadas, sin reajustar: `P2_c08_km_k4`, `P2_c16_km_k4`, S-SOLAPE y S-ORD (ridit) con 12 componentes y k = 4 | Efecto global del MRS |
| S-B1CV | Etiquetas B1 con validación cruzada del complemento | F5 |
| S-SIN9 | Total sin el ítem 9 (problemas sexuales) y urogenital sin el ítem 9, por solapamiento conceptual | `tiene_actividad_sexual`, `tiene_pareja`, A y B1 |

Las particiones de S-PARTICIONES no compiten con A: solo muestran si la descripción depende de la configuración.

## 10. Riesgos de circularidad declarados

- `tiene_actividad_sexual` y `tiene_pareja` se solapan con el ítem 9 (problemas sexuales) y con la dimensión urogenital.
- `distension_abdominal` y `evacuacion_intestinal` son síntomas digestivos y pueden relacionarse con la dimensión somática.
- `estres_entorno_laboral` y `sobrecarga_fisica_emocional` pueden ser consecuencia de los síntomas o compartir su causa.
- `etapa_menopausica` y `edad` están relacionadas entre sí; ninguna se ajusta por la otra en esta fase.
- Las diferencias entre segmentos en las variables con las que se construyeron no validan los segmentos.
- Toda asociación con el MRS en datos sintéticos refleja lo que la simulación programó.

## 11. Reglas de no selección

- El MRS no se usa para elegir segmentación, configuración, número de grupos ni variables.
- No hay criterio de «ganador» entre A y B1. La comparación solo describe.
- La nota para las Fases 38 y 39 propone candidatas por su significado y por su calidad de datos (frecuencias, faltantes, redundancia), no por haber resultado asociadas aquí.
- Los grupos se llaman Grupo 0, Grupo 1, Grupo 2 y Grupo 3, con la numeración histórica. No se les asignan nombres clínicos.

## 12. Limitaciones previstas

Datos sintéticos, análisis no ciego respecto de fases anteriores, ausencia de un criterio externo real, imputaciones de la limpieza (sin marca por participante en diabetes y previsión), IMC observado solo en la mitad, módulos con poblaciones parciales, muchas comparaciones y efectos marginales sin ajuste por otras variables.

## 13. Reproducibilidad y recursos

Semilla 42. Un hilo por biblioteca numérica y como máximo 2 procesos, con vigilancia de memoria. Los resultados se guardan por etapas para poder reanudar. Todo se escribe en `analisis/fase37/37D_caracterizacion/`.

## 14. Fuera de alcance

No se ejecutan Apriori, FP-Growth ni otros algoritmos de reglas. No se inician las Fases 38, 39 ni 40. No se modifica la plataforma, no se hace commit y no se hace push.
