# Revisión de la Fase 35B. Primera ejecución con 10.000 permutaciones

*Generado por `analisis/revision_35b_reunion_1103.py` el 03-11-2026. Protocolo: `protocolo_revision_35b.md`.*

> **Análisis exploratorio e informativo.** Usa entropía de Shannon (log₂), información mutua y SU. Ninguna variable sale de la Fase 36 por estos resultados. Los datos son sintéticos y **ninguna asociación se interpreta como causal**.

## 1. Las 34 variables

Benjamini-Hochberg sobre una única familia de 34 pruebas. p = (1 + k) / 10.001.

| Variable | Población | n | SU | k | p | q | q < 0,10 | q < 0,05 |
|---|---|---|---|---|---|---|---|---|
| `dias_ejercicio_semana` | general | 529 | 0,0183 | 23 | 0,00240 | 0,05609 | sí | no |
| `frecuencia_bajo_impacto` | general | 529 | 0,0167 | 32 | 0,00330 | 0,05609 | sí | no |
| `imc` | general | 529 | 0,0176 | 69 | 0,00700 | 0,07933 | sí | no |
| `frecuencia_fuerza` | general | 529 | 0,0193 | 117 | 0,01180 | 0,08612 | sí | no |
| `trabaja_actualmente` | general | 529 | 0,0083 | 143 | 0,01440 | 0,08612 | sí | no |
| `lugar_trabajo_comprensivo` | laboral | 287 | 0,0205 | 151 | 0,01520 | 0,08612 | sí | no |
| `usa_medicamentos_diabetes` | general | 529 | 0,0101 | 261 | 0,02620 | 0,12724 | no | no |
| `sobrecarga_fisica_emocional` | cuidadoras | 239 | 0,0203 | 421 | 0,04220 | 0,17780 | no | no |
| `estres_entorno_laboral` | laboral | 287 | 0,0156 | 517 | 0,05179 | 0,17780 | no | no |
| `cantidad_personas_cuida` | general | 529 | 0,0078 | 522 | 0,05229 | 0,17780 | no | no |
| `quien_prepara_comidas` | general | 529 | 0,0107 | 635 | 0,06359 | 0,18273 | no | no |
| `tabaco_frecuencia` | general | 529 | 0,0116 | 644 | 0,06449 | 0,18273 | no | no |
| `usa_medicamentos_presion` | general | 529 | 0,0054 | 849 | 0,08499 | 0,21588 | no | no |
| `vasos_agua_dia` | general | 529 | 0,0073 | 888 | 0,08889 | 0,21588 | no | no |
| `falta_tiempo_influye` | general | 529 | 0,0070 | 1122 | 0,11229 | 0,25452 | no | no |
| `tiene_pareja` | general | 529 | 0,0032 | 1371 | 0,13719 | 0,29152 | no | no |
| `frecuencia_aerobico` | general | 529 | 0,0086 | 1668 | 0,16688 | 0,33377 | no | no |
| `frecuencia_comida_fuera` | general | 529 | 0,0047 | 2081 | 0,20818 | 0,39323 | no | no |
| `pescado_semana` | general | 529 | 0,0030 | 2723 | 0,27237 | 0,48740 | no | no |
| `alcohol_frecuencia` | general | 529 | 0,0051 | 3218 | 0,32187 | 0,54718 | no | no |
| `distension_abdominal` | general | 529 | 0,0032 | 3741 | 0,37416 | 0,60579 | no | no |
| `frutas_dia` | general | 529 | 0,0036 | 4064 | 0,40646 | 0,62816 | no | no |
| `horas_sedentarismo` | general | 529 | 0,0020 | 5358 | 0,53585 | 0,75200 | no | no |
| `tiene_actividad_sexual` | general | 529 | 0,0006 | 5361 | 0,53615 | 0,75200 | no | no |
| `legumbres_semana` | general | 529 | 0,0015 | 5529 | 0,55294 | 0,75200 | no | no |
| `operada_no_mas_hijos` | general | 529 | 0,0006 | 5832 | 0,58324 | 0,76270 | no | no |
| `platos_verduras_dia` | general | 529 | 0,0020 | 6990 | 0,69903 | 0,88026 | no | no |
| `jugos_gaseosas_dia` | general | 529 | 0,0011 | 7842 | 0,78422 | 0,95227 | no | no |
| `evacuacion_intestinal` | general | 529 | 0,0008 | 8676 | 0,86761 | 0,96440 | no | no |
| `panes_dia` | general | 529 | 0,0006 | 9193 | 0,91931 | 0,96440 | no | no |
| `edad` | general | 529 | 0,0010 | 9363 | 0,93631 | 0,96440 | no | no |
| `carnes_semana` | general | 529 | 0,0006 | 9582 | 0,95820 | 0,96440 | no | no |
| `lacteos_dia` | general | 529 | 0,0004 | 9632 | 0,96320 | 0,96440 | no | no |
| `golosinas_semana` | general | 529 | 0,0005 | 9644 | 0,96440 | 0,96440 | no | no |

