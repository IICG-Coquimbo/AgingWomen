# 1. Resumen

Se prepararon cuatro matrices de 529 filas para PCA y FAMD, sin ajustar ningún modelo. Las cifras salen de los archivos guardados en `analisis/fase36/`.

| Matriz | Ruta | Filas | Columnas | Varianza o inercia total |
|---|---|---|---|---|
| `P1_pca_con_imc.csv` | PCA con IMC | 529 | 34 | 29,5047 |
| `P2_pca_sin_imc.csv` | PCA sin IMC | 529 | 33 | 29,0000 |
| `F1_famd_con_imc.csv` | FAMD con IMC | 529 | 50 | 38,5047 |
| `F2_famd_sin_imc.csv` | FAMD sin IMC | 529 | 49 | 38,0000 |

Todas las columnas tienen media cero en las 529. **La validación matemática de FAMD fue satisfactoria: 32 de 32 comprobaciones cumplen**, por lo que F1 y F2 pueden llamarse FAMD, con la precisión de la sección 6 sobre el IMC.

# 2. Entradas

- **Valores:** `datos/limpio_usuaria/dataset_usuaria_limpio.csv`, con las 529 de `datos/analitico/dataset_fase35.csv`, en el orden de este último.
- **Niveles y roles:** `fase36_diseno/diccionario_codificacion_fase36.csv` y `matriz_decisiones_variables.csv`.
- **Procedencia:** reconstrucción en memoria desde `datos/sintetico/dataset_usuaria_sucio.csv`.
- **Identificador:** solo `participante_id`, un número sin datos personales, en `matrices/identificadores.csv`. Las matrices no lo incluyen: la fila N corresponde a la fila N de ese archivo.

# 3. Codificación

| Tipo | Regla | Ejemplo |
|---|---|---|
| Binaria | Código 0/1 | `tiene_pareja`: NO = 0, SI = 1 |
| Ordinal | Código consecutivo del instrumento | `frutas_dia`: 1 a 5 |
| Frecuencia de ejercicio | 0 y 1 → 0; 2 → 1; 3 → 2; 4 → 3; 5 → 4 | «No lo realiza» y «Nunca» = 0 |
| Cantidad de personas | Vacío con `cuida_otras_personas` = NO → 0; 1, 2, 3 | «No cuida» = 0 |
| Nominal | Indicadoras | `quien_prepara_comidas` |

El diccionario completo está en `artefactos/diccionario_codificacion_36B.csv`. **Supuesto explícito:** los códigos consecutivos suponen pasos iguales entre niveles; S-ORD lo contrasta con ridit, calculado sobre la escala del instrumento.

# 4. Por qué StandardScaler

RobustScaler no falla cuando el rango intercuartílico es cero: scikit-learn sustituye esa escala por 1. No se usa por adecuación al diseño. Aplicado a las 28 columnas numéricas con referencia en las 529, nueve conservarían su unidad original, y la varianza iría de 0,14 a 2,26. Con StandardScaler todas valen 1, y las cuantitativas quedan como FAMD las define.

# 5. Parámetros de escalado

Se calculan con `ddof = 0`. Son iguales en las rutas PCA y FAMD para las columnas que comparten.

