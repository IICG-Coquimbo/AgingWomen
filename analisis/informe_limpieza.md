# Informe de limpieza del dataset (Fase 32)

Generado por `analisis/limpiar_dataset.py` el 2026-10-11. Volver a ejecutar el script regenera este informe y los archivos de salida.

- Entrada: `datos/dataset_menopausia_sucio.csv` — 511 filas.
- Salida: `datos/limpio/dataset_menopausia_limpio.csv` — **495 filas**.
- Excluidas: 16 filas (`datos/limpio/excluidas.csv`, con el motivo).
- Diccionario: `datos/limpio/diccionario_variables.csv` (faltantes y tratamiento por variable).

Los códigos válidos, la lógica condicional y los campos solo para personal de salud se
leen del código de la plataforma (`models.py`, `condicionales.py`, `campos_por_rol.py`),
así la limpieza nunca contradice lo que la encuesta acepta.

## 1. Filas excluidas

| Motivo | Filas |
|---|---|
| duplicado exacto | 6 |
| RUT repetido (versión antigua) | 5 |
| edad no verificable (fecha de nacimiento imposible) | 2 |
| menor de 40 sin excepción de edad | 2 |
| mayor de 65 años | 1 |

## 2. Correcciones por paso

Una fila por (paso, variable, motivo). "Ejemplos" muestra valores originales.

