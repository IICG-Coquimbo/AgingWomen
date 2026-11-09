> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Conclusión

**La evidencia de reglas de asociación es débil.**

- **Señal difusa:** en los datos sintéticos hay más combinaciones de hábitos y contexto asociadas con la severidad de lo que produciría el azar (971 reglas marcadas frente a 544 esperadas). Esa señal está repartida en muchas reglas débiles.
- **Reglas puntuales:** de 9.761 reglas, **solo una cumple todos los criterios sellados**, y lo hace por poco. Además:
  - incluye una variable próxima a síntomas;
  - desaparece sin imputados (S1, n_A 52) y con el umbral más alto (S3-alto);
  - con el umbral más bajo (S3-bajo) se mantiene, pero no supera su referencia nula.
- **Conclusión:** **no hay reglas suficientemente sólidas para destacar como hallazgos.** Los patrones que más se repiten (trabajar y no hacer ejercicio con síntomas severos; no trabajar y tener pareja con síntomas no severos) coinciden con las asociaciones pequeñas de la Fase 37D, pero esta fase no las confirma de forma independiente.

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: es un análisis **exploratorio** y su utilidad clínica no está demostrada.

# Respuestas

**1. ¿Cuántas variables se utilizaron?**
- **Análisis principal:** 29 variables generales medidas en las 529 participantes.
- **Sensibilidades:** 4 más, cada una solo en su sensibilidad: el IMC, las dos preguntas laborales y la sobrecarga.
- **Excluidas:** el MRS (solo como consecuente), los segmentos, la etapa menopáusica y, de forma definitiva, las variables retiradas por esta corrección.
- **Criterio:** ninguna variable se eligió por su asociación con el MRS.

**2. ¿Cómo se agruparon las categorías poco frecuentes?**
- **Regla fija:** se aplicó la regla del protocolo, sin mirar el MRS: una categoría ordinal con menos de 27 participantes se une a su vecina de menor frecuencia.
- **Nominales:** las escasas, sin vecina compatible, no generan ítem: «compro comida» y «otro» en quién prepara.
- **Alcance:** 22 ítems resultan de unir categorías escasas (informe 04).

**3. ¿Cuántos ítems transaccionales se generaron?**
- **Principal:** 90 ítems, con unos 29 por participante, más los dos consecuentes.
- **Sensibilidades:** entre 60 y 113.

**4. ¿Qué configuraciones de búsqueda se evaluaron?**
- **Principal:** antecedentes de 1 a 3 condiciones, al menos 53 participantes con el antecedente y 27 con antecedente y consecuente.
- **15 sensibilidades:**
  - S1: sin imputados.
  - S2a y S2b: agrupaciones.
  - S3: umbrales de 27 y 80.
  - S4: largo 1 y 2.
  - S5: sin frecuencias de ejercicio.
  - S6: sin variables próximas a síntomas.
  - S7a y S7a-309: quienes trabajan (287 con información laboral y 309 ampliada).
  - S7b y S7b-251: quienes cuidan (239 con sobrecarga observada y 251 ampliada).
  - S8a y S8b: IMC.
- **Para cada configuración:** 1.000 permutaciones nulas. En la principal, además, 200 submuestras.

**5. ¿Cuántas reglas se encontraron?**
- **Principal:** 9.761 reglas evaluadas, de las cuales 971 son marcadas (al menos 10 puntos sobre la basal). Son 629 hacia síntomas severos y 342 hacia no severos.

**6. ¿Cuántas superan los criterios previamente definidos?**
- **Clase 6:** **una**, que cumple marcada, no redundante, supera la referencia nula y estable.
- **Las demás marcadas:** 787 son redundantes y 183 son compatibles con la nula.

**7. ¿Cuáles son las principales reglas y cómo se interpretan?**
- **La regla de la clase 6:** quienes trabajan, no hacen ejercicio de bajo impacto y casi nunca tienen distensión abdominal → síntomas severos.
  - **Cifras:** 46 de 57, es decir, 81 % frente al 53 % general.
  - **Lectura:** describe una combinación frecuente en la simulación. No dice que trabajar o no hacer ejercicio cause síntomas, y la dirección de la distensión es poco intuitiva.
- **Otras reglas fuertes:** son compatibles con el azar (informe 07).

**8. ¿Cuánto se aleja su confianza de la frecuencia basal?**
- **La regla de la clase 6:** 27,6 puntos (lift 1,52).
- **Marcadas no redundantes:** entre 10 y unos 28 puntos.
- **Referencia nula:** el azar ya produce diferencias de hasta 26,5 puntos en el 5 % de las búsquedas.

**9. ¿Qué soporte real tienen en participantes?**
- **La regla de la clase 6:** 46 participantes cumplen antecedente y consecuente, de 57 con el antecedente; el soporte es 8,7 %.
- **Marcadas:** la mediana de n_A es 67 y el 90 % tiene 96 o menos.
- **Antecedentes grandes:** ninguna regla con más de 185 participantes en el antecedente se aleja 10 puntos de la basal.

