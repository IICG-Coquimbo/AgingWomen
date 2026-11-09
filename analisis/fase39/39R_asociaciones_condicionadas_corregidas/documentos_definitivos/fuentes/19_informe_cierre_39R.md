> **Versión correctiva (Fase 39R).** Corrige la Fase 39 histórica, que heredaba de la Fase 38 histórica dos variables que las decisiones de las Fases 35 y 36 excluían del modelado: `prevision` y `usa_medicamentos_diabetes`. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Conclusión

**Resultado C: Las asociaciones son débiles o compatibles con el azar y no se identifican diferencias suficientemente consistentes.**

La conclusión se obtuvo de forma mecánica con los criterios sellados (sección 10 del protocolo de la 39R):
- **Diferencias consistentes entre estratos:** ninguna; ni siquiera hay comparaciones que superen la nula de su dimensión.
- **Reglas que superan la nula de su estrato:** ninguna.

**La señal difusa de la Fase 38R se mantiene en cuatro de los estratos grandes** (trabaja, tiene pareja, 0 días y cuida): hay más reglas marcadas que por azar. Pero no se concentra en reglas puntuales ni cambia de forma demostrable según el trabajo, la pareja, el ejercicio o el cuidado.

Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. No hay validación externa y la utilidad clínica no está demostrada. Es un análisis **exploratorio**: los estratos y la pregunta se definieron después de conocer las Fases 37D y 38 (versión histórica), y la 39R los repitió conociendo además la 38R.

# Respuestas

**1. ¿Cuántas participantes forman cada estrato?**

| Dimensión | Estratos |
|---|---|
| Trabajo | trabaja 309, no trabaja 220 |
| Pareja | tiene pareja 356, no tiene pareja 173 |
| Ejercicio | 0 días 302, 1-2 días 148, 3 días o más 79 |
| Cuidado | cuida 251, no cuida 278 |

**Grupos secundarios:** A 150/76/132/171 y B1 150/79/126/174.

**2. ¿Cuál es la frecuencia basal de MRS severo en cada uno?**

trabaja 57,6 %, no trabaja 46,8 %, tiene pareja 50,8 %, no tiene pareja 57,8 %, 0 días de ejercicio 58,6 %, 1-2 días de ejercicio 52,7 %, 3 días o más de ejercicio 32,9 %, cuida a una o más personas 56,2 %, no cuida 50,4 %.

- **Diferencias claras de basal:** 3 días o más de ejercicio frente a 0 días (−25,7 puntos, IC −36,5 a −13,4) y frente a 1-2 días; trabaja frente a no trabaja (+10,8, IC 2,2 a 19,2).
- **Pareja y cuidado:** sus intervalos incluyen el 0.

**3. ¿Cuántas reglas se encontraron?**
- **Total:** 47.912 reglas en los 9 estratos, de las cuales 9.085 son marcadas (al menos 10 puntos sobre la basal del estrato).
- **Estratos grandes** (largo 3): entre 8.611 y 9.190 reglas cada uno.
- **Estratos medianos** (largo 2): entre 1.035 y 1.302.
- **3 días o más** (largo 1): 41 reglas.

**4. ¿Cuántas superaron su referencia nula?**
- **Principal:** **ninguna**, ni dentro de su estrato ni en la nula conjunta.
- **Sensibilidades:** 7 reglas superan la nula de su estrato en alguna, cada una en una sola configuración.
- **Comparaciones entre estratos:** ninguna supera la nula de su dimensión en la principal. En las sensibilidades, una sola, en S3-bajo (p ajustado conjunto 0,048), que no cumple la comparabilidad mínima del análisis principal y depende de 18 participantes.

**5. ¿Qué reglas son redundantes?**
- **Dentro de los estratos:** 7.087 de las 9.085 reglas marcadas (78 %). Agregan una condición que casi no cambia la confianza.
- **Entre estratos:** 1.171 de 1.820 diferencias marcadas.

**6. ¿Qué asociaciones aparecen en quienes trabajan y quienes no?**
- **Exceso de reglas marcadas:** trabaja: 1.842 reglas marcadas frente a 1.168 por azar (p 0,006); no trabaja: 243 reglas marcadas frente a 201 por azar (p 0,148).
- **Ninguna regla** supera la nula de su estrato.
- **Ninguna diferencia** entre ambos estratos supera la nula (menor p ajustado 0,336).

