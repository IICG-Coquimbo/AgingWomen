# 1. Estado

**La Fase 37B queda cerrada: 26 de 26 pruebas superadas.** Las 420 configuraciones, las 20 réplicas nulas y los 3.332 ajustes de sensibilidad están completos. La Fase 37C no se inició y no hay commit ni push. Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.

# 2. ¿Hay agrupaciones suficientemente diferenciadas y estables?

**Estables, sí, en parte. Claramente diferenciadas, no hay evidencia.**

- **K-means forma particiones reproducibles con 2 a 4 grupos.** Ward no, salvo parcialmente con k = 2.
- **La separación es modesta.** Con 3 o más ejes, y k ≥ 3, la silueta es de 0,30 o menos. Con 2 ejes llega a 0,42, pero esos ejes retienen solo cerca del 11 al 14 % de la inercia.
- **Con k = 2, los grupos se dividen casi solo por actividad física.** Esa división, además, cambia con la codificación de las ordinales.
- **Con k = 3, la división añade una dimensión que depende de una variable** (S-SOLAPE: ARI 0,24).
- **Superar la nula** muestra que las variables no son independientes, no que existan grupos naturales.

Por eso, estos grupos se entienden mejor como **una segmentación útil de un continuo** que como tipos naturales de participantes. Si esa segmentación sirve para la plataforma es una pregunta para la Fase 37C.

# 3. Regla del protocolo

108 configuraciones cumplen las dos condiciones del protocolo. La regla resultó **poco exigente**: 57 de ellas tienen un peso del eje 1 de 0,80 o más, y 52 tienen repeticiones inestables. El protocolo está sellado, así que la regla se aplicó sin cambios y estas limitaciones se informan aparte.

**Vista resumida que fija el protocolo:**

| Configuración | Silueta | ARI entre | Percentil 5 | Grupo menor | Peso del eje 1 | Señales |
|---|---|---|---|---|---|---|
| F1_c02_km_k2 | 0,508 | 0,98 | 0,94 | 92 | 1,00 | eje 1 |
| F2_c02_km_k3 | 0,413 | 0,98 | 0,95 | 83 | 0,65 | Ninguna |
| F1_c03_km_k4 | 0,298 | 0,95 | 0,91 | 76 | 0,51 | Ninguna |
| F1_c03_km_k6 | 0,270 | 0,90 | 0,76 | 30 | 0,47 | Ninguna |
| F2_c03_ward_k2 | 0,399 | 0,79 | 0,61 | 79 | 0,99 | eje 1, inestables |
| P1_c08_km_k2 | 0,219 | 0,98 | 0,93 | 94 | 0,98 | eje 1 |
| P1_c02_km_k3 | 0,424 | 0,96 | 0,89 | 82 | 0,63 | Ninguna |
| P2_c12_km_k4 | 0,080 | 0,84 | 0,70 | 76 | 0,48 | Ninguna |
| P1_c02_km_k5 | 0,413 | 0,96 | 0,91 | 51 | 0,67 | Ninguna |
| P1_c02_km_k6 | 0,392 | 0,87 | 0,72 | 51 | 0,65 | Ninguna |
| P2_c02_km_k7 | 0,394 | 0,86 | 0,69 | 23 | 0,63 | grupo pequeño |
| P2_c02_km_k8 | 0,392 | 0,84 | 0,68 | 22 | 0,62 | grupo pequeño |
| P2_c02_ward_k2 | 0,512 | 0,81 | 0,51 | 63 | 0,99 | eje 1, inestables |
| P1_c02_ward_k5 | 0,367 | 0,67 | 0,52 | 58 | 0,69 | inestables |
| R0P1_cTodas_km_k2 | 0,127 | 0,94 | 0,88 | 90 | 0,95 | eje 1 |
| R0P1_cTodas_ward_k2 | 0,127 | 0,72 | 0,58 | 73 | 0,91 | eje 1, inestables |

Esta vista elige en cada grupo la de mayor ARI entre remuestreos, lo que favorece a 2 componentes, donde la nula también es alta. Por eso, el documento de preparación de la Fase 37C propone además otra lista.

# 4. Adiciones y decisiones propias

El encargo no pidió lo siguiente; lo incorporé y queda a tu criterio:

- **Peso del primer eje** (`SSB en C1 / SSB total`), descriptivo.
- **Semilla alternativa en K-means,** para distinguir la inestabilidad del optimizador de la del muestreo.
- **Asignación fuera de muestra,** en cada remuestreo.
- **Sensibilidades en las 98 combinaciones de cada variante,** en lugar de una configuración de referencia, para no elegir antes de tiempo.
- **Regla de la sección 11 del protocolo,** con los controles de búsqueda múltiple.
- **Ejemplos fijos (5 ejes, k = 3)** en las figuras ilustrativas. No son una selección.

# 5. Pruebas e integridad

26 de 26 pruebas superadas. El control introdujo 22 errores, detectados en 26 de 26 comprobaciones. Detalle en `14_informe_pruebas.md` y `15_informe_integridad.md`. Las Fases 34, 35, 36 y 37A no cambiaron.

# 6. Lo que no se hizo

No se seleccionó un modelo, no se caracterizaron los grupos, no se les dio nombre, no se usó el MRS, no se usó GMM, no se generaron reglas de asociación y no se modificó la plataforma.

# 7. Límites

- **Datos sintéticos.** Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.
- **No son diagnósticos.** Los grupos no equivalen a niveles de riesgo, y su número no indica un orden.
- **La nula solo descarta independencia.** Un conjunto con variables correlacionadas puede superarla sin tener grupos naturales. Tampoco es una prueba sobre la población.
- **La reducción no se recalculó en los remuestreos.** Se ajustó con las 529, así que la estabilidad evalúa solo el agrupamiento.
- **Pocas réplicas.** Con 20 réplicas, `p` no baja de 0,048.
