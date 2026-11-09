# Random Forest como análisis complementario de la Fase 35B, con 33 variables

*Registrado el 03-11-2026, después de conocer los resultados de Shannon y antes de entrenar cualquier modelo con los datos reales. Actualiza `analisis/random_forest_revision_35b/protocolo_random_forest_revision_35b.md`, que quedó preparado sin ejecutarse y se conserva sin cambios.*

## 1. Carácter y objetivo

Análisis **complementario y exploratorio**. Evalúa qué características ayudan a predecir `severo_mrs` cuando se consideran conjuntamente y compara ese aporte con Shannon (SU, 10.000 y 50.000 permutaciones, q < 0,10).

No reemplaza a Shannon ni a FCBF. **No elige ni elimina variables para la Fase 36.** Como los resultados de Shannon ya se conocían, este análisis no es independiente de ellos. Los datos son sintéticos: los resultados describen este conjunto y no demuestran relaciones causales, generalización a mujeres reales ni validez clínica.

## 2. Cambios respecto de lo preparado

| Elemento | Preparado | Ahora | Motivo |
|---|---|---|---|
| Entrada | `dataset_fase35.csv` | `datos/analitico/dataset_fase35_33_variables.csv` | Indicación de la usuaria; se comprueba que solo difiere en la columna excluida |
| Carpeta | `random_forest_revision_35b/` | `random_forest_revision_35b_33_variables/` | Carpeta independiente |
| Grupos | Actividad, trabajo, cuidados | Agrega «Días y bajo impacto» | Pregunta de redundancia entre ambas |
| Retirada de variables | 4 modelos | Agrega `B_sin_dias_bajo_impacto` | La misma pregunta |
| Imputaciones de 34B | Declaradas como limitación | Revisadas y con sensibilidad (sección 7) | Indicación de la usuaria |

**No cambian:** parámetros, semillas, particiones, 200 permutaciones de etiquetas, reglas de lectura y clasificaciones.

## 3. Datos

- **Objetivo:** `severo_mrs`; 1 = MRS total ≥ 16. Se exige 529 mujeres, 281 severas y 248 no severas.
- **Conjuntos limpio y sucio:** solo para identificar respuestas observadas, celdas imputadas y la población de sobrecarga.
- **Versión verdadera del simulador:** no se lee. Los efectos programados solo se citan al discutir.
- **`dataset_fase35b.csv`:** no se usa.

### Predictores prohibidos
Identificadores, preguntas del MRS, `mrs_total`, `severidad_mrs_4`, `severo_mrs`, `prevision`, `doble_carga`, `usa_medicamentos_diabetes`, `etapa_menopausica`, variables menstruales, indicadores de imputación y `configuracion.PROHIBIDAS`. El programa se detiene si alguna entra en un modelo. Además, se comprueba sin entrenar que ningún predictor tenga |ρ de Spearman| ≥ 0,5 con `mrs_total`.

## 4. Poblaciones

| Población | n | Severas | Definición |
|---|---:|---:|---|
| General | 529 | 281 | MRS completo |
| Laboral | 287 | 166 | Las mismas de la revisión entrópica; no son todas las trabajadoras (309) |
| Cuidadoras | 239 | 136 | Cuidadoras con sobrecarga observada |

**«No aplica» nunca es cero ni se imputa.** Las variables laborales solo entran con las 287 y la sobrecarga solo con las 239.

## 5. Modelos principales

| Modelo | Población | Variables | Contenido |
|---|---|---:|---|
| A | 529 | 3 | `edad`, `imc`, `trabaja_actualmente` |
| B | 529 | 30 | Las 33 menos 2 laborales y sobrecarga |
| C0 | 287 | 29 | B sin `trabaja_actualmente`, constante en este grupo |
| C1 | 287 | 31 | C0, `lugar_trabajo_comprensivo` y `estres_entorno_laboral` |
| D0 | 239 | 30 | Las mismas 30 de B |
| D1 | 239 | 31 | D0 y `sobrecarga_fisica_emocional` |

