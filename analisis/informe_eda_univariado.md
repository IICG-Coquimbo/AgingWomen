# Fase 34D. Análisis univariado variable por variable

*Generado por `analisis/eda_univariado.py` el 30-10-2026. Conjunto: `datos/limpio_usuaria/dataset_usuaria_limpio.csv` (Fase 34B).*

## 1. Propósito y criterios

Acordado en la reunión del 27-10-2026: antes del análisis multivariado se describe cada variable por separado, con un gráfico de barras verticales que muestra el porcentaje y la frecuencia absoluta de cada respuesta. El objetivo es ver qué variables tienen una respuesta que domina (80 % o más) y dónde hay vacíos, antes de filtrar e imputar en la Fase 35A.

- **Participantes.** Se describen las 529 participantes con las 11 preguntas del MRS completas (de 546 tras la limpieza). Las 17 restantes no entran a los análisis con la variable objetivo.
- **Sin imputar.** Los gráficos muestran los datos tal como quedaron tras la limpieza; no se agrega ninguna imputación nueva. El IMC se muestra solo para quienes informaron peso y talla, en los intervalos de la OMS, sin una categoría "no informado".
- **Denominadores.** Preguntas generales: todas las participantes. Preguntas condicionales: solo quienes debían responder (por ejemplo, la frecuencia de fuerza solo entre quienes hacen fuerza; las preguntas de trabajo solo entre quienes trabajan; las de menstruación solo entre quienes aún menstrúan). Selección múltiple: quienes respondieron; los porcentajes pueden sumar más de 100.
- **Faltante.** Participante que debía responder y no tiene dato. Quien no debía responder ("no aplica") no cuenta como faltante.
- **Orden de las barras.** Escalas en su orden lógico; categorías nominales de mayor a menor frecuencia. Las categorías sin casos se muestran con "0,0 % (n = 0)".
- **Baja variabilidad.** Una categoría reúne el 80 % o más de las respuestas válidas (criterio de la profesora). Decisión de la usuaria (28-10-2026): solo se eliminan en la Fase 35A las que **superan el 85 %**; entre 80 % y 85 % se conservan por su relevancia.
- **Entropía de Shannon** (bits): H = −Σ p·log₂(p) sobre las respuestas válidas. Vale 0 si todas responden lo mismo y log₂(k) si las k categorías se reparten igual; la entropía normalizada (H / log₂ k) va de 0 a 1.
- **Imputación de la Fase 34B.** La limpieza imputó por moda o mediana hasta un 7 % de algunas preguntas. Para no esconder ese efecto, el resumen trae la dominancia que quedaría sin esos valores (`pct_dominante_sin_imputados_34B`) y el comentario avisa si cambia de tramo.

## 2. Variables con baja variabilidad

| Variable | Sección | Categoría dominante | % dominante | Entropía (bits) | Tramo |
|---|---|---|---|---|---|
| Género | Identificación | Femenino | 98,9 % | 0.09 | > 85 %: candidata a eliminar |
| Origen | Identificación | Chileno/a | 96,4 % | 0.30 | > 85 %: candidata a eliminar |
| Tiene ovarios | Etapa reproductiva y salud ginecológica | Sí | 96,4 % | 0.22 | > 85 %: candidata a eliminar |
| Usa terapia hormonal | Etapa reproductiva y salud ginecológica | No | 94,0 % | 0.33 | > 85 %: candidata a eliminar |
| Bebidas energéticas al día | Alimentación | No consumo | 93,0 % | 0.37 | > 85 %: candidata a eliminar |
| Pueblo originario / afro | Identificación | Ninguno | 92,2 % | 0.53 | > 85 %: candidata a eliminar |
| Marihuana | Sustancias | Nunca | 90,5 % | 0.58 | > 85 %: candidata a eliminar |
| Tiene útero | Etapa reproductiva y salud ginecológica | Sí | 90,0 % | 0.47 | > 85 %: candidata a eliminar |
| Medicamentos para la diabetes | Medicamentos y digestión | No | 87,5 % | 0.54 | > 85 %: candidata a eliminar |
| Realiza ejercicio de fuerza | Actividad física | No | 84,7 % | 0.62 | 80-85 %: se conserva |
| Medicamentos para la presión | Medicamentos y digestión | No | 83,2 % | 0.65 | 80-85 %: se conserva |
| Previsión de salud | Previsión de salud | Fonasa | 82,2 % | 0.88 | 80-85 %: se conserva |
| Platos de verduras al día | Alimentación | 1-2 porciones | 80,7 % | 0.97 | 80-85 %: se conserva |
| Operada para no tener más hijos | Etapa reproductiva y salud ginecológica | No | 80,3 % | 0.72 | 80-85 %: se conserva |
| Realiza ejercicio aeróbico | Actividad física | No | 80,2 % | 0.72 | 80-85 %: se conserva |

