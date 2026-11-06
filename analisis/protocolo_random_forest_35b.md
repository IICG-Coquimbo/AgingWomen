# Random Forest como análisis complementario de la Fase 35B

*Registrado el 03-11-2026, después de conocer los resultados de FCBF y antes de entrenar cualquier modelo con los datos reales.*

## 1. Carácter y objetivo

Este análisis es **exploratorio**. Evalúa qué características ayudan a predecir `severo_mrs` y compara sus aportes con SU y FCBF. No reemplaza FCBF, no sustituye el resultado oficial de la Fase 35B (0 variables seleccionadas) y **no elige variables para la segmentación**. Los datos son sintéticos: los resultados describen su comportamiento y no demuestran relaciones causales.

## 2. Referencias que no se modifican

Se leen de archivos guardados, sin recalcularlas:

| Referencia | Permutaciones | q < | Seleccionadas |
|---|---:|---:|---|
| E1 (oficial) | 5.000 | 0,05 | Ninguna |
| E3 / C3 | 50.000 | 0,05 | `dias_ejercicio_semana` |
| E4 / C4 | 50.000 | 0,10 | `frecuencia_fuerza`, `lugar_trabajo_comprensivo`, `doble_carga` |

## 3. Datos

- **Base:** `datos/analitico/dataset_fase35.csv`. `dataset_fase35b.csv` no se usa.
- **Conjuntos limpio y sucio:** solo para identificar respuestas observadas e imputaciones.
- **Versión verdadera del simulador:** no se lee.
- **Vista en memoria:** no se genera ningún dataset.
- **Objetivo:** `severo_mrs`, 1 = síntomas severos.

### Excluidas del entrenamiento
Identificadores, preguntas del MRS, `mrs_total`, `severidad_mrs_4`, `prevision`, `etapa_menopausica`, variables menstruales, indicadores de imputación, y las variables consecuencia de los síntomas de `configuracion.PROHIBIDAS`. Las 30 candidatas no están en esa lista y se mantienen; una variable como `distension_abdominal` podría solaparse con síntomas, y por eso se lee con cautela.

## 4. Poblaciones

| Población | n | Severas | Definición |
|---|---:|---:|---|
| Todas | 529 | 281 | MRS completo |
| Trabajadoras con datos laborales | 287 | 166 | Máscara de la Fase 35B; no son todas las trabajadoras (hay 309 con `trabaja_actualmente` = 1) |
| Cuidadoras con sobrecarga observada | 239 | 136 | Las mismas de `protocolo_cuidados_35b.md` |

Si algún tamaño cambia, el programa se detiene.

## 5. Modelos principales

| Modelo | Población | Variables | Contenido |
|---|---|---:|---|
| A | 529 | 4 | Controles |
| B | 529 | 32 | Controles y 28 no laborales |
| C0 | 287 | 3 | Edad, IMC y diabetes (`trabaja_actualmente` es constante) |
| C1 | 287 | 31 | C0 y 28 no laborales |
| C2 | 287 | 33 | C1, `lugar_trabajo_comprensivo` y `estres_entorno_laboral` |
| D0 | 239 | 31 | Controles y 27 no laborales |
| D1 | 239 | 32 | D0 y `sobrecarga_fisica_emocional` |

### Decisiones fijadas para D0 y D1
- **`doble_carga` queda fuera.** Entre estas 239 es idéntica a `trabaja_actualmente`; mantener ambas repartiría el mismo aporte entre dos nombres.
- **`trabaja_actualmente` se mantiene.** Es el control, y distingue a 140 que trabajan de 99 que no.
- **`cantidad_personas_cuida` se mantiene.** Toma valores 1 a 3; no hay ceros en esta población.
- **Las variables laborales quedan fuera.** Solo 130 de las 239 tienen esos datos. Incluirlas obligaría a imputar a quienes no trabajan, confundiendo «no aplica» con faltante, o a reducir la población.

### Relación entre variables de cuidado
`doble_carga` depende de otras variables según la población: en las 529 es función de trabajar y cuidar; en las 287 equivale a cuidar o no; en las 239 equivale a trabajar. No se le atribuye importancia independiente.

## 6. Modelos adicionales declarados

Se agregan solo para responder las preguntas del plan:

