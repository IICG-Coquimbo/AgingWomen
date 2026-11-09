# Nota para la tesis: estabilidad de la selección con las 33 variables finales

*Texto propuesto para la sección 3.6, en estilo académico. Se puede insertar después del párrafo que describe la selección definitiva por SU y FCBF.*

---

**Evaluación retrospectiva de la estabilidad de la selección.** La estabilidad descrita en el protocolo de la Fase 35B se estimó por primera vez el 02-11-2026, sobre una lista preliminar de 30 candidatas que incluía `doble_carga` y usaba un umbral q < 0,05. Después se cambió la lista de candidatas: se excluyeron `doble_carga` y, por dominancia superior al 85 %, `usa_medicamentos_diabetes`; edad, IMC y situación laboral pasaron de control a candidatas; se incorporó la sobrecarga de las cuidadoras, y el umbral pasó a q < 0,10. Con estos cambios, esa estimación dejó de corresponder a la configuración definitiva. Por eso se repitió el procedimiento con las 33 variables finales. Esta repetición se realizó **después del cierre de las Fases 36 a 39** y no modificó ninguno de sus resultados.

El procedimiento consistió en 500 remuestreos bootstrap estratificados por la severidad sintomática (MRS ≥ 16), con reemplazo y conservando 281 casos severos y 248 no severos. En cada remuestreo se repitió la selección completa:

- incertidumbre simétrica (SU) con 5.000 permutaciones por variable;
- corrección de Benjamini-Hochberg sobre la familia de 33 pruebas;
- relevancia con q < 0,10;
- pruebas de redundancia entre pares de relevantes;
- FCBF en tres etapas (general, laboral y cuidadoras), en sus variantes adaptada y estándar.

Las subpoblaciones laboral y de cuidadoras acompañaron a cada persona remuestreada. Se usaron las mismas semillas de remuestreo que en la estimación preliminar, de modo que ambas se basan en las mismas 500 muestras.

La estabilidad de la selección final fue baja:
- Ninguna variable fue seleccionada en la mitad o más de los remuestreos. Las cuatro variables de la selección definitiva (IMC, frecuencia de ejercicio de fuerza, situación laboral y lugar de trabajo comprensivo) fueron las más frecuentes, con 39,0 %, 35,2 %, 32,6 % y 31,4 %.
- El índice de Nogueira fue 0,129 (IC 95 %: 0,118–0,139) en la variante adaptada y 0,128 en la estándar.
- El Jaccard promedio entre remuestreos fue 0,14.
- Ningún remuestreo reprodujo exactamente la selección adaptada definitiva. El Jaccard medio con ella fue 0,24.

En cambio, la **relevancia** fue considerablemente más estable que la selección. Cinco de las seis variables relevantes en la definitiva superaron el filtro de relevancia en el 82 % al 91 % de los remuestreos: días de ejercicio, ejercicio de bajo impacto, IMC, ejercicio de fuerza y lugar de trabajo comprensivo. La sexta, situación laboral, lo superó en el 67 %. Esto ocurrió porque la selección tuvo que elegir entre variables muy relacionadas entre sí:
- Las tres variables de ejercicio fueron relevantes juntas en casi todos los remuestreos.
- En el 78,8 % de los remuestreos FCBF retuvo una de ellas, y casi nunca más de una (0,2 %).
- Cuál de las tres quedaba seleccionada cambió de una muestra a otra.

La inestabilidad, por lo tanto, afecta sobre todo a la elección de una representante dentro de un grupo de variables relacionadas, más que a la presencia de una señal asociada a la actividad física y al IMC.

Tres advertencias limitan esta interpretación:
1. En el bootstrap las personas repetidas se tratan como observaciones distintas, también en las permutaciones. Esto tiende a hacer más fácil la significancia: en promedio resultaron relevantes 13,2 variables por remuestreo, frente a 6 en la muestra original. Por eso los porcentajes se interpretan solo de forma descriptiva.
2. Se usaron 5.000 permutaciones por remuestreo, como en la estimación histórica, y no las 10.000 o 50.000 de la selección definitiva.
3. Los datos son sintéticos. El resultado describe el comportamiento del procedimiento de selección en este conjunto y **no constituye una validación clínica** de ninguna variable.

Esta evaluación no cambia las Fases 36 y 37. En la configuración definitiva FCBF tiene carácter informativo y no elimina variables: la matriz global usada para el agrupamiento se construyó con las variables generales, independientemente del resultado de la selección. Por eso la estabilidad del selector no debe confundirse con la estabilidad de los agrupamientos, que se evaluó por separado en la Fase 37.

---

**Correcciones al texto existente**

- Si la sección 3.6 o un anexo muestra la figura `estabilidad_seleccion.png` o los índices 0,121 y 0,126, se debe indicar que corresponden a la lista preliminar de 30 candidatas con q < 0,05, o reemplazarlos por la figura `f01_estabilidad_33_variables_finales.png` y los valores de esta nota.
- El término «bootstrap» es correcto: el procedimiento histórico y este complemento remuestrean con reemplazo. No hace falta corregir el nombre.
- No se debe decir que las variables seleccionadas por FCBF son «estables» ni «robustas». Lo que se puede sostener es que su **relevancia** se detecta de forma consistente y que la representante elegida por FCBF varía entre muestras.
