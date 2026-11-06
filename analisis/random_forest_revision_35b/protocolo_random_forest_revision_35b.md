# Random Forest como análisis complementario de la revisión de la Fase 35B

*Registrado el 03-11-2026, después de conocer los resultados de Shannon de la revisión y antes de entrenar cualquier modelo con los datos reales. Actualiza `analisis/protocolo_random_forest_35b.md`, que no se ejecutó y se conserva sin cambios.*

*Corregido el 03-11-2026, también antes de entrenar: `usa_medicamentos_diabetes` sale por dominancia (87,52 %), de modo que el análisis pasa de 34 a 33 variables. Ver `reunion_2026-11-03/revision_33_variables/protocolo_revision_33.md`. No cambian parámetros, semilla, particiones ni reglas de lectura.*

## 1. Carácter y objetivo

Análisis **complementario y exploratorio**. Evalúa qué características ayudan a predecir `severo_mrs` cuando se consideran conjuntamente y compara ese aporte con la revisión entrópica (Shannon, SU, 10.000 y 50.000 permutaciones, q < 0,10).

No reemplaza a Shannon ni a FCBF. **No elige ni elimina variables para la Fase 36.** Como los resultados de Shannon ya se conocían, este análisis no es independiente de ellos. Los datos son sintéticos: los resultados describen este conjunto y no demuestran relaciones causales ni validez clínica.

## 2. Revisión de viabilidad del diseño anterior

| Elemento | Anterior | Ahora | Motivo |
|---|---|---|---|
| Variables | 30 candidatas antiguas y controles, con `doble_carga` | Las 33 de la revisión corregida | Decisión de la profesora y criterio de dominancia |
| Modelos | A, B, C0, C1, C2, D0, D1 | A, B, C0, C1, D0, D1 | Pedido de la usuaria: C0 ya incluye las variables generales |
| Referencias | FCBF E1, E3, E4, C3, C4 | Shannon 10.000 y 50.000, con 33 variables | Revisión del 03-11 |
| Grupos | Con `doble_carga` | Actividad física, trabajo y cuidados | `doble_carga` excluida |
| Pruebas contra el azar | A, B, C0, C2 | A, B, C0, C1, D0, D1 | Cubre todos los principales |

**Conclusión: compatible.** Se conservan los parámetros, la vista en memoria, la imputación dentro de cada partición, las particiones, la importancia por permutación y las pruebas contra el azar. Las funciones sin cambios se importan de `random_forest_fase35b.py`; no se reescriben.

## 3. Datos

- **Base:** `datos/analitico/dataset_fase35.csv`. No se modifica ni se genera ningún dataset.
- **Conjuntos limpio y sucio:** solo para identificar respuestas observadas y la población de sobrecarga.
- **Versión verdadera del simulador:** no se lee. Los efectos programados solo se citan al discutir.
- **Objetivo:** `severo_mrs`; 1 = MRS total ≥ 16. Se exige 529 mujeres, 281 severas y 248 no severas.

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

### Variables laborales en cuidadoras: decisión previa
**D0 y D1 no incluyen las dos variables laborales.** Solo 130 de las 239 tienen esos datos. Incluirlas obligaría a imputar «no aplica» a quienes no trabajan o a reducir la población. `trabaja_actualmente` se mantiene (140 trabajan y 99 no) y `cantidad_personas_cuida` toma valores 1 a 3.

## 6. Modelos secundarios declarados

| Función | Modelos | Pregunta |
|---|---|---|
| Sensibilidad sin IMC | `A_sin_imc`, `B_sin_imc`, `C0_sin_imc`, `C1_sin_imc`, `D0_sin_imc`, `D1_sin_imc` | ¿Dependen los resultados de un IMC imputado en 49,5 %? |
| Retirada de variables | `B_sin_dias`, `B_sin_fuerza`, `B_sin_bajo_impacto`, `B_sin_actividad` | ¿Se reemplazan entre sí los indicadores de ejercicio? |
| Conjunto Shannon | `B_shannon`, `B_resto`, `C1_shannon` | ¿Aportan algo las variables que no superaron q < 0,10? |
| Clasificador sencillo | `Ref_general`, `Ref_laboral`, `Ref_cuidadoras` | ¿Se supera una predicción sin información? |

- `B_shannon`: las 5 generales con q < 0,10 (`dias_ejercicio_semana`, `frecuencia_bajo_impacto`, `frecuencia_fuerza`, `imc`, `trabaja_actualmente`).
- `B_resto`: las otras 25 generales.
- `C1_shannon`: `imc`, las 3 de ejercicio y `lugar_trabajo_comprensivo`.
- **Estas listas se eligieron mirando todos los datos, de modo que sus comparaciones son exploratorias y potencialmente optimistas. No son filtros de los modelos principales.**

## 7. Preparación

Todo lo que aprende parámetros se ajusta solo con entrenamiento, en cada partición:

