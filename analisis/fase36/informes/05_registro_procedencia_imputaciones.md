# Fase 36B: registro de procedencia e imputaciones

**Detalle por celda:** `procedencia/procedencia_celdas.csv`, con 17.457 filas (529 × 33): identificador, variable, valor original, estado y marca de pregunta previa imputada. **Ninguna de estas marcas entra a las matrices.**

## Método

La limpieza 34B se repite en memoria sobre el conjunto sucio y se exige que coincida con el archivo limpio en todas las celdas. Una celda es:

| Estado | Criterio |
|---|---|
| Imputada | Vacía justo antes del paso 9 y con valor en el limpio; en el IMC, vacía en el limpio y con la media de la Fase 35A |
| Deducida | Vacía antes del paso 8 y con valor antes del paso 9 |
| Observada | El resto de las celdas con valor |
| No aplicable | Vacía porque la pregunta no se mostró |
| Faltante | Vacía aunque la pregunta aplicaba: las respuestas laborales de las 22 con trabajo imputado |

No se leyó la verdad del simulador ni la bitácora. Lo confirma un gancho de auditoría de Python: `integridad/archivos_leidos.csv`. Este módulo tampoco importa `auditoria_fase34`, que sí las carga.

## Contraste con las auditorías

| Auditoría histórica | Recuentos comparados | Coinciden |
|---|---|---|
| auditoria_figuras_34D | 32 | 32 |
| marca _imputado del conjunto limpio | 16 | 16 |
| origen_respuestas_34D | 162 | 162 |

Además, en las 16 variables con marca `_imputado` en el limpio, la máscara coincide **celda a celda**, no solo en el recuento.

## Recuento por variable (529 participantes)

| Variable | Observada | Deducida | Imputada | No aplicable | Faltante | Vacías por previa imputada |
|---|---|---|---|---|---|---|
| `edad` | 529 | 0 | 0 | 0 | 0 | 0 |
| `imc` | 267 | 0 | 262 | 0 | 0 | 0 |
| `horas_sedentarismo` | 502 | 0 | 27 | 0 | 0 | 0 |
| `trabaja_actualmente` | 506 | 1 | 22 | 0 | 0 | 0 |
| `tiene_pareja` | 501 | 0 | 28 | 0 | 0 | 0 |
| `tiene_actividad_sexual` | 499 | 0 | 30 | 0 | 0 | 0 |
| `operada_no_mas_hijos` | 511 | 0 | 18 | 0 | 0 | 0 |
| `usa_medicamentos_presion` | 499 | 0 | 30 | 0 | 0 | 0 |
| `quien_prepara_comidas` | 505 | 0 | 24 | 0 | 0 | 0 |
| `alcohol_frecuencia` | 500 | 0 | 29 | 0 | 0 | 0 |
| `cantidad_personas_cuida` | 244 | 0 | 7 | 278 | 0 | 21 |
| `carnes_semana` | 498 | 0 | 31 | 0 | 0 | 0 |
| `dias_ejercicio_semana` | 493 | 0 | 36 | 0 | 0 | 0 |
| `distension_abdominal` | 512 | 0 | 17 | 0 | 0 | 0 |
| `evacuacion_intestinal` | 497 | 0 | 32 | 0 | 0 | 0 |
| `falta_tiempo_influye` | 500 | 0 | 29 | 0 | 0 | 0 |
| `frecuencia_aerobico` | 98 | 0 | 7 | 424 | 0 | 29 |
| `frecuencia_bajo_impacto` | 209 | 0 | 15 | 305 | 0 | 22 |
| `frecuencia_comida_fuera` | 495 | 0 | 34 | 0 | 0 | 0 |
| `frecuencia_fuerza` | 79 | 0 | 2 | 448 | 0 | 28 |
| `frutas_dia` | 505 | 0 | 24 | 0 | 0 | 0 |
| `golosinas_semana` | 512 | 0 | 17 | 0 | 0 | 0 |
| `jugos_gaseosas_dia` | 499 | 0 | 30 | 0 | 0 | 0 |
| `lacteos_dia` | 500 | 0 | 29 | 0 | 0 | 0 |
| `legumbres_semana` | 505 | 0 | 24 | 0 | 0 | 0 |
| `panes_dia` | 499 | 0 | 30 | 0 | 0 | 0 |
| `pescado_semana` | 510 | 0 | 19 | 0 | 0 | 0 |
| `platos_verduras_dia` | 496 | 0 | 33 | 0 | 0 | 0 |
| `tabaco_frecuencia` | 512 | 0 | 17 | 0 | 0 | 0 |
| `vasos_agua_dia` | 505 | 0 | 24 | 0 | 0 | 0 |
| `lugar_trabajo_comprensivo` | 271 | 0 | 16 | 220 | 22 | 22 |
| `estres_entorno_laboral` | 277 | 0 | 10 | 220 | 22 | 22 |
| `sobrecarga_fisica_emocional` | 239 | 0 | 12 | 278 | 0 | 21 |

## Totales de las 30 variables generales

- **Imputadas: 927 de 15.870 (5.8 %).** Son 665 de la limpieza 34B y 262 de IMC en la Fase 35A. El diseño citaba solo las 665.
- **Valores estructurales que dependen de una pregunta previa imputada:** 100 (21 de cuidado, y 29, 22 y 28 de ejercicio).

## Poblaciones afectadas

| Grupo | n | Pregunta imputada | Tratamiento |
|---|---|---|---|
| Trabajo imputado como Sí | 22 | `trabaja_actualmente` | Siguen en la capa general; fuera del módulo laboral, porque no tienen respuestas. S-TRA |
| Cuidado imputado como No | 21 | `cuida_otras_personas` | Su cantidad = 0 no es respuesta observada. S-CUI |
| Ceros de ejercicio heredados | 75 (unión de 29, 22 y 28) | `realiza_*` | Su frecuencia = 0 no es respuesta observada. S-EJE |

Listas: `sensibilidades/poblaciones/`.

## Valores que no entran a los módulos

Los 220 valores 0 de quienes no trabajan y los 22 valores 3 de relleno de `dataset_fase35.csv` no aparecen: los módulos se toman del conjunto limpio.
