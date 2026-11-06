# Protocolo de la comprobación complementaria de la Fase 37C

**Carácter:** exploratorio y posterior al cierre técnico de la Fase 37C. Se redacta conociendo los resultados de 37A, 37B y 37C, por lo que no es ciego. No modifica la conclusión B, no elige un modelo definitivo y no inicia la Fase 37D. La decisión queda en manos de la responsable del proyecto.

**Datos:** las mismas 529 participantes del conjunto sintético. Nada de esto permite afirmar algo sobre mujeres reales.

**Lo único conocido al sellar sobre esta comparación:** el código y el resultado de la comprobación anterior (ARI 0,677), los perfiles por grupo de la Fase 37C y las frecuencias y los estados de imputación de las tres preguntas. No se había calculado B1 fuera de muestra, ni B2, ni ninguna medida de información por bloques.

# 1. Pregunta

¿La complejidad adicional de `P2_c12_km_k4` produce un beneficio suficientemente claro frente a tres preguntas (`trabaja_actualmente`, `tiene_pareja`, `dias_ejercicio_semana`) y frente a no segmentar?

# 2. Alternativas

**Modelo A.** `P2_c12_km_k4` tal como quedó guardado: sus etiquetas oficiales no se cambian. Fuera de muestra se usa la cadena E3 de la Fase 37C: imputación, escalado, PCA y K-means ajustados solo con la submuestra; las demás participantes se proyectan al centroide más cercano. Debe reproducir exactamente los lotes de la Fase 37C.

**Celdas.** La combinación de las tres respuestas: 2 × 2 × 5 = 20 celdas posibles. `dias_ejercicio_semana` usa los cinco códigos del instrumento (1 = 0 días, 2 = 1-2, 3 = 3-4, 4 = 5-6, 5 = todos los días). Sin puntos de corte.

**B1: reproducción del Modelo A.** Tabla de celdas: cada celda recibe el segmento del Modelo A más frecuente entre las participantes de entrenamiento de esa celda. Empates: el segmento más grande en el entrenamiento y, si persiste, el de menor número. Celda vacía: el segmento más grande en el entrenamiento. Usa las etiquetas del Modelo A como objetivo, así que **es una aproximación al modelo complejo, no una validación independiente**. Puede terminar con menos de cuatro segmentos: no se fuerza.

**B1-N: búsqueda anidada (control).** Dentro de cada entrenamiento se repite la búsqueda exhaustiva del mejor trío entre las 30 variables de la comprobación anterior, con 5 pliegues internos, y se evalúa ese trío en las no usadas. Mide cuánto del resultado de B1 se debe a haber elegido el trío con todos los datos.

**B2: segmentación con tres preguntas, sin imitar a A.** K-means con k = 4 sobre las tres columnas de la matriz P2 (puntuaciones z, calibradas solo con el entrenamiento), con los mismos parámetros de la Fase 37B (`n_init` = 50, `lloyd`, mismas semillas). No usa las etiquetas de A. **No es del todo independiente de A:** el trío se eligió antes porque reproducía a A; esta dependencia se declara en todos los informes. Para la cantidad de grupos se describen k = 2 a 8 (silueta e inercia en las tres columnas) sin elegir automáticamente.

**B2-C: cruce simple (secundario).** Pareja × trabajo × ejercicio (bajo o alto), hasta 8 segmentos. El corte de ejercicio sale de K-means con k = 2 sobre los códigos, solo con el entrenamiento, y queda registrado.

**Modelo C: sin segmentación.** Usar directamente las variables generales. Conserva toda la información individual: es la referencia de lo que se pierde al resumir.

# 3. Comparación de asignaciones en las 529

- Para B1, B2 y B2-C: cantidad de segmentos, tamaños, ARI con A, tabla de correspondencia.
- Coincidencia: B1 comparte nombres con A; B2 y B2-C se alinean con el método húngaro antes de calcular porcentajes.
- Se informa por separado B1 con **doble uso** (tabla construida y evaluada en las 529) y con validación cruzada de 5 pliegues (los mismos de la Fase 37C). Un ARI no es un porcentaje de aciertos.
- Desacuerdos frente a las fronteras de A: margen de A (1 − d1/d2) en quienes coinciden y quienes no, AUC, y desacuerdo por tramo de margen (< 0,10; 0,10 a 0,20; ≥ 0,20).

