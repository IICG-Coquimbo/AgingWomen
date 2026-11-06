# 1. Estado de este documento

Este protocolo se redactó y se selló con SHA-256 **antes de ajustar K-means o el método aglomerativo sobre las coordenadas**. Al sellarlo no existía ninguna etiqueta, métrica ni resultado de estabilidad de la Fase 37B. La única medición previa fue de tiempo de cálculo, sobre datos aleatorios generados para ese fin.

Completa la sección 8 del protocolo D-13 de la Fase 37A, sin cambiarla. Cada regla indica su origen: «D-13», «encargo» (el encargo de la Fase 37B) o «propuesta» (completada aquí porque ninguno de los dos la fija).

**Entradas verificadas antes de sellar:** 175 archivos del manifiesto final de la Fase 37A sin cambios; 529 identificadores únicos; coordenadas en el orden de `identificadores.csv`, sin valores faltantes; HEAD 745d689. El `Transformador` de la Fase 36 reproduce las cuatro matrices a partir de las respuestas originales, con diferencia máxima de 4,4e-16.

# 2. Reglas generales

| Regla | Origen |
|---|---|
| Esta fase forma y evalúa clústeres. No elige un modelo definitivo, no caracteriza clínicamente los grupos, no les da nombres y no genera recomendaciones | Encargo |
| El MRS no se lee: ni para formar, ni para evaluar, ni para colorear | Encargo |
| No se vuelve a codificar, imputar ni escalar. Las coordenadas se usan tal como salieron de la Fase 37A | Encargo |
| No se usa GMM ni otro enlace o métrica | Encargo |
| Un número de etiqueta no es un orden: el clúster 0 no significa menos que el clúster 1 | Encargo |
| Todas las etiquetas se guardan junto al identificador de la participante | Encargo |
| No se abre ningún archivo de `datos/`. Un gancho de auditoría lo registra | Propuesta |

# 3. Configuraciones

| Elemento | Valores | Origen |
|---|---|---|
| Espacios con reducción | P1, P2, F1, F2 | Encargo |
| Componentes | 2, 3, 5, 8, 12, 16, 20 | Encargo |
| Número de clústeres | 2 a 8 | Encargo |
| Algoritmos | K-means; aglomerativo con Ward | Encargo |
| Referencia sin reducción | R0-P1 y R0-P2: matrices P1 y P2 completas | D-13 |
| Total | 392 con reducción + 28 sin reducción = 420 | Encargo |

**Identificador:** `<espacio>_c<componentes>_<km|ward>_k<clústeres>`, por ejemplo `F1_c05_km_k3` o `R0P1_cTodas_ward_k4`.

Ningún candidato se elimina antes de evaluarlo.

# 4. Ajuste

| Aspecto | K-means | Aglomerativo | Origen |
|---|---|---|---|
| Implementación | `sklearn.cluster.KMeans` | `sklearn.cluster.AgglomerativeClustering` | Encargo |
| Parámetros | `n_init=50`, `random_state=42`, `algorithm='lloyd'`; lo demás por defecto | `linkage='ward'`, `metric='euclidean'` | Encargo |
| Se registra | Convergencia, iteraciones, inercia interna, tamaños, centroides | Tamaños, parámetros, prototipos | Encargo |
| Hilos | Un hilo por proceso, para que el resultado no dependa del paralelismo | Igual | Propuesta |

**Control adicional (propuesta):** cada K-means se repite con `random_state=43` y se informa el ARI con la solución principal. Sirve para distinguir un óptimo inestable de una inestabilidad causada por la muestra. No participa en ningún criterio.

# 5. Calidad interna y tamaños

- **Silueta:** media, proporción de valores negativos, mínimo, máximo y, por grupo, media, cuartiles, mínimo y máximo.
- **Davies-Bouldin y Calinski-Harabasz:** con sklearn, en el mismo espacio usado por el algoritmo.
- **Comparabilidad:** los valores absolutos no se comparan entre espacios de distinta dimensión o ponderación. Entre espacios se compara mediante la referencia nula de cada configuración.
- **Sin umbrales universales:** no se fija un valor de silueta que declare buena una configuración.
- **Tamaños:** se señala todo grupo con menos de 27 participantes (5 %). No se elimina ni se fusiona. También se informa la razón entre el mayor y el menor, y el equilibrio, medido como entropía de Shannon de los tamaños dividida por log(k).

**Peso del primer eje (propuesta).** Para saber si una agrupación separa sobre todo por actividad física, se calcula qué fracción de la separación entre grupos ocurre en el eje 1 del escenario: `SSB en C1 / SSB total`. En R0 se usa el eje 1 de P1 o P2, según corresponda. Se señala cuando es 0,80 o más. Es una descripción de los ejes, no una exclusión.

