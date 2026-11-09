# Protocolo de la Fase 38: reglas de asociación generales

Este protocolo se redacta y se sella con SHA-256 **antes de calcular ninguna regla**. Después del sellado no se modifica. Cualquier ajuste posterior irá en una nota aparte, rotulada como exploratoria.

## 1. Objetivo y alcance

1. **Objetivo:** describir qué combinaciones de características generales, hábitos y condiciones de vida aparecen con más o menos frecuencia junto a síntomas severos de menopausia en el conjunto sintético de 529 participantes.
2. **Resultado:** `severo_mrs = 1` cuando `mrs_total ≥ 16`, con 281 participantes (53,1 %). Su complemento es `severo_mrs = 0`, con 248 (46,9 %).
3. **Alcance:** la fase es exploratoria y descriptiva. No produce diagnósticos, predicciones clínicas ni recomendaciones, y no atribuye causalidad.
4. **No es una confirmación independiente.** Las asociaciones con el MRS ya se examinaron:
   - **Fases 34C, 35A y 35B:** FCBF, permutaciones y Random Forest.
   - **Fase 37D:** 11 de 36 características se asociaron con el MRS total, todas con efecto pequeño (diabetes, IMC, sobrecarga, estrés laboral, tabaco, trabajo, alcohol, lugar de trabajo comprensivo, ejercicio de bajo impacto, días de ejercicio y agua).
   
   Esos resultados se conocen al redactar este protocolo y **no se usan para elegir variables, cortes ni reglas**.
5. **Fuera de alcance:** las Fases 39 y 40 no se inician.

## 2. Población, identificadores y fuentes

- **Participantes:** las 529 con MRS completo, en el orden y con los identificadores de `fase36/matrices/identificadores.csv`.
- **Carga:** se reutiliza la carga verificada de la Fase 37D (`nucleo_37d.cargar`), importada sin escribir en su carpeta. Esa carga:
  - recalcula el MRS desde los 11 ítems;
  - exige que coincida con la limpieza y con `severo_mrs` de la Fase 35;
  - entrega los códigos del instrumento según las definiciones de la Fase 36 (P2), con el estado de cada celda (observada, imputada, deducida o con pregunta madre imputada).
- **Significado de las respuestas:** se toma del esquema de la Fase 36, del diccionario de la limpieza y de los textos de las preguntas en la definición de la encuesta (`src/apps/encuestas/models.py`, solo lectura). No se infiere un significado por el nombre de la variable.
- **Prohibiciones:**
  - No se abre ningún archivo del simulador (`verdad`, `bitacora`, `dataset_usuaria_sucio`). Un gancho de auditoría lo impide y registra cada lectura.
  - No se usan las etiquetas de clustering (A, B1) como antecedentes.

## 3. Variables

### 3.1 Análisis principal: 31 variables medidas en las 529

| Bloque | Variables |
|---|---|
| Contexto | `trabaja_actualmente`, `tiene_pareja`, `cantidad_personas_cuida` |
| Actividad física | `dias_ejercicio_semana`, `frecuencia_aerobico`, `frecuencia_bajo_impacto`, `frecuencia_fuerza`, `horas_sedentarismo` |
| Alimentación e hidratación | `quien_prepara_comidas`, `carnes_semana`, `falta_tiempo_influye`, `frecuencia_comida_fuera`, `frutas_dia`, `golosinas_semana`, `jugos_gaseosas_dia`, `lacteos_dia`, `legumbres_semana`, `panes_dia`, `pescado_semana`, `platos_verduras_dia`, `vasos_agua_dia` |
| Tabaco y alcohol | `tabaco_frecuencia`, `alcohol_frecuencia` |
| Generales y salud | `edad`, `operada_no_mas_hijos`, `usa_medicamentos_presion`, `usa_medicamentos_diabetes`, `prevision` |
| Próximas a síntomas (marcadas) | `tiene_actividad_sexual`, `distension_abdominal`, `evacuacion_intestinal` |

**Criterio de inclusión:** son todas las características generales disponibles para las 529, salvo las excluidas en 3.2 por razones documentadas. **Ninguna se incluye ni se excluye por su asociación con el MRS.**

- **Variables marcadas:**
  - `tiene_actividad_sexual` se solapa con el ítem 9 (problemas sexuales).
  - `distension_abdominal` y `evacuacion_intestinal` son molestias digestivas, cercanas a los síntomas somáticos.
  
  Se mantienen en el análisis principal con advertencia, y la sensibilidad S6 las excluye.
