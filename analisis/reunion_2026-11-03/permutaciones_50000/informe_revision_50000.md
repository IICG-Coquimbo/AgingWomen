# Revisión de la Fase 35B. Versión B: 50.000 permutaciones

*Generado por `analisis/revision_35b_50000.py` el 03-11-2026. Protocolo: `protocolo_revision_35b.md` y `adenda_50000_permutaciones.md`.*

> **Análisis complementario de la versión A (10.000 permutaciones), que no se reemplaza.** Usa entropía de Shannon, información mutua y SU. Ninguna variable sale de la Fase 36. Datos sintéticos; ninguna asociación se interpreta como causal. La comparación de ambas versiones está en `informe_integrado/`.

## 1. Las 34 variables

p = (1 + k) / 50.001; Benjamini-Hochberg sobre una familia de 34 pruebas; q < 0,10 exploratorio.

| Variable | Población | n | SU | k | p | q | q < 0,10 | q < 0,05 |
|---|---|---|---|---|---|---|---|---|
| `dias_ejercicio_semana` | general | 529 | 0,0183 | 102 | 0,00206 | 0,04726 | sí | sí |
| `frecuencia_bajo_impacto` | general | 529 | 0,0167 | 138 | 0,00278 | 0,04726 | sí | sí |
| `imc` | general | 529 | 0,0176 | 367 | 0,00736 | 0,08341 | sí | no |
| `frecuencia_fuerza` | general | 529 | 0,0193 | 596 | 0,01194 | 0,09214 | sí | no |
| `lugar_trabajo_comprensivo` | laboral | 287 | 0,0205 | 776 | 0,01554 | 0,09214 | sí | no |
| `trabaja_actualmente` | general | 529 | 0,0083 | 812 | 0,01626 | 0,09214 | sí | no |
| `usa_medicamentos_diabetes` | general | 529 | 0,0101 | 1219 | 0,02440 | 0,11851 | no | no |
| `sobrecarga_fisica_emocional` | cuidadoras | 239 | 0,0203 | 2059 | 0,04120 | 0,17510 | no | no |
| `estres_entorno_laboral` | laboral | 287 | 0,0156 | 2447 | 0,04896 | 0,17770 | no | no |
| `cantidad_personas_cuida` | general | 529 | 0,0078 | 2656 | 0,05314 | 0,17770 | no | no |
| `tabaco_frecuencia` | general | 529 | 0,0116 | 3087 | 0,06176 | 0,17770 | no | no |
| `quien_prepara_comidas` | general | 529 | 0,0107 | 3135 | 0,06272 | 0,17770 | no | no |
| `usa_medicamentos_presion` | general | 529 | 0,0054 | 4006 | 0,08014 | 0,20783 | no | no |
| `vasos_agua_dia` | general | 529 | 0,0073 | 4278 | 0,08558 | 0,20783 | no | no |
| `falta_tiempo_influye` | general | 529 | 0,0070 | 5495 | 0,10992 | 0,24915 | no | no |
| `tiene_pareja` | general | 529 | 0,0032 | 6824 | 0,13650 | 0,29006 | no | no |
| `frecuencia_aerobico` | general | 529 | 0,0086 | 8247 | 0,16496 | 0,32991 | no | no |
| `frecuencia_comida_fuera` | general | 529 | 0,0047 | 10605 | 0,21212 | 0,40066 | no | no |
| `pescado_semana` | general | 529 | 0,0030 | 13508 | 0,27017 | 0,48347 | no | no |
| `alcohol_frecuencia` | general | 529 | 0,0051 | 15882 | 0,31765 | 0,54001 | no | no |
| `distension_abdominal` | general | 529 | 0,0032 | 18406 | 0,36813 | 0,59602 | no | no |
| `frutas_dia` | general | 529 | 0,0036 | 20104 | 0,40209 | 0,62141 | no | no |
| `horas_sedentarismo` | general | 529 | 0,0020 | 26548 | 0,53097 | 0,74820 | no | no |
| `tiene_actividad_sexual` | general | 529 | 0,0006 | 27059 | 0,54119 | 0,74820 | no | no |
| `legumbres_semana` | general | 529 | 0,0015 | 27507 | 0,55015 | 0,74820 | no | no |
| `operada_no_mas_hijos` | general | 529 | 0,0006 | 29176 | 0,58353 | 0,76308 | no | no |
| `platos_verduras_dia` | general | 529 | 0,0020 | 35004 | 0,70009 | 0,88159 | no | no |
| `jugos_gaseosas_dia` | general | 529 | 0,0011 | 39247 | 0,78494 | 0,95315 | no | no |
| `evacuacion_intestinal` | general | 529 | 0,0008 | 43403 | 0,86806 | 0,96374 | no | no |
| `panes_dia` | general | 529 | 0,0006 | 45878 | 0,91756 | 0,96374 | no | no |
| `edad` | general | 529 | 0,0010 | 46905 | 0,93810 | 0,96374 | no | no |
| `carnes_semana` | general | 529 | 0,0006 | 47872 | 0,95744 | 0,96374 | no | no |
| `lacteos_dia` | general | 529 | 0,0004 | 48024 | 0,96048 | 0,96374 | no | no |
| `golosinas_semana` | general | 529 | 0,0005 | 48187 | 0,96374 | 0,96374 | no | no |