## 2. Variables con q < 0,10

6: `dias_ejercicio_semana`, `frecuencia_bajo_impacto`, `imc`, `frecuencia_fuerza`, `trabaja_actualmente`, `lugar_trabajo_comprensivo`.

## 3. Variables con q < 0,05 (referencia)

0: ninguna.

## 4. Variables cercanas a q = 0,10

Cercana = el intervalo de Monte Carlo al 95 % de q contiene 0,10 (regla registrada antes de ver resultados).

| Variable | q | IC Monte Carlo de q | P(q < 0,10) |
|---|---|---|---|
| `lugar_trabajo_comprensivo` | 0,08612 | 0,07702 a 0,10013 | 0,974 |

## 5. FCBF informativo y redundancia

Pares evaluados entre relevantes: 15. Rótulos descriptivos: **no eliminan variables de la Fase 36**.

- **Variante adaptada (q del par < 0,10), no redundantes (4):** `frecuencia_fuerza`, `imc`, `lugar_trabajo_comprensivo`, `trabaja_actualmente`.

- **Variante estándar, no redundantes (2):** `frecuencia_fuerza`, `lugar_trabajo_comprensivo`.

| Variante | Variable | Etapa | Decisión | Redundante con | SU con severidad | SU del par | q del par |
|---|---|---|---|---|---|---|---|
| adaptado | `lugar_trabajo_comprensivo` | laboral | seleccionada | - | 0,0205 | - | - |
| adaptado | `frecuencia_fuerza` | no laboral | seleccionada | - | 0,0193 | - | - |
| adaptado | `dias_ejercicio_semana` | no laboral | redundante | `frecuencia_fuerza` | 0,0183 | 0,1655 | 0,00050 |
| adaptado | `imc` | no laboral | seleccionada | - | 0,0176 | - | - |
| adaptado | `frecuencia_bajo_impacto` | no laboral | redundante | `frecuencia_fuerza` | 0,0167 | 0,0555 | 0,00050 |
| adaptado | `trabaja_actualmente` | no laboral | seleccionada | - | 0,0083 | - | - |
| estandar | `lugar_trabajo_comprensivo` | laboral | seleccionada | - | 0,0205 | - | - |
| estandar | `frecuencia_fuerza` | no laboral | seleccionada | - | 0,0193 | - | - |
| estandar | `dias_ejercicio_semana` | no laboral | redundante | `frecuencia_fuerza` | 0,0183 | 0,1655 | 0,00050 |
| estandar | `imc` | no laboral | redundante | `frecuencia_fuerza` | 0,0176 | 0,0193 | 1,00000 |
| estandar | `frecuencia_bajo_impacto` | no laboral | redundante | `frecuencia_fuerza` | 0,0167 | 0,0555 | 0,00050 |
| estandar | `trabaja_actualmente` | no laboral | redundante | `frecuencia_fuerza` | 0,0083 | 0,0119 | 0,35584 |

**Pares evaluados:**

| Variable 1 | Variable 2 | n | SU | p | q |
|---|---|---|---|---|---|
| `dias_ejercicio_semana` | `frecuencia_bajo_impacto` | 529 | 0,2733 | 0,00010 | 0,00050 |
| `dias_ejercicio_semana` | `frecuencia_fuerza` | 529 | 0,1655 | 0,00010 | 0,00050 |
| `dias_ejercicio_semana` | `imc` | 529 | 0,0205 | 0,26857 | 0,80572 |
| `dias_ejercicio_semana` | `lugar_trabajo_comprensivo` | 287 | 0,0129 | 0,95230 | 1,00000 |
| `dias_ejercicio_semana` | `trabaja_actualmente` | 529 | 0,0022 | 0,73623 | 1,00000 |
| `frecuencia_bajo_impacto` | `frecuencia_fuerza` | 529 | 0,0555 | 0,00010 | 0,00050 |
| `frecuencia_bajo_impacto` | `imc` | 529 | 0,0110 | 0,90661 | 1,00000 |
| `frecuencia_bajo_impacto` | `lugar_trabajo_comprensivo` | 287 | 0,0199 | 0,57634 | 1,00000 |
| `frecuencia_bajo_impacto` | `trabaja_actualmente` | 529 | 0,0012 | 0,88041 | 1,00000 |
| `frecuencia_fuerza` | `imc` | 529 | 0,0193 | 0,63004 | 1,00000 |
| `frecuencia_fuerza` | `lugar_trabajo_comprensivo` | 287 | 0,0195 | 0,87511 | 1,00000 |
| `frecuencia_fuerza` | `trabaja_actualmente` | 529 | 0,0119 | 0,09489 | 0,35584 |
| `imc` | `lugar_trabajo_comprensivo` | 287 | 0,0258 | 0,60954 | 1,00000 |
| `imc` | `trabaja_actualmente` | 529 | 0,0043 | 0,64524 | 1,00000 |
| `lugar_trabajo_comprensivo` | `trabaja_actualmente` | 287 | 0,0000 | 1,00000 | 1,00000 |

