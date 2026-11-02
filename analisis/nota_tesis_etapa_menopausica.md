# Texto para la tesis: tratamiento de la etapa menopáusica y variables relacionadas

*Documento de trabajo del 02-11-2026 para revisar y adaptar. Los textos entre corchetes están pendientes: no son decisiones ni referencias verificadas, y no deben publicarse así.*

## 1. Decisión metodológica

La etapa menopáusica (`etapa_menopausica`) no se preguntó directamente en la encuesta. Se derivó durante la limpieza a partir de la fecha de la última menstruación, la fecha de la encuesta, la regularidad menstrual y la presencia de útero y ovarios.

La regla clasifica a cada participante de la siguiente manera:

| Categoría | Regla |
|---|---|
| Quirúrgica | No tiene ovarios |
| Posmenopausia | 12 meses o más desde la última menstruación |
| Premenopausia | Menos de 12 meses y menstruación regular |
| Perimenopausia | Menos de 12 meses y menstruación irregular o no segura |
| Indeterminada | Sin fecha de última menstruación utilizable (se distingue si no tiene útero) |

El criterio de 12 meses proviene de STRAW+10 (Harlow et al., 2012) y de la OMS (1996). La regla no aplica STRAW+10 de forma completa: es una simplificación propia, condicionada por las preguntas disponibles, y [aún no ha sido validada por la profesora guía].

Por esta razón, la variable se conservó en el conjunto de datos limpio solo con fines descriptivos: permite caracterizar la muestra y describir los clústeres una vez formados. Se excluyó de la selección de variables, la codificación, el escalado, PCA, K-Means, el agrupamiento aglomerativo, las reglas de asociación y la plataforma. La regla de cálculo y el conjunto sintético no se modificaron por esta decisión.

## 2. Justificación de las exclusiones

Excluir solo la etapa no era suficiente. Tres preguntas menstruales se responden únicamente si la última menstruación ocurrió hace menos de 12 meses, el mismo corte que usa la regla. Por eso, su categoría "no aplica" transmite información sobre la etapa reproductiva.

| Variable | Tratamiento | Motivo |
|---|---|---|
| `etapa_menopausica` | Solo descriptiva | Clasificación derivada, con una regla propia sin validar |
| `menstruacion_llega` | Solo exploratoria | Cumple los criterios de selección, pero permite reconstruir casi por completo la etapa |
| `tipo_sangrado` | Solo exploratoria | Comparte las 354 respuestas "no aplica" con la clasificación |
| `usa_metodo_anticonceptivo` | Solo exploratoria | Comparte las 354 respuestas "no aplica" con la clasificación |

Las cuatro variables permanecen en el conjunto limpio y en el análisis exploratorio correspondiente (`menstruacion_llega` se describe en las Fases 34C y 34D, pero no integra la matriz de la Fase 34E). El filtro de redundancia no detectó esta relación porque mide cada par solo donde ambas variables aplican. Por eso, la exclusión es una decisión metodológica adicional a los filtros, y no un resultado de ellos.

Tras retirar estas variables quedaron 52 candidatas, que se redujeron a 35 predictoras: 5 salieron por decisión metodológica previa, 9 por baja variabilidad y 3 por redundancia. La edad se mantuvo como candidata.

La edad es una característica demográfica y no equivale a la etapa menopáusica, aunque aporta información indirecta sobre la etapa reproductiva. La regla de la etapa no usa la edad, y el análisis no incorpora la clasificación derivada a través de ella.

## 3. Resultados del conjunto sintético de usuarias

**Los resultados de esta sección provienen del conjunto sintético de usuarias (n = 529 con MRS completo). Describen ese conjunto y lo que el simulador generó; no permiten estimar efectos en la población.**

**Coincidencia con las categorías.** Las 354 respuestas "no aplica" corresponden a 313 participantes en posmenopausia, 19 en categoría quirúrgica y 22 indeterminadas. Las 175 restantes corresponden a 96 en premenopausia y 79 en perimenopausia. Esta coincidencia se deriva de la lógica de la encuesta y de la regla, por lo que no depende de la magnitud de ningún efecto simulado.

**Asociación con la etapa** (V de Cramér, todas las filas): `menstruacion_llega` 0,82; `usa_metodo_anticonceptivo` 0,71; `tipo_sangrado` 0,46.

**Reconstrucción de la etapa** (bosque aleatorio, validación cruzada de 5 particiones, semilla 42). Este ejercicio solo documenta la exclusión; no es un modelo del estudio.

| Variables usadas | Acierto |
|---|---|
| Línea base: siempre la categoría más frecuente | 59,2 % |
| Solo regularidad de la menstruación | 92,2 % |
| Solo tipo de sangrado y método anticonceptivo | 78,6 % |
| Solo edad | 69,9 % |
| 35 predictoras más sangrado y método anticonceptivo | 80,0 % |
| 35 predictoras finales | 66,4 % |
| 35 predictoras sin edad | 58,2 % |

