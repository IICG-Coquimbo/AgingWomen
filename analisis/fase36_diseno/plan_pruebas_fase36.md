# Fase 36A: plan de pruebas para la Fase 36B

**Estado:** diseño. Estas pruebas **no se han ejecutado**, porque aún no existen matrices.

**Reglas generales:** trabajar en una carpeta nueva (`analisis/fase36/`), con datos de prueba sintéticos pequeños para las funciones y las matrices reales solo cuando se apruebe la Fase 36B. Ninguna prueba debe escribir fuera de una carpeta temporal.

## 1. Pruebas requeridas

| N.º | Requisito | Prueba propuesta | Resultado esperado |
|---|---|---|---|
| 1 | Conservación de las 529 | Comparar identificadores de cada matriz con `dataset_fase35.csv` | 529 iguales, sin duplicados, mismo orden |
| 2 | Las 30 generales | Comparar con `relevancia_33.csv` donde `poblacion == general` | Conjunto exacto; 30 en el esquema |
| 3 | Sin excluidas | Buscar por nombre y por prefijo de columna en esquema y matrices | Ausentes: `usa_medicamentos_diabetes`, `doble_carga`, `prevision`, `etapa_menopausica`, `cuida_otras_personas`, `realiza_*`, preguntas menstruales, `mrs_*`, `severo_mrs`, `severidad_*`, consecuencias, `participante_id`, `*_imputado`, `imc_fue_imputado` |
| 4 | Códigos y significados | Comparar el codificador con `diccionario_codificacion_fase36.csv` y `catalogo.leer_modelos()` | Todos los niveles del instrumento mapeados; sin niveles inventados; orden ascendente |
| 5 | Sin NaN ni códigos espurios | `np.isfinite` en cada matriz; ningún 0 ni 3 de relleno laboral (no hay columnas laborales) | Todo finito; columnas exactas |
| 6 | Trazabilidad de imputaciones | Máscaras por celda contra `origen_respuestas_34D.csv` | Coinciden en las 33; 665 imputadas y 100 heredadas en las generales; 262 de IMC |
| 7 | Sin fuga del MRS | Comprobar columnas y código: ninguna transformación recibe MRS; permutar el MRS no cambia la matriz | Matriz idéntica; lectura de MRS solo en caracterización |
| 8 | Determinismo | Construir dos veces, en procesos distintos | Bytes iguales (SHA-256) |
| 9 | Escalado reproducible | Aplicar los parámetros guardados y comparar | Diferencia máxima < 1e-12; media y varianza esperadas |
| 10 | Nueva participante | Transformar un caso de referencia como caso nuevo | Fila igual a la de la matriz; los parámetros no cambian |
| 11 | Compatibilidad con PCA y FAMD | Con datos pequeños: dimensiones y suma de varianza | PCA: 34 y 33 columnas; varianza 29,505 y 29. FAMD: 50 y 49 columnas; inercia 38,505 y 38 |
| 12 | Separación de módulos | Comprobar columnas y poblaciones | Laborales y sobrecarga fuera de las matrices generales; 287, 263, 239 y 251 |
| 13 | Datos históricos | Manifiesto SHA-256 contra `cierre_fases_34_35/integridad/manifiesto_despues.csv` | Sin cambios fuera de la carpeta nueva |

## 2. Pruebas adicionales recomendadas

| N.º | Riesgo | Prueba | Resultado esperado |
|---|---|---|---|
| 14 | Valores laborales falsos | Módulo laboral desde el conjunto limpio | 0 valores de relleno; 22 fuera; ninguna fila con «0» de no aplica |
| 15 | Confusión de ceros | Cantidad = 0 no crea sobrecarga | 278 sin dato de sobrecarga, no sobrecarga 0 |
| 16 | Salto en frecuencias | Mapa `0, 2, 3, 4, 5` → `0, 1, 2, 3, 4` | Y código 1 → 0, si llega |
| 17 | Agrupación de FAMD | Regla determinista contra la tabla del diseño | Grupos iguales a los documentados; todos ≥ 5 % |
| 18 | IMC | Parámetros de las 267; imputadas en z = 0 | Media 29,23; DE 6,26; varianza 0,505 |
| 19 | Nominal | Distancia entre categorías distintas | Igual en toda pareja (4,11); varianza total 1 |
| 20 | Nivel inválido | Código fuera del instrumento | Error, sin perfil |
| 21 | Variable constante | DE = 0 en datos de prueba | Error, sin eliminar la variable |
| 22 | Fuga de ajuste | Transformar datos nuevos | Parámetros intactos (SHA-256) |
| 23 | Verdad del simulador | Registrar los archivos leídos | `dataset_usuaria_verdad.csv` y la bitácora no se leen |
| 24 | Sensibilidades | S-TRA, S-CUI y S-EJE | Filas de ajuste y de proyección separadas: 507 + 22; 508 + 21 |
| 25 | Etiquetas | Lista de ids contra los conteos históricos | 22 imputadas; 21 de cuidado; 29, 22 y 28 ceros de ejercicio |

## 3. Orden de ejecución

1. Pruebas de funciones con datos pequeños (4, 9, 16 a 22).
2. Construcción de artefactos de la Fase 36B, una vez aprobada.
3. Pruebas sobre matrices reales (1 a 3, 5 a 8, 10 a 15, 23 a 25).
4. Manifiesto final (13).

## 4. Criterio de cierre de la Fase 36B

Debe cumplirse todo lo anterior sin excepciones. Si una prueba falla, se documenta la causa y no se declara cerrada la fase. La calidad de los clústeres **no** es una prueba de esta fase: corresponde a la Fase 37.

## 5. No ejecutado en la Fase 36A

Ninguna de estas pruebas. En esta etapa solo se comprobó que el diccionario y la matriz cubren las 33 variables, y la integridad de los archivos (`apoyo/verificacion_diseno.csv`).
