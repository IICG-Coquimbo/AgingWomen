> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Alcance

Esta nota conserva la organización de la nota preparatoria original. **La Fase 39R ya se ejecutó con su propio protocolo sellado:** sus resultados están en `analisis/fase39/39R_asociaciones_condicionadas_corregidas/`. Esta nota no ejecuta ninguna comparación entre subpoblaciones.

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: es un análisis **exploratorio** y su utilidad clínica no está demostrada.

# Punto de partida

La Fase 38R encontró una **señal difusa**: más reglas que por azar, pero ninguna regla general robusta. Los patrones que más se repiten (trabajo, ejercicio, pareja) son las mismas variables que definen las subpoblaciones. Dentro de cada estrato el n baja y el azar pesa más.

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
- **Estratos pequeños:** los de ejercicio de 3-4 días (52) y de 5 días o más (27) son demasiado chicos para buscar reglas propias. Por eso la Fase 39R usó la agrupación «3 días o más» (79), la misma de B1 y de S2b, fijada de antemano.
- **Cuidado:** por la misma razón, la Fase 39R comparó a quienes cuidan (251) con quienes no cuidan (278), sin separar por número de personas cuidadas.

# Riesgos que se mantuvieron presentes

- **Circularidad:** el módulo laboral menciona los síntomas, y la sobrecarga puede ser consecuencia de ellos.
- **Variables próximas a síntomas:** actividad sexual, distensión y evacuación.
- **Imputaciones:** muchas reglas pierden casos sin imputados.
- **Estratos y reglas pequeños:** varios estratos tienen menos de 100 participantes, lo que limita la precisión.
