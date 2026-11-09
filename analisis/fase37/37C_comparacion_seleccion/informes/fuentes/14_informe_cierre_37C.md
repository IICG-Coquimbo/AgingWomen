# Conclusión

**Conclusión B: segmentación operativa condicionada, con `P2_c12_km_k4` como propuesta provisional.** No hay evidencia suficiente de grupos naturales: los resultados son compatibles con un continuo. La propuesta cumple las reglas selladas, pero es débil, y no seleccionar nada también es defendible.

Lo que aquí se propone es provisional. La decisión final queda en manos de la responsable del proyecto.

Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.

# Explicación en lenguaje sencillo

**¿Qué se quería saber?** Si las 529 participantes del conjunto sintético se dividen en grupos que existan de verdad en los datos, o si solo se puede repartirlas de forma práctica.

**¿Qué se encontró?** No hay evidencia suficiente de grupos naturales. Los resultados son compatibles con un continuo: en separación, la división propuesta no se distingue de un conjunto sin grupos con las mismas correlaciones. Algunas medidas sí muestran diferencias con ese conjunto, pero no bastan para afirmar que existan grupos. Imagine dividir a las personas por estatura en «bajas», «medianas» y «altas»: la división puede servir, pero nadie cree que existan tres tipos de personas.

**¿Qué se propone?** Una división práctica en 4 segmentos, `P2_c12_km_k4`, como herramienta de trabajo provisional. No es un diagnóstico, ni una clasificación clínica, ni un modelo validado.

**¿Por qué esa y no otras?**

- Las divisiones en 2 grupos son las más estables, pero casi solo separan según cuántos días hace ejercicio la participante. Para eso basta con preguntarlo.
- Las divisiones en 3 grupos son básicamente un gradiente de ejercicio.
- Las que parecían mejores en la fase anterior, con 3 componentes, caen al repetir todo el procedimiento.
- Esta división de 4 segmentos es la que mejor resiste entre las que combinan varios temas: ejercicio, pareja, trabajo y alimentación.

**¿Qué tan firme es?** No mucho. Es lo que las reglas fijadas de antemano permiten, no una conclusión sólida:

- Si se quitan dos preguntas (`tiene_actividad_sexual` y `distension_abdominal`), la división cambia bastante.
- Cerca de la mitad de las participantes queda cerca de la frontera entre dos segmentos.
- Tres preguntas directas (trabajo, pareja y días de ejercicio) reproducen buena parte de la división.
- Se probaron 7 criterios alternativos, planteados después de ver los resultados y no como reglas de decisión. Con 5 de ellos, la conclusión habría sido no seleccionar nada.

**¿Qué falta?** Datos reales e independientes. Todo esto se hizo con datos simulados y nada de esto describe a mujeres reales.


# Respuestas a las preguntas del encargo

## 1. ¿Qué configuraciones A y B se examinaron?

108 de la Lista A y 15 de la Lista B, todas también en A. La estabilidad se midió en 127 y el análisis completo en 50 priorizadas.

## 2. ¿Cuáles llegaron a la comparación final?

`F1_c02_km_k2`, `P2_c12_km_k4`, `P2_c03_km_k3`, `P2_c05_km_k3`, `P2_c08_km_k4`. `P2_c12_km_k4` representa también a `P1_c12_km_k4`, y `P2_c05_km_k3` a `P1_c05_km_k3`.

## 3. ¿Qué pasó al recalcular PCA y FAMD dentro de los remuestreos?

Los subespacios se parecen (mediana 0,92), pero las fronteras se mueven. Es el paso que más reduce la estabilidad. Las configuraciones con pocos componentes parecían estables solo porque la reducción estaba congelada: `F2_c03_km_k3` pasa de 0,95 a 0,54.

## 4. ¿La estabilidad subió o bajó frente a la Fase 37B?

Bajó. En la Lista A, con media ≥ 0,65: de 108 a 73. Sumando p05 ≥ 0,50: de 88 a 53. Sobre 0,80: de 58 a 30. `P2_c12_km_k4` baja de 0,84 a 0,77.

## 5. ¿Qué mostró la referencia correlacionada?

