
Este protocolo se sella con SHA-256 antes de ejecutar cualquier búsqueda condicionada. Las modificaciones posteriores al sellado se registran en `protocolo/02_modificaciones_posteriores.md` y se identifican como exploratorias.

## 0. Carácter del análisis y revisión inicial

**El análisis es exploratorio.** Las subpoblaciones y la hipótesis general («la asociación entre hábitos y severidad cambia según el contexto») se definieron **después** de conocer los resultados de las Fases 37D y 38:
- **Fase 37D:** asociaciones pequeñas del MRS con trabajo, pareja y días de ejercicio.
- **Fase 38:** una señal general difusa, sin reglas individuales robustas. Los patrones que más se repetían incluían trabajo y ejercicio.

Sellar el protocolo antes de ejecutar evita ajustar los criterios a los resultados de esta fase, pero no convierte el análisis en confirmatorio. Todo se hace sobre las 529 participantes **sintéticas** con MRS completo, y ningún resultado se interpreta como causal ni clínico.

**Revisión hecha antes de redactar.** Revisé:
- de la Fase 38: el protocolo, el diccionario, la matriz transaccional principal, las reglas generales, la estabilidad, la referencia nula, las sensibilidades, el informe de cierre y la nota para la Fase 39;
- de la Fase 37D: el núcleo de carga y las etiquetas históricas.

**Información conocida antes de sellar:** el tamaño de cada estrato y su frecuencia basal de MRS severo, publicados en la nota de la Fase 38. No se conoce ninguna regla calculada dentro de un estrato ni ninguna comparación entre estratos.

## 1. Subpoblaciones

Hay cuatro dimensiones. Cada una divide a las 529 en estratos que no se superponen. Las dimensiones sí se superponen entre sí: una participante pertenece a un estrato de cada dimensión.

| Dimensión | Estratos (código del instrumento, Fase 36) | n conocido |
|---|---|---|
| Trabajo | trabaja (1) / no trabaja (0) | 309 / 220 |
| Pareja | tiene pareja (1) / no tiene pareja (0) | 356 / 173 |
| Ejercicio | 0 días / 1-2 días / 3 días o más (3-4, 5-6 y todos los días) | 302 / 148 / 79 |
| Cuidado | cuida a una o más personas / no cuida | 251 / 278 |

- **Ejercicio:** el nivel «3 días o más» se fija por el significado de las respuestas, como en B1 y en la sensibilidad S2b de la Fase 38. No se usa el MRS para definirlo.
- **Sin cruces:** no se analizan combinaciones entre dimensiones, como «trabaja y tiene pareja».
- **Pertenencia:** cada participante se asigna a su estrato con su código en la Fase 36. No hay faltantes en estas cuatro variables.

**Comparación secundaria con A y B1 (sección 12).** Se recuperan las etiquetas históricas, sin reconstruirlas:
- **A:** `P2_c12_km_k4`, desde `37C_comparacion_seleccion/seleccion/artefactos_provisionales/P2_c12_km_k4/etiquetas.csv`.
- **B1:** desde `37C_complemento_tres_preguntas/asignaciones/etiquetas_alternativas.csv`, columna `B1_doble_uso`. Se exige que coincida con la regla de cuatro pasos.

## 2. Variables admisibles

Son las 31 variables principales de la Fase 38, con su misma codificación en ítems.

- **Excluida en cada estrato:** la variable que define la dimensión. En trabajo no entra «trabaja»; en pareja no entra «tiene pareja»; en ejercicio no entran los días de ejercicio; en cuidado no entran las personas a su cuidado.
- **Ítems constantes o vacíos:** un ítem que todas o ninguna participantes del estrato cumplen se quita en ese estrato.
- **Frecuencias de ejercicio en «0 días»:** las frecuencias de aeróbico, bajo impacto y fuerza no son estructurales, pero en ese estrato casi todas responden «no realiza» (por ejemplo, 285 de 302 en aeróbico). Las otras categorías tendrán pocos casos y en general no alcanzarán los umbrales. No se tratan de forma especial.
- **Pares determinados:** se excluyen los antecedentes con dos ítems en que uno implica al otro dentro del estrato.
- **Siguen excluidos de la búsqueda principal**, como en la Fase 38:
  - el IMC, porque falta en la mitad;
  - el módulo laboral, porque sus preguntas mencionan los síntomas;
  - la sobrecarga por cuidar;
  - la etapa menopáusica;
  - el MRS, sus ítems, sus dimensiones y sus categorías;
  - las etiquetas de clustering.
