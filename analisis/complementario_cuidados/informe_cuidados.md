# Módulo de cuidados. Versión complementaria exploratoria de FCBF

*Generado por `analisis/complementario_cuidados.py` el 03-11-2026. Protocolo: `analisis/protocolo_cuidados_35b.md`. Este informe no interpreta causalidad.*

> **Análisis exploratorio y posterior a los resultados anteriores. No sustituye el resultado oficial de la Fase 35B: 0 variables seleccionadas con 5.000 permutaciones y q < 0,05 (commit `745d689`).**

## 1. Poblaciones

| Población | n |
|---|---|
| todas | 529 |
| laboral | 287 |
| cuidadoras | 251 |
| sobrecarga observada | 239 |
| sobrecarga imputada | 12 |
| sobrecarga y laboral | 130 |
| cuidadoras y laboral | 137 |
| cuida imputada no | 21 |
| cuida deducida | 4 |
| cuida imputada en observadas | 0 |
| cuida deducida en observadas | 3 |
| sobrecarga borrada por condicional | 2 |
| trabaja imputada | 22 |
| doble con trabaja imputada | 10 |
| trabaja imputada en observadas | 10 |
| trabaja imputada en sobrecarga y laboral | 0 |
| laborales observadas en 287 | 263 |
| laborales observadas en sobrecarga y laboral | 122 |

## 2. Resultado por escenario

| Escenario | Sobrecarga | n | q < | q de sobrecarga | Decisión de sobrecarga | Relevantes | Seleccionadas (adaptado) | Seleccionadas (estándar) |
|---|---|---|---|---|---|---|---|---|
| C3 | observadas | 239 | 0,05 | 0,19362 | no relevante | 2 | Días de ejercicio a la semana | Días de ejercicio a la semana |
| C4 | observadas | 239 | 0,10 | 0,19362 | no relevante | 5 | Doble carga (trabaja y cuida), Frecuencia de ejercicio de fuerza, Lugar de trabajo comprensivo | Doble carga (trabaja y cuida), Frecuencia de ejercicio de fuerza, Lugar de trabajo comprensivo |
| S3 | cuidadoras | 251 | 0,05 | 0,15365 | no relevante | 2 | Días de ejercicio a la semana | Días de ejercicio a la semana |
| S4 | cuidadoras | 251 | 0,10 | 0,15365 | no relevante | 5 | Doble carga (trabaja y cuida), Frecuencia de ejercicio de fuerza, Lugar de trabajo comprensivo | Doble carga (trabaja y cuida), Frecuencia de ejercicio de fuerza, Lugar de trabajo comprensivo |

## 3. Las 31 candidatas con 50.000 permutaciones y q < 0,10