**Parejas con mayor SU entre las 34** (cobertura común, sin permutaciones; detalle en `su_todas_las_parejas.csv`):

| Variable 1 | Variable 2 | n | SU |
|---|---|---|---|
| `dias_ejercicio_semana` | `frecuencia_bajo_impacto` | 529 | 0,2733 |
| `dias_ejercicio_semana` | `frecuencia_aerobico` | 529 | 0,2147 |
| `tiene_actividad_sexual` | `tiene_pareja` | 529 | 0,2019 |
| `dias_ejercicio_semana` | `frecuencia_fuerza` | 529 | 0,1655 |
| `frecuencia_aerobico` | `frecuencia_fuerza` | 529 | 0,0939 |
| `estres_entorno_laboral` | `lugar_trabajo_comprensivo` | 287 | 0,0811 |
| `frecuencia_aerobico` | `frecuencia_bajo_impacto` | 529 | 0,0788 |
| `golosinas_semana` | `sobrecarga_fisica_emocional` | 239 | 0,0615 |
| `frutas_dia` | `platos_verduras_dia` | 529 | 0,0607 |
| `frecuencia_comida_fuera` | `trabaja_actualmente` | 529 | 0,0600 |
| `cantidad_personas_cuida` | `sobrecarga_fisica_emocional` | 239 | 0,0560 |
| `frecuencia_bajo_impacto` | `frecuencia_fuerza` | 529 | 0,0555 |

## 6. Clasificación descriptiva de posibles factores

Clases fijadas en el protocolo. La columna «Un valor mayor significa» indica cómo leer el signo. No implica causalidad.

