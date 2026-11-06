# Fase 36B: resultados de las pruebas

**32 de 32 pruebas superadas.** 25 vienen de `plan_pruebas_fase36.md` y 7 se agregaron en este encargo. Ninguna quedó con fallo sin resolver. Se repiten con `python fase36/pruebas_fase36.py`.

| N.º | Grupo | Prueba | Resultado | Detalle |
|---|---|---|---|---|
| 1 | Plan | Conservación de las 529 | OK | 529 identificadores iguales y en el mismo orden; 24 matrices con 529 filas |
| 2 | Plan | Las 30 generales | OK | 30 en P1 y F1; 29 sin IMC en P2 y F2; conjunto exacto de relevancia_33.csv |
| 3 | Plan | Sin variables excluidas | OK | Ninguna excluida en esquemas ni en columnas, por nombre, prefijo o sufijo; 37 tablas sin identificadores personales |
| 4 | Plan | Códigos y significados | OK | 120 niveles iguales al diccionario y al catálogo; códigos ascendentes y consecutivos |
| 5 | Plan | Sin NaN ni códigos espurios | OK | Todo finito; sin columnas laborales ni de sobrecarga; columnas y orden exactos |
| 6 | Plan | Trazabilidad de imputaciones | OK | 210 recuentos iguales a las auditorías; 665 + 262 imputadas, 100 heredadas; 16 variables iguales celda a celda con la marca histórica |
| 7 | Plan | Sin fuga del MRS | OK | Agregar y permutar el MRS no cambia matriz ni parámetros; el transformador no lo nombra en su código |
| 8 | Plan | Determinismo | OK | Dos procesos distintos y la versión oficial: 234 archivos con el mismo SHA-256 |
| 9 | Plan | Escalado reproducible | OK | Recalculado a mano con el CSV de parámetros: diferencia máxima 8.9e-16; media 0 y varianza 1 salvo IMC |
| 10 | Plan | Nueva participante: caso de referencia | OK | 24 filas transformadas de una en una en 4 escenarios: diferencia máxima 4.4e-16; artefactos con el mismo SHA-256 |
| 11 | Plan | Compatibilidad con PCA y FAMD | OK | P1 34 col., 29.5047; P2 33 col., 29.0000; F1 50 col., 38.5047; F2 49 col., 38.0000. Centradas. No se ajustó ningún modelo |
| 12 | Plan | Separación de módulos | OK | Fuera de las matrices generales; 287, 263, 239 y 251; laboral y sobrecarga observada a la vez: 130; las tres observadas: 122 |
| 13 | Plan | Datos históricos | OK | 511 archivos de datos iguales al manifiesto del cierre |
| 14 | Adicional | Valores laborales falsos | OK | 287 con valores 1 a 5 iguales al limpio; fuera las 22 con relleno 3 y las 220 con 0 de no aplica |
| 15 | Adicional | Confusión de ceros | OK | 278 con cantidad 0 sin fila en el módulo de sobrecarga; ninguna sobrecarga 0 |
| 16 | Adicional | Salto en frecuencias | OK | Mapa 0, 1, 2, 3, 4, 5 → 0, 0, 1, 2, 3, 4 solo en las tres frecuencias de ejercicio; «Nunca» conserva su código en las otras 9 variables |
| 17 | Adicional | Agrupación de FAMD | OK | La regla determinista reproduce la tabla fija; 31 grupos, todos con al menos 5 % (mínimo 5.5%) |
| 18 | Adicional | IMC | OK | Media 29.2296, DE 6.2636 en 267; varianza en 529 = 0.5047; 262 imputadas con z = 0 |
| 19 | Adicional | Nominal | OK | Distancia² igual en las 10 parejas (4.1067); varianza total 1 |
| 20 | Adicional | Nivel inválido | OK | 5 valores no admitidos × 4 escenarios: error, sin matriz |
| 21 | Adicional | Variable constante | OK | DE = 0 detiene la calibración con error; la variable no se elimina en silencio |
| 22 | Adicional | Fuga de ajuste | OK | Parámetros intactos en memoria y en disco (SHA-256); el transformador no tiene método de ajuste |
| 23 | Adicional | Verdad del simulador | OK | 8 archivos leídos según el gancho de auditoría: ni la verdad ni la bitácora; sin escrituras fuera de la salida |
| 24 | Adicional | Sensibilidades | OK | 507 + 22; 508 + 21; 454 + 75. Centradas en las filas de ajuste. 32 preparadas, ninguna ejecutada |
| 25 | Adicional | Etiquetas | OK | 22 trabajo imputado; 21 cuidado; 29, 22 y 28 ceros de ejercicio |
| 26 | Encargo | Equivalencia matemática de FAMD | OK | 32 comprobaciones con datos sintéticos, incluido un control negativo; referencia externa: prince 0.23.1 |
| 27 | Encargo | Ausencia de doble escalado del IMC | OK | Varianza en 529 = 267/529 = 0.5047 en P1 y F1; DE 1 solo entre las 267; misma columna en ambas rutas |
| 28 | Encargo | Conservación del cero válido de cuidados | OK | 278 ceros como nivel válido, no como ausencia; valor original vacío preservado; 21 marcados como heredados |
| 29 | Encargo | Trazabilidad del ejercicio con ceros heredados | OK | 29, 22 y 28 ceros trazables por participante; unión 75; todos con la madre en NO |
| 30 | Encargo | Codificación de categorías válidas no observadas | OK | 13 niveles válidos sin observaciones en 4 escenarios: finitos, sin error ni cambio de parámetros, con marca; «Nunca» igual a «No lo realiza», sin columna propia |
| 31 | Encargo | Reutilización de parámetros con una nueva participante | OK | Caso inventado en 4 escenarios: columnas exactas, valores iguales al cálculo manual, IMC ausente en z = 0 con marca, otra ausente con valor congelado y aviso; parámetros intactos |
| 32 | Encargo | Integridad frente al manifiesto del cierre 34-35 | OK | 1130 archivos iguales al manifiesto; HEAD 745d689; nada preparado; 14 archivos del diseño 36A sin modificar desde antes de la 36B |

## Control de mutaciones

Las 32 pruebas pasaron en la primera ejecución completa, de modo que se comprobó que pueden fallar. Se introdujeron errores en memoria, sin tocar los archivos, y cada prueba correspondiente debía detectarlos: **14 de 14 detectados**.

| Error introducido | Función de prueba | Detectado |
|---|---|---|
| Se pierde una fila | p01 | Sí |
| IMC estandarizado dos veces | p11 | Sí |
| IMC estandarizado dos veces | p18 | Sí |
| IMC estandarizado dos veces | p27 | Sí |
| Entra una variable del MRS | p03 | Sí |
| Entra una variable del MRS | p05 | Sí |
| Valor no finito en una matriz | p05 | Sí |
| Nominal sin ponderar en PCA | p19 | Sí |
| «Nunca» deja de unificarse | p16 | Sí |
| Se pierde una marca de cero heredado | p25 | Sí |
| Se pierde una marca de cero heredado | p29 | Sí |
| Se abre la verdad del simulador | p23 | Sí |
| Aparece sobrecarga 0 | p15 | Sí |
| Aparece un 0 laboral de relleno | p14 | Sí |

## Alcance

- No se evaluó la calidad de clústeres ni la varianza explicada, porque corresponden a la Fase 37.
- La equivalencia de FAMD se probó con datos sintéticos, no con las matrices reales.
- La comparación con `prince` necesita indicar su carpeta con `--referencia`. Sin esa opción, la prueba 26 ejecuta las demás comprobaciones.
