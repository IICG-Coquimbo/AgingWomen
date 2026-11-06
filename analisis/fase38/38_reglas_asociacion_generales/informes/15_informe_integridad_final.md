# Fase 38: informe de integridad final

- **Protocolo:** huella `9f9614115801805f9cde6c1586a8d7571ee44116c18ac7638025a645ee7f5a82`, sellado el 2026-11-05T17:52:08, antes de calcular ninguna regla. La prueba 19 comprueba que todas las reglas y permutaciones son posteriores.
- **Lecturas fuera de la carpeta:** 3.504 archivos, casi todos para comparar huellas con los manifiestos. De ellos, 508 están en `datos/`: 500 son la caché de la Fase 35B, que solo se lee para calcular su huella. Los otros son: `datos/analitico/conjunto_eda.csv`, `datos/analitico/conjunto_eda_usuaria.csv`, `datos/analitico/dataset_fase35.csv`, `datos/analitico/dataset_fase35_33_variables.csv`, `datos/analitico/dataset_fase35b.csv`, `datos/limpio_usuaria/dataset_usuaria_limpio.csv`, `datos/limpio_usuaria/diccionario_variables.csv`, `datos/limpio_usuaria/excluidas.csv`.
- **Simulador:** no se leyó ningún archivo del simulador; el gancho de auditoría lo impide. Registro: `integridad/archivos_leidos.csv`.
- **Escrituras fuera de la carpeta:** 0.
- **Memoria:** un proceso de análisis más el vigilante, con un hilo por biblioteca. Registro: `integridad/registro_memoria.csv`.
- **Manifiesto:** `integridad/manifiesto_final.csv`.

## Verificación final

- **Fecha:** 2026-11-05T18:28:50.
- **Archivos protegidos:** 3.642 comparados por huella, 0 distintos.
- **Entradas:** iguales al inicio: sí.
- **Git:** HEAD 745d689; cambios en `src/`: 0; cambios fuera de `analisis/`: 0; datos versionados modificados: 0.
- **`__pycache__` en fases protegidas:** 0.

## Restricciones

Se cumplieron todas:

- **Fases y datos:** sin cambios en las Fases 34 a 37D ni en los datos originales.
- **Simulador y modelos:** sin la verdad del simulador, sin reajustar PCA, FAMD ni K-means, y sin etiquetas de clustering como antecedentes.
- **Selección:** sin seleccionar por el MRS ni por la significación de la 37D, y sin Random Forest.
- **Interpretación:** sin causalidad y sin recomendaciones clínicas.
- **Alcance:** sin integrar en Django y sin iniciar las Fases 39 ni 40.
- **Git:** sin commit ni push.