| Clase | Variable | Un valor mayor significa | n | ρ con MRS | IC 95 % | Dirección | q SU | q ρ |
|---|---|---|---|---|---|---|---|---|
| Posible factor de riesgo | `imc` | mayor IMC | 529 | +0,192 | +0,108 a +0,274 | positiva | 0,07933 | 0,00015 |
| Posible factor de riesgo | `trabaja_actualmente` | trabaja actualmente | 529 | +0,106 | +0,025 a +0,189 | positiva | 0,08612 | 0,04319 |
| Posible factor de protección | `dias_ejercicio_semana` | más días de ejercicio a la semana (1 = 0 días) | 529 | -0,151 | -0,235 a -0,070 | negativa | 0,05609 | 0,00262 |
| Posible factor de protección | `frecuencia_bajo_impacto` | ejercicio de bajo impacto más frecuente (0 = no lo realiza) | 529 | -0,166 | -0,250 a -0,085 | negativa | 0,05609 | 0,00134 |
| Posible factor de protección | `lugar_trabajo_comprensivo` | lugar de trabajo percibido como más comprensivo | 287 | -0,269 | -0,368 a -0,159 | negativa | 0,08612 | 0,00013 |
| Asociación sin dirección clara | `frecuencia_fuerza` | ejercicio de fuerza más frecuente (0 = no lo realiza) | 529 | -0,080 | -0,164 a +0,009 | mixta | 0,08612 | 0,15929 |
| Indicio de riesgo (solo orden) | `usa_medicamentos_diabetes` | usa medicamentos para la diabetes | 529 | +0,163 | +0,087 a +0,240 | positiva | 0,12724 | 0,00139 |
| Indicio de riesgo (solo orden) | `estres_entorno_laboral` | más estrés del entorno laboral | 287 | +0,195 | +0,087 a +0,297 | positiva | 0,17780 | 0,00382 |
| Indicio de riesgo (solo orden) | `sobrecarga_fisica_emocional` | sobrecarga más frecuente | 239 | +0,230 | +0,105 a +0,353 | positiva | 0,17780 | 0,00227 |
| Indicio de riesgo (solo orden) | `tabaco_frecuencia` | fuma con mayor frecuencia | 529 | +0,144 | +0,059 a +0,227 | positiva | 0,18273 | 0,00382 |
| Indicio de riesgo (solo orden) | `falta_tiempo_influye` | la falta de tiempo influye más en la alimentación | 529 | +0,098 | +0,011 a +0,181 | positiva | 0,25452 | 0,06586 |
| Indicio de riesgo (solo orden) | `alcohol_frecuencia` | consume alcohol con mayor frecuencia | 529 | +0,111 | +0,019 a +0,196 | positiva | 0,54718 | 0,03505 |
| Indicio de protección (solo orden) | `vasos_agua_dia` | más vasos de agua al día | 529 | -0,125 | -0,208 a -0,044 | negativa | 0,21588 | 0,01441 |
| Indicio de protección (solo orden) | `frutas_dia` | más frutas al día | 529 | -0,091 | -0,173 a -0,011 | negativa | 0,62816 | 0,09121 |
| Sin respaldo tras la corrección | `cantidad_personas_cuida` | más personas cuidadas (0 = no cuida) | 529 | +0,020 | -0,070 a +0,115 | mixta | 0,17780 | 0,71096 |
| Sin respaldo tras la corrección | `quien_prepara_comidas` | sin orden: no tiene signo | 529 | - | - a - | poco clara | 0,18273 | - |
| Sin respaldo tras la corrección | `usa_medicamentos_presion` | usa medicamentos para la presión | 529 | +0,050 | -0,030 a +0,134 | poco clara | 0,21588 | 0,38928 |
| Sin respaldo tras la corrección | `tiene_pareja` | tiene pareja | 529 | -0,052 | -0,133 a +0,033 | poco clara | 0,29152 | 0,38928 |
| Sin respaldo tras la corrección | `frecuencia_aerobico` | ejercicio aeróbico más frecuente (0 = no lo realiza) | 529 | -0,052 | -0,134 a +0,029 | poco clara | 0,33377 | 0,38928 |
| Sin respaldo tras la corrección | `frecuencia_comida_fuera` | más comidas preparadas fuera del hogar | 529 | +0,058 | -0,027 a +0,145 | poco clara | 0,39323 | 0,35262 |
| Sin respaldo tras la corrección | `pescado_semana` | más pescado a la semana | 529 | -0,029 | -0,114 a +0,056 | poco clara | 0,48740 | 0,68677 |
| Sin respaldo tras la corrección | `distension_abdominal` | distensión abdominal más frecuente | 529 | -0,069 | -0,160 a +0,019 | poco clara | 0,60579 | 0,24989 |
| Sin respaldo tras la corrección | `tiene_actividad_sexual` | tiene actividad sexual | 529 | +0,063 | -0,025 a +0,150 | poco clara | 0,75200 | 0,30816 |
| Sin respaldo tras la corrección | `horas_sedentarismo` | más horas sentada al día | 529 | -0,020 | -0,110 a +0,067 | poco clara | 0,75200 | 0,71096 |
| Sin respaldo tras la corrección | `legumbres_semana` | más legumbres a la semana | 529 | -0,017 | -0,098 a +0,071 | poco clara | 0,75200 | 0,73829 |
| Sin respaldo tras la corrección | `operada_no_mas_hijos` | operada para no tener más hijos | 529 | +0,043 | -0,041 a +0,127 | poco clara | 0,76270 | 0,49159 |
| Sin respaldo tras la corrección | `platos_verduras_dia` | más platos de verduras al día | 529 | -0,036 | -0,118 a +0,050 | poco clara | 0,88026 | 0,59452 |
| Sin respaldo tras la corrección | `jugos_gaseosas_dia` | más jugos o gaseosas al día | 529 | +0,022 | -0,060 a +0,111 | poco clara | 0,95227 | 0,71096 |
| Sin respaldo tras la corrección | `carnes_semana` | más carnes a la semana | 529 | +0,011 | -0,076 a +0,102 | poco clara | 0,96440 | 0,82919 |
| Sin respaldo tras la corrección | `edad` | mayor edad | 529 | +0,025 | -0,060 a +0,106 | poco clara | 0,96440 | 0,70357 |
| Sin respaldo tras la corrección | `panes_dia` | más panes al día | 529 | +0,028 | -0,056 a +0,114 | poco clara | 0,96440 | 0,69355 |
| Sin respaldo tras la corrección | `lacteos_dia` | más lácteos al día | 529 | -0,024 | -0,109 a +0,061 | poco clara | 0,96440 | 0,70357 |
| Sin respaldo tras la corrección | `evacuacion_intestinal` | evacuaciones MENOS frecuentes (escala inversa a la frecuencia) | 529 | -0,051 | -0,137 a +0,035 | poco clara | 0,96440 | 0,38928 |
| Sin respaldo tras la corrección | `golosinas_semana` | más golosinas a la semana | 529 | +0,003 | -0,083 a +0,088 | poco clara | 0,96440 | 0,93781 |

**Magnitud: categoría más baja frente a la más alta con n ≥ 10.** Diferencia = alta − baja.

