# Fase 36A: decisiones pendientes de revisión

Cada punto trae una recomendación. Nada se implementa hasta que el protocolo se apruebe.

## Decisiones que conviene revisar primero

| ID | Decisión | Recomendación | Alternativa | Por qué importa |
|---|---|---|---|---|
| D-01 | Representación de ordinales en PCA | Códigos consecutivos, con ridit como sensibilidad | Ridit como principal | Afecta a 21 de 30 variables. La equidistancia es un supuesto |
| D-03 | Rol de las ordinales en FAMD | 16 cuantitativas y 5 categóricas, por quiebre estructural o bimodalidad | Todas cuantitativas o todas categóricas | Es lo que más distingue FAMD de PCA |
| D-05 | Parámetros del IMC | Media y DE de las 267 observadas | Las 529 (DE 4,45) | Define si el IMC pesa 0,505 o 1 en la distancia |
| D-07 | Peso de los bloques | Sin ponderar; contraste en S-BLOQUE | Peso igual por bloque | Alimentación tiene 13 de 30 variables y puede orientar los perfiles |
| D-08 | Procedencia por celda | Reconstruir en memoria los pasos 8 y 9, sin la verdad del simulador | Solo marcas existentes, en 15 de 30 variables | Sin esto, S-TRA, S-CUI y S-EJE no se pueden hacer con exactitud |

## Decisiones técnicas

| ID | Decisión | Recomendación | Alternativa |
|---|---|---|---|
| D-02 | Frecuencias de ejercicio | Escala consecutiva 0 a 4; «Nunca» (no observado) se une a «No lo realiza» | Conservar el salto de los códigos 0, 2, 3, 4, 5 |
| D-04 | Umbral de agrupación en FAMD | 5 %, solo en FAMD, con S-RARA | Sin agrupar |
| D-06 | Nominal en PCA | Indicadoras centradas con varianza total 1; sin agrupar | Indicadoras estandarizadas: OTRO quedaría en z = 8,6 |
| D-09 | Respuestas ausentes en la Fase 40 | Valor congelado con marca y aviso; fijar un límite | Exigir todas las respuestas |
| D-10 | `tiene_actividad_sexual` y `distension_abdominal` | Mantenerlas, porque están en la lista vigente, y contrastar con S-SOLAPE | Retirarlas |
| D-11 | Referencia sin reducción | Matriz euclidiana (R0) con K-means y Ward; Gower con enlace promedio como adicional | Solo R0 |
| D-12 | Implementación de FAMD | Transformación propia y PCA de scikit-learn | Instalar `prince` |

## Por fijar antes de ejecutar la Fase 37

| ID | Decisión | Recomendación |
|---|---|---|
| D-13 | Reglas de decisión | Fijar antes de ver resultados: rango de clústeres, número de componentes, tamaño mínimo, medida de estabilidad y qué cambio de una sensibilidad se considera relevante |
| D-14 | Edad | Base con edad y comparación sin ella, como anunció 35A |

## Por fijar antes de las Fases 38 y 39

| ID | Decisión | Recomendación |
|---|---|---|
| D-15 | Ítems de los módulos en las reglas | Agrupar según el sentido de la escala (por ejemplo, 1-2, 3 y 4-5), solo con respuestas aplicables y con el denominador del módulo |

## Contradicciones y hallazgos del diseño

| Tema | Hallazgo | Consecuencia | Tratamiento |
|---|---|---|---|
| Código «Nunca» | El instrumento lo admite en las frecuencias de ejercicio, pero ninguna participante lo tiene; el diccionario 35 lista 0 y 1 como niveles distintos | Los códigos dejan un salto artificial | D-02 |
| Diccionario 35 | El 0 de las frecuencias dice «no realiza / no cuida» de forma genérica. La sobrecarga no aparece | No basta para codificar | El nuevo diccionario separa cada caso |
| Ceros de ejercicio | 29, 22 y 28 ceros dependen de una imputación. No estaba en el encargo | Igual riesgo que en cuidados | Nueva sensibilidad S-EJE |
| Marcas | Solo 15 de 30 generales tienen marca `_imputado` | No alcanzan para la trazabilidad por celda | D-08 |
| Niveles no observados | 13 niveles válidos no se observan, como `frutas_dia = 5` | Una usuaria nueva puede tenerlos | Los mapas salen del instrumento, no de los datos |
| Edad | La referencia va de 36 a 65; la plataforma admite 40 a 65, y bajo 40 con excepción | No es contradicción; bajo 36 habría extrapolación | Aviso en la Fase 40 |
| Nota de memoria | Una nota de trabajo decía 40-60; el formulario vigente dice 40-65 (cambio del 2026-10-01) | Se corrigió la nota | Sin efecto en el análisis |

## Límite de esta etapa

La Fase 36A no ajustó escaladores ni modelos, no creó matrices y no ejecutó sensibilidades. Los descriptivos por columna solo justifican el diseño.