- **Diabetes y previsión:** no tienen marca de imputación por participante. Según la Fase 34D, diabetes tiene 23 celdas imputadas y previsión 19 imputadas y 2 deducidas. Se mantienen, con advertencia, y quedan fuera de S1.

### 3.2 Excluidas del análisis principal

| Variable | Motivo | Dónde se analiza |
|---|---|---|
| MRS total, dimensiones, ítems, severidad y derivados | Son el resultado | Solo como consecuente (`severo_mrs`) |
| Segmentos A, B1 y otras etiquetas | Restricción de la fase | Nota para la Fase 39 |
| `imc` | Solo 267 observados (50,5 %) | S8 |
| `lugar_trabajo_comprensivo`, `estres_entorno_laboral` | Solo para quienes trabajan. Además, sus preguntas mencionan los síntomas («comprensivo frente a estos síntomas»; estrés «que intensifique sus síntomas»), así que la circularidad es directa | S7a, con advertencia |
| `sobrecarga_fisica_emocional` | Solo para quienes cuidan | S7b |
| `etapa_menopausica` | Decisión del 01-11: solo descriptiva. Además, depende de preguntas menstruales excluidas | No se usa como antecedente |

## 4. Transformación de respuestas en ítems

### 4.1 Reglas de agrupación

Se fijan aquí y se aplican de forma automática. Usan **solo las frecuencias marginales de las 529, sin el MRS**. Al sellar se conocen estas frecuencias por la tabla de la Fase 37D. El umbral es el 5 %, es decir, 27 participantes (26,45 redondeado hacia arriba).

- **R1. Categorías suficientes:** una categoría con 27 participantes o más se conserva tal cual.
- **R2. Categorías ordinales escasas:**
  - Una categoría ordinal con menos de 27 se une a su vecina adyacente de **menor frecuencia**. Si las dos vecinas tienen igual frecuencia, se une hacia el centro de la escala.
  - Se repite hasta que todas tengan al menos 27, o la variable quede con 2 niveles.
  - La categoría unida se nombra con el rango original (por ejemplo, «5 o más días»).
- **R3. Categorías nominales escasas:** una categoría nominal con menos de 27 y sin vecina compatible no genera ítem. Esas participantes no tienen ítem en esa variable, y se documenta. Así ocurre con:
  - `quien_prepara_comidas`: «compro comida preparada» (22) y «otro» (7).
  - `prevision`: FFAA (7), NINGUNA (15) y NS (2). Son significados distintos y no se mezclan.
- **R4. Binarias:** se conservan como «sí» y «no». En la principal ninguna tiene menos de 27 en un nivel.
- **R5. Numéricas:** cortes fijados de antemano por su significado, no por los datos.
  - Edad: 36-44, 45-54 y 55-65 años.
  - Horas sentada al día: menos de 6, 6-7, y 8 o más (8 horas es un umbral habitual de tiempo sedentario alto).
  - IMC (solo en S8), según las categorías de la OMS: menos de 25, 25-29,9, y 30 o más.
- **R6. «No aplica» estructural** en ejercicio y cuidado («no realiza», «no cuida»): es una respuesta sustantiva, no un dato faltante, y conserva su ítem («no realiza ejercicio aeróbico», «no cuida»). No se crean ítems de «no aplica» para los módulos laboral y de cuidados: solo reproducirían su pregunta de entrada.
- **R7. Faltantes:** un valor faltante no genera ítem. Nunca se confunde con una respuesta negativa.

### 4.2 Consecuentes

Hay dos: `severo_mrs=SI` y `severo_mrs=NO`. Nunca son antecedentes.

### 4.3 Transacciones

- **Forma:** una transacción por participante, con su identificador original, un ítem por variable como máximo, y su ítem de consecuente.
- **Verificación:**
  - Ninguna transacción tiene dos estados de la misma variable.
  - El ítem `severo_mrs` reproduce los 529 valores históricos.
- **Archivos:** las transacciones de cada sensibilidad se guardan por separado de las principales.

## 5. Diseño de las reglas