| Paso | Variable | Motivo | Celdas | Ejemplos |
|---|---|---|---|---|
| 1 formato | `comuna` | espacios sobrantes | 4 |  |
| 1 formato | `genero` | espacios sobrantes | 4 |  |
| 1 formato | `nivel_educacion` | espacios sobrantes | 3 |  |
| 1 formato | `prevision` | espacios sobrantes | 1 |  |
| 1 formato | `usa_medicamentos_presion` | espacios sobrantes | 1 |  |
| 1 formato | `vdrl_rpr` | espacios sobrantes | 1 |  |
| 3 centinelas | `alcohol_frecuencia` | texto "sin dato" | 1 | NA |
| 3 centinelas | `alcohol_frecuencia` | número "sin dato" (-1/99/999/9999) | 1 | 99 |
| 3 centinelas | `cambio_relacion_pareja_menopausia` | texto "sin dato" | 2 | N/A |
| 3 centinelas | `cambio_relacion_pareja_menopausia` | número "sin dato" (-1/99/999/9999) | 4 | 999 |
| 3 centinelas | `circunferencia_cintura_cm` | texto "sin dato" | 2 | NA |
| 3 centinelas | `circunferencia_cintura_cm` | número "sin dato" (-1/99/999/9999) | 2 | 999 |
| 3 centinelas | `considera_informacion_suficiente` | número "sin dato" (-1/99/999/9999) | 1 | 99 |
| 3 centinelas | `dias_ejercicio_semana` | texto "sin dato" | 1 | NA |
| 3 centinelas | `dias_ejercicio_semana` | número "sin dato" (-1/99/999/9999) | 1 | -1 |
| 3 centinelas | `distension_abdominal` | texto "sin dato" | 2 | NA, sin dato |
| 3 centinelas | `distension_abdominal` | número "sin dato" (-1/99/999/9999) | 1 | 999 |
| 3 centinelas | `estres_entorno_laboral` | texto "sin dato" | 3 | N/A, NA |
| 3 centinelas | `estres_entorno_laboral` | número "sin dato" (-1/99/999/9999) | 2 | -1, 999 |
| 3 centinelas | `evacuacion_intestinal` | texto "sin dato" | 1 | N/A |
| 3 centinelas | `evacuacion_intestinal` | número "sin dato" (-1/99/999/9999) | 4 | -1, 999 |
| 3 centinelas | `falta_tiempo_influye` | número "sin dato" (-1/99/999/9999) | 1 | 99.0 |
| 3 centinelas | `fecha_ultima_menstruacion` | texto "sin dato" | 5 | N/A, no recuerdo |
| 3 centinelas | `frecuencia_ausencias` | número "sin dato" (-1/99/999/9999) | 1 | 99.0 |
| 3 centinelas | `frecuencia_comida_fuera` | número "sin dato" (-1/99/999/9999) | 1 | -1.0 |
| 3 centinelas | `glicemia_mg_dl` | número "sin dato" (-1/99/999/9999) | 1 | 9999.0 |
| 3 centinelas | `golosinas_semana` | número "sin dato" (-1/99/999/9999) | 1 | -1.0 |
| 3 centinelas | `horas_sedentarismo` | número "sin dato" (-1/99/999/9999) | 1 | 999.0 |
| 3 centinelas | `lacteos_dia` | número "sin dato" (-1/99/999/9999) | 1 | -1.0 |
| 3 centinelas | `marihuana_frecuencia` | texto "sin dato" | 1 | NA |
| 3 centinelas | `marihuana_frecuencia` | número "sin dato" (-1/99/999/9999) | 2 | 999 |
| 3 centinelas | `peso_kg` | texto "sin dato" | 2 | N/A, NA |
| 3 centinelas | `peso_kg` | número "sin dato" (-1/99/999/9999) | 3 | -1 |
| 3 centinelas | `platos_verduras_dia` | texto "sin dato" | 1 | NA |
| 3 centinelas | `rendimiento_afectado` | número "sin dato" (-1/99/999/9999) | 1 | 99.0 |
| 3 centinelas | `tabaco_frecuencia` | texto "sin dato" | 1 | - |
| 3 centinelas | `tabaco_frecuencia` | número "sin dato" (-1/99/999/9999) | 2 | -1, 999 |
| 3 centinelas | `talla_actual_cm` | número "sin dato" (-1/99/999/9999) | 1 | 999 |
| 3 centinelas | `tiene_actividad_sexual` | texto "sin dato" | 4 | -, N/A, NA |
| 3 centinelas | `usa_antidepresivos` | texto "sin dato" | 2 | NA |
| 3 centinelas | `vasos_agua_dia` | texto "sin dato" | 1 | sin dato |
| 4 códigos | `bienestar_trabajo_afectado` | valor fuera de las opciones → vacío | 1 | 7.0 |
| 4 códigos | `comuna` | ortografía oficial | 13 |  |
| 4 códigos | `considera_informacion_suficiente` | valor fuera de las opciones → vacío | 1 | 6 |
| 4 códigos | `cuida_otras_personas` | recodificado al código del sistema | 1 | N |
| 4 códigos | `desea_mas_informacion_apoyo` | recodificado al código del sistema | 5 | 1, Sí, si, sí |
| 4 códigos | `genero` | recodificado al código del sistema | 10 | FEMENINO, Femenino, Mujer, femenino |
| 4 códigos | `nivel_educacion` | recodificado al código del sistema | 6 | Educación Básica Completa, Educación Media Completa, b_com, b_inc, m_com, u_com |
| 4 códigos | `nivel_informacion_servicios` | valor fuera de las opciones → vacío | 1 | 6 |
| 4 códigos | `operada_no_mas_hijos` | recodificado al código del sistema | 2 | No, si |
| 4 códigos | `pregunta_1` | valor fuera de las opciones → vacío | 1 | 9 |
| 4 códigos | `pregunta_11` | valor fuera de las opciones → vacío | 1 | 5 |
| 4 códigos | `pregunta_2` | valor fuera de las opciones → vacío | 1 | 5 |
| 4 códigos | `prevision` | recodificado al código del sistema | 4 | Fonasa, Isapre, fonasa, isapre |
| 4 códigos | `realiza_aerobico` | recodificado al código del sistema | 1 | si |
| 4 códigos | `realiza_bajo_impacto` | recodificado al código del sistema | 1 | S |
| 4 códigos | `region_residencia` | recodificado al código del sistema | 2 | Atacama, Coquimbo |
| 4 códigos | `rendimiento_afectado` | valor fuera de las opciones → vacío | 1 | 0.0 |
| 4 códigos | `tiene_actividad_sexual` | recodificado al código del sistema | 3 | 0, N, S |
| 4 códigos | `trabaja_actualmente` | recodificado al código del sistema | 6 | 1, FALSE, Sí, TRUE, verdadero |
| 4 códigos | `usa_antidepresivos` | recodificado al código del sistema | 1 | no |
| 4 códigos | `usa_medicamentos_diabetes` | recodificado al código del sistema | 1 | N |
| 4 códigos | `usa_medicamentos_presion` | recodificado al código del sistema | 3 | No, Sí |
| 4 códigos | `usa_metodo_anticonceptivo` | recodificado al código del sistema | 2 | No, S |
| 4 códigos | `usa_terapia_hormonal` | recodificado al código del sistema | 1 | No |
| 5 mediciones | `circunferencia_cintura_cm` | unidad o coma decimal quitada | 2 | 102 cm, 103 cm |
| 5 mediciones | `circunferencia_cintura_cm` | fuera del rango plausible 50-170 → vacío | 2 | 10.39, 910.0 |
| 5 mediciones | `colesterol_hdl_mg_dl` | fuera del rango plausible 15-150 → vacío | 1 | 210.0 |
| 5 mediciones | `colesterol_total_mg_dl` | fuera del rango plausible 80-500 → vacío | 2 | 21.0, 23.0 |
| 5 mediciones | `glicemia_mg_dl` | fuera del rango plausible 40-600 → vacío | 1 | 0.0 |
| 5 mediciones | `horas_sedentarismo` | fuera del rango plausible 0-24 → vacío | 3 | 25.0, 72.0 |
| 5 mediciones | `peso_kg` | unidad o coma decimal quitada | 4 | 53,0, 66,2, 73,3, 81.0 kg |
| 5 mediciones | `peso_kg` | fuera del rango plausible 30-200 → vacío | 2 | 780.0, 994.0 |
| 5 mediciones | `presion_*` | diastólica ≥ sistólica → ambas vacías | 1 |  |
| 5 mediciones | `presion_diastolica` | cmHg → mmHg (×10) | 2 | 7.0, 8.0 |
| 5 mediciones | `presion_sistolica` | cmHg → mmHg (×10) | 2 | 12.0, 13.0 |
| 5 mediciones | `presion_sistolica` | fuera del rango plausible 70-250 → vacío | 2 | 65.0, 310.0 |
| 5 mediciones | `talla_actual_cm` | unidad o coma decimal quitada | 2 | 147 cm, 159 cm |
| 5 mediciones | `talla_actual_cm` | metros → centímetros (×100) | 2 | 1.56, 1.72 |
| 5 mediciones | `talla_actual_cm` | fuera del rango plausible 120-200 → vacío | 2 | 1620.0 |
| 5 mediciones | `trigliceridos_mg_dl` | fuera del rango plausible 20-1500 → vacío | 1 | 0.0 |
| 6 fechas | `fecha_mamografia` | formato DD/MM/AAAA → AAAA-MM-DD | 3 |  |
| 6 fechas | `fecha_mamografia` | posterior a la evaluación → vacío | 1 |  |
| 6 fechas | `fecha_nacimiento` | formato DD/MM/AAAA → AAAA-MM-DD | 2 |  |
| 6 fechas | `fecha_nacimiento` | posterior a la evaluación → vacío | 1 |  |
| 6 fechas | `fecha_ultima_menstruacion` | normalizada a AAAA-MM / AAAA | 16 |  |
| 6 fechas | `fecha_ultima_menstruacion` | texto ilegible → vacío | 2 |  |
| 6 fechas | `fecha_ultimo_empa` | formato DD/MM/AAAA → AAAA-MM-DD | 2 |  |
| 6 fechas | `fecha_ultimo_empa` | posterior a la evaluación → vacío | 1 |  |
| 6 fechas | `fecha_ultimo_pap` | formato DD/MM/AAAA → AAAA-MM-DD | 3 |  |
| 6 fechas | `fecha_ultimo_pap` | posterior a la evaluación → vacío | 1 |  |
| 8 condicionales | `bienestar_trabajo_afectado` | respondida sin trabajar → borrada | 4 |  |
| 8 condicionales | `cambio_relacion_pareja_menopausia` | pregunta oculta (depende de tiene_pareja) → borrada | 6 |  |
| 8 condicionales | `cantidad_personas_cuida` | pregunta oculta (depende de cuida_otras_personas) → borrada | 3 |  |
| 8 condicionales | `colesterol_hdl_mg_dl` | campo solo profesional en encuesta autoaplicada → borrado | 11 |  |
| 8 condicionales | `colesterol_total_mg_dl` | campo solo profesional en encuesta autoaplicada → borrado | 10 |  |
| 8 condicionales | `conoce_sistema_publico_climaterio` | pregunta oculta (depende de prevision) → borrada | 3 |  |
| 8 condicionales | `considera_informacion_suficiente` | pregunta oculta (depende de prevision) → borrada | 135 |  |
| 8 condicionales | `estres_entorno_laboral` | respondida sin trabajar → borrada | 4 |  |
| 8 condicionales | `evaluacion_atencion_recibida` | pregunta oculta (depende de ha_consultado_por_sintomas) → borrada | 2 |  |
| 8 condicionales | `fecha_ecotomografia_mamaria` | campo solo profesional en encuesta autoaplicada → borrado | 35 |  |
| 8 condicionales | `fecha_mamografia` | campo solo profesional en encuesta autoaplicada → borrado | 128 |  |
| 8 condicionales | `fecha_ultimo_pap` | campo solo profesional en encuesta autoaplicada → borrado | 136 |  |
| 8 condicionales | `frecuencia_ausencias` | respondida sin trabajar → borrada | 4 |  |
| 8 condicionales | `glicemia_mg_dl` | campo solo profesional en encuesta autoaplicada → borrado | 11 |  |
| 8 condicionales | `ha_consultado_por_sintomas` | pregunta oculta (depende de prevision) → borrada | 3 |  |
| 8 condicionales | `ha_tenido_dificultades_acceso` | pregunta oculta (depende de prevision) → borrada | 3 |  |
| 8 condicionales | `lugar_trabajo_comprensivo` | respondida sin trabajar → borrada | 4 |  |
| 8 condicionales | `menstruacion_llega` | pregunta oculta (depende de fecha_ultima_menstruacion) → borrada | 5 |  |
| 8 condicionales | `nivel_informacion_servicios` | pregunta oculta (depende de prevision) → borrada | 134 |  |
| 8 condicionales | `presion_diastolica` | campo solo profesional en encuesta autoaplicada → borrado | 17 |  |
| 8 condicionales | `presion_sistolica` | campo solo profesional en encuesta autoaplicada → borrado | 17 |  |
| 8 condicionales | `rendimiento_afectado` | respondida sin trabajar → borrada | 4 |  |
| 8 condicionales | `resultado_birads` | campo solo profesional en encuesta autoaplicada → borrado | 130 |  |
| 8 condicionales | `resultado_pap` | campo solo profesional en encuesta autoaplicada → borrado | 135 |  |
| 8 condicionales | `riesgo_cv_atp3` | campo solo profesional en encuesta autoaplicada → borrado | 1 |  |
| 8 condicionales | `sabe_donde_acudir` | pregunta oculta (depende de prevision) → borrada | 3 |  |
| 8 condicionales | `talla_maxima_cm` | campo solo profesional en encuesta autoaplicada → borrado | 236 |  |
| 8 condicionales | `tipo_informacion_apoyo_deseado` | pregunta oculta (depende de desea_mas_informacion_apoyo) → borrada | 2 |  |
| 8 condicionales | `tipo_metodo_anticonceptivo` | pregunta oculta (depende de usa_metodo_anticonceptivo) → borrada | 28 |  |
| 8 condicionales | `tipo_sangrado` | pregunta oculta (depende de fecha_ultima_menstruacion) → borrada | 2 |  |
| 8 condicionales | `trabaja_actualmente` | vacío pero respondió Trabajo → True | 1 |  |
| 8 condicionales | `trigliceridos_mg_dl` | campo solo profesional en encuesta autoaplicada → borrado | 11 |  |
| 8 condicionales | `usa_metodo_anticonceptivo` | pregunta oculta (depende de fecha_ultima_menstruacion) → borrada | 325 |  |
| 8 condicionales | `vdrl_rpr` | campo solo profesional en encuesta autoaplicada → borrado | 5 |  |
| 9 imputación | `alcohol_frecuencia` | imputado con mediana (1) | 11 |  |
| 9 imputación | `bebidas_energeticas_dia` | imputado con mediana (1) | 6 |  |
| 9 imputación | `bienestar_trabajo_afectado` | imputado con mediana (3) | 3 |  |
| 9 imputación | `cambio_relacion_pareja_menopausia` | imputado con mediana (2) | 8 |  |
| 9 imputación | `cantidad_personas_cuida` | imputado con mediana (2) | 2 |  |
| 9 imputación | `carnes_semana` | imputado con mediana (3) | 6 |  |
| 9 imputación | `circunferencia_cintura_cm` | imputado con mediana (92.5) | 75 |  |
| 9 imputación | `colesterol_hdl_mg_dl` | imputado con mediana (54) | 39 |  |
| 9 imputación | `colesterol_total_mg_dl` | imputado con mediana (200) | 39 |  |
| 9 imputación | `considera_informacion_suficiente` | imputado con mediana (2) | 2 |  |
| 9 imputación | `cuida_otras_personas` | imputado con moda (NO) | 2 |  |
| 9 imputación | `dias_ejercicio_semana` | imputado con mediana (2) | 6 |  |
| 9 imputación | `distension_abdominal` | imputado con mediana (2) | 6 |  |
| 9 imputación | `estres_entorno_laboral` | imputado con mediana (3) | 10 |  |
| 9 imputación | `evacuacion_intestinal` | imputado con mediana (2) | 6 |  |
| 9 imputación | `falta_tiempo_influye` | imputado con mediana (3) | 7 |  |
| 9 imputación | `frecuencia_ausencias` | imputado con mediana (2) | 3 |  |
| 9 imputación | `frecuencia_comida_fuera` | imputado con mediana (2) | 7 |  |
| 9 imputación | `frutas_dia` | imputado con mediana (2) | 6 |  |
| 9 imputación | `glicemia_mg_dl` | imputado con mediana (95) | 40 |  |
| 9 imputación | `golosinas_semana` | imputado con mediana (3) | 7 |  |
| 9 imputación | `horas_sedentarismo` | imputado con mediana (7) | 11 |  |
| 9 imputación | `jugos_gaseosas_dia` | imputado con mediana (2) | 6 |  |
| 9 imputación | `lacteos_dia` | imputado con mediana (2) | 7 |  |
| 9 imputación | `legumbres_semana` | imputado con mediana (2) | 6 |  |
| 9 imputación | `lugar_trabajo_comprensivo` | imputado con mediana (3) | 2 |  |
| 9 imputación | `marihuana_frecuencia` | imputado con mediana (1) | 14 |  |
| 9 imputación | `menstruacion_llega` | imputado con moda (REGULAR) | 11 |  |
| 9 imputación | `nivel_educacion` | imputado con moda (M_COM) | 3 |  |
| 9 imputación | `panes_dia` | imputado con mediana (3) | 6 |  |
| 9 imputación | `pescado_semana` | imputado con mediana (2) | 6 |  |
| 9 imputación | `peso_kg` | imputado con mediana (71) | 8 |  |
| 9 imputación | `platos_verduras_dia` | imputado con mediana (2) | 10 |  |
| 9 imputación | `presion_diastolica` | imputado con mediana (75) | 13 |  |
| 9 imputación | `presion_sistolica` | imputado con mediana (120) | 15 |  |
| 9 imputación | `pueblo_originario_afro` | imputado con moda (NINGUNO) | 4 |  |
| 9 imputación | `quien_prepara_comidas` | imputado con moda (YO_MAYORIA) | 6 |  |
| 9 imputación | `realiza_aerobico` | imputado con moda (NO) | 2 |  |
| 9 imputación | `realiza_bajo_impacto` | imputado con moda (NO) | 2 |  |
| 9 imputación | `realiza_fuerza` | imputado con moda (NO) | 2 |  |
| 9 imputación | `rendimiento_afectado` | imputado con mediana (2) | 4 |  |
| 9 imputación | `riesgo_cv_atp3` | imputado con moda (BAJO) | 48 |  |
| 9 imputación | `tabaco_frecuencia` | imputado con mediana (1) | 12 |  |
| 9 imputación | `talla_actual_cm` | imputado con mediana (156) | 6 |  |
| 9 imputación | `tiene_actividad_sexual` | imputado con moda (SI) | 9 |  |
| 9 imputación | `tiene_pareja` | imputado con moda (SI) | 4 |  |
| 9 imputación | `tipo_metodo_anticonceptivo` | imputado con moda (ORAL) | 2 |  |
| 9 imputación | `tipo_sangrado` | imputado con moda (MODERADO) | 11 |  |
| 9 imputación | `trabaja_actualmente` | imputado con moda (True) | 2 |  |
| 9 imputación | `trigliceridos_mg_dl` | imputado con mediana (146) | 39 |  |
| 9 imputación | `usa_antidepresivos` | imputado con moda (NO) | 4 |  |
| 9 imputación | `usa_terapia_hormonal` | imputado con moda (NO) | 4 |  |
| 9 imputación | `vasos_agua_dia` | imputado con mediana (3) | 10 |  |
| 10 derivadas | `mrs_*` | MRS incompleto: sin puntaje (fuera del análisis de severidad) | 3 |  |
| 10 derivadas | `perdida_talla_cm` | talla actual > talla máxima → sin dato | 5 |  |