## 2. FCBF informativo

Pares evaluados: 15. Rótulos descriptivos: no eliminan variables de la Fase 36.

| Variante | Variable | Etapa | Decisión | Redundante con | SU con severidad | SU del par | q del par |
|---|---|---|---|---|---|---|---|
| adaptado | `lugar_trabajo_comprensivo` | laboral | seleccionada | - | 0,0205 | - | - |
| adaptado | `frecuencia_fuerza` | no laboral | seleccionada | - | 0,0193 | - | - |
| adaptado | `dias_ejercicio_semana` | no laboral | redundante | `frecuencia_fuerza` | 0,0183 | 0,1655 | 0,00010 |
| adaptado | `imc` | no laboral | seleccionada | - | 0,0176 | - | - |
| adaptado | `frecuencia_bajo_impacto` | no laboral | redundante | `frecuencia_fuerza` | 0,0167 | 0,0555 | 0,00010 |
| adaptado | `trabaja_actualmente` | no laboral | seleccionada | - | 0,0083 | - | - |
| estandar | `lugar_trabajo_comprensivo` | laboral | seleccionada | - | 0,0205 | - | - |
| estandar | `frecuencia_fuerza` | no laboral | seleccionada | - | 0,0193 | - | - |
| estandar | `dias_ejercicio_semana` | no laboral | redundante | `frecuencia_fuerza` | 0,0183 | 0,1655 | 0,00010 |
| estandar | `imc` | no laboral | redundante | `frecuencia_fuerza` | 0,0176 | 0,0193 | 1,00000 |
| estandar | `frecuencia_bajo_impacto` | no laboral | redundante | `frecuencia_fuerza` | 0,0167 | 0,0555 | 0,00010 |
| estandar | `trabaja_actualmente` | no laboral | redundante | `frecuencia_fuerza` | 0,0083 | 0,0119 | 0,35572 |

## 3. Pares evaluados

| Variable 1 | Variable 2 | n | SU | p | q |
|---|---|---|---|---|---|
| `dias_ejercicio_semana` | `frecuencia_bajo_impacto` | 529 | 0,2733 | 0,00002 | 0,00010 |
| `dias_ejercicio_semana` | `frecuencia_fuerza` | 529 | 0,1655 | 0,00002 | 0,00010 |
| `dias_ejercicio_semana` | `imc` | 529 | 0,0205 | 0,26829 | 0,80488 |
| `dias_ejercicio_semana` | `lugar_trabajo_comprensivo` | 287 | 0,0129 | 0,95212 | 1,00000 |
| `dias_ejercicio_semana` | `trabaja_actualmente` | 529 | 0,0022 | 0,73327 | 1,00000 |
| `frecuencia_bajo_impacto` | `frecuencia_fuerza` | 529 | 0,0555 | 0,00002 | 0,00010 |
| `frecuencia_bajo_impacto` | `imc` | 529 | 0,0110 | 0,90320 | 1,00000 |
| `frecuencia_bajo_impacto` | `lugar_trabajo_comprensivo` | 287 | 0,0199 | 0,58523 | 1,00000 |
| `frecuencia_bajo_impacto` | `trabaja_actualmente` | 529 | 0,0012 | 0,88154 | 1,00000 |
| `frecuencia_fuerza` | `imc` | 529 | 0,0193 | 0,63275 | 1,00000 |
| `frecuencia_fuerza` | `lugar_trabajo_comprensivo` | 287 | 0,0195 | 0,87184 | 1,00000 |
| `frecuencia_fuerza` | `trabaja_actualmente` | 529 | 0,0119 | 0,09486 | 0,35572 |
| `imc` | `lugar_trabajo_comprensivo` | 287 | 0,0258 | 0,61205 | 1,00000 |
| `imc` | `trabaja_actualmente` | 529 | 0,0043 | 0,64435 | 1,00000 |
| `lugar_trabajo_comprensivo` | `trabaja_actualmente` | 287 | 0,0000 | 1,00000 | 1,00000 |

