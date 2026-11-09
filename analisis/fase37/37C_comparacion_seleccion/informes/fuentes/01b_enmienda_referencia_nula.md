# Enmienda 1 al protocolo de la Fase 37C: referencia correlacionada

**Momento:** después de sellar el protocolo y de medir las propiedades de la referencia. **Antes** de ajustar cualquier clúster sobre datos de la referencia y antes de ver los resultados de estabilidad. El protocolo sellado no se modifica.

## Qué ocurrió

La alternativa A, construida según la sección 5.3 del protocolo, **no cumplió el criterio de validez de la sección 5.4**:

| Criterio | Límite | Resultado |
|---|---|---|
| Marginales exactas y lógica madre-hija | Exactas | Cumplido |
| Error máximo de Spearman, promedio de 20 réplicas | ≤ 0,05 | 0,034: cumplido |
| Valor propio 1, P1 y F1 | < 10 % | 2,2 % y 2,6 %: cumplido |
| **Valor propio 2, P1 y F1** | < 10 % | **11,9 % y 10,1 %: no cumplido** |
| Valor propio 3, P1 y F1 | < 10 % | 6,9 % y 7,6 %: cumplido |

Las réplicas dan valores propios mayores que los observados en los ejes 2 a 5.

## Por qué ocurre

La matriz objetivo ya es una estimación con ruido muestral. Al sortear 529 filas a partir de ella se añade ruido por segunda vez, y el ruido infla los primeros valores propios. Es un efecto conocido del muestreo de matrices de covarianza. Una referencia con ejes inflados haría más difícil superarla, de modo que sería conservadora, pero por una razón artificial.

## Cambio

Contracción lineal de la matriz latente: `R' = (1 − α) R + α I`. Reduce el exceso de varianza en los ejes sin alterar marginales ni lógica de salto.

**Regla, fijada antes de calcularla:** se prueba α en la grilla 0,025, 0,05, 0,075, 0,10, 0,125, 0,15 y 0,20, con las mismas 20 réplicas, y se elige el **menor α que cumpla todos los criterios de la sección 5.4**, en P1 y F1. La elección solo usa esas propiedades: no usa clústeres, siluetas ni estabilidad.

**Si ningún α cumple:** la referencia correlacionada se declara no válida. Se documenta la limitación, no se usa en la decisión y la etapa 5 queda como no evaluada. En ese caso, la conclusión A no sería alcanzable, porque la exige.

## Qué se conserva

La versión sin contracción queda registrada con su incumplimiento en `referencias_nulas/propiedades_alpha_0.json`. Si la contracción cumple los criterios, la versión sin contracción se evalúa también como contraste, rotulada **no válida según el criterio, solo informativa**, para mostrar cuánto cambia la conclusión.

## Carácter

Es una decisión posterior, y todo lo que dependa de ella es exploratorio.