| Variable | Baja | Alta | Dif. MRS (IC 95 %) | Dif. % severas (IC 95 %) | ε² | K-W p |
|---|---|---|---|---|---|---|
| `dias_ejercicio_semana` | 0 días | Todos los días | -4,32 (-9,07 a +0,44) | -33,6 (-50,6 a -4,8) | 0,0273 | 0,00612 |
| `frecuencia_bajo_impacto` | No lo realiza | Siempre | -5,52 (-10,03 a -1,01) | -40,6 (-53,9 a -15,7) | 0,0301 | 0,00316 |
| `imc` | 18,5-24,9 | >= 40 | +9,11 (+1,59 a +16,62) | +35,7 (+4,8 a +55,3) | 0,0331 | 0,00370 |
| `frecuencia_fuerza` | No lo realiza | Siempre | -5,54 (-10,80 a -0,28) | -29,9 (-46,6 a -1,3) | 0,0185 | 0,04410 |
| `lugar_trabajo_comprensivo` | Muy en desacuerdo | Muy de acuerdo | -7,87 (-12,69 a -3,06) | -32,0 (-52,5 a -4,4) | 0,0890 | 0,00004 |
| `trabaja_actualmente` | No | Sí | +2,06 (+0,48 a +3,65) | +10,8 (+2,2 a +19,2) | 0,0113 | 0,01454 |
| `usa_medicamentos_diabetes` | No | Sí | +4,74 (+2,37 a +7,11) | +15,5 (+2,6 a +26,6) | 0,0265 | 0,00018 |
| `cantidad_personas_cuida` | No cuida | 3 o más personas | -2,31 (-5,26 a +0,64) | -8,7 (-22,8 a +6,5) | 0,0167 | 0,03169 |
| `estres_entorno_laboral` | Nada de estrés | Estrés extremo | +5,57 (+1,30 a +9,84) | +25,0 (-0,3 a +47,0) | 0,0390 | 0,02481 |
| `sobrecarga_fisica_emocional` | Nunca o casi nunca | Siempre | +6,09 (-0,14 a +12,32) | +5,6 (-23,3 a +37,6) | 0,0601 | 0,00636 |
| `tabaco_frecuencia` | Nunca | Diariamente | +2,68 (+0,48 a +4,88) | +11,1 (-0,8 a +22,1) | 0,0263 | 0,00764 |
| `usa_medicamentos_presion` | No | Sí | +1,21 (-0,99 a +3,41) | +10,4 (-0,9 a +20,9) | 0,0025 | 0,24735 |
| `vasos_agua_dia` | No consumo | 7 o más porciones | -4,09 (-8,00 a -0,17) | -26,9 (-45,1 a -3,6) | 0,0160 | 0,07638 |
| `falta_tiempo_influye` | Nunca o casi nunca | Siempre | +0,07 (-5,30 a +5,45) | -0,3 (-24,5 a +25,6) | 0,0136 | 0,12677 |
| `tiene_pareja` | No | Sí | -1,05 (-2,75 a +0,65) | -7,0 (-15,8 a +2,1) | 0,0027 | 0,23074 |
| `frecuencia_aerobico` | No lo realiza | Siempre | +1,85 (-2,77 a +6,47) | +10,0 (-12,2 a +27,6) | 0,0093 | 0,29816 |
| `frecuencia_comida_fuera` | Nunca | 5-6 veces por semana | +1,73 (-3,16 a +6,61) | +23,4 (-0,4 a +39,8) | 0,0041 | 0,53820 |
| `pescado_semana` | Nunca | 3-4 veces por semana | -0,25 (-2,97 a +2,47) | -3,4 (-17,4 a +10,4) | 0,0019 | 0,59895 |
| `alcohol_frecuencia` | Nunca | Diariamente | +4,32 (-3,03 a +11,67) | +7,2 (-20,3 a +32,3) | 0,0126 | 0,15552 |
| `distension_abdominal` | Nunca o casi nunca | Siempre | -0,67 (-4,69 a +3,35) | -2,6 (-22,1 a +15,7) | 0,0089 | 0,19380 |
| `frutas_dia` | No consumo | 5-6 porciones | -3,02 (-7,69 a +1,66) | -12,8 (-34,9 a +11,4) | 0,0086 | 0,20683 |
| `horas_sedentarismo` | <= 5 | > 8 | -1,24 (-3,59 a +1,12) | -4,0 (-16,0 a +8,2) | 0,0061 | 0,35886 |
| `legumbres_semana` | Nunca | 3-4 veces por semana | -0,43 (-3,59 a +2,73) | +9,5 (-7,4 a +25,6) | 0,0003 | 0,92255 |
| `tiene_actividad_sexual` | No | Sí | +1,01 (-0,58 a +2,59) | +2,8 (-5,7 a +11,2) | 0,0039 | 0,14923 |
| `operada_no_mas_hijos` | No | Sí | +1,16 (-0,92 a +3,24) | +3,3 (-7,4 a +13,6) | 0,0018 | 0,32726 |
| `platos_verduras_dia` | No consumo | 5-6 porciones | +0,62 (-5,73 a +6,98) | +2,4 (-26,5 a +30,8) | 0,0042 | 0,52730 |
| `jugos_gaseosas_dia` | No consumo | 5-6 porciones | +1,14 (-2,59 a +4,86) | -1,5 (-18,5 a +15,4) | 0,0026 | 0,71644 |
| `carnes_semana` | Nunca | Diariamente | +2,00 (-3,74 a +7,74) | +0,0 (-27,3 a +27,3) | 0,0016 | 0,93491 |
| `edad` | 36-39 | 60-65 | +0,40 (-3,96 a +4,77) | +2,9 (-18,2 a +24,9) | 0,0018 | 0,96741 |
| `evacuacion_intestinal` | Más de una vez al día | 3 o más días entre evacuaciones | -2,75 (-6,62 a +1,12) | -7,8 (-26,3 a +11,7) | 0,0045 | 0,49985 |
| `golosinas_semana` | Nunca | Diariamente | -2,10 (-6,43 a +2,24) | -2,6 (-24,0 a +19,0) | 0,0027 | 0,84322 |
| `lacteos_dia` | No consumo | 3-4 porciones | -0,26 (-3,02 a +2,50) | +0,0 (-14,7 a +14,8) | 0,0024 | 0,73085 |
| `panes_dia` | No consumo | 5-6 porciones | +3,33 (-6,60 a +13,25) | +4,1 (-27,0 a +30,5) | 0,0018 | 0,81129 |