| Columna | Media | DE | n de referencia |
|---|---|---|---|
| `edad` | 50,9773 | 7,6997 | 529 |
| `imc` | 29,2296 | 6,2636 | 267 |
| `horas_sedentarismo` | 6,2741 | 2,3867 | 529 |
| `trabaja_actualmente` | 0,5841 | 0,4929 | 529 |
| `tiene_pareja` | 0,6730 | 0,4691 | 529 |
| `tiene_actividad_sexual` | 0,4745 | 0,4993 | 529 |
| `operada_no_mas_hijos` | 0,1966 | 0,3974 | 529 |
| `usa_medicamentos_presion` | 0,1682 | 0,3741 | 529 |
| `alcohol_frecuencia` | 1,8431 | 0,8453 | 529 |
| `cantidad_personas_cuida` | 0,7826 | 0,9838 | 529 |
| `carnes_semana` | 2,8507 | 0,8859 | 529 |
| `dias_ejercicio_semana` | 1,6522 | 0,9305 | 529 |
| `distension_abdominal` | 1,9282 | 0,8490 | 529 |
| `evacuacion_intestinal` | 2,3913 | 0,7874 | 529 |
| `falta_tiempo_influye` | 2,7278 | 0,9632 | 529 |
| `frecuencia_aerobico` | 0,4858 | 1,0722 | 529 |
| `frecuencia_bajo_impacto` | 0,8336 | 1,1366 | 529 |
| `frecuencia_comida_fuera` | 1,9754 | 0,8001 | 529 |
| `frecuencia_fuerza` | 0,3762 | 0,9567 | 529 |
| `frutas_dia` | 2,1437 | 0,6257 | 529 |
| `golosinas_semana` | 2,4518 | 0,9829 | 529 |
| `jugos_gaseosas_dia` | 2,0340 | 0,8557 | 529 |
| `lacteos_dia` | 2,0586 | 0,6197 | 529 |
| `legumbres_semana` | 2,1720 | 0,5523 | 529 |
| `panes_dia` | 2,1229 | 0,6072 | 529 |
| `pescado_semana` | 1,8147 | 0,6328 | 529 |
| `platos_verduras_dia` | 2,1588 | 0,5301 | 529 |
| `tabaco_frecuencia` | 1,7958 | 1,5036 | 529 |
| `vasos_agua_dia` | 3,1853 | 1,0433 | 529 |

**Indicadoras de la ruta PCA.** Valor: `(I − p) / divisor`.

| Columna | p | Divisor |
|---|---|---|
| `quien_prepara_comidas__YO_MAYORIA` | 0,6900 | 0,6979 |
| `quien_prepara_comidas__COMPARTIDO` | 0,1626 | 0,6979 |
| `quien_prepara_comidas__OTRA_HOGAR` | 0,0926 | 0,6979 |
| `quien_prepara_comidas__COMPRO` | 0,0416 | 0,6979 |
| `quien_prepara_comidas__OTRO` | 0,0132 | 0,6979 |

Todas las proporciones de FAMD están en `artefactos/parametros_escalado.csv`.

# 6. IMC

- **Parámetros:** media 29,2296 y DE 6,2636, de las 267 observadas.
- **Imputadas:** las 262 quedan en z = 0 exacto.
- **Varianza en las 529:** 267/529 = 0,5047, igual en P1 y F1. Entre las 267 observadas, la DE es 1.
- **Sin doble estandarización:** el transformador no reescala después y la columna es idéntica en ambas rutas.

**Precisión.** F1 no es una FAMD estándar en esa columna: el método original daría varianza 1 a cada cuantitativa. F1 aplica un peso reducido deliberado, y por eso `prince`, que reestandariza, no puede reproducir F1. Se comparó en el caso estándar, y el peso reducido se validó con el criterio ponderado (sección 8). F2, sin IMC, es FAMD estándar.

# 7. Agrupaciones de categorías en FAMD