**7. ¿Qué ocurre según la situación de pareja?**
- **Exceso de reglas marcadas:** tiene pareja: 1.617 reglas marcadas frente a 947 por azar (p 0,002); no tiene pareja: 164 reglas marcadas frente a 195 por azar (p 0,809).
- **Sin reglas que superen la nula** ni diferencias (menor p ajustado 0,226).
- **Coincidencia con la Fase 38R:** la regla más fuerte de «tiene pareja» es la misma que fue de clase 6 en la Fase 38R (trabaja, sin bajo impacto, distensión casi nunca). Aquí no supera la nula (p 0,107).

**8. ¿Qué ocurre según los días de ejercicio?**
- **Exceso de reglas marcadas:** 0 días de ejercicio: 1.574 reglas marcadas frente a 1.168 por azar (p 0,047); 1-2 días de ejercicio: 167 reglas marcadas frente a 191 por azar (p 0,747); 3 días o más de ejercicio: 7 reglas marcadas frente a 5 por azar (p 0,212).
- **3 días o más:** solo admite reglas de una condición, y ninguna supera la nula.
- **Comparación entre los tres estratos:** es la más débil (menor p ajustado 0,905). Sin el estrato pequeño (S9) tampoco aparece nada.
- **Lo único claro** es la diferencia de basal: menos severas con 3 días o más.

**9. ¿Qué ocurre según las responsabilidades de cuidado?**
- **Exceso de reglas marcadas:** cuida a una o más personas: 2.169 reglas marcadas frente a 1.494 por azar (p 0,006); no cuida: 1.302 reglas marcadas frente a 1.390 por azar (p 0,595).
- **Sin reglas ni diferencias** que superen la nula (menor p ajustado 0,757).
- **Con la sobrecarga (39R S7b, quienes cuidan, n = 251):** aparece una regla con 34 participantes en el antecedente, potencialmente circular. La misma regla aparece en la 38R S7b (n = 239, sobrecarga observada) y en la 38R S7b-251 (n = 251, ampliada).

**Poblaciones de los módulos** (no deben equipararse resultados de poblaciones diferentes):

| Fase | Sensibilidad | Población | Participantes |
|---|---|---|---|
| 38R | S7a | Quienes trabajan y tienen información laboral | 287 |
| 38R | S7a-309 (ampliada) | Todas quienes trabajan; 22 sin ítems laborales | 309 |
| 38R | S7b | Quienes cuidan y tienen la sobrecarga observada | 239 |
| 38R | S7b-251 (ampliada) | Todas quienes cuidan; incluye 12 con sobrecarga imputada | 251 |
| 39R | S7a | Quienes trabajan, con el módulo laboral | 309 |
| 39R | S7b | Quienes cuidan, con la sobrecarga | 251 |


**10. ¿Hay evidencia de diferencias de asociación entre estratos o solo diferencias de significación?**
- **Solo diferencias de significación.** Cientos de antecedentes son nominalmente significativos en un estrato y no en el otro (por ejemplo, 183 en trabajo). Ninguna diferencia resiste la referencia nula de la búsqueda.
- **Diferencias marcadas:** su número es el que produce el azar en todas las dimensiones (p de exceso entre 0,178 y 0,898).
- **Exceso de reglas dentro de los estratos:** aparece en los estratos grandes, no en los pequeños, pero eso refleja el tamaño y no prueba una interacción.

**11. ¿Cuáles se mantienen en sensibilidades?**
- **Nada que haya superado los controles,** porque nada los superó en la principal.
- **Dirección de las diferencias marcadas** (compatibles con el azar):
  - se mantiene con categorías originales (S2a), sin frecuencias de ejercicio (S5) y sin variables próximas a síntomas (S6);
  - se debilita o cambia sin imputados (S1);
  - en ejercicio, se debilita sin el estrato pequeño (S9).
- **El exceso de reglas marcadas** en los estratos grandes se mantiene en casi todas las sensibilidades.

**12. ¿Qué resultados podrían explicarse por azar?**
- **Todas** las reglas dentro de los estratos y **todas** las diferencias entre estratos.
- **Lo que no se explica del todo por azar:** el exceso global de reglas marcadas en los estratos grandes (la señal difusa) y las diferencias de basal (sobre todo, el ejercicio).

