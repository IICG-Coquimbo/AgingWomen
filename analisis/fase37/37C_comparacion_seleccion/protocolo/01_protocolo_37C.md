# 1. Estado de este documento

Este protocolo se redactó y se selló con SHA-256 **antes de ejecutar cualquier evaluación nueva de la Fase 37C**. Al sellarlo no existía ningún resultado de estabilidad con reducción reajustada, de referencia correlacionada, de descomposición de S-ORD, de interpretabilidad ni de asignación de esta fase.

**No es un protocolo ciego.** Quien lo redacta ya conoce los resultados de las Fases 37A y 37B. Por eso, cada regla indica su origen y su momento, y ninguna decisión tomada aquí debe presentarse como preespecificada en las fases anteriores.

| Etiqueta | Significado |
|---|---|
| **Previo-D13** | Fijado en el protocolo D-13 antes de ajustar PCA o FAMD |
| **Previo-37B** | Fijado en el protocolo de la Fase 37B antes de formar clústeres |
| **Encargo-37C** | Pedido en el encargo de esta fase, escrito después de conocer la Fase 37B |
| **Propuesta-37C** | Completado aquí, después de conocer la Fase 37B y antes de evaluar la Fase 37C |

Los protocolos D-13 y 37B no se modifican.

## 1.1. Resultados ya observados antes de sellar

Estas cifras condicionan inevitablemente el diseño, y se declaran:

- Lista A: 108 configuraciones, 57 con peso del eje 1 de 0,80 o más y 52 con repeticiones inestables.
- K-means supera a Ward en estabilidad con la reducción congelada. S-ORD: ARI mediano 0,47 en K-means.
- S-SOLAPE: ARI mediano 0,24 con k = 3, y de 0,35 a 0,41 en las configuraciones de la Lista B con k = 4.
- S-ORD: cerca de 0,27 con k = 2; 0,80 en F1_c03_km_k3; 0,20 en F1_c05_km_k3.
- Silueta de 0,30 o menos con 3 o más ejes y k ≥ 3.

## 1.2. Hallazgo previo a la evaluación

Al comprobar si la regla de imputación podía reestimarse, 27 de las 28 variables generales con valor imputado reproducen ese valor sobre las celdas observadas de las 529. **La excepción es `tiene_actividad_sexual`:** las celdas observadas dan 251 «SI» y 248 «NO», de modo que la moda en las 529 es «SI», mientras que sus 30 celdas imputadas valen «NO». Según `informe_limpieza_usuaria.md`, la moda se calculó sobre 546 filas, y allí resultó «NO». Es decir, esa imputación descansa en un empate casi perfecto, sobre una variable con gran peso en el eje 2 (de 23 a 32 % de contribución).

No se corrige nada en las fases anteriores. Se trata como pregunta de esta fase: ver S-IMPMODA (sección 7).

# 2. Reglas generales

| Regla | Origen |
|---|---|
| Se distingue entre encontrar grupos naturales y construir segmentos operativos dentro de un continuo | Encargo-37C |
| No se selecciona un modelo automáticamente. Concluir que ninguno es adecuado es un resultado válido | Encargo-37C |
| Solo el conjunto sintético de 529 participantes. No se lee `datos/` ni la verdad del simulador | Encargo-37C |
| El MRS no se lee ni se usa para elegir, evaluar ni colorear | Encargo-37C |
| No se usan Random Forest ni Shannon como criterio de selección. No se agrega GMM ni reglas de asociación | Encargo-37C |
| No se modifican las Fases 34, 35, 36, 37A ni 37B, ni Django, ni se hace commit o push. La Fase 37D no se inicia | Encargo-37C |
| Sin puntuación compuesta: una métrica alta no compensa una debilidad crítica | Encargo-37C |
| Todas las salidas quedan en `analisis/fase37/37C_comparacion_seleccion/` | Encargo-37C |
| Un gancho de auditoría registra lecturas y escrituras, y detiene la ejecución si se lee `datos/` o se escribe fuera | Propuesta-37C |

**Datos sintéticos.** Ningún resultado permite afirmar nada sobre mujeres reales. Los grupos no son diagnósticos, niveles de riesgo ni tipos naturales.

# 3. Listas y conjunto de evaluación