La decisión final de cada una (con las excepciones justificadas) está en la Fase 35A (`resultados/usuaria/variables_baja_variabilidad.csv`). Las de la sección MRS y la variable objetivo no se filtran: se describen como referencia.

## 3. Faltantes

| Variable | Debían responder | Faltantes | % faltante |
|---|---|---|---|
| IMC | 529 | 262 | 49,5 % |
| Peso (kg) | 529 | 249 | 47,1 % |
| Talla (cm) | 529 | 209 | 39,5 % |
| Regularidad de la menstruación | 197 | 22 | 11,2 % |
| Usa método anticonceptivo | 197 | 22 | 11,2 % |
| Tipo de sangrado | 197 | 22 | 11,2 % |
| Lugar de trabajo comprensivo | 309 | 22 | 7,1 % |
| Estrés del entorno laboral | 309 | 22 | 7,1 % |
| A quién cuida | 251 | 16 | 6,4 % |

Peso, talla e IMC concentran los vacíos (muchas participantes no informan sus medidas). Las preguntas de menstruación tienen como faltantes a las participantes sin fecha de última menstruación: no se sabe si les correspondía responder.

## 4. Distribución de variables numéricas y asimetría

Las variables numéricas (edad, peso, talla, IMC, horas sentada al día y puntaje MRS total) se muestran en intervalos en su figura principal y, además, en una figura de distribución con tres elementos:

- **Histograma** de los valores observados (intervalos de 1 unidad en las discretas; 25 intervalos iguales en las continuas).
- **Curva de densidad (KDE)**: estimación de densidad por núcleo gaussiano (`scipy.stats.gaussian_kde`, ancho de banda de Scott). Suaviza el histograma para ver la forma sin depender de dónde caen los cortes de los intervalos. Se escala a participantes por intervalo (n × ancho) para leerla sobre el mismo eje. En el MRS total y las horas sentada (valores enteros) la curva es una aproximación continua de una variable discreta. No se dibuja KDE en las preguntas ordinales con pocas opciones (por ejemplo, días de ejercicio), porque inventaría valores intermedios que no existen.
- **Diagrama de caja** con la regla de Tukey (Q1 − 1,5 × RIC, Q3 + 1,5 × RIC) para ubicar posibles atípicos. Como en la Fase 34, un atípico estadístico no es un error: se conserva si es clínicamente posible.

**Cómo se calculan.** *Asimetría*: coeficiente de Fisher-Pearson ajustado por tamaño muestral (G1, `pandas.Series.skew`). *Curtosis*: exceso de curtosis ajustado (G2, `pandas.Series.kurt`), que vale 0 en una distribución normal. Se calculan sobre los valores observados, sin imputados (peso, talla e IMC solo de quienes los informaron).

| Variable | n | Media | DE | Mediana | Mín. | Máx. | Asimetría | Curtosis | Atípicos (Tukey) | Lectura |
|---|---|---|---|---|---|---|---|---|---|---|
| Edad | 529 | 51,0 | 7,7 | 50,0 | 36,0 | 65,0 | +0,11 | -1,00 | 0 | aproximadamente simétrica; achatada (pocos valores extremos) |
| Peso (kg) | 280 | 71,2 | 15,9 | 69,4 | 40,4 | 122,8 | +0,42 | -0,24 | 1 | aproximadamente simétrica; colas similares a la normal |
| Talla (cm) | 320 | 155,6 | 5,8 | 156,0 | 140,0 | 176,0 | +0,09 | +0,05 | 4 | aproximadamente simétrica; colas similares a la normal |
| IMC | 267 | 29,2 | 6,3 | 28,5 | 18,2 | 45,7 | +0,35 | -0,52 | 0 | aproximadamente simétrica; colas similares a la normal |
| Horas sentada al día | 529 | 6,3 | 2,4 | 6,0 | 1,0 | 14,0 | +0,05 | +0,00 | 2 | aproximadamente simétrica; colas similares a la normal |
| MRS total | 529 | 16,4 | 9,3 | 16,0 | 0,0 | 42,0 | +0,32 | -0,62 | 0 | aproximadamente simétrica; colas similares a la normal |

