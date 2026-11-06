# Fase 37B: informe de pruebas

**Resultado: 26 de 26 pruebas superadas.** Control de errores: 22 errores introducidos, detectados en 26 de 26 comprobaciones.

Los programas son `scripts/pruebas_37b.py` y `scripts/control_mutaciones_37b.py`. Los resultados están en `pruebas/`. Silueta, Davies-Bouldin, Calinski-Harabasz y ARI se recalculan con implementaciones propias, en una muestra de configuraciones.

## Pruebas

| N.º | Prueba | Resultado | Detalle |
|---|---|---|---|
| 1 | Integridad de matrices y coordenadas | OK | 53 verificaciones previas OK; cada configuración guarda la huella del archivo que coincide con su entrada |
| 2 | Conservación de las 529 participantes | OK | 529 filas y 420 configuraciones, sin valores faltantes |
| 3 | Identificadores correctos | OK | Etiquetas, distancias y las 34 variantes: los identificadores coinciden, sin repetidos ni faltantes |
| 4 | Ausencia de variables del MRS | OK | Sin columnas del MRS; 98 archivos leídos según la auditoría, ninguno de datos/; los programas no lo mencionan |
| 5 | Ausencia de escalado adicional | OK | Inercia y centroides se reproducen con las coordenadas tal como están; sin escaladores en los programas |
| 6 | Reproducibilidad de K-means | OK | 3 configuraciones ajustadas otra vez: etiquetas idénticas. La repetición completa está en la prueba 22 |
| 7 | Reproducibilidad del aglomerativo | OK | 3 configuraciones ajustadas otra vez: etiquetas idénticas. La repetición completa está en la prueba 22 |
| 8 | Número correcto de etiquetas | OK | Cada participante tiene una etiqueta, y cada configuración usa exactamente k grupos |
| 9 | Tamaños de grupos consistentes | OK | Tamaños recalculados iguales a la tabla en las 420; 40 grupos bajo 27 registrados |
| 10 | Métricas correctamente calculadas | OK | 6 configuraciones con implementación propia de silueta, Davies-Bouldin y Calinski-Harabasz: diferencia máxima 4.4e-16 |
| 11 | ARI correcto e invariante a los nombres de los clústeres | OK | Coincide con una implementación propia; renombrar los grupos no cambia el valor; primera repetición reproducida |
| 12 | Remuestreos reproducibles | OK | 30 subconjuntos de 423, sin repetidos y distintos entre sí, iguales a los guardados; estabilidad de una configuración reproducida completa |
| 13 | Comparaciones solo sobre participantes compartidas | OK | ARI entre remuestreos recalculado sobre la intersección; ARI de sensibilidades recalculado solo con las filas presentes en ambas |
| 14 | Referencia nula correctamente construida | OK | Marginales conservadas; frecuencias con su madre; transformar lo permutado equivale a mover las columnas de cada variable (118 comprobaciones); inercia conservada sin reescalar; asociaciones debilitadas; 8.400 filas; no usa etiquetas observadas |
| 15 | Ausencia de fuga de información | OK | Cambiar a quienes quedan fuera del subconjunto no altera las etiquetas; la ejecución principal no lee la procedencia; ajuste y proyección no comparten filas. Límite: la reducción se ajustó con las 529, como declara el protocolo |
| 16 | Separación entre ajuste y proyección | OK | Filas 507/22, 508/21 y 454/75; las demás, 529/0. Las proyectadas se asignan con prototipos calculados solo con las filas de ajuste |
| 17 | Conservación de parámetros | OK | 420 configuraciones con la huella del protocolo sellado; parámetros, centroides y versiones guardados |
| 18 | Asignación por centroides | OK | K-means 100 % en las 210; flujo completo con un caso inventado en los 4 escenarios; distancia y margen coinciden con el cálculo manual |
| 19 | Prototipos del aglomerativo | OK | Recalculado; acuerdo entre 70.9 % y 98.1 %: no se asume perfecto |
| 20 | Integridad de los archivos históricos | OK | 175 de la Fase 37A (y sin archivos nuevos), 258 de la Fase 36 y 1130 del cierre 34-35, sin cambios |
| 21 | Sin commits, push ni cambios en la plataforma | OK | HEAD 745d689; nada preparado; los mismos 8 archivos seguidos con cambios previos; src/ y dependencias sin cambios |
| 22 | Reproducción completa en otra carpeta y con otro número de procesos | OK | Las 420 configuraciones con todos sus datos, y 2 réplicas nulas, idénticas con 5 procesos en lugar de 10 |
| 23 | Tablas consolidadas iguales a los lotes | OK | 420 configuraciones, 12.600 valores de ARI y 3.332 ajustes de sensibilidad |
| 24 | Comparación con la nula y lista para la Fase 37C según el protocolo | OK | 108 configuraciones cumplen la regla, recalculada desde las tablas; sin puntuación compuesta |
| 25 | Sin GMM, reglas de asociación ni selección de un ganador | OK | Sin GMM ni reglas; sin archivos de modelo definitivo; la Fase 37C no se inició |
| 26 | Correspondencia entre resultados y gráficos | OK | 3 figuras comparadas punto a punto con sus tablas; 13 PNG; sin color por severidad |