| Conjunto | Definición | Carácter |
|---|---|---|
| **Lista A** | Las 108 con `lista_37C = True` en `resultados/tabla_completa_configuraciones.csv` de la Fase 37B, sin cambios | Regla Previo-37B; poco exigente |
| **Lista B** | Las 15 de la segunda tabla de `informes/17_preparacion_37C.docx`, leídas del propio archivo | **Exploratoria permanentemente:** se definió tras ver resultados |
| **Vista A** | Las 16 con `lista_37C_visible = True` | Regla Previo-37B; controles representativos |
| **Referencias k = 2** | F1_c05_km_k2 y P1_c05_km_k2, las sugeridas en el documento de preparación | Segmentación dominada por ejercicio |
| **Comparador Ward** | Las homólogas Ward de la Lista B (mismo espacio, componentes y k) | Comparación; no se eliminan |
| **Referencias sin reducción** | R0P1 y R0P2, K-means, k = 3 y 4 | Comparación |

**Conjunto priorizado:** Lista B ∪ Vista A ∪ referencias k = 2 ∪ comparador Ward ∪ referencias sin reducción. Recibe las pruebas costosas: referencia correlacionada, S-ORD descompuesta e interpretabilidad.

**Estabilidad:** se evalúa en la Lista A completa y en el conjunto priorizado, porque su costo es bajo y evita que la comparación dependa de una lista elegida después de ver los resultados. No se repiten las 420.

Estar en ambas listas no da ventaja alguna (Encargo-37C).

# 4. Estabilidad del procedimiento completo

## 4.1. Cuatro niveles, que no son equivalentes

| Nivel | Se reajusta dentro de la submuestra | Queda congelado |
|---|---|---|
| **E0** (Fase 37B) | Agrupamiento | Imputación, escalado, reducción |
| **E1** | Reducción y agrupamiento | Imputación, escalado |
| **E2** | Escalado (medias, DE, proporciones y media del IMC), reducción y agrupamiento | Imputación |
| **E3** | Imputación de las celdas marcadas, escalado, reducción y agrupamiento | Lo indicado en 4.3 |

E0 no se recalcula: se usa la tabla de la Fase 37B y una prueba reproduce una muestra. E3 es el nivel principal de la decisión.

## 4.2. Reestimación de imputaciones (E3)

Todo ocurre en memoria. Con la submuestra y sus celdas `observada`:

- Binarias y nominal: moda, con el mismo desempate alfabético de la limpieza.
- Ordinales: mediana inferior, sin contar el nivel estructural.
- `horas_sedentarismo`: mediana, redondeada.
- IMC: las celdas sin dato siguen sin dato; la media de las observadas de la submuestra sale al recalibrar.
- **Preguntas madre** (ejercicio y cuidado): con las celdas no heredadas de la submuestra se calcula la moda. Si es «SI», las hijas heredadas pasan a «SI» y reciben la mediana de la hija; si es «NO», quedan en su nivel estructural.

El valor reestimado se aplica a todas las celdas marcadas de las 529, porque una participante nueva recibiría el valor de la cadena ajustada.

## 4.3. Qué no se recalibra, ni siquiera en E3

Limpieza, reglas de validez y deduplicación; selección de las 30 variables; agrupación de categorías raras de FAMD; códigos ordinales del instrumento; número de componentes y de clústeres. E3 no equivale a repetir toda la investigación, y los informes lo deben decir.

## 4.4. Diseño

| Aspecto | Regla | Origen |
|---|---|---|
| Remuestreos | Los mismos 30 subconjuntos de 423 de la Fase 37B (`default_rng(42)`), sin reemplazo | Previo-37B |
| K-means | `n_init=50`, `lloyd`, semilla `SeedSequence([42, r])` | Previo-37B |
| Ward | Se ajusta de nuevo en el subconjunto, sin `predict` | Previo-37B |
| Filas no usadas | Las 106 pasan por la cadena de la submuestra y se asignan al prototipo más cercano | Propuesta-37C |
| Coordenadas | No se alinean signos ni rotaciones: el ARI compara particiones de personas | Propuesta-37C |

**Medidas (ARI):**

