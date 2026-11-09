# Fase 37A: informe de integridad

1130 archivos del cierre 34-35 y 258 de la Fase 36 sin cambios; HEAD 745d689; sin nada preparado; src/ y dependencias sin cambios.

## Comprobaciones

| Elemento | Resultado |
|---|---|
| Fase 36 | 258 archivos iguales a `fase36/integridad/manifiesto_final_36B.csv` |
| Cierre de las Fases 34 y 35 | 1.130 archivos iguales a `cierre_fases_34_35/integridad/manifiesto_despues.csv` |
| Matrices de entrada | SHA-256 iguales a sus huellas de la Fase 36 |
| Protocolo | SHA-256 igual al sello |
| Git | HEAD 745d689; nada preparado; sin commit ni push |
| Archivos seguidos con cambios previos | Los mismos 8 de `analisis/`, de antes de esta fase. No se tocaron |
| Plataforma | `src/` y dependencias sin cambios |

## Lecturas durante el ajuste

Un gancho de auditoría de Python registró 91 archivos leídos por `ejecutar_37a.py` (`integridad/archivos_leidos.csv`). Ninguno pertenece a `datos/`, y no se usaron `dataset_usuaria_verdad.csv`, `bitacora_suciedad.csv` ni el MRS.

| Carpeta | Archivos |
|---|---|
| analisis/fase36 | 89 |
| analisis/fase37 | 2 |

`integridad/escrituras_fuera.csv` no registra escrituras fuera de la carpeta de salida.

## Manifiesto

`integridad/manifiesto_final_37A.csv` guarda la huella de todos los archivos de `37A_reduccion/`, y se escribe al final.
