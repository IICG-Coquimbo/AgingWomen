# Informe de limpieza del conjunto sintético de la usuaria (Fase 34B)

Generado por `analisis/limpiar_dataset.py` el 2026-10-24. Volver a ejecutar el script regenera este informe y los archivos de salida.

- Entrada: `datos/sintetico/dataset_usuaria_sucio.csv` — 565 filas.
- Salida: `datos/limpio_usuaria/dataset_usuaria_limpio.csv` — **546 filas**.
- Excluidas: 19 filas (`datos/limpio_usuaria/excluidas.csv`, con el motivo).
- Diccionario: `datos/limpio_usuaria/diccionario_variables.csv` (faltantes y tratamiento por variable).

Los códigos válidos, la lógica condicional y los campos solo para personal de salud se
leen del código de la plataforma (`models.py`, `condicionales.py`, `campos_por_rol.py`),
así la limpieza nunca contradice lo que la encuesta acepta.

## 1. Filas excluidas

| Motivo | Filas |
|---|---|
| duplicado exacto | 8 |
| RUT repetido (versión antigua) | 7 |
| mayor de 65 años | 3 |
| edad no verificable (fecha de nacimiento imposible) | 1 |

## 2. Correcciones por paso

Una fila por (paso, variable, motivo). "Ejemplos" muestra valores originales.

