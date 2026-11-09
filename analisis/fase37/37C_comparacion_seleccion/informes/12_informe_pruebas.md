# Fase 37C: informe de pruebas

Programas: `scripts/pruebas_37c.py` y `scripts/control_mutaciones_37c.py`. Resultados: `pruebas/resultados_pruebas.csv` y `pruebas/control_mutaciones.csv`. Revisión documental: `scripts/verificar_informes_37c.py`.

**Resultado: 26 de 26 pruebas superadas; 23 de 23 errores introducidos detectados; 43 comprobaciones documentales superadas.**

Las 22 pruebas pedidas en el encargo están cubiertas, y se agregaron otras cuatro. Ninguna se declara superada sin haberse ejecutado. Las mutaciones se aplican en memoria y no alteran ningún archivo.

## Pruebas

| N.º | Prueba | Resultado | Detalle |
|---|---|---|---|
| 1 | Integridad de resultados históricos: manifiestos de las Fases 34-35, 36, 37A y 37B | superada | 2217 archivos iguales a sus manifiestos |
| 2 | Identificadores: 529 únicos y en el mismo orden en etiquetas, coordenadas y Cadena | superada | 529 identificadores |
| 3 | Listas A y B coinciden con los archivos originales | superada | 108 (57 y 52) y 15, leídas de sus originales |
| 4 | Ausencia de variables MRS en entradas y salidas | superada | Sin columnas MRS; 93 archivos leídos, ninguno de datos/ |
| 5 | Reproducibilidad: repetir la cadena en otra carpeta da las mismas etiquetas | superada | 18 particiones recalculadas son idénticas a las guardadas |
| 6 | Sin contaminación: cambiar a las participantes no usadas no altera parámetros, reducción ni etiquetas de la submuestra | superada | Parámetros, reducción, etiquetas e imputaciones idénticos |
| 7 | Reajuste correcto de PCA y FAMD: con las 529 reproduce la Fase 37A; con la submuestra usa solo sus filas | superada | Reproducción con 1e-8; ajuste en submuestra comprobado con SVD independiente |
| 8 | Recalibración solo dentro de la muestra: con las 529 da la matriz histórica, y con la submuestra usa sus medias y proporciones | superada | Reproducción histórica con 1e-10; medias e IMC de la submuestra |
| 9 | Proyección sin información futura: una fila a la vez da lo mismo que el lote | superada | Cuatro participantes: transformar, proyectar y asignar no dependen de las demás |
| 10 | ARI correcto: implementación propia, invariante al nombre de los grupos | superada | Coincide con implementación propia y con el valor guardado |
| 11 | Comparaciones sobre participantes compartidas | superada | 435 pares, intersección de al menos 317, recalculados de forma independiente |
| 12 | Referencia nula reproducible y bien definida | superada | Semillas, réplica guardada e hipótesis comprobadas; 100 réplicas |
| 13 | La referencia correlacionada conserva lo que declara | superada | Marginales exactas, salto íntegro, Spearman 0.041, controles sintéticos correctos |
| 14 | Separación entre lo confirmatorio y lo exploratorio | superada | Lista B, enmienda y contraste rotulados; etiquetas de origen en el protocolo |
| 15 | Trazabilidad de los cambios de codificación | superada | Ridit reproduce la Fase 36 con 1e-10; puntuaciones normales con media 0 y DE 1; sin artefactos que la reemplacen |
| 16 | Tamaños y métricas consistentes | superada | Tamaños suman 529 y 423; siluetas recalculadas |
| 17 | Ausencia de selección por MRS: el código de decisión no lee nada relacionado | superada | Sin MRS, Random Forest, GMM ni Shannon en el código de decisión |
| 18 | Asignación de nuevas participantes: la regla reproduce K-means y el margen está bien calculado | superada | K-means 100 %; Ward por prototipos reproducido y rotulado como aproximación |
| 19 | Conservación de parámetros y versiones | superada | Versiones iguales a la Fase 37B; protocolo y enmienda coinciden con sus sellos |
| 20 | Correspondencia entre tablas y figuras | superada | 12 figuras; 451 valores dibujados coinciden con las tablas |
| 21 | Ausencia de cambios en la plataforma | superada | git status fuera de analisis/ vacío |
| 22 | Ausencia de commit y de push | superada | HEAD 745d689; la rama no existe en el remoto |
| 23 | La decisión se deriva de las tablas y una debilidad crítica no se compensa | superada | Conclusión por reglas: B; 5 particiones finalistas |
| 24 | La imputación reestimada con las 529 reproduce la histórica, salvo la excepción documentada | superada | Solo difieren las 30 celdas de tiene_actividad_sexual |
| 25 | Niveles distintos no se tratan como equivalentes: E1 sin reducción coincide con E0, y las tablas guardan cada nivel | superada | E1 = E0 en las referencias sin reducción; tres niveles por configuración |
| 26 | Sin archivos ajenos: todo queda en la carpeta 37C, y sin carpetas __pycache__ en fases protegidas | superada | Sin escrituras fuera de 37C ni __pycache__ en fases protegidas |