**10. ¿Qué reglas son redundantes?**
- **Cuántas:** 787 de las 971 marcadas (81 %). Agregan una condición que mejora la confianza en menos de 5 puntos.
- **Patrón típico:** una regla de dos condiciones con trabajo, a la que se le suma un hábito.

**11. ¿Cuáles son estables?**
- **Cuántas:** 480 reglas marcadas reaparecen en al menos el 70 % de las submuestras con la misma dirección, incluida la de la clase 6 (88 %).
- **Advertencia:** la estabilidad no distingue señal de ruido. Las reglas compatibles con el azar también son estables a menudo, porque las submuestras comparten el 80 % de los datos.

**12. ¿Cuáles también aparecen bajo la referencia nula?**
- **Todas menos una.** Las 183 marcadas no redundantes, las redundantes y las débiles tienen una fuerza que el azar alcanza al buscar entre 9.761 reglas.

**13. ¿Cómo afectan los datos imputados?**
- **Sin imputados (S1):** ninguna regla cambia de dirección, pero muchas pierden casos (373 quedan bajo el umbral). Entre ellas está la de la clase 6, que baja a 52 participantes.
- **Lectura:** las imputaciones no fabrican las reglas, pero ayudan a que algunas superen el umbral.
- **Señal global:** se mantiene sin imputados, con 889 marcadas frente a 460 esperadas.

**14. ¿Qué pasa al cambiar agrupaciones y umbrales?**
- **Categorías originales:** dan casi lo mismo.
- **Agrupación gruesa (S2b):** dos reglas superan su nula solo ahí, una de ellas redundante (informe 12). No son evidencia confirmatoria.
- **Umbrales:** con un umbral más bajo hay muchas más reglas y ninguna supera la nula; con uno más alto, menos reglas y tampoco ninguna.
- **Conclusión:** no cambia.

**15. ¿Qué restricciones presentan los módulos laboral y de cuidado?**
- **Poblaciones parciales:** solo aplican a quienes trabajan (287 con información laboral; 309 ampliada) y a quienes cuidan (239 con sobrecarga observada; 251 ampliada), así que se analizaron por separado, con su propia basal y sus umbrales proporcionales.
- **Circularidad:** las preguntas laborales mencionan los síntomas, y la sobrecarga puede ser consecuencia de ellos.
- **Resultados:** en quienes trabajan no hay reglas que superen la nula. En quienes cuidan hay una, la misma en S7b y S7b-251, con 34 participantes y la sobrecarga como condición; es exploratoria.

**16. ¿Existen reglas suficientemente sólidas para destacar, o la evidencia es débil?**
- **La evidencia es débil.** Hay una señal global, pero ninguna regla es robusta. La única que cumple los criterios es frágil ante las sensibilidades.

**17. ¿Qué limitaciones impiden considerarlas clínicas o causales?**
- **Datos:**
  - Son sintéticos.
  - Las asociaciones son marginales, sin ajuste por otras variables.
  - No se sabe la dirección: los síntomas podrían influir en los hábitos.
  - Hay imputaciones en muchas participantes.
  - No hay validación externa.
- **Diseño:**
  - No es un análisis ciego, porque las Fases 35 y 37D ya examinaron estas asociaciones.
  - Las mismas 529 sirven para descubrir y evaluar, sin muestra de confirmación.
- **Variables:** algunas están próximas a los síntomas.
- **Estabilidad:** no implica validez.

**18. ¿Qué se exploró en la Fase 39R?**
- **Diferencias entre estratos:** se compararon trabajo, pareja, ejercicio (0, 1-2 y 3 o más días) y cuidado, con un protocolo sellado, referencia nula dentro de cada estrato y denominadores visibles. Sus resultados están en los documentos de la Fase 39R.

**19. ¿Qué pruebas se ejecutaron?**
- **Pruebas:** 20 de 20 superadas.
- **Controles negativos:** 11 de 11 errores introducidos detectados.
- **Cobertura:**
  - Identificadores y MRS.
  - Antecedentes prohibidos, contradicciones y agrupaciones.
  - Imputaciones y módulos.
  - Medidas, equivalencia de algoritmos y del evaluador matricial, y reproducibilidad.
  - Estabilidad sin fuga y referencia nula.
  - Multiplicidad y reglas triviales.
  - Sello y barreras de exclusión.
  - Clasificación.

**20. ¿Se preservaron todos los archivos históricos?**
- **Sí.** En el control final de la 38R, 6.265 archivos con huella no cambiaron (0 cambiados) y los manifiestos de 6.462 archivos solo muestran 4 diferencias ya documentadas antes de la corrección.
- **Simulador:** sus archivos no se abrieron.
- **Git:** rama datos-simulados, HEAD 573d3a3, sin commit ni push.