**Cómo leerla.** Asimetría: |G1| < 0,5 = aproximadamente simétrica; entre 0,5 y 1 = moderada; > 1 = marcada. Positiva = cola hacia los valores altos (la media queda sobre la mediana); negativa = cola hacia los bajos. Curtosis: |G2| < 1 = colas parecidas a la normal; > 1 = colas pesadas (más valores extremos); < −1 = distribución achatada. Estos criterios son orientativos y sirven para elegir el escalado de la Fase 36: con asimetría marcada o colas pesadas conviene el escalado robusto (mediana y RIC) en vez de media y DE.

**Figura 4.1. Variables numéricas: un punto por participante (swarm plot)**

![Swarm plot de las variables numéricas](figuras/eda_univariado/univariado_numericas_puntos.png)

**Qué muestra.** Cada punto es una participante, ubicada según su valor. Así se ven todas las observaciones (no solo su resumen): dónde se concentran, si hay huecos y cuáles quedan lejos del resto. La caja marca la mediana y los cuartiles; los puntos rojos están fuera de la regla de Tukey (1,5 × RIC) y son los posibles atípicos que cuenta la tabla. La altura de cada punto es aleatoria (semilla 42) y solo sirve para que no se tapen entre sí: el eje vertical no significa nada. Se usa este desplazamiento aleatorio en vez de un enjambre exacto porque con valores enteros repetidos (edad, MRS) el enjambre se vuelve demasiado ancho para leerse.

**Por qué solo estas seis.** Son las únicas variables numéricas. El resto son categóricas (sí/no, escalas de pocas opciones u opciones sin orden): en ellas todos los puntos se apilarían en unas pocas columnas, repitiendo el gráfico de barras, y el concepto de atípico no aplica, porque toda respuesta es una opción válida de la encuesta. Para ellas lo relevante es si una categoría es rara o dominante, y eso lo muestran las barras de la sección 5.

## 5. Una figura por variable

### 5.1. Identificación

**Figura 1. Edad** (`edad`)

![Edad](figuras/eda_univariado/univariado_edad.png)

Respuestas repartidas entre 6 categorías (entropía normalizada 0.95).

**Figura 2. Edad: distribución**

![Edad: distribución](figuras/eda_univariado/univariado_edad_distribucion.png)

Histograma con curva de densidad (KDE) y caja de los valores observados (apoyo para la versión en intervalos). Asimetría +0,11: aproximadamente simétrica; curtosis -1,00: achatada (pocos valores extremos).

**Figura 3. Comuna de residencia** (`comuna`)

![Comuna de residencia](figuras/eda_univariado/univariado_comuna.png)

Predomina «La Serena» (31,9 %), sin llegar al 80 %.

**Figura 4. Origen** (`origen_procedencia`)

![Origen](figuras/eda_univariado/univariado_origen_procedencia.png)

Baja variabilidad: «Chileno/a» concentra 96,4 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

**Figura 5. Pueblo originario / afro** (`pueblo_originario_afro`)

![Pueblo originario / afro](figuras/eda_univariado/univariado_pueblo_originario_afro.png)

Baja variabilidad: «Ninguno» concentra 92,2 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

**Figura 6. Género** (`genero`)

![Género](figuras/eda_univariado/univariado_genero.png)

Baja variabilidad: «Femenino» concentra 98,9 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

**Figura 7. Trabaja actualmente** (`trabaja_actualmente`)

![Trabaja actualmente](figuras/eda_univariado/univariado_trabaja_actualmente.png)

Respuestas repartidas entre 2 categorías (entropía normalizada 0.98).

### 5.2. Etapa reproductiva y salud ginecológica

**Figura 8. Etapa menopáusica** (`etapa_menopausica`)

![Etapa menopáusica](figuras/eda_univariado/univariado_etapa_menopausica.png)

Predomina «Posmenopausia» (59,2 %), sin llegar al 80 %.

**Figura 9. Regularidad de la menstruación** (`menstruacion_llega`)

![Regularidad de la menstruación](figuras/eda_univariado/univariado_menstruacion_llega.png)