| Paso | Variable | Motivo | Celdas | Ejemplos |
|---|---|---|---|---|
| 1 formato | `a_quien_cuida` | espacios sobrantes | 2 |  |
| 1 formato | `comuna` | espacios sobrantes | 3 |  |
| 1 formato | `conoce_recursos_disponibles` | espacios sobrantes | 2 |  |
| 1 formato | `conoce_sistema_publico_climaterio` | espacios sobrantes | 1 |  |
| 1 formato | `cuida_otras_personas` | espacios sobrantes | 3 |  |
| 1 formato | `desea_mas_informacion_apoyo` | espacios sobrantes | 3 |  |
| 1 formato | `en_control_programa_consultorio` | espacios sobrantes | 3 |  |
| 1 formato | `en_control_programa_cual` | espacios sobrantes | 1 |  |
| 1 formato | `excepcion_edad` | espacios sobrantes | 5 |  |
| 1 formato | `fecha_ultima_menstruacion` | espacios sobrantes | 1 |  |
| 1 formato | `genero` | espacios sobrantes | 9 |  |
| 1 formato | `ha_consultado_por_sintomas` | espacios sobrantes | 11 |  |
| 1 formato | `ha_escuchado_programa_climaterio` | espacios sobrantes | 3 |  |
| 1 formato | `ha_tenido_dificultades_acceso` | espacios sobrantes | 4 |  |
| 1 formato | `incomodidad` | espacios sobrantes | 3 |  |
| 1 formato | `menstruacion_llega` | espacios sobrantes | 1 |  |
| 1 formato | `nivel_educacion` | espacios sobrantes | 4 |  |
| 1 formato | `operada_no_mas_hijos` | espacios sobrantes | 4 |  |
| 1 formato | `origen_procedencia` | espacios sobrantes | 11 |  |
| 1 formato | `prevision` | espacios sobrantes | 6 |  |
| 1 formato | `principales_dificultades` | espacios sobrantes | 3 |  |
| 1 formato | `pueblo_originario_afro` | espacios sobrantes | 8 |  |
| 1 formato | `quien_prepara_comidas` | espacios sobrantes | 5 |  |
| 1 formato | `realiza_aerobico` | espacios sobrantes | 5 |  |
| 1 formato | `realiza_bajo_impacto` | espacios sobrantes | 3 |  |
| 1 formato | `realiza_fuerza` | espacios sobrantes | 5 |  |
| 1 formato | `tiene_actividad_sexual` | espacios sobrantes | 4 |  |
| 1 formato | `tiene_ovario` | espacios sobrantes | 6 |  |
| 1 formato | `tiene_pareja` | espacios sobrantes | 3 |  |
| 1 formato | `tiene_utero` | espacios sobrantes | 6 |  |
| 1 formato | `tipo_informacion_apoyo_deseado` | espacios sobrantes | 3 |  |
| 1 formato | `tipo_sangrado` | espacios sobrantes | 2 |  |
| 1 formato | `trabaja_actualmente` | espacios sobrantes | 6 |  |
| 1 formato | `usa_antidepresivos` | espacios sobrantes | 6 |  |
| 1 formato | `usa_medicamentos_diabetes` | espacios sobrantes | 5 |  |
| 1 formato | `usa_medicamentos_presion` | espacios sobrantes | 9 |  |
| 1 formato | `usa_metodo_anticonceptivo` | espacios sobrantes | 2 |  |
| 1 formato | `usa_terapia_hormonal` | espacios sobrantes | 9 |  |
| 3 centinelas | `a_quien_cuida` | texto "sin dato" | 1 | - |
| 3 centinelas | `a_quien_cuida_otro` | texto "sin dato" | 1 | N/A |
| 3 centinelas | `alcohol_frecuencia` | texto "sin dato" | 5 | N/A, NA, sin dato |
| 3 centinelas | `alcohol_frecuencia` | número "sin dato" (-1/99/999/9999) | 3 | 99, 999, 9999 |
| 3 centinelas | `bebidas_energeticas_dia` | número "sin dato" (-1/99/999/9999) | 2 | 999, 9999 |
| 3 centinelas | `bienestar_trabajo_afectado` | texto "sin dato" | 1 | NA |
| 3 centinelas | `bienestar_trabajo_afectado` | número "sin dato" (-1/99/999/9999) | 1 | 9999 |
| 3 centinelas | `cambio_relacion_pareja_menopausia` | texto "sin dato" | 1 | N/A |
| 3 centinelas | `cambio_relacion_pareja_menopausia` | número "sin dato" (-1/99/999/9999) | 4 | -1, 999, 9999 |
| 3 centinelas | `cantidad_personas_cuida` | texto "sin dato" | 2 | -, sin dato |
| 3 centinelas | `carnes_semana` | texto "sin dato" | 4 | N/A, NA, sin dato |
| 3 centinelas | `carnes_semana` | número "sin dato" (-1/99/999/9999) | 4 | -1, 99, 999 |
| 3 centinelas | `comodidad_diseno` | número "sin dato" (-1/99/999/9999) | 1 | -1 |
| 3 centinelas | `conoce_recursos_disponibles` | texto "sin dato" | 3 | NA, sin dato |
| 3 centinelas | `conoce_sistema_publico_climaterio` | texto "sin dato" | 2 | -, sin dato |
| 3 centinelas | `considera_informacion_suficiente` | texto "sin dato" | 2 | -, N/A |
| 3 centinelas | `considera_informacion_suficiente` | número "sin dato" (-1/99/999/9999) | 3 | -1, 99, 999 |
| 3 centinelas | `cuida_otras_personas` | texto "sin dato" | 4 | N/A, NA, sin dato |
| 3 centinelas | `dias_ejercicio_semana` | número "sin dato" (-1/99/999/9999) | 4 | -1, 9999 |
| 3 centinelas | `distension_abdominal` | texto "sin dato" | 2 | N/A, NA |
| 3 centinelas | `distension_abdominal` | número "sin dato" (-1/99/999/9999) | 3 | -1, 99, 999 |
| 3 centinelas | `en_control_programa_consultorio` | texto "sin dato" | 3 | -, N/A, NA |
| 3 centinelas | `estres_entorno_laboral` | texto "sin dato" | 2 | -, NA |
| 3 centinelas | `evacuacion_intestinal` | texto "sin dato" | 4 | -, N/A, NA, sin dato |
| 3 centinelas | `evacuacion_intestinal` | número "sin dato" (-1/99/999/9999) | 1 | 9999 |
| 3 centinelas | `evaluacion_atencion_recibida` | número "sin dato" (-1/99/999/9999) | 1 | 99 |
| 3 centinelas | `facilidad_uso` | número "sin dato" (-1/99/999/9999) | 3 | 99, 9999 |
| 3 centinelas | `falta_tiempo_influye` | texto "sin dato" | 2 | NA, sin dato |
| 3 centinelas | `falta_tiempo_influye` | número "sin dato" (-1/99/999/9999) | 1 | 9999 |
| 3 centinelas | `fatiga_mental` | número "sin dato" (-1/99/999/9999) | 1 | 999 |
| 3 centinelas | `fecha_ultimo_empa` | texto "sin dato" | 1 | N/A |
| 3 centinelas | `frecuencia_aerobico` | texto "sin dato" | 1 | NA |
| 3 centinelas | `frecuencia_ausencias` | número "sin dato" (-1/99/999/9999) | 3 | 99, 999, 9999 |
| 3 centinelas | `frecuencia_bajo_impacto` | texto "sin dato" | 1 | - |
| 3 centinelas | `frecuencia_bajo_impacto` | número "sin dato" (-1/99/999/9999) | 1 | 9999 |
| 3 centinelas | `frecuencia_comida_fuera` | texto "sin dato" | 1 | sin dato |
| 3 centinelas | `frecuencia_comida_fuera` | número "sin dato" (-1/99/999/9999) | 5 | -1, 99, 999, 9999 |
| 3 centinelas | `frutas_dia` | texto "sin dato" | 2 | sin dato |
| 3 centinelas | `frutas_dia` | número "sin dato" (-1/99/999/9999) | 7 | 99, 999, 9999 |
| 3 centinelas | `golosinas_semana` | número "sin dato" (-1/99/999/9999) | 2 | -1, 999 |
| 3 centinelas | `ha_consultado_por_sintomas` | texto "sin dato" | 2 | - |
| 3 centinelas | `ha_tenido_dificultades_acceso` | texto "sin dato" | 2 | sin dato |
| 3 centinelas | `horas_sedentarismo` | texto "sin dato" | 2 | sin dato |
| 3 centinelas | `horas_sedentarismo` | número "sin dato" (-1/99/999/9999) | 3 | -1 |
| 3 centinelas | `jugos_gaseosas_dia` | texto "sin dato" | 1 | sin dato |
| 3 centinelas | `jugos_gaseosas_dia` | número "sin dato" (-1/99/999/9999) | 3 | 99, 999 |
| 3 centinelas | `lacteos_dia` | texto "sin dato" | 2 | -, NA |
| 3 centinelas | `lacteos_dia` | número "sin dato" (-1/99/999/9999) | 2 | 999 |
| 3 centinelas | `legumbres_semana` | texto "sin dato" | 2 | N/A, NA |
| 3 centinelas | `legumbres_semana` | número "sin dato" (-1/99/999/9999) | 3 | -1, 999 |
| 3 centinelas | `marihuana_frecuencia` | texto "sin dato" | 2 | N/A, NA |
| 3 centinelas | `marihuana_frecuencia` | número "sin dato" (-1/99/999/9999) | 3 | 99, 999 |
| 3 centinelas | `nivel_informacion_servicios` | texto "sin dato" | 2 | N/A, sin dato |
| 3 centinelas | `nivel_informacion_servicios` | número "sin dato" (-1/99/999/9999) | 3 | 99, 9999 |
| 3 centinelas | `panes_dia` | número "sin dato" (-1/99/999/9999) | 6 | -1, 99, 999, 9999 |
| 3 centinelas | `pescado_semana` | texto "sin dato" | 1 | N/A |
| 3 centinelas | `pescado_semana` | número "sin dato" (-1/99/999/9999) | 2 | 99, 999 |
| 3 centinelas | `peso_kg` | texto "sin dato" | 2 | -, NA |
| 3 centinelas | `peso_kg` | número "sin dato" (-1/99/999/9999) | 4 | -1, 9999 |
| 3 centinelas | `platos_verduras_dia` | texto "sin dato" | 3 | -, sin dato |
| 3 centinelas | `platos_verduras_dia` | número "sin dato" (-1/99/999/9999) | 3 | 99, 999 |
| 3 centinelas | `prevision` | texto "sin dato" | 3 | -, NA, sin dato |
| 3 centinelas | `quien_prepara_comidas` | texto "sin dato" | 1 | - |
| 3 centinelas | `realiza_aerobico` | texto "sin dato" | 3 | -, NA |
| 3 centinelas | `realiza_fuerza` | texto "sin dato" | 2 | N/A |
| 3 centinelas | `rendimiento_afectado` | texto "sin dato" | 1 | N/A |
| 3 centinelas | `rendimiento_afectado` | número "sin dato" (-1/99/999/9999) | 1 | 999 |
| 3 centinelas | `sabe_donde_acudir` | texto "sin dato" | 1 | N/A |
| 3 centinelas | `sintomas_tomados_en_serio` | texto "sin dato" | 4 | N/A, NA, sin dato |
| 3 centinelas | `sintomas_tomados_en_serio` | número "sin dato" (-1/99/999/9999) | 4 | -1, 99, 999 |
| 3 centinelas | `sobrecarga_fisica_emocional` | texto "sin dato" | 1 | sin dato |
| 3 centinelas | `tabaco_frecuencia` | texto "sin dato" | 3 | -, N/A |
| 3 centinelas | `tabaco_frecuencia` | número "sin dato" (-1/99/999/9999) | 1 | -1 |
| 3 centinelas | `talla_actual_cm` | número "sin dato" (-1/99/999/9999) | 2 | -1, 9999 |
| 3 centinelas | `tiene_actividad_sexual` | texto "sin dato" | 3 | N/A, NA |
| 3 centinelas | `tiene_ovario` | texto "sin dato" | 4 | -, N/A, NA |
| 3 centinelas | `tiene_pareja` | texto "sin dato" | 1 | NA |
| 3 centinelas | `tiene_utero` | texto "sin dato" | 2 | -, NA |
| 3 centinelas | `tipo_informacion_apoyo_deseado` | texto "sin dato" | 1 | sin dato |
| 3 centinelas | `tipo_metodo_anticonceptivo` | texto "sin dato" | 1 | sin dato |
| 3 centinelas | `tipo_sangrado` | texto "sin dato" | 1 | - |
| 3 centinelas | `trabaja_actualmente` | texto "sin dato" | 1 | - |
| 3 centinelas | `usa_medicamentos_diabetes` | texto "sin dato" | 2 | -, sin dato |
| 3 centinelas | `usa_medicamentos_presion` | texto "sin dato" | 1 | N/A |
| 3 centinelas | `usa_terapia_hormonal` | texto "sin dato" | 2 | sin dato |
| 3 centinelas | `vasos_agua_dia` | texto "sin dato" | 1 | NA |
| 3 centinelas | `vasos_agua_dia` | número "sin dato" (-1/99/999/9999) | 3 | 99, 9999 |
| 4 códigos | `conoce_recursos_disponibles` | recodificado al código del sistema | 8 | No, Sí, no, si, sí |
| 4 códigos | `conoce_sistema_publico_climaterio` | recodificado al código del sistema | 9 | N, No, S, Sí, si |
| 4 códigos | `cuida_otras_personas` | recodificado al código del sistema | 11 | N, No, S, no, si |
| 4 códigos | `desea_mas_informacion_apoyo` | recodificado al código del sistema | 13 | N, No, S, Sí, no, sí |
| 4 códigos | `en_control_programa_consultorio` | recodificado al código del sistema | 8 | N, No, S, si, sí |
| 4 códigos | `excepcion_edad` | recodificado al código del sistema | 4 | ninguna |
| 4 códigos | `genero` | recodificado al código del sistema | 8 | FEMENINO, Femenino, Mujer |
| 4 códigos | `ha_consultado_por_sintomas` | recodificado al código del sistema | 6 | N, No, S, no, sí |
| 4 códigos | `ha_escuchado_programa_climaterio` | recodificado al código del sistema | 3 | S, no, sí |
| 4 códigos | `ha_tenido_dificultades_acceso` | recodificado al código del sistema | 7 | N, No, S, si, sí |
| 4 códigos | `incomodidad` | recodificado al código del sistema | 5 | N, No, si |
| 4 códigos | `nivel_educacion` | recodificado al código del sistema | 7 | m_com, post, s_n_com, u_com |
| 4 códigos | `operada_no_mas_hijos` | recodificado al código del sistema | 20 | N, No, Sí, no, si |
| 4 códigos | `pregunta_1` | valor fuera de las opciones → vacío | 1 | 5 |
| 4 códigos | `pregunta_11` | valor fuera de las opciones → vacío | 4 | 5, 9 |
| 4 códigos | `pregunta_2` | valor fuera de las opciones → vacío | 1 | 5 |
| 4 códigos | `pregunta_4` | valor fuera de las opciones → vacío | 3 | 9 |
| 4 códigos | `pregunta_5` | valor fuera de las opciones → vacío | 3 | 5, 9 |
| 4 códigos | `pregunta_6` | valor fuera de las opciones → vacío | 2 | 5, 9 |
| 4 códigos | `pregunta_7` | valor fuera de las opciones → vacío | 1 | 9 |
| 4 códigos | `pregunta_8` | valor fuera de las opciones → vacío | 1 | 9 |
| 4 códigos | `pregunta_9` | valor fuera de las opciones → vacío | 1 | 5 |
| 4 códigos | `prevision` | recodificado al código del sistema | 4 | fonasa |
| 4 códigos | `pueblo_originario_afro` | recodificado al código del sistema | 6 | ninguno |
| 4 códigos | `quien_prepara_comidas` | recodificado al código del sistema | 7 | compartido, otra_hogar, yo_mayoria |
| 4 códigos | `realiza_aerobico` | recodificado al código del sistema | 7 | N, No, sí |
| 4 códigos | `realiza_bajo_impacto` | recodificado al código del sistema | 10 | N, No, Sí, no, si, sí |
| 4 códigos | `realiza_fuerza` | recodificado al código del sistema | 10 | N, S, Sí, no |
| 4 códigos | `recomendaria` | recodificado al código del sistema | 7 | Sí, sí, tal_vez |
| 4 códigos | `recomendaria` | valor fuera de las opciones → vacío | 3 | N, S |
| 4 códigos | `region_residencia` | recodificado al código del sistema | 7 | Coquimbo |
| 4 códigos | `region_residencia` | valor fuera de las opciones → vacío | 8 | 999, Región de Coquimbo |
| 4 códigos | `region_residencia` | deducida desde la comuna | 8 |  |
| 4 códigos | `sabe_donde_acudir` | recodificado al código del sistema | 8 | N, No, no, sí |
| 4 códigos | `tiene_actividad_sexual` | recodificado al código del sistema | 10 | N, No, S, Sí, no |
| 4 códigos | `tiene_ovario` | recodificado al código del sistema | 7 | No, S, Sí, no, si, sí |
| 4 códigos | `tiene_pareja` | recodificado al código del sistema | 10 | N, No, S, Sí, no, sí |
| 4 códigos | `tiene_utero` | recodificado al código del sistema | 12 | N, S, Sí, si, sí |
| 4 códigos | `tipo_sangrado` | recodificado al código del sistema | 3 | leve, moderado, muy_abund |
| 4 códigos | `trabaja_actualmente` | recodificado al código del sistema | 11 | 1, FALSE, TRUE, verdadero |
| 4 códigos | `usa_antidepresivos` | recodificado al código del sistema | 11 | N, No, Sí, no |
| 4 códigos | `usa_medicamentos_diabetes` | recodificado al código del sistema | 8 | N, No, no, sí |
| 4 códigos | `usa_medicamentos_presion` | recodificado al código del sistema | 12 | N, No, S, Sí, no, si |
| 4 códigos | `usa_metodo_anticonceptivo` | recodificado al código del sistema | 2 | N, No |
| 4 códigos | `usa_terapia_hormonal` | recodificado al código del sistema | 10 | N, No, no |
| 5 mediciones | `circunferencia_cintura_cm` | unidad o coma decimal quitada | 14 | 100 cm, 100,0, 111 cm, 72,0, 80 cm, 81,0 |
| 5 mediciones | `circunferencia_cintura_cm` | fuera del rango plausible 50-170 → vacío | 30 | 0.0 |
| 5 mediciones | `circunferencia_cintura_cm` | incoherente con el IMC (|z robusto| > 4) → vacía | 1 | 75 cm con IMC 43.4 |
| 5 mediciones | `peso_kg` | unidad o coma decimal quitada | 17 | 104.6 kg, 48,1, 50,1, 50.0 kg, 56,9, 57,0 |
| 5 mediciones | `talla_actual_cm` | unidad o coma decimal quitada | 20 | 146 cm, 148,0, 150,0, 151,0, 152,0, 153 cm |
| 5 mediciones | `talla_actual_cm` | metros → centímetros (×100) | 8 | 1.43, 1.44, 1.49, 1.55, 1.57, 1.58, 1.64, 1.65 |
| 5 mediciones | `talla_actual_cm` | fuera del rango plausible 120-200 → vacío | 2 | 1565.0, 1587.0 |
| 6 fechas | `fecha_nacimiento` | formato DD/MM/AAAA → AAAA-MM-DD | 38 |  |
| 6 fechas | `fecha_nacimiento` | posterior a la evaluación → vacío | 1 |  |
| 6 fechas | `fecha_ultima_menstruacion` | normalizada a AAAA-MM / AAAA | 70 |  |
| 8 condicionales | `cambio_relacion_pareja_menopausia` | pregunta oculta (depende de tiene_pareja) → borrada | 196 |  |
| 8 condicionales | `cantidad_personas_cuida` | pregunta oculta (depende de cuida_otras_personas) → borrada | 2 |  |
| 8 condicionales | `cuida_otras_personas` | vacía pero respondió cantidad_personas_cuida → SI | 4 |  |
| 8 condicionales | `en_control_programa_consultorio` | vacía pero respondió en_control_programa_cual → SI | 1 |  |
| 8 condicionales | `frecuencia_aerobico` | pregunta oculta (depende de realiza_aerobico) → borrada | 5 |  |
| 8 condicionales | `frecuencia_fuerza` | pregunta oculta (depende de realiza_fuerza) → borrada | 5 |  |
| 8 condicionales | `ha_consultado_por_sintomas` | vacía pero respondió evaluacion_atencion_recibida → SI | 1 |  |
| 8 condicionales | `menstruacion_llega` | pregunta oculta (depende de fecha_ultima_menstruacion) → borrada | 2 |  |
| 8 condicionales | `prevision` | vacía pero respondió conoce_sistema_publico_climaterio → FONASA | 2 |  |
| 8 condicionales | `realiza_fuerza` | vacía pero respondió frecuencia_fuerza → SI | 1 |  |
| 8 condicionales | `sobrecarga_fisica_emocional` | pregunta oculta (depende de cuida_otras_personas) → borrada | 2 |  |
| 8 condicionales | `tipo_metodo_anticonceptivo` | pregunta oculta (depende de usa_metodo_anticonceptivo) → borrada | 6 |  |
| 8 condicionales | `tipo_sangrado` | pregunta oculta (depende de fecha_ultima_menstruacion) → borrada | 2 |  |
| 8 condicionales | `trabaja_actualmente` | vacío pero respondió Trabajo → True | 1 |  |
| 8 condicionales | `usa_metodo_anticonceptivo` | vacía pero respondió tipo_metodo_anticonceptivo → SI | 5 |  |
| 8 condicionales | `usa_metodo_anticonceptivo` | pregunta oculta (depende de fecha_ultima_menstruacion) → borrada | 4 |  |
| 9 imputación | `alcohol_frecuencia` | imputado con mediana (2) | 29 |  |
| 9 imputación | `bebidas_energeticas_dia` | imputado con mediana (1) | 22 |  |
| 9 imputación | `bienestar_trabajo_afectado` | imputado con mediana (2) | 16 |  |
| 9 imputación | `cambio_relacion_pareja_menopausia` | imputado con mediana (2) | 23 |  |
| 9 imputación | `cantidad_personas_cuida` | imputado con mediana (1) | 7 |  |
| 9 imputación | `carnes_semana` | imputado con mediana (3) | 31 |  |
| 9 imputación | `conoce_recursos_disponibles` | imputado con moda (NO) | 20 |  |
| 9 imputación | `conoce_sistema_publico_climaterio` | imputado con moda (NO) | 25 |  |
| 9 imputación | `considera_informacion_suficiente` | imputado con mediana (2) | 13 |  |
| 9 imputación | `cuida_otras_personas` | imputado con moda (NO) | 21 |  |
| 9 imputación | `desea_mas_informacion_apoyo` | imputado con moda (SI) | 31 |  |
| 9 imputación | `dias_ejercicio_semana` | imputado con mediana (1) | 37 |  |
| 9 imputación | `distension_abdominal` | imputado con mediana (2) | 18 |  |
| 9 imputación | `en_control_programa_consultorio` | imputado con moda (NO) | 26 |  |
| 9 imputación | `estres_entorno_laboral` | imputado con mediana (3) | 10 |  |
| 9 imputación | `evacuacion_intestinal` | imputado con mediana (2) | 33 |  |
| 9 imputación | `evaluacion_atencion_recibida` | imputado con mediana (3) | 11 |  |
| 9 imputación | `falta_tiempo_influye` | imputado con mediana (3) | 30 |  |
| 9 imputación | `frecuencia_aerobico` | imputado con mediana (3) | 7 |  |
| 9 imputación | `frecuencia_ausencias` | imputado con mediana (2) | 17 |  |
| 9 imputación | `frecuencia_bajo_impacto` | imputado con mediana (3) | 15 |  |
| 9 imputación | `frecuencia_comida_fuera` | imputado con mediana (2) | 35 |  |
| 9 imputación | `frecuencia_fuerza` | imputado con mediana (3) | 2 |  |
| 9 imputación | `frutas_dia` | imputado con mediana (2) | 24 |  |
| 9 imputación | `golosinas_semana` | imputado con mediana (2) | 17 |  |
| 9 imputación | `ha_consultado_por_sintomas` | imputado con moda (NO) | 21 |  |
| 9 imputación | `ha_escuchado_programa_climaterio` | imputado con moda (NO) | 15 |  |
| 9 imputación | `ha_tenido_dificultades_acceso` | imputado con moda (NO) | 20 |  |
| 9 imputación | `horas_sedentarismo` | imputado con mediana (6) | 27 |  |
| 9 imputación | `jugos_gaseosas_dia` | imputado con mediana (2) | 31 |  |
| 9 imputación | `lacteos_dia` | imputado con mediana (2) | 32 |  |
| 9 imputación | `legumbres_semana` | imputado con mediana (2) | 27 |  |
| 9 imputación | `lugar_trabajo_comprensivo` | imputado con mediana (3) | 16 |  |
| 9 imputación | `marihuana_frecuencia` | imputado con mediana (1) | 18 |  |
| 9 imputación | `menstruacion_llega` | imputado con moda (REGULAR) | 5 |  |
| 9 imputación | `nivel_informacion_servicios` | imputado con mediana (2) | 26 |  |
| 9 imputación | `operada_no_mas_hijos` | imputado con moda (NO) | 18 |  |
| 9 imputación | `panes_dia` | imputado con mediana (2) | 33 |  |
| 9 imputación | `pescado_semana` | imputado con mediana (2) | 19 |  |
| 9 imputación | `platos_verduras_dia` | imputado con mediana (2) | 33 |  |
| 9 imputación | `prevision` | imputado con moda (FONASA) | 19 |  |
| 9 imputación | `quien_prepara_comidas` | imputado con moda (YO_MAYORIA) | 24 |  |
| 9 imputación | `realiza_aerobico` | imputado con moda (NO) | 29 |  |
| 9 imputación | `realiza_bajo_impacto` | imputado con moda (NO) | 24 |  |
| 9 imputación | `realiza_fuerza` | imputado con moda (NO) | 28 |  |
| 9 imputación | `rendimiento_afectado` | imputado con mediana (2) | 10 |  |
| 9 imputación | `sabe_donde_acudir` | imputado con moda (SI) | 21 |  |
| 9 imputación | `sintomas_tomados_en_serio` | imputado con mediana (2) | 31 |  |
| 9 imputación | `sobrecarga_fisica_emocional` | imputado con mediana (3) | 12 |  |
| 9 imputación | `tabaco_frecuencia` | imputado con mediana (1) | 18 |  |
| 9 imputación | `tiene_actividad_sexual` | imputado con moda (NO) | 30 |  |
| 9 imputación | `tiene_ovario` | imputado con moda (SI) | 23 |  |
| 9 imputación | `tiene_pareja` | imputado con moda (SI) | 28 |  |
| 9 imputación | `tiene_utero` | imputado con moda (SI) | 26 |  |
| 9 imputación | `tipo_metodo_anticonceptivo` | imputado con moda (DIU) | 6 |  |
| 9 imputación | `tipo_sangrado` | imputado con moda (MODERADO) | 11 |  |
| 9 imputación | `trabaja_actualmente` | imputado con moda (True) | 22 |  |
| 9 imputación | `usa_antidepresivos` | imputado con moda (NO) | 26 |  |
| 9 imputación | `usa_medicamentos_diabetes` | imputado con moda (NO) | 24 |  |
| 9 imputación | `usa_medicamentos_presion` | imputado con moda (NO) | 30 |  |
| 9 imputación | `usa_metodo_anticonceptivo` | imputado con moda (NO) | 3 |  |
| 9 imputación | `usa_terapia_hormonal` | imputado con moda (NO) | 25 |  |
| 9 imputación | `vasos_agua_dia` | imputado con mediana (3) | 25 |  |
| 10 derivadas | `mrs_*` | MRS incompleto: sin puntaje (fuera del análisis de severidad) | 17 |  |

