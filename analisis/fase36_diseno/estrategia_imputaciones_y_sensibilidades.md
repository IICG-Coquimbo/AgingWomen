# Fase 36A: estrategia de imputaciones y sensibilidades

**Estado:** propuesta para revisión. No se ejecutó ninguna sensibilidad. Se respetan las decisiones de limpieza y **nunca se usa la verdad del simulador**.

## 1. Cuatro estados de un valor

Cada celda de las 33 variables debe tener una procedencia explícita en la Fase 36B.

| Estado | Significado | Tratamiento en matrices | Tratamiento en caracterización |
|---|---|---|---|
| Observado | Respuesta presente en el conjunto sucio | Entra | Entra |
| Deducido | Se infiere de otra respuesta por lógica (por ejemplo, 1 `trabaja_actualmente`) | Entra | Entra, marcado |
| Imputado | Asignado en 34B por moda o mediana, o en 35A por la media | Entra en la capa general, marcado | Entra en la población principal; se excluye en la sensibilidad |
| No aplicable | La pregunta no se mostró | Solo como nivel estructural de cero, si existe | Se excluye; nunca es un valor de escala |

En las 30 variables generales hay **665 celdas imputadas directamente de 15.870 (4,2 %)**, a las que se suman **100 valores estructurales que dependen de una pregunta previa imputada**.

### Procedencia por celda: un vacío que debe resolverse

Las marcas `_imputado` existen solo si faltaba al menos 5 %: están en **15 de las 30 generales** y en 16 de las 33. Falta, por ejemplo, la marca de `trabaja_actualmente`. El CSV de origen da recuentos, no celdas.

**Recomendación (D-08):** en la Fase 36B, obtener la máscara por celda reconstruyendo en memoria los pasos 8 y 9 de la limpieza, como `revision_correctiva_fase34/origen_respuestas.py`, y exigir que coincida con `origen_respuestas_34D.csv` en cada variable. El módulo de auditoría carga la verdad del simulador al importarse, por lo que debe extraerse solo la parte de la reconstrucción. Esto no modifica datos ni escribe en la limpieza.

## 2. Escenarios principales

| ID | Ruta | IMC | Filas | Propósito |
|---|---|---|---|---|
| P1 | PCA | Con IMC | 529 | Base |
| P2 | PCA | Sin IMC | 529 | Comparación acordada |
| F1 | FAMD | Con IMC | 529 | Base |
| F2 | FAMD | Sin IMC | 529 | Comparación acordada |
| R0 | Sin reducción | Con y sin IMC | 529 | Referencia |

## 3. IMC

- **Hechos:** 262 de 529 imputados (49,5 %) con la media 29,23; rho con el MRS baja de 0,250 a 0,192; la falta de IMC no se asocia con la severidad (53,4 % frente a 52,8 %, p = 0,885).
- **Sin eliminación de filas:** las 262 siguen en los escenarios con y sin IMC.
- **Marca de auditoría:** `imc_fue_imputado` no entra a ninguna matriz.
- **Diagnóstico en la Fase 37:**
  - proporción de IMC imputado por clúster, para detectar grupos creados por el valor repetido;
  - acuerdo (ARI) entre con y sin IMC, en las 529 y en las 267;
  - contribución del IMC a los ejes.
- **Criterio de elección:** métricas, tamaños de los grupos, estabilidad e interpretabilidad. La regla exacta se fija antes de ejecutar la Fase 37.

## 4. Trabajo

### Capa general

Las 22 participantes con `trabaja_actualmente` imputado como Sí permanecen, con valor 1 y procedencia «imputado». Si la procedencia se pierde en la matriz, la sensibilidad no es posible, de modo que se conserva en una tabla paralela.

### Valores que no entran

| Valor en `dataset_fase35.csv` | Quiénes | n | Regla |
|---|---|---|---|
| 0 en lugar y estrés | No trabajan | 220 | No aplicable; no es un valor de escala |
| 3 en lugar y estrés | Situación laboral imputada | 22 | Relleno de la Fase 35; no es una opinión |

Las columnas laborales **no entran a las matrices generales**, así que estos valores no pueden afectar a los clústeres. En los módulos se usa el conjunto limpio, donde ambos casos están vacíos, y por tanto no hace falta recodificar el dataset.

