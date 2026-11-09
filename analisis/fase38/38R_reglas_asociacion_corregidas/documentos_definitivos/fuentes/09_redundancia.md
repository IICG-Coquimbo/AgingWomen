> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Criterio

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: es un análisis **exploratorio** y su utilidad clínica no está demostrada.

Una regla de 2 o 3 condiciones es **redundante** si alguna regla más simple, con un subconjunto propio de sus condiciones y en la misma dirección, tiene una confianza menor en **menos de 5 puntos**. Es decir, la condición agregada casi no aporta. Las reglas con las mismas variables y la misma dirección forman una **familia**.

# Resultados

- **Reglas marcadas:** de las 971, **787 son redundantes** (81 %).
- **No redundantes:** quedan 184 marcadas. Una supera la referencia nula; las demás son compatibles con ella.
- **Familias:** las reglas marcadas pertenecen a 944 familias distintas. Casi todas tienen una o dos reglas, así que no hay un patrón dominante que se repita con muchas variantes.
- **Trabajo:** 25 % de las reglas marcadas incluyen la pregunta de trabajo. Muchas reglas de tres condiciones agregan a «trabaja: sí» o «trabaja: no» uno o dos hábitos.

**Ejemplos de reglas marcadas redundantes:**

| Regla | Consecuente | Confianza | Regla más simple casi igual | Mejora |
|---|---|---|---|---|
| Vasos de agua al día: no consumo o 1-2 porciones y Operada para no tener más hijos: no y Trabaja actualmente: sí | severos | 73,2 % | Vasos de agua al día: no consumo o 1-2 porciones y Trabaja actualmente: sí | 2,6 pts |
| Frecuencia de ejercicio aeróbico: no realiza o nunca y Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | severos | 72,7 % | Vasos de agua al día: no consumo o 1-2 porciones y La falta de tiempo influye en su alimentación: a veces | −1,4 pts |
| Vasos de agua al día: no consumo o 1-2 porciones y Usa medicamentos para la presión: no y Trabaja actualmente: sí | severos | 72,2 % | Vasos de agua al día: no consumo o 1-2 porciones y Trabaja actualmente: sí | 1,6 pts |
| Distensión abdominal: nunca o casi nunca y Evacuación intestinal: 1 vez al día y Trabaja actualmente: sí | severos | 71,9 % | Distensión abdominal: nunca o casi nunca y Trabaja actualmente: sí | 3,1 pts |
| Vasos de agua al día: no consumo o 1-2 porciones y Días de ejercicio a la semana: 0 días y Legumbres a la semana: 1-2 veces por semana | severos | 71,6 % | Vasos de agua al día: no consumo o 1-2 porciones y Legumbres a la semana: 1-2 veces por semana | 5,0 pts |
| Distensión abdominal: nunca o casi nunca y Frutas al día: 1-2 porciones y Trabaja actualmente: sí | severos | 71,4 % | Distensión abdominal: nunca o casi nunca y Trabaja actualmente: sí | 2,6 pts |
| Vasos de agua al día: no consumo o 1-2 porciones y Frutas al día: 1-2 porciones y Trabaja actualmente: sí | severos | 71,4 % | Vasos de agua al día: no consumo o 1-2 porciones y Trabaja actualmente: sí | 0,8 pts |
| Distensión abdominal: nunca o casi nunca y La falta de tiempo influye en su alimentación: a veces y Trabaja actualmente: sí | severos | 70,9 % | Distensión abdominal: nunca o casi nunca y Trabaja actualmente: sí | 2,1 pts |
| Días de ejercicio a la semana: 0 días y La falta de tiempo influye en su alimentación: a veces y Trabaja actualmente: sí | severos | 70,9 % | Días de ejercicio a la semana: 0 días y La falta de tiempo influye en su alimentación: a veces | 5,0 pts |
| Distensión abdominal: nunca o casi nunca y Frecuencia de ejercicio de fuerza: no realiza o nunca y Trabaja actualmente: sí | severos | 70,5 % | Distensión abdominal: nunca o casi nunca y Trabaja actualmente: sí | 1,7 pts |
| Personas a su cuidado: 1 persona y Días de ejercicio a la semana: 0 días y Frutas al día: 1-2 porciones | severos | 70,2 % | Personas a su cuidado: 1 persona y Días de ejercicio a la semana: 0 días | 3,9 pts |
| Tiene actividad sexual: sí y Frecuencia de ejercicio aeróbico: no realiza o nunca y Vasos de agua al día: no consumo o 1-2 porciones | severos | 70,2 % | Tiene actividad sexual: sí y Vasos de agua al día: no consumo o 1-2 porciones | 1,9 pts |


**Familias con más reglas marcadas:**

| Familia | Reglas marcadas | Redundantes | Confianza máxima |
|---|---|---|---|
| edad & frecuencia_bajo_impacto & tiene_actividad_sexual → severos | 2 | 1 | 67,9 % |
| dias_ejercicio_semana & horas_sedentarismo & trabaja_actualmente → severos | 2 | 2 | 66,7 % |
| alcohol_frecuencia & cantidad_personas_cuida & trabaja_actualmente → no severos | 2 | 2 | 59,7 % |
| dias_ejercicio_semana & tiene_pareja & trabaja_actualmente → severos | 2 | 2 | 66,1 % |
| carnes_semana & falta_tiempo_influye & trabaja_actualmente → severos | 2 | 2 | 67,2 % |
| distension_abdominal & panes_dia & trabaja_actualmente → no severos | 2 | 2 | 57,9 % |
| alcohol_frecuencia & horas_sedentarismo & tabaco_frecuencia → no severos | 2 | 2 | 64,2 % |
| distension_abdominal & falta_tiempo_influye & trabaja_actualmente → severos | 2 | 2 | 70,9 % |
| alcohol_frecuencia & carnes_semana & trabaja_actualmente → severos | 2 | 1 | 69,0 % |
| dias_ejercicio_semana & falta_tiempo_influye & tiene_actividad_sexual → severos | 2 | 2 | 67,7 % |


La lista completa está en `reglas/redundantes_marcadas.csv` y `reglas/familias_marcadas.csv`.