| Variable | Grupo | n | p | Máximo de la columna |
|---|---|---|---|---|
| `trabaja_actualmente` | False | 220 | 0,4159 | 0,91 |
| `trabaja_actualmente` | True | 309 | 0,5841 | 0,54 |
| `tiene_pareja` | NO | 173 | 0,3270 | 1,18 |
| `tiene_pareja` | SI | 356 | 0,6730 | 0,40 |
| `tiene_actividad_sexual` | NO | 278 | 0,5255 | 0,65 |
| `tiene_actividad_sexual` | SI | 251 | 0,4745 | 0,76 |
| `operada_no_mas_hijos` | NO | 425 | 0,8034 | 0,22 |
| `operada_no_mas_hijos` | SI | 104 | 0,1966 | 1,81 |
| `usa_medicamentos_presion` | NO | 440 | 0,8318 | 0,18 |
| `usa_medicamentos_presion` | SI | 89 | 0,1682 | 2,03 |
| `quien_prepara_comidas` | YO_MAYORIA | 365 | 0,6900 | 0,37 |
| `quien_prepara_comidas` | COMPARTIDO | 86 | 0,1626 | 2,08 |
| `quien_prepara_comidas` | OTRA_HOGAR | 49 | 0,0926 | 2,98 |
| `quien_prepara_comidas` | COMPRO + OTRO | 29 | 0,0548 | 4,04 |
| `cantidad_personas_cuida` | 0 | 278 | 0,5255 | 0,65 |
| `cantidad_personas_cuida` | 1 | 136 | 0,2571 | 1,47 |
| `cantidad_personas_cuida` | 2 | 67 | 0,1267 | 2,45 |
| `cantidad_personas_cuida` | 3 | 48 | 0,0907 | 3,02 |
| `frecuencia_aerobico` | 0 | 424 | 0,8015 | 0,22 |
| `frecuencia_aerobico` | 2 + 3 | 59 | 0,1115 | 2,66 |
| `frecuencia_aerobico` | 4 + 5 | 46 | 0,0870 | 3,10 |
| `frecuencia_bajo_impacto` | 0 | 305 | 0,5766 | 0,56 |
| `frecuencia_bajo_impacto` | 2 | 79 | 0,1493 | 2,20 |
| `frecuencia_bajo_impacto` | 3 | 89 | 0,1682 | 2,03 |
| `frecuencia_bajo_impacto` | 4 + 5 | 56 | 0,1059 | 2,75 |
| `frecuencia_fuerza` | 0 | 448 | 0,8469 | 0,17 |
| `frecuencia_fuerza` | 2 + 3 | 43 | 0,0813 | 3,22 |
| `frecuencia_fuerza` | 4 + 5 | 38 | 0,0718 | 3,46 |
| `tabaco_frecuencia` | 1 | 399 | 0,7543 | 0,28 |
| `tabaco_frecuencia` | 2 + 3 + 4 | 48 | 0,0907 | 3,02 |
| `tabaco_frecuencia` | 5 | 82 | 0,1550 | 2,15 |

Los grupos están fijados de antemano y todos superan el 5 %. En las sensibilidades de proyección se mantienen iguales; el grupo menor sigue en 5,5 % a 5,7 %.

# 8. Validación matemática de FAMD

Se usaron datos sintéticos (n = 400, semilla 42) con cuatro cuantitativas y tres categóricas de 2, 3 y 4 niveles. **No se ajustó FAMD sobre los datos del estudio.**

La referencia externa fue `prince` 0.23.1, instalada en una carpeta temporal fuera del proyecto: las dependencias no cambiaron. `prince` y la transformación propia dieron los mismos valores propios y coordenadas, con diferencias del orden de 1e-14.