## 4. Clasificación descriptiva

| Clase | Variable | Un valor mayor significa | ρ con MRS | Dirección | q SU | q ρ |
|---|---|---|---|---|---|---|
| Asociación sin dirección clara | `frecuencia_fuerza` | ejercicio de fuerza más frecuente (0 = no lo realiza) | -0,080 | mixta | 0,09214 | 0,15929 |
| Indicio de protección (solo orden) | `vasos_agua_dia` | más vasos de agua al día | -0,125 | negativa | 0,20783 | 0,01441 |
| Indicio de protección (solo orden) | `frutas_dia` | más frutas al día | -0,091 | negativa | 0,62141 | 0,09121 |
| Indicio de riesgo (solo orden) | `usa_medicamentos_diabetes` | usa medicamentos para la diabetes | +0,163 | positiva | 0,11851 | 0,00139 |
| Indicio de riesgo (solo orden) | `sobrecarga_fisica_emocional` | sobrecarga más frecuente | +0,230 | positiva | 0,17510 | 0,00227 |
| Indicio de riesgo (solo orden) | `estres_entorno_laboral` | más estrés del entorno laboral | +0,195 | positiva | 0,17770 | 0,00382 |
| Indicio de riesgo (solo orden) | `tabaco_frecuencia` | fuma con mayor frecuencia | +0,144 | positiva | 0,17770 | 0,00382 |
| Indicio de riesgo (solo orden) | `falta_tiempo_influye` | la falta de tiempo influye más en la alimentación | +0,098 | positiva | 0,24915 | 0,06586 |
| Indicio de riesgo (solo orden) | `alcohol_frecuencia` | consume alcohol con mayor frecuencia | +0,111 | positiva | 0,54001 | 0,03505 |
| Posible factor de protección | `dias_ejercicio_semana` | más días de ejercicio a la semana (1 = 0 días) | -0,151 | negativa | 0,04726 | 0,00262 |
| Posible factor de protección | `frecuencia_bajo_impacto` | ejercicio de bajo impacto más frecuente (0 = no lo realiza) | -0,166 | negativa | 0,04726 | 0,00134 |
| Posible factor de protección | `lugar_trabajo_comprensivo` | lugar de trabajo percibido como más comprensivo | -0,269 | negativa | 0,09214 | 0,00013 |
| Posible factor de riesgo | `imc` | mayor IMC | +0,192 | positiva | 0,08341 | 0,00015 |
| Posible factor de riesgo | `trabaja_actualmente` | trabaja actualmente | +0,106 | positiva | 0,09214 | 0,04319 |
| Sin respaldo tras la corrección | `cantidad_personas_cuida` | más personas cuidadas (0 = no cuida) | +0,020 | mixta | 0,17770 | 0,71096 |
| Sin respaldo tras la corrección | `quien_prepara_comidas` | sin orden: no tiene signo | - | poco clara | 0,17770 | - |
| Sin respaldo tras la corrección | `usa_medicamentos_presion` | usa medicamentos para la presión | +0,050 | poco clara | 0,20783 | 0,38928 |
| Sin respaldo tras la corrección | `tiene_pareja` | tiene pareja | -0,052 | poco clara | 0,29006 | 0,38928 |
| Sin respaldo tras la corrección | `frecuencia_aerobico` | ejercicio aeróbico más frecuente (0 = no lo realiza) | -0,052 | poco clara | 0,32991 | 0,38928 |
| Sin respaldo tras la corrección | `frecuencia_comida_fuera` | más comidas preparadas fuera del hogar | +0,058 | poco clara | 0,40066 | 0,35262 |
| Sin respaldo tras la corrección | `pescado_semana` | más pescado a la semana | -0,029 | poco clara | 0,48347 | 0,68677 |
| Sin respaldo tras la corrección | `distension_abdominal` | distensión abdominal más frecuente | -0,069 | poco clara | 0,59602 | 0,24989 |
| Sin respaldo tras la corrección | `horas_sedentarismo` | más horas sentada al día | -0,020 | poco clara | 0,74820 | 0,71096 |
| Sin respaldo tras la corrección | `legumbres_semana` | más legumbres a la semana | -0,017 | poco clara | 0,74820 | 0,73829 |
| Sin respaldo tras la corrección | `tiene_actividad_sexual` | tiene actividad sexual | +0,063 | poco clara | 0,74820 | 0,30816 |
| Sin respaldo tras la corrección | `operada_no_mas_hijos` | operada para no tener más hijos | +0,043 | poco clara | 0,76308 | 0,49159 |
| Sin respaldo tras la corrección | `platos_verduras_dia` | más platos de verduras al día | -0,036 | poco clara | 0,88159 | 0,59452 |
| Sin respaldo tras la corrección | `jugos_gaseosas_dia` | más jugos o gaseosas al día | +0,022 | poco clara | 0,95315 | 0,71096 |
| Sin respaldo tras la corrección | `carnes_semana` | más carnes a la semana | +0,011 | poco clara | 0,96374 | 0,82919 |
| Sin respaldo tras la corrección | `edad` | mayor edad | +0,025 | poco clara | 0,96374 | 0,70357 |
| Sin respaldo tras la corrección | `evacuacion_intestinal` | evacuaciones MENOS frecuentes (escala inversa a la frecuencia) | -0,051 | poco clara | 0,96374 | 0,38928 |
| Sin respaldo tras la corrección | `golosinas_semana` | más golosinas a la semana | +0,003 | poco clara | 0,96374 | 0,93781 |
| Sin respaldo tras la corrección | `lacteos_dia` | más lácteos al día | -0,024 | poco clara | 0,96374 | 0,70357 |
| Sin respaldo tras la corrección | `panes_dia` | más panes al día | +0,028 | poco clara | 0,96374 | 0,69355 |

