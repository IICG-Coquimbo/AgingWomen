# Fase 35A. Preprocesamiento para la selección por entropía

*Generado por `analisis/preprocesar_fase35.py` el 28-10-2026. Configuración: `analisis/preprocesamiento/configuracion.py`. Conjunto: `datos/limpio_usuaria/dataset_usuaria_limpio.csv`.*

Este paso aplica los acuerdos de la reunión con la profesora del 27-10-2026 y las decisiones de la usuaria del 28-10-2026. Todo umbral o excepción está en el archivo de configuración: si la profesora pide cambiar algo, se edita ese archivo y se vuelve a correr el script.

## 1. Variable objetivo

`severo_mrs` = 1 si el MRS total es 16 o más (corte de la clase "severa"). Sobre las 529 participantes con MRS completo: **281 severas (53,1 %)** y 248 no severas (46,9 %). Las clases quedan casi balanceadas, que es lo que buscaba la binarización. `mrs_total` y `severidad_mrs_4` se guardan solo como referencia para caracterizar los clústeres; ninguna de las tres entra como predictora.

## 2. IMC imputado por la media

262 participantes (49,5 %) no informaron peso o talla. Reciben la media de las observadas, **29,23 kg/m²**, y la columna `imc_fue_imputado` deja la marca (solo auditoría; no es predictora).

| Escenario | n | Imputados | Media | Mediana | DE | Mín. | Máx. | rho con MRS total | Media IMC severas / no severas |
|---|---|---|---|---|---|---|---|---|---|
| IMC observado (solo quienes informaron) | 267 | 0 | 29,23 | 28,50 | 6,28 | 18,20 | 45,70 | +0,250 | 30,60 / 27,69 |
| IMC imputado por la media (todas) | 529 | 262 | 29,23 | 29,23 | 4,45 | 18,20 | 45,70 | +0,192 | 29,92 / 28,45 |

**Sensibilidad.** La media no cambia, pero la desviación estándar baja de 6,28 a 4,45 y la asociación con el MRS pasa de rho = 0,250 a 0,192. La imputación por la media no inventa relación, pero diluye la que existe, porque la mitad de las participantes queda con el mismo valor. Se aplica por el criterio acordado con la profesora y se deja constancia de esta limitación.

## 3. Módulos reducidos por decisión de la profesora

| Eliminada | Representante | Asociación medida | Motivo |
|---|---|---|---|
| peso_kg | imc | rho de Spearman = 0,93 | Decisión de la profesora (27-10). Redundante con el IMC (el IMC se calcula con peso y talla). |
| talla_actual_cm | imc | rho de Spearman = -0,04 | Decisión de la profesora (27-10). El IMC ya incorpora la talla en su cálculo. Ojo: medida sola, la talla casi no se asocia con el IMC (ver valor), así que sale por decisión y no por redundancia estadística. |
| cuida_otras_personas | cantidad_personas_cuida | rho de Spearman = 0,95 | Decisión de la profesora (27-10). El módulo de cuidado queda representado por la cantidad de personas que cuida (0 = no cuida). |
| sobrecarga_fisica_emocional | cantidad_personas_cuida | rho de Spearman = 0,92 | Decisión de la profesora (27-10). El módulo de cuidado queda representado por la cantidad de personas que cuida. Ojo: la cantidad mide intensidad de cuidado, no sobrecarga percibida. |
| a_quien_cuida | cantidad_personas_cuida | no calculable (selección múltiple) | Decisión de la profesora (27-10). Selección múltiple del mismo módulo de cuidado; queda representado por la cantidad. |

Peso y talla siguen en el conjunto limpio; solo salen del conjunto para el modelado. La cantidad de personas que cuida vale 0 para quienes no cuidan y mide intensidad de cuidado, no la sobrecarga percibida.

## 4. Preguntas que no aplican a todas

- **Trabajo** (lugar comprensivo, estrés laboral): quienes no trabajan quedan en la categoría "no aplica / no trabaja" (código 0, fuera de la escala 1-5), en el conjunto general. Así no se pierden participantes y no se confunde "no trabaja" con "no respondió". 22 trabajadoras sin respuesta en lugar de trabajo comprensivo, 22 trabajadoras sin respuesta en estrés del entorno laboral reciben la mediana de las trabajadoras.
- **Menstruación** (regularidad, sangrado, método anticonceptivo): "no aplica" para quienes ya no menstrúan y para las 22 sin fecha de última menstruación.
- **Frecuencias de ejercicio**: 0 = "no lo realiza" (es un valor real: frecuencia cero).