## Control de errores

Se introducen errores en memoria, sin tocar resultados, para comprobar que las pruebas pueden fallar.

| Error introducido | Prueba | ¿Detectado? |
|---|---|---|
| Se pierde una fila de etiquetas | p02 | Sí |
| Etiquetas en otro orden | p03 | Sí |
| Etiqueta fuera de los k grupos | p08 | Sí |
| Etiquetas que no corresponden a los tamaños | p09 | Sí |
| Huella de entrada incorrecta | p01 | Sí |
| Coordenadas reescaladas | p05 | Sí |
| Coordenadas reescaladas | p10 | Sí |
| Inercia y centroides alterados | p05 | Sí |
| Inercia y centroides alterados | p19 | Sí |
| Silueta alterada en la tabla | p10 | Sí |
| Davies-Bouldin alterado en la tabla | p10 | Sí |
| ARI de remuestreo alterado | p11 | Sí |
| Estabilidad alterada | p12 | Sí |
| Estabilidad alterada | p23 | Sí |
| Subconjuntos repetidos | p12 | Sí |
| Subconjuntos de otro tamaño | p12 | Sí |
| Nula con una sola permutación | p14 | Sí |
| Nula con la madre separada de su frecuencia | p14 | Sí |
| Nula con marginal alterada | p14 | Sí |
| Nula incompleta | p14 | Sí |
| Proyección donde no corresponde | p16 | Sí |
| Filas de ajuste incorrectas | p16 | Sí |
| Huella de protocolo incorrecta | p17 | Sí |
| Acuerdo de K-means alterado | p18 | Sí |
| Acuerdo de K-means alterado | p19 | Sí |
| Lista para la Fase 37C inflada | p24 | Sí |

## Fallos encontrados y cómo se resolvieron

| Fallo | Causa | Resolución |
|---|---|---|
| Prueba 23, tablas iguales a los lotes | Error de la prueba: exigía igualdad exacta tras leer decimales de un CSV. Los datos estaban bien | Usa una tolerancia de 1e-12 |
| Control: centroides alterados sin detectar en la prueba 19 | La prueba recalculaba los prototipos sin revisar los guardados | La prueba compara también los guardados |

Antes de sellar el protocolo también corregí un error de programación: el nombre de una variable no general estaba mal escrito, y por eso `sobrecarga_fisica_emocional` quedaba en la tabla que se permuta. No afectó ningún resultado, porque aún no se ejecutaba nada.

## Limitaciones

- Las implementaciones propias se comprobaron en 6 configuraciones, no en las 420. Las pruebas de reproducción, tamaños y etiquetas sí cubren las 420.
- La reproducción de la nula cubre 2 de las 20 réplicas.
- La correspondencia de figuras se comprobó punto a punto en 3 figuras de 13. Las demás se revisaron visualmente.