## 5. Incertidumbre Monte Carlo

| Variable | k | p | EE de p | q | IC MC de q | P(q < 0,10) | Cercana a 0,10 |
|---|---|---|---|---|---|---|---|
| `dias_ejercicio_semana` | 102 | 0,00206 | 0,00020 | 0,04726 | 0,03974 a 0,05516 | 1,000 | no |
| `frecuencia_bajo_impacto` | 138 | 0,00278 | 0,00024 | 0,04726 | 0,03974 a 0,05519 | 1,000 | no |
| `imc` | 367 | 0,00736 | 0,00038 | 0,08341 | 0,07498 a 0,09128 | 1,000 | no |
| `frecuencia_fuerza` | 596 | 0,01194 | 0,00049 | 0,09214 | 0,08728 a 0,09807 | 0,996 | no |
| `lugar_trabajo_comprensivo` | 776 | 0,01554 | 0,00055 | 0,09214 | 0,08728 a 0,09840 | 0,994 | no |
| `trabaja_actualmente` | 812 | 0,01626 | 0,00057 | 0,09214 | 0,08728 a 0,09842 | 0,993 | no |
| `usa_medicamentos_diabetes` | 1219 | 0,02440 | 0,00069 | 0,11851 | 0,11193 a 0,12518 | 0,000 | no |
| `sobrecarga_fisica_emocional` | 2059 | 0,04120 | 0,00089 | 0,17510 | 0,16773 a 0,17942 | 0,000 | no |
| `cantidad_personas_cuida` | 2656 | 0,05314 | 0,00100 | 0,17770 | 0,17291 a 0,18222 | 0,000 | no |
| `estres_entorno_laboral` | 2447 | 0,04896 | 0,00096 | 0,17770 | 0,17290 a 0,18195 | 0,000 | no |
| `quien_prepara_comidas` | 3135 | 0,06272 | 0,00108 | 0,17770 | 0,17340 a 0,18384 | 0,000 | no |
| `tabaco_frecuencia` | 3087 | 0,06176 | 0,00108 | 0,17770 | 0,17340 a 0,18382 | 0,000 | no |
| `usa_medicamentos_presion` | 4006 | 0,08014 | 0,00121 | 0,20783 | 0,20164 a 0,21179 | 0,000 | no |
| `vasos_agua_dia` | 4278 | 0,08558 | 0,00125 | 0,20783 | 0,20198 a 0,21382 | 0,000 | no |
| `falta_tiempo_influye` | 5495 | 0,10992 | 0,00140 | 0,24915 | 0,24295 a 0,25531 | 0,000 | no |
| `tiene_pareja` | 6824 | 0,13650 | 0,00154 | 0,29006 | 0,28361 a 0,29640 | 0,000 | no |
| `frecuencia_aerobico` | 8247 | 0,16496 | 0,00166 | 0,32991 | 0,32358 a 0,33642 | 0,000 | no |
| `frecuencia_comida_fuera` | 10605 | 0,21212 | 0,00183 | 0,40066 | 0,39392 a 0,40737 | 0,000 | no |
| `pescado_semana` | 13508 | 0,27017 | 0,00199 | 0,48347 | 0,47650 a 0,49038 | 0,000 | no |
| `alcohol_frecuencia` | 15882 | 0,31765 | 0,00208 | 0,54001 | 0,53306 a 0,54705 | 0,000 | no |
| `distension_abdominal` | 18406 | 0,36813 | 0,00216 | 0,59602 | 0,58910 a 0,60291 | 0,000 | no |
| `frutas_dia` | 20104 | 0,40209 | 0,00219 | 0,62141 | 0,61463 a 0,62812 | 0,000 | no |
| `horas_sedentarismo` | 26548 | 0,53097 | 0,00223 | 0,74820 | 0,74230 a 0,75412 | 0,000 | no |
| `legumbres_semana` | 27507 | 0,55015 | 0,00222 | 0,74820 | 0,74230 a 0,75412 | 0,000 | no |
| `tiene_actividad_sexual` | 27059 | 0,54119 | 0,00223 | 0,74820 | 0,74230 a 0,75412 | 0,000 | no |
| `operada_no_mas_hijos` | 29176 | 0,58353 | 0,00220 | 0,76308 | 0,75737 a 0,76866 | 0,000 | no |
| `platos_verduras_dia` | 35004 | 0,70009 | 0,00205 | 0,88159 | 0,87653 a 0,88657 | 0,000 | no |
| `jugos_gaseosas_dia` | 39247 | 0,78494 | 0,00184 | 0,95315 | 0,94874 a 0,95745 | 0,000 | no |
| `carnes_semana` | 47872 | 0,95744 | 0,00090 | 0,96374 | 0,96205 a 0,96538 | 0,000 | no |
| `edad` | 46905 | 0,93810 | 0,00108 | 0,96374 | 0,96205 a 0,96538 | 0,000 | no |
| `evacuacion_intestinal` | 43403 | 0,86806 | 0,00151 | 0,96374 | 0,96205 a 0,96538 | 0,000 | no |
| `golosinas_semana` | 48187 | 0,96374 | 0,00084 | 0,96374 | 0,96205 a 0,96538 | 0,000 | no |
| `lacteos_dia` | 48024 | 0,96048 | 0,00087 | 0,96374 | 0,96205 a 0,96538 | 0,000 | no |
| `panes_dia` | 45878 | 0,91756 | 0,00123 | 0,96374 | 0,96205 a 0,96538 | 0,000 | no |

## 6. Sensibilidades, fuera de la familia

| Variable | Versión | n | SU | p | q al reemplazar | ρ con MRS |
|---|---|---|---|---|---|---|
| `imc` | solo observados | 267 | 0,0284 | 0,00612 | 0,06936 | +0,250 |
| `sobrecarga_fisica_emocional` | cuidadoras, con 12 imputadas | 251 | 0,0213 | 0,03010 | 0,12792 | +0,230 |

## 7. Tiempo de ejecución

| Etapa | Segundos |
|---|---|
| reproduccion_version_a | 9,5 |
| permutaciones | 33,6 |
| repeticion | 34,1 |
| comprobacion_anidamiento | 33,3 |
| total | 114,7 |