Datos sin grupos reproducen buena parte de lo observado, incluidos ARI altos. Ninguna finalista pasa el control de búsqueda múltiple en silueta y estabilidad, aunque Calinski-Harabasz y Davies-Bouldin sí lo superan en el conjunto de la búsqueda (p = 0,010 y 0,050). `P2_c12_km_k4` tiene silueta igual a la nula (p = 0,238) y estabilidad E1 sobre las 20 réplicas (p = 0,048, el mínimo posible). La referencia usa la enmienda α = 0,05, de carácter exploratorio.

## 6. ¿Qué tan grave fue S-ORD?

Depende de la configuración. Es grave en k = 2 (cerca de 0,25) y en FAMD con 5 u 8 componentes y k = 3 (cerca de 0,20). Es moderada en `P2_c12_km_k4` (0,69), con cambios concentrados en la frontera (AUC 0,82), y se mantiene por la regla 6.3. Pero con ridit su estabilidad baja a 0,53. Viene sobre todo del reajuste de fronteras, no de los ejes.

## 7. ¿Qué sensibilidades afectaron más a las finalistas?

S-SOLAPE en las de k = 3 y k = 4 (`P2_c12_km_k4`: 0,36, crítica) y S-ORD en todas. Fuera de las reglas, S-BLOQUE también es baja (0,14). Población, imputación y edad afectan poco.

## 8. ¿Qué tan multivariables son las agrupaciones?

Las de k = 2 y k = 3 son principalmente gradientes de ejercicio. `P2_c12_km_k4` es multivariable según la regla (9 variables, 4 bloques), pero tres preguntas la reconstruyen con ARI 0,68 (exploratorio).

## 9. ¿K-means mantuvo sus ventajas frente al método aglomerativo?

Sí: mayor estabilidad, asignación directa, y todas las finalistas son K-means. Eso no indica que los grupos sean reales: con `P2_c12_km_k4`, el ARI entre K-means y Ward es 0,33.

## 10. ¿Qué configuraciones asignan nuevas participantes con mayor consistencia?

Las de k = 2 (ARI fuera cercano a 0,95), que no son elegibles. Entre las elegibles, `P2_c12_km_k4` (0,83, p05 0,73, desacuerdo 6,4 %). El margen identifica bien las asignaciones dudosas, pero señala a muchas participantes.

## 11. ¿Modelo, segmentación operativa condicionada o ninguna selección?

Segmentación operativa condicionada (B).

## 12. Justificación exacta

Cumple los requisitos sellados de B: finalista, multivariable, incertidumbre evaluada y regla V declarada. No cumple A por el CRIT en S-SOLAPE y por no superar a la nula con control de búsqueda múltiple. Entre las elegibles, tiene menos advertencias que `P2_c08_km_k4` (4 frente a 7). Es B en los 9 escenarios de umbrales, pero pasaría a C en 5 de 7 lecturas alternativas, planteadas después de ver los resultados y no aplicadas para decidir.

## 13. Limitaciones que permanecen

Datos sintéticos y sin validación independiente; protocolo no ciego; enmienda con margen estrecho; resolución de 20 réplicas; potencia frente a grupos débiles sin evaluar; partes no recalibradas en E3; dependencia de S-SOLAPE, de la codificación, de la ponderación, del algoritmo y del método de reducción; 14 configuraciones sin evaluación completa; imputación de `tiene_actividad_sexual` abierta; y umbrales de incertidumbre sin definir.

## 14. Pruebas ejecutadas y superadas

26 de 26 pruebas, y 23 de 23 errores introducidos detectados.

## 15. ¿Se preservaron los archivos protegidos?

Sí. 2.217 archivos iguales a sus manifiestos, HEAD en 745d689, sin escrituras fuera de la subfase y sin cambios en Django.

## 16. Archivos creados

Unos 1131 archivos, todos en `analisis/fase37/37C_comparacion_seleccion/`. Ver `informes/00_indice_entregables.md` e `integridad/manifiesto_final_37C.csv`.

## 17. ¿Qué queda preparado para la Fase 37D?

La nota `15_nota_metodologica_37D.docx`, las etiquetas y parámetros provisionales, y la tabla de variables. **La Fase 37D no se inició.**

# Réplicas y estado de la fase

- **Recuperadas:** 72 réplicas (000 a 071), todas válidas.
- **Ejecutadas de nuevo:** ninguna. Por primera vez: 28 (072 a 099), más las 20 del contraste α = 0.
- **Estado:** la Fase 37C puede declararse **completa desde el punto de vista técnico**, a la espera de la decisión de la responsable.
