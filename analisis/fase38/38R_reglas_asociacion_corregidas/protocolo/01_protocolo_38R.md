# Protocolo de la Fase 38R: reglas de asociación generales, versión correctiva

Se redacta y se sella con SHA-256 **antes de calcular ninguna regla**. No se modifica después del sello; cualquier ajuste posterior irá en una nota aparte, rotulada como exploratoria.

## 1. Objeto

La Fase 38 incorporó en su matriz principal `prevision` y `usa_medicamentos_diabetes`, excluidas del modelado por decisiones definitivas de las Fases 35 y 36. El origen está en la constante `PRINCIPAL` de `fase38/38_reglas_asociacion_generales/scripts/nucleo_38.py:50-56` y en la sección 3.1 de su protocolo.

La Fase 38R elimina esas variables y repite el procedimiento sin cambiar sus condiciones. **La Fase 38 original se conserva intacta como evidencia histórica.** Esta fase no incluye la Fase 39R, cambios en la Fase 40, actualización de la tesis, commits ni pushes.

## 2. Procedimiento heredado

Rige sin cambios el protocolo histórico `fase38/38_reglas_asociacion_generales/protocolo/01_protocolo_38.md` (sello `9f9614115801805f9cde6c1586a8d7571ee44116c18ac7638025a645ee7f5a82`) en sus secciones 4 (ítems, reglas R1 a R7), 5 (diseño de reglas), 6 (algoritmos), 7 (umbrales y medidas), 8 (referencia nula), 9 (criterios, clasificación y estabilidad) y 12 (recursos). Las funciones históricas `algoritmos_38.py`, `evaluacion_38.py` y `nucleo_38.py` se **importan sin modificar**.

Se conservan en particular:

- Apriori, FP-Growth y enumeración exhaustiva como verificación; las sensibilidades usan FP-Growth.
- Antecedentes de 1 a 3 condiciones en la principal; `n_A ≥ 53` y `n_AC ≥ 27`.
- Semilla 42; 1.000 permutaciones por configuración; 200 submuestras del 80 %, solo en la principal.
- Regla marcada `|c − p₀| ≥ 0,10`; mejora mínima 0,05; estabilidad 70 % y 95 %; alfa 0,05 de Westfall-Young.
- Clases 1 a 6, en el mismo orden.

**Convicción.** La instrucción de la 38R la menciona entre las métricas, pero el protocolo histórico no la define ni la usa (sección 7.2). Para no introducir un método nuevo, se calcula solo como anexo descriptivo en `reglas/conviccion_descriptiva_anexo.csv`, con `(1 − p₀) / (1 − c)`. No interviene en umbrales, reglas marcadas ni clases.

## 3. Variables

**Fuente obligatoria:** `reunion_2026-11-03/revision_33_variables/fase35a/predictores_elegibles_33.csv`, contrastada al ejecutar con `complemento_bootstrap_33/configuracion/candidatas_y_exclusiones.csv`, `reunion_2026-11-03/revision_33_variables/protocolo_revision_33.md`, `cierre_fases_34_35/informes/informe_preprocesamiento_fase35_revisado.md`, `fase36/configuracion_fase36.py`, `fase36/informes/fuentes/01_protocolo_fase36A_ajustado.md` y `fase36/artefactos/P2/esquema_variables.json`.

**Exclusiones definitivas**, en toda configuración: `prevision`, `usa_medicamentos_diabetes`, `doble_carga`. No pueden volver por estar disponibles en el conjunto limpio, aparecer en resultados descriptivos o haberse usado en fases históricas.

**Matriz principal: 29 variables generales.** Son las 30 de población general de la Fase 35 menos `imc`:

`trabaja_actualmente`, `tiene_pareja`, `cantidad_personas_cuida`, `dias_ejercicio_semana`, `frecuencia_aerobico`, `frecuencia_bajo_impacto`, `frecuencia_fuerza`, `horas_sedentarismo`, `quien_prepara_comidas`, `carnes_semana`, `falta_tiempo_influye`, `frecuencia_comida_fuera`, `frutas_dia`, `golosinas_semana`, `jugos_gaseosas_dia`, `lacteos_dia`, `legumbres_semana`, `panes_dia`, `pescado_semana`, `platos_verduras_dia`, `vasos_agua_dia`, `tabaco_frecuencia`, `alcohol_frecuencia`, `edad`, `operada_no_mas_hijos`, `usa_medicamentos_presion`, `tiene_actividad_sexual`, `distension_abdominal`, `evacuacion_intestinal`.

Con las transformaciones originales se esperan **90 ítems binarios** (94 históricos menos `med_diabetes=NO`, `med_diabetes=SI`, `prevision=FONASA` y `prevision=ISAPRE`).

**Reservadas para sensibilidades:** `imc` (S8b), `lugar_trabajo_comprensivo` y `estres_entorno_laboral` (S7a), `sobrecarga_fisica_emocional` (S7b). Esta separación no significa falta de relevancia estadística.