Predomina «Regular (cada 21-35 días)» (54,9 %), sin llegar al 80 %. Condicional: % sobre quienes aún menstrúan (última menstruación hace menos de 12 meses) (n = 197). Faltante 11,2 % (n = 22).

**Figura 10. Tipo de sangrado** (`tipo_sangrado`)

![Tipo de sangrado](figuras/eda_univariado/univariado_tipo_sangrado.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.89). Condicional: % sobre quienes aún menstrúan (última menstruación hace menos de 12 meses) (n = 197). Faltante 11,2 % (n = 22).

**Figura 11. Usa método anticonceptivo** (`usa_metodo_anticonceptivo`)

![Usa método anticonceptivo](figuras/eda_univariado/univariado_usa_metodo_anticonceptivo.png)

Respuestas repartidas entre 2 categorías (entropía normalizada 0.98). Condicional: % sobre quienes aún menstrúan (última menstruación hace menos de 12 meses) (n = 197). Faltante 11,2 % (n = 22).

**Figura 12. Método anticonceptivo** (`tipo_metodo_anticonceptivo`)

![Método anticonceptivo](figuras/eda_univariado/univariado_tipo_metodo_anticonceptivo.png)

Respuestas repartidas entre 7 categorías (entropía normalizada 0.84). Condicional: % sobre quienes usan método anticonceptivo (n = 72).

**Figura 13. Usa terapia hormonal** (`usa_terapia_hormonal`)

![Usa terapia hormonal](figuras/eda_univariado/univariado_usa_terapia_hormonal.png)

Baja variabilidad: «No» concentra 94,0 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

**Figura 14. Operada para no tener más hijos** (`operada_no_mas_hijos`)

![Operada para no tener más hijos](figuras/eda_univariado/univariado_operada_no_mas_hijos.png)

Baja variabilidad: «No» concentra 80,3 % de las respuestas válidas. Entre 80 % y 85 %: se conserva (decisión de la usuaria 2026-10-28). Ojo: sin los 18 valores imputados en 34B la dominancia baja a 79,6 % y cambia de tramo.

**Figura 15. Tiene útero** (`tiene_utero`)

![Tiene útero](figuras/eda_univariado/univariado_tiene_utero.png)

Baja variabilidad: «Sí» concentra 90,0 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

**Figura 16. Tiene ovarios** (`tiene_ovario`)

![Tiene ovarios](figuras/eda_univariado/univariado_tiene_ovario.png)

Baja variabilidad: «Sí» concentra 96,4 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

**Figura 17. Tiene pareja** (`tiene_pareja`)

![Tiene pareja](figuras/eda_univariado/univariado_tiene_pareja.png)

Respuestas repartidas entre 2 categorías (entropía normalizada 0.91).

**Figura 18. Tiene actividad sexual** (`tiene_actividad_sexual`)

![Tiene actividad sexual](figuras/eda_univariado/univariado_tiene_actividad_sexual.png)

Respuestas repartidas entre 2 categorías (entropía normalizada 1.00).

### 5.3. Medicamentos y digestión

**Figura 19. Medicamentos para la diabetes** (`usa_medicamentos_diabetes`)

![Medicamentos para la diabetes](figuras/eda_univariado/univariado_usa_medicamentos_diabetes.png)

Baja variabilidad: «No» concentra 87,5 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

**Figura 20. Medicamentos para la presión** (`usa_medicamentos_presion`)

![Medicamentos para la presión](figuras/eda_univariado/univariado_usa_medicamentos_presion.png)

Baja variabilidad: «No» concentra 83,2 % de las respuestas válidas. Entre 80 % y 85 %: se conserva (decisión de la usuaria 2026-10-28).

**Figura 21. Frecuencia de evacuación intestinal** (`evacuacion_intestinal`)

![Frecuencia de evacuación intestinal](figuras/eda_univariado/univariado_evacuacion_intestinal.png)

Respuestas repartidas entre 4 categorías (entropía normalizada 0.80).

**Figura 22. Distensión abdominal** (`distension_abdominal`)

![Distensión abdominal](figuras/eda_univariado/univariado_distension_abdominal.png)

Respuestas repartidas entre 4 categorías (entropía normalizada 0.86).

### 5.4. Medidas autodeclaradas

**Figura 23. Peso (kg)** (`peso_kg`)

