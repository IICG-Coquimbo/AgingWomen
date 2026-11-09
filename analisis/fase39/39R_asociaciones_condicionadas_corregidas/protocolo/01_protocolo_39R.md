# Protocolo de la Fase 39R: asociaciones condicionadas, versión correctiva

Se redacta y se sella con SHA-256 **antes de buscar ninguna regla**. No se modifica después del sello. Cualquier ajuste posterior irá en `protocolo/02_modificaciones_posteriores.md`, rotulado como exploratorio.

## 1. Objeto y carácter

La Fase 39 heredó de la Fase 38 las variables `prevision` y `usa_medicamentos_diabetes`, excluidas del modelado por decisiones definitivas de las Fases 35 y 36. La Fase 39R repite el análisis sin ellas, desde la matriz validada de la Fase 38R, y determina si cambian las asociaciones condicionadas por trabajo, pareja, ejercicio y cuidado.

**La Fase 39 original se conserva intacta como evidencia histórica.** Esta fase no incluye cambios en las Fases 38, 38R o 39, en la Fase 40, en el conjunto limpio ni en la tesis, y no incluye commits ni pushes.

**Información conocida antes de sellar.** El análisis no es ciego: se conocen los resultados de la Fase 39 histórica (resultado C, ninguna regla ni comparación supera su nula) y los de la Fase 38R. Sellar evita ajustar criterios a los resultados de esta fase, pero no convierte el análisis en confirmatorio. Sigue siendo exploratorio y sobre 529 participantes **sintéticas**, sin interpretación causal ni clínica.

## 2. Procedimiento heredado

Rige sin cambios el protocolo histórico `fase39/39_asociaciones_condicionadas/protocolo/01_protocolo_39.md` (sello `18f15f821635f8c3d55a31f539d84d95ef8e5a32591e465073fb181a424c9042`), secciones 1, 3, 5 a 13, salvo lo indicado en la sección 3 de este documento. Las funciones `busqueda_39.py` y `heterogeneidad_39.py`, y `H39.construir`, `H39.mascaras` y `H39.umbrales` de `nucleo_39.py`, se **importan sin modificar**, igual que las de la Fase 38.

Se conservan en particular:

- Cuatro dimensiones y nueve estratos: trabaja 309 / no trabaja 220; pareja 356 / sin pareja 173; 0 días 302 / 1-2 días 148 / 3 o más 79; cuida 251 / no cuida 278. Mismos códigos y criterios de pertenencia.
- Dentro de cada estrato: se excluye su variable, se retiran ítems constantes o vacíos, se excluyen antecedentes determinados, frecuencia basal propia.
- Umbrales: `n_A ≥ max(20, ⌈0,10·n⌉)`, `n_AC ≥ max(10, ⌈0,05·n⌉)`; largo 3 si n ≥ 250, 2 si 120 ≤ n < 250, 1 si 60 ≤ n < 120.
- Marcada 0,10; mejora mínima 0,05; estabilidad 70 % y 95 %; composición 0,20; alfa 0,05.
- Comparación entre estratos: DR, Newcombe, Q, Δ y z con dos estratos, MOVER, comparabilidad ≥ 20 en cada lado, antecedentes de 1 y 2 condiciones, todos los comparables.
- Referencias nulas: 1.000 permutaciones dentro de cada estrato. **Semillas históricas sin cambio**: `[42, 39, k]` por estrato, `[42, 39, 100 + d]` por dimensión, `[42, 39, 2, k]` y `[42, 39, 3, d]` en estabilidad, `[42, 39, 1000 + 20·i + k]` y `[42, 39, 2000 + 10·i + d]` en sensibilidades, `[42, 39, 200 + 10·g + k]`, `[42, 39, 110 + g]` y `[42, 39, 3, 10 + g]` en A y B1.
- Ajustes: Westfall-Young por estrato, conjunto de 9 estratos, por dimensión y conjunto de 4 dimensiones; Benjamini-Hochberg sobre todas las filas.
- 200 submuestras del 80 % y sus criterios.
- Clases 1 a 5 y H0 a H5; resultados A, B y C según la sección 13 histórica.