| Sección | Comprobación | Obtenido | Resultado |
|---|---|---|---|
| Ponderación | Todas las columnas tienen media cero | 1.8e-16 | OK |
| Ponderación | Cada cuantitativa tiene varianza 1 | 2.2e-16 | OK |
| Ponderación | Varianza de cada indicadora = 1 − p | 5.6e-17 | OK |
| Inercia | Inercia total = cuantitativas + Σ(K − 1) | 10 | OK |
| Inercia | La suma de valores propios iguala la inercia | 10 | OK |
| Inercia | Rango = columnas − una por categórica | 10 | OK |
| Equivalencia: métrica 1/p | Valores propios iguales a la métrica 1/p | 1.3e-15 | OK |
| Equivalencia: métrica 1/p | Coordenadas iguales a la métrica 1/p (8 ejes) | 6.6e-14 | OK |
| Equivalencia: criterio de Pagès | λ = Σ r² + Σ η² en los 10 primeros ejes | 1.6e-15 | OK |
| Equivalencia: criterio de Pagès | Control negativo: con la ponderación equivocada el criterio se rompe | 3,2395 | OK |
| Equivalencia: casos límite | Solo categóricas: λ = Q × λ(MCA) | 2.0e-15 | OK |
| Equivalencia: casos límite | Solo cuantitativas: λ = correlaciones | 1.1e-15 | OK |
| Equivalencia: scikit-learn | scikit-learn: varianza × (n − 1)/n = λ | 1.7e-15 | OK |
| Equivalencia: scikit-learn | scikit-learn: mismas coordenadas (8 ejes) | 4.7e-14 | OK |
| Doble estandarización | Variable con media asignada: varianza = fracción observada | 0,5 | OK |
| Doble estandarización | Valores asignados con z = 0 exacto | 0 | OK |
| Doble estandarización | Filas con marca de ausencia | 200 | OK |
| Doble estandarización | Con peso reducido, λ = v·r² + Σ r² + Σ η² | 2.7e-15 | OK |
| Doble estandarización | Una segunda estandarización sí cambiaría el peso (se detecta) | 1 | OK |
| Doble estandarización | La inercia lleva el peso reducido, no el reescalado | 9,5 | OK |
| Categorías vacías | Categoría propia con frecuencia cero: se rechaza (evita dividir por 0) | 1 | OK |
| Categorías vacías | Nivel sin observaciones unido a un grupo: finito e igual a su grupo | 0 | OK |
| Categorías vacías | La columna vacía no se crea | 0 | OK |
| Categorías vacías | Nivel no admitido por el esquema: error | 1 | OK |
| Reproducibilidad | Calibrar dos veces da parámetros idénticos | 1 | OK |
| Reproducibilidad | El orden de las filas no cambia los parámetros | 3.6e-15 | OK |
| Nueva participante | Fila de referencia como caso nuevo = misma fila | 0 | OK |
| Nueva participante | Transformar no altera los parámetros | 1 | OK |
| Nueva participante | Proyección de un caso nuevo = coordenada original | 3.3e-14 | OK |
| Referencia externa | prince 0.23.1: 8 valores propios | 2.9e-15 | OK |
| Referencia externa | prince 0.23.1: coordenadas de filas (8 ejes) | 4.9e-14 | OK |
| Referencia externa | prince no congela proporciones al proyectar una sola fila; el transformador propio sí | 1,2796 | OK |

**Qué demuestra:**

- la ponderación de categorías y la inercia total son las de FAMD;
- la transformación coincide con cuatro derivaciones independientes y con una implementación externa;
- si la ponderación fuera incorrecta, el criterio de Pagès lo detectaría (control negativo).

**Qué no demuestra:** que los ejes del estudio sean interpretables, ni que exista estructura de clústeres. Eso corresponde a la Fase 37.

**Hallazgo.** `prince` recalcula las proporciones con los datos que recibe al proyectar: con una sola fila, el resultado cambia. La transformación propia las mantiene congeladas. Por eso `prince` no debe usarse para proyectar participantes en la Fase 40.

# 9. Valores desconocidos y participantes nuevas

| Caso | Regla |
|---|---|
| Nivel no admitido | Error, sin perfil |
| Nivel válido no observado | Se transforma normalmente, con marca si queda fuera del rango |
| Pregunta condicional no mostrada | Nivel estructural de cero, con marca |
| Pregunta madre ausente | Nivel estructural, igual que la limpieza, con marca |
| IMC ausente | z = 0, con marca |
| Otra respuesta ausente | Valor congelado, con marca y aviso. Límite pendiente (D-09) |

Los valores congelados están en `valores_desconocidos.json`. Salen solo de respuestas no imputadas: moda en binarias y nominal, mediana inferior en ordinales, y mediana en `edad` y `horas_sedentarismo`. En las preguntas condicionales se calculan entre quienes sí responden.

# 10. Artefactos

```text
analisis/fase36/
  matrices/        4 matrices, identificadores y resumen
  artefactos/      P1, P2, F1, F2: esquema, orden, codificadores, escaladores, desconocidos,
                   procedencia, entorno y huellas; además diccionario, parámetros, agrupaciones
                   y esquema para nuevas participantes
  procedencia/     celdas, resumen y contraste con auditorías
  modulos/         laboral y cuidados, sin escalar
  sensibilidades/  poblaciones, catálogo, pesos de bloques y 20 matrices preparadas
  validacion/      FAMD con datos de prueba
  pruebas/         resultados y control de mutaciones
  integridad/      archivos leídos, escrituras y manifiestos
```

Los parámetros se guardan en JSON, sin pickle, y `transformador.py` solo depende de NumPy y pandas.