## 5. Filtro por baja variabilidad (> 85 % elimina)

Las categorías se muestran con su código (el significado de cada código está en `resultados/usuaria/diccionario_datos_fase35.csv`).

| Variable | Categoría dominante | % dominancia | Entropía (bits) | Decisión | Justificación |
|---|---|---|---|---|---|
| Género | F | 98,9 % | 0,09 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. |
| Origen | CL | 96,4 % | 0,30 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. |
| Tiene ovarios | Sí | 96,4 % | 0,22 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. |
| Usa terapia hormonal | No | 94,0 % | 0,33 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. |
| Bebidas energéticas al día | 1 | 93,0 % | 0,37 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. |
| Pueblo originario / afro | NINGUNO | 92,2 % | 0,53 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. |
| Marihuana | 1 | 90,5 % | 0,58 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. |
| Tiene útero | Sí | 90,0 % | 0,47 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. |
| Medicamentos para la diabetes | No | 87,5 % | 0,54 | conservar (excepción) | Factor validado por la profesora (20-10) y variable de control; la diabetes es un modificador clínico conocido de los síntomas. |
| Método anticonceptivo | NO_APLICA | 86,4 % | 0,90 | eliminar | La categoría dominante supera el 85 %: casi no varía y no puede discriminar entre participantes. La categoría dominante es "no aplica": la pregunta solo corresponde a muy pocas participantes, así que en el conjunto general casi no aporta información. |
| Frecuencia de ejercicio de fuerza | 0 | 84,7 % | 0,91 | revisar → conservar | Entre 80 % y 85 %: se conserva por relevancia (decisión de la usuaria 2026-10-28). |
| Realiza ejercicio de fuerza | No | 84,7 % | 0,62 | revisar → conservar | Entre 80 % y 85 %: se conserva por relevancia (decisión de la usuaria 2026-10-28). |
| Medicamentos para la presión | No | 83,2 % | 0,65 | revisar → conservar | Entre 80 % y 85 %: se conserva por relevancia (decisión de la usuaria 2026-10-28). |
| Previsión de salud | FONASA | 82,2 % | 0,88 | revisar → conservar | Entre 80 % y 85 %: se conserva por relevancia (decisión de la usuaria 2026-10-28). Variable de control (acceso a salud); no supera el 85 % pero se deja explícita para que la excepción no dependa de pequeñas variaciones. |
| Platos de verduras al día | 2 | 80,7 % | 0,97 | revisar → conservar | Entre 80 % y 85 %: se conserva por relevancia (decisión de la usuaria 2026-10-28). |
| Operada para no tener más hijos | No | 80,3 % | 0,72 | revisar → conservar | Entre 80 % y 85 %: se conserva por relevancia (decisión de la usuaria 2026-10-28). |
| Realiza ejercicio aeróbico | No | 80,2 % | 0,72 | revisar → conservar | Entre 80 % y 85 %: se conserva por relevancia (decisión de la usuaria 2026-10-28). |
| Frecuencia de ejercicio aeróbico | 0 | 80,2 % | 1,10 | revisar → conservar | Entre 80 % y 85 %: se conserva por relevancia (decisión de la usuaria 2026-10-28). |

La dominancia se mide sobre la variable tal como entra al modelo (con el 0 de "no realiza" y la categoría "no aplica"). Por eso la frecuencia de fuerza muestra la misma concentración que "realiza fuerza". El resto de las variables no llega al 80 % (tabla completa en `resultados/usuaria/variables_baja_variabilidad.csv`).

## 6. Filtro por redundancia (|asociación| > 0,80)

Se midieron todos los pares de las variables que quedaban: rho de Spearman entre numéricas, ordinales y binarias, y V de Cramér si una es nominal (la continua se agrupa en quintiles). Si una de las dos tiene "no aplica", el par se mide solo donde ambas aplican; si no, la asociación sería un artefacto de la propia encuesta (por ejemplo, "no aplica" en trabajo equivale a "no trabaja"). Ante un par redundante se conserva, en este orden: la variable de la lista de preferencia, la de control, la con menor % de faltantes y la con más niveles.