**Ningún valor p ajustado, máximo nulo ni clasificación histórica se reutiliza.** Las permutaciones usan las mismas semillas, pero las referencias se recalculan por completo sobre las nuevas búsquedas.

## 3. Cambios respecto de la Fase 39 (estrictamente los necesarios)

| Código | Fase 39 | Fase 39R | Motivo |
|---|---|---|---|
| D-1 | 31 variables, 94 ítems | **29 variables, 90 ítems** | Decisiones de las Fases 35 y 36 |
| D-2 | `N39.base_items`, con `N38.PRINCIPAL` y `N38.construir` | `nucleo_39r.base_items`, con `R38.PRINCIPAL` y `R38.construir` | Ausencia desde la construcción de las transacciones |
| D-3 | Verificación contra la matriz de 94 ítems de la Fase 38 | Verificación contra la matriz de 90 ítems de la 38R, y contra la histórica menos las retiradas en cada configuración | Trazabilidad |
| D-4 | Sin barreras por estrato | `barreras_39r.py` detiene el proceso ante cualquier incumplimiento | Control |
| D-5 | Control de integridad ligado a HEAD `745d689` | `integridad_39r.py`, independiente de HEAD | Incompatibilidad documentada en la sección 7 |

Las transformaciones, las agrupaciones (fijadas con las 529 y sin el MRS) y las etiquetas no cambian. La sección 2 histórica se lee con 29 variables en lugar de 31, y la sección 4 con 90 ítems en lugar de 94.

**Exclusiones definitivas** en todas las configuraciones, estratos, sensibilidades y comparaciones A y B1: `prevision`, `usa_medicamentos_diabetes`, `doble_carga`. No pueden reincorporarse por sus categorías ni transformaciones.

**Dependencias revisadas.** `etapa_a_preparacion.py` recorre los scripts históricos en busca de `N38.PRINCIPAL`, `N38.construir`, `N38.esquema`, `N38.matriz_items`, `N38.cargar`, `matriz_transaccional_principal` y `base_items`, y deja cada aparición con su destino en `preparacion/auditoria_dependencias.csv`. Una aparición en un archivo no revisado detiene el proceso.

## 4. Modificaciones históricas posteriores al sello

El registro `02_modificaciones_posteriores.md` de la Fase 39 no forma parte de su protocolo sellado. Se evalúa punto por punto:

| Punto | Naturaleza | Decisión en la 39R |
|---|---|---|
| 1. Corrección previa al sellado | Ya integrada en el texto sellado | Nada que hacer |
| 2. Lectura estricta de S9 | Cambia, en el código, una condición de la sección 13: exige «se mantiene» donde el texto sellado dice «mantenerse en S9 o ser evaluable allí» | **Rige el texto sellado.** La lectura estricta se calcula aparte y se informa. Si los dos dan un resultado distinto, se declara como incidencia y queda a decisión de la responsable. Solo afecta a comparaciones H5 de ejercicio |
| 3. Tabla de significación nominal | Exploratoria | Se reproduce en `exploratorio_posterior_al_sello/`, rotulada; no interviene en ninguna clase ni en la conclusión |
| 4. Tolerancia numérica en la prueba de reproducibilidad | Técnica de la prueba | Se adopta, declarada |
| 5. Ajustes de leyendas en figuras | Presentación | No aplica: esta fase no genera figuras |

## 5. Sensibilidades

Las once de la sección 11 histórica, con su propia referencia nula de 1.000 permutaciones y el orden histórico de semillas: S1, S2a, S3-bajo, S3-alto, S4-1, S4-2, S5, S6, S7a, S7b, S9.

**No son las configuraciones homónimas de la 38R.** Diferencias en esta fase:

- **S7a:** se agregan a las 529 los ítems `lugar_trabajo_comprensivo` y `estres_entorno_laboral`, y solo se analiza dentro del estrato **trabaja, con 309 participantes**. Entre ellas, 22 tienen el trabajo imputado y no tienen ítems laborales (tratamiento histórico). Equivale en población a la S7a-309 de la 38R. **S7a con 263 no se ejecuta.**
- **S7b:** se agrega `sobrecarga_fisica_emocional` y solo se analiza dentro del estrato **cuida, con 251 participantes**, 12 de ellas con sobrecarga imputada. Equivale en población a la S7b-251 de la 38R.
- S7a, S7b y S4-2 no tienen comparación propia entre estratos, como en el protocolo histórico.
- S9 solo compara ejercicio entre 0 y 1-2 días.
- No existen S2b ni S8 en esta fase.

Si alguna configuración no puede reproducirse con su definición, se documenta antes de modificarla.

## 6. Comparaciones A y B1

Exploratorias. Etiquetas históricas sin reajustar (`P2_c12_km_k4` y `B1_doble_uso`), sin calcular PCA, K-means ni FAMD. Sin `trabaja_actualmente`, `tiene_pareja` ni `dias_ejercicio_semana`. Las etiquetas no son antecedentes ni perfiles clínicos.

## 7. Integridad

Los controles históricos `integridad_39.py` y las pruebas p18 y p19 exigen HEAD `745d689` y `src/` sin cambios, por lo que ya no pueden cumplirse. **No se desactivan ni se modifican.** Se usa `scripts/integridad_39r.py`, además de `test_40b1_proteccion_historica.py`. La medición inicial se hizo antes de crear ningún otro archivo de la fase.

Deben permanecer sin cambios: Fases 34 a 39 y 38R (carpetas, manifiestos y sellos), conjunto limpio, `src/` y los 134 archivos pendientes de la Fase 40, respaldados en `datos/respaldos/2026-11-08_antes_38R/`. Toda escritura va a la carpeta nueva de la 39R.

## 8. Barreras

`barreras_39r.py` y las barreras reutilizadas de la 38R detienen el proceso, sin corregir nada, si:

1. Las 29 variables no coinciden con las autorizadas, leídas de las Fases 35 y 36.
2. Aparece una variable excluida, por nombre, forma transformada o contenido (vector igual o complementario a una de sus categorías en las 529).
3. Un antecedente pertenece al MRS, es posterior a los síntomas o es una etiqueta de segmentación.
4. La matriz principal no es idéntica a la matriz de 90 ítems de la 38R.
5. Un estrato no tiene su tamaño, severas o umbrales; conserva su propia variable o ítems constantes.
6. Los módulos de S7a y S7b entran fuera de su estrato o con otra población.
7. Una tabla de reglas o de comparaciones contiene una variable no autorizada.

## 9. Etapas

A: preparación. B y C: reglas y referencias nulas (la búsqueda y su nula comparten los antecedentes). D: comparaciones entre estratos. E: sensibilidades, A y B1. F: pruebas, controles negativos, reproducibilidad e integridad. La fase no se declara completa con errores críticos o controles sin resolver.

**Modo de humo.** Antes del sello, el código se ejecutó en una carpeta temporal con la severidad permutada y pocas permutaciones, solo para comprobar que corre. Esa salida no se conserva, no se revisa como resultado y no forma parte del análisis. Las ejecuciones reales registran `modo_humo: false`.

## 10. Conclusión

Se decide de forma mecánica después de todas las comprobaciones, con las condiciones de la sección 13 histórica:

- **A:** al menos una diferencia consistente: H5, p ajustado conjunto de 4 dimensiones < 0,05, se mantiene en S1, S2a, S3-bajo, S3-alto y S6 cuando es evaluable y es evaluable al menos en 3, y en ejercicio cumple la condición de S9.
- **B:** ninguna diferencia consistente y al menos una regla de clase 5 que supera la nula conjunta de los 9 estratos.
- **C:** ninguna de las anteriores.

Los tres resultados son válidos y ninguno es preferido. Una regla significativa en un estrato y no en otro no se interpreta como interacción. Cualquier hallazgo queda en el alcance exploratorio de datos sintéticos: sin causalidad, validación clínica ni recomendaciones.