# 11. Sensibilidad de ponderación por bloques

Preparada, sin aplicar a clústeres. Cada bloque recibiría la misma inercia, y la inercia global se conserva.

| Bloque | Inercia P1 | Multiplicador P1 | Inercia F1 | Multiplicador F1 |
|---|---|---|---|---|
| Identificación | 2,000 | 1,358 | 2,000 | 1,551 |
| Medidas autodeclaradas | 0,505 | 2,703 | 0,505 | 3,088 |
| Actividad física | 5,000 | 0,859 | 9,000 | 0,731 |
| Etapa reproductiva y salud ginecológica | 3,000 | 1,109 | 3,000 | 1,267 |
| Medicamentos y digestión | 3,000 | 1,109 | 3,000 | 1,267 |
| Alimentación | 13,000 | 0,533 | 15,000 | 0,566 |
| Sustancias | 2,000 | 1,358 | 3,000 | 1,267 |
| Cuidado de otras personas | 1,000 | 1,920 | 3,000 | 1,267 |

**Advertencia.** El bloque de medidas solo contiene el IMC, de modo que S-BLOQUE lo amplificaría por 2,70 o 3,09, aunque la mitad de esa columna es un valor imputado.

# 12. Catálogo de sensibilidades preparadas

Ninguna se ejecutó. Las filas de proyección quedan con media distinta de cero por diseño, y por eso la inercia en las 529 difiere de la de referencia.

| Sensibilidad | Base | Columnas | Ajuste | Proyección | Inercia en 529 |
|---|---|---|---|---|---|
| S-ORD | P1 | 34 | 529 | 0 | 29,5047 |
| S-ORD | P2 | 33 | 529 | 0 | 29,0000 |
| S-ORD | F1 | 50 | 529 | 0 | 38,5047 |
| S-ORD | F2 | 49 | 529 | 0 | 38,0000 |
| S-FAMD | F1 | 38 | 529 | 0 | 31,5047 |
| S-RARA | F1 | 58 | 529 | 0 | 46,5047 |
| S-FAMD | F2 | 37 | 529 | 0 | 31,0000 |
| S-RARA | F2 | 57 | 529 | 0 | 46,0000 |
| S-TRA | P1 | 34 | 507 | 22 | 29,5914 |
| S-TRA | P2 | 33 | 507 | 22 | 29,0954 |
| S-TRA | F1 | 50 | 507 | 22 | 38,6004 |
| S-TRA | F2 | 49 | 507 | 22 | 38,1045 |
| S-CUI | P1 | 34 | 508 | 21 | 29,4806 |
| S-CUI | P2 | 33 | 508 | 21 | 28,9911 |
| S-CUI | F1 | 50 | 508 | 21 | 38,3899 |
| S-CUI | F2 | 49 | 508 | 21 | 37,9005 |
| S-EJE | P1 | 34 | 454 | 75 | 29,2162 |
| S-EJE | P2 | 33 | 454 | 75 | 28,7063 |
| S-EJE | F1 | 50 | 454 | 75 | 37,9893 |
| S-EJE | F2 | 49 | 454 | 75 | 37,4795 |
| S-EDAD | P1 | 33 | 529 | 0 | 28,5047 |
| S-EDAD | P2 | 32 | 529 | 0 | 28,0000 |
| S-EDAD | F1 | 49 | 529 | 0 | 37,5047 |
| S-EDAD | F2 | 48 | 529 | 0 | 37,0000 |
| S-SOLAPE | P1 | 32 | 529 | 0 | 27,5047 |
| S-SOLAPE | P2 | 31 | 529 | 0 | 27,0000 |
| S-SOLAPE | F1 | 47 | 529 | 0 | 36,5047 |
| S-SOLAPE | F2 | 46 | 529 | 0 | 36,0000 |
| S-BLOQUE | P1 | 34 | 529 | 0 | 29,5047 |
| S-BLOQUE | P2 | 33 | 529 | 0 | 29,0000 |
| S-BLOQUE | F1 | 50 | 529 | 0 | 38,5047 |
| S-BLOQUE | F2 | 49 | 529 | 0 | 38,0000 |