Estos porcentajes dependen de la distribución simulada de edades y etapas. Lo que puede sostenerse es que el ajuste redujo la información sobre la etapa disponible para el modelado, y que la que permanece se explica principalmente por la edad.

**Relación con la severidad.** La asociación entre la etapa y la severidad no fue significativa (n = 527; ε² = 0,006; p = 0,128; p ajustado = 0,310). Es un hallazgo exploratorio, limitado por una clasificación sin validar, y no constituye evidencia causal. Tampoco demuestra que la etapa no influya en los síntomas: el simulador le asignó un efecto a la etapa verdadera, y aun así la asociación con la etapa derivada no resultó significativa.
## 4. Evidencia empírica disponible

**Este trabajo aún no dispone de evidencia empírica propia sobre la relación entre la etapa menopáusica, los estilos de vida y la severidad de los síntomas.** Las respuestas reales de la encuesta del proyecto corresponden a 5 participantes y se usaron para reproducir patrones de respuesta en el conjunto sintético, no para estimar asociaciones.

**Análisis complementario de la profesora.** El análisis principal de esta nota es el del conjunto sintético de usuarias. El análisis exploratorio y el Random Forest realizados con el conjunto de datos de la profesora se conservan como trabajo complementario: no forman parte de estas correcciones, no se revisaron ni recalcularon, y no se usan para sustentar estas decisiones ni como evidencia empírica.

Las fuentes citadas sustentan la definición de las etapas, no el efecto de la etapa sobre los síntomas. [Si la tesis afirma que la etapa influye en los síntomas, agregar y verificar una referencia específica. Pendiente de búsqueda: no se ha revisado ninguna fuente para esta nota.]

Estas decisiones deberán revisarse cuando existan datos reales y [la profesora guía se haya pronunciado sobre la regla].

## 5. Comparación con y sin edad en la Fase 37

Esta comparación **todavía no se ha realizado**. Se dejará registrada como parte de la segmentación.

**Configuraciones.** Se compararán dos segmentaciones con el mismo conjunto de variables, la misma codificación, el mismo escalado y la misma semilla, cambiando únicamente la presencia de la edad. [Definir cómo proceder si la selección de la Fase 35B no retiene la edad.]

[Pendiente de confirmar: la misma semilla, el índice de silueta y el de Davies-Bouldin son propuestas, todavía no son decisiones.]

**Criterios de comparación**, aplicados tanto a K-Means como al agrupamiento aglomerativo:

1. **Calidad:** índice de silueta y de Davies-Bouldin.
2. **Tamaño de los grupos:** número de participantes por clúster, para detectar grupos muy pequeños o desbalanceados.
3. **Interpretabilidad:** si los perfiles se pueden describir por hábitos, estilos de vida y contexto laboral, o si se separan principalmente por edad.

**Criterio de decisión.** La decisión final considerará el objetivo de identificar patrones de hábitos, estilos de vida y contexto laboral, y no solamente la métrica estadística. Una mejor métrica con edad no bastará para conservarla si los clústeres terminan separándose principalmente por edad.

**Uso de la etapa.** En ambas configuraciones, la etapa quedará fuera del cálculo de distancias y de la asignación a clústeres. Una vez formados los grupos, se describirá con frecuencias y porcentajes, sin interpretar las diferencias como causas de pertenencia a un clúster.

**Resultado.** [Completar después de la Fase 37.]

## 6. Limitaciones

- La regla de clasificación es una simplificación propia, pendiente de validación. La regularidad menstrual es autodeclarada, y la encuesta no permite distinguir todas las etapas de STRAW+10.
- Excluir las preguntas menstruales evita la entrada directa de esa información, pero no elimina la relación indirecta con la edad ni con otras variables.
- Sin estas variables, el modelado no permite separar el efecto de los hábitos del de la etapa. Esa pregunta queda fuera del alcance de la segmentación.
- Todos los resultados de esta nota provienen del conjunto sintético de usuarias: describen ese conjunto y no permiten estimar efectos en la población.

## Referencias

[Pendientes de verificar contra la fuente original antes de citarlas.]

Harlow, S. D., Gass, M., Hall, J. E., Lobo, R., Maki, P., Rebar, R. W., Sherman, S., Sluss, P. M., de Villiers, T. J., & STRAW + 10 Collaborative Group. (2012). Executive summary of the Stages of Reproductive Aging Workshop + 10: Addressing the unfinished agenda of staging reproductive aging. *Menopause, 19*(4), 387-395. https://doi.org/10.1097/gme.0b013e31824d8f40

World Health Organization. (1996). *Research on the menopause in the 1990s: Report of a WHO Scientific Group* (WHO Technical Report Series 866). World Health Organization.
