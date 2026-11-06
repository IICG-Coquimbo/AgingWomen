# Complemento de la Fase 35B: estabilidad de la selección con las 33 variables finales

## Revisión metodológica inicial y configuración (registrada antes de ejecutar)

*Registrado el 05-11-2026, antes de ejecutar los 500 remuestreos y después del cierre de las Fases 36 a 39. Es una evaluación **retrospectiva**: no se ejecutó antes de esos análisis y no los modifica. El SHA-256 de este archivo queda en `protocolo/sello.json`.*

Solo se ejecutaron dos remuestreos de prueba, los números 0 y 1, para medir el tiempo. Sus resultados no se guardaron. Esos mismos remuestreos se recalculan dentro de la corrida completa, con la misma semilla.

### 1. Archivos revisados

| Archivo | Qué se verificó |
|---|---|
| `analisis/resultados/usuaria/log_seleccion_fase35b.txt` | Corrida histórica del 02-11, 21:14; commit 745d689; semilla 42; 5.000 permutaciones; 500 remuestreos; 11 procesos; **30 candidatas**; 0 relevantes con q < 0,05; remuestreos en 1.510 s |
| `estabilidad_remuestreos.csv` | 1.000 filas: 500 remuestreos × 2 variantes |
| `estabilidad_fcbf.csv` | 60 filas: **30 candidatas** × 2 variantes; incluye `doble_carga` |
| `estabilidad_global.csv` | Nogueira 0,121 (adaptado) y 0,126 (estándar); tamaño medio 3,14 y 2,30 |
| `figuras/seleccion_35b/estabilidad_seleccion.png` | **30 barras**, contadas una por una, solo de la variante adaptada. La cifra de 35 no aparece en ningún archivo de la corrida; la cuenta 30 + 4 de control + `prevision` = 35 corresponde al total de predictoras del protocolo original, no a la figura |
| `reunion_2026-11-03/revision_33_variables/log_revision_33.txt` y `protocolo_revision_33.md` | Exclusión de `usa_medicamentos_diabetes`; **ninguna permutación nueva**; ningún remuestreo |
| `protocolo_fase35b.md` §7 | Procedimiento de estabilidad |
| `protocolo_revision_35b.md` | Configuración vigente: 34 variables, 3 poblaciones, q < 0,10 y Etapa 3 |
| `preprocesamiento/fcbf.py`, `entropia.py` y `estabilidad.py`; `complementario_cuidados.py`; `revision_35b_reunion_1103.py`; `revision_33_variables.py` | Código de SU, permutación, BH, FCBF, bootstrap e indicadores |
| `revision_33_variables/fase35a/predictores_elegibles_33.csv` | Lista de 33 |
| `revision_33_variables/permutaciones_10000` y `permutaciones_50000` | Selección definitiva |
| `fase36/configuracion_fase36.py` | Relación con la Fase 36: la relevancia se lee de `permutaciones_50000/relevancia_33.csv`; las dos laborales y la sobrecarga son módulos aparte (`MODULOS`) |

### 2. Qué son las 33

**33 es el número de candidatas elegibles**, no el de seleccionadas.

| Cantidad | Valor | Detalle |
|---|---:|---|
| Candidatas de la selección (familia BH) | **33** | 30 generales (n = 529), 2 laborales (n = 287) y la sobrecarga (n = 239) |
| Relevantes con q < 0,10 (10.000 y 50.000) | 6 | `dias_ejercicio_semana`, `frecuencia_bajo_impacto`, `frecuencia_fuerza`, `imc`, `lugar_trabajo_comprensivo`, `trabaja_actualmente` |
| Seleccionadas, FCBF adaptado (definitiva) | **4** | `frecuencia_fuerza`, `imc`, `lugar_trabajo_comprensivo`, `trabaja_actualmente` |
| Seleccionadas, FCBF estándar | 2 | `frecuencia_fuerza`, `lugar_trabajo_comprensivo` |
| Variables de la matriz global de la Fase 36 | 30 (P1) / 29 (P2) | Las 30 generales; P2 no incluye el IMC. Las 3 de módulos van en matrices aparte |
| Columnas codificadas de P2 | 33 | 29 variables, con `quien_prepara_comidas` convertida en 5 indicadoras: 28 + 5 = 33 |
| Componentes del PCA de A | 12 | `P2_c12_km_k4` |

Que las candidatas y las columnas de P2 sean ambas 33 es una **coincidencia**: son conjuntos distintos.

**Punto clave:** según `protocolo_revision_33.md` §2, «FCBF sigue siendo informativo y no elimina variables». Las variables de la Fase 36 **no dependen** del resultado de la selección.

### 3. El procedimiento histórico (verificado en el código)

1. **Remuestreo:** es un bootstrap en sentido estricto. Es **con reemplazo y estratificado por `severo_mrs`**: dentro de cada clase se sortean tantas personas como tiene la clase, 281 severas y 248 no severas (`fcbf.indices_bootstrap`). Cada muestra tiene 529 filas, con personas repetidas.
2. **Generación y semillas:** `SeedSequence(42, spawn_key=(1, i, 0, 0))`, donde el análisis es `ID_ESTABILIDAD = 1`, i es el remuestreo y el tipo 0 corresponde al bootstrap.
3. **Repetidas:** se tratan como filas distintas, también en las permutaciones. Esto es una limitación declarada en el protocolo 35B §9: puede favorecer la significancia, por lo que la estabilidad es descriptiva.
4. **Poblaciones:** la máscara laboral (y ahora la de la sobrecarga) acompaña a cada persona remuestreada, así que su tamaño varía.
5. **Procedimiento completo en cada remuestreo:**
   - SU y p por permutación (5.000) de cada candidata con `severo_mrs`;
   - BH sobre la familia;
   - relevancia;
   - pares de relevantes con 5.000 permutaciones y BH;
   - FCBF en dos variantes.
