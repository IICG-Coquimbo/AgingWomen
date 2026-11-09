# 1. Conclusión

**La Fase 36B queda cerrada técnicamente:** las cuatro matrices, sus transformadores y las poblaciones de sensibilidad están listos para la Fase 37. Las 32 pruebas se superaron y la validación matemática de FAMD fue satisfactoria (32 de 32 comprobaciones). No se ajustó PCA ni FAMD, no se formaron clústeres ni reglas, y no se hizo commit ni push.

# 2. Matrices

| Matriz | Ruta | Filas | Columnas | Inercia total |
|---|---|---|---|---|
| P1 | PCA con IMC | 529 | 34 | 29,5047 |
| P2 | PCA sin IMC | 529 | 33 | 29,0000 |
| F1 | FAMD con IMC | 529 | 50 | 38,5047 |
| F2 | FAMD sin IMC | 529 | 49 | 38,0000 |

La referencia sin reducción R0 usa P1 y P2.

**Incluidas:** las 30 variables generales. **Excluidas de las matrices:** las laborales, la sobrecarga, todas las variables objetivo del MRS y los identificadores, además de `usa_medicamentos_diabetes`, `doble_carga`, `prevision`, `etapa_menopausica`, `cuida_otras_personas`, `realiza_*`, preguntas menstruales, consecuencias y marcas de auditoría.

# 3. Tratamientos

| Tema | Tratamiento |
|---|---|
| IMC | Media 29,2296 y DE 6,2636, de las 267 observadas. Las 262 imputadas quedan en z = 0. Varianza en las 529: 0,5047, sin doble escalado |
| Cuidados | Cantidad = 0 es un nivel válido, con 278 casos; no significa sobrecarga 0. 21 ceros dependen de una imputación |
| Ejercicio | «Nunca» y «No lo realiza» se unen solo en las tres frecuencias. 29, 22 y 28 ceros heredados; 75 participantes en total |
| Procedencia | Por celda, sin la verdad del simulador. 210 recuentos iguales a las auditorías históricas |
| Módulos | Laboral 287 y 263; cuidados 239 y 251. Sin escalar y fuera de las matrices |

# 4. Validación de FAMD

Con datos sintéticos, la transformación coincidió con la métrica 1/p, con el criterio de Pagès, con los casos límite de MCA y de PCA, y con `prince` 0.23.1, instalada fuera del proyecto. Las diferencias fueron del orden de 1e-14. Un control negativo confirmó que el criterio detecta una ponderación equivocada.

**Límite.** F1 tiene peso reducido en el IMC por decisión de diseño, de modo que es FAMD con esa ponderación. F2 es estándar.

# 5. Pruebas e integridad

- **Pruebas:** 32 de 32 superadas, 25 del plan y 7 del encargo.
- **Control de mutaciones:** 14 de 14 errores introducidos fueron detectados.
- **Determinismo:** dos construcciones en procesos distintos producen los mismos SHA-256.
- **Integridad:** 1.130 de 1.130 archivos coinciden con el manifiesto del cierre 34-35. HEAD sigue en 745d689.

# 6. Hallazgos que corrigen o amplían el diseño

| Hallazgo | Consecuencia |
|---|---|
| Las imputaciones en las generales son 927 (5,8 %), y no 665 (4,2 %), al contar el IMC | Cifra corregida en el protocolo ajustado |
| RobustScaler no falla con IQR = 0 | La justificación pasa a ser la adecuación al diseño |
| S-EJE afecta a 75 participantes (14,2 %) | Es una sensibilidad grande: su ajuste queda en 454 |
| S-BLOQUE multiplicaría el IMC por 2,70 o 3,09 | Debe interpretarse con cuidado, porque la mitad de esa columna es imputada |
| 22 respuestas laborales son faltantes, no «no aplica» | Se agrega ese estado a la procedencia |
| `prince` no congela proporciones al proyectar una sola fila | No debe usarse para proyectar participantes en la Fase 40 |
| `explained_variance_` de scikit-learn usa n − 1 | La Fase 37 debe convertirla para informar la inercia de FAMD |

# 7. Límites

- **Datos sintéticos:** los parámetros valen para este conjunto, no para usuarias reales.
- **Sin ajustar:** no se sabe aún si hay estructura de clústeres, y las asociaciones débiles permiten dudarlo (424 de 435 pares bajo |0,2|).
- **Supuestos:** la equidistancia de los códigos y el umbral del 5 % son convenciones que se contrastan con sensibilidades no ejecutadas todavía.
- **Límites de plausibilidad:** los rangos para rechazar valores imposibles son un criterio técnico mío, a revisar en la Fase 40.
- **Referencias:** se citan de memoria y deben verificarse antes de la tesis.

# 8. Entregables

| N.º | Entregable | Ubicación en `analisis/fase36/` |
|---|---|---|
| 1 | Protocolo 36A ajustado | `informes/01_protocolo_fase36A_ajustado.docx` |
| 2 | Matrices 36B | `matrices/` |
| 3 | Artefactos de transformación | `artefactos/` y `transformador.py` |
| 4 | Informe técnico | `informes/04_informe_tecnico_codificacion_escalado.docx` |
| 5 | Registro de procedencia | `informes/05_registro_procedencia_imputaciones.md` y `procedencia/` |
| 6 | Resultados de pruebas | `informes/06_resultados_pruebas.md` y `pruebas/` |
| 7 | Informe de integridad | `informes/07_informe_integridad.md` e `integridad/` |
| 8 | Informe de cierre | `informes/08_informe_cierre_fase36B.docx` |
| 9 | Pendientes para la Fase 37 | `informes/09_pendientes_fase37.md` |

# 9. Siguiente paso

La Fase 37 no se inició. Antes de ejecutarla hay que fijar las reglas de decisión de D-13, sin ver resultados.