| Variable | n | SU | p | q | Decisión (adaptado) |
|---|---|---|---|---|---|
| Lugar de trabajo comprensivo | 287 | 0,0205 | 0,01488 | 0,09225 | seleccionada |
| Sobrecarga por trabajo y cuidado | 239 | 0,0203 | 0,04178 | 0,19362 | no relevante |
| Frecuencia de ejercicio de fuerza | 529 | 0,0193 | 0,01140 | 0,09225 | seleccionada |
| Días de ejercicio a la semana | 529 | 0,0183 | 0,00244 | 0,03782 | redundante (por Frecuencia de ejercicio de fuerza) |
| Frecuencia de ejercicio de bajo impacto | 529 | 0,0167 | 0,00240 | 0,03782 | redundante (por Frecuencia de ejercicio de fuerza) |
| Estrés del entorno laboral | 287 | 0,0156 | 0,04714 | 0,19362 | no relevante |
| Tabaco | 529 | 0,0116 | 0,06212 | 0,19362 | no relevante |
| Quién prepara las comidas | 529 | 0,0107 | 0,06246 | 0,19362 | no relevante |
| Doble carga (trabaja y cuida) | 529 | 0,0094 | 0,01466 | 0,09225 | seleccionada |
| Frecuencia de ejercicio aeróbico | 529 | 0,0086 | 0,16314 | 0,33715 | no relevante |
| Cantidad de personas que cuida | 529 | 0,0078 | 0,05368 | 0,19362 | no relevante |
| Vasos de agua al día | 529 | 0,0073 | 0,08472 | 0,21886 | no relevante |
| Falta de tiempo influye en lo que come | 529 | 0,0070 | 0,10810 | 0,25777 | no relevante |
| Medicamentos para la presión | 529 | 0,0054 | 0,08134 | 0,21886 | no relevante |
| Alcohol | 529 | 0,0051 | 0,31851 | 0,54855 | no relevante |
| Comidas fuera del hogar | 529 | 0,0047 | 0,20938 | 0,40567 | no relevante |
| Frutas al día | 529 | 0,0036 | 0,40899 | 0,63394 | no relevante |
| Tiene pareja | 529 | 0,0032 | 0,13584 | 0,30078 | no relevante |
| Distensión abdominal | 529 | 0,0032 | 0,37081 | 0,60501 | no relevante |
| Pescado a la semana | 529 | 0,0030 | 0,27053 | 0,49333 | no relevante |
| Horas sentada al día | 529 | 0,0020 | 0,53023 | 0,74218 | no relevante |
| Platos de verduras al día | 529 | 0,0020 | 0,70209 | 0,87059 | no relevante |
| Legumbres a la semana | 529 | 0,0015 | 0,55065 | 0,74218 | no relevante |
| Jugos y gaseosas al día | 529 | 0,0011 | 0,78594 | 0,93709 | no relevante |
| Frecuencia de evacuación intestinal | 529 | 0,0008 | 0,86664 | 0,96494 | no relevante |
| Carnes a la semana | 529 | 0,0006 | 0,95612 | 0,96494 | no relevante |
| Panes al día | 529 | 0,0006 | 0,91684 | 0,96494 | no relevante |
| Operada para no tener más hijos | 529 | 0,0006 | 0,58353 | 0,75372 | no relevante |
| Tiene actividad sexual | 529 | 0,0006 | 0,54389 | 0,74218 | no relevante |
| Dulces y snacks a la semana | 529 | 0,0005 | 0,96494 | 0,96494 | no relevante |
| Lácteos al día | 529 | 0,0004 | 0,95974 | 0,96494 | no relevante |

## 4. Las tres variables de cuidados

| Variable | C3 | C4 | S3 | S4 |
|---|---|---|---|---|
| Doble carga (trabaja y cuida) | no relevante | seleccionada | no relevante | seleccionada |
| Cantidad de personas que cuida | no relevante | no relevante | no relevante | no relevante |
| Sobrecarga por trabajo y cuidado | no relevante | no relevante | no relevante | no relevante |

Las decisiones se informan tal como resultan del método: ninguna variable se conserva ni se retira por fuera de él.

## 5. Advertencias

- **Posterior a los resultados:** el umbral y la incorporación de la sobrecarga se decidieron conociendo ejecuciones anteriores.

- **Sobrecarga:** una SU con 239 personas no se compara directamente con una SU con 529; se lee con su n y su población.

- **No aplica:** quienes no cuidan no tienen sobrecarga 0; quedan fuera de toda medición de esta variable.

- **Población de la Etapa 3:** describe a quienes se identifican como cuidadoras y respondieron, no a todas las que cuidan.

- **Texto de la pregunta:** menciona "su trabajo" y también se muestra a cuidadoras que no trabajan.

- **`doble_carga`:** entre cuidadoras coincide con `trabaja_actualmente`; 10 de sus valores 1 dependen de `trabaja_actualmente` imputada.

- **`cantidad_personas_cuida`:** 21 de sus ceros provienen de `cuida_otras_personas` imputada como "No".

- **Laborales:** las 287 no son todas respuestas observadas; 263 tienen ambas preguntas observadas.

- **Sin estabilidad:** no se ejecutaron remuestreos para estas selecciones.

- **Carácter sintético:** refleja lo que generó el simulador, no evidencia sobre la población.

- **Interpretación:** seleccionada no significa causal, y eliminada no significa irrelevante.

## 6. Tiempo de ejecución

| Etapa | Segundos |
|---|---|
| C3 | 66,2 |
| C4 | 77,3 |
| S3 | 66,9 |
| S4 | 65,9 |
| repeticion_ultimo_escenario | 38,6 |
| total | 315,5 |