**13. ¿Qué limitaciones presentan los estratos pequeños?**
- **3 días o más (79 participantes, 26 severas):**
  - admite solo reglas de una condición;
  - en la comparación, muchas diferencias dependen de 20 a 30 participantes;
  - la única diferencia que superó una nula (S3-bajo) se apoyaba en 18 participantes y 0 severas.
- **Estratos de 148 a 220:** tienen menos poder, sin exceso detectable.
- **Diferencias marcadas con menos de 30 casos en algún estrato:** 821 de 1.820.

**14. ¿Qué aporta la comparación complementaria A/B1?**
- **Confirma descriptivamente** basales distintas, sobre todo por el ejercicio (A1 38 %, B1-1 33 %).
- **Coincidencia:** A y B1 asignan al grupo correspondiente a 88 % de las participantes.
- **Sin evidencia nueva:** no hay reglas que superen la nula dentro de los grupos ni diferencias entre ellos.
- **No agrega información** sobre la que ya dan trabajo, pareja y ejercicio por separado.

**15. ¿Se identificaron patrones suficientemente consistentes?** **No.**

**16. ¿Qué resultados no deben utilizarse para generar recomendaciones?**
- **Ninguna regla** dentro de los estratos.
- **Ninguna diferencia** entre estratos.
- **Ninguna basal** por estrato o grupo.
- **Ninguna regla de las sensibilidades**, incluidas las de S4-1 y S7b.
- **Ningún segmento de A o B1** como perfil de riesgo.

Todo es sintético, exploratorio y compatible con el azar o frágil.

**17. ¿Qué información puede mostrar descriptivamente el tablero?**
- **Clasificación usada en el análisis estadístico:** `severo_mrs` (MRS ≥ 16) es un criterio de este análisis sintético y no una categoría que muestre la plataforma.
- **Información MRS que presenta hoy la plataforma (Fase 40B-3):** el puntaje de 0 a 44 y sus dimensiones cuando el resultado es definitivo; una suma provisional o parcial, o un aviso, en los demás estados; y la evolución entre rondas. No muestra categoría de severidad.
- **Pendiente de validación clínica:** mostrar una categoría de severidad o textos que interpreten clínicamente el puntaje (informe 20).
- **Respuestas propias:** las de la usuaria.
- **Etiqueta B1 opcional:** solo si la profesora la aprueba, como descripción neutra del contexto (informe 20).

**18. ¿Qué necesita el futuro motor de orientaciones personalizadas?**
- **Catálogo:** orientaciones educativas con criterios de activación explícitos sobre las respuestas, cada una con su fuente sanitaria confiable.
- **Revisión:** aprobación de la profesora.
- **Funcionamiento:** versión, registro de lo mostrado y tono no clínico.
- **Separación:** el MRS solo indica cuándo sugerir consultar a un profesional, no qué hábito cambiar.
- **No debe basarse** en las asociaciones de estas fases (informe 20).

**19. ¿Qué pruebas se ejecutaron?**
- **Pruebas:** 27 de 27 superadas.
- **Controles negativos:** 30 de 30 errores introducidos detectados (`pruebas/control_mutaciones.csv`).
- **Cobertura:**
  - identificadores, MRS, tamaños, basales y umbrales;
  - pertenencia recalculada desde las respuestas crudas;
  - codificación idéntica a la Fase 38R;
  - ausencia de ítems del MRS, de contradicciones, de la variable del estrato y de ítems constantes;
  - medidas;
  - referencias nulas dentro de los estratos y entre ellos;
  - comparación recalculada de forma independiente;
  - calibración del estadístico de interacción por simulación;
  - búsqueda múltiple e imputaciones;
  - reproducibilidad;
  - etiquetas A y B1;
  - fases anteriores y sello;
  - clasificación y conclusión.

**20. ¿Permanecieron intactas las fases anteriores?**
- **Sí.** En el control final de la 39R, 6.537 archivos con huella no cambiaron (0 cambiados) y los manifiestos de 6.462 archivos solo muestran 4 diferencias ya documentadas.
- **Simulador:** sus archivos no se abrieron.
- **Git:** rama datos-simulados, HEAD 573d3a3, sin commit ni push.