**Notas:**

- 4 filas con comuna que no pertenece a la región declarada (participante_id 116, 147, 154, 407); se dejaron como venían porque no se sabe cuál de los dos datos está mal.

## 3. Datos faltantes y tratamiento

Un vacío es **"no aplica"** cuando la encuesta no habría mostrado la pregunta (lógica
condicional, sección Trabajo sin trabajo, campos solo para personal de salud en encuestas
autoaplicadas, encuesta de satisfacción no respondida). Esos vacíos no se imputan. El %
faltante se calcula solo sobre las filas donde la pregunta aplica.

Reglas: < 5 % se imputa; 5-30 % se imputa y se
agrega la columna `<variable>_imputado` (1 = imputado); > 30 % no se usa para modelar.
Moda para categóricas, mediana para ordinales y continuas. El MRS nunca se imputa.

| Variable | Ámbito | Aplica a | Faltan | % | Tratamiento |
|---|---|---|---|---|---|
| `resultado_birads` | subgrupo profesional | 259 | 119 | 45.9 | > 30 %: no se modela |
| `resultado_pap` | subgrupo profesional | 259 | 108 | 41.7 | > 30 %: no se modela |
| `riesgo_cv_atp3` | subgrupo profesional | 259 | 48 | 18.5 | imputada (moda = BAJO) + marca riesgo_cv_atp3_imputado |
| `glicemia_mg_dl` | subgrupo profesional | 259 | 40 | 15.4 | imputada (mediana = 95) + marca glicemia_mg_dl_imputado |
| `circunferencia_cintura_cm` | general | 495 | 75 | 15.2 | imputada (mediana = 92.5) + marca circunferencia_cintura_cm_imputado |
| `colesterol_total_mg_dl` | subgrupo profesional | 259 | 39 | 15.1 | imputada (mediana = 200) + marca colesterol_total_mg_dl_imputado |
| `trigliceridos_mg_dl` | subgrupo profesional | 259 | 39 | 15.1 | imputada (mediana = 146) + marca trigliceridos_mg_dl_imputado |
| `colesterol_hdl_mg_dl` | subgrupo profesional | 259 | 39 | 15.1 | imputada (mediana = 54) + marca colesterol_hdl_mg_dl_imputado |
| `menstruacion_llega` | general | 170 | 11 | 6.5 | imputada (moda = REGULAR) + marca menstruacion_llega_imputado |
| `tipo_sangrado` | general | 170 | 11 | 6.5 | imputada (moda = MODERADO) + marca tipo_sangrado_imputado |
| `presion_sistolica` | subgrupo profesional | 259 | 15 | 5.8 | imputada (mediana = 120) + marca presion_sistolica_imputado |
| `presion_diastolica` | subgrupo profesional | 259 | 13 | 5.0 | imputada (mediana = 75) + marca presion_diastolica_imputado |
| `estres_entorno_laboral` | general | 306 | 10 | 3.3 | imputada (mediana = 3) |
| `tipo_metodo_anticonceptivo` | general | 66 | 2 | 3.0 | imputada (moda = ORAL) |
| `marihuana_frecuencia` | general | 495 | 14 | 2.8 | imputada (mediana = 1) |
| `cambio_relacion_pareja_menopausia` | general | 324 | 8 | 2.5 | imputada (mediana = 2) |
| `tabaco_frecuencia` | general | 495 | 12 | 2.4 | imputada (mediana = 1) |
| `alcohol_frecuencia` | general | 495 | 11 | 2.2 | imputada (mediana = 1) |
| `horas_sedentarismo` | general | 495 | 11 | 2.2 | imputada (mediana = 7) |
| `platos_verduras_dia` | general | 495 | 10 | 2.0 | imputada (mediana = 2) |
| `vasos_agua_dia` | general | 495 | 10 | 2.0 | imputada (mediana = 3) |
| `tiene_actividad_sexual` | general | 495 | 9 | 1.8 | imputada (moda = SI) |
| `peso_kg` | general | 495 | 8 | 1.6 | imputada (mediana = 71) |
| `falta_tiempo_influye` | general | 495 | 7 | 1.4 | imputada (mediana = 3) |
| `frecuencia_comida_fuera` | general | 495 | 7 | 1.4 | imputada (mediana = 2) |
| `lacteos_dia` | general | 495 | 7 | 1.4 | imputada (mediana = 2) |
| `golosinas_semana` | general | 495 | 7 | 1.4 | imputada (mediana = 3) |
| `rendimiento_afectado` | general | 306 | 4 | 1.3 | imputada (mediana = 2) |
| `frutas_dia` | general | 495 | 6 | 1.2 | imputada (mediana = 2) |
| `panes_dia` | general | 495 | 6 | 1.2 | imputada (mediana = 3) |
| `carnes_semana` | general | 495 | 6 | 1.2 | imputada (mediana = 3) |
| `jugos_gaseosas_dia` | general | 495 | 6 | 1.2 | imputada (mediana = 2) |
| `bebidas_energeticas_dia` | general | 495 | 6 | 1.2 | imputada (mediana = 1) |
| `dias_ejercicio_semana` | general | 495 | 6 | 1.2 | imputada (mediana = 2) |
| `pescado_semana` | general | 495 | 6 | 1.2 | imputada (mediana = 2) |
| `evacuacion_intestinal` | general | 495 | 6 | 1.2 | imputada (mediana = 2) |
| `distension_abdominal` | general | 495 | 6 | 1.2 | imputada (mediana = 2) |
| `talla_actual_cm` | general | 495 | 6 | 1.2 | imputada (mediana = 156) |
| `quien_prepara_comidas` | general | 495 | 6 | 1.2 | imputada (moda = YO_MAYORIA) |
| `legumbres_semana` | general | 495 | 6 | 1.2 | imputada (mediana = 2) |
| `bienestar_trabajo_afectado` | general | 306 | 3 | 1.0 | imputada (mediana = 3) |
| `frecuencia_ausencias` | general | 306 | 3 | 1.0 | imputada (mediana = 2) |
| `cantidad_personas_cuida` | general | 213 | 2 | 0.9 | imputada (mediana = 2) |
| `pueblo_originario_afro` | general | 495 | 4 | 0.8 | imputada (moda = NINGUNO) |
| `usa_terapia_hormonal` | general | 495 | 4 | 0.8 | imputada (moda = NO) |
| `tiene_pareja` | general | 495 | 4 | 0.8 | imputada (moda = SI) |
| `usa_antidepresivos` | general | 495 | 4 | 0.8 | imputada (moda = NO) |
| `lugar_trabajo_comprensivo` | general | 306 | 2 | 0.7 | imputada (mediana = 3) |
| `nivel_educacion` | general | 495 | 3 | 0.6 | imputada (moda = M_COM) |
| `considera_informacion_suficiente` | general | 360 | 2 | 0.6 | imputada (mediana = 2) |
| `realiza_bajo_impacto` | general | 495 | 2 | 0.4 | imputada (moda = NO) |
| `realiza_fuerza` | general | 495 | 2 | 0.4 | imputada (moda = NO) |
| `cuida_otras_personas` | general | 495 | 2 | 0.4 | imputada (moda = NO) |
| `trabaja_actualmente` | general | 495 | 2 | 0.4 | imputada (moda = True) |
| `realiza_aerobico` | general | 495 | 2 | 0.4 | imputada (moda = NO) |
| `pregunta_1` | general | 495 | 1 | 0.2 | no se imputa (variable resultado) |
| `pregunta_2` | general | 495 | 1 | 0.2 | no se imputa (variable resultado) |
| `pregunta_11` | general | 495 | 1 | 0.2 | no se imputa (variable resultado) |