| Variable 1 | Variable 2 | Métrica | Valor | Se conserva | Se elimina | Por qué |
|---|---|---|---|---|---|---|
| etapa_menopausica | menstruacion_llega | V de Cramér | 1,00 | etapa_menopausica | menstruacion_llega | etapa_menopausica representa mejor el constructo (lista de preferencia de configuracion.py). |
| realiza_fuerza | frecuencia_fuerza | rho de Spearman | 1,00 | frecuencia_fuerza | realiza_fuerza | frecuencia_fuerza representa mejor el constructo (lista de preferencia de configuracion.py). |
| realiza_aerobico | frecuencia_aerobico | rho de Spearman | 0,99 | frecuencia_aerobico | realiza_aerobico | frecuencia_aerobico representa mejor el constructo (lista de preferencia de configuracion.py). |
| realiza_bajo_impacto | frecuencia_bajo_impacto | rho de Spearman | 0,96 | frecuencia_bajo_impacto | realiza_bajo_impacto | frecuencia_bajo_impacto representa mejor el constructo (lista de preferencia de configuracion.py). |

**Pares que la profesora pidió evaluar (trabajo y alimentación, cuidado).**

| Variable 1 | Variable 2 | Métrica | Valor | Resultado |
|---|---|---|---|---|
| Trabaja actualmente | Falta de tiempo influye en lo que come | rho de Spearman | 0,24 | se conservan ambas |
| Trabaja actualmente | Comidas fuera del hogar | rho de Spearman | 0,32 | se conservan ambas |
| Falta de tiempo influye en lo que come | Comidas fuera del hogar | rho de Spearman | 0,06 | se conservan ambas |
| Trabaja actualmente | Doble carga (trabaja y cuida) | rho de Spearman | 0,52 | se conservan ambas |
| Cantidad de personas que cuida | Doble carga (trabaja y cuida) | rho de Spearman | 0,63 | se conservan ambas |

Se decide con la métrica medida y no por suposición: si el par no supera el umbral, ambas variables se quedan (regla de no manipular el conjunto).

**Pares cercanos al umbral (entre 0,60 y 0,80; se conservan).**

| Variable 1 | Variable 2 | Métrica | Valor |
|---|---|---|---|
| dias_ejercicio_semana | frecuencia_bajo_impacto | rho de Spearman | 0,64 |
| cantidad_personas_cuida | doble_carga | rho de Spearman | 0,63 |

## 7. Validación contra la simulación (no decide nada)

Se compara lo observado con los efectos que la simulación puso a propósito. Que un patrón aparezca no es un descubrimiento: confirma que la limpieza no lo borró. Si no aparece, se informa y no se tocan los datos.

| Relación | Esperado | Subconjunto | n | Observado | p ajustado | Coherencia |
|---|---|---|---|---|---|---|
| IMC | positivo | todas | 267 | +0,250 | < 0,001 | esperado |
| Medicamentos para la diabetes | positivo | todas | 529 | +0,163 | < 0,001 | esperado |
| Doble carga (trabaja y cuida) | positivo | todas | 529 | +0,114 | 0,016 | esperado |
| Sobrecarga por trabajo y cuidado | positivo | quienes cuidan | 251 | +0,230 | < 0,001 | esperado |
| Estrés del entorno laboral | positivo | quienes trabajan | 287 | +0,195 | 0,002 | esperado |
| Lugar de trabajo comprensivo | negativo | quienes trabajan | 287 | -0,269 | < 0,001 | esperado |
| Días de ejercicio a la semana | negativo | todas | 529 | -0,151 | 0,001 | esperado |
| Vasos de agua al día | negativo | todas | 529 | -0,125 | 0,008 | esperado |
| Tabaco | positivo | todas | 529 | +0,144 | 0,002 | esperado |
| Alcohol | positivo | todas | 529 | +0,111 | 0,018 | esperado |
| Marihuana | positivo | todas | 529 | +0,075 | 0,130 | parcial |
| Regularidad de la menstruación | sin asociación | quienes menstrúan | 175 | -0,011 | 1,000 | esperado |
| Tipo de sangrado | sin asociación | quienes menstrúan | 175 | +0,002 | 1,000 | esperado |
| Usa método anticonceptivo | sin asociación | quienes menstrúan | 175 | -0,020 | 0,945 | esperado |
| Operada para no tener más hijos | sin asociación | todas | 529 | +0,043 | 0,410 | esperado |
| Tiene útero | sin asociación | todas | 529 | +0,000 | 1,000 | esperado |
| Tiene ovarios | sin asociación | todas | 529 | +0,001 | 1,000 | esperado |
| Medicamentos para la presión | sin asociación | todas | 529 | +0,050 | 0,326 | esperado |
| Frecuencia de evacuación intestinal | sin asociación | todas | 529 | -0,051 | 0,326 | esperado |
| Distensión abdominal | sin asociación | todas | 529 | -0,069 | 0,167 | esperado |
| Rendimiento laboral afectado | positivo | quienes trabajan | 287 | +0,643 | < 0,001 | esperado |
| Bienestar en el trabajo afectado | positivo | quienes trabajan | 287 | +0,634 | < 0,001 | esperado |
| Ausencias o atrasos por síntomas | positivo | quienes trabajan | 287 | +0,485 | < 0,001 | esperado |
| Cambio en la relación de pareja | positivo | quienes tienen pareja | 328 | +0,568 | < 0,001 | esperado |
| Usa antidepresivos o medicamentos para dormir | positivo | todas | 529 | +0,241 | < 0,001 | esperado |