# 4. Reproducción del ARI de 0,68

Se reproduce con el código original sin cambios (`pocas_variables`). Se publica la distribución de las 4.060 combinaciones: posición del trío y distancia a las siguientes. Se declaran las fuentes de optimismo: selección del trío con todos los datos, y etiquetas de A ajustadas también con las participantes de cada pliegue de evaluación.

# 5. Evaluación fuera de muestra

Las mismas 30 submuestras de 423 de la Fase 37B y 37C (`Q.subconjuntos`), con 106 de evaluación, y la misma semilla por repetición. En cada una, todo se ajusta con el entrenamiento y se congela. Las celdas se forman con la tabla E3 de esa repetición.

- **Imitación:** ARI y coincidencia en evaluación entre cada alternativa y A de esa misma repetición (A_r); también frente a las etiquetas oficiales de A, cuyo ajuste sí incluyó a esas participantes.
- **Estabilidad:** las cuatro medidas de la Fase 37C: `completo`, `entre` (pares de repeticiones sobre participantes compartidas), `fuera` y `fuera_pares` (solo participantes que ningún par usó).
- **Tamaños y equilibrio** por repetición. **Medias, medianas, percentil 5, mínimo y máximo.**
- **Referencia de tríos al azar:** B2 con 30 tríos al azar de variables de una columna, con semilla fija, para saber si su estabilidad es mérito de estas preguntas o una propiedad de agrupar pocas respuestas discretas.

Una regla de pocas celdas tiende a ser estable por construcción: las participantes no cambian de celda. Esa estabilidad **no es evidencia de grupos reales**, y una imitación exacta de una partición frágil no sería una mejora.

# 6. Información adicional (análisis principal)

**Bloques**, con las 29 variables de P2 repartidas sin solapamiento:

| Bloque | Variables | Uso |
|---|---|---|
| Las tres preguntas | `trabaja_actualmente`, `tiene_pareja`, `dias_ejercicio_semana` | Definen B; circularidad evidente |
| Alimentación | las 13 de esa sección, incluida `quien_prepara_comidas` | Lectura principal |
| Actividad física adicional | `frecuencia_aerobico`, `frecuencia_bajo_impacto`, `frecuencia_fuerza` | Lectura principal |
| Sedentarismo | `horas_sedentarismo` | Lectura principal |
| Cuidados | `cantidad_personas_cuida` | Lectura principal |
| Tabaco y alcohol | `tabaco_frecuencia`, `alcohol_frecuencia` | Lectura principal |
| Otras generales | `edad`, `operada_no_mas_hijos`, `usa_medicamentos_presion` | Lectura principal |
| Actividad sexual | `tiene_actividad_sexual` | Solo descriptiva |
| Digestión | `distension_abdominal`, `evacuacion_intestinal` | Solo descriptiva: respuestas cercanas a síntomas, no son criterio |

También se describe el IMC observado (n = 267), que ninguna alternativa usa en P2. El MRS no se lee en ningún paso.

**Precaución de circularidad.** A usa casi todas estas variables, de modo que diferenciará sus propios grupos en ellas. B no las usa. Comparar efectos crudos favorecería a A sin demostrar nada. Por eso:

1. **Descripción (529, circular para A):** η² o V² y diferencia máxima entre segmentos en desviaciones estándar, para A, B1, B2, B2-C y celdas.
2. **A sin el bloque (A−X), medida principal:** por cada bloque se quitan sus columnas de la matriz, se rehace PCA (12 componentes) y K-means con k = 4 en la misma repetición y se evalúa en ese bloque. Así el modelo complejo no ve la variable que debe describir, igual que B.
3. **Información incremental:** R² fuera de muestra al predecir cada variable con celdas, frente a celdas más los segmentos de A−X (regresión con indicadores, ajustada en entrenamiento). Las variables nominales se tratan como indicadores. **ΔR² es la respuesta directa a qué añade A más allá de las tres preguntas.** También se calcula con A completo, rotulado como circular.
4. Solo cuentan celdas realmente observadas de la variable descrita, sin imputadas ni heredadas de una pregunta previa imputada. La media de referencia sale del entrenamiento.
5. **Dominio del trío:** parte de la suma de cuadrados entre grupos de A (SSB) que cae en las tres preguntas y en las variables de ejercicio, y parte de la varianza multivariable de P2 que retiene cada partición.

