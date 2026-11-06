# Fase 37D: índice de entregables

| N.º | Entregable | Archivo |
|---|---|---|
| 1 | Protocolo sellado | `informes/01_protocolo_37D.docx`, `protocolo/01_protocolo_37D.md`, `protocolo/sello_protocolo.json` |
| 1b | Nota posterior al sellado | `informes/01b_nota_posterior.docx`, `protocolo/02_nota_posterior_37D.md` |
| 2 | Informe de integridad inicial | `informes/02_integridad_inicial.md` |
| 3 | Diccionario de variables | `informes/03_diccionario_variables.docx`, `diccionario/diccionario_variables_37D.csv` |
| 4 | Caracterización general | `informes/04_caracterizacion_general.docx` |
| 5 | Segmentos A | `informes/05_caracterizacion_segmentos_A.docx` |
| 6 | Segmentos B1 | `informes/06_caracterizacion_segmentos_B1.docx` |
| 7 | Características individuales frente al MRS | `informes/07_individual_frente_a_MRS.docx` |
| 8 | MRS por segmento A | `informes/08_mrs_por_segmento_A.docx` |
| 9 | MRS por segmento B1 | `informes/09_mrs_por_segmento_B1.docx` |
| 10 | Comparación A, B1 y sin segmentar | `informes/10_comparacion_tres_perspectivas.docx` |
| 11 | Sensibilidades y limitaciones | `informes/11_sensibilidades_limitaciones.docx` |
| 12 | Figuras y tablas | `informes/12_figuras_tablas.docx`, `figuras/`, `resultados/` |
| 13 | Informe de pruebas | `informes/13_informe_pruebas.md` |
| 14 | Informe de integridad final | `informes/14_informe_integridad_final.md` |
| 15 | Informe final | `informes/15_informe_final_37D.docx` |
| 16 | Nota para las Fases 38 y 39 | `informes/16_nota_fases_38_39.docx` |

**Respaldo:** `resultados/descripcion/`, `resultados/individual/`, `resultados/segmentos/` y `resultados/resumen_37D.json`.

**Scripts:** `scripts/`. Orden de ejecución:

1. `sellar_protocolo_37d.py`
2. `integridad_37d.py inicial`
3. `descripcion_37d.py`
4. `individual_37d.py`
5. `segmentos_37d.py`
6. `graficos_37d.py`
7. `pruebas_37d.py --mutaciones`
8. `generar_informes_37d.py`
9. `integridad_37d.py final`
10. `manifiesto_37d.py`