Las comparaciones por categoría están en `direccion_categorias.csv`.

## 7. Comparación con resultados anteriores

E1 y E4 tienen familia de 30, con `doble_carga` y sin sobrecarga. C4 tiene familia de 31. Las antiguas de control no tenían q.

| Variable | SU | q E1 (5.000) | q E4 (50.000) | q C4 (50.000) | p 50.000 | p 10.000 | q 10.000 | q 10.000, solo 30 |
|---|---|---|---|---|---|---|---|---|
| `dias_ejercicio_semana` | 0,0183 | 0,05099 | 0,03660 | 0,03782 | 0,00244 | 0,00240 | 0,05609 | 0,04950 |
| `frecuencia_bajo_impacto` | 0,0167 | 0,05099 | 0,03660 | 0,03782 | 0,00240 | 0,00330 | 0,05609 | 0,04950 |
| `imc` | 0,0176 | - | - | - | - | 0,00700 | 0,07933 | - |
| `frecuencia_fuerza` | 0,0193 | 0,08518 | 0,08928 | 0,09225 | 0,01140 | 0,01180 | 0,08612 | 0,11399 |
| `lugar_trabajo_comprensivo` | 0,0205 | 0,08518 | 0,08928 | 0,09225 | 0,01488 | 0,01520 | 0,08612 | 0,11399 |
| `trabaja_actualmente` | 0,0083 | - | - | - | - | 0,01440 | 0,08612 | - |
| `usa_medicamentos_diabetes` | 0,0101 | - | - | - | - | 0,02620 | 0,12724 | - |
| `cantidad_personas_cuida` | 0,0078 | 0,20863 | 0,20820 | 0,19362 | 0,05368 | 0,05229 | 0,17780 | 0,21498 |
| `estres_entorno_laboral` | 0,0156 | 0,20863 | 0,20820 | 0,19362 | 0,04714 | 0,05179 | 0,17780 | 0,21498 |
| `sobrecarga_fisica_emocional` | 0,0203 | - | - | 0,19362 | 0,04178 | 0,04220 | 0,17780 | 0,21498 |
| `quien_prepara_comidas` | 0,0107 | 0,20863 | 0,20820 | 0,19362 | 0,06246 | 0,06359 | 0,18273 | 0,21498 |
| `tabaco_frecuencia` | 0,0116 | 0,20863 | 0,20820 | 0,19362 | 0,06212 | 0,06449 | 0,18273 | 0,21498 |
| `vasos_agua_dia` | 0,0073 | 0,24213 | 0,23105 | 0,21886 | 0,08472 | 0,08889 | 0,21588 | 0,24243 |
| `usa_medicamentos_presion` | 0,0054 | 0,23035 | 0,23105 | 0,21886 | 0,08134 | 0,08499 | 0,21588 | 0,24243 |
| `falta_tiempo_influye` | 0,0070 | 0,27644 | 0,27025 | 0,25777 | 0,10810 | 0,11229 | 0,25452 | 0,28072 |
| `tiene_pareja` | 0,0032 | 0,32716 | 0,31347 | 0,30078 | 0,13584 | 0,13719 | 0,29152 | 0,31658 |
| `frecuencia_aerobico` | 0,0086 | 0,35650 | 0,34958 | 0,33715 | 0,16314 | 0,16688 | 0,33377 | 0,35761 |
| `frecuencia_comida_fuera` | 0,0047 | 0,41752 | 0,41875 | 0,40567 | 0,20938 | 0,20818 | 0,39323 | 0,41636 |
| `pescado_semana` | 0,0030 | 0,51027 | 0,50725 | 0,49333 | 0,27054 | 0,27237 | 0,48740 | 0,51070 |
| `alcohol_frecuencia` | 0,0051 | 0,54977 | 0,56208 | 0,54855 | 0,31851 | 0,32187 | 0,54718 | 0,56800 |
| `distension_abdominal` | 0,0032 | 0,62954 | 0,61802 | 0,60501 | 0,37081 | 0,37416 | 0,60579 | 0,62360 |
| `frutas_dia` | 0,0036 | 0,62987 | 0,64578 | 0,63394 | 0,40899 | 0,40646 | 0,62816 | 0,64178 |
| `horas_sedentarismo` | 0,0020 | 0,74603 | 0,75089 | 0,74218 | 0,53023 | 0,53585 | 0,75200 | 0,75402 |
| `legumbres_semana` | 0,0015 | 0,74603 | 0,75089 | 0,74218 | 0,55065 | 0,55294 | 0,75200 | 0,75402 |
| `tiene_actividad_sexual` | 0,0006 | 0,74603 | 0,75089 | 0,74218 | 0,54389 | 0,53615 | 0,75200 | 0,75402 |
| `operada_no_mas_hijos` | 0,0006 | 0,75872 | 0,76112 | 0,75372 | 0,58353 | 0,58324 | 0,76270 | 0,76075 |
| `platos_verduras_dia` | 0,0020 | 0,88057 | 0,87761 | 0,87059 | 0,70209 | 0,69903 | 0,88026 | 0,87379 |
| `jugos_gaseosas_dia` | 0,0011 | 0,94493 | 0,94313 | 0,93709 | 0,78594 | 0,78422 | 0,95227 | 0,94107 |
| `golosinas_semana` | 0,0005 | 0,96341 | 0,96494 | 0,96494 | 0,96494 | 0,96440 | 0,96440 | 0,96440 |
| `carnes_semana` | 0,0006 | 0,96341 | 0,96494 | 0,96494 | 0,95612 | 0,95820 | 0,96440 | 0,96440 |
| `edad` | 0,0010 | - | - | - | - | 0,93631 | 0,96440 | - |
| `evacuacion_intestinal` | 0,0008 | 0,96341 | 0,96494 | 0,96494 | 0,86664 | 0,86761 | 0,96440 | 0,96440 |
| `lacteos_dia` | 0,0004 | 0,96341 | 0,96494 | 0,96494 | 0,95974 | 0,96320 | 0,96440 | 0,96440 |
| `panes_dia` | 0,0006 | 0,96341 | 0,96494 | 0,96494 | 0,91684 | 0,91931 | 0,96440 | 0,96440 |

