# Alcance

Esta nota prepara las reglas de asociación. **No ejecuta Apriori, FP-Growth ni otro algoritmo, no fija umbrales y no inicia las Fases 38 ni 39.** Las candidatas se proponen por su significado y su calidad de datos, **no por haber resultado asociadas con el MRS en esta fase**: seleccionarlas así sería usar dos veces los mismos datos.

Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales ni tienen valor clínico.

# Candidatas a antecedentes

| Grupo | Variables | Observación |
|---|---|---|
| Contexto | trabajo, pareja, cuidado (número de personas) | Base para comparaciones condicionadas |
| Actividad física | días de ejercicio; aeróbico, bajo impacto y fuerza | Muy relacionadas entre sí: conviene elegir una forma o agrupar |
| Sedentarismo | horas sentada | Numérica: requiere cortes fijados de antemano |
| Alimentación | 12 frecuencias y quién prepara | Muchas categorías poco frecuentes: agrupar antes |
| Tabaco y alcohol | frecuencias | Tabaco: «nunca» domina (75 %); conviene binarizar |
| Salud | medicamentos para presión y diabetes, IMC | IMC solo en 267; diabetes con imputaciones sin marca |
| Módulos | lugar comprensivo, estrés laboral, sobrecarga | Solo en subpoblaciones: reglas separadas |
| Descriptivas | edad (en tramos), etapa menopáusica | La etapa no fue predictora (decisión del 01-11); usarla solo en análisis descriptivos |

# Candidatos a consecuentes

- **Severidad:** `severo_mrs` (≥ 16) como consecuente principal, que es el objetivo acordado el 27-10. La severidad en 4 clases puede servir como alternativa.
- **Dimensiones:** solo si se fija un corte de antemano, por ejemplo el percentil 75 o un umbral del instrumento. No conviene elegir el corte mirando las reglas.
- **Ítems intensos:** ítems con respuesta 3 o 4, solo como análisis exploratorio.

# Riesgos

- **Circularidad:**
  - Actividad sexual y pareja frente al ítem 9 y la dimensión urogenital.
  - Distensión y evacuación frente a síntomas somáticos.
  - Estrés laboral y sobrecarga, que pueden ser consecuencias de los síntomas.
  - Los segmentos A o B1 como antecedentes repetirían trabajo, pareja y ejercicio.
- **Redundancia:**
  - Días de ejercicio y frecuencias de ejercicio.
  - Trabajo y módulo laboral, que están anidados.
  - Cuidado y sobrecarga.
  - Edad y etapa.
  - B1 es una función exacta de tres variables. Sin tratar esto, aparecerán reglas triviales.
- **Datos faltantes:** IMC (49,5 % sin observar) y módulos parciales. Las imputaciones de la limpieza afectan al 72,8 % de las participantes. Conviene repetir las reglas solo con datos observados.
- **Frecuencias insuficientes:** 34 categorías tienen menos del 5 % de las participantes, entre ellas ejercicio de 5-6 días (15) y todos los días (12), «otro» en quién prepara (7), FFAA (7) y la etapa quirúrgica (19). Reglas con esas categorías tendrían soporte mínimo. Conviene agrupar de antemano. La lista completa está en `resultados/descripcion/caracteristicas_categorias.csv`.

# Posibles análisis

1. **Generales:** reglas sobre las 529 con antecedentes agrupados y `severo_mrs` como consecuente.
2. **Condicionados:** reglas por separado según trabajo (sí o no), pareja (sí o no), ejercicio (3 días o más frente a menos) y cuidado (sí o no). Son las condiciones que definen B1.
3. **Subpoblaciones:** reglas laborales solo en quienes trabajan y de sobrecarga solo en quienes cuidan.
4. **Segmentos:** solo como estratificación descriptiva, nunca como antecedente junto a las variables que los definen.

# Decisiones pendientes de la responsable

- Elegir A, B1 o ninguna segmentación como estratificación de las reglas. Esta fase no cambia la conclusión de la Fase 37C.
- Fijar las agrupaciones de categorías, los cortes de las variables numéricas y el consecuente.
- Fijar, antes de ver las reglas, los umbrales de soporte, confianza y lift, y el control de reglas espurias (por ejemplo, permutaciones o una muestra de confirmación).