| Función | Modelos |
|---|---|
| Sensibilidad sin IMC | `A_sin_imc`, `B_sin_imc`, `C2_sin_imc` |
| Retirada de variables | `B_sin_dias`, `B_sin_fuerza`, `B_sin_actividad`, `B_sin_doble`, `A_cantidad`, `A_cantidad_doble` |
| Listas FCBF elegidas con todos los datos | `A_dias`, `A_fuerza`, `Lista_E4_529`, `C0_dias`, `Lista_E4_287` |
| Clasificador sencillo | `Ref_todas`, `Ref_trabajadoras`, `Ref_cuidadoras` |

- La lista oficial (ninguna variable) equivale a A o C0. C3 y C4 seleccionaron las mismas listas que E3 y E4.
- `Lista_E4_529` omite `lugar_trabajo_comprensivo` porque no aplica a las 529. `Lista_E4_287` usa la lista completa.
- `trabaja_actualmente` sigue en `A_cantidad_doble`, de modo que `A_cantidad_doble − A_cantidad` mide lo que agrega `doble_carga` a trabajo y cantidad de personas cuidadas.
- **Las listas FCBF se eligieron con todos los datos: esas comparaciones son exploratorias y potencialmente optimistas. No son una evaluación independiente.**

## 7. Preparación

Todo ocurre **dentro de cada partición**, ajustado solo con entrenamiento:

- **Faltantes reconstruidos en memoria:** 262 IMC (`imc_fue_imputado`), 16 `lugar_trabajo_comprensivo` y 10 `estres_entorno_laboral` imputados en la Fase 34B. Los laborales se identifican con el conjunto sucio. Se imputan con la mediana de entrenamiento, porque la imputación previa usó todos los datos, incluidos los que luego se evalúan.
- **Otras imputaciones de la Fase 34B:** se mantienen. No usan la severidad y están documentadas como limitación. Entre las 529, 23 personas no tienen respuesta válida de `trabaja_actualmente` en el conjunto sucio y 25 no la tienen de `cuida_otras_personas`.
- **Nominales:** solo `quien_prepara_comidas`, con codificación one-hot en cada partición. Una categoría nueva en evaluación no rompe el modelo.
- **Ordinales:** conservan sus valores y orden. No se escala nada.
- **Sin indicadores de imputación.**
- **«No aplica»:** las laborales quedan vacías fuera de las 287, y la sobrecarga fuera de las 239. Esas personas no están en los modelos que usan esas variables. Por eso «no aplica» nunca se imputa ni se toma como faltante.

## 8. Entrenamiento

`RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt", class_weight="balanced", random_state=42)`. Validación `RepeatedStratifiedKFold(5, 3, random_state=42)`: mismas particiones entre modelos con la misma población. No se buscan hiperparámetros.

**Clasificador sencillo:** `DummyClassifier(strategy="prior")`, en cada población y con las mismas particiones. Predice la clase más frecuente del entrenamiento, y su AUC y exactitud balanceada son 0,5.

## 9. Evaluación

Exactitud balanceada, ROC-AUC, F1 de severos y de no severos, matrices de confusión, y rendimiento de entrenamiento frente a evaluación.

**Comparaciones principales:** B − A, C1 − C0, C2 − C1 y D1 − D0. Se informan promedio, desviación estándar, mínimo, máximo y particiones a favor. Las particiones comparten datos y no son independientes, de modo que esta variación es descriptiva. No se calcula un valor p para estas diferencias.

## 10. Pruebas contra el azar

200 permutaciones de etiquetas para A, B, C0 y C2. En cada una se barajan las etiquetas, se generan de nuevo las particiones estratificadas con esas etiquetas y se repite todo: imputación, codificación, entrenamiento y evaluación.

- **Estadístico:** promedio de evaluación. ROC-AUC como principal y exactitud balanceada como secundaria.
- **p = (1 + k) / 201**, donde k es el número de permutaciones con resultado mayor o igual al observado. El mínimo posible es 0,005.
- **Semillas:** una permutación determinada por población e índice, de modo que A y B comparten etiquetas barajadas, igual que C0 y C2. Bosque con `random_state=42`.
- **Tiempo:** 12.000 bosques, unos 50 minutos estimados con 6 procesos, según mediciones con datos inventados. Se usan 6 procesos porque fue el valor más rápido entre 4, 6 y 8, y el equipo tiene 7,7 GB de RAM. Es un ajuste de cálculo: no cambia el método ni los resultados.

