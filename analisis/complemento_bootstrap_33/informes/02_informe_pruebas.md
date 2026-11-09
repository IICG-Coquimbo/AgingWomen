# Complemento de la Fase 35B: informe de pruebas

*05-11-2026. Programa: `scripts/pruebas_b33.py`. Resultados: `pruebas/resultados_pruebas.csv` y `pruebas/controles_negativos.csv`.*

**Resultado:** 19 de 19 pruebas superadas y 23 de 23 controles negativos detectados.

Las pruebas se ejecutaron al terminar la corrida principal, en un solo proceso. Después se repitieron dos veces más, cada vez que se regeneró el resumen: la primera para añadir una tabla descriptiva y redondear una columna, la segunda para corregir el título de una figura. Las tres ejecuciones tuvieron el mismo resultado.

## 1. Pruebas (sección 12 de la instrucción)

| N.º | Prueba | Resultado | Detalle |
|---:|---|---|---|
| 1 | Exactamente las 33 candidatas documentadas | Superada | 33 = `predictores_elegibles_33.csv` = `VARIABLES_33` |
| 2 | `doble_carga` no es candidata | Superada | Ausente del escenario y de los 500 resultados |
| 3 | `prevision` no ingresa | Superada | Ausente del escenario y de los 500 resultados |
| 4 | Población analítica correcta | Superada | 529 personas (281 severas y 248 no severas), 287 laborales y 239 cuidadoras. `dataset_fase35_33_variables.csv` es igual texto a texto a `dataset_fase35.csv` sin la columna de diabetes |
| 5 | Exactamente 500 remuestreos | Superada | `rem_0000` a `rem_0499` |
| 6 | Índices dentro del conjunto y con huella | Superada | 500 vectores en 0–528; la SHA-256 recalculada es igual a la guardada |
| 7 | Mecanismo bootstrap | Superada | Estratificado con reemplazo (281/248). Cada muestra tiene entre 314 y 358 personas distintas, con media de 335. El n laboral es igual al de la corrida antigua en los 500 casos, es decir, son las mismas muestras |
| 8 | Sin filtraciones del MRS | Superada | Ninguna candidata es ítem, puntaje o categoría del MRS. El objetivo es `severo_mrs`, el mismo de la selección definitiva |
| 9 | Procedimiento completo en cada remuestreo | Superada | Los 500 registros son coherentes: q es BH de las 33, la relevancia usa q < 0,10, están todos los pares de relevantes, ninguna laboral eliminó a una general y la sobrecarga nunca eliminó a otra variable. Los remuestreos 0, 250 y 499 se recalcularon desde cero y dieron igual |
| 10 | Parámetros constantes | Superada | 500 remuestreos, 5.000 permutaciones, q < 0,10, identificador 1 y un proceso. El umbral global volvió a 0,05 al terminar |
| 11 | Frecuencias recalculadas de forma independiente | Superada | Cinco columnas iguales al recuento directo |
| 12 | Ninguna frecuencia supera 100 % | Superada | Todas entre 0 y 100; los tres estados suman 100 |
| 13 | Las nunca seleccionadas aparecen con 0 % | Superada | 33 filas por variante. En la variante adaptada ninguna tiene 0 %; en la estándar tienen 0 % `edad`, `evacuacion_intestinal` y `golosinas_semana` |
| 14 | Reproducibilidad y fidelidad | Superada | El remuestreo 7 da lo mismo dos veces. `medir_remuestreo` sin remuestreo (i = 0) es exactamente igual a `complementario_cuidados.medir` |
| 15 | Comparación con la corrida antigua bien identificada | Superada | La antigua tiene 30 candidatas e incluye `doble_carga`; hay 29 variables comunes. El código antiguo reprodujo exactamente los remuestreos antiguos 0 y 1 |
| 16 | Archivos de las Fases 34 a 39 intactos | Superada | 5.873 archivos de `analisis/` y `datos/` con la misma huella |
| 17 | Django intacto | Superada | 104 archivos de `src/` iguales; git sin cambios en `src/` |
| 18 | Resultados antiguos no sobrescritos | Superada | 6 archivos históricos de estabilidad y registros con la misma huella |
| 19 | Selección definitiva leída correctamente | Superada | La variante adaptada y la estándar, con 10.000 y con 50.000 permutaciones, coinciden con `log_revision_33.txt` |

## 2. Controles negativos

A una copia de cada objeto se le introdujo un error a propósito. El control debía detectarlo, y en los 23 casos lo hizo.

| Ámbito | Controles |
|---|---|
| Variables | Candidata extra `doble_carga`; candidata extra `prevision`; candidata del MRS (`mrs_total`); falta una candidata (32); escenario con `doble_carga`; población laboral alterada |
| Índices | Índice fuera del conjunto (529); remuestreo sin estratificar; remuestreo sin reemplazo; 499 remuestreos |
| Procedimiento | Decisión incoherente con la relevancia; faltan pares; umbral 0,05 en vez de 0,10; una laboral elimina a una general |
| Configuración | Permutaciones alteradas (10.000); alfa alterado en la configuración |
| Frecuencias | Un conteo de más; porcentaje sobre 499; frecuencia mayor que 100; falta una variable con 0 % |
| Integridad | Remuestreo guardado alterado; archivo de una fase anterior alterado; archivo de Django alterado |

## 3. Alcance de las pruebas

- Comprueban que el procedimiento se aplicó como se fijó en el protocolo y que los números del informe salen de los 500 remuestreos.
- No comprueban si la selección es «correcta» en sentido sustantivo.
- No usan la verdad del simulador.
