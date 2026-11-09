# Fase 40D-1 — Reglas preliminares de personalización (BORRADOR)

> **Nota de actualización (2026-11-09):** B1 sí se muestra a la participante en su tablero, por decisión de la responsable para la revisión de la profesora guía (Fase 40D-H), con la advertencia de que es exploratorio y no es un diagnóstico. Sigue sin seleccionar ni modificar orientaciones (C-5) y no aparece en la ficha individual del profesional. La indicación «no recomendado por ahora» quedó reemplazada.

**Estado:** diseño preliminar, sin código. Las decisiones marcadas como **[decidir]** quedan para la revisión.

## 1. Principios

1. **Solo respuestas individuales.** Una orientación se destaca por lo que la participante respondió en la pregunta MRS correspondiente, nunca por asociaciones estadísticas ni por grupos de caracterización (ver §6 y el informe, §5).
2. **Solo rondas cerradas y verificables.** Se usa el MRS de una ronda cuyo resultado es `DEFINITIVO` según la regla única de `apps/rondas/resultado_mrs.py` (Fases 40B-3 y 40C). Nunca se usan:
   - una ronda abierta, aunque su suma sea provisional;
   - una ronda «Histórica no verificable»;
   - una ronda incompleta.
3. **Sin severidad total.** No se usan las categorías de `MRS.SEVERIDAD_TOTAL`, ni el puntaje total, ni los puntajes por dimensión, para decidir qué mostrar.
4. **Sin interpretar cambios.** No se compara una ronda con otra: no hay mensajes de «mejoraste», «empeoraste» ni «se mantiene».
5. **Deterministas y explicables.** Con las mismas respuestas y la misma versión del catálogo, el resultado es siempre el mismo, y cada orientación mostrada dice por qué aparece.

## 2. Datos de entrada

| Entrada | Origen | Nota |
|---|---|---|
| Ronda de referencia | La **última ronda cerrada** de la participante | Ver R-1 |
| Respuestas `pregunta_1`…`pregunta_11` de esa ronda | Modelo `MRS` (valores 0 a 4: Ninguna, Leve, Moderada, Intensa, Muy intensa) | Son las opciones de respuesta del instrumento, no categorías de severidad |
| Estado del resultado | `resultado_mrs(mrs).estado` | Debe ser `DEFINITIVO` |
| Versión del catálogo | Archivo versionado (40A, §40D) | Se registra junto a la selección |

No se usan datos sociodemográficos, actuales ni históricos.

## 3. Reglas

**R-1 · Ronda de referencia**
- Se toma la última ronda cerrada.
- Si su resultado no es `DEFINITIVO`, **no hay selección personalizada**. Se muestra el aviso general, la biblioteca completa de temas y un mensaje: «Todavía no hay una ronda finalizada con resultado verificable para personalizar estas orientaciones».
- **[decidir]** Alternativa: usar la última ronda *verificable*, aunque haya otra más reciente no verificable. Se propone **no** hacerlo, para no orientar con respuestas desactualizadas.

**R-2 · Orientaciones destacadas**
- La orientación `O-i` se destaca si la respuesta a `pregunta_i` en la ronda de referencia es **2 o más** (Moderada, Intensa o Muy intensa).
- **[decidir]** El umbral es una decisión de diseño, no clínica. Alternativas:
  - ≥ 1 (cualquier molestia): más orientaciones;
  - ≥ 3: solo molestias intensas.

**R-3 · Orden y cantidad**
- Las destacadas se ordenan por respuesta, de mayor a menor. Si empatan, se ordenan por el número de pregunta.
- Se muestran como máximo **3**, para no saturar la pantalla. Las demás quedan en «Otros temas que marcaste», plegadas.
- Las orientaciones con respuesta 0 o 1 **no se destacan**, pero siguen disponibles en la biblioteca completa («Todos los temas»).

