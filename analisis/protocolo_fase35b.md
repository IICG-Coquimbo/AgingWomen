# Protocolo definitivo de la Fase 35B

Aprobado por la usuaria el 2 de noviembre de 2026, antes de escribir el código y de ejecutar la selección.
Integra las decisiones A, B, C, D y la sensibilidad S5.

## 1. Objetivo y variables

**Objetivo:** seleccionar las predictoras que pasan a la Fase 36, según su relación con `severo_mrs` (MRS ≥ 16). La entrada es `datos/analitico/dataset_fase35.csv` (n = 529).

| Grupo | Variables | Tratamiento |
|---|---|---|
| Control (4) | `edad`, `imc`, `usa_medicamentos_diabetes`, `trabaja_actualmente` | Pasan a la Fase 36 sin filtro y no eliminan a otras; su SU es descriptiva |
| Pendiente (1) | `prevision` | No pasa a la Fase 36 ni entra al filtro; sigue en el conjunto limpio y el EDA, y su SU es descriptiva |
| Candidatas no laborales (28) | Las demás predictoras | Etapa 1, con n = 529 |
| Candidatas laborales (2) | `lugar_trabajo_comprensivo`, `estres_entorno_laboral` | Etapa 2, con n = 287 |

Si la profesora pide filtrar `prevision`, la familia pasa a 31 pruebas, y habría que volver a ejecutar y declararlo.

Las 287 son las trabajadoras con respuestas laborales reales. De las 309 trabajadoras, las otras 22 tienen la mediana imputada en ambas preguntas; se verificó que son las mismas personas en las dos.

## 2. Medida y discretización

**SU(X,Y) = 2·I(X;Y) / [H(X) + H(Y)]**, con log₂ y frecuencias observadas, sin corrección de sesgo. Si H(X) + H(Y) = 0, entonces SU = 0.

Las categorías ordinales y nominales se usan tal como están. Estos intervalos se usan solo para calcular la SU, y los valores originales pasan intactos a la Fase 36:

| Variable | Intervalos (n) |
|---|---|
| Edad | 36–39 (22), 40–44 (104), 45–49 (120), 50–54 (110), 55–59 (79), 60–65 (94) |
| IMC (OMS) | < 18,5 (2), 18,5–24,9 (61), 25–29,9 (363), 30–34,9 (47), 35–39,9 (44), ≥ 40 (12) |
| Horas sentada | ≤ 5 (185), > 5 a 6 (118), > 6 a 8 (129), > 8 (97) |

- **Edad:** dos tramos no miden 5 años. El primero tiene 4, porque hay participantes menores de 40 por la excepción de edad. El último tiene 6, para que 65 años no quede sola.
- **Empates en horas:** los cuartiles son 5, 6 y 8, calculados una sola vez con las 529. Valores iguales van al mismo tramo, y un corte duplicado se fusiona.
- **Remuestreos y S5:** usan estos mismos cortes.
- **IMC:** su SU se informa con todos y solo con observados (n = 267), porque los 262 imputados caen en 25–29,9.

## 3. Filtro de relevancia

1. Las 28 no laborales se calculan con n = 529, y las 2 laborales con n = 287.
2. Se permuta `severo_mrs` entre las personas de cada cálculo, 5.000 veces.
3. **p = (1 + nº de permutaciones con SU ≥ SU observada) / 5.001.**
4. Se aplica Benjamini-Hochberg a la familia de 30 candidatas.
5. **Una variable es relevante si q < 0,05.**

## 4. Prueba de azar entre predictoras

La familia son **todos los pares entre las R variables relevantes**, R(R−1)/2, fijada antes de recorrer FCBF.

| Par | Personas |
|---|---|
| No laboral – no laboral | 529 |
| Laboral – laboral, o laboral – no laboral | 287 |

En cada par se permuta X con Y fija, 5.000 veces, y se usa la misma fórmula de p. Benjamini-Hochberg se aplica una sola vez a toda la familia. **El par supera el azar si q < 0,05.**