- **Solo en sensibilidades:** el módulo laboral (S7a) y la sobrecarga (S7b), cada uno dentro del único estrato donde aplica.

## 3. Consecuentes

- **Consecuentes:** `severo_mrs=SI` (mrs_total ≥ 16) y su complemento `severo_mrs=NO`.
- **Recálculo:** se recalcula desde los 11 ítems y debe reproducir 281 participantes con síntomas severos y 248 sin ellos, la limpieza y la Fase 35.
- **Dirección:** cada antecedente produce una sola regla, en la dirección con lift > 1 dentro de su estrato, como en la Fase 38.
- **Corte:** no se modifica el corte del MRS.

## 4. Codificación de ítems

Se reutiliza exactamente la preparación principal de la Fase 38: las reglas R1 a R7, los 94 ítems, las agrupaciones fijadas con las 529 y sin el MRS, y el «no aplica» estructural como respuesta sustantiva.

- **Sin reagrupar:** dentro de un estrato no se vuelve a agrupar nada, aunque una categoría quede con pocas participantes. Si queda por debajo del umbral, simplemente no forma reglas.
- **Estados de las celdas:** se conservan como en la Fase 38 los estados observado, imputado, deducido y no aplica. Solo S1 los cambia.
- **Verificación:** la matriz de ítems de las 529 debe ser idéntica a `preparacion/matriz_transaccional_principal.csv` de la Fase 38.

## 5. Redundancia y circularidad

- **Redundancia dentro del estrato:** se aplica el criterio de la Fase 38. Una regla de 2 o 3 condiciones es redundante si una regla más simple, con parte de sus condiciones y en la misma dirección, tiene una confianza menor en menos de 5 puntos.
- **Redundancia entre estratos:** una diferencia entre estratos para un antecedente de dos condiciones es redundante si alguna de sus condiciones, sola, produce una diferencia (rango de diferencias de riesgo) mayor o igual a la del par menos 0,05.
- **Ejercicio:** las frecuencias de aeróbico, bajo impacto y fuerza dependen de los días de ejercicio. Dentro de la dimensión ejercicio, las diferencias en esas frecuencias se marcan como «ligadas a la variable del estrato». La sensibilidad S5 las quita.
- **Trabajo, cuidado y síntomas:**
  - El módulo laboral solo aparece en S7a y la sobrecarga solo en S7b. Toda regla con ellos se marca como potencialmente circular.
  - Las variables próximas a síntomas (actividad sexual, distensión y evacuación) se marcan en todas las tablas, y la sensibilidad S6 las quita.
- **Diferencias y reglas:** una diferencia entre estratos no se presenta como una regla independiente, ni una regla dentro de un estrato como una diferencia.

## 6. Umbrales mínimos por tamaño de estrato

Para un estrato con n participantes:
- **Antecedente:** n_A ≥ max(20, ⌈0,10·n⌉).
- **Antecedente y consecuente:** n_AC ≥ max(10, ⌈0,05·n⌉).
- **Largo máximo del antecedente:**
  - 3 condiciones si n ≥ 250;
  - 2 si 120 ≤ n < 250;
  - 1 si 60 ≤ n < 120;
  - si n < 60, el estrato solo se describe, sin búsqueda.

Con los tamaños conocidos:

| Estrato | n | Largo | n_A mínimo | n_AC mínimo |
|---|---|---|---|---|
| Trabaja | 309 | 3 | 31 | 16 |
| No trabaja | 220 | 2 | 22 | 11 |
| Tiene pareja | 356 | 3 | 36 | 18 |
| No tiene pareja | 173 | 2 | 20 | 10 |
| 0 días | 302 | 3 | 31 | 16 |
| 1-2 días | 148 | 2 | 20 | 10 |
| 3 días o más | 79 | 1 | 20 | 10 |
| Cuida | 251 | 3 | 26 | 13 |
| No cuida | 278 | 3 | 28 | 14 |

Los mínimos de 20 y 10 impiden interpretar reglas con unos pocos casos. Los umbrales no se bajan para encontrar asociaciones. Las alternativas (S3) son sensibilidades fijadas aquí.