6. **SU y FCBF:** SU es la medida de relevancia y redundancia; FCBF recorre las relevantes. «Seleccionada» significa relevante y no eliminada por FCBF.
7. **Frecuencias:** se calcula el % de remuestreos en que la variable es «seleccionada», «no relevante» o «redundante», y la variable que más veces la eliminó. Las no seleccionadas aparecen con 0 %.
8. **Permutaciones:** son internas a cada remuestreo, no una etapa aparte. La corrida histórica usó 5.000 en todas.

### 4. Configuración de este complemento

| Elemento | Valor | Origen |
|---|---|---|
| Datos | `datos/analitico/dataset_fase35.csv` con las poblaciones de `comprobar_datos_reales` (529, 287, 239) | Igual que la revisión de 33, que comprobó que `dataset_fase35_33_variables.csv` es idéntico salvo por la columna excluida |
| Candidatas | Las 33 de `revision_33_variables.VARIABLES_33` | Definitiva |
| Excluidas | `doble_carga`, `prevision`, `usa_medicamentos_diabetes` y todas las de `C.PROHIBIDAS` (MRS, resultado, auditoría) | Definitiva |
| Discretización | Edad, IMC y horas en los cortes fijos de la 35B (`R.codigos_su`) | Definitiva |
| Objetivo de la SU | `severo_mrs` (MRS ≥ 16) | **El mismo criterio de la selección definitiva**; el MRS no entra como candidata ni como criterio nuevo |
| Familia BH | 33 pruebas, una sola | Definitiva |
| Relevancia | q < 0,10 estricto | Definitiva (revisión 03-11) |
| Pares | Todos los de las relevantes, cobertura común, BH único; adaptado exige q del par < 0,10 | Definitiva |
| FCBF | Etapas 1, 2 y 3 de `complementario_cuidados.seleccionar`; variantes adaptada y estándar | Definitiva |
| Tolerancia | 1e-12 en las comparaciones de SU | Protocolo 35B §12 |
| Remuestreo | Bootstrap estratificado con reemplazo (281/248), `fcbf.indices_bootstrap` | Histórico |
| Remuestreos | 500 | Histórico |
| Permutaciones por remuestreo | **5.000** | Histórico de la estabilidad. No se sustituye por 10.000 ni por 50.000 |
| Semillas | `SeedSequence(42, (1, i, tipo, índice))`, con el **índice alfabético de las 34** (mapa de la revisión de 33) | Ver la nota |
| Procesos | 1 | Restricción de memoria |

**Nota sobre las semillas.** Se usa el mismo identificador de análisis que la corrida histórica (1). Así, **el remuestreo i contiene exactamente las mismas personas que en la corrida del 02-11**, y la comparación queda pareada. Las semillas de permutación usan el mapa de índices de las 34, igual que la configuración definitiva.

**Única función nueva:** `medir_remuestreo`, idéntica a `complementario_cuidados.medir` salvo que lleva i en la clave de semilla. Una prueba exige igualdad exacta con la función original cuando i = 0 y no hay remuestreo.

### 5. Diferencias metodológicas con la corrida histórica

| Elemento | Histórica (02-11) | Complemento (33) |
|---|---|---|
| Candidatas | 30 (con `doble_carga`; sin sobrecarga; edad, IMC, trabajo y diabetes fuera, como control) | 33 (sin `doble_carga` ni diabetes; con sobrecarga; edad, IMC y trabajo compiten) |
| Familia BH | 30 | 33 |
| Relevancia | q < 0,05 | q < 0,10 |
| Pares, variante adaptada | q < 0,05 | q < 0,10 |
| Etapa 3 (sobrecarga) | No | Sí |
| Muestras | — | Las mismas (misma semilla de bootstrap) |

Cambian a la vez el universo, el umbral y una etapa. Por eso **los porcentajes no se comparan como una diferencia causada por una sola cosa**. Solo se describen lado a lado, en las 29 variables comunes.

### 6. Resultados que se informarán (fijado antes de ver resultados)

- **Por variable y variante:**
  - remuestreos y % seleccionada, no relevante y redundante;
  - % relevante (q < 0,10), es decir, la frecuencia del filtro SU;
  - eliminadora más frecuente;
  - estado en la selección definitiva.
- **Global:** Nogueira con IC 95 % (`estabilidad.nogueira`), Jaccard promedio, distribución del tamaño de la selección y Jaccard de cada remuestreo con la selección definitiva.
- **Bandas:** se usan las del protocolo 35B (≥ 80 %, 50–79 %, < 50 %), **solo descriptivas**. No se crean umbrales nuevos.
- **Dependencia de personas:** relación entre la selección de cada variable y el número de personas distintas o de trabajadoras de la muestra (descriptiva).

### 7. Prohibiciones

- No se cambian candidatas, umbrales ni parámetros según los resultados.
- No se modifica nada fuera de `analisis/complemento_bootstrap_33/`.
- No se recalculan PCA, FAMD, K-means ni Ward, ni se tocan las etiquetas de A o B1.
- No se toca Django, ni se hace commit o push.