## 11. Importancia

Por permutación, **solo con datos de evaluación**, para A, B, C0, C1, C2, D0 y D1. Cada variable o grupo se baraja 20 veces por partición en una copia de los datos, antes de la preparación. Medida principal: pérdida de ROC-AUC; secundaria: pérdida de exactitud balanceada.

Se informan promedio, desviación estándar, mínimo, máximo y particiones con pérdida positiva. La lectura usa solo el signo y la frecuencia, sin umbrales.

**Grupos, barajados con filas completas para que las combinaciones sigan siendo posibles:**

| Grupo | Variables, si están en el modelo |
|---|---|
| Actividad física | `dias_ejercicio_semana`, `frecuencia_aerobico`, `frecuencia_bajo_impacto`, `frecuencia_fuerza` |
| Cuidados | `cantidad_personas_cuida`, `doble_carga`, `sobrecarga_fisica_emocional` |
| Trabajo y cuidados | `trabaja_actualmente` y las de cuidados |
| Entorno laboral | `lugar_trabajo_comprensivo`, `estres_entorno_laboral` |

`horas_sedentarismo` no se incluye en actividad física porque mide otra conducta.

## 12. Comparación con FCBF

- `rf_vs_fcbf.csv` compara importancia con las decisiones guardadas de E1, E3, E4, C3 y C4. Las variables laborales se leen en C2, la sobrecarga en D1 y las demás en B.
- Importancia de RF y SU miden cosas distintas: una mide pérdida de predicción dentro de un modelo con otras variables, y la otra asociación marginal. Una discrepancia no indica error de ninguno.

### FCBF dentro de cada partición: pendiente
**No se implementa en esta versión.** Requiere decisiones metodológicas nuevas que deben aprobarse antes, según lo pedido en el plan:

1. Permutaciones y umbral: 5.000/q < 0,05, 50.000/q < 0,05 o 50.000/q < 0,10.
2. Qué modelo se ajusta si una partición no selecciona ninguna variable. La propuesta es usar solo los controles.
3. Población de cada selección: 529 con Etapa 2 laboral, y si incorpora la Etapa 3.
4. Calcular dentro de cada entrenamiento los cuartiles de `horas_sedentarismo` y los datos reconstruidos.
5. Semillas propias, sin reutilizar las de la selección anterior.

Hasta entonces, solo existen comparaciones con listas elegidas con todos los datos, rotuladas como exploratorias.

## 13. Separación e integridad

- Salidas solo en `analisis/random_forest_35b/`, con lista cerrada y sin sobrescribir. La excepción es `interpretacion_resultados.md`, escrito después de ver resultados y rotulado así.
- No se regeneran datasets, no se modifican resultados, protocolos ni archivos de FCBF, y no se actualiza el Word.
- Sin commit ni push. El registro guarda los SHA-256 del programa, de este protocolo y de sus pruebas.
- Se calcula y comprueba todo antes de escribir.

## 14. Condiciones para ejecutar

La ejecución requiere `--autorizado-por-usuaria` y se detiene si:

1. Falla alguna prueba de los cuatro módulos.
2. HEAD no es `745d689`, hay cambios en archivos versionados o difieren los hashes del respaldo.
3. Cambian candidatas, controles o tamaños.
4. Entra una variable prohibida, constante o con faltantes no previstos.
5. Hay superposición entre entrenamiento y evaluación, o una persona no se evalúa una vez por repetición.
6. Dos corridas no coinciden.
7. Cambia cualquier archivo vigilado.

## 15. Limitaciones

- Casi la mitad del IMC recibe la mediana: su aporte puede subestimarse, y la sensibilidad sin IMC no puede compensarlo.
- Con 5 particiones y 3 repeticiones, las diferencias pequeñas pueden deberse a variación de las particiones.
- La importancia por permutación se reparte entre variables relacionadas.
- `class_weight="balanced"` y el corte en 0,5 no se ajustan.
- Importancia no significa causa, y un resultado en datos sintéticos refleja lo que se programó en el simulador.