## 7. Métricas de asociación

**Dentro de cada estrato.** Para cada regla se calculan, con la basal propia del estrato:
- los recuentos exactos n, n_A y n_AC;
- soporte, confianza con IC de Wilson, frecuencia basal y lift;
- diferencia respecto de la basal y leverage;
- diferencia de riesgo respecto de quienes no cumplen el antecedente, con IC de Newcombe;
- razón de riesgos con IC de Katz;
- z = (c − p₀) / √(p₀(1 − p₀)/n_A), p de Fisher y q de Benjamini-Hochberg sobre todas las reglas del estrato.

**Regla marcada:** |c − p₀| ≥ 0,10.

## 8. Comparación entre estratos

La comparación usa **todos** los antecedentes de 1 y 2 condiciones que sean comparables, no solo las reglas seleccionadas en algún estrato.

**Antecedente comparable:** en cada estrato de la dimensión hay al menos 20 participantes que lo cumplen (n_A ≥ 20) y al menos 20 que no lo cumplen. Además:
- no usa la variable que define la dimensión;
- no está determinado en ningún estrato, es decir, ninguna de sus condiciones implica a la otra.

**Medida común:** la diferencia de riesgo dentro de cada estrato s:

DR_s = P(severo | A, s) − P(severo | no A, s)

Se informa con su IC de Newcombe y con los recuentos de los cuatro grupos.

**Estadístico de heterogeneidad:** Q = Σ w_s (DR_s − DR̄)², con w_s = 1/var_s y DR̄ la media ponderada.
- **Varianza:** var_s = p₁(1 − p₁)/n_A + p₀(1 − p₀)/n_noA, con p₁ = (k + 0,5)/(n_A + 1) y p₀ igual en quienes no cumplen. La corrección de 0,5 evita varianzas nulas.
- **Dos estratos:** se informan también Δ = DR₁ − DR₂, z = Δ/√(var₁ + var₂), con Q = z², y el IC 95 % de Δ por el método MOVER con los IC de Newcombe.
- **Tres o más estratos:** se informa el rango, máximo menos mínimo de DR_s.

**Diferencia marcada:** el rango de DR_s es de al menos 0,10.

**Interacción:** la diferencia entre los p de dos estratos **no** se interpreta como interacción. Para cada regla que supera la nula en un estrato y no en otro se informa su prueba de interacción, en la tabla «diferencias de significación».

## 9. Referencia nula

**Dentro de cada estrato:** 1.000 permutaciones de la severidad, solo entre las participantes del estrato, con la semilla [42, 39, número del estrato]. Así se conserva su número de participantes con síntomas severos.
- En cada permutación se repite la búsqueda completa, con los mismos antecedentes frecuentes, que no dependen del consecuente.
- Se registran el máximo |z|, las reglas marcadas y la mayor diferencia.
- No se mezclan resultados entre estratos con basales distintas.

**Para la comparación entre estratos:** en cada dimensión, 1.000 permutaciones de la severidad dentro de cada estrato a la vez, con la semilla [42, 39, 100 + número de la dimensión]. Se registran el máximo Q y el menor valor p χ² (con k − 1 grados de libertad) entre todos los antecedentes comparables.
- **Qué representa:** esta referencia corresponde a la ausencia de asociación en todos los estratos. Se usa como **aproximación** a la ausencia de interacción.
- **Por qué sirve:** el estadístico Q tiene aproximadamente la misma distribución si hay una asociación común sin interacción, porque cada var_s ya incluye la variabilidad del estrato.
- **Comprobación:** las pruebas incluyen una simulación con una asociación común no nula sin interacción.
- **Limitación:** esta aproximación es una de las razones por las que el análisis de heterogeneidad se declara exploratorio.

**Estabilidad:** se usa como control adicional.
- **Reglas de cada estrato:** 200 submuestras del 80 % del estrato, con la semilla [42, 39, 2, número del estrato] y umbrales ⌈0,8·n_A mínimo⌉ y ⌈0,8·n_AC mínimo⌉.
- **Comparaciones:** 200 submuestras estratificadas del 80 % de cada estrato, con la semilla [42, 39, 3, número de la dimensión].

## 10. Control de la búsqueda múltiple

**Dentro de un estrato:** p ajustado de Westfall-Young, igual a (1 + número de permutaciones con un máximo |z| igual o mayor) / 1.001. La regla supera la nula del estrato si es menor que 0,05.

