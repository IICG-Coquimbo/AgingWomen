# Fase 37D: informe de integridad final

- **Protocolo:** huella `f7c8d125aa9181224360c226586eb990779d15776a5adb00a26ac5e54eb326b9`, sellado el 2026-11-05T16:44:19, antes de cualquier asociación con el MRS. La prueba 10 comprueba que todos los resultados son posteriores.
- **Nota posterior:** huella `bf5938d5d393399c22827074d0954c6357c4c6e2a2fab0c198566f866634642b`, sellada el 2026-11-05T17:01:53.
- **Lecturas fuera de la carpeta:** 3405 archivos, casi todos para comparar huellas con los manifiestos protegidos. De ellos, 508 están en `datos/`: 500 son la caché de remuestreos de la Fase 35B, que figura en el manifiesto 34-35 y solo se lee para calcular su huella. Los otros son: `datos/analitico/conjunto_eda.csv`, `datos/analitico/conjunto_eda_usuaria.csv`, `datos/analitico/dataset_fase35.csv`, `datos/analitico/dataset_fase35_33_variables.csv`, `datos/analitico/dataset_fase35b.csv`, `datos/limpio_usuaria/dataset_usuaria_limpio.csv`, `datos/limpio_usuaria/diccionario_variables.csv`, `datos/limpio_usuaria/excluidas.csv`. El análisis usa solo `datos/limpio_usuaria/dataset_usuaria_limpio.csv` y su diccionario. No se leyó ningún archivo del simulador: el gancho de auditoría lo impide. Registro: `integridad/archivos_leidos.csv`.
- **Escrituras fuera de la carpeta:** 0.
- **Memoria:** como máximo un proceso de análisis a la vez, con vigilancia. Registro: `integridad/registro_memoria.csv`.
- **Manifiesto:** `integridad/manifiesto_final.csv`, con la huella de todos los archivos de esta carpeta salvo él mismo.

## Verificación final

- **Fecha:** 2026-11-05T17:10:05.
- **Archivos protegidos:** 3.532 comparados, 0 distintos.
- **Entradas:** iguales al inicio: sí.
- **Git:** HEAD 745d689; cambios en `src/`: 0; cambios fuera de `analisis/`: 0; datos versionados modificados: 0.
- **`__pycache__` en fases protegidas:** 0.

## Restricciones

Se cumplieron todas:

- **Fases y datos:** sin cambios en las Fases 34 a 37C ni en el complemento, en los datos originales ni en los resultados históricos.
- **Modelos:** sin reajustar PCA, FAMD ni K-means, y sin modificar la regla B1.
- **Uso del MRS y del simulador:** sin MRS para elegir y sin la verdad del simulador.
- **Interpretación:** sin nombres clínicos, sin causalidad y sin recomendaciones clínicas.
- **Alcance:** sin reglas de asociación y sin Fases 38, 39 ni 40.
- **Plataforma y git:** sin cambios en Django, sin commit y sin push.