## Controles negativos

| Error introducido | Prueba | ¿Detectado? | Mensaje |
|---|---|---|---|
| Manifiesto histórico alterado | 1 | Sí | AssertionError: 37B: cambió estabilidad/ari_por_remuestreo.csv |
| Etiquetas en otro orden | 2 | Sí | AssertionError: etiquetas en otro orden |
| Lista A sin una configuración | 3 | Sí | AssertionError: Lista A distinta de la tabla de la Fase 37B |
| Lista B con un identificador sustituido | 3 | Sí | AssertionError: Lista B distinta del documento |
| Variable MRS en la tabla de entrada | 4 | Sí | AssertionError: Columnas prohibidas: [('entrada', 'mrs_total')] |
| Parámetros calibrados con todas las filas | 6 | Sí | AssertionError: Los parámetros usan filas no usadas |
| Reducción ajustada con todas las filas (contaminación) | 6 | Sí | AssertionError: La reducción usa filas no usadas |
| Reducción ajustada con todas las filas (reajuste) | 7 | Sí | AssertionError:  |
| Recalibración con todas las filas | 8 | Sí | AssertionError: edad no usa la media de la submuestra |
| ARI reemplazado por coincidencia directa | 10 | Sí | AssertionError: ARI distinto del propio |
| ARI de pares con filas no compartidas | 11 | Sí | AssertionError: Los pares no usan solo a las compartidas |
| Réplica sin semilla | 12 | Sí | AssertionError: Misma semilla, tablas distintas |
| Marginal alterada en la referencia | 13 | Sí | AssertionError: Marginal distinta en edad |
| Lógica de salto rota en la referencia | 13 | Sí | AssertionError: Marginal distinta en realiza_fuerza |
| Lista B rotulada como confirmatoria | 14 | Sí | AssertionError: Lista B sin rótulo exploratorio |
| Tamaños alterados en una repetición | 16 | Sí | AssertionError: Una repetición no suma 423 |
| Valor de una figura distinto de la tabla | 20 | Sí | AssertionError: f02_estabilidad_completa: F1_c03_km_k4 dibujado 0.4533886586235165, tabla  |
| Cambio en la plataforma | 21 | Sí | AssertionError: Hay cambios fuera de analisis/:  M encuestas/models.py |
| Commit nuevo | 22 | Sí | AssertionError: HEAD cambió: abc1234 |
| Rama publicada | 22 | Sí | AssertionError: La rama aparece en el remoto |
| Estado de un criterio distinto de la regla | 23 | Sí | AssertionError: Estado distinto de la regla |
| Finalista con debilidad crítica | 23 | Sí | AssertionError: Una finalista tiene CRIT en una etapa que la excluye |
| Niveles E1 y E0 sin distinguir en las referencias | 25 | Sí | AssertionError: Sin reducción, E1 debe igualar a E0 |


## Lo que estas pruebas no aseguran

- Comprueban que el cálculo es correcto y coherente con el protocolo, no que la conclusión sea verdadera.
- No se reejecutaron las pruebas históricas de las fases anteriores. La integridad de esas fases se verificó por huellas. Alguna prueba histórica que revise el contenido de la carpeta `fase37` podría señalar la nueva subcarpeta, sin que eso signifique un cambio en sus archivos.