**Notas:**

- 4 filas hacen ejercicio al menos 1 día pero no marcan ningún tipo; se conservan y se marcan en `incoherencia_ejercicio` (no se sabe cuál de los datos está mal).
- 2 filas usan píldora anticonceptiva y terapia hormonal a la vez; se conservan y se marcan en `incoherencia_pildora_th` (no se sabe cuál de los datos está mal).

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
| `circunferencia_cintura_cm` | general | 546 | 286 | 52.4 | > 30 %: no se modela |
| `peso_kg` | general | 546 | 256 | 46.9 | > 30 %: no se modela |
| `talla_actual_cm` | general | 546 | 215 | 39.4 | > 30 %: no se modela |
| `tipo_sangrado` | general | 204 | 33 | 16.2 | imputada (moda = MODERADO) + marca tipo_sangrado_imputado; 22 sin fecha de última menstruación quedan sin dato |
| `menstruacion_llega` | general | 204 | 27 | 13.2 | imputada (moda = REGULAR) + marca menstruacion_llega_imputado; 22 sin fecha de última menstruación quedan sin dato |
| `usa_metodo_anticonceptivo` | general | 204 | 25 | 12.3 | imputada (moda = NO) + marca usa_metodo_anticonceptivo_imputado; 22 sin fecha de última menstruación quedan sin dato |
| `evaluacion_atencion_recibida` | general | 127 | 11 | 8.7 | imputada (mediana = 3) + marca evaluacion_atencion_recibida_imputado |
| `tipo_metodo_anticonceptivo` | general | 73 | 6 | 8.2 | imputada (moda = DIU) + marca tipo_metodo_anticonceptivo_imputado |
| `dias_ejercicio_semana` | general | 546 | 37 | 6.8 | imputada (mediana = 1) + marca dias_ejercicio_semana_imputado |
| `cambio_relacion_pareja_menopausia` | general | 339 | 23 | 6.8 | imputada (mediana = 2) + marca cambio_relacion_pareja_menopausia_imputado |
| `frecuencia_aerobico` | general | 106 | 7 | 6.6 | imputada (mediana = 3) + marca frecuencia_aerobico_imputado |
| `frecuencia_bajo_impacto` | general | 231 | 15 | 6.5 | imputada (mediana = 3) + marca frecuencia_bajo_impacto_imputado |
| `frecuencia_comida_fuera` | general | 546 | 35 | 6.4 | imputada (mediana = 2) + marca frecuencia_comida_fuera_imputado |
| `a_quien_cuida` | general | 257 | 16 | 6.2 | no se imputa (selección múltiple) |
| `en_control_programa_consultorio` | general | 428 | 26 | 6.1 | imputada (moda = NO) + marca en_control_programa_consultorio_imputado |
| `nivel_informacion_servicios` | general | 428 | 26 | 6.1 | imputada (mediana = 2) + marca nivel_informacion_servicios_imputado |
| `panes_dia` | general | 546 | 33 | 6.0 | imputada (mediana = 2) + marca panes_dia_imputado |
| `platos_verduras_dia` | general | 546 | 33 | 6.0 | imputada (mediana = 2) + marca platos_verduras_dia_imputado |
| `evacuacion_intestinal` | general | 546 | 33 | 6.0 | imputada (mediana = 2) + marca evacuacion_intestinal_imputado |
| `lacteos_dia` | general | 546 | 32 | 5.9 | imputada (mediana = 2) + marca lacteos_dia_imputado |
| `conoce_sistema_publico_climaterio` | general | 428 | 25 | 5.8 | imputada (moda = NO) + marca conoce_sistema_publico_climaterio_imputado |
| `sintomas_tomados_en_serio` | general | 546 | 31 | 5.7 | imputada (mediana = 2) + marca sintomas_tomados_en_serio_imputado |
| `jugos_gaseosas_dia` | general | 546 | 31 | 5.7 | imputada (mediana = 2) + marca jugos_gaseosas_dia_imputado |
| `carnes_semana` | general | 546 | 31 | 5.7 | imputada (mediana = 3) + marca carnes_semana_imputado |
| `desea_mas_informacion_apoyo` | general | 546 | 31 | 5.7 | imputada (moda = SI) + marca desea_mas_informacion_apoyo_imputado |
| `frecuencia_ausencias` | general | 298 | 17 | 5.7 | imputada (mediana = 2) + marca frecuencia_ausencias_imputado |
| `tiene_actividad_sexual` | general | 546 | 30 | 5.5 | imputada (moda = NO) + marca tiene_actividad_sexual_imputado |
| `falta_tiempo_influye` | general | 546 | 30 | 5.5 | imputada (mediana = 3) + marca falta_tiempo_influye_imputado |
| `usa_medicamentos_presion` | general | 546 | 30 | 5.5 | imputada (moda = NO) + marca usa_medicamentos_presion_imputado |
| `lugar_trabajo_comprensivo` | general | 298 | 16 | 5.4 | imputada (mediana = 3) + marca lugar_trabajo_comprensivo_imputado |
| `bienestar_trabajo_afectado` | general | 298 | 16 | 5.4 | imputada (mediana = 2) + marca bienestar_trabajo_afectado_imputado |
| `alcohol_frecuencia` | general | 546 | 29 | 5.3 | imputada (mediana = 2) + marca alcohol_frecuencia_imputado |
| `realiza_aerobico` | general | 546 | 29 | 5.3 | imputada (moda = NO) + marca realiza_aerobico_imputado |
| `tiene_pareja` | general | 546 | 28 | 5.1 | imputada (moda = SI) + marca tiene_pareja_imputado |
| `realiza_fuerza` | general | 546 | 28 | 5.1 | imputada (moda = NO) + marca realiza_fuerza_imputado |
| `sabe_donde_acudir` | general | 428 | 21 | 4.9 | imputada (moda = SI) |
| `legumbres_semana` | general | 546 | 27 | 4.9 | imputada (mediana = 2) |
| `ha_consultado_por_sintomas` | general | 428 | 21 | 4.9 | imputada (moda = NO) |
| `horas_sedentarismo` | general | 546 | 27 | 4.9 | imputada (mediana = 6) |
| `tiene_utero` | general | 546 | 26 | 4.8 | imputada (moda = SI) |
| `usa_antidepresivos` | general | 546 | 26 | 4.8 | imputada (moda = NO) |
| `tipo_informacion_apoyo_deseado` | general | 417 | 20 | 4.8 | no se imputa (selección múltiple) |
| `ha_tenido_dificultades_acceso` | general | 428 | 20 | 4.7 | imputada (moda = NO) |
| `sobrecarga_fisica_emocional` | general | 257 | 12 | 4.7 | imputada (mediana = 3) |
| `conoce_recursos_disponibles` | general | 428 | 20 | 4.7 | imputada (moda = NO) |
| `principales_dificultades` | general | 151 | 7 | 4.6 | no se imputa (selección múltiple) |
| `usa_terapia_hormonal` | general | 546 | 25 | 4.6 | imputada (moda = NO) |
| `vasos_agua_dia` | general | 546 | 25 | 4.6 | imputada (mediana = 3) |
| `realiza_bajo_impacto` | general | 546 | 24 | 4.4 | imputada (moda = NO) |
| `quien_prepara_comidas` | general | 546 | 24 | 4.4 | imputada (moda = YO_MAYORIA) |
| `frutas_dia` | general | 546 | 24 | 4.4 | imputada (mediana = 2) |
| `usa_medicamentos_diabetes` | general | 546 | 24 | 4.4 | imputada (moda = NO) |
| `tiene_ovario` | general | 546 | 23 | 4.2 | imputada (moda = SI) |
| `trabaja_actualmente` | general | 546 | 22 | 4.0 | imputada (moda = True) |
| `bebidas_energeticas_dia` | general | 546 | 22 | 4.0 | imputada (mediana = 1) |
| `cuida_otras_personas` | general | 546 | 21 | 3.8 | imputada (moda = NO) |
| `ha_escuchado_programa_climaterio` | general | 428 | 15 | 3.5 | imputada (moda = NO) |
| `prevision` | general | 546 | 19 | 3.5 | imputada (moda = FONASA) |
| `pescado_semana` | general | 546 | 19 | 3.5 | imputada (mediana = 2) |
| `estres_entorno_laboral` | general | 298 | 10 | 3.4 | imputada (mediana = 3) |
| `rendimiento_afectado` | general | 298 | 10 | 3.4 | imputada (mediana = 2) |
| `operada_no_mas_hijos` | general | 546 | 18 | 3.3 | imputada (moda = NO) |
| `marihuana_frecuencia` | general | 546 | 18 | 3.3 | imputada (mediana = 1) |
| `distension_abdominal` | general | 546 | 18 | 3.3 | imputada (mediana = 2) |
| `tabaco_frecuencia` | general | 546 | 18 | 3.3 | imputada (mediana = 1) |
| `golosinas_semana` | general | 546 | 17 | 3.1 | imputada (mediana = 2) |
| `considera_informacion_suficiente` | general | 428 | 13 | 3.0 | imputada (mediana = 2) |
| `cantidad_personas_cuida` | general | 257 | 7 | 2.7 | imputada (mediana = 1) |
| `frecuencia_fuerza` | general | 83 | 2 | 2.4 | imputada (mediana = 3) |
| `facilidad_uso` | satisfacción | 264 | 3 | 1.1 | no se imputa (encuesta voluntaria, Fase 39) |
| `recomendaria` | satisfacción | 264 | 3 | 1.1 | no se imputa (encuesta voluntaria, Fase 39) |
| `pregunta_11` | general | 546 | 4 | 0.7 | no se imputa (variable resultado) |
| `pregunta_4` | general | 546 | 3 | 0.5 | no se imputa (variable resultado) |
| `pregunta_5` | general | 546 | 3 | 0.5 | no se imputa (variable resultado) |
| `fatiga_mental` | satisfacción | 264 | 1 | 0.4 | no se imputa (encuesta voluntaria, Fase 39) |
| `pregunta_6` | general | 546 | 2 | 0.4 | no se imputa (variable resultado) |
| `comodidad_diseno` | satisfacción | 264 | 1 | 0.4 | no se imputa (encuesta voluntaria, Fase 39) |
| `pregunta_2` | general | 546 | 1 | 0.2 | no se imputa (variable resultado) |
| `pregunta_1` | general | 546 | 1 | 0.2 | no se imputa (variable resultado) |
| `pregunta_7` | general | 546 | 1 | 0.2 | no se imputa (variable resultado) |
| `pregunta_8` | general | 546 | 1 | 0.2 | no se imputa (variable resultado) |
| `pregunta_9` | general | 546 | 1 | 0.2 | no se imputa (variable resultado) |