## 5. FCBF adaptado por cobertura (selección definitiva)

**Regla de cobertura:** una variable solo puede eliminar a otra si tiene datos para todas las personas de esa otra. Por eso una laboral nunca elimina a una no laboral.

**Etapa 1: no laborales relevantes (n = 529)**

1. Se ordenan por SU con la severidad de mayor a menor, y los empates se resuelven por orden alfabético.
2. Y se elimina frente a una Z más fuerte si **SU(Z,Y) ≥ SU(Y, severidad) y q(Z,Y) < 0,05**.

**Etapa 2: laborales relevantes (exactamente las mismas 287 observaciones)**

1. Se ordenan por su SU con la severidad, calculada con las 287.
2. Cada una se compara con las laborales más fuertes que sigan en la lista y con las no laborales que sobrevivieron a la Etapa 1.
3. La laboral Y se elimina frente a Z solo si se cumplen las tres condiciones:
   - SU₂₈₇(Z, severidad) ≥ SU₂₈₇(Y, severidad)
   - SU₂₈₇(Z,Y) ≥ SU₂₈₇(Y, severidad)
   - q(Z,Y) < 0,05, con su valor p calculado sobre las 287

**La SU de cada no laboral con la severidad se recalcula con las 287 para estas comparaciones.** No se usa su valor con n = 529, y el recálculo no cambia su resultado en la Etapa 1.

Si quedan pocas variables o ninguna, se informa así y no se relajan las reglas.

## 6. Las tres variantes en el informe

| Nombre | Personas | Regla de redundancia | Función |
|---|---|---|---|
| **FCBF adaptado por cobertura** | 529 y 287, en dos etapas | Con q < 0,05 | **Selección definitiva** |
| **FCBF estándar por cobertura** | 529 y 287, en dos etapas | Sin exigir q < 0,05 | Comparación |
| **FCBF completo con n = 287 (S5)** | 287 en todo, con una sola lista | Con q < 0,05, y su versión sin q como referencia | Sensibilidad |

Las dos primeras comparten el filtro de relevancia, así que solo difieren en la prueba del par. El informe también listará los pares laboral–no laboral que parecen redundantes y que la regla de cobertura no permite eliminar.

## 7. Estabilidad (complementaria)

Se aplican **500 remuestreos con 5.000 permutaciones, en 11 procesos**. En cada uno:

1. **Bootstrap estratificado por `severo_mrs`:** con reemplazo, manteniendo 281 y 248 casos.
2. **Personas laborales:** se vuelven a identificar en cada remuestreo, así que su número varía y no es exactamente 287.
3. **Selección:** se repiten las secciones 3 a 5, con ambas variantes por cobertura.

**Qué se informa:**

- **Por variable:** porcentaje de selección, salida por motivo y variable que más la eliminó. Las bandas ≥ 80 %, 50–79 % y < 50 % son solo descriptivas.
- **Global:** índice de Nogueira con IC 95 %, Jaccard promedio y tamaño de la selección.

**Reproducibilidad:** cada cálculo usa `SeedSequence(42)` con una clave fija por análisis, remuestreo y variable o par, de modo que las semillas son independientes y deterministas. El resultado no depende del orden ni del número de procesos.

**Tiempos:** el informe indicará que los estimados previos son **extrapolaciones** de mediciones breves (cerca de 14 µs por SU; hasta unas 1,5 h en el peor caso), y además registrará el tiempo real.

## 8. Sensibilidad (complementaria, lista cerrada)

| # | Variación |
|---|---|
| S1 | Horas sentada en terciles y en sus 14 valores originales |
| S2 | Severidad en 4 clases |
| S3 | Laborales con n = 309, incluidas las 22 imputadas |
| S4 | Lista única con n = 529 y "no aplica" como categoría (FCBF original, para mostrar el artefacto) |
| S5 | FCBF completo de las 30 candidatas con n = 287 |

