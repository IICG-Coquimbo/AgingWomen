# Fase 35B. Análisis complementario exploratorio

*Generado por `analisis/complementario_fase35b.py` el 02-11-2026. Protocolo: `analisis/protocolo_complementario_35b.md`. Este informe no interpreta causalidad.*

> **Análisis exploratorio, posterior a la ejecución original. No sustituye el resultado oficial de la Fase 35B: 0 variables seleccionadas con 5.000 permutaciones y q < 0,05 (commit `745d689`).**

## 1. Resultado del análisis complementario (50.000 permutaciones, q < 0,10)

- Relevantes: **5**: Días de ejercicio a la semana, Doble carga (trabaja y cuida), Frecuencia de ejercicio de bajo impacto, Frecuencia de ejercicio de fuerza, Lugar de trabajo comprensivo.

- Eliminadas por redundancia con la variante adaptada: Días de ejercicio a la semana, Frecuencia de ejercicio de bajo impacto.

- Seleccionadas con FCBF adaptado: **3**: Doble carga (trabaja y cuida), Frecuencia de ejercicio de fuerza, Lugar de trabajo comprensivo.

- Seleccionadas con FCBF estándar: **3**: Doble carga (trabaja y cuida), Frecuencia de ejercicio de fuerza, Lugar de trabajo comprensivo.

## 2. Comparación de los cuatro escenarios

Cada escenario calcula de nuevo la relevancia, sus pares y FCBF. No se deduce de otro cambiando el umbral.

| Escenario | Permutaciones | q < | Relevantes | Pares evaluados | Redundantes adaptado | Seleccionadas adaptado | Redundantes estándar | Seleccionadas estándar |
|---|---|---|---|---|---|---|---|---|
| E1 | 5.000 | 0,05 | 0 | 0 | 0 | 0 | 0 | 0 |
| E2 | 5.000 | 0,10 | 5 | 10 | 2 | 3 | 2 | 3 |
| E3 | 50.000 | 0,05 | 2 | 1 | 1 | 1 | 1 | 1 |
| E4 | 50.000 | 0,10 | 5 | 10 | 2 | 3 | 2 | 3 |

**Decisión por escenario, FCBF adaptado** (variables relevantes en algún escenario):

| Variable | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| Lugar de trabajo comprensivo | no relevante | seleccionada | no relevante | seleccionada |
| Frecuencia de ejercicio de fuerza | no relevante | seleccionada | no relevante | seleccionada |
| Días de ejercicio a la semana | no relevante | redundante (por Frecuencia de ejercicio de fuerza) | seleccionada | redundante (por Frecuencia de ejercicio de fuerza) |
| Frecuencia de ejercicio de bajo impacto | no relevante | redundante (por Frecuencia de ejercicio de fuerza) | redundante (por Días de ejercicio a la semana) | redundante (por Frecuencia de ejercicio de fuerza) |
| Doble carga (trabaja y cuida) | no relevante | seleccionada | no relevante | seleccionada |

**Decisión por escenario, FCBF estándar** (variables relevantes en algún escenario):

| Variable | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| Lugar de trabajo comprensivo | no relevante | seleccionada | no relevante | seleccionada |
| Frecuencia de ejercicio de fuerza | no relevante | seleccionada | no relevante | seleccionada |
| Días de ejercicio a la semana | no relevante | redundante (por Frecuencia de ejercicio de fuerza) | seleccionada | redundante (por Frecuencia de ejercicio de fuerza) |
| Frecuencia de ejercicio de bajo impacto | no relevante | redundante (por Frecuencia de ejercicio de fuerza) | redundante (por Días de ejercicio a la semana) | redundante (por Frecuencia de ejercicio de fuerza) |
| Doble carga (trabaja y cuida) | no relevante | seleccionada | no relevante | seleccionada |

## 3. Las 30 candidatas con 50.000 permutaciones

