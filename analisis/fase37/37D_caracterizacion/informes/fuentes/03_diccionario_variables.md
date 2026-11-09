# Alcance

Variables usadas en la Fase 37D: 29 que usa el Modelo A, 7 externas a A y las del MRS. El significado de cada código viene de la Fase 36 (`fase36/artefactos/P2/esquema_variables.json`) y de la limpieza, no del nombre de la variable. La tabla completa, con la codificación de cada nivel, está en `diccionario/diccionario_variables_37D.csv`.

Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales ni tienen valor clínico.

# Características

| Variable | Bloque | Tipo | Población | Obs. | Imp. | No aplica | Falt. | n análisis |
|---|---|---|---|---|---|---|---|---|
| Trabaja actualmente | Las tres preguntas | binaria | Las 529 | 506 | 22 | — | — | 529 |
| Tiene pareja | Las tres preguntas | binaria | Las 529 | 501 | 28 | — | — | 529 |
| Días de ejercicio a la semana | Las tres preguntas | ordinal | Las 529 | 493 | 36 | — | — | 529 |
| Frecuencia de ejercicio aeróbico | Actividad física adicional | ordinal | Las 529 | 98 | 7 | 424 | — | 529 |
| Frecuencia de ejercicio de bajo impacto | Actividad física adicional | ordinal | Las 529 | 209 | 15 | 305 | — | 529 |
| Frecuencia de ejercicio de fuerza | Actividad física adicional | ordinal | Las 529 | 79 | 2 | 448 | — | 529 |
| Horas sentada al día | Sedentarismo | cuantitativa | Las 529 | 502 | 27 | — | — | 529 |
| Personas a su cuidado | Cuidados | ordinal | Las 529 | 244 | 7 | 278 | — | 529 |
| Quién prepara las comidas | Alimentación | nominal | Las 529 | 505 | 24 | — | — | 529 |
| Carnes a la semana | Alimentación | ordinal | Las 529 | 498 | 31 | — | — | 529 |
| La falta de tiempo influye en su alimentación | Alimentación | ordinal | Las 529 | 500 | 29 | — | — | 529 |
| Comidas fuera de casa | Alimentación | ordinal | Las 529 | 495 | 34 | — | — | 529 |
| Frutas al día | Alimentación | ordinal | Las 529 | 505 | 24 | — | — | 529 |
| Golosinas a la semana | Alimentación | ordinal | Las 529 | 512 | 17 | — | — | 529 |
| Jugos o gaseosas al día | Alimentación | ordinal | Las 529 | 499 | 30 | — | — | 529 |
| Lácteos al día | Alimentación | ordinal | Las 529 | 500 | 29 | — | — | 529 |
| Legumbres a la semana | Alimentación | ordinal | Las 529 | 505 | 24 | — | — | 529 |
| Panes al día | Alimentación | ordinal | Las 529 | 499 | 30 | — | — | 529 |
| Pescado a la semana | Alimentación | ordinal | Las 529 | 510 | 19 | — | — | 529 |
| Platos de verduras al día | Alimentación | ordinal | Las 529 | 496 | 33 | — | — | 529 |
| Vasos de agua al día | Alimentación | ordinal | Las 529 | 505 | 24 | — | — | 529 |
| Frecuencia de tabaco | Tabaco y alcohol | ordinal | Las 529 | 512 | 17 | — | — | 529 |
| Frecuencia de alcohol | Tabaco y alcohol | ordinal | Las 529 | 500 | 29 | — | — | 529 |
| Edad | Otras generales | cuantitativa | Las 529 | 529 | — | — | — | 529 |
| Operada para no tener más hijos | Otras generales | binaria | Las 529 | 511 | 18 | — | — | 529 |
| Usa medicamentos para la presión | Otras generales | binaria | Las 529 | 499 | 30 | — | — | 529 |
| Tiene actividad sexual | Actividad sexual | binaria | Las 529 | 499 | 30 | — | — | 529 |
| Distensión abdominal | Digestión | ordinal | Las 529 | 512 | 17 | — | — | 529 |
| Evacuación intestinal | Digestión | ordinal | Las 529 | 497 | 32 | — | — | 529 |
| IMC (solo observado) | Externa: salud | cuantitativa | Solo IMC observado | 267 | 262 | — | — | 267 |
| Etapa menopáusica | Externa: etapa | nominal | Las 529 | — | — | — | — | 529 |
| Usa medicamentos para la diabetes | Externa: salud | binaria | Las 529 | — | — | — | — | 529 |
| Previsión de salud | Externa: acceso a salud | nominal | Las 529 | — | — | — | — | 529 |
| Lugar de trabajo comprensivo | Externa: módulo laboral | ordinal | Solo quienes trabajan | 271 | 16 | 220 | 22 | 287 |
| Estrés en el entorno laboral | Externa: módulo laboral | ordinal | Solo quienes trabajan | 277 | 10 | 220 | 22 | 287 |
| Sobrecarga física o emocional por cuidar | Externa: módulo de cuidados | ordinal | Solo quienes cuidan | 239 | 12 | 278 | — | 251 |


- **«—» en estado:** son variables tomadas de la limpieza (etapa, diabetes, previsión), que no tienen marca de imputación por participante. Según la Fase 34D, diabetes tiene 23 imputadas y previsión 19 imputadas y 2 deducidas; la etapa depende de respuestas imputadas en 27 participantes.
- **No aplica:** en ejercicio y cuidado es un 0 estructural («no realiza», «no cuida»). En los módulos laboral y de cuidados queda fuera del análisis.
- **IMC:** se usa solo el observado (267). La imputación por la media de la Fase 35 no se usa.

# MRS

| Variable | Contenido | Codificación |
|---|---|---|
| pregunta_1 | MRS ítem 1: Bochornos, sudoración | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_2 | MRS ítem 2: Molestias al corazón | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_3 | MRS ítem 3: Molestias musculares y articulares | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_4 | MRS ítem 4: Dificultades en el sueño | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_5 | MRS ítem 5: Ánimo depresivo | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_6 | MRS ítem 6: Irritabilidad | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_7 | MRS ítem 7: Ansiedad | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_8 | MRS ítem 8: Cansancio físico y mental | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_9 | MRS ítem 9: Problemas sexuales | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_10 | MRS ítem 10: Problemas con la orina | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| pregunta_11 | MRS ítem 11: Sequedad vaginal | 0 = Ninguna; 1 = Leve; 2 = Moderada; 3 = Intensa; 4 = Muy intensa |
| mrs_somatico | Dimensión somática | Suma de los ítems 1 a 4 (0 a 16) |
| mrs_psicologico | Dimensión psicológica | Suma de los ítems 5 a 8 (0 a 16) |
| mrs_urogenital | Dimensión urogenital | Suma de los ítems 9 a 11 (0 a 12) |
| mrs_total | MRS total | Suma de los 11 ítems (0 a 44) |
| severidad | severidad | 0-4 sin síntomas o muy leves; 5-8 leve; 9-15 moderada; 16 o más severa |
| severo_mrs | severo_mrs | 1 si el total es 16 o más |
| mrs_total_sin9 | mrs_total_sin9 | Total sin el ítem 9, solo para la sensibilidad S-SIN9 |
| mrs_urogenital_sin9 | mrs_urogenital_sin9 | Urogenital sin el ítem 9, solo para S-SIN9 |


Las dimensiones siguen el orden de ítems del proyecto (`limpieza/reglas.py`), que no es el de la publicación original del MRS. Los cortes de severidad son los del modelo de la plataforma (leído sin modificarlo). Los once ítems están completos en las 529 participantes.
