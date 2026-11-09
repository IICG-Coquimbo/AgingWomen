# 1. Propósito

Deja lista la información metodológica para la Fase 37B. **Este documento no la inicia.** Las reglas están en la sección 8 del protocolo D-13.

# 2. Entradas disponibles

| Entrada | Ubicación | Uso |
|---|---|---|
| Coordenadas principales | `coordenadas/<escenario>/coordenadas_kNN.csv` | Entrada de los algoritmos |
| Modelos | `artefactos/<escenario>/modelo.json` | Asignar participantes nuevas |
| Coordenadas de sensibilidades | `sensibilidades/<variante>/<escenario>/` | Comparar asignaciones |
| Matrices P1 y P2 | `analisis/fase36/matrices/` | Referencia sin reducción (R0) |

**Las coordenadas no se deben estandarizar:** dividirlas por su DE daría a los ejes tardíos, de poca varianza, el mismo peso que al primero, y cambiaría lo definido en este protocolo.

# 3. Tamaño del análisis

Según el protocolo: 4 escenarios × 7 candidatos × 2 algoritmos × 7 valores de k = **392 configuraciones**, más 28 de la referencia R0 (420 en total), cada una con 30 remuestreos y una referencia nula de 20 permutaciones.

**Advertencia:** con tantas configuraciones, alguna destacará por azar. Por eso, el protocolo no admite un ganador automático y exige comparar con la referencia nula.

# 4. Recomendaciones

- **Revisar la estabilidad antes que la calidad,** como fija el protocolo. La estructura débil hace probable que las métricas sean bajas en general.
- **Mirar con atención los candidatos pequeños (k = 2, 3, 5, 8).** Son los que superan la referencia de ruido. Desde k = 12 se añaden ejes por debajo de ella en todos los escenarios, y son los más expuestos a variar. Los candidatos no se eliminan; es solo una expectativa que hay que comprobar.
- **Cuidar que el resultado no sea solo la actividad física.** Con k = 2 o 3, el eje 1 pesa mucho. Agrupar ahí podría limitarse a separar por nivel de ejercicio. Debe informarse así si ocurre.
- **Cuidar la dependencia de `tiene_actividad_sexual`.** Con pocos ejes, S-SOLAPE es de las variantes que más cambian la representación. Conviene revisar sus asignaciones con ARI.
- **Con y sin IMC serán casi iguales.** Un ARI alto entre ellas es esperable y no prueba estabilidad. Sigue haciendo falta la revisión de IMC imputado por grupo, como fija el protocolo.
- **Leer S-BLOQUE como otra ponderación,** no como una prueba de robustez. Sus cambios no deben contar en contra de una configuración del mismo modo que S-ORD o S-TRA.
- **Aceptar la posibilidad de que no haya perfiles marcados.** Si ninguna configuración es estable y supera la referencia nula, el protocolo pide informarlo y no forzar perfiles. Con estos datos es un resultado posible y sería válido.

# 5. Variantes señaladas para revisar

| Variante | Escenarios y candidatos bajo 0,80 |
|---|---|
| S-FAMD | F1: k=5 (0,796); F2: k=5 (0,798), k=12 (0,800) |
| S-RARA | F1: k=5 (0,743), k=8 (0,768), k=12 (0,785); F2: k=5 (0,744), k=8 (0,768), k=12 (0,786) |
| S-EJE | F1: k=5 (0,764); F2: k=5 (0,766) |
| S-SOLAPE | P1: k=5 (0,793); P2: k=5 (0,792); F1: k=5 (0,789); F2: k=5 (0,789) |
| S-BLOQUE | P1: k=5 (0,368), k=8 (0,565), k=12 (0,592); P2: k=5 (0,521), k=8 (0,596), k=12 (0,628); F1: k=5 (0,427), k=8 (0,454), k=12 (0,536); F2: k=5 (0,463), k=8 (0,475), k=12 (0,547) |
| S-BLOQUE-SA | P1: k=5 (0,521), k=8 (0,597), k=12 (0,629); F1: k=5 (0,463), k=8 (0,475), k=12 (0,547) |

# 6. Asuntos por decidir antes de comenzar

Estas propuestas quedaron en el protocolo y puedes cambiarlas:

- Número de inicializaciones: `n_init = 50`.
- Remuestreo sin reemplazo.
- Tramos de ARI: bajo 0,65, de 0,65 a 0,80, y sobre 0,80.
- Referencia nula de 20 permutaciones.
- Orden de decisión sin puntuación compuesta.