- `ari_completo`: frente a las etiquetas de la Fase 37B, en la submuestra.
- `ari_entre`: 435 pares, sobre las participantes usadas por ambos. Es la medida principal.
- `ari_fuera`: las 106 no usadas, frente a las etiquetas de la Fase 37B. Es algo optimista, porque el modelo de la 37B sí las vio.
- `ari_fuera_pares`: en cada par, las participantes no usadas por ninguno de los dos modelos. Son unas 21 filas por par, de modo que es ruidoso, pero no tiene contaminación.

Se informan media, mediana, DE, percentiles 5, 25 y 75, mínimo y máximo, y tamaños de los grupos por repetición. **Una mediana alta no autoriza a llamar robusto a un modelo si hay repeticiones que cambian drásticamente.** Tramos de trabajo: bajo 0,65; de 0,65 a 0,80; sobre 0,80 (Previo-D13).

# 5. Referencia nula correlacionada

## 5.1. Hipótesis de esta referencia

Las variables conservan sus marginales y sus asociaciones monótonas por pares, y provienen de **una única nube continua latente, unimodal, sin grupos**. Superarla indicaría más estructura que la explicable por marginales y correlaciones. No superarla significa que la partición es compatible con un continuo correlacionado; **no prueba que no existan grupos.**

## 5.2. Alternativas evaluadas

| Alternativa | Marginales | Asociaciones | Tipos mixtos y saltos | ¿Puede introducir o conservar grupos? | Decisión |
|---|---|---|---|---|---|
| **A. Cópula gaussiana con marginales empíricas exactas** | Exactas, por asignación de rangos | Spearman por pares, calibrada iterativamente | Ordinales y binarias por rangos; IMC con indicador de ausencia; nominal condicional; madre derivada de la hija | Latente unimodal: no los crea por sí misma. La discreción puede formar acumulaciones, pero esas son parte de lo que se quiere conservar | **Elegida** |
| B. Permutación por bloques temáticos | Exactas | Exactas dentro del bloque; ninguna entre bloques | Trivial | **Sí:** conserva cualquier grupo real dentro de un bloque, como ejercicio. Prueba otra cosa | Descartada como referencia principal |
| C. Reordenamiento de Iman-Conover | Exactas | Spearman aproximado, con atenuación por empates | Igual que A | No | Equivale a A sin calibración; descartada |
| D. Factores latentes de bajo rango con umbrales | Aproximadas | Solo las explicadas por pocos factores | Exige elegir número de factores | No, pero pierde asociaciones | Descartada |
| E. Modelos condicionales secuenciales (árboles) | Aproximadas | Incluye de orden superior | Buena | **Sí:** reproduciría grupos reales, por lo que no es nula | Descartada |
| F. Normal multivariada sobre las columnas | Falla: no respeta discreción ni saltos | Covarianza exacta | Mala | Falla en el otro sentido: suaviza acumulaciones reales del cuestionario | Descartada (Encargo-37C) |

## 5.3. Construcción de A

1. Tabla de variables generales de la Fase 36 (`procedencia_celdas.csv`), como en la nula de la Fase 37B.
2. Variables latentes: las 28 no nominales con valores, más el IMC observado y un indicador de ausencia del IMC. Las hijas con madre «NO» se tratan como nivel 0.
3. Objetivo: matriz de Spearman observada sobre códigos del instrumento. La correlación IMC-otra variable usa solo las 267 observadas. IMC-indicador se fija en 0.
4. Calibración: 25 iteraciones con 40.000 filas simuladas y semilla fija, `R ← R + (S_obs − S_sim)`, proyectando a una matriz de correlación válida.
5. Cada réplica: se sortean 529 filas latentes. **Los valores observados de cada variable se asignan por rango,** de modo que la marginal es exactamente la observada.
6. `quien_prepara_comidas`: logística multinomial regularizada sobre las demás variables, ajustada una vez; las categorías se reparten sin reemplazo con el método de Gumbel para conservar sus conteos exactos.
7. Las madres se derivan de sus hijas, de modo que la lógica de salto se conserva por construcción.
8. Se aplica el `Transformador` congelado (las marginales no cambian), se recalcula la reducción y se ajustan las configuraciones.

## 5.4. Lo que conserva y lo que no

**Conserva:** marginales exactas, salto madre-hija y, de forma aproximada, Spearman por pares. **No conserva:** asociaciones no monótonas, dependencias de orden superior, incoherencias o combinaciones lógicas entre variables. Se medirán, por réplica: error frente a la matriz de Spearman, valores propios de la matriz principal, V de Cramér por pares, y combinación `dias_ejercicio_semana` = 0 con alguna frecuencia positiva.

