# Fase 39: índice de entregables

**Conclusión:** resultado C. Las asociaciones son débiles o compatibles con el azar y no se identifican diferencias suficientemente consistentes.

| N.º | Entregable | Archivos |
|---|---|---|
| 1 | Índice de entregables | `informes/01_indice_entregables.md` |
| 2 | Protocolo sellado | `informes/02_protocolo_39.docx`, `protocolo/01_protocolo_39.md`, `protocolo/sello_protocolo.json`, `protocolo/02_modificaciones_posteriores.md` |
| 3 | Integridad inicial | `informes/03_integridad_inicial.md`, `integridad/integridad_inicial.json` |
| 4 | Diccionario de estratos | `informes/04_diccionario_estratos.docx`, `preparacion/diccionario_estratos.csv`, `preparacion/pertenencia_estratos.csv` |
| 5 | Tamaños y frecuencias basales | `informes/05_tamanos_frecuencias_basales.docx`, `preparacion/diferencias_basales.csv` |
| 6 | Preparación de las matrices condicionadas | `informes/06_preparacion_matrices_condicionadas.docx`, `preparacion/matrices/`, `preparacion/verificacion_codificacion.json` |
| 7 | Reglas por trabajo | `informes/07_reglas_por_trabajo.docx`, `reglas/trabajo/`, `comparacion/comparacion_trabajo.csv` |
| 8 | Reglas por pareja | `informes/08_reglas_por_pareja.docx`, `reglas/pareja/`, `comparacion/comparacion_pareja.csv` |
| 9 | Reglas por ejercicio | `informes/09_reglas_por_ejercicio.docx`, `reglas/ejercicio/`, `comparacion/comparacion_ejercicio.csv` |
| 10 | Reglas por cuidado | `informes/10_reglas_por_cuidado.docx`, `reglas/cuidado/`, `comparacion/comparacion_cuidado.csv` |
| 11 | Referencias nulas por estrato | `informes/11_referencias_nulas_estrato.docx`, `referencia_nula/` |
| 12 | Comparación formal entre estratos | `informes/12_comparacion_formal_estratos.docx`, `comparacion/` |
| 13 | Análisis de redundancia | `informes/13_redundancia.docx`, `redundancia/` |
| 14 | Sensibilidades | `informes/14_sensibilidades.docx`, `sensibilidades/` |
| 15 | Comparación exploratoria A y B1 | `informes/15_comparacion_exploratoria_A_B1.docx`, `ab1/` |
| 16 | Figuras y tablas | `informes/16_figuras_tablas.docx`, `figuras/` |
| 17 | Informe de pruebas | `informes/17_informe_pruebas.md`, `pruebas/` |
| 18 | Integridad final | `informes/18_informe_integridad_final.md`, `integridad/` |
| 19 | Informe metodológico de cierre | `informes/19_informe_cierre_39.docx`, `resultados/conclusion_39.json` |
| 20 | Nota para implementar la lógica del tablero | `informes/20_nota_logica_tablero.docx` |


**Resumen:** `informes/resumen_39.json`.

**Scripts:** `scripts/`. Orden de ejecución:

1. `sellar_protocolo_39.py`
2. `integridad_39.py inicial`
3. `preparacion_39.py`
4. `estratos_39.py`
5. `ab1_39.py`
6. `sensibilidades_39.py`
7. `significacion_39.py` (exploratorio)
8. `graficos_39.py`
9. `pruebas_39.py --mutaciones`
10. `generar_informes_39.py`
11. `verificar_informes_39.py`
12. `integridad_39.py final`
13. `manifiesto_39.py`

Las etapas de cálculo corren bajo `vigilar_memoria.py`.