![Peso (kg)](figuras/eda_univariado/univariado_peso_kg.png)

Respuestas repartidas entre 7 categorías (entropía normalizada 0.93). Faltante 47,1 % (n = 249).

**Figura 24. Peso (kg): distribución**

![Peso (kg): distribución](figuras/eda_univariado/univariado_peso_kg_distribucion.png)

Histograma con curva de densidad (KDE) y caja de los valores observados (apoyo para la versión en intervalos). Asimetría +0,42: aproximadamente simétrica; curtosis -0,24: colas similares a la normal.

**Figura 25. Talla (cm)** (`talla_actual_cm`)

![Talla (cm)](figuras/eda_univariado/univariado_talla_actual_cm.png)

Respuestas repartidas entre 7 categorías (entropía normalizada 0.81). Faltante 39,5 % (n = 209).

**Figura 26. Talla (cm): distribución**

![Talla (cm): distribución](figuras/eda_univariado/univariado_talla_actual_cm_distribucion.png)

Histograma con curva de densidad (KDE) y caja de los valores observados (apoyo para la versión en intervalos). Asimetría +0,09: aproximadamente simétrica; curtosis +0,05: colas similares a la normal.

**Figura 27. IMC** (`imc`)

![IMC](figuras/eda_univariado/univariado_imc.png)

Respuestas repartidas entre 6 categorías (entropía normalizada 0.83). Faltante 49,5 % (n = 262).

**Figura 28. IMC: distribución**

![IMC: distribución](figuras/eda_univariado/univariado_imc_distribucion.png)

Histograma con curva de densidad (KDE) y caja de los valores observados (apoyo para la versión en intervalos). Asimetría +0,35: aproximadamente simétrica; curtosis -0,52: colas similares a la normal.

### 5.5. Previsión de salud

**Figura 29. Previsión de salud** (`prevision`)

![Previsión de salud](figuras/eda_univariado/univariado_prevision.png)

Baja variabilidad: «Fonasa» concentra 82,2 % de las respuestas válidas. Entre 80 % y 85 %: se conserva (decisión de la usuaria 2026-10-28).

### 5.6. Trabajo (solo quienes trabajan)

**Figura 30. Lugar de trabajo comprensivo** (`lugar_trabajo_comprensivo`)

![Lugar de trabajo comprensivo](figuras/eda_univariado/univariado_lugar_trabajo_comprensivo.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.91). Condicional: % sobre quienes trabajan (n = 309). Faltante 7,1 % (n = 22).

**Figura 31. Estrés del entorno laboral** (`estres_entorno_laboral`)

![Estrés del entorno laboral](figuras/eda_univariado/univariado_estres_entorno_laboral.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.92). Condicional: % sobre quienes trabajan (n = 309). Faltante 7,1 % (n = 22).

### 5.7. Cuidado de otras personas

**Figura 32. Cuida a otras personas** (`cuida_otras_personas`)

![Cuida a otras personas](figuras/eda_univariado/univariado_cuida_otras_personas.png)

Respuestas repartidas entre 2 categorías (entropía normalizada 1.00).

**Figura 33. Cantidad de personas que cuida** (`cantidad_personas_cuida`)

![Cantidad de personas que cuida](figuras/eda_univariado/univariado_cantidad_personas_cuida.png)

Respuestas repartidas entre 3 categorías (entropía normalizada 0.91). Condicional: % sobre quienes cuidan a otras personas (n = 251).

**Figura 34. A quién cuida** (`a_quien_cuida`)

![A quién cuida](figuras/eda_univariado/univariado_a_quien_cuida.png)

Selección múltiple: la opción más marcada es «Hijos/as menores de edad» (56,2 % de quienes respondieron); los % pueden sumar más de 100. Condicional: % sobre quienes cuidan a otras personas (n = 251). Faltante 6,4 % (n = 16).

**Figura 35. Sobrecarga por trabajo y cuidado** (`sobrecarga_fisica_emocional`)

![Sobrecarga por trabajo y cuidado](figuras/eda_univariado/univariado_sobrecarga_fisica_emocional.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.86). Condicional: % sobre quienes cuidan a otras personas (n = 251).

**Figura 36. Doble carga (trabaja y cuida)** (`doble_carga`)

![Doble carga (trabaja y cuida)](figuras/eda_univariado/univariado_doble_carga.png)