**Bandas de lectura, solo descriptivas:** ΔR² < 0,01 despreciable; 0,01 a 0,06 pequeña; ≥ 0,06 moderada. El percentil 5 entre repeticiones no es un intervalo de confianza, porque las submuestras se solapan. No se usan valores p para decidir.

**Variantes de A:** se repite la medida con 8 y 16 componentes, solo para responder si 12 componentes se justifican.

# 7. Complejidad, codificación y sensibilidades

Se comparan preguntas necesarias, pasos, parámetros y forma de asignar. Las sensibilidades de A se leen de la Fase 37C sin recalcular:

- **B1:** se reconstruye la tabla con el objetivo de cada variante sellada de A (S-ORD, S-SOLAPE, S-EDAD, S-BLOQUE, S-TRA, S-CUI, S-EJE, S-IMPMODA) y se compara con B1 base.
- **B2:** días codificado como ridit y como puntuación normal; peso de ejercicio ×0,5 y ×2; ajuste sin imputadas en cada pregunta y sin imputadas en ninguna de las tres, proyectando las demás. S-SOLAPE, S-EDAD y S-IMPMODA no le afectan por construcción: se comprueba y se rotula así, sin presentarlo como un logro.
- **Incertidumbre:** margen en A y B2; pureza de celda en B1. Sin umbrales definitivos.

# 8. Sin segmentación

Parte de la información de cada bloque que queda fuera de cada partición (1 − R²), correlación media entre bloques y qué se gana o se pierde al usar grupos. No se desarrollan recomendaciones ni se usan resultados clínicos.

# 9. Imputación

Se mantiene documentado `tiene_actividad_sexual`: 251 «SI» y 248 «NO» observados; 30 imputadas como «NO» desde la moda calculada en 546 filas. No se modifica la limpieza ni la Fase 36. No se afirma que la moda de 529 sea más correcta. Se explica cómo afecta a cada alternativa, y se cuenta cuántas participantes tienen alguna de las tres preguntas imputada, y si B1 y B2 discrepan más de A entre ellas.

# 10. Guía de lectura, fijada antes de ver los resultados

No hay puntuación compuesta ni elección automática. Orienta la recomendación, que no es vinculante:

- **A favorece a la opción A** si, en al menos un bloque de lectura principal, A−X añade a las celdas un ΔR² medio ≥ 0,06, o si lo hace ≥ 0,01 en al menos tres bloques, con percentil 5 mayor que 0 en ambos casos, y su estabilidad no es claramente inferior.
- **A favorece a la opción B** si el aporte de A queda en despreciable o pequeño sin cumplir lo anterior, y además B1 o B2 son al menos tan estables como A y conservan parte reconocible de las diferencias.
- **A favorece a la opción C** si las particiones retienen muy poca información de los bloques que no las definen y las tres preguntas como tales dicen lo mismo que los segmentos. C también es razonable si, cumpliéndose B, no hay un uso concreto que exija asignar segmentos.

Si la evidencia queda entre dos opciones, se informa así. Los datos sintéticos no permiten evaluar utilidad clínica: esa parte de la decisión no se resuelve aquí.

# 11. Pruebas e integridad

Conservación e identificadores de las 529, reproducción exacta de las etiquetas de A y de los lotes de 37C, reproducción del 0,677, separación entre entrenamiento y evaluación, ausencia de fuga, reproducibilidad, alineación, ARI, estabilidad con participantes compartidas, variables limitadas a las autorizadas, ausencia de MRS, archivos protegidos (incluida la Fase 37C), Django, commits y push. Cada prueba crítica tiene un control negativo que introduce un error y exige que se detecte.

# 12. Límites

Máximo 2 procesos por la memoria disponible, con vigilancia y reanudación. Sin commit, sin push, sin reglas de asociación, sin caracterización clínica, sin verdad del simulador y sin Fase 37D. Toda salida queda en `analisis/fase37/37C_complemento_tres_preguntas/`.