- **Forma:** antecedente → consecuente, con un solo consecuente (`severo_mrs=SI` o `severo_mrs=NO`).
- **Longitud:** el antecedente tiene 1, 2 o 3 condiciones. Tres se justifica porque las tres preguntas de contexto (trabajo, pareja, ejercicio) se combinaban en la Fase 37C. No hay más de 3, para evitar reglas demasiado específicas.
- **Una variable por antecedente:** ninguna variable aparece dos veces, lo que ya garantiza la transacción.
- **Ítems determinados:** se excluye todo antecedente que contenga dos ítems a y b tales que todas las participantes con a tienen también b. Así se evita que una condición quede determinada lógicamente por otra. Se calcula solo con los antecedentes, sin el MRS.
- **Jerarquías:** en las sensibilidades S7, la pregunta de entrada (trabaja, cuida) no se combina con las preguntas de su módulo. La subpoblación ya la fija.
- **Dirección:** cada antecedente se evalúa con los dos consecuentes. Se informa como regla la dirección con lift > 1, la del consecuente que el antecedente hace más frecuente. La otra dirección es su complemento exacto: confianza 1 − c.
- **Exhaustividad:** la búsqueda recorre **todo** el espacio definido aquí, y las reglas se evalúan todas con los mismos criterios. No se eligen reglas atractivas después.

## 6. Algoritmos

- **Implementaciones:** Apriori y FP-Growth, escritos en el propio código del proyecto. `mlxtend` no está instalado y no se instala, para no modificar el entorno.
- **Comparación:** los dos se comparan con una **enumeración exhaustiva**, sobre las mismas transacciones y con los mismos parámetros:
  - Conjuntos frecuentes de hasta 3 ítems de antecedente más, como máximo, un consecuente.
  - Soporte mínimo conjunto de 27.
  - Exigencia: los mismos conjuntos, con los mismos recuentos, y las mismas reglas.
- **Registro:** versiones de Python, NumPy, pandas y SciPy; duración; y memoria máxima (`tracemalloc`).
- **El algoritmo no se elige por las reglas que entrega.** Si son equivalentes, las sensibilidades usan FP-Growth.
- **Referencia nula y estabilidad:** usan un evaluador matricial sobre los mismos antecedentes frecuentes. Con agrupaciones fijas, los antecedentes frecuentes no dependen del consecuente, así que permutar el consecuente o tomar una submuestra equivale a recontar los mismos antecedentes. Una prueba lo verifica: compara el evaluador con FP-Growth ejecutado de nuevo en permutaciones y submuestras.

## 7. Umbrales y medidas

### 7.1 Umbrales

| Configuración | Antecedente mínimo (n_A) | Conjunto mínimo (antecedente y consecuente) |
|---|---|---|
| Principal | 53 (10 %) | 27 (5 %) |
| S3-bajo | 27 (5 %) | 14 |
| S3-alto | 80 (15 %) | 40 |

- **Confianza mínima:** no hay. La frecuencia basal es de 53,1 %, así que la confianza sola no basta para destacar.
- **Grilla cerrada:** no se agregan umbrales más bajos aunque no aparezcan reglas.

### 7.2 Medidas por regla

Con A el antecedente, C el consecuente, n = 529 (o la subpoblación) y p₀ la frecuencia basal de C:

- **n_A**, **n_AC**, **soporte** = n_AC / n y **soporte del antecedente** = n_A / n.
- **Confianza** c = n_AC / n_A, con su IC 95 % de Wilson.
- **Lift** = c / p₀.
- **Diferencia respecto de la basal:** c − p₀.
- **Leverage:** soporte − (n_A / n)·p₀.
- **Diferencia de riesgo frente a quienes no cumplen A:** c − c(¬A), con IC 95 % de Newcombe (método 10).
- **Razón de riesgos** c / c(¬A), con IC 95 % logarítmico de Katz.
- **Estadístico estandarizado** z = (c − p₀) / √(p₀(1 − p₀) / n_A), que solo se usa para ordenar y para la referencia nula.
- **p de Fisher (bilateral)** para A frente a ¬A. Es un p **ordinario**: la regla se descubrió con los mismos datos, así que no confirma nada.
- **q de Benjamini-Hochberg** aplicado a **todas** las reglas evaluadas de la configuración, no solo a las seleccionadas. Se informa como referencia; el control principal de la búsqueda es la referencia nula.

## 8. Referencia nula (control de la búsqueda múltiple)