Respuestas repartidas entre 2 categorías (entropía normalizada 0.85).

### 5.8. Actividad física

**Figura 37. Días de ejercicio a la semana** (`dias_ejercicio_semana`)

![Días de ejercicio a la semana](figuras/eda_univariado/univariado_dias_ejercicio_semana.png)

Predomina «0 días» (57,1 %), sin llegar al 80 %.

**Figura 38. Realiza ejercicio aeróbico** (`realiza_aerobico`)

![Realiza ejercicio aeróbico](figuras/eda_univariado/univariado_realiza_aerobico.png)

Baja variabilidad: «No» concentra 80,2 % de las respuestas válidas. Entre 80 % y 85 %: se conserva (decisión de la usuaria 2026-10-28). Ojo: sin los 29 valores imputados en 34B la dominancia baja a 79,0 % y cambia de tramo.

**Figura 39. Frecuencia de ejercicio aeróbico** (`frecuencia_aerobico`)

![Frecuencia de ejercicio aeróbico](figuras/eda_univariado/univariado_frecuencia_aerobico.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.83). Condicional: % sobre quienes realizan ejercicio aeróbico (n = 105).

**Figura 40. Realiza ejercicio de bajo impacto** (`realiza_bajo_impacto`)

![Realiza ejercicio de bajo impacto](figuras/eda_univariado/univariado_realiza_bajo_impacto.png)

Respuestas repartidas entre 2 categorías (entropía normalizada 0.98).

**Figura 41. Frecuencia de ejercicio de bajo impacto** (`frecuencia_bajo_impacto`)

![Frecuencia de ejercicio de bajo impacto](figuras/eda_univariado/univariado_frecuencia_bajo_impacto.png)

Predomina «A veces» (39,7 %), sin llegar al 80 %. Condicional: % sobre quienes realizan ejercicio de bajo impacto (n = 224).

**Figura 42. Realiza ejercicio de fuerza** (`realiza_fuerza`)

![Realiza ejercicio de fuerza](figuras/eda_univariado/univariado_realiza_fuerza.png)

Baja variabilidad: «No» concentra 84,7 % de las respuestas válidas. Entre 80 % y 85 %: se conserva (decisión de la usuaria 2026-10-28).

**Figura 43. Frecuencia de ejercicio de fuerza** (`frecuencia_fuerza`)

![Frecuencia de ejercicio de fuerza](figuras/eda_univariado/univariado_frecuencia_fuerza.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.81). Condicional: % sobre quienes realizan ejercicio de fuerza (n = 81).

**Figura 44. Horas sentada al día** (`horas_sedentarismo`)

![Horas sentada al día](figuras/eda_univariado/univariado_horas_sedentarismo.png)

Respuestas repartidas entre 4 categorías (entropía normalizada 0.85).

**Figura 45. Horas sentada al día: distribución**

![Horas sentada al día: distribución](figuras/eda_univariado/univariado_horas_sedentarismo_distribucion.png)

Histograma con curva de densidad (KDE) y caja de los valores observados (apoyo para la versión en intervalos). Asimetría +0,05: aproximadamente simétrica; curtosis +0,00: colas similares a la normal.

### 5.9. Alimentación

**Figura 46. Quién prepara las comidas** (`quien_prepara_comidas`)

![Quién prepara las comidas](figuras/eda_univariado/univariado_quien_prepara_comidas.png)

Predomina «Yo preparo la mayoría» (69,0 %), sin llegar al 80 %.

**Figura 47. Comidas fuera del hogar** (`frecuencia_comida_fuera`)

![Comidas fuera del hogar](figuras/eda_univariado/univariado_frecuencia_comida_fuera.png)

Predomina «1-2 veces por semana» (46,7 %), sin llegar al 80 %.

**Figura 48. Falta de tiempo influye en lo que come** (`falta_tiempo_influye`)

![Falta de tiempo influye en lo que come](figuras/eda_univariado/univariado_falta_tiempo_influye.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.85).

**Figura 49. Vasos de agua al día** (`vasos_agua_dia`)

![Vasos de agua al día](figuras/eda_univariado/univariado_vasos_agua_dia.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.89).

**Figura 50. Platos de verduras al día** (`platos_verduras_dia`)

![Platos de verduras al día](figuras/eda_univariado/univariado_platos_verduras_dia.png)