Cambian de clasificación respecto de C4 con q < 0,10: ninguna.

**Sensibilidades, fuera de la familia:**

| Variable | Versión | n | SU | p | q al reemplazar | ρ con MRS |
|---|---|---|---|---|---|---|
| `imc` | solo observados | 267 | 0,0284 | 0,00600 | 0,06799 | +0,250 |
| `sobrecarga_fisica_emocional` | cuidadoras, con 12 imputadas | 251 | 0,0213 | 0,03020 | 0,12834 | +0,230 |

## 8. Incertidumbre Monte Carlo

Posterior de Jeffreys para cada p, 20.000 sorteos propagados por Benjamini-Hochberg. La proyección con 50.000 es solo una referencia.

| Variable | k | p | EE de p | IC MC de p | q | IC MC de q | P(q < 0,10) | IC MC de q proyectado con 50.000 |
|---|---|---|---|---|---|---|---|---|
| `dias_ejercicio_semana` | 23 | 0,00240 | 0,00048 | 0,00150 a 0,00339 | 0,05609 | 0,04003 a 0,07241 | 1,000 | 0,04704 a 0,06393 |
| `frecuencia_bajo_impacto` | 32 | 0,00330 | 0,00057 | 0,00223 a 0,00446 | 0,05609 | 0,04020 a 0,07414 | 1,000 | 0,04704 a 0,06396 |
| `imc` | 69 | 0,00700 | 0,00083 | 0,00542 a 0,00867 | 0,07933 | 0,06144 a 0,09019 | 1,000 | 0,07072 a 0,08585 |
| `frecuencia_fuerza` | 117 | 0,01180 | 0,00108 | 0,00973 a 0,01395 | 0,08612 | 0,07671 a 0,09694 | 0,994 | 0,08103 a 0,09177 |
| `lugar_trabajo_comprensivo` | 151 | 0,01520 | 0,00122 | 0,01285 a 0,01763 | 0,08612 | 0,07702 a 0,10013 | 0,974 | 0,08103 a 0,09189 |
| `trabaja_actualmente` | 143 | 0,01440 | 0,00119 | 0,01211 a 0,01677 | 0,08612 | 0,07696 a 0,09850 | 0,987 | 0,08103 a 0,09182 |
| `usa_medicamentos_diabetes` | 261 | 0,02620 | 0,00160 | 0,02311 a 0,02936 | 0,12724 | 0,11210 a 0,14275 | 0,000 | 0,12036 a 0,13399 |
| `cantidad_personas_cuida` | 522 | 0,05229 | 0,00222 | 0,04797 a 0,05669 | 0,17780 | 0,16933 a 0,18887 | 0,000 | 0,17347 a 0,18352 |
| `estres_entorno_laboral` | 517 | 0,05179 | 0,00221 | 0,04749 a 0,05617 | 0,17780 | 0,16933 a 0,18869 | 0,000 | 0,17347 a 0,18352 |
| `sobrecarga_fisica_emocional` | 421 | 0,04220 | 0,00201 | 0,03830 a 0,04617 | 0,17780 | 0,16250 a 0,18509 | 0,000 | 0,17149 a 0,18177 |
| `quien_prepara_comidas` | 635 | 0,06359 | 0,00244 | 0,05885 a 0,06841 | 0,18273 | 0,17447 a 0,19606 | 0,000 | 0,17831 a 0,18890 |
| `tabaco_frecuencia` | 644 | 0,06449 | 0,00246 | 0,05971 a 0,06934 | 0,18273 | 0,17458 a 0,19699 | 0,000 | 0,17831 a 0,18891 |
| `vasos_agua_dia` | 888 | 0,08889 | 0,00284 | 0,08334 a 0,09449 | 0,21588 | 0,20487 a 0,22938 | 0,000 | 0,20995 a 0,22193 |
| `usa_medicamentos_presion` | 849 | 0,08499 | 0,00279 | 0,07956 a 0,09048 | 0,21588 | 0,20431 a 0,22567 | 0,000 | 0,20995 a 0,22121 |
| `falta_tiempo_influye` | 1122 | 0,11229 | 0,00316 | 0,10613 a 0,11850 | 0,25452 | 0,24041 a 0,26878 | 0,000 | 0,24819 a 0,26078 |
| `tiene_pareja` | 1371 | 0,13719 | 0,00344 | 0,13046 a 0,14395 | 0,29152 | 0,27705 a 0,30561 | 0,000 | 0,28509 a 0,29788 |