### Sensibilidad S-TRA

| Variante | Diseño | Lectura |
|---|---|---|
| A: proyección (recomendada) | Ajustar transformación y modelo con 507; proyectar a las 22 con parámetros congelados | ARI en las 507 frente a la base; distribución de las 22 entre clústeres |
| B: punto de quiebre (opcional) | Recodificar las 22 a 0 solo en esta prueba | Si incluso el caso opuesto no cambia los perfiles, la imputación no es decisiva |

## 5. Cuidados

### Hechos

- `cantidad_personas_cuida` se mantiene entre las generales y `cuida_otras_personas` no se reincorpora.
- 278 participantes tienen cantidad = 0. En **21 de ellas, el 0 depende de `cuida_otras_personas` imputado como No**, de modo que su cero no es una respuesta observada.
- Otras 7 cantidades (dentro de las 251) son imputadas directas.
- El 0 significa «no cuida». **No equivale a sobrecarga cero:** la sobrecarga simplemente no se preguntó.

### Sensibilidad S-CUI

| Variante | Diseño | Lectura |
|---|---|---|
| A: proyección (recomendada) | Ajustar con 508; proyectar a las 21 | ARI en las 508; ubicación de las 21 |
| B: punto de quiebre (opcional) | Asignar cantidad = 1, el mínimo si cuidara, solo en esta prueba | Cota del efecto; es hipotético y no es un dato |

La identificación de las 21 está en `complementario_cuidados.py` (`cuida_imputada`).

## 6. Hallazgo adicional: ceros de ejercicio heredados

El encargo solo menciona el caso de cuidados, pero la misma situación ocurre en ejercicio:

| Variable | Ceros totales | Ceros que dependen de una imputación |
|---|---|---|
| `frecuencia_aerobico` | 424 | 29 (`realiza_aerobico`) |
| `frecuencia_bajo_impacto` | 305 | 22 (`realiza_bajo_impacto`) |
| `frecuencia_fuerza` | 448 | 28 (`realiza_fuerza`) |

**Recomendación:** agregar **S-EJE**, con el diseño de proyección de S-CUI. Se proyectan a la vez las participantes con cualquiera de los tres ceros heredados. Su número exacto se conocerá en la Fase 36B, porque las imputaciones pueden solaparse.

## 7. Módulos

| Módulo | Principal | Sensibilidad | Observación |
|---|---|---|---|
| Laboral | 287 | 263 con ambas respuestas observadas | 16 valores de lugar y 10 de estrés imputados en 34B dentro de las 287 |
| Cuidados | 239 con sobrecarga observada | 251 cuidadoras, con 12 imputadas | La pregunta menciona el trabajo y 99 de las 239 no trabajan |

Detalle en la sección 8 del protocolo.

## 8. Catálogo de sensibilidades

Se varía **un factor por vez** respecto de la configuración base que la Fase 37 seleccione, para no multiplicar combinaciones. Ninguna sensibilidad reemplaza a la base ni llega a la plataforma.

| ID | Factor | Comparación | Prioridad |
|---|---|---|---|
| S-ORD | Ordinales | Códigos consecutivos frente a ridit | Alta |
| S-FAMD | Rol de las ordinales en FAMD | Regla mixta frente a todas cuantitativas | Alta |
| S-RARA | Categorías raras en FAMD | Agrupadas frente a sin agrupar | Media |
| S-EDAD | Edad | Con y sin edad (anunciada en 35A) | Alta |
| S-TRA | 22 con situación laboral imputada | Proyección | Alta |
| S-CUI | 21 con cuidado imputado | Proyección | Alta |
| S-EJE | Ceros de ejercicio heredados | Proyección | Media |
| S-BLOQUE | Peso de los bloques | Sin ponderar frente a peso por bloque | Media |
| S-SOLAPE | `tiene_actividad_sexual` y `distension_abdominal` | Con y sin ellas | Baja |

## 9. Cómo medir el efecto

Para cada sensibilidad se informan: ARI en las filas comunes, porcentaje de asignaciones que cambian tras alinear etiquetas, cambio de tamaño de los grupos y cambio en las métricas internas. **No se proponen umbrales ahora**, para no fijarlos sin datos. Deben acordarse antes de ejecutar la Fase 37 (D-13).
