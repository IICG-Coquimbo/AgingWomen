> **Versión correctiva (Fase 39R).** Corrige la Fase 39 histórica, que heredaba de la Fase 38 histórica dos variables que las decisiones de las Fases 35 y 36 excluían del modelado: `prevision` y `usa_medicamentos_diabetes`. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Criterios

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. No hay validación externa y la utilidad clínica no está demostrada. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38 (versión histórica), y la 39R los repitió conociendo además la 38R.

**Dentro de un estrato.** Se aplica el criterio de la Fase 38R: una regla de 2 o 3 condiciones es redundante si una regla más simple, en la misma dirección, tiene una confianza menor en menos de 5 puntos.

**Entre estratos.** Una diferencia para un antecedente de dos condiciones es redundante si una de sus condiciones, sola, produce un rango de diferencias de riesgo mayor o igual al del par menos 0,05.

**Además se marcan:**
- **Ligadas al estrato:** las frecuencias de modalidades de ejercicio dentro de la dimensión ejercicio.
- **Próximas a síntomas:** actividad sexual, distensión y evacuación.
- **Con módulos:** las preguntas laborales y la sobrecarga, que solo aparecen en S7a (n = 309) y S7b (n = 251).

# Dentro de los estratos

| Dimensión | Estrato | Reglas | Marcadas | Marcadas redundantes | % redundantes | Marcadas con variable próxima a síntomas |
|---|---|---|---|---|---|---|
| Trabajo | Trabaja | 8.611 | 1.842 | 1.503 | 82 % | 562 |
| Trabajo | No trabaja | 1.302 | 243 | 115 | 47 % | 53 |
| Pareja | Tiene pareja | 8.709 | 1.617 | 1.334 | 82 % | 428 |
| Pareja | No tiene pareja | 1.116 | 164 | 72 | 44 % | 24 |
| Ejercicio | 0 días de ejercicio | 9.030 | 1.574 | 1.291 | 82 % | 389 |
| Ejercicio | 1-2 días de ejercicio | 1.035 | 167 | 69 | 41 % | 50 |
| Ejercicio | 3 días o más de ejercicio | 41 | 7 | 0 | 0 % | 1 |
| Cuidado | Cuida a una o más personas | 8.878 | 2.169 | 1.738 | 80 % | 610 |
| Cuidado | No cuida | 9.190 | 1.302 | 965 | 74 % | 321 |


En total, 7.087 de 9.085 reglas marcadas (78 %) son redundantes: agregar una condición casi no cambia la confianza.

**Ejemplos:**

| Estrato | Regla | Confianza | Regla más simple casi igual | Mejora |
|---|---|---|---|---|
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y Frecuencia de ejercicio de bajo impacto: no realiza o nunca y La falta de tiempo influye en su alimentación: a veces → severos | 88,6 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 4,4 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Platos de verduras al día: no consumo o 1-2 porciones → severos | 87,9 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 3,7 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Lácteos al día: 1-2 porciones → severos | 87,1 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 2,9 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Frecuencia de ejercicio de fuerza: no realiza o nunca → severos | 86,1 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 1,9 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Usa medicamentos para la presión: no → severos | 85,3 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 1,1 pts |
| 0 días de ejercicio | Frecuencia de ejercicio de fuerza: no realiza o nunca y Golosinas a la semana: 1-2 veces por semana y Tiene pareja: no → severos | 84,8 % | Golosinas a la semana: 1-2 veces por semana y Tiene pareja: no | −0,4 pts |
| Cuida a una o más personas | Días de ejercicio a la semana: 0 días y Evacuación intestinal: cada 2 días y Frutas al día: 1-2 porciones → severos | 84,6 % | Días de ejercicio a la semana: 0 días y Evacuación intestinal: cada 2 días | 3,5 pts |
| Trabaja | Frecuencia de ejercicio de bajo impacto: no realiza o nunca y Distensión abdominal: nunca o casi nunca y Operada para no tener más hijos: no → severos | 84,4 % | Frecuencia de ejercicio de bajo impacto: no realiza o nunca y Distensión abdominal: nunca o casi nunca | 3,7 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Operada para no tener más hijos: no → severos | 83,9 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | −0,3 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Quién prepara las comidas: ella prepara la mayoría → severos | 83,9 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | −0,3 pts |


# Entre estratos

| Dimensión | Diferencias marcadas | Redundantes | Con variable próxima a síntomas | Ligadas al estrato |
|---|---|---|---|---|
| Trabajo | 569 | 362 | 132 | 0 |
| Pareja | 435 | 295 | 69 | 0 |
| Ejercicio | 234 | 158 | 49 | 21 |
| Cuidado | 582 | 356 | 126 | 0 |


**Patrón típico de las diferencias redundantes:** una condición que ya difiere entre estratos, como «0 días de ejercicio» en la dimensión trabajo, más otra que casi no aporta.

**No confundir con reglas independientes.** Una diferencia entre estratos no es una regla independiente, y una regla dentro de un estrato no es una diferencia entre estratos. Las tablas los mantienen separados.
