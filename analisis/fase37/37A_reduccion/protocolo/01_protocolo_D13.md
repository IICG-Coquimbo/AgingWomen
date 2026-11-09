# 1. Estado de este documento

Este protocolo se redactó y se selló con SHA-256 **antes de ajustar PCA o FAMD**. Al sellarlo no existía ningún valor propio, carga ni coordenada de la Fase 37. Fija las reglas de la Fase 37A y deja preestablecidas las de la Fase 37B.

- **Entradas verificadas antes de sellar:** P1 (529 × 34; 29,5047), P2 (529 × 33; 29,0000), F1 (529 × 50; 38,5047), F2 (529 × 49; 38,0000). Coinciden con sus huellas, y el orden de columnas coincide con `orden_columnas.json`. Los 258 archivos de `analisis/fase36/` y los 1.130 del cierre 34-35 están sin cambios. HEAD 745d689.
- **Origen de las reglas:** las marcadas como «encargo» vienen de la responsable del proyecto. Las marcadas como «propuesta» son completadas aquí porque el encargo no las fija, y pueden cambiarse antes de ejecutar la Fase 37B.

# 2. Reglas generales

| Regla | Origen |
|---|---|
| Esta fase no forma clústeres, no selecciona perfiles y no ejecuta K-means ni el método aglomerativo | Encargo |
| El MRS no se lee en la Fase 37A: ni para elegir componentes, ni para evaluar sensibilidades, ni para colorear gráficos | Encargo |
| Las matrices no se vuelven a escalar. P1 y F1 conservan el peso reducido del IMC | Encargo |
| Ningún eje se interpreta como severidad o riesgo clínico. Cada dimensión se describe solo por las características que la componen | Encargo |
| Un porcentaje acumulado de 50 a 90 % es una referencia descriptiva, no un criterio de selección | Encargo |
| PCA o FAMD no se declara mejor por la cantidad absoluta de inercia explicada | Encargo |
| La Fase 37A no abre ningún archivo de `datos/`. Un gancho de auditoría lo registra | Propuesta |

# 3. Número de componentes

**Candidatos:** 2, 3, 5, 8, 12, 16 y 20, sin superar el rango efectivo de cada matriz.

En la Fase 37A **no se elige** un número de componentes: se generan coordenadas para todos los candidatos. La elección corresponde a la Fase 37B, por los criterios de la sección 8.

# 4. Cálculo de PCA y FAMD

| Aspecto | Regla | Origen |
|---|---|---|
| Algoritmo | `sklearn.decomposition.PCA` con `svd_solver='full'`, sin escaladores nuevos | Encargo |
| Rango efectivo | `numpy.linalg.matrix_rank` con su tolerancia por defecto. Se conservan solo esos componentes | Propuesta |
| Valores propios | `explained_variance_ × 528/529` (convención n), en todos los escenarios | Encargo |
| Signo de los ejes | El que entrega scikit-learn 1.6.1, guardado en los artefactos. Es arbitrario y no se interpreta | Propuesta |
| Coordenadas | `(Z − media) · V`, con `V` y la media guardadas. Para nuevas participantes se aplica primero el transformador de la Fase 36, sin recalibrar | Propuesta |

**Medidas descriptivas** (todas fijadas de antemano; propuesta):

- **Carga:** `V × √λ`, la covarianza entre la columna y el eje.
- **Correlación:** carga dividida por la DE de la columna. En IMC, esa DE es √0,5047.
- **Contribución de columna:** `V² × 100`; suma 100 % en cada eje.
- **Contribución de variable:** suma de sus columnas. En una variable categórica de FAMD equivale a `η² / λ`, y en una cuantitativa a `r² / λ` (`v·r² / λ` en IMC). Se comprobará esa igualdad.
- **Contribución de bloque:** suma de sus variables, por eje y acumulada hasta cada candidato, con los ejes ponderados por λ.

# 5. Orden de las cinco ordinales categóricas

Se calcula el baricentro de cada nivel (media de coordenadas de quienes lo tienen) en los cinco primeros ejes, con los grupos activos de FAMD. Regla fija:

- En cada eje, el orden se **conserva** si los baricentros son estrictamente monótonos en el orden del instrumento, en cualquiera de los dos sentidos.
- Se evalúa primero el eje donde la variable tiene mayor `η²`.
- Una curva no monótona en un eje secundario no se considera por sí sola una ruptura, porque un eje posterior puede recoger la parte curva de un mismo gradiente. Se informa como relación no lineal.
- No se corrige nada: es un resultado descriptivo.

# 6. Referencia frente al ruido (adición propuesta)

El encargo no la pide. La agrego porque las asociaciones son débiles (424 de 435 pares bajo |0,2|) y un gráfico de sedimentación por sí solo no indica si un eje supera lo esperable por azar.

Análisis paralelo: 200 permutaciones con semilla 42. En cada una se permuta de forma independiente cada variable original (las indicadoras de una variable se mueven juntas), y se obtiene el percentil 95 de cada valor propio. Es **descriptivo**: no selecciona componentes ni reduce la lista de candidatos.

# 7. Sensibilidades