| Variable | Grupo | n | SU | p | q | Relevante (q < 0,10) |
|---|---|---|---|---|---|---|
| Lugar de trabajo comprensivo | laboral | 287 | 0,0205 | 0,01488 | 0,08928 | sí |
| Frecuencia de ejercicio de fuerza | no laboral | 529 | 0,0193 | 0,01140 | 0,08928 | sí |
| Días de ejercicio a la semana | no laboral | 529 | 0,0183 | 0,00244 | 0,03660 | sí |
| Frecuencia de ejercicio de bajo impacto | no laboral | 529 | 0,0167 | 0,00240 | 0,03660 | sí |
| Estrés del entorno laboral | laboral | 287 | 0,0156 | 0,04714 | 0,20820 | no |
| Tabaco | no laboral | 529 | 0,0116 | 0,06212 | 0,20820 | no |
| Quién prepara las comidas | no laboral | 529 | 0,0107 | 0,06246 | 0,20820 | no |
| Doble carga (trabaja y cuida) | no laboral | 529 | 0,0094 | 0,01466 | 0,08928 | sí |
| Frecuencia de ejercicio aeróbico | no laboral | 529 | 0,0086 | 0,16314 | 0,34958 | no |
| Cantidad de personas que cuida | no laboral | 529 | 0,0078 | 0,05368 | 0,20820 | no |
| Vasos de agua al día | no laboral | 529 | 0,0073 | 0,08472 | 0,23105 | no |
| Falta de tiempo influye en lo que come | no laboral | 529 | 0,0070 | 0,10810 | 0,27024 | no |
| Medicamentos para la presión | no laboral | 529 | 0,0054 | 0,08134 | 0,23105 | no |
| Alcohol | no laboral | 529 | 0,0051 | 0,31851 | 0,56208 | no |
| Comidas fuera del hogar | no laboral | 529 | 0,0047 | 0,20938 | 0,41875 | no |
| Frutas al día | no laboral | 529 | 0,0036 | 0,40899 | 0,64578 | no |
| Tiene pareja | no laboral | 529 | 0,0032 | 0,13584 | 0,31347 | no |
| Distensión abdominal | no laboral | 529 | 0,0032 | 0,37081 | 0,61802 | no |
| Pescado a la semana | no laboral | 529 | 0,0030 | 0,27053 | 0,50725 | no |
| Horas sentada al día | no laboral | 529 | 0,0020 | 0,53023 | 0,75088 | no |
| Platos de verduras al día | no laboral | 529 | 0,0020 | 0,70209 | 0,87761 | no |
| Legumbres a la semana | no laboral | 529 | 0,0015 | 0,55065 | 0,75088 | no |
| Jugos y gaseosas al día | no laboral | 529 | 0,0011 | 0,78594 | 0,94313 | no |
| Frecuencia de evacuación intestinal | no laboral | 529 | 0,0008 | 0,86664 | 0,96494 | no |
| Carnes a la semana | no laboral | 529 | 0,0006 | 0,95612 | 0,96494 | no |
| Panes al día | no laboral | 529 | 0,0006 | 0,91684 | 0,96494 | no |
| Operada para no tener más hijos | no laboral | 529 | 0,0006 | 0,58353 | 0,76112 | no |
| Tiene actividad sexual | no laboral | 529 | 0,0006 | 0,54389 | 0,75088 | no |
| Dulces y snacks a la semana | no laboral | 529 | 0,0005 | 0,96494 | 0,96494 | no |
| Lácteos al día | no laboral | 529 | 0,0004 | 0,95974 | 0,96494 | no |

## 4. Pares evaluados con 50.000 permutaciones y q < 0,10

| Variable 1 | Variable 2 | n | SU | p | q | q < 0,10 |
|---|---|---|---|---|---|---|
| Días de ejercicio a la semana | Doble carga (trabaja y cuida) | 529 | 0,0035 | 0,55107 | 0,97771 | no |
| Días de ejercicio a la semana | Frecuencia de ejercicio de bajo impacto | 529 | 0,2733 | 0,00002 | 0,00007 | sí |
| Días de ejercicio a la semana | Frecuencia de ejercicio de fuerza | 529 | 0,1655 | 0,00002 | 0,00007 | sí |
| Días de ejercicio a la semana | Lugar de trabajo comprensivo | 287 | 0,0129 | 0,95302 | 0,97948 | no |
| Doble carga (trabaja y cuida) | Frecuencia de ejercicio de bajo impacto | 529 | 0,0054 | 0,28223 | 0,70559 | no |
| Doble carga (trabaja y cuida) | Frecuencia de ejercicio de fuerza | 529 | 0,0023 | 0,84340 | 0,97948 | no |
| Doble carga (trabaja y cuida) | Lugar de trabajo comprensivo | 287 | 0,0007 | 0,97948 | 0,97948 | no |
| Frecuencia de ejercicio de bajo impacto | Frecuencia de ejercicio de fuerza | 529 | 0,0555 | 0,00002 | 0,00007 | sí |
| Frecuencia de ejercicio de bajo impacto | Lugar de trabajo comprensivo | 287 | 0,0199 | 0,58663 | 0,97771 | no |
| Frecuencia de ejercicio de fuerza | Lugar de trabajo comprensivo | 287 | 0,0195 | 0,87528 | 0,97948 | no |

## 5. Qué cambia con cada parámetro

- **Más permutaciones** mejoran la precisión con que se estima cada valor p. No hacen más permisiva la prueba.

- **Subir el umbral a 0,10** hace menos estricta la selección y aumenta el riesgo de incluir variables por azar: se tolera que, en promedio, hasta cerca de 1 de cada 10 variables declaradas relevantes sea un falso positivo.

## 6. Advertencias

- **Posterior a los resultados:** el umbral se eligió conociendo la ejecución oficial, por lo que este análisis no es confirmatorio.

- **Sin estabilidad ni sensibilidad:** no se ejecutaron remuestreos ni S1-S5 para estas selecciones.

- **Fuerza de la relación:** un q más bajo no indica una relación más fuerte; hay que leerlo junto con la SU.

- **Carácter sintético:** refleja lo que generó el simulador, no evidencia sobre la población.

- **Circularidad:** seleccionar por severidad puede hacer que los clústeres difieran en severidad por esa misma selección.

- **Interpretación:** seleccionada no significa causal, y eliminada no significa irrelevante.

- **Poblaciones distintas:** la SU laboral describe a trabajadoras (n = 287) y la no laboral a todas (n = 529).

- **`doble_carga`:** es función exacta de `trabaja_actualmente` y `cantidad_personas_cuida`, y sigue en consulta con la profesora.

## 7. Tiempo de ejecución

| Etapa | Segundos |
|---|---|
| E1 | 2,8 |
| E2 | 3,4 |
| E3 | 28,0 |
| E4 | 37,4 |
| repeticion_ultimo_escenario | 35,6 |
| total | 107,3 |