**Criterio de validez.** La referencia solo se usa si: el error máximo de la matriz de Spearman promediada sobre las réplicas es de 0,05 o menos; los tres primeros valores propios medios difieren menos de 10 % de los observados; y pasa los controles sintéticos de 5.5. **Si no los cumple, se documenta la limitación y no se sustituye por una referencia inadecuada.**

## 5.5. Controles sintéticos (Propuesta-37C)

Con tablas de prueba del mismo esquema, generadas aquí (no es la verdad del simulador):

- **Sin grupos:** una tabla generada por la propia cópula. La silueta observada no debe superar sistemáticamente a su nula.
- **Con grupos sembrados:** una tabla con tres grupos latentes. La silueta observada debe superar a su nula.

## 5.6. Réplicas y comparación

| Aspecto | Regla |
|---|---|
| Réplicas 0 a 19 | Separación y estabilidad (E0 y E1), en el conjunto priorizado |
| Réplicas 20 a 99 | Solo separación, por su menor costo (adición, para mejorar la resolución) |
| Comparación | Media, DE, `z`, y `p = (1 + réplicas iguales o mejores) / (N + 1)` |
| Resolución | 20 réplicas: `p` ≥ 1/21 ≈ 0,048. 100 réplicas: `p` ≥ 1/101 ≈ 0,0099. **Con esto no se prueba existencia ni ausencia de clústeres** |
| Búsqueda múltiple | Mayor z del conjunto priorizado frente al mayor z de cada réplica (con media y DE de las demás), y conteo de configuraciones que superan a todas |

**Superar esta referencia no elige un modelo** (Encargo-37C).

# 6. Análisis de S-ORD

## 6.1. Descomposición (conjunto priorizado)

| Paso | Qué cambia | Se compara con la base por ARI |
|---|---|---|
| H1 | Distancias: matriz ridit sobre los ejes base, con los centroides base | Efecto de distancias sobre la regla ya ajustada |
| H2 | H1, con K-means/Ward reajustado | Distancias + fronteras |
| H3 | Matriz base sobre los ejes de la variante ridit, reajustado | Ejes |
| H4 | S-ORD completa (etiquetas de la Fase 37B) | Todo |

Además: similitud de subespacio; participantes que cambian, con grupos alineados por el método húngaro **solo para leer** la tabla de transición; tamaños; y si quienes cambian están en la frontera (margen `1 − d1/d2` en la base; AUC del margen para predecir el cambio; proporción de cambios en el cuartil de menor margen).

**Por variable** (Lista B y referencias k = 2): cada ordinal cuantitativa pasa a ridit por separado (entrada), y todas menos ella pasan a ridit (salida). Además, se mide cuánto altera cada variable las distancias entre pares de participantes.

## 6.2. Representaciones comparadas

Consecutiva (principal), ridit y puntuaciones normales (`Φ⁻¹(ridit)`, añadida aquí). Se comparan su acuerdo mutuo y su estabilidad E3. **No se usa el MRS.**

## 6.3. Regla de decisión (por configuración finalista)

- **Mantener con limitaciones aceptables:** ARI consecutiva-ridit ≥ 0,65, o entre 0,40 y 0,65 con cambios concentrados en la frontera (AUC ≥ 0,70).
- **Alternativa mejor justificada:** solo si tiene ARI `entre` E3 mayor en al menos 0,05, no empeora los percentiles 5, y es la más central en acuerdo con las otras dos. Se guardaría como versión nueva y exploratoria en 37C, sin sobrescribir la Fase 36.
- **Selección frágil:** ARI consecutiva-ridit bajo 0,40, o entre 0,40 y 0,65 sin concentración en la frontera.

La codificación principal no se cambia automáticamente.

# 7. Sensibilidades

Se reutilizan los 3.332 ajustes de la Fase 37B y sus etiquetas: no se recalculan.

