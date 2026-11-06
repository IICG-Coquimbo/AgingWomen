# Fase 37B: informe de integridad

## Comprobaciones

| Elemento | Resultado |
|---|---|
| Históricos | 175 de la Fase 37A (y sin archivos nuevos), 258 de la Fase 36 y 1130 del cierre 34-35, sin cambios |
| Git | HEAD 745d689; nada preparado; los mismos 8 archivos seguidos con cambios previos; src/ y dependencias sin cambios |
| Entradas antes de ajustar | 53 de 53 comprobaciones OK (`integridad/verificacion_entradas.csv`) |
| Protocolo | Sellado antes de los ajustes; cada una de las 420 configuraciones guarda su huella |

## Lecturas durante la ejecución

Un gancho de auditoría de Python registró 98 archivos leídos por los programas de ajuste (`integridad/archivos_leidos.csv`). Ninguno pertenece a `datos/`, y no se usaron `dataset_usuaria_verdad.csv`, `bitacora_suciedad.csv` ni el MRS. `integridad/escrituras_fuera.csv` no registra escrituras fuera de la carpeta de salida.

| Carpeta | Archivos |
|---|---|
| analisis/fase37/37A_reduccion | 74 |
| analisis/fase36/artefactos | 20 |
| analisis/fase36/matrices | 3 |
| analisis/fase36/procedencia | 1 |

`consolidar_37b.py` y `graficos_37b.py` no pasan por ese gancho, pero solo leen resultados de esta subfase, coordenadas de la Fase 37A y `procedencia_celdas.csv` para saber qué IMC está observado.

## Pruebas históricas

La prueba 16 de `37A_reduccion/scripts/pruebas_37a.py` comprueba que `fase37/` tiene solo la carpeta de la Fase 37A. Ahora fallaría si se volviera a ejecutar, porque existe `37B_clustering/`. Es una comprobación válida para el momento de la Fase 37A, y no indica un cambio en sus resultados. No la modifiqué.

## Registro de ejecución

`integridad/registro_ejecucion.csv` guarda el estado y el tiempo de cada trabajo. Una primera ejecución completó las 420 configuraciones, las 34 variantes y las 20 réplicas, sin errores.

## Manifiesto

`integridad/manifiesto_final_37B.csv` guarda la huella de todos los archivos de `37B_clustering/`, y se escribe al final.
