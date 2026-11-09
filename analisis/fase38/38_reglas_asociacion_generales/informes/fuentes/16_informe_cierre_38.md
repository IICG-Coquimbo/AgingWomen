# Conclusión

**La evidencia de reglas de asociación es débil.**

- **Señal difusa:** en los datos sintéticos hay más combinaciones de hábitos y contexto asociadas con la severidad de lo que produciría el azar (1.119 reglas marcadas frente a 650 esperadas). Esa señal está repartida en muchas reglas débiles.
- **Reglas puntuales:** de 12.201 reglas, **solo una cumple todos los criterios sellados**, y lo hace por poco. Además:
  - incluye una variable próxima a síntomas;
  - no se mantiene sin imputaciones ni con otros umbrales.
- **Conclusión:** **no hay reglas suficientemente sólidas para destacar como hallazgos.** Los patrones que más se repiten (trabajar y no hacer ejercicio con síntomas severos; no trabajar y tener pareja con síntomas no severos) coinciden con las asociaciones pequeñas de la Fase 37D, pero esta fase no las confirma de forma independiente.

Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa.

# Respuestas

**1. ¿Cuántas variables se utilizaron?**
- **Análisis principal:** 31 variables generales medidas en las 529 participantes.
- **Sensibilidades:** 4 más, cada una solo en su sensibilidad: el IMC, las dos preguntas laborales y la sobrecarga.
- **Excluidas:** el MRS (solo como consecuente), los segmentos y la etapa menopáusica.
- **Criterio:** ninguna variable se eligió por su asociación con el MRS.

**2. ¿Cómo se agruparon las categorías poco frecuentes?**
- **Regla fija:** se aplicó la regla del protocolo, sin mirar el MRS: una categoría ordinal con menos de 27 participantes se une a su vecina de menor frecuencia.
- **Nominales:** las escasas, sin vecina compatible, no generan ítem: «compro comida» y «otro» en quién prepara; FFAA, «ninguna» y «no sabe» en previsión.
- **Alcance:** 40 categorías originales tenían menos del 5 % (varias con 0 participantes) y se resolvieron así (informe 04).

**3. ¿Cuántos ítems transaccionales se generaron?**
- **Principal:** 94 ítems, con unos 31 por participante, más los dos consecuentes.
- **Sensibilidades:** entre 64 y 120.

**4. ¿Qué configuraciones de búsqueda se evaluaron?**
- **Principal:** antecedentes de 1 a 3 condiciones, al menos 53 participantes con el antecedente y 27 con antecedente y consecuente.
- **13 sensibilidades:**
  - S1: sin imputados.
  - S2a y S2b: agrupaciones.
  - S3: umbrales de 27 y 80.
  - S4: largo 1 y 2.
  - S5: sin frecuencias de ejercicio.
  - S6: sin variables próximas a síntomas.
  - S7a y S7b: quienes trabajan y quienes cuidan.
  - S8a y S8b: IMC.
- **Para cada configuración:** 1.000 permutaciones nulas. En la principal, además, 200 submuestras.

**5. ¿Cuántas reglas se encontraron?**
- **Principal:** 12.201 reglas evaluadas, de las cuales 1.119 son marcadas (al menos 10 puntos sobre la basal). Son 674 hacia síntomas severos y 445 hacia no severos.

**6. ¿Cuántas superan los criterios previamente definidos?**
- **Clase 6:** **una**, que cumple marcada, no redundante, supera la referencia nula y estable.
- **Las demás marcadas:** 926 son redundantes y 192 son compatibles con la nula.

**7. ¿Cuáles son las principales reglas y cómo se interpretan?**
- **La regla de la clase 6:** quienes trabajan, no hacen ejercicio de bajo impacto y casi nunca tienen distensión abdominal → síntomas severos.
  - **Cifras:** 46 de 57, es decir, 81 % frente al 53 % general.
  - **Lectura:** describe una combinación frecuente en la simulación. No dice que trabajar o no hacer ejercicio cause síntomas, y la dirección de la distensión es poco intuitiva.
- **Otras reglas fuertes:** son compatibles con el azar (informe 07).

**8. ¿Cuánto se aleja su confianza de la frecuencia basal?**
- **La regla de la clase 6:** 27,6 puntos (lift 1,52).
- **Marcadas no redundantes:** entre 10 y unos 28 puntos.
- **Referencia nula:** el azar ya produce diferencias de hasta 26,7 puntos en el 5 % de las búsquedas.

**9. ¿Qué soporte real tienen en participantes?**
- **La regla de la clase 6:** 46 participantes cumplen antecedente y consecuente, de 57 con el antecedente; el soporte es 8,7 %.
- **Marcadas:** casi todas tienen entre 53 y unas 100 participantes en el antecedente.
- **Antecedentes grandes:** ninguna regla con más de unas 150 participantes en el antecedente se aleja 10 puntos de la basal.