| Familia | Variantes | Lectura |
|---|---|---|
| Muestra | E0 a E3 | Referencia de ruido: un cambio del orden de `ari_entre` no se atribuye a la variante |
| Codificación | S-ORD, S-FAMD, S-RARA | Perturbación metodológica |
| Población e imputación | S-TRA, S-CUI, S-EJE, S-IMPMODA | Perturbación metodológica |
| Variables | S-EDAD, S-SOLAPE | Cambia qué entra |
| IMC | Con y sin IMC | Perturbación, en las 529 y en las 267 |
| Algoritmo | K-means frente a Ward | Comparación |
| Ponderación | S-BLOQUE, S-BLOQUE-SA | **Otra pregunta: no cuenta como fallo de robustez** (Previo-37B) |

**S-IMPMODA (nueva, exploratoria):** las 30 celdas imputadas de `tiene_actividad_sexual` toman la moda de las 529 («SI»). Cadena completa con recalibración sobre las 529. Surge del hallazgo 1.2. No reemplaza nada.

Las tablas de transición alinean etiquetas solo para leerlas. No se informan coincidencias directas sin alinear.

# 8. Interpretabilidad preliminar

Solo las 30 variables generales y sin MRS. El IMC se describe con sus 267 valores observados.

**Por configuración:** descriptivos por grupo; `η²` en cuantitativas y ordinales (sobre códigos); V de Cramér en nominal; parte de la separación entre grupos (SSB en las columnas de la matriz) por variable y por bloque; número efectivo de variables y de bloques (inverso de Herfindahl).

**Reconstrucción con pocas variables (Propuesta-37C):** para cada variable y cada par de las 30 (435 pares; cuantitativas en cuartiles), se asigna a cada celda su clúster mayoritario, con validación cruzada de 5 particiones, y se calcula el ARI con la partición. No usa impureza ni entropía. Pregunta: ¿el modelo aporta algo frente a preguntar directamente una o dos cosas?

**Clasificación descriptiva, en este orden:**

| Clase | Regla |
|---|---|
| Diferencias muy pequeñas | Menos de 3 variables con `η²` o V² ≥ 0,06 |
| Principalmente gradiente de ejercicio | Bloque Actividad física ≥ 60 % de la SSB, o peso del eje 1 ≥ 0,80 |
| Dominada por pocas variables | ARI de reconstrucción con 2 variables ≥ 0,65, o una variable ≥ 40 % de la SSB |
| Segmentación multivariable | Al menos 3 bloques con una variable de `η²` o V² ≥ 0,06, y número efectivo de variables ≥ 5 |
| Difícil de interpretar | Ninguna de las anteriores |

El 0,06 es una referencia convencional de efecto moderado, no un umbral clínico. **No se asignan nombres ni interpretaciones clínicas.** La facilidad de narrar un perfil no es un criterio.

# 9. Asignación de nuevas participantes

- **K-means:** centroides guardados, por la cadena E3 de cada remuestreo. Concordancia fuera de muestra, distancia al centro, margen respecto del segundo.
- **Ward:** prototipos, comparados con las etiquetas originales. **La limitación queda explícita: no equivale al agrupamiento jerárquico original.**
- **Una participante a la vez:** se comprueba que el resultado no depende de las demás filas.

**Mecanismo de incertidumbre (propuesta provisional):** clara, frontera o alejada. Se prueba una grilla (margen bajo 0,05, 0,10, 0,15, 0,20, 0,30; distancia sobre los percentiles 90, 95, 99 del grupo) con umbrales fijados en la submuestra y evaluados en las no usadas: porcentaje señalado y desacuerdo con la Fase 37B entre señaladas y no señaladas, alineando etiquetas. **No se fijan umbrales definitivos.** Una asignación algorítmica no es una clasificación clínica.

# 10. Reglas de selección

Se aplican en este orden (Encargo-37C). Cada criterio da **OK**, **ADV** (advertencia) o **CRIT** (debilidad crítica). Los umbrales son reglas de trabajo fijadas aquí, conociendo los resultados de la sección 1.1: se informará además qué cambiaría al moverlos.