Cada variante se ajusta aparte. No se reemplazan los escenarios principales ni se modifican las matrices de la Fase 36. No se compara varianza absoluta entre representaciones de distinta escala. Se usan medidas relativas o basadas en las filas:

| Medida | Definición |
|---|---|
| Porcentaje acumulado | Por candidato, dentro de cada variante |
| Componentes para 50 a 90 % | Dentro de cada variante |
| Similitud de subespacio | Media de cos² de los ángulos principales entre las coordenadas de filas de la base y de la variante, para k = 2, 3, 5, 8, 12, 16 y 20. 1 = mismo subespacio |
| Correlación por eje | Máxima \|r\| entre cada uno de los 5 primeros ejes de la base y los ejes de la variante |

**Reglas por variante:**

- **S-TRA, S-CUI y S-EJE:** se ajusta en las filas de referencia de esa sensibilidad (507, 508 y 454), con su matriz preparada. Las participantes marcadas se proyectan con los parámetros congelados. Ajuste y proyección se guardan e informan por separado. El cambio de población puede alterar la estimación, y así se informa.
- **Desplazamiento de proyección:** se alinea la variante con la base mediante Procrustes ortogonal en las filas de ajuste, y se mide la distancia de las filas proyectadas, relativa a la dispersión de las filas de ajuste.
- **S-BLOQUE:** usa los multiplicadores de `pesos_bloques.json`.
- **S-BLOQUE-SA (variante nueva, sin amplificar el IMC):** en P1 y F1, la columna IMC conserva multiplicador 1, y los otros siete bloques se igualan entre sí con la inercia restante. La inercia global se conserva. El bloque de medidas queda deliberadamente fuera de la igualación. No hace falta en P2 ni F2, que no tienen IMC.
- **S-EDAD y S-SOLAPE:** se omiten las columnas indicadas en el catálogo, sin reescalar.

**Cambio relevante (propuesta orientativa):** similitud de subespacio por debajo de 0,80 en k = 5, 8 o 12 se señala para revisión en la Fase 37B. No descarta nada automáticamente.

# 8. Reglas preestablecidas para la Fase 37B

Esta fase no las ejecuta.

| Aspecto | Regla | Origen |
|---|---|---|
| Número de clústeres | k = 2 a 8 | Encargo |
| K-means | Múltiples inicializaciones (`n_init = 50`), semilla 42 | Encargo; 50 es propuesta |
| Aglomerativo | Enlace Ward, distancia euclidiana | Encargo |
| Tamaño mínimo | 5 % de las participantes (27 personas), solo orientativo. Un clúster pequeño no se elimina automáticamente ni se declara sin interés | Encargo |
| Calidad | Silueta, Davies-Bouldin y Calinski-Harabasz | Encargo |
| Estabilidad | 30 remuestreos del 80 %, sin reemplazo, semilla 42 | Encargo; «sin reemplazo» es propuesta |
| Concordancia | ARI, calculado sobre participantes compartidas | Encargo |
| Tamaños | Tamaño mínimo, máximo y equilibrio de los grupos | Encargo |
| IMC | Comparación con y sin IMC: ARI en las 529 y en las 267 con IMC observado, y proporción de IMC imputado por clúster | Encargo; detalle de la Fase 36 |
| Interpretabilidad | Perfil de cada grupo descrito por sus variables, sin MRS para elegir | Encargo |
| Uso del MRS | No se usa para escoger configuración. Una descripción posterior de la severidad por perfil no puede cambiar la elección | Encargo |
| Fase 40 | El método elegido debe permitir asignar a una participante nueva. K-means: centroide más cercano. Ward: centroide más cercano de los grupos formados, informando su concordancia con la asignación original | Encargo; regla de la Fase 36 |

**Combinaciones:** cada escenario (P1, P2, F1, F2) × cada candidato de componentes × dos algoritmos × k = 2 a 8. La referencia sin reducción R0 usa P1 y P2. Gower con enlace promedio queda fuera, salvo que se decida lo contrario, porque no permite K-means ni Ward.

**Cómo se decide (propuesta).** No se usa una puntuación compuesta ni un ganador automático por silueta. Se revisa en este orden:

1. **Estabilidad:** ARI medio de los remuestreos. Orientación: bajo 0,65 es inestable; de 0,65 a 0,80, moderada; sobre 0,80, buena.
2. **Tamaños:** se señalan los grupos bajo el 5 %, sin eliminarlos.
3. **Calidad interna:** las tres métricas, comparadas también con la referencia nula.
4. **Sensibilidades:** cambios de asignación con S-ORD, S-TRA, S-CUI, S-EJE y demás, por ARI en filas compartidas.
5. **Interpretabilidad** de los perfiles.
6. **Utilidad para la Fase 40.**

**Referencia nula (adición propuesta):** las mismas métricas sobre 20 matrices con las variables permutadas, para saber si la calidad supera lo esperable sin estructura. **Si ninguna configuración es estable ni supera la referencia nula, se informa la ausencia de estructura marcada y no se fuerzan perfiles.**

# 9. Criterio de cierre de la Fase 37A

Todas las pruebas de la Parte 8 del encargo deben pasar. Si una falla, se corrige y no se declara cerrada la subfase mientras siga pendiente. La Fase 37B no comienza automáticamente.