**D0 y D1 no incluyen las dos variables laborales:** solo 130 de las 239 tienen esos datos, e incluirlas obligaría a imputar «no aplica» o a reducir la población. `trabaja_actualmente` se mantiene (140 trabajan y 99 no).

## 6. Modelos secundarios declarados

| Función | Modelos | Pregunta |
|---|---|---|
| Sensibilidad sin IMC | `A_sin_imc`, `B_sin_imc`, `C0_sin_imc`, `C1_sin_imc`, `D0_sin_imc`, `D1_sin_imc` | ¿Dependen los resultados de un IMC faltante en 49,5 %? |
| Retirada de variables | `B_sin_dias`, `B_sin_fuerza`, `B_sin_bajo_impacto`, `B_sin_dias_bajo_impacto`, `B_sin_actividad` | ¿Se reemplazan entre sí los indicadores de ejercicio? |
| Conjunto Shannon | `B_shannon`, `B_resto`, `C1_shannon` | ¿Aportan algo las variables que no superaron q < 0,10? |
| Imputación en partición | `B_imp_particion`, `C1_imp_particion`, `D1_imp_particion` | ¿Cambia algo al reimputar dentro de cada partición? |
| Clasificador sencillo | `Ref_general`, `Ref_laboral`, `Ref_cuidadoras` | ¿Se supera una predicción sin información? |

Las listas del conjunto Shannon se eligieron mirando todos los datos, de modo que sus comparaciones son exploratorias y potencialmente optimistas. No son filtros de los modelos principales.

## 7. Preparación

Todo lo que aprende parámetros se ajusta solo con entrenamiento, en cada partición:

- **Faltantes reconstruidos en memoria:** 262 de `imc` (`imc_fue_imputado`, que no es predictor), 16 de `lugar_trabajo_comprensivo` y 10 de `estres_entorno_laboral`. Se imputan con la mediana de entrenamiento. La Fase 35A había usado la media global (29,23) en el conjunto analítico.
- **Nominal:** `quien_prepara_comidas`, con codificación one-hot. Una categoría nueva en evaluación no rompe el modelo.
- **Ordinales:** conservan valores y orden. No se escala nada.
- **Sin indicadores de imputación.**

### Comprobaciones previas de filtración, sin entrenar

**IMC.** Faltar el IMC no se relaciona con la severidad: 53,4 % de severas entre quienes no lo informaron y 52,8 % entre quienes sí (ji cuadrado, p = 0,885). Por eso el valor imputado no funciona como marca de la severidad.

**Otras imputaciones de la Fase 34B.** La limpieza imputó faltantes con la mediana o la moda de todo el conjunto, antes de particionar. **No usa la severidad**, de modo que no filtra el objetivo; sí usa estadísticos de personas que luego quedan en evaluación. Se comparó el valor global con el que habría resultado usando solo entrenamiento, en las 45 particiones de las tres poblaciones:

- 23 de 28 variables: el valor es igual en todas. No hay nada que rehacer.
- 5 variables difieren en alguna partición: `tiene_actividad_sexual` (30 celdas; 27 de 45 particiones), `frecuencia_fuerza` (2; 17), `frecuencia_aerobico` (7; 14), `cantidad_personas_cuida` (6 identificadas de 7; 2) y `dias_ejercicio_semana` (36; 1).

**Decisión.** Los modelos principales mantienen estos valores, como el resto del proyecto, y no se ajustan a posteriori. Se agrega la sensibilidad `*_imp_particion`: esas celdas vuelven a estar vacías en memoria y se imputan solo con entrenamiento, con el mismo criterio de la limpieza. Se identifican con la marca del conjunto limpio o, si no existe, con celdas vacías en el conjunto sucio; esto último omite respuestas inválidas (una celda de `cantidad_personas_cuida`). Se elige por adelantado: si esta sensibilidad cambia alguna lectura de las comparaciones principales, se informa como limitación y no se reemplazan los resultados principales sin consultar.