**Conjunto de los 9 estratos:** un p ajustado con el máximo |z| entre los 9 estratos en cada índice de permutación. Las permutaciones de dimensiones distintas son independientes, así que esto aproxima de forma conservadora la búsqueda en las 9 a la vez.

**Comparación entre estratos:**
- **Por dimensión:** p ajustado con el máximo Q.
- **Conjunto de las 4 dimensiones:** con el menor p χ² de las cuatro en cada índice.

**Benjamini-Hochberg:** se aplica a **todas** las reglas o comparaciones evaluadas, no solo a las seleccionadas.

Una regla elegida por extrema no se confirma con una prueba ordinaria posterior.

## 11. Sensibilidades

Todas se fijan aquí. Cada una repite la búsqueda en cada estrato y la comparación con su propia referencia nula de 1.000 permutaciones.

| Código | Cambio | Dentro de estratos | Comparación |
|---|---|---|---|
| S1 | Sin valores imputados ni deducidos (sin diabetes ni previsión, que no tienen marca) | sí | sí |
| S2a | Categorías originales sin agrupar | sí | sí |
| S3-bajo | n_A ≥ max(15, ⌈0,075·n⌉), n_AC ≥ max(8, ⌈0,0375·n⌉), comparabilidad ≥ 15 | sí | sí |
| S3-alto | n_A ≥ max(30, ⌈0,15·n⌉), n_AC ≥ max(15, ⌈0,075·n⌉), comparabilidad ≥ 30 | sí | sí |
| S4-1 | Antecedentes de una condición | sí | sí |
| S4-2 | Antecedentes de hasta dos condiciones | sí (solo cambia en estratos de largo 3) | igual a la principal |
| S5 | Sin frecuencias de ejercicio aeróbico, bajo impacto y fuerza | sí | sí |
| S6 | Sin variables próximas a síntomas | sí | sí |
| S7a | Quienes trabajan, con el módulo laboral | solo el estrato «trabaja» | no aplica |
| S7b | Quienes cuidan, con la sobrecarga | solo el estrato «cuida» | no aplica |
| S9 | Sin el estrato de 3 días o más: ejercicio solo 0 frente a 1-2 días | no | solo ejercicio |

**Además:**
- la **estabilidad** de la sección 9;
- la **dependencia entre antecedentes**: para cada comparación marcada, la prevalencia de su antecedente en cada estrato, señalando una diferencia de al menos 0,20 como «composición distinta»;
- la revisión de los resultados que dependen de **grupos pequeños**: estratos de menos de 100 participantes y antecedentes con menos de 30 participantes en algún estrato.

**Lectura de cada diferencia marcada de la principal en cada sensibilidad:**
- **se mantiene:** mismo orden de estratos y rango ≥ 0,10;
- **se debilita:** mismo orden y rango < 0,10;
- **cambia de dirección:** otro orden. Para dos estratos, otro signo de Δ. Para tres, otro estrato con la mayor o la menor DR;
- **no evaluable:** el antecedente no es comparable o no existe.

## 12. Comparación secundaria con A y B1

- **Uso:** solo exploratorio. A y B1 no se presentan como segmentaciones naturales ni validadas, no se elige entre ellas y no se usan como antecedentes.
- **Variables excluidas:** las tres preguntas que las definen principalmente (trabajo, pareja y días de ejercicio).
- **Mismo protocolo que las dimensiones:** tamaños, frecuencias basales con IC de Wilson y viabilidad según la sección 6, búsqueda dentro de cada grupo con referencia nula, y comparación entre los 4 grupos con Q, 3 grados de libertad y su propia nula.
- **Grupos pequeños:** un grupo de menos de 100 solo admite antecedentes de una condición.
- **Sin reajuste:** A y B1 no se reajustan.

## 13. Interpretación y conclusión

**Clases de las reglas dentro de un estrato** (excluyentes, como en la Fase 38):
1. Asociación débil: |c − p₀| < 0,10.
2. Redundante.
3. Compatible con la nula del estrato.
4. Inestable: reaparece marcada en menos del 70 % de las submuestras o mantiene la dirección en menos del 95 %.
5. Asociación relativamente más marcada dentro del estrato.