Las 19 variables restantes no tienen faltantes reales.

**Fecha de última menstruación vacía:** las preguntas que dependen de ella (regularidad,
sangrado, anticonceptivo) no se imputan, porque no se sabe si aplicaban.

**IMC:** peso y talla no se imputan cuando faltan más del 30 %; el IMC queda
como `imc_categoria` con el nivel "no informado" (269 filas, 49.3 %).
Inventar el peso de tantas participantes cambiaría justamente el factor más fuerte.

Todas las encuestas son autoaplicadas: los campos solo para personal de salud
(laboratorio, presión, tamizaje, talla máxima) son "no aplica" en todas las filas.

## 4. Variables derivadas

- `edad` y `tramo_edad` a la fecha de evaluación.
- `mrs_somatico` (p1-p4), `mrs_psicologico` (p5-p8), `mrs_urogenital` (p9-p11), `mrs_total`
  y `mrs_severidad` con los cortes de `MRS.SEVERIDAD_TOTAL` (confirmados por la profesora el 20-10).
- `meses_desde_fum` y `etapa_menopausica` (STRAW+10 simplificado: ovario = NO → quirúrgica;
  ≥ 12 meses → posmenopausia; < 12 meses y regular → premenopausia; si no → perimenopausia).
- `imc`, `imc_categoria` (OMS), `perdida_talla_cm`, `presion_elevada` (≥ 140/90),
  `doble_carga` (trabaja y cuida a otras personas).