Cada una usa 5.000 permutaciones y se compara con la selección definitiva mediante variables que entran, variables que salen y Jaccard. También se compara la selección con los efectos programados en el simulador, solo como descripción.

**Ni la estabilidad, ni la sensibilidad, ni esa comparación modifican la lista seleccionada.** Cualquier cambio posterior de criterio sería una versión nueva, declarada y justificada.

## 9. Advertencias y limitaciones

- **Carácter sintético:** la selección refleja lo que generó el simulador, no evidencia sobre la población.
- **Circularidad:** seleccionar por severidad puede hacer que los clústeres difieran en severidad por esa misma selección. Esa diferencia no es una confirmación independiente.
- **Interpretación:** seleccionada no significa causal, y eliminada no significa irrelevante.
- **Adaptaciones propias:** la prueba de azar entre predictoras y la regla de cobertura se apartan del FCBF original y se declaran en la tesis.
- **Límite de la preespecificación:** ya vimos relaciones bivariadas con la severidad (34C y 34E), la SU de `prevision` y la SU del par laboral.
- **Poblaciones distintas:** la SU laboral describe a trabajadoras y la no laboral a todas, y la Etapa 2 tiene menos potencia.
- **Redundancia conservada:** puede quedar redundancia entre variables laborales y no laborales.
- **Límite de los valores p:** desde 23 variables relevantes, un par aislado no puede alcanzar q < 0,05, lo que hace eliminar menos.
- **Duplicados en el bootstrap:** las permutaciones tratan las filas repetidas como distintas, lo que puede favorecer la significancia en los remuestreos. Por eso la estabilidad es descriptiva y no un valor inferencial.
- **`prevision`:** el diccionario de la 35A la sigue llamando "predictora". No se modifica, y el informe de la 35B aclara que está pendiente.
- **Fase 37:** se mantiene la comparación de la segmentación con y sin edad.

## 10. Controles antes de aceptar resultados

- **Cálculo:** SU = 0 con variables independientes, SU = 1 con idénticas, y simetría.
- **Exclusiones:** quedan fuera la etapa, las preguntas menstruales, `imc_fue_imputado`, los puntajes MRS, las variables de consecuencia y `prevision`.
- **Subconjuntos:** toda comparación de la Etapa 2 debe tener las mismas 287 personas, y ninguna laboral puede eliminar a una no laboral.
- **Reproducibilidad:** misma semilla, mismo resultado, con 1 y con 11 procesos en algunos remuestreos.
- **Fases anteriores:** los archivos de la 35A no deben cambiar (se comprueba con su hash).

## 11. Archivos previstos para la implementación

La implementación y la ejecución requieren una aprobación aparte de la usuaria.

| Acción | Archivo |
|---|---|
| Modificar | `analisis/preprocesamiento/configuracion.py` (bloque de la 35B, sin alterar la 35A) |
| Crear | `analisis/preprocesamiento/entropia.py` |
| Crear | `analisis/seleccionar_fase35b.py` |
| Crear | `analisis/resultados/usuaria/`: `su_objetivo.csv`, `su_pares.csv`, `decisiones_fcbf.csv`, `estabilidad_fcbf.csv`, `sensibilidad_fcbf.csv` |
| Crear | `analisis/figuras/seleccion_35b/` |
| Crear | `analisis/informe_seleccion_fase35b.md` |
| Crear, sin versionar | `datos/analitico/dataset_fase35b.csv` |

El conjunto `dataset_fase35b.csv` tendría `participante_id`, `severo_mrs`, `mrs_total`, `severidad_mrs_4`, `imc_fue_imputado`, las 4 de control y las seleccionadas. Las columnas de resultado y auditoría no son predictoras. Si se seleccionan variables laborales, conservan la codificación de la 35A (0 = "no aplica" y las 22 imputadas), y su tratamiento se decide en la Fase 36.
