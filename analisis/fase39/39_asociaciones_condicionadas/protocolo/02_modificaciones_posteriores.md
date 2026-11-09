# Fase 39: modificaciones y precisiones posteriores al sellado

El protocolo `01_protocolo_39.md` (sha256 `18f15f821635f8c3d55a31f539d84d95ef8e5a32591e465073fb181a424c9042`, sellado el 2026-11-05 a las 19:30:04) no se modificó. Esta nota registra lo que se hizo de otra forma, o se precisó, después del sellado.

## 1. Corrección previa al sellado (no es una modificación)

Antes de sellar comprobé una afirmación del borrador: «en 0 días, las frecuencias de ejercicio son "no realiza" por diseño». Era falsa. Las frecuencias no son estructurales; por ejemplo, 285 de 302 participantes responden «no realiza» en aeróbico, pero no todas. Corregí el texto antes de sellar. El protocolo sellado ya dice lo correcto.

## 2. Precisión de la regla S9 (interpretación, sin cambio de resultados)

La sección 13 exige, para la dimensión ejercicio, que una diferencia consistente «se mantenga en S9 o sea evaluable allí». El código aplica la lectura estricta: la diferencia debe quedar «se mantiene» en S9.

Esto no cambia nada: ninguna comparación llegó a la clase H5, así que la condición nunca se evaluó.

## 3. Tabla exploratoria de significación nominal (agregada)

La tabla «diferencias de significación» de la sección 8 está vacía, porque ninguna regla superó la nula de su estrato. Para ilustrar el riesgo que el protocolo describe, agregué `scripts/significacion_39.py`. Para cada antecedente comparable de trabajo, pareja y cuidado, la tabla muestra:
- el p de Fisher sin ajuste en cada estrato;
- la prueba de interacción.

Es exploratoria, no interviene en ninguna clasificación ni en la conclusión, y se identifica como tal en los informes.

## 4. Comparación de reproducibilidad en las pruebas

La primera versión de la prueba 16 comparaba como texto los p ajustados recalculados con los guardados. Fallaba por el último dígito decimal al releer el CSV (0,42657342657342656 frente a 0,4265734265734265). Ahora compara numéricamente, con una tolerancia relativa de 10⁻¹². No cambió ningún resultado.

## 5. Figuras

Después de revisar las figuras, moví dos leyendas y un rótulo que tapaban datos (f01 y f04). Los datos no cambian.