El detalle queda en `resultados/revision_imputaciones_34B.csv` y `resultados/imc_faltante_y_severidad.csv`.

## 8. Entrenamiento

`RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=1)`. `RepeatedStratifiedKFold(5, 3, random_state=42)`. Las particiones dependen solo del objetivo, por lo que son idénticas entre modelos de una misma población. No se buscan hiperparámetros ni se eligen semillas.

**Referencia:** `DummyClassifier(strategy="prior")`, con las mismas particiones.

**Memoria y procesos:** 4 procesos, unos 145 MB cada uno (equipo de 7,7 GB). Se detiene si hay menos de 500 MB disponibles. El número de procesos no cambia los resultados.

## 9. Evaluación

Exactitud balanceada, ROC-AUC, F1, precisión y sensibilidad de ambas clases, matrices de confusión, rendimiento de entrenamiento frente a evaluación y variación entre particiones.

**Comparaciones principales:** B − A, C1 − C0 y D1 − D0, con las mismas personas y particiones. Se informan promedio, desviación estándar, mínimo, máximo y particiones a favor.

Las particiones comparten datos. Por eso se agrega un intervalo de 95 % con la **corrección de Nadeau y Bengio**: varianza × (1/15 + 0,25), con t de 14 grados de libertad. Es aproximado y se usa de forma descriptiva.

**Lectura fijada antes de ver resultados:** *mejora respaldada* si el límite inferior es mayor que 0; *empeora* si el superior es menor que 0; *sin diferencia clara* si el intervalo incluye 0.

No se comparan directamente valores absolutos entre poblaciones. No se elige un «mejor modelo» por una partición.

## 10. Pruebas contra el azar

200 permutaciones de etiquetas para los seis modelos principales, repitiendo todo el procedimiento: particiones estratificadas con las etiquetas barajadas, imputación, codificación, entrenamiento y evaluación.

- p = (1 + k) / 201; mínimo posible 0,005. ROC-AUC como principal y exactitud balanceada como secundaria.
- Sin corrección por los 6 modelos; se informa así.
- Prueban el rendimiento de cada modelo, no la mejora entre modelos.
- **Costo:** 18.000 bosques; estimación de 1 a 1,5 horas, más el resto del análisis. Es viable y no se reduce el número de permutaciones.

## 11. Importancia

Por permutación, **solo con datos de evaluación**, en A, B, C0, C1, D0, D1, `B_sin_imc`, `C1_sin_imc` y `D1_sin_imc`. Cada variable o grupo se baraja 20 veces por partición, en una copia y antes de la preparación. Medida principal: pérdida de ROC-AUC; complementaria: pérdida de exactitud balanceada. No se usa la importancia por impureza.

**Clasificación fijada antes de ver resultados (pérdida de AUC, 15 particiones):**

| Clase | Regla |
|---|---|
| Aporte consistente | Promedio ≥ 0,005 y positiva en al menos 12 de 15 particiones |
| Aporte pequeño | Promedio > 0 y < 0,005, positiva en al menos 12 de 15 |
| Aporte inestable | Promedio > 0, positiva en menos de 12 de 15 |
| Nulo o negativo | Promedio ≤ 0 |

Estos cortes son una convención descriptiva, no una prueba estadística.

**Grupos, barajados con filas completas:**

| Grupo | Variables, si están en el modelo |
|---|---|
| Actividad física | `dias_ejercicio_semana`, `frecuencia_bajo_impacto`, `frecuencia_fuerza`, `frecuencia_aerobico` |
| Días y bajo impacto | `dias_ejercicio_semana`, `frecuencia_bajo_impacto` |
| Trabajo | `lugar_trabajo_comprensivo`, `estres_entorno_laboral` |
| Cuidados | `cantidad_personas_cuida`, `sobrecarga_fisica_emocional` |