- **Permutaciones:** 1.000 del consecuente (semilla 42). Cada una conserva todas las características de cada participante y rompe su relación con la severidad. En las subpoblaciones se permuta dentro de la subpoblación.
- **Búsqueda completa en cada permutación:** misma población, mismos ítems y mismos umbrales. Se guardan:
  - el máximo de |z| entre todas las reglas;
  - el número de reglas «marcadas» (sección 9);
  - la mayor diferencia |c − p₀| entre las reglas con n_A ≥ umbral.
- **Valor p ajustado por toda la búsqueda** (máximo estadístico, Westfall-Young de un paso): para cada regla, es la proporción de permutaciones cuyo máximo |z| alcanza o supera el |z| observado. Una regla **supera la referencia nula** si ese p es menor que 0,05.
- **Comparación de conjunto:** número de reglas marcadas observadas frente a su distribución nula (media y percentil 95).

## 9. Criterios de evaluación y clasificación

**Regla marcada:** n_A ≥ umbral, n_AC ≥ umbral conjunto, y |c − p₀| ≥ 0,10. Para `SI`, esto es una confianza de 63,1 % o más (lift ≥ 1,19). Para `NO`, 56,9 % o más (lift ≥ 1,21).

**Redundancia (mejora mínima):** una regla de 2 o 3 condiciones es redundante si alguna regla con un subconjunto propio de su antecedente, en la misma dirección, tiene una confianza menor en menos de 0,05. Es decir, si agregar la condición mejora la confianza en menos de 5 puntos. Las reglas que comparten las mismas variables y la misma dirección forman una **familia**.

**Estabilidad:**
- **Submuestras:** 200 del 80 % sin reemplazo (423 participantes; semilla 42). En cada una se redescubren las reglas con los mismos ítems y agrupaciones, y con umbrales proporcionales: n_A ≥ 10 % y n_AC ≥ 5 % de la submuestra.
- **Por regla se mide:**
  - la frecuencia con que reaparece como marcada;
  - la frecuencia con que mantiene la dirección;
  - la variación de soporte, confianza y lift (percentiles 2,5 y 97,5);
  - el número de reglas marcadas nuevas y desaparecidas.
- **Por familia:** la proporción de submuestras en que aparece marcada al menos una regla de la familia.
- **Regla estable:** reaparece como marcada en al menos el 70 % de las submuestras y mantiene la dirección en al menos el 95 %.
- **Sin fuga:** las agrupaciones se fijaron con las 529 y sin el MRS, y no se reajustan en las submuestras. No hay ninguna preparación ajustada con el consecuente.

**Clasificación** (excluyente, en este orden):
1. **Soporte insuficiente:** solo en S3-bajo, 27 ≤ n_A < 53.
2. **Asociación débil:** |c − p₀| < 0,10.
3. **Redundante.**
4. **Compatible con la referencia nula:** p ajustado ≥ 0,05.
5. **Inestable:** no cumple el criterio de estabilidad.
6. **Asociación descriptiva relativamente más marcada:** cumple todo lo anterior. Solo estas son **reglas sólidas para destacar**.

**Tabla de destacadas:**
- Contiene todas las reglas de la clase 6.
- Si hay menos de 10, se agrega una tabla aparte, rotulada «no destacadas», con las 10 reglas no redundantes de mayor |z| para cada consecuente y su clase. Así se ve qué hay, sin presentarlo como hallazgo.

**Conclusión de ausencia:** si ninguna regla queda en la clase 6, la conclusión es: «no se encontraron reglas suficientemente sólidas para destacar». No se cambian los umbrales ni los criterios para evitarla.

## 10. Sensibilidades

Todas usan FP-Growth, los mismos criterios de la sección 9 y 1.000 permutaciones propias. La estabilidad por submuestras se calcula solo en la configuración principal, por costo. Esa limitación se declara.

