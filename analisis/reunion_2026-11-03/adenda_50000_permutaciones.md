# Adenda: ejecución complementaria de 50.000 permutaciones

*Registrada el 03-11-2026, después de conocer los resultados de 10.000 y antes de calcular los de 50.000, con autorización expresa de la usuaria. Complementa a `protocolo_revision_35b.md`, que no se modifica.*

## 1. Dos versiones de la misma revisión

| Versión | Permutaciones | Función | Carpeta |
|---|---:|---|---|
| A | 10.000 | Análisis entrópico principal | `permutaciones_10000/` |
| B | 50.000 | Análisis complementario: evalúa precisión y consistencia de A | `permutaciones_50000/` |

**La única diferencia es el número de permutaciones.** Se mantienen las 34 variables, la codificación, las poblaciones (529, 287 y 239), la entropía de Shannon en base 2, Benjamini-Hochberg sobre 34 pruebas, q < 0,10, las reglas de FCBF y las de dirección. B no reemplaza a A.

La Fase 35B busca identificar asociaciones. **Ninguna variable se elimina:** las 34 quedan como conjunto inicial de la Fase 36.

## 2. Extensión reproducible

Se usan las mismas claves `SeedSequence(42, spawn_key=(1103, 0, tipo, índice))`, sin cambios por los resultados. Como `prueba_permutacion` baraja en lotes de 1.000, **las primeras 10.000 permutaciones de B son exactamente las de A**. B agrega 40.000 nuevas.

## 3. Comprobaciones antes de aceptar B

Si falla alguna, no se escribe ningún resultado:

1. **Código de A intacto:** el SHA-256 del programa, del protocolo y de las pruebas coincide con el registro de A.
2. **A se reproduce:** recalculada ahora, cada tabla de A coincide byte a byte con su archivo guardado.
3. **Anidamiento:** en cada variable y cada par, k₁₀ₖ de los primeros 10.000 sorteos es igual al guardado en A si existe, y k₁₀ₖ + k₄₀ₖ, continuando el mismo generador, es igual al k₅₀ₖ de B.
4. **SU:** es idéntica en A y B.
5. **Dos corridas de B:** son idénticas.
6. **Archivos vigilados:** A, los resultados históricos, los conjuntos de datos, el código anterior y los Word no cambian.

## 4. Comparación fijada de antemano

**Consistencia de cada valor p.** Los primeros 10.000 sorteos y los 40.000 siguientes son independientes y estiman el mismo p exacto, de modo que se compara:

z = (k₁₀ₖ/10.000 − k₄₀ₖ/40.000) / √[p̂(1 − p̂)(1/10.000 + 1/40.000)], con p̂ = (k₁₀ₖ + k₄₀ₖ + 1) / 50.001.

Una diferencia es **compatible con la precisión de Monte Carlo** si |z| ≤ 3,19, valor bilateral con corrección de Bonferroni: 0,05 / 34. Si |z| > 3,19 se investiga otra causa técnica antes de interpretar.

**Descomposición de la diferencia de q.** En BH, q depende también de los demás valores p. Para cada variable:

- **Efecto propio:** q con solo su p cambiado a 50.000, menos q₁₀ₖ.
- **Efecto del resto:** q₅₀ₖ menos ese valor.

**Cambio de clasificación.** Solo cuenta cruzar q = 0,10 con comparación estricta. Una diferencia de q sin cruce no se interpreta como cambio en la relación con la severidad. La SU, que es la medida de asociación, es la misma en ambas versiones.

**Incertidumbre de B.** Se aplica el método de la sección 7 del protocolo con N = 50.000, con clave `(1103, 0, 4, 2)` para los sorteos. Una variable cercana a 0,10 se informa como tal: la regla de la versión A no autoriza por sí sola más permutaciones.

## 5. Dirección

Spearman, Kruskal-Wallis y las comparaciones por categoría no dependen de las permutaciones y usan las mismas claves, de modo que deben coincidir exactamente con A. Solo la clase descriptiva puede cambiar, porque usa el q de SU. Las clases son las de la sección 6 del protocolo.

## 6. Salidas

- `permutaciones_50000/`: las mismas tablas de A con N = 50.000, informe y registro.
- `informe_integrado/`: informe académico, comparación de las 34 variables, resultados históricos identificados como versiones previas y figuras.

Los resultados históricos (E1, E3, E4, C3, C4) se leen sin alterarlos: son **versiones previas con otra composición de variables**, y sus q no se reutilizan.

No se regeneran conjuntos de datos, no se modifican fases anteriores, no se ejecuta Random Forest, no se avanza a la Fase 36, no se hace commit ni push, y no se actualizan los Word anteriores.