Un grupo se informa solo si tiene al menos dos variables en el modelo. Las variables relacionadas pueden reemplazarse entre sí, de modo que su importancia individual no mide un aporte independiente.

## 12. Comparación con Shannon

Tabla de 33 filas, leída de archivos guardados: `reunion_2026-11-03/revision_33_variables/informe/comparacion_10000_50000.csv` y `reunion_2026-11-03/revision_33_variables/permutaciones_50000/direccion_resumen.csv`. **Cada variable se lee en un solo modelo:** las generales en B, las laborales en C1 y la sobrecarga en D1. Las importancias de distintas poblaciones no se ordenan juntas.

| Consistencia | Regla |
|---|---|
| Coinciden ambos métodos | q < 0,10 y aporte consistente |
| Shannon sí; RF aporte pequeño | q < 0,10 y aporte pequeño |
| Solo Shannon | q < 0,10 y aporte inestable, nulo o negativo |
| Solo Random Forest | q ≥ 0,10 y aporte consistente |
| Ninguno claro (aporte pequeño) | q ≥ 0,10 y aporte pequeño |
| Sin respaldo en ninguno | q ≥ 0,10 y aporte inestable, nulo o negativo |

La dirección se toma de lo ya documentado. Random Forest no indica si una variable es de riesgo o protectora, y una importancia alta no la clasifica como tal.

## 13. Separación e integridad

- Salidas solo en esta carpeta. Los resultados crudos (`resultados/crudos/`) se escriben una vez y no se sobrescriben. Las tablas y figuras derivadas se pueden regenerar desde ellos sin entrenar.
- Si una ejecución se interrumpe, retoma lo que falte; cada cálculo está determinado por sus semillas.
- No se modifican datasets, EDA, resultados de Shannon, informes ni programas anteriores. Se comprueba por huellas antes y después. FCBF no se ejecuta.
- Sin commit ni push. No se avanza a la Fase 36.

## 14. Condiciones para ejecutar

Requiere `--autorizado-por-usuaria` y se detiene si: falla una prueba; hay cambios en archivos versionados o difieren los hashes del respaldo; cambian las 33 variables, los tamaños, las severas o las celdas a reimputar; el conjunto de 33 difiere de `dataset_fase35.csv` en algo más que la columna excluida; entra una variable prohibida, constante o con faltantes no previstos; hay superposición entre entrenamiento y evaluación; dos corridas de control no coinciden; cambia un archivo vigilado; o hay menos de 500 MB disponibles.

## 15. Limitaciones

- Casi la mitad del IMC recibe la mediana: su aporte puede subestimarse, y entre quienes no lo informaron el valor no distingue personas.
- Las 5 particiones con 3 repeticiones comparten datos: las diferencias pequeñas pueden deberse a la variación entre particiones.
- La importancia por permutación se reparte entre variables relacionadas y, al barajar una sola, puede crear combinaciones poco realistas.
- `class_weight="balanced"` y el corte en 0,5 no se ajustan.
- Los modelos laborales y de cuidadoras tienen menos personas, y sus estimaciones son menos precisas. Entre las 239 cuidadoras, `frecuencia_fuerza` llega a 86,61 % en «No lo realiza»; se conserva porque la regla de dominancia se mide en la población de la variable (529, 84,69 %).
- Las listas del conjunto Shannon se eligieron con todos los datos.
- Importancia no significa causa, y un resultado en datos sintéticos refleja en parte lo programado en el simulador.

## 16. Adenda posterior a la ejecución

*04-11-2026.* Después de entrenar se corrigieron solo funciones de figuras de `rf_33_variables.py`: la figura de sensibilidad al IMC incluía tres filas que comparaban otros modelos, la de rendimiento invertía el orden, las matrices usaban una escala por panel y faltaba coma decimal. No se cambió ningún cálculo ni resultado crudo; las figuras y tablas derivadas se regeneraron con `--resumir`, sin entrenar. Por eso el registro muestra huellas distintas de programa y protocolo entre el cálculo y el resumen.