MRS completo en 529 de 546 filas. Media del total: 16.4 ± 9.3 (somático 5.9, psicológico 7.7, urogenital 2.7).

| Severidad MRS | Filas | % |
|---|---|---|
| Sin síntomas o muy leves | 56 | 10.6 % |
| Leve | 74 | 14.0 % |
| Moderada | 118 | 22.3 % |
| Severa | 281 | 53.1 % |

| Etapa | Filas | % |
|---|---|---|
| posmenopausia | 323 | 59.2 % |
| premenopausia | 100 | 18.3 % |
| perimenopausia | 82 | 15.0 % |
| indeterminada | 20 | 3.7 % |
| quirurgica | 19 | 3.5 % |
| indeterminada (histerectomía) | 2 | 0.4 % |

| Tramo de edad | Filas |
|---|---|
| 40-44 | 105 |
| 45-49 | 124 |
| 50-54 | 116 |
| 55-59 | 83 |
| 60-65 | 96 |
| <40 | 22 |

## 5. Decisiones que conviene validar con la profesora

- La definición de etapa menopáusica (los cortes del MRS los confirmó el 20-10).
- `cambio_relacion_pareja_menopausia` se trata como "no aplica" sin pareja (regla propia del
  análisis: la plataforma muestra la pregunta a todas).