Resumen: 24 esperados, 1 parciales, 0 no esperados. Los comentarios de cada fila están en `resultados/usuaria/validacion_patrones_simulacion.csv`.

## 8. Conjunto para la Fase 35B (38 predictoras)

| Bloque | Predictoras |
|---|---|
| Control | Edad, Etapa menopáusica, IMC, Previsión de salud, Medicamentos para la diabetes, Trabaja actualmente |
| Identificación | Tiene pareja, Tiene actividad sexual |
| Ginecológica | Tipo de sangrado, Usa método anticonceptivo, Operada para no tener más hijos |
| Salud | Medicamentos para la presión, Frecuencia de evacuación intestinal, Distensión abdominal |
| Trabajo | Lugar de trabajo comprensivo, Estrés del entorno laboral |
| Cuidado | Cantidad de personas que cuida, Doble carga (trabaja y cuida) |
| Actividad física | Días de ejercicio a la semana, Frecuencia de ejercicio aeróbico, Frecuencia de ejercicio de bajo impacto, Frecuencia de ejercicio de fuerza, Horas sentada al día |
| Alimentación | Quién prepara las comidas, Comidas fuera del hogar, Falta de tiempo influye en lo que come, Vasos de agua al día, Platos de verduras al día, Frutas al día, Panes al día, Lácteos al día, Jugos y gaseosas al día, Pescado a la semana, Legumbres a la semana, Carnes a la semana, Dulces y snacks a la semana |
| Sustancias | Tabaco, Alcohol |

Archivo: `datos/analitico/dataset_fase35.csv` (identificador, `severo_mrs`, `mrs_total` y `severidad_mrs_4` como referencia, predictoras e `imc_fue_imputado`). Diccionario con valores permitidos y rol de cada columna: `resultados/usuaria/diccionario_datos_fase35.csv`.

**Verificaciones antes de entregar.**

- ✔ sin fuga de información (objetivo, ítems MRS, consecuencias, auditoría)
- ✔ sin variables del personal de salud
- ✔ no se leyeron dataset_usuaria_verdad.csv ni bitacora_suciedad.csv
- ✔ predictoras sin vacíos
- ✔ IMC numérico tras imputar
- ✔ ordinales con su orden (códigos numéricos)
- ✔ Se regenera con el mismo script, la misma configuración y la semilla 42.

## 9. Productos

- `resultados/usuaria/decisiones_preprocesamiento.csv`: cada decisión, con motivo, regla, efecto en n y fuente.
- `resultados/usuaria/variables_baja_variabilidad.csv`, `pares_redundantes.csv` (y todos los pares en `pares_asociacion_todos.csv`), `imc_imputacion.csv` y `validacion_patrones_simulacion.csv`.
- `resultados/usuaria/log_eda_fase34c_35.txt`: registro de la ejecución, con advertencias y limitaciones.