| Etapa | Criterio | ADV | CRIT |
|---|---|---|---|
| 1. Integridad | Se reproducen las etiquetas de la Fase 37B | — | No se reproducen |
| 2. Asignación | Ward: ARI de prototipos frente a sus etiquetas | < 0,80 | < 0,65 |
| 2. Asignación | E3: `ari_fuera`, media | < 0,80 | < 0,65 |
| 2. Asignación | E3: `ari_fuera`, percentil 5 | < 0,65 | < 0,50 |
| 3. Estabilidad | E3: `ari_entre`, media | < 0,80 | < 0,65 |
| 3. Estabilidad | E3: `ari_entre`, percentil 5 | < 0,65 | < 0,50 |
| 4. Codificación | S-ORD, S-FAMD, S-RARA, ARI de ajuste | < 0,65 | < 0,40 |
| 4. Población e imputación | S-TRA, S-CUI, S-EJE, S-IMPMODA | < 0,80 | < 0,65 |
| 4. Variables | S-EDAD, S-SOLAPE | < 0,65 | < 0,40 (ver regla V) |
| 5. Nula correlacionada | Silueta y `ari_entre` | No supera a todas las réplicas | — (nunca descarta) |
| 6. Tamaños | Grupo menor | Bajo 27 | — |
| 7. Separación | Silueta | Sin umbral universal; proporción de valores negativos ≥ 10 % da ADV | — |
| 8. Interpretabilidad | Clase de la sección 8 | Difícil de interpretar | — (ver resultados) |
| 9. Complejidad | Sin reducción, o 12 o más componentes | ADV | — |

Se añade margen: un valor a menos de 0,03 de un umbral CRIT se rotula «en el límite», aunque cuente según su lado.

**Regla V.** Un CRIT en S-SOLAPE o S-EDAD no es un fallo de ruido: indica que la partición descansa en esas variables, que siguen siendo elegibles (decisión D-10). Impide la conclusión A. No impide por sí solo la B, pero debe declararse como condición de uso. S-SOLAPE es especialmente delicada para la Fase 37D, porque esas variables se relacionan con síntomas.

## 10.1. Finalistas

Pasan a la comparación final las que no tienen CRIT en las etapas 1 a 3 ni en codificación ni en población e imputación. Las casi idénticas (ARI ≥ 0,95 entre ellas) se tratan como una sola partición; se representa por la de menos ADV, luego la sin IMC (la mitad de ese dato falta), luego la de menos componentes. Se muestran hasta 6, una por método × k, y la lista completa queda en una tabla.

**Si ninguna pasa,** las menos débiles se muestran aparte, rotuladas como no finalistas. Las referencias k = 2 y Ward siempre se muestran como comparación.

## 10.2. Conclusión

| Conclusión | Requisitos |
|---|---|
| **A. Modelo respaldado** | Finalista, sin ningún CRIT, supera a la nula correlacionada en silueta y `ari_entre` con control de búsqueda múltiple, clase multivariable |
| **B. Segmentación operativa condicionada** | Finalista; clase multivariable; asignación con mecanismo de incertidumbre evaluado; regla V declarada si aplica. No necesita superar a la nula: se admite que sea un continuo |
| **C. No seleccionar** | Ninguna cumple A ni B |

Si una finalista es un gradiente de ejercicio, o se reconstruye con 1 o 2 variables, **no se elige como modelo:** preguntar directamente esas variables es más simple y transparente, y se informa como alternativa.

Si hay más de una elegible para la misma conclusión, se informan todas con su diferencia práctica: menos ADV, luego mayor percentil 5 en E3, luego menor complejidad. Lo que se elija es **provisional** hasta la Fase 37D y las posteriores. La decisión final queda en manos de la responsable del proyecto.

**Confirmatorio y exploratorio.** Nada de esta fase es confirmatorio en sentido estricto, porque el diseño conoce los datos. Se rotula «regla previa» lo derivado de Previo-D13 o Previo-37B aplicado sin cambios, y «exploratorio» todo lo demás, incluida la Lista B. Sin datos independientes, ninguna selección queda validada.

# 11. Ejecución y reproducibilidad

- Un hilo por proceso. Las semillas dependen de la configuración, el nivel y la repetición, no del orden de ejecución.
- Trabajos guardados uno a uno con la huella de este protocolo. Al reanudar se omite lo completo.
- Una ejecución parcial no se presenta como completa. Lo que falte se registra.
- `sys.dont_write_bytecode` activo, para no dejar archivos en carpetas de fases anteriores.

# 12. Criterio de cierre

Deben estar completas las evaluaciones y ejecutadas las pruebas de la Parte 12 del encargo, con controles negativos. Si una prueba crítica falla, se detiene la parte afectada y se documenta. Al terminar se detiene el trabajo: **la Fase 37D no comienza.**
