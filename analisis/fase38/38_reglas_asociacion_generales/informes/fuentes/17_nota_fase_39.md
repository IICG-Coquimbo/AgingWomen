# Alcance

Esta nota prepara la Fase 39. **No ejecuta ninguna comparación entre subpoblaciones.** La Fase 39 no se inicia sin una decisión expresa.

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa.

# Punto de partida

La Fase 38 encontró una **señal difusa**: más reglas que por azar, pero ninguna regla general robusta. Los patrones que más se repiten (trabajo, ejercicio, pareja) son las mismas variables que definen las subpoblaciones propuestas. Por eso la pregunta de la Fase 39 es razonable: **¿la relación entre hábitos y severidad es distinta según el contexto?** También tiene un riesgo: dentro de cada estrato el n baja y el azar pesa más.

# Subpoblaciones y tamaños

| Dimensión | Estrato | Participantes | Con síntomas severos | Basal del estrato | Antecedente mínimo (10 %) |
|---|---|---|---|---|---|
| Trabajo | sí | 309 | 178 | 57,6 % | 31 |
| Trabajo | no | 220 | 103 | 46,8 % | 22 |
| Pareja | sí | 356 | 181 | 50,8 % | 36 |
| Pareja | no | 173 | 100 | 57,8 % | 18 |
| Días de ejercicio | 0 días | 302 | 177 | 58,6 % | 31 |
| Días de ejercicio | 1-2 días | 148 | 78 | 52,7 % | 15 |
| Días de ejercicio | 3-4 días | 52 | 18 | 34,6 % | 6 |
| Días de ejercicio | 5-6 días o todos los días | 27 | 8 | 29,6 % | 3 |
| Cuidado | no cuida | 278 | 140 | 50,4 % | 28 |
| Cuidado | 1 persona | 136 | 78 | 57,4 % | 14 |
| Cuidado | 2 personas | 67 | 43 | 64,2 % | 7 |
| Cuidado | 3 o más personas | 48 | 20 | 41,7 % | 5 |


- **Basales distintas:** varían entre estratos, así que las reglas deben compararse con la basal de **su** estrato, no con el 53,1 % general.
- **Estratos pequeños:** los de ejercicio de 3-4 días (52) y de 5 días o más (27) son demasiado chicos para buscar reglas propias. Conviene usar la agrupación «3 días o más» (79), la misma de B1 y de S2b, fijada de antemano.
- **Cuidado:** por la misma razón, conviene comparar quienes cuidan (251) con quienes no cuidan (278), sin separar por número de personas cuidadas.

# Cómo evaluar las diferencias

1. **Protocolo sellado antes de mirar.** Hay que fijar de antemano:
   - los estratos, con «3 días o más» para el ejercicio;
   - los ítems, iguales a los de la Fase 38 menos la variable que define el estrato;
   - umbrales proporcionales al tamaño del estrato, con un mínimo absoluto de 20 participantes en el antecedente;
   - los criterios.
2. **Búsqueda dentro de cada estrato:** con su propia referencia nula, permutando la severidad **dentro** del estrato. Con estratos de 79 a 356 participantes, la referencia nula será más exigente que en la principal.
3. **Comparación entre estratos de una misma regla:**
   - Confianza de la regla en cada estrato, **siempre con su denominador** (por ejemplo, «41 de 60» frente a «30 de 70»), su IC 95 % y la diferencia respecto de la basal de cada estrato.
   - Diferencia entre estratos con su IC 95 % (Newcombe).
   - Prueba de interacción por permutaciones dentro de los estratos, como referencia exploratoria.
   - Nunca porcentajes sin el n.
4. **Control de la búsqueda:** el número de comparaciones entre estratos se multiplica. Hay que usar el máximo estadístico sobre todas las reglas y estratos a la vez, no correcciones aplicadas solo a las reglas seleccionadas.
5. **Lectura de las diferencias:** una diferencia entre estratos es exploratoria. Si la regla no supera la nula en ningún estrato, una diferencia de porcentajes entre ellos no tiene interpretación.
6. **Segmentos A y B1:** pueden usarse como comparación exploratoria adicional, nunca como base obligatoria. B1 equivale a combinar trabajo, pareja y ejercicio, así que comparar por B1 repite en buena parte las comparaciones por esas tres variables.

# Riesgos

- **Circularidad:** el módulo laboral menciona los síntomas, y la sobrecarga puede ser consecuencia de ellos.
- **Variables próximas a síntomas:** actividad sexual, distensión y evacuación. Conviene repetir sin ellas (como S6).
- **Imputaciones:** repetir sin imputados (como S1). En la Fase 38, muchas reglas perdieron casos sin imputados.
- **Estratos y reglas pequeños:** varios estratos tienen menos de 100 participantes, así que las reglas dentro de ellos tendrán entre 10 y 30 casos. Lo esperable es mucho ruido.

# Decisiones pendientes para la responsable

1. **Si iniciar la Fase 39**, y con qué dimensiones: trabajo, pareja, ejercicio, cuidado, o una selección.
2. **Agrupación del ejercicio:** 0, 1-2 y 3 o más días.
3. **Variables:** si se incluyen las próximas a síntomas y los módulos (S7) en el análisis por estratos.
4. **Segmentos:** si A y B1 se usan como comparación exploratoria.