# 6. Estabilidad

| Aspecto | Regla | Origen |
|---|---|---|
| Remuestreos | 30, con 423 participantes (80 % de 529, redondeado), sin reemplazo | Encargo |
| Semillas | Los 30 subconjuntos salen de `numpy.random.default_rng(42)` y son los mismos en todas las configuraciones, para que las diferencias no se deban a qué muestra le tocó a cada una. Sus identificadores se guardan | Propuesta |
| K-means en cada remuestreo | `n_init=50`. La semilla sale de `SeedSequence([42, repetición])` | Encargo; derivación propuesta |
| Aglomerativo en cada remuestreo | Se ajusta de nuevo sobre el subconjunto, sin `predict` | Encargo |
| Coordenadas | Las de la Fase 37A: la reducción **no** se recalcula en cada remuestreo | Propuesta |

**Dos medidas, con ARI:**

- **Frente al modelo completo:** etiquetas del remuestreo frente a las del modelo principal, en esas mismas 423 participantes. Hay 30 valores. Parte de la coincidencia viene de que ambos modelos comparten el 80 % de los datos.
- **Entre remuestreos:** para cada uno de los 435 pares, ARI sobre las participantes que ambos comparten. Es la medida más exigente, porque ningún modelo es referencia del otro.

**Resumen:** media, mediana, DE, mínimo, máximo, percentiles 5, 25 y 75, y cantidad de valores por tramo.

**Tramos descriptivos:** bajo 0,65, baja; de 0,65 a 0,80, intermedia; sobre 0,80, alta. Son reglas de trabajo, no estándares. Una media alta no se llama robusta si hay repeticiones inestables, por lo que siempre se informa también el percentil 5 y el mínimo.

**Límite declarado:** como la reducción se ajustó con las 529, estas medidas solo evalúan la inestabilidad del agrupamiento, no la de la reducción.

# 7. Referencia nula

**Hipótesis nula de trabajo:** las variables son independientes entre sí y conservan sus distribuciones marginales. Superarla indica que hay más estructura que con variables independientes. **No prueba que existan clústeres,** porque un conjunto correlacionado sin grupos naturales también puede superarla. Tampoco es una prueba sobre la población.

**Construcción de cada una de las 20 réplicas:**

1. Se parte de la tabla de variables generales previa a la reducción, reconstruida desde `fase36/procedencia/procedencia_celdas.csv`.
2. Cada variable se permuta por separado entre participantes, con semilla `SeedSequence([42, 1000 + réplica, posición de la variable])`. Cada frecuencia se mueve junto con su pregunta madre, para conservar su lógica de salto.
3. Se aplica el `Transformador` congelado de la Fase 36 a cada escenario. Las indicadoras de una variable quedan juntas de forma natural. Sin reestandarizar: las marginales no cambian, y por eso los parámetros siguen siendo válidos. Una prueba lo comprobará.
4. PCA o FAMD se recalculan con el método de la Fase 37A.
5. Se ajustan las 420 configuraciones con las mismas reglas.
6. Se calculan las mismas métricas de calidad y estabilidad, con los mismos 30 subconjuntos.

No se permutan etiquetas de clúster ni columnas de coordenadas.

**Comparación por configuración:** media y DE de la réplicas, `z = (observado − media) / DE`, y `p = (1 + réplicas iguales o mejores) / 21`. El mínimo posible es 1/21 ≈ 0,048. En Davies-Bouldin se invierte el sentido.

**Búsqueda múltiple.** Con 420 configuraciones, unas 20 quedarían por encima de las 20 réplicas por puro azar, por lo que una mejora aislada no es evidencia. Dos controles, por métrica:

- **Máximo de la búsqueda:** el mayor z observado de las 420 se compara con el mayor z de cada réplica, calculado con media y DE de las otras 19.
- **Conteo:** cuántas configuraciones superan a todas las réplicas, comparado con cuántas de cada réplica superan a las otras 19.

Con 20 réplicas estos resultados son exploratorios: `p` no baja de 0,048.

# 8. Sensibilidades

**Cobertura:** las 34 variantes de la Fase 37A × 7 componentes × 2 algoritmos × 7 valores de k = 3.332 ajustes, con los mismos parámetros. Evaluarlas todas evita elegir antes de tiempo una «configuración de referencia». No se agregan variantes nuevas.

