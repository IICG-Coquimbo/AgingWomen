# Corrección de las Fases 35A y 35B: de 34 a 33 variables

*Registrado el 03-11-2026, antes de escribir resultados. Complementa `protocolo_revision_35b.md` y `adenda_50000_permutaciones.md`, que se conservan sin cambios.*

## 1. Decisión

`usa_medicamentos_diabetes` queda fuera de todo el modelado desde la Fase 35: preprocesamiento, análisis entrópico, Random Forest y fases posteriores de segmentación. Se aplica sin excepciones el criterio de dominancia de la Fase 34D: se excluye toda variable con más de 85 % en una categoría. La variable sigue en el conjunto limpio y en el EDA histórico.

**Revierte** la excepción del 28-10-2026 (`CONSERVAR_PESE_A_DOMINANCIA` en `preprocesamiento/configuracion.py`), que la había conservado como variable de control.

## 2. Qué no cambia

Participantes, valores de las otras variables, limpieza e imputación, codificación, poblaciones (529, 287 y 239), semillas, número de permutaciones, criterio exploratorio q < 0,10 y reglas de FCBF. `doble_carga` y `prevision` siguen excluidas; `sobrecarga_fisica_emocional` y `cantidad_personas_cuida` siguen incluidas.

Las **33 variables** son el conjunto inicial de la Fase 36. FCBF sigue siendo informativo y no elimina variables.

## 3. Reutilización de resultados

**No se ejecuta ninguna permutación nueva.** El programa lo garantiza desactivando la función de permutación durante el cálculo.

| Elemento | Tratamiento | Motivo |
|---|---|---|
| SU y n de cada variable | Se recalculan desde los datos, sin azar, y deben coincidir con lo guardado | Solo dependen de la variable y de su población |
| k y p de cada variable | Se reutilizan de los archivos | Se obtuvieron sobre los mismos datos |
| k y p de cada par | Se reutilizan de los archivos | Ningún par incluye la variable excluida |
| q de las variables | Se recalcula con Benjamini-Hochberg sobre 33 | Cambió la familia |
| q de los pares | Se recalcula y debe coincidir | La familia de pares no cambia si no cambian las relevantes |
| FCBF | Se vuelve a recorrer con las funciones congeladas | Es determinista |
| ρ, IC bootstrap, Kruskal-Wallis y categorías | Se reutilizan | No dependen de la familia |
| q de ρ | Se recalcula sobre 32 pruebas | Cambió la familia; una variable es nominal y no tiene ρ |
| Clase descriptiva | Se recalcula | Depende de q y de q de ρ |
| Incertidumbre Monte Carlo de q | Se recalcula con las mismas claves de semilla | Propaga los p por Benjamini-Hochberg; no permuta datos |

### Condición sobre las semillas

La semilla de cada variable depende de su **posición alfabética** en la lista. Al quitar la diabetes, `usa_medicamentos_presion` pasaría del índice 32 al 31 y `vasos_agua_dia` del 33 al 32. Volver a permutar con 33 variables daría a esas dos otra corriente de números aleatorios y otro p, solo por el cambio de posición. Por eso se reutilizan los k guardados y se mantiene el mapa de índices de las 34 en el cálculo.

## 4. Conjunto de datos

Se crea `datos/analitico/dataset_fase35_33_variables.csv`, igual a `dataset_fase35.csv` sin la columna excluida. No se ejecuta la limpieza ni se regenera nada. Una comparación automática exige que las demás columnas sean idénticas, texto a texto.

Se conservan como columnas `prevision` y `doble_carga`, porque ya estaban y no son elegibles, según indica `fase35a/predictores_elegibles_33.csv`. `sobrecarga_fisica_emocional` tampoco se agrega: se sigue incorporando en memoria desde el conjunto limpio.

## 5. Límite de compatibilidad de Monte Carlo

Se mantiene |z| ≤ 3,19, fijado en la adenda con 34 pruebas. Con 33 el límite sería casi el mismo y más estricto por una diferencia mínima; ningún |z| se acerca a él.

## 6. Detenciones

El programa se detiene sin escribir si: cambia una SU o un tamaño guardado; la dominancia de la variable excluida no supera 85 %; otra de las 33 supera 85 % en las 529; cambia el grupo de variables relevantes y faltan pares calculados; una decisión o un par incluye la variable excluida; una columna del conjunto de datos difiere; o cambia un archivo vigilado.

Si cambiara el grupo de variables relevantes, habría que permutar pares nuevos, lo que requiere autorización.

## 7. Límites

Sin regenerar conjuntos de datos, sin cambiar `configuracion.py`, sin ejecutar Random Forest, sin avanzar a la Fase 36, sin commit, sin push y sin publicar.