**Clases de las comparaciones** (excluyentes):
- **H0 no comparable:** no se informa como diferencia.
- **H1 sin diferencia apreciable:** rango < 0,10.
- **H2 redundante:** según la sección 5.
- **H3 diferencia compatible con la nula:** p ajustado de la dimensión ≥ 0,05.
- **H4 diferencia inestable:** según el criterio de la sección 9, con la diferencia marcada y el mismo orden.
- **H5 diferencia que supera los controles de la dimensión.**

**Diferencia consistente.** Una comparación H5 es consistente si cumple las tres condiciones:
1. Su p ajustado conjunto de las 4 dimensiones es menor que 0,05.
2. Se mantiene en S1, S2a, S3-bajo, S3-alto y S6 cuando es evaluable, y es evaluable al menos en 3 de ellas.
3. En ejercicio, no depende solo del estrato de 3 días o más: debe mantenerse en S9 o ser evaluable allí.

**Conclusión global.** Se decide de forma mecánica y se informa tal cual:
- **Resultado A:** al menos una diferencia consistente entre estratos.
- **Resultado B:** ninguna diferencia consistente, pero al menos una regla de clase 5 dentro de algún estrato que además supera la nula conjunta de los 9 estratos.
- **Resultado C:** ni lo uno ni lo otro. Las asociaciones son débiles o compatibles con el azar, y no se identifican diferencias suficientemente consistentes.

Los tres resultados son válidos y ninguno es preferido.

**Información adicional, sin cambiar la clasificación:**
- el exceso de reglas marcadas frente a la nula en cada estrato, como en la Fase 38;
- las «diferencias de significación».

**Límites de la interpretación:**
- No se producen recomendaciones clínicas.
- Las asociaciones sintéticas no se transforman en reglas de orientación.
- La nota para el tablero solo describe qué puede mostrarse de forma descriptiva.


# Sello

- **Huella SHA-256:** `18f15f821635f8c3d55a31f539d84d95ef8e5a32591e465073fb181a424c9042`.
- **Fecha:** 2026-11-05T19:30:04.
- **Antes de los resultados:** la prueba 20 comprueba que todos los resultados son posteriores al sello.

# Anexo: modificaciones posteriores al sellado


El protocolo `01_protocolo_39.md` (sha256 `18f15f821635f8c3d55a31f539d84d95ef8e5a32591e465073fb181a424c9042`, sellado el 2026-11-05 a las 19:30:04) no se modificó. Esta nota registra lo que se hizo de otra forma, o se precisó, después del sellado.

## 1. Corrección previa al sellado (no es una modificación)

Antes de sellar comprobé una afirmación del borrador: «en 0 días, las frecuencias de ejercicio son "no realiza" por diseño». Era falsa. Las frecuencias no son estructurales; por ejemplo, 285 de 302 participantes responden «no realiza» en aeróbico, pero no todas. Corregí el texto antes de sellar. El protocolo sellado ya dice lo correcto.

## 2. Precisión de la regla S9 (interpretación, sin cambio de resultados)

La sección 13 exige, para la dimensión ejercicio, que una diferencia consistente «se mantenga en S9 o sea evaluable allí». El código aplica la lectura estricta: la diferencia debe quedar «se mantiene» en S9.

Esto no cambia nada: ninguna comparación llegó a la clase H5, así que la condición nunca se evaluó.

## 3. Tabla exploratoria de significación nominal (agregada)

La tabla «diferencias de significación» de la sección 8 está vacía, porque ninguna regla superó la nula de su estrato. Para ilustrar el riesgo que el protocolo describe, agregué `scripts/significacion_39.py`. Para cada antecedente comparable de trabajo, pareja y cuidado, la tabla muestra:
- el p de Fisher sin ajuste en cada estrato;
- la prueba de interacción.

Es exploratoria, no interviene en ninguna clasificación ni en la conclusión, y se identifica como tal en los informes.

## 4. Comparación de reproducibilidad en las pruebas

La primera versión de la prueba 16 comparaba como texto los p ajustados recalculados con los guardados. Fallaba por el último dígito decimal al releer el CSV (0,42657342657342656 frente a 0,4265734265734265). Ahora compara numéricamente, con una tolerancia relativa de 10⁻¹². No cambió ningún resultado.

## 5. Figuras

Después de revisar las figuras, moví dos leyendas y un rótulo que tapaban datos (f01 y f04). Los datos no cambian.