Las 43 variables restantes no tienen faltantes reales.

**Ámbito "subgrupo profesional":** laboratorio, presión, tamizaje y talla máxima solo los
registra el personal de salud (`campos_por_rol.SOLO_PROFESIONAL`). Aplican a las 259 encuestas con origen MEDICO o API, y se
analizan en ese subgrupo, no en el modelado general.

## 4. Variables derivadas

- `edad` y `tramo_edad` a la fecha de evaluación.
- `mrs_somatico` (p1-p4), `mrs_psicologico` (p5-p8), `mrs_urogenital` (p9-p11), `mrs_total`
  y `mrs_severidad` con los cortes de `MRS.SEVERIDAD_TOTAL` (pendientes de confirmar).
- `meses_desde_fum` y `etapa_menopausica` (STRAW+10 simplificado: ovario = NO → quirúrgica;
  ≥ 12 meses → posmenopausia; < 12 meses y regular → premenopausia; si no → perimenopausia).
- `imc`, `imc_categoria` (OMS), `perdida_talla_cm`, `presion_elevada` (≥ 140/90),
  `doble_carga` (trabaja y cuida a otras personas).

MRS completo en 492 de 495 filas. Media del total: 14.4 ± 8.8 (somático 5.6, psicológico 5.7, urogenital 3.1).

