# Fase 37A: informe de pruebas

**Resultado: 19 de 19 pruebas superadas.** Control de mutaciones: 11 errores introducidos, 14 de 14 comprobaciones los detectaron.

Los programas son `scripts/pruebas_37a.py` y `scripts/control_mutaciones_37a.py`. Los resultados están en `pruebas/`. La prueba 10 repite el ajuste en dos procesos.

## Pruebas

| N.º | Prueba | Resultado | Detalle |
|---|---|---|---|
| 1 | Conservación de las 529 participantes | OK | 28 archivos principales y 34 variantes con 529 participantes, sumando ajuste y proyección |
| 2 | Conservación del orden de identificadores | OK | Mismo orden que fase36/matrices/identificadores.csv; las variantes conservan el orden relativo |
| 3 | Integridad de las matrices de entrada | OK | SHA-256 iguales a los de la Fase 36; columnas e inercia esperadas |
| 4 | Ausencia de escalado adicional | OK | Coordenadas = matriz · V sin otra transformación; IMC reconstruido con varianza 267/529; sin StandardScaler, blanqueo ni prince |
| 5 | Ausencia de MRS en las entradas | OK | 1588 columnas sin variables excluidas; 91 archivos leídos según el gancho, ninguno de datos/; sin escrituras fuera de la salida |
| 6 | Valores propios no negativos y ordenados | OK | 38 modelos con valores propios no negativos y decrecientes; mínimo 8.32e-03 |
| 7 | Ortogonalidad de los componentes | OK | V·Vᵀ = I, diferencia máxima 4.0e-15; coordenadas sin correlación y con varianza λ, diferencia 1.3e-14 |
| 8 | Consistencia de la inercia total | OK | Σλ = 29,5047, 29, 38,5047 y 38. Factor 528/529 comprobado frente a explained_variance_. Rangos 33, 32, 39 y 38 |
| 9 | Reconstrucción numérica | OK | Con todos los ejes, error máximo 9.3e-15. Con k ejes, el error cuadrático medio iguala la suma de los λ omitidos |
| 10 | Reproducibilidad de coordenadas | OK | Dos procesos distintos y la versión oficial: 131 archivos con el mismo SHA-256 |
| 11 | Transformación de una participante nueva | OK | 24 filas desde sus respuestas originales: diferencia 1.3e-15 con la coordenada guardada. Caso inventado correcto en 4 escenarios, independiente de otras filas; artefactos intactos |
| 12 | Consistencia de las sensibilidades | OK | 34 variantes: ajuste y proyección separados, proyección con parámetros congelados, IMC sin amplificar en S-BLOQUE-SA con inercia global conservada; similitud 1 ante una rotación |
| 13 | Correspondencia entre resultados y gráficos | OK | 6 figuras comparadas con sus tablas, punto a punto; proyección en un solo color; 16 PNG presentes |
| 14 | Conservación de los archivos protegidos | OK | 1130 archivos del cierre 34-35 y 258 de la Fase 36 sin cambios; HEAD 745d689; sin nada preparado; src/ y dependencias sin cambios |
| 15 | Protocolo sellado antes de los resultados | OK | SHA-256 igual al sello (3c4d2de951c2…); el sello es anterior al programa que ajusta los modelos |
| 16 | Sin clústeres ni selección | OK | Sin importar módulos de agrupamiento, sin archivos de clústeres ni etiquetas; la Fase 37B no se inició |
| 17 | Coordenadas por candidato | OK | 7 candidatos en 4 escenarios: cada archivo son los primeros k ejes del de 20; ninguno supera el rango |
| 18 | Contribuciones de FAMD frente a su definición | OK | En 8 ejes y todas las variables: aporte = r² (v·r² en IMC) o η², diferencia máxima 2.7e-15 |
| 19 | Orden de niveles | OK | Cinco variables con un eje principal cada una; baricentro recalculado igual al de la tabla |

## Control de mutaciones

Se introducen errores en memoria, sin tocar resultados, para comprobar que las pruebas pueden fallar.

| Error introducido | Prueba | ¿Detectado? |
|---|---|---|
| Se pierde una fila de coordenadas | p01 | Sí |
| Coordenadas en otro orden | p02 | Sí |
| Coordenadas reescaladas | p04 | Sí |
| Un candidato no coincide con los primeros ejes | p17 | Sí |
| Valores propios sin el factor 528/529 | p07 | Sí |
| Valores propios sin el factor 528/529 | p08 | Sí |
| Componentes no ortogonales | p07 | Sí |
| Componentes no ortogonales | p09 | Sí |
| Entra una variable del MRS | p05 | Sí |
| Valor propio negativo | p06 | Sí |
| IMC estandarizado otra vez | p03 | Sí |
| IMC estandarizado otra vez | p08 | Sí |
| Contribuciones alteradas | p18 | Sí |
| Baricentros alterados | p19 | Sí |

## Fallos encontrados y cómo se resolvieron

| Fallo | Causa | Resolución |
|---|---|---|
| Prueba 10, reproducibilidad | `archivos_leidos.csv` difería entre la salida oficial y una temporal: el protocolo está dentro de la carpeta oficial, y el registro omitía las lecturas de esa carpeta. Coordenadas y tablas sí coincidían | El registro siempre incluye el protocolo. Se volvió a ejecutar todo |
| Prueba 14, archivos protegidos | Error de la prueba: `strip()` recortaba el primer carácter de estado de `git status`, y deformaba la primera ruta. Ningún archivo protegido había cambiado | La prueba conserva los espacios iniciales |
| Control: valor propio negativo no detectado | La prueba 6 leía los modelos del disco y no por la función que la mutación sustituye | La prueba 6 usa esa función |
| Control: coordenadas reescaladas sin detectar en la prueba 17 | El reescalado era igual en todos los candidatos, y esa prueba solo compara candidatos entre sí; no era un error que debiera detectar | Se creó una mutación propia: un candidato que no coincide con los primeros ejes |

## Limitación

La prueba 15 compara fechas de modificación de archivos. Sirve como comprobación interna, pero no es una prueba independiente de la secuencia temporal: el SHA-256 solo garantiza que el protocolo no cambió desde el sello. Además, `ejecutar_37a.py` se detiene al comenzar si la huella no coincide.