- **Faltantes reconstruidos en memoria:** 262 de `imc` (`imc_fue_imputado`), 16 de `lugar_trabajo_comprensivo` y 10 de `estres_entorno_laboral`. Se imputan con la mediana de entrenamiento.
- **Otras imputaciones de la Fase 34B:** se mantienen, incluidas las 22 de `trabaja_actualmente`. No usan la severidad y se declaran como limitación.
- **Nominal:** `quien_prepara_comidas`, con codificación one-hot. Una categoría nueva en evaluación no rompe el modelo.
- **Ordinales:** conservan valores y orden. No se escala nada.
- **Sin indicadores de imputación.**

## 8. Entrenamiento

`RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=1)`. `RepeatedStratifiedKFold(5, 3, random_state=42)`. Las particiones dependen solo del objetivo, por lo que son idénticas entre modelos de una misma población. No se buscan hiperparámetros.

**Referencia:** `DummyClassifier(strategy="prior")`, con las mismas particiones.

**Memoria y procesos:** 4 procesos. Medido con datos inventados: unos 145 MB por proceso, en un equipo de 7,7 GB con cerca de 900 MB disponibles. El programa se detiene si hay menos de 500 MB disponibles. El número de procesos no cambia los resultados.

## 9. Evaluación

Exactitud balanceada, ROC-AUC, F1, precisión y sensibilidad de ambas clases, matrices de confusión, rendimiento de entrenamiento frente a evaluación y variación entre particiones.

**Comparaciones principales:** B − A, C1 − C0 y D1 − D0, con las mismas personas y particiones. Se informan promedio, desviación estándar, mínimo, máximo y particiones a favor.

Las particiones comparten datos. Por eso se agrega un intervalo de 95 % con la **corrección de Nadeau y Bengio**: varianza × (1/15 + 0,25), con t de 14 grados de libertad. Es aproximado y se usa de forma descriptiva.

**Lectura fijada antes de ver resultados:**
- **Mejora respaldada:** el límite inferior es mayor que 0.
- **Empeora:** el límite superior es menor que 0.
- **Sin diferencia clara:** el intervalo incluye 0.

No se comparan directamente valores absolutos entre poblaciones. No se elige un «mejor modelo» por una partición.

## 10. Pruebas contra el azar

200 permutaciones de etiquetas para A, B, C0, C1, D0 y D1, repitiendo todo el procedimiento: particiones estratificadas con las etiquetas barajadas, imputación, codificación, entrenamiento y evaluación.

- p = (1 + k) / 201; mínimo posible 0,005. ROC-AUC como principal y exactitud balanceada como secundaria.
- Sin corrección por los 6 modelos; se informa así.
- Prueban el rendimiento de cada modelo, no la mejora entre modelos.
- **Costo:** 18.000 bosques; estimación de 1 a 1,5 horas. No se reduce el número de permutaciones. Si no fuera viable, se pide autorización antes de cambiarlo.

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

- Salidas solo en `analisis/random_forest_revision_35b/`.
- Los resultados crudos (`resultados/crudos/`) se escriben una vez y no se sobrescriben. Las tablas y figuras derivadas se pueden regenerar desde ellos sin entrenar.
- Si una ejecución se interrumpe, retoma lo que falte; cada cálculo está determinado por sus semillas.
- No se modifican datasets, resultados, protocolos, informes ni programas anteriores. Se comprueba por huellas antes y después.
- Sin commit ni push. No se avanza a la Fase 36.

## 14. Condiciones para ejecutar

Requiere `--autorizado-por-usuaria` y se detiene si:

1. Falla alguna prueba.
2. Hay cambios en archivos versionados o difieren los hashes del respaldo. HEAD se registra, sin exigir un valor, para que un commit posterior no impida reproducir.
3. Cambian las 33 variables, los tamaños o las severas.
4. Entra una variable prohibida, constante o con faltantes no previstos.
5. Hay superposición entre entrenamiento y evaluación, o una persona no se evalúa una vez por repetición.
6. Dos corridas de control no coinciden.
7. Cambia cualquier archivo vigilado.
8. Hay menos de 500 MB disponibles.

## 15. Limitaciones

- Casi la mitad del IMC recibe la mediana: su aporte puede subestimarse, y el valor imputado podría funcionar como marca de dato faltante dentro de los árboles.
- Las 5 particiones con 3 repeticiones comparten datos: las diferencias pequeñas pueden deberse a la variación entre particiones.
- La importancia por permutación se reparte entre variables relacionadas y, al barajar una sola, puede crear combinaciones poco realistas.
- `class_weight="balanced"` y el corte en 0,5 no se ajustan.
- Los modelos laborales y de cuidadoras tienen menos personas, y sus estimaciones son menos precisas. Entre las 239 cuidadoras, `frecuencia_fuerza` llega a 86,61 % en «No lo realiza»; se conserva porque la regla de dominancia se mide en la población de la variable (529, 84,69 %).
- Las listas del conjunto Shannon se eligieron con todos los datos.
- Importancia no significa causa, y un resultado en datos sintéticos refleja en parte lo programado en el simulador.