| Severidad MRS | Filas | % |
|---|---|---|
| Sin síntomas o muy leves | 71 | 14.4 % |
| Leve | 75 | 15.2 % |
| Moderada | 141 | 28.7 % |
| Severa | 205 | 41.7 % |

| Etapa | Filas | % |
|---|---|---|
| posmenopausia | 301 | 60.8 % |
| premenopausia | 90 | 18.2 % |
| perimenopausia | 67 | 13.5 % |
| quirurgica | 25 | 5.1 % |
| indeterminada | 12 | 2.4 % |

| Tramo de edad | Filas |
|---|---|
| 40-44 | 58 |
| 45-49 | 140 |
| 50-54 | 152 |
| 55-59 | 99 |
| 60-65 | 33 |
| <40 | 13 |

## 5. Decisiones que conviene validar con la profesora

- Cortes de severidad del MRS (0-4 / 5-8 / 9-15 / 16+) y la definición de etapa menopáusica.
- `cambio_relacion_pareja_menopausia` se trata como "no aplica" sin pareja (regla propia del
  análisis: la plataforma muestra la pregunta a todas).
- Las opciones de selección múltiple del dataset (p. ej. "Largas listas de espera",
  "Hijos/as") no son las mismas que ofrece hoy la plataforma (`esquema.OPCIONES_MULTISELECCION`).
  Se conservaron tal como vienen.
- Correcciones de unidad: talla en metros (×100) y presión en cmHg (×10).