**Consecuente:** `severo_mrs`, nunca antecedente.

## 4. Poblaciones

| Configuración | n | Definición | Respaldo documental |
|---|---|---|---|
| Principal y S1 a S6 | 529 | MRS completo: 281 severas y 248 no severas | Fase 36, `identificadores.csv` |
| S7a | 287 | Trabajadoras con respuestas en el módulo laboral | Protocolo 35B, línea 19; Fase 36 ajustado, §10 |
| S7a-309 | 309 | Todas las trabajadoras, sensibilidad ampliada. Las 22 con trabajo imputado no tienen ítems laborales (tratamiento histórico de faltantes) | Fase 38, S7a |
| S7b | 239 | Cuidadoras con sobrecarga observada | Fase 36 ajustado, §10 |
| S7b-251 | 251 | Todas las cuidadoras, con 12 sobrecargas imputadas, solo como sensibilidad | Fase 36 ajustado, §10 |
| S8a y S8b | 267 | IMC observado y MRS completo | Fase 38, S8 |

**Matiz del rótulo de S7a.** De las 287, 263 tienen ambas respuestas laborales en estado observada; las otras 24 tienen al menos una imputada en la limpieza. La Fase 36 define 287 como población principal del módulo y 263 como sensibilidad. Esta fase usa 287 según lo indicado y **no ejecuta la versión de 263**, que no fue solicitada.

Las poblaciones y los faltantes se comprueban por configuración antes de buscar reglas.

## 5. Sensibilidades

Todas con FP-Growth, los criterios de la sección 2 y 1.000 permutaciones propias. **Ningún resultado histórico se reutiliza.** Umbrales: 10 % y 5 % de cada población, salvo S3.

| Código | Cambio respecto de la principal | Comparable con la histórica |
|---|---|---|
| S1 | Sin valores imputados, deducidos ni con pregunta madre imputada | S1: misma definición |
| S2a / S2b | Categorías originales / agrupación gruesa | S2a / S2b, menos las dos variables |
| S3-bajo / S3-alto | Umbrales 27 y 14 / 80 y 40 | Sí, menos las dos variables |
| S4-1 / S4-2 | 1 o hasta 2 condiciones | Sí, menos las dos variables |
| S5 | Sin frecuencias de ejercicio | Sí, menos las dos variables |
| S6 | Sin variables próximas a síntomas | Sí, menos las dos variables |
| S7a | Laboral en 287 | Sin equivalente: cambia la población |
| S7a-309 | Laboral en 309 | S7a histórica, menos las dos variables |
| S7b | Sobrecarga en 239 | Sin equivalente: cambia la población |
| S7b-251 | Sobrecarga en 251 | S7b histórica, menos las dos variables |
| S8a / S8b | IMC observado, sin y con IMC | Sí, menos las dos variables |

Se añaden las lecturas de 287 frente a 309 y 239 frente a 251.

## 6. Barreras

`scripts/barreras_38r.py` detiene el proceso, sin corregir nada, si:

1. Las 29 variables no coinciden exactamente con las autorizadas, leídas de las fuentes de la sección 3.
2. Aparece `prevision`, `usa_medicamentos_diabetes` o `doble_carga`.
3. Un ítem deriva de ellas, por su nombre (incluidas formas transformadas) o porque su vector, o el complemento, reproduce una de sus categorías en las 529.
4. Un antecedente es del MRS, posterior a los síntomas o una etiqueta de segmentación, por nombre o por contenido.
5. Una población o el tratamiento de sus faltantes no corresponde.
6. Una tabla de reglas contiene una variable no autorizada.

Se declara una coincidencia conocida: en S2b, `dias_ejercicio=3_o_mas_dias` es idéntico por definición al primer paso de la regla B1. Es un ítem de ejercicio, no una etiqueta, y existe igual en la Fase 38 histórica.

## 7. Etapas

A: preparación. B: reglas y comparación de las conservadas. C: robustez y sensibilidades. D: integridad y pruebas.

## 8. Integridad

Los controles históricos exigen HEAD `745d689` y `src/` sin cambios, por lo que ya no pueden cumplirse. **No se desactivan ni se modifican.** Se usa un control correctivo independiente, `scripts/integridad_38r.py`, además de la prueba `test_40b1_proteccion_historica.py`.

Los manifiestos de las Fases 34 a 39 no deben cambiar. Tampoco los archivos pendientes de la Fase 40, respaldados en `datos/respaldos/2026-11-08_antes_38R/`.

## 9. Reglas de lectura

- Solo una regla de clase 6 cumple los criterios de destacada.
- Una regla no se llama robusta si no supera todas las comprobaciones originales, incluida su lectura en las sensibilidades.
- Si ninguna regla queda en clase 6: «no se encontraron reglas suficientemente sólidas para destacar».
- Datos sintéticos, análisis no ciego y misma muestra para descubrir y evaluar: las limitaciones históricas siguen vigentes.