| Familia | Variantes | Lectura |
|---|---|---|
| Codificación | S-ORD, S-FAMD, S-RARA | Perturbación metodológica |
| Población | S-TRA, S-CUI, S-EJE | Cambia quién participa en el ajuste |
| Variables | S-EDAD, S-SOLAPE | Se quitan columnas |
| Ponderación | S-BLOQUE, S-BLOQUE-SA | **Otra pregunta, no un fallo de robustez** |

- **Base comparable:** mismo escenario, componentes, algoritmo y k.
- **Comparación:** ARI solo en participantes presentes en ambas.
- **Ajuste y proyección:** en S-TRA, S-CUI y S-EJE, el agrupamiento usa solo las filas de ajuste. Las excluidas se asignan al prototipo más cercano del modelo de la variante, y se informa aparte: ARI de ajuste y ARI de proyectadas. Con 21 a 75 filas, este último es poco preciso.
- **Tamaños:** se registran, con los grupos bajo 5 % de las filas de ajuste.

# 9. Comparaciones entre configuraciones

ARI en las 529 para el mismo número de componentes, algoritmo y k:

- **Con y sin IMC** (P1-P2, F1-F2, R0): en las 529 y en las 267 con IMC observado. También la proporción de IMC imputado por clúster en los escenarios con IMC (D-13).
- **PCA y FAMD** (P1-F1, P2-F2).
- **K-means y aglomerativo.**

# 10. Asignación de participantes nuevas

| Aspecto | Regla | Origen |
|---|---|---|
| K-means | Centroide más cercano, con los centroides guardados | Encargo |
| Aglomerativo | Centroide más cercano de los grupos formados. **No equivale a la asignación jerárquica original** | Encargo |
| Acuerdo | Porcentaje de coincidencia y ARI de esa regla frente a las etiquetas originales, en las 529 | Encargo |
| Fuera de muestra (propuesta) | En cada remuestreo, las 106 no usadas se asignan a los prototipos de ese modelo, y se comparan con el modelo principal por ARI | Propuesta |
| Incertidumbre | Distancia al prototipo más cercano; margen `1 − d1/d2`; y percentil 95 de la distancia dentro de cada grupo, para señalar casos alejados | Encargo; medidas propuestas |

Flujo previsto para una participante nueva: `Transformador` de la Fase 36 → `proyectar` de la Fase 37A → prototipo más cercano. No se integra con Django.

# 11. Qué pasa a la Fase 37C (propuesta)

**No se elige un ganador.** Se usa una regla escrita antes de ver resultados para armar una lista de comparación detallada. No hay puntuación compuesta.

Una configuración entra a la lista si cumple **todas** estas condiciones:

1. **Estabilidad:** media de ARI frente al modelo completo y media de ARI entre remuestreos, ambas en 0,65 o más.
2. **Frente a la nula:** en silueta y en ARI entre remuestreos, supera a las 20 réplicas (`p` = 1/21).

Después se informa de cada una, sin excluir por ello:

- Si tiene grupos bajo 5 %.
- Si el peso del primer eje es de 0,80 o más.
- Si tiene repeticiones inestables (percentil 5 bajo 0,65).
- El ARI mediano por familia de sensibilidad.
- El acuerdo de la regla de prototipos.

Si la lista supera las 12 configuraciones, se muestran por grupos (método de reducción × algoritmo × k), y en cada grupo la de mayor ARI entre remuestreos. La lista completa queda en una tabla.

**Si ninguna cumple las condiciones,** se informa que no hay evidencia suficiente de agrupaciones estables y diferenciadas, y no se fuerzan perfiles. Las configuraciones menos débiles pueden mostrarse aparte, rotuladas como tales.

# 12. Ejecución

- Los trabajos se guardan uno a uno, junto con la huella de sus entradas y de este protocolo. Al reanudar, se omite solo lo que ya esté completo y coincida.
- La semilla depende de la configuración o réplica, no del orden de ejecución.
- Una ejecución parcial no se presenta como completa. Si algo no se pudiera terminar, se registra exactamente qué falta y la subfase no se cierra.

# 13. Interpretación

Las 529 participantes son sintéticas y sus asociaciones vienen de una simulación. Los grupos no son diagnósticos ni niveles de riesgo. Un algoritmo puede dividir datos aunque no exista una estructura natural. Una silueta o una estabilidad altas no garantizan utilidad clínica ni perfiles integrales.

# 14. Criterio de cierre

Deben estar completas las 420 configuraciones, las 20 réplicas y las 3.332 sensibilidades, y deben pasar todas las pruebas de la Parte 12 del encargo. Si una falla, se corrige y la subfase no se declara cerrada mientras siga pendiente. La Fase 37C no comienza automáticamente.