**10. ¿Qué reglas son redundantes?**
- **Cuántas:** 926 de las 1.119 marcadas (83 %). Agregan una condición que mejora la confianza en menos de 5 puntos.
- **Patrón típico:** una regla de dos condiciones con trabajo, a la que se le suma un hábito.

**11. ¿Cuáles son estables?**
- **Cuántas:** 535 reglas marcadas reaparecen en al menos el 70 % de las submuestras con la misma dirección, incluida la de la clase 6 (88 %).
- **Advertencia:** la estabilidad no distingue señal de ruido. Las reglas compatibles con el azar también son estables a menudo, porque las submuestras comparten el 80 % de los datos.

**12. ¿Cuáles también aparecen bajo la referencia nula?**
- **Todas menos una.** Las 192 marcadas no redundantes, las redundantes y las débiles tienen una fuerza que el azar alcanza al buscar entre 12.201 reglas.

**13. ¿Cómo afectan los datos imputados?**
- **Sin imputados (S1):** ninguna regla cambia de dirección, pero muchas pierden casos (373 quedan bajo el umbral). Entre ellas está la de la clase 6, que baja a 52 participantes.
- **Lectura:** las imputaciones no fabrican las reglas, pero ayudan a que algunas superen el umbral.
- **Señal global:** se mantiene sin imputados, con 889 marcadas frente a 460 esperadas.
- **Diabetes y previsión:** no tienen marca por participante, así que no pudieron evaluarse sin imputados.

**14. ¿Qué pasa al cambiar agrupaciones y umbrales?**
- **Categorías originales:** dan casi lo mismo.
- **Agrupación gruesa:** hace aparecer reglas de «3 días o más de ejercicio → no severos» que superan la nula solo ahí.
- **Umbrales:** con un umbral más bajo hay muchas más reglas y ninguna supera la nula; con uno más alto, menos reglas y tampoco ninguna.
- **Conclusión:** no cambia.

**15. ¿Qué restricciones presentan los módulos laboral y de cuidado?**
- **Poblaciones parciales:** solo aplican a quienes trabajan (309) y a quienes cuidan (251), así que se analizaron por separado, con su propia basal y sus umbrales proporcionales.
- **Circularidad:** las preguntas laborales mencionan los síntomas, y la sobrecarga puede ser consecuencia de ellos.
- **Resultados:** en quienes trabajan no hay reglas que superen la nula. En quienes cuidan hay una, con 34 participantes y la sobrecarga como condición.

**16. ¿Existen reglas suficientemente sólidas para destacar, o la evidencia es débil?**
- **La evidencia es débil.** Hay una señal global, pero ninguna regla es robusta. La única que cumple los criterios es frágil ante las sensibilidades.

**17. ¿Qué limitaciones impiden considerarlas clínicas o causales?**
- **Datos:**
  - Son sintéticos.
  - Las asociaciones son marginales, sin ajuste por otras variables.
  - No se sabe la dirección: los síntomas podrían influir en los hábitos.
  - Hay imputaciones en muchas participantes, y diabetes y previsión no tienen marca.
- **Diseño:**
  - No es un análisis ciego, porque las Fases 35 y 37D ya examinaron estas asociaciones.
  - Las mismas 529 sirven para descubrir y evaluar, sin muestra de confirmación.
- **Variables:** algunas están próximas a los síntomas.
- **Estabilidad:** no implica validez.

**18. ¿Qué se recomienda explorar en la Fase 39?**
- **Diferencias entre estratos:** comparar trabajo, pareja, ejercicio (0, 1-2 y 3 o más días) y cuidado, con un protocolo sellado, referencia nula dentro de cada estrato y denominadores siempre visibles (nota 17).
- **Expectativas:** son prudentes, porque los estratos son más pequeños.

**19. ¿Qué pruebas se ejecutaron?**
- **Pruebas:** 20 de 20 superadas.
- **Controles negativos:** 18 de 18 errores introducidos detectados.
- **Cobertura:**
  - Identificadores y MRS.
  - Antecedentes prohibidos, contradicciones y agrupaciones.
  - Imputaciones y módulos.
  - Medidas, equivalencia de algoritmos y del evaluador matricial, y reproducibilidad.
  - Estabilidad sin fuga y referencia nula.
  - Multiplicidad y reglas triviales.
  - Integridad, Django y sello.
  - Clasificación.

**20. ¿Se preservaron todos los archivos históricos?**
- **Sí.** 3.642 archivos protegidos de las Fases 34 a 37D coinciden con sus manifiestos al inicio y al final.
- **Simulador:** los 4 archivos del manifiesto 34-35 no se abrieron.
- **Git:** HEAD sigue en 745d689, sin cambios en Django ni en los datos, y sin commit ni push.

# Decisiones para la responsable

1. **Lectura de la conclusión:** confirmar que la Fase 38 se lee como evidencia débil, sin reglas destacadas.
2. **Fase 39:** decidir si se inicia y con qué estratos (nota 17).
