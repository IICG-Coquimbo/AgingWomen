# Fase 36B: informe de integridad

## Resultado

**1130 de 1130 archivos coinciden** con `cierre_fases_34_35/integridad/manifiesto_despues.csv`, por SHA-256. Ningún archivo histórico cambió.

| Comprobación | Resultado |
|---|---|
| Commit | 745d689 (sin cambios) |
| Archivos preparados para commit | 0 |
| Datasets históricos | Sin cambios (`datos/`, 511 archivos) |
| Shannon, FCBF y Random Forest | Sin cambios y sin ejecutar |
| Plataforma AgingWomen (`src/`) | Sin cambios |
| Diseño 36A (`fase36_diseno/`) | Sin modificar |
| Commit o push | No se hizo |
| Dependencias del proyecto | Sin cambios; `prince` solo en una carpeta temporal |

## Manifiesto de partida, por carpeta

| Carpeta | Archivos |
|---|---|
| `datos/analitico` | 505 |
| `analisis/figuras` | 200 |
| `analisis/revision_correctiva_fase34` | 132 |
| `analisis/reunion_2026-11-03` | 99 |
| `analisis/resultados` | 46 |
| `analisis/random_forest_revision_35b_33_variables` | 41 |
| `analisis` | 40 |
| `analisis/preprocesamiento` | 15 |
| `analisis/complementario_cuidados` | 13 |
| `analisis/eda` | 12 |
| `analisis/complementario_35b_q10` | 8 |
| `analisis/limpieza` | 5 |
| `analisis/simulacion` | 4 |
| `datos/limpio_usuaria` | 3 |

## Archivos leídos por la construcción

Registrados con un gancho de auditoría de Python, no declarados a mano. La verdad del simulador y la bitácora no aparecen, y no hubo escrituras fuera de `analisis/fase36/`.

- `analisis/fase36_diseno/diccionario_codificacion_fase36.csv`
- `analisis/fase36_diseno/matriz_decisiones_variables.csv`
- `analisis/reunion_2026-11-03/revision_33_variables/permutaciones_50000/relevancia_33.csv`
- `analisis/revision_correctiva_fase34/tablas/auditoria_figuras_34D.csv`
- `analisis/revision_correctiva_fase34/tablas/origen_respuestas_34D.csv`
- `datos/analitico/dataset_fase35.csv`
- `datos/limpio_usuaria/dataset_usuaria_limpio.csv`
- `datos/sintetico/dataset_usuaria_sucio.csv`

## Estado de git

**Archivos modificados con seguimiento (8).** Son los mismos 8 de la corrección controlada del cierre; la Fase 36B no agregó ninguno:

- `analisis/eda/informe_multivariado.py`
- `analisis/eda/informe_usuaria.py`
- `analisis/eda/multivariado.py`
- `analisis/eda/univariado.py`
- `analisis/eda/variables.py`
- `analisis/eda_univariado.py`
- `analisis/eda_usuaria.py`
- `analisis/limpieza/informe.py`

**Nuevo en esta fase:** `analisis/fase36/`. El resto de archivos sin seguimiento ya existía.

## Manifiesto de esta fase

- `integridad/manifiesto_fase36.csv`: lo que produce la construcción. Es determinista: dos procesos distintos dan los mismos SHA-256.
- `integridad/manifiesto_final_36B.csv`: toda la carpeta `analisis/fase36/`, incluidos código e informes.

## Nota sobre el verificador del diseño

`fase36_diseno/scripts/verificar_diseno.py` marcará ahora «existe carpeta de implementación». Es esperado, porque su comprobación solo valía antes de la Fase 36B. No se volvió a ejecutar, para no reescribir su registro.
