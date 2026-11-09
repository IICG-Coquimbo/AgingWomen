# Criterios

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38.

**Dentro de un estrato.** Se aplica el criterio de la Fase 38: una regla de 2 o 3 condiciones es redundante si una regla más simple, en la misma dirección, tiene una confianza menor en menos de 5 puntos.

**Entre estratos.** Una diferencia para un antecedente de dos condiciones es redundante si una de sus condiciones, sola, produce un rango de diferencias de riesgo mayor o igual al del par menos 0,05.

**Además se marcan:**
- **Ligadas al estrato:** las frecuencias de modalidades de ejercicio dentro de la dimensión ejercicio.
- **Próximas a síntomas:** actividad sexual, distensión y evacuación.
- **Con módulos:** las preguntas laborales y la sobrecarga, que solo aparecen en S7a y S7b.

# Dentro de los estratos

| Dimensión | Estrato | Reglas | Marcadas | Marcadas redundantes | % redundantes | Marcadas con variable próxima a síntomas |
|---|---|---|---|---|---|---|
| Trabajo | Trabaja | 10.849 | 2.162 | 1.800 | 83 % | 629 |
| Trabajo | No trabaja | 1.453 | 264 | 131 | 50 % | 54 |
| Pareja | Tiene pareja | 10.985 | 1.922 | 1.626 | 85 % | 480 |
| Pareja | No tiene pareja | 1.254 | 183 | 85 | 46 % | 26 |
| Ejercicio | 0 días de ejercicio | 11.232 | 1.874 | 1.567 | 84 % | 438 |
| Ejercicio | 1-2 días de ejercicio | 1.167 | 182 | 82 | 45 % | 51 |
| Ejercicio | 3 días o más de ejercicio | 43 | 7 | 0 | 0 % | 1 |
| Cuidado | Cuida a una o más personas | 11.161 | 2.553 | 2.100 | 82 % | 710 |
| Cuidado | No cuida | 11.528 | 1.592 | 1.219 | 77 % | 373 |


En total, 8.610 de 10.739 reglas marcadas (80 %) son redundantes: agregar una condición casi no cambia la confianza.

**Ejemplos:**

| Estrato | Regla | Confianza | Regla más simple casi igual | Mejora |
|---|---|---|---|---|
| No tiene pareja | Frecuencia de ejercicio aeróbico: no realiza o nunca y Usa medicamentos para la diabetes: sí → severos | 90,0 % | Usa medicamentos para la diabetes: sí | 3,6 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y Frecuencia de ejercicio de bajo impacto: no realiza o nunca y La falta de tiempo influye en su alimentación: a veces → severos | 88,6 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 4,4 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Platos de verduras al día: no consumo o 1-2 porciones → severos | 87,9 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 3,7 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Lácteos al día: 1-2 porciones → severos | 87,1 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 2,9 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Frecuencia de ejercicio de fuerza: no realiza o nunca → severos | 86,1 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 1,9 pts |
| 0 días de ejercicio | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces y Usa medicamentos para la presión: no → severos | 85,3 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | 1,1 pts |
| No tiene pareja | Usa medicamentos para la diabetes: sí y Platos de verduras al día: no consumo o 1-2 porciones → severos | 85,0 % | Usa medicamentos para la diabetes: sí | −1,4 pts |
| No tiene pareja | Tiene actividad sexual: no y Usa medicamentos para la diabetes: sí → severos | 85,0 % | Usa medicamentos para la diabetes: sí | −1,4 pts |
| 0 días de ejercicio | Frecuencia de ejercicio de fuerza: no realiza o nunca y Golosinas a la semana: 1-2 veces por semana y Tiene pareja: no → severos | 84,8 % | Golosinas a la semana: 1-2 veces por semana y Tiene pareja: no | −0,4 pts |
| Cuida a una o más personas | Días de ejercicio a la semana: 0 días y Evacuación intestinal: cada 2 días y Frutas al día: 1-2 porciones → severos | 84,6 % | Días de ejercicio a la semana: 0 días y Evacuación intestinal: cada 2 días | 3,5 pts |


# Entre estratos

| Dimensión | Diferencias marcadas | Redundantes | Con variable próxima a síntomas | Ligadas al estrato |
|---|---|---|---|---|
| Trabajo | 620 | 404 | 137 | 0 |
| Pareja | 491 | 342 | 72 | 0 |
| Ejercicio | 286 | 185 | 55 | 24 |
| Cuidado | 637 | 398 | 133 | 0 |


**Patrón típico de las diferencias redundantes:** una condición que ya difiere entre estratos, como «0 días de ejercicio» en la dimensión trabajo, más otra que casi no aporta.

**No confundir con reglas independientes.** Una diferencia entre estratos no es una regla independiente, y una regla dentro de un estrato no es una diferencia entre estratos. Las tablas los mantienen separados.