- Correcciones de unidad: talla en metros (×100) y presión en cmHg (×10).
- IMC sin imputar, como categoría con "no informado".

## 6. Evaluación contra el conjunto verdadero

El conjunto sintético trae su versión sin errores y una bitácora de cada error agregado, así que
se puede medir qué tan bien funciona la limpieza. Cada celda ensuciada termina en uno de estos
estados: **recuperado** (la limpieza devolvió el valor verdadero), **imputado** (quedó un valor
estimado, distinto del verdadero), **vacío** (quedó sin dato) o **fila excluida**.

### 6.1 Filas excluidas

| Motivo | Evaluación | Filas |
|---|---|---|
| duplicado exacto | fila sucia (correcto) | 8 |
| RUT repetido (versión antigua) | fila sucia (correcto) | 7 |
| mayor de 65 años | edad alterada por el error (correcto) | 3 |
| edad no verificable (fecha de nacimiento imposible) | edad alterada por el error (correcto) | 1 |

### 6.2 Celdas ensuciadas, por tipo de error

| Tipo de error | recuperado | imputado | vacío | fila excluida | Total |
|---|---|---|---|---|---|
| omitida | 701 | 492 | 1049 | 17 | 2259 |
| omitida (cascada) | 0 | 2 | 336 | 5 | 343 |
| código escrito distinto | 231 | 0 | 3 | 2 | 236 |
| espacios sobrantes | 164 | 1 | 0 | 1 | 166 |
| formato de fecha | 107 | 0 | 0 | 1 | 108 |
| centinela de texto | 57 | 40 | 7 | 1 | 105 |
| centinela numérico | 44 | 40 | 12 | 2 | 98 |
| responde pregunta que no aplica | 27 | 4 | 0 | 1 | 32 |
| código en minúsculas | 31 | 0 | 0 | 1 | 32 |
| cintura 0 en vez de vacía | 30 | 0 | 0 | 0 | 30 |
| coma decimal | 25 | 0 | 0 | 1 | 26 |
| unidad en el texto | 25 | 0 | 0 | 0 | 25 |
| MRS fuera de rango | 0 | 0 | 17 | 0 | 17 |
| región como nombre | 12 | 0 | 0 | 1 | 13 |
| días de ejercicio sin tipo marcado | 0 | 6 | 6 | 0 | 12 |
| talla en metros | 8 | 0 | 0 | 0 | 8 |
| edad fuera del criterio 40-65 | 0 | 0 | 0 | 3 | 3 |
| píldora y terapia hormonal a la vez | 0 | 2 | 0 | 0 | 2 |
| talla sin punto decimal | 0 | 0 | 2 | 0 | 2 |
| edad imposible | 0 | 0 | 0 | 1 | 1 |

De 3518 celdas ensuciadas, 1462 (41.6 %) recuperaron su valor
verdadero (en las omisiones, "recuperado" significa que la imputación o la deducción coincidió
con el valor real). Sin contar las omisiones, que no se pueden recuperar con certeza, la
limpieza recupera el **83 %** de los errores. Los centinelas se imputan
porque el valor verdadero se perdió.

### 6.3 Celdas correctas que la limpieza cambió

Se revisaron 65353 celdas que venían bien; la limpieza cambió por error **1** (0.0 %).

| Variable | Celdas | Ejemplo | Motivo |
|---|---|---|---|
| cambio_relacion_pareja_menopausia | 196 | 1 → (vacío) | regla del análisis: "no aplica" sin pareja (la plataforma la muestra a todas) |
| circunferencia_cintura_cm | 1 | 75 → (vacío) |  |