**R-4 · Mensaje de apoyo (ánimo)**
- Si `pregunta_5` ≥ 3 (Intensa o Muy intensa), se muestra **primero**, fuera del límite de 3, un mensaje de apoyo breve con la Línea \*4141 y Salud Responde (O-05).
- Esto retoma T-26 de la 40A.
- **[decidir]** (DR-6): el umbral (≥ 3 o ≥ 2), el texto exacto y si el profesional ve una marca.
- Limitación: el MRS **no pregunta por pensamientos suicidas**. El mensaje no puede presumirlos; solo ofrece apoyo.

**R-5 · Señales de alerta siempre visibles**
- Dentro de cada orientación mostrada, la sección de señales de alerta y la de «¿Cuándo consultar…?» se muestran siempre, sin plegar.
- No dependen de la respuesta: un síntoma marcado como «Leve» también puede presentar una señal de alerta.

**R-6 · Sin orientaciones destacadas**
- Si ninguna respuesta llega al umbral, se muestra: «En tu última ronda finalizada no marcaste molestias moderadas o mayores. Igual puedes revisar todos los temas», junto con la biblioteca.
- No se felicita ni se interpreta como «estar bien».

**R-7 · Explicación visible**
- Cada orientación destacada dice por qué aparece, sin calificar. Por ejemplo: «Aparece porque en la ronda 3 respondiste "Intensa" a la pregunta sobre bochornos».

**R-8 · Trazabilidad** (40A, §40D, para la 40D-2)
- Se registra:
  - la versión del catálogo;
  - la ronda de referencia;
  - los identificadores de las orientaciones mostradas y la regla que activó cada una.
- No se registran los valores en los logs.

## 4. Pseudocódigo (ilustrativo; no es implementación)

```
seleccionar(ficha, catalogo):
    ronda = última ronda cerrada de la ficha
    si ronda es None o resultado_mrs(mrs de la ronda).estado != DEFINITIVO:
        return {personalizada: False, motivo: 'sin_ronda_verificable'}
    r = respuestas pregunta_1..11 de esa ronda
    apoyo = r[5] >= UMBRAL_APOYO                         # R-4 [decidir]
    destacadas = [O-i para i en 1..11 si r[i] >= UMBRAL] # R-2 [decidir]
    ordenar destacadas por (-r[i], i)                    # R-3
    return {personalizada: True, ronda, apoyo,
            principales: destacadas[:3], otras: destacadas[3:],
            version: catalogo.version}
```

## 5. Casos de prueba previstos para la 40D-2 (ligados a los criterios C-1 a C-8)

| Caso | Esperado | Criterio |
|---|---|---|
| Ronda abierta con respuestas altas | Sin selección personalizada | Principio 2 |
| Última ronda cerrada «Histórica no verificable» | Sin selección; mensaje de R-1 | Principio 2 |
| Respuestas 4, 4, 4, 2 y el resto 0 | 3 principales ordenadas y 1 en «otras» | R-3 |
| Mismas entradas dos veces | Misma salida | Principio 5 |
| Todas en 0 o 1 | Mensaje de R-6, sin felicitar | R-6, C-7 |
| `pregunta_5` = 4 | Mensaje de apoyo primero, con \*4141 | R-4, C-4 |
| Cambio entre rondas | Ningún texto de mejoría o empeoramiento | Principio 4 |
| Puntaje total ≥ 16 con todas las respuestas en 1 | Ninguna destacada (el total no decide) | Principio 3 |
| Cualquier página de orientaciones | Aviso general visible y sin confirmación previa | C-1, C-8 |
| Cada orientación | Tiene «¿Cuándo consultar…?» con fuente | C-2, C-6 |
| Todo el catálogo | Sin expresiones vetadas (diagnóstico, fármacos, «suspenda») | C-3, C-7 |
| Grupo de caracterización | No interviene en la selección | C-5 |

## 6. Grupos de caracterización

**No se usan para seleccionar orientaciones.** Se documenta como **no recomendado por ahora**; la justificación está en `40D-1_informe.md`, §5. Si en el futuro se aprobara mostrar la etiqueta B1 (Fase 40E), sería solo un texto descriptivo aparte, que no activa ni ordena orientaciones (C-5).