Se muestran las 16 con menor q; el resto está en `incertidumbre_monte_carlo.csv`.

**Estabilidad numérica:** dos corridas idénticas; SU igual a la guardada y a una implementación independiente en las 34.

## 9. Recomendación técnica

**Según la regla registrada, se recomienda ejecutar 50.000 permutaciones.** Motivo: variables cuyo intervalo de Monte Carlo de q contiene 0,10: lugar_trabajo_comprensivo.

La ejecución de 50.000 **no se realizó** y requiere autorización expresa.

## 10. Advertencias

- **Exploratorio:** la lista de variables y el umbral se fijaron conociendo resultados anteriores.

- **`evacuacion_intestinal`:** un valor mayor significa evacuaciones menos frecuentes.

- **`cantidad_personas_cuida`:** se mide en las 529, con 0 = no cuida; su signo mezcla cuidar o no cuidar con cuántas personas.

- **`imc`:** 262 de 529 valores están imputados y caen en 25-29,9; ver la sensibilidad con observadas.

- **`trabaja_actualmente`:** 22 valores imputados como True; la variable es constante entre las 287.

- **Consecuencias posibles:** `distension_abdominal` puede solaparse con síntomas, y los medicamentos pueden ser consecuencia o marcar otra condición.

- **Sobrecarga:** describe a quienes se identifican como cuidadoras y respondieron; la pregunta menciona «su trabajo».

- **Poblaciones:** una SU con 239 o 287 personas no se compara directamente con una con 529.

## 11. Tiempo de ejecución

| Etapa | Segundos |
|---|---|
| permutaciones | 7,2 |
| repeticion | 7,3 |
| total | 18,6 |