| Código | Cambio respecto de la principal | Población |
|---|---|---|
| S1 | Sin valores imputados: las celdas imputadas o deducidas, o con pregunta madre imputada, no generan ítem. Se excluyen diabetes y previsión por no tener marca | 529 |
| S2a | Categorías originales, sin agrupar (R2 desactivada; las de menos de 27 no alcanzan los umbrales) | 529 |
| S2b | Agrupación gruesa fijada aquí (ver abajo) | 529 |
| S3-bajo / S3-alto | Umbrales de 7.1 | 529 |
| S4-1 / S4-2 | Antecedentes de 1 condición como máximo / de 2 como máximo | 529 |
| S5 | Sin las frecuencias de ejercicio aeróbico, bajo impacto y fuerza, que son redundantes con los días de ejercicio | 529 |
| S6 | Sin actividad sexual, distensión ni evacuación | 529 |
| S7a | Quienes trabajan, más lugar comprensivo y estrés laboral (desacuerdo 1-2, neutral 3, acuerdo 4-5; estrés nada o leve 1-2, moderado 3, alto o extremo 4-5), sin el ítem de trabajo. Umbrales: 10 % y 5 % de la subpoblación | 309 |
| S7b | Quienes cuidan, más sobrecarga (nunca o rara vez 1-2, a veces 3, frecuentemente o siempre 4-5), sin «no cuida». Mismos umbrales proporcionales | 251 |
| S8a / S8b | Con IMC observado: S8a sin IMC; S8b con categorías de IMC. La comparación separa el efecto de la subpoblación del efecto del IMC | 267 |

**Agrupación gruesa S2b** (por significado del instrumento):
- **Ejercicio:**
  - Días: 0, 1-2, y 3 o más.
  - Aeróbico, bajo impacto y fuerza: no realiza frente a realiza.
- **Contexto:** cuida, no frente a sí.
- **Frecuencias semanales** (carnes, golosinas, legumbres, pescado, comidas fuera): 2 veces o menos frente a 3 o más.
- **Porciones diarias** (frutas, jugos, lácteos, panes, verduras, agua): 2 o menos frente a 3 o más.
- **Frecuencias subjetivas** (falta de tiempo, distensión): hasta «a veces» frente a «frecuentemente o siempre».
- **Tabaco y alcohol:** nunca frente a alguna vez.
- **Evacuación:** al menos 1 vez al día frente a menos.
- **Numéricas:** edad, menos de 50 frente a 50 o más; horas sentada, menos de 8 frente a 8 o más.
- **Sin cambio:** el resto queda como en la principal.

**Lectura de cada regla marcada de la principal en cada sensibilidad:**
- Se mantiene (marcada, misma dirección).
- Se debilita (misma dirección, |c − p₀| < 0,10).
- Cambia de dirección.
- Desaparece por falta de casos (n_A bajo el umbral).
- No evaluable (variable excluida o constante).

**Tamaños:** se informan siempre el tamaño efectivo y la cobertura. Una subpoblación nunca se presenta como si fueran 529.

## 11. Pruebas e integridad

**Pruebas:**
- **Datos:** 529 únicas, identificadores, correspondencia con las fuentes y `severo_mrs` correcto.
- **Antecedentes:** ningún ítem del MRS, ninguna contradicción y ningún par determinado.
- **Codificación:** agrupaciones según R1-R7, imputaciones (S1) y módulos parciales.
- **Medidas:** soporte, confianza, lift, leverage, diferencia y razón de riesgos.
- **Algoritmos:** equivalencia de los tres y del evaluador matricial, y reproducibilidad.
- **Estabilidad y nula:** estabilidad sin fuga y referencia nula correcta (bajo una permutación, las reglas marcadas son las esperadas por azar).
- **Selección y trivialidad:** multiplicidad declarada y ausencia de reglas triviales.
- **Integridad y plataforma:** fases anteriores intactas y Django sin cambios.
- **Controles negativos:** errores introducidos en memoria, que alguna prueba debe detectar.

**Integridad:**
- Se comparan los manifiestos de las Fases 34-35, 36, 37A, 37B, 37C, del complemento y de la 37D, al inicio y al final.
- Se revisa git: HEAD 745d689, sin cambios en `src/` ni en datos versionados.
- No hay commit ni push.

## 12. Recursos

- Un proceso de análisis, con un hilo por biblioteca numérica, más el vigilante de memoria: dos procesos en total.
- Las permutaciones y submuestras se procesan por lotes y se guardan para poder reanudar.
- Si falta memoria, la etapa se detiene, se conserva lo hecho y se documenta lo pendiente. No se cambian los criterios.

## 13. Limitaciones conocidas de antemano

- Datos sintéticos.
- Análisis no ciego (sección 1.4).
- Asociaciones marginales, sin ajuste.
- Imputaciones de la limpieza en el 72,8 % de las participantes, en alguna variable.
- Diabetes y previsión sin marca de imputación.
- Las mismas 529 se usan para descubrir y evaluar, sin muestra de confirmación.
- La estabilidad no es validez clínica.