Baja variabilidad: «1-2 porciones» concentra 80,7 % de las respuestas válidas. Entre 80 % y 85 %: se conserva (decisión de la usuaria 2026-10-28). Ojo: sin los 33 valores imputados en 34B la dominancia baja a 79,4 % y cambia de tramo.

**Figura 51. Frutas al día** (`frutas_dia`)

![Frutas al día](figuras/eda_univariado/univariado_frutas_dia.png)

Predomina «1-2 porciones» (71,8 %), sin llegar al 80 %.

**Figura 52. Panes al día** (`panes_dia`)

![Panes al día](figuras/eda_univariado/univariado_panes_dia.png)

Predomina «1-2 porciones» (67,3 %), sin llegar al 80 %.

**Figura 53. Lácteos al día** (`lacteos_dia`)

![Lácteos al día](figuras/eda_univariado/univariado_lacteos_dia.png)

Predomina «1-2 porciones» (66,4 %), sin llegar al 80 %.

**Figura 54. Jugos y gaseosas al día** (`jugos_gaseosas_dia`)

![Jugos y gaseosas al día](figuras/eda_univariado/univariado_jugos_gaseosas_dia.png)

Predomina «1-2 porciones» (48,8 %), sin llegar al 80 %.

**Figura 55. Bebidas energéticas al día** (`bebidas_energeticas_dia`)

![Bebidas energéticas al día](figuras/eda_univariado/univariado_bebidas_energeticas_dia.png)

Baja variabilidad: «No consumo» concentra 93,0 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

**Figura 56. Pescado a la semana** (`pescado_semana`)

![Pescado a la semana](figuras/eda_univariado/univariado_pescado_semana.png)

Predomina «1-2 veces por semana» (56,5 %), sin llegar al 80 %.

**Figura 57. Legumbres a la semana** (`legumbres_semana`)

![Legumbres a la semana](figuras/eda_univariado/univariado_legumbres_semana.png)

Predomina «1-2 veces por semana» (66,5 %), sin llegar al 80 %.

**Figura 58. Carnes a la semana** (`carnes_semana`)

![Carnes a la semana](figuras/eda_univariado/univariado_carnes_semana.png)

Predomina «3-4 veces por semana» (44,2 %), sin llegar al 80 %.

**Figura 59. Dulces y snacks a la semana** (`golosinas_semana`)

![Dulces y snacks a la semana](figuras/eda_univariado/univariado_golosinas_semana.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.84).

### 5.10. Sustancias

**Figura 60. Tabaco** (`tabaco_frecuencia`)

![Tabaco](figuras/eda_univariado/univariado_tabaco_frecuencia.png)

Predomina «Nunca» (75,4 %), sin llegar al 80 %.

**Figura 61. Alcohol** (`alcohol_frecuencia`)

![Alcohol](figuras/eda_univariado/univariado_alcohol_frecuencia.png)

Predomina «1-2 veces por semana» (50,7 %), sin llegar al 80 %.

**Figura 62. Marihuana** (`marihuana_frecuencia`)

![Marihuana](figuras/eda_univariado/univariado_marihuana_frecuencia.png)

Baja variabilidad: «Nunca» concentra 90,5 % de las respuestas válidas. Supera el 85 %: candidata a eliminación en la Fase 35A.

### 5.11. Síntomas (MRS) y variable objetivo

**Figura 63. Bochornos y sudoración** (`pregunta_1`)

![Bochornos y sudoración](figuras/eda_univariado/univariado_pregunta_1.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.90).

**Figura 64. Molestias al corazón** (`pregunta_2`)

![Molestias al corazón](figuras/eda_univariado/univariado_pregunta_2.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.85).

**Figura 65. Dolor muscular y articular** (`pregunta_3`)

![Dolor muscular y articular](figuras/eda_univariado/univariado_pregunta_3.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.95).

**Figura 66. Problemas de sueño** (`pregunta_4`)

![Problemas de sueño](figuras/eda_univariado/univariado_pregunta_4.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.93).

**Figura 67. Ánimo depresivo** (`pregunta_5`)

![Ánimo depresivo](figuras/eda_univariado/univariado_pregunta_5.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.95).

**Figura 68. Irritabilidad** (`pregunta_6`)

![Irritabilidad](figuras/eda_univariado/univariado_pregunta_6.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.96).

**Figura 69. Ansiedad** (`pregunta_7`)

