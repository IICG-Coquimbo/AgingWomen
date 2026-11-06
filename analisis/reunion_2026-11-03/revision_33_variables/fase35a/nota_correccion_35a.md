# Corrección de la Fase 35A: `usa_medicamentos_diabetes`

*Generado por `analisis/revision_33_variables.py` el 03-11-2026. Los registros históricos de la Fase 35A no se modifican.*

## Dominancia

«No» concentra **463 de 529 respuestas (87,52 %)**, sobre el umbral estricto de 85 %. Sin las 24 imputaciones de la Fase 34B sería 86,93 %: también lo supera.

## Excepción que se revierte

`preprocesamiento/configuracion.py` y `resultados/usuaria/variables_baja_variabilidad.csv` registran la decisión del 28-10-2026: «conservar (excepción)», por ser factor validado por la profesora el 20-10 y variable de control. La corrección aplica el criterio sin excepciones.

**`configuracion.py` no se modifica,** porque es código congelado. Si alguna vez se ejecuta `preprocesar_fase35.py` sin actualizarlo, la variable volvería a aparecer.

## Las demás variables

Ninguna de las otras 33 supera 85 % en su población. La más alta es `frecuencia_fuerza`, con 84,69 %. Dentro de las cuidadoras llega a 86,61 %; la regla se definió sobre la población de cada variable, de modo que esto solo se informa.

## Conjunto de datos

`datos/analitico/dataset_fase35_33_variables.csv`: 529 participantes y 39 columnas. 39 columnas conservadas son idénticas, texto a texto, a `dataset_fase35.csv`, que no cambió. No se ejecutó la limpieza.

- `prevision` y `doble_carga` siguen como columnas, pero no son elegibles.
- `sobrecarga_fisica_emocional` es elegible, pero no es columna: se incorpora en memoria desde el conjunto limpio. La Fase 36 deberá decidir cómo representarla.
- `dataset_fase35b.csv` es un producto histórico que todavía incluye la variable excluida: **no debe usarse como entrada de la Fase 36.**

La lista de elegibles está en `predictores_elegibles_33.csv`.
