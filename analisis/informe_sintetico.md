# Validación del conjunto sintético (Fase 34A)

Generado por `analisis/generar_sintetico.py` el 2026-10-23. Compara el conjunto **verdadero** (sin errores) con lo pedido por la profesora el 20-10. Las correlaciones son de Spearman con el puntaje MRS total.

## 1. Tamaño y MRS

- Participantes: **550** (solo usuaria común, solo primera encuesta).
- Filas del conjunto sucio: **565** (incluye duplicados y versiones antiguas).
- MRS total: **16.3 ± 9.3** (objetivo chileno 16.2).

| Severidad | n | % |
|---|---|---|
| 0-4 | 59 | 10.7 |
| 5-8 | 78 | 14.2 |
| 9-15 | 120 | 21.8 |
| 16-44 | 293 | 53.3 |

## 2. Factores validados por la profesora

| Factor | n | rho | Sentido esperado | Rango pedido | Cumple |
|---|---|---|---|---|---|
| IMC | 550 | +0.31 | + | 0.25-0.35 | sí |
| Diabetes (medicamentos) | 550 | +0.16 | + | 0.10-0.25 | sí |
| Doble carga (trabaja y cuida) | 550 | +0.11 | + | 0.10-0.25 | sí |
| Sobrecarga (quien cuida) | 273 | +0.21 | + | 0.10-0.25 | sí |
| Estrés laboral (quien trabaja) | 311 | +0.19 | + | 0.10-0.25 | sí |
| Lugar de trabajo comprensivo | 311 | -0.26 | − | 0.10-0.25 | sí |
| Días de ejercicio | 550 | -0.15 | − | 0.10-0.25 | sí |
| Vasos de agua | 550 | -0.13 | − | 0.10-0.25 | sí |
| Tabaco | 550 | +0.14 | + | 0.10-0.25 | sí |
| Alcohol | 550 | +0.12 | + | 0.10-0.25 | sí |
| Marihuana | 550 | +0.07 | + | 0.00-0.25 | sí |

Marihuana: el 94 % nunca consume, así que su rho queda bajo aunque el efecto por consumidora es el mayor; solo se exige que sea positivo.

## 3. Alimentación: ninguna protectora

| Variable | rho | p | Protectora significativa |
|---|---|---|---|
| panes_dia | +0.01 | 0.793 | no |
| golosinas_semana | -0.00 | 0.939 | no |
| jugos_gaseosas_dia | +0.05 | 0.218 | no |
| bebidas_energeticas_dia | -0.05 | 0.289 | no |
| platos_verduras_dia | -0.06 | 0.157 | no |
| frutas_dia | -0.07 | 0.092 | no |
| lacteos_dia | -0.02 | 0.600 | no |
| pescado_semana | -0.02 | 0.567 | no |
| legumbres_semana | -0.02 | 0.638 | no |
| carnes_semana | +0.01 | 0.819 | no |

## 4. Suciedad agregada

| Tipo de error | Celdas o filas |
|---|---|
| omitida | 2230 |
| omitida (cascada) | 398 |
| código escrito distinto | 231 |
| espacios sobrantes | 163 |
| formato de fecha | 120 |
| centinela de texto | 113 |
| centinela numérico | 95 |
| responde pregunta que no aplica | 35 |
| coma decimal | 28 |
| código en minúsculas | 27 |
| días de ejercicio sin tipo marcado | 25 |
| cintura 0 en vez de vacía | 24 |
| MRS fuera de rango | 22 |
| unidad en el texto | 19 |
| región como nombre | 12 |
| duplicado exacto | 9 |
| RUT repetido (versión anterior) | 6 |
| edad fuera del criterio 40-65 | 5 |
| talla en metros | 5 |
| talla sin punto decimal | 3 |
| píldora y terapia hormonal a la vez | 1 |
| peso con dígito de más | 1 |

IMC no calculable en el conjunto sucio (sin peso o sin talla): **45 %**.

**Resultado:** todos los controles se cumplen.
