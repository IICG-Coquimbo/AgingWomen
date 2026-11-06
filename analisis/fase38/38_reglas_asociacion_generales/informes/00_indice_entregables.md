# Fase 38: índice de entregables

| N.º | Entregable | Archivo |
|---|---|---|
| 1 | Protocolo sellado | `informes/01_protocolo_38.docx`, `protocolo/01_protocolo_38.md`, `protocolo/sello_protocolo.json` |
| 2 | Auditoría de integridad inicial | `informes/02_integridad_inicial.md` |
| 3 | Diccionario de variables y categorías | `informes/03_diccionario_variables_categorias.docx`, `preparacion/diccionario_variables_categorias.csv`, `preparacion/diccionario_items.csv` |
| 4 | Agrupamiento de categorías poco frecuentes | `informes/04_agrupacion_categorias_escasas.docx`, `preparacion/agrupaciones_escasas.csv`, `preparacion/categorias_escasas_detalle.csv` |
| 5 | Matriz transaccional y trazabilidad | `informes/05_matriz_transaccional_trazabilidad.docx`, `preparacion/matriz_transaccional_principal.csv`, `preparacion/trazabilidad_transformaciones.csv` |
| 6 | Equivalencia Apriori/FP-Growth | `informes/06_equivalencia_apriori_fpgrowth.docx`, `reglas/equivalencia_*.csv`, `reglas/entorno.json` |
| 7 | Reglas generales | `informes/07_reglas_generales.docx`, `reglas/reglas_principal.csv`, `reglas/reglas_destacadas.csv` |
| 8 | Soporte, confianza, lift y cobertura | `informes/08_soporte_confianza_lift_cobertura.docx`, `reglas/cobertura.csv` |
| 9 | Redundancia | `informes/09_redundancia.docx`, `reglas/redundantes_marcadas.csv`, `reglas/familias_marcadas.csv` |
| 10 | Estabilidad | `informes/10_estabilidad.docx`, `estabilidad/` |
| 11 | Referencia nula | `informes/11_referencia_nula.docx`, `referencia_nula/nula_principal.csv` |
| 12 | Sensibilidades | `informes/12_sensibilidades.docx`, `sensibilidades/` |
| 13 | Figuras y tablas | `informes/13_figuras_tablas.docx`, `figuras/` |
| 14 | Informe de pruebas | `informes/14_informe_pruebas.md`, `pruebas/` |
| 15 | Integridad final | `informes/15_informe_integridad_final.md`, `integridad/` |
| 16 | Informe metodológico de cierre | `informes/16_informe_cierre_38.docx` |
| 17 | Nota para la Fase 39 | `informes/17_nota_fase_39.docx` |
| 18 | Índice de entregables | `informes/00_indice_entregables.md` |

**Resumen:** `reglas/resumen_principal.json` y `sensibilidades/resumen_sensibilidades.csv`.

**Scripts:** `scripts/`. Orden de ejecución:

1. `sellar_protocolo_38.py`
2. `integridad_38.py inicial`
3. `preparacion_38.py`
4. `reglas_38.py`
5. `sensibilidades_38.py`
6. `graficos_38.py`
7. `pruebas_38.py --mutaciones`
8. `generar_informes_38.py`
9. `verificar_informes_38.py`
10. `integridad_38.py final`
11. `manifiesto_38.py`

Las etapas de cálculo corren bajo `vigilar_memoria.py`.