![Ansiedad](figuras/eda_univariado/univariado_pregunta_7.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.94).

**Figura 70. Cansancio físico y mental** (`pregunta_8`)

![Cansancio físico y mental](figuras/eda_univariado/univariado_pregunta_8.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.95).

**Figura 71. Problemas sexuales** (`pregunta_9`)

![Problemas sexuales](figuras/eda_univariado/univariado_pregunta_9.png)

Respuestas repartidas entre 5 categorías (entropía normalizada 0.81).

**Figura 72. Problemas urinarios** (`pregunta_10`)

![Problemas urinarios](figuras/eda_univariado/univariado_pregunta_10.png)

Predomina «Ninguna» (50,3 %), sin llegar al 80 %.

**Figura 73. Sequedad vaginal** (`pregunta_11`)

![Sequedad vaginal](figuras/eda_univariado/univariado_pregunta_11.png)

Predomina «Ninguna» (40,3 %), sin llegar al 80 %.

**Figura 74. MRS total** (`mrs_total`)

![MRS total](figuras/eda_univariado/univariado_mrs_total.png)

Respuestas repartidas entre 9 categorías (entropía normalizada 0.90).

**Figura 75. MRS total: distribución**

![MRS total: distribución](figuras/eda_univariado/univariado_mrs_total_distribucion.png)

Histograma con curva de densidad (KDE) y caja de los valores observados (apoyo para la versión en intervalos). Asimetría +0,32: aproximadamente simétrica; curtosis -0,62: colas similares a la normal.

**Figura 76. Severidad MRS (4 clases)** (`severidad_mrs_4`)

![Severidad MRS (4 clases)](figuras/eda_univariado/univariado_severidad_mrs_4.png)

Respuestas repartidas entre 4 categorías (entropía normalizada 0.85).

**Figura 77. MRS severo (16 puntos o más)** (`severo_mrs`)

![MRS severo (16 puntos o más)](figuras/eda_univariado/univariado_severo_mrs.png)

Respuestas repartidas entre 2 categorías (entropía normalizada 1.00).

## 6. Variables que no se describen

| Motivo | Variables |
|---|---|
| identificadores y control de registro | `participante_id`, `uuid_local`, `rut_hash`, `usuario_id`, `ronda`, `ronda_actual`, `origen_registro`, `excepcion_edad` |
| fechas administrativas o de origen | `sincronizado_en`, `creado_en`, `ultima_finalizacion_en`, `fecha_evaluacion`, `fecha_nacimiento`, `fecha_registro`, `fecha_ultimo_empa`, `fecha_ultima_menstruacion (se usa vía etapa)` |
| solo personal de salud (reunión 2026-10-20) | `talla_maxima_cm`, `circunferencia_cintura_cm`, `presion_sistolica`, `presion_diastolica`, `colesterol_total_mg_dl`, `colesterol_hdl_mg_dl`, `trigliceridos_mg_dl`, `glicemia_mg_dl`, `vdrl_rpr`, `riesgo_cv_atp3`, `fecha_ultimo_pap`, `resultado_pap`, `fecha_mamografia`, `resultado_birads`, `fecha_ecotomografia_mamaria`, `perdida_talla_cm`, `presion_elevada` |
| consecuencias del MRS (módulo aparte) | `rendimiento_afectado`, `bienestar_trabajo_afectado`, `frecuencia_ausencias`, `cambio_relacion_pareja_menopausia`, `usa_antidepresivos` |
| decisión del equipo (nivel educacional, ConocimientoSistema, satisfacción) | `nivel_educacion`, `conoce_sistema_publico_climaterio`, `… (ConocimientoSistema completo salvo previsión)`, `facilidad_uso`, `fatiga_mental`, `comodidad_diseno`, `recomendaria`, `incomodidad` |
| constante en el conjunto | `region_residencia (100 % Coquimbo)` |
| texto libre de "otro" | `tipo_metodo_anticonceptivo_otro`, `a_quien_cuida_otro`, `quien_prepara_comidas_otro`, `comentario_incomodidad` |
| derivadas repetidas o marcas de limpieza | `tramo_edad (= intervalos de edad)`, `imc_categoria (= intervalos OMS)`, `mrs_somatico`, `mrs_psicologico`, `mrs_urogenital`, `mrs_completo`, `meses_desde_fum`, `incoherencia_*`, `*_imputado` |
