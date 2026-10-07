# Supuestos de simulación (Paso 1)

> Define de dónde sale cada respuesta de las participantes simuladas. No contiene código:
> el generador es el Paso 2 y se construye leyendo este documento.
> Fecha: 2026-10-06 · Rama `datos-simulados`.

## 0. Cómo leer este documento

Cada número lleva una etiqueta según la fuente:

| Etiqueta | Nivel | Significado |
|---|---|---|
| **[C]** | Región de Coquimbo | Dato oficial de la región |
| **[N]** | Chile | Dato nacional, cuando no hay dato regional |
| **[L]** | Latinoamérica / internacional | Literatura o el dataset de Jordania (solo para relaciones entre variables) |
| **[S]** | Supuesto propio | Sin fuente directa; valor razonable que **debe validar la profesora** |

Copias de los informes usados en `datos/fuentes/`. Lista completa de fuentes al final (§11).

---

## 1. Diseño de la muestra (decisiones aprobadas)

| Parámetro | Valor | Detalle |
|---|---|---|
| Participantes | **N = 200** por defecto | Configurable (`--n`) |
| Rondas | Las 200 hacen la ronda 1; **50 hacen también la ronda 2** | **250 encuestas** en total |
| Plazo entre rondas | ≥ 15 días | Regla de la Fase 31 (`plazo.py`); se simulan entre 15 y 120 días |
| Quién aplica la encuesta | **30 % personal de salud**, 70 % autoaplicada | Solo con personal de salud se llenan los 14 campos clínicos del EMPA (`origen_registro = MEDICO`) |
| Respuestas en blanco | **~5 %** de las preguntas **opcionales** | Las obligatorias nunca quedan vacías |
| Excepción de edad | **5 % (10 mujeres) de 36 a 39 años** | Todas con `excepcion_edad = QUIRURGICA` (histerectomía y/o ooforectomía) |
| Reproducibilidad | Semilla fija | Misma semilla → mismos datos |

**Ronda 2:** la persona es la misma (identificación, comuna, educación y previsión no cambian). Cambia poco:
síntomas MRS ±1 punto en algunos ítems (con leve tendencia a mejorar si inició terapia hormonal o ejercicio),
peso ±2 kg, y ~10 % cambia algún hábito. Si estaba en perimenopausia puede pasar a posmenopausia.

---

## 2. Cadena de generación

No se sortea cada pregunta por separado: cada bloque depende de los anteriores, para que no salgan
personas incoherentes.

```
1. Perfil base        edad, comuna, educación, origen, pueblo originario, trabajo, previsión
        │
2. Etapa reproductiva pre / peri / posmenopausia natural / quirúrgica
        │              → última menstruación, útero, ovarios, anticonceptivos, terapia hormonal
3. Salud crónica      HTA, diabetes, IMC (según edad y educación)
        │              → medicamentos, valores del EMPA
4. Estilo de vida     ejercicio, alimentación, tabaco, alcohol
        │
5. Cuidado y trabajo  cuida a otras personas, estrés laboral
        │
6. Síntomas MRS       nivel latente de síntomas ← etapa, ejercicio, sobrecarga, estrés, IMC
        │
7. Consecuencias      sección Trabajo, antidepresivos, conocimiento del sistema de salud
```

Los efectos entre variables son **moderados** (tamaño similar al del dataset de Jordania: R² ≈ 0,18
para calidad de vida), para no fabricar relaciones más fuertes que las reales.

---

## 3. Perfil base (sección Identificación)

### Edad
Proporcional a las mujeres de la región por tramo **[C] Censo 2024**:

| Tramo | Mujeres en Coquimbo | Peso |
|---|---|---|
| 40-44 | 30.220 | 25,0 % |
| 45-49 | 29.334 | 24,3 % |
| 50-54 | 28.170 | 23,3 % |
| 55-59 | 27.740 | 22,9 % |
| 60 | ≈ 5.550 (1/5 del tramo 55-59) **[S]** | 4,5 % |

Edad uniforme dentro de cada tramo. Más el 5 % de excepciones de 36-39 años (§1).
`fecha_nacimiento` = fecha de la encuesta − edad − día aleatorio.

### Comuna (`region_residencia` = Coquimbo para todas)
Proporcional a la población femenina por comuna **[C] Censo 2024** (total 449.019 mujeres):

| Comuna | % | Comuna | % | Comuna | % |
|---|---|---|---|---|---|
| Coquimbo | 31,5 | Vicuña | 3,5 | Andacollo | 1,3 |
| La Serena | 30,5 | Salamanca | 3,3 | Canela | 1,1 |
| Ovalle | 14,1 | Los Vilos | 2,7 | Paiguano | 0,5 |
| Illapel | 3,8 | Combarbalá | 1,6 | La Higuera | 0,5 |
| Monte Patria | 3,7 | Punitaqui | 1,4 | Río Hurtado | 0,5 |

Con 200 personas, las comunas de 0,5 % tendrán 0-2 participantes; es lo esperable.

### Género
Femenino 99 %, "Prefiero no decirlo" 1 % **[S]** (el estudio es de mujeres).

### Origen / procedencia
Chilena 96,4 %, extranjera 3,6 % **[C] Casen 2022** (por provincia: Elqui 3,9 %, Limarí 2,2 %, Choapa 4,2 %).
Entre las extranjeras: Venezuela 35 %, Perú 15 %, Colombia 15 %, Bolivia 10 %, Haití 10 %, Argentina 5 %,
Ecuador 3 %, otra 7 % **[S]**, con la forma de la migración nacional.

### Pueblo originario / afrodescendiente
Se identifica con alguno: Elqui 5,6 %, Limarí 9,4 %, Choapa 5,0 % según la provincia de la comuna **[C] Casen 2022**.
Entre ellas: Diaguita 57,8 %, Mapuche 25,5 %, Aymara 6,9 %, Chango 4,5 %, Colla 1,9 %, Quechua 0,9 %,
otro 2,5 % **[C] Casen 2022**.

### Nivel educacional
Calibrado a la escolaridad promedio regional de 12,6 años **[C] Casen 2022**, un poco más bajo por ser una
generación mayor **[S]**:

| Nivel | % |
|---|---|
| Sin estudios | 1 |
| Básica incompleta | 8 |
| Básica completa | 7 |
| Media incompleta | 10 |
| Media completa | 32 |
| Superior no universitaria incompleta | 4 |
| Superior no universitaria completa | 14 |
| Universitaria incompleta | 5 |
| Universitaria completa | 15 |
| Postgrado | 4 |

### Trabaja actualmente
**58 %** sí. Base: tasa de ocupación de mujeres de Coquimbo 44,5 % (15 años y más, may-jul 2026)
**[C] INE-ENE**, ajustada hacia arriba porque 40-60 años es el tramo de mayor ocupación **[S]**.
Menor con baja educación y en mayores de 55 **[S]**.

### Previsión de salud
Mujeres en Chile **[N] Casen 2022**: Fonasa 81,2 %, Isapre 13,8 %, FF.AA. 1,5 %, ninguna 2,6 %, no sé 0,9 %.
Isapre más probable con educación universitaria y si trabaja **[S]**.
Ojo: la mayor parte de la sección "Conocimiento del sistema de salud" solo aparece si responde Fonasa.

---

## 4. Etapa reproductiva (cuestionario complementario)

### Edad a la menopausia natural
Normal con media **49 años**, DE 3,5 (recortada entre 40 y 58) **[L]** (mediana 48 en el estudio
multicéntrico latinoamericano REDLINC; 50 en un estudio chileno pequeño).

### Etapa resultante
| Etapa | Regla | Esperado (40-60 años) |
|---|---|---|
| Premenopausia | Edad < edad de menopausia − 4 | ~30 % |
| Perimenopausia | Dentro de los 4 años previos a la menopausia | ~20 % |
| Posmenopausia natural | Edad ≥ edad de menopausia | ~43 % |
| Quirúrgica | Histerectomía y/o ooforectomía, **7 %** de 40-60 **[S]** + las 10 excepciones <40 | ~7 % + 5 % |

Referencia de validación: 48,8 % posmenopáusicas con edad media de 49 años **[L] REDLINC**.

### Preguntas derivadas
| Pregunta | Regla |
|---|---|
| Fecha de la última menstruación | Pre/peri: en los últimos 1-6 meses. Posmenopausia: año en que cumplió la edad de menopausia. **30 % responde solo el año** **[S]** |
| Menstruación llega (si menstruó en <12 meses) | Pre: regular 75 %, irregular 20 %, no sé 5 %. Peri: regular 20 %, irregular 75 %, no sé 5 % **[S]** |
| Tipo de sangrado | Moderado 45 %, leve 25 %, abundante 15 %, muy leve 8 %, muy abundante 7 %; en peri sube "abundante" **[S]** |
| Usa anticonceptivo (si menstruó en <12 meses) | 40 % sí **[S]** |
| Tipo de anticonceptivo | DIU 30 %, oral 20 %, preservativo 20 %, implante 10 %, inyectable 10 %, otro 5 %, no sé 5 % **[S]** |
| Operada para no tener más hijos | 20 % **[S]** (esterilización tubaria) |
| Tiene útero | No en histerectomía (7 % + excepciones) |
| Tiene al menos un ovario | No en 40 % de las quirúrgicas (ooforectomía bilateral) **[S]** |
| Terapia hormonal | Posmenopausia/quirúrgica: **10 %** **[N]** (estudio MUSA 2025: ~1 de cada 10 accede). Peri: 3 %, pre: 0 % **[S]**. Más probable con Isapre y MRS alto |

---

## 5. Salud crónica y EMPA

### Prevalencias (definen medicamentos y valores clínicos)
| Condición | Valor usado | Fuente |
|---|---|---|
| Hipertensión | Sube con la edad: 15 % a los 40 → 45 % a los 60 (promedio ~30 %) | **[N] ENS 2016-17**: mujeres 27,7 %; 45-64 años (ambos sexos) 45,1 % |
| Diabetes | 6 % a los 40 → 20 % a los 60 (promedio ~13 %) | **[N] ENS**: mujeres 14,0 %; 45-64 años 18,3 % |
| Estado nutricional (IMC) | Bajo peso 0,5 %, normal 20 %, sobrepeso 38 %, obesidad 37 %, obesidad mórbida 4,5 % | **[N] ENS**: mujeres (normal 24,0, sobrepeso 36,4, obesidad 33,7, mórbida 4,7) y 50-64 años (normal 14,6, sobrepeso 43,6, obesidad 38,1) |

Obesidad y diabetes más probables con menos de 8 años de estudio **[N] ENS** (diferencias significativas por escolaridad).

| Pregunta | Regla |
|---|---|
| Usa medicamentos para la presión | 65 % de las hipertensas **[S]** |
| Usa medicamentos para la diabetes | 75 % de las diabéticas **[S]** |

### Antropometría (autoaplicada u opcional para la usuaria)
| Campo | Regla |
|---|---|
| Talla actual | Normal 156 cm, DE 6 **[S]** |
| Peso | Talla² × IMC sorteado según la tabla anterior |
| Circunferencia de cintura | ≈ 2,3 × IMC + 25 cm, DE 6 **[S]** |
| Talla máxima (solo personal de salud) | Talla actual + 0-3 cm, más pérdida a mayor edad **[S]** |
| Fecha último EMPA | <1 año 40 %, 1-3 años 30 %, nunca/no recuerda (en blanco) 30 % **[S]** |

### Laboratorio y exámenes (solo el 30 % aplicado por personal de salud)
| Campo | Regla **[S]** |
|---|---|
| Presión sistólica / diastólica | Hipertensa: 138/86 ± 15/9. No hipertensa: 117/74 ± 11/8 (criterio ENS ≥140/90) |
| Glicemia | Diabética: 150 ± 40. No diabética: 92 ± 10 mg/dL (criterio ENS ≥126) |
| Colesterol total | 205 ± 38 mg/dL (más alto en posmenopausia) |
| HDL | 52 ± 12 mg/dL (más bajo con obesidad) |
| Triglicéridos | Log-normal, mediana 140 mg/dL (más alto con obesidad/diabetes) |
| Riesgo cardiovascular ATP-III | Se deriva de edad, colesterol, HDL, presión y tabaco: bajo ~80 %, moderado ~15 %, alto ~5 % |
| VDRL/RPR | "No reactivo" 99 %, "Reactivo" 1 % |
| PAP: fecha y resultado | Vigente (≤3 años) 60 %. Negativo 85 %, inflamatorio 8 %, atrófico 6 % (solo posmenopausia), sospechoso 1 % |
| Mamografía: fecha y BI-RADS | Vigente 50 % (más en ≥50 años). BI-RADS 1: 50 %, 2: 35 %, 0: 8 %, 3: 5 %, 4: 2 % |
| Ecotomografía mamaria | Solo si BI-RADS 0, 3 o 4 |

Pendiente: extraer de la ENS las prevalencias de colesterol alto y HDL bajo para mujeres y reemplazar estos supuestos.

---

## 6. Estilo de vida

### Actividad física
Base: **sedentarismo** (menos de 3 veces/semana) 90 % en mujeres y 93 % en 50-64 años **[N] ENS 2016-17**.
La literatura APS de Santiago también reporta 90 % sedentarias **[N]**.

| Pregunta | Regla |
|---|---|
| Días de ejercicio por semana | 0 días 55 %, 1-2 días 32 %, 3-4 días 8 %, 5-6 días 3 %, todos 2 % (→ ~13 % activas) |
| Ejercicio aeróbico | Sí 25 % (casi todas las que hacen ≥3 días) **[S]** |
| Bajo impacto (caminata, yoga) | Sí 35 % **[S]** |
| Fuerza | Sí 12 % **[S]** |
| Frecuencias (si sí) | Coherentes con los días de ejercicio |
| Horas sedentaria al día | Normal 6 h, DE 2,5 (1-14); +2 h si trabaja en oficina, sin dato para eso → solo ruido **[S]** |

### Alimentación
| Pregunta | Regla |
|---|---|
| Frutas + verduras | Solo **16 %** llega a ≥5 porciones al día **[N] ENS** (mujeres 16,4 %; 50-64 años 15,7 %). Más con educación >12 años **[N]** |
| Platos de verduras / frutas al día | Mayoría 1-2 porciones; "no consumo" 8 % frutas, 3 % verduras **[N] ENS** (días sin consumo) |
| Vasos de agua | 1-2: 30 %, 3-4: 40 %, 5-6: 20 %, 7+: 10 % **[S]** |
| Panes al día | No: 10 %, 1-2: 65 %, 3-4: 22 %, 5+: 3 % **[S]** |
| Lácteos | No: 15 %, 1-2: 65 %, 3-4: 18 %, 5+: 2 % **[S]** |
| Jugos / bebidas | No: 30 %, 1-2: 50 %, 3-4: 15 %, 5+: 5 % **[S]** |
| Bebidas energéticas | No: 93 %, 1-2: 7 % **[S]** |
| Pescado / semana | Nunca 35 %, 1-2: 55 %, 3+: 10 % **[S]** |
| Legumbres / semana | Nunca 10 %, 1-2: 65 %, 3+: 25 % **[S]** |
| Carnes / semana | 1-2: 30 %, 3-4: 45 %, 5+: 20 %, nunca 5 % **[S]** |
| Dulces y snacks / semana | Nunca 15 %, 1-2: 40 %, 3-4: 30 %, 5+: 15 % **[S]** |
| Quién prepara las comidas | Yo la mayoría 65 %, compartido 20 %, otra persona del hogar 10 %, compro 4 %, otro 1 % **[S]** |
| Comida fuera del hogar | Más frecuente si trabaja **[S]** |
| Falta de tiempo influye | Más si trabaja y cuida **[S]** |

### Tabaco, alcohol y marihuana
| Pregunta | Regla |
|---|---|
| Tabaco | Fuma **27 %** **[N] ENS** (mujeres 29,1 %; 50-64 años 30,7 %). Entre fumadoras: diariamente 60 %, 5-6 v/sem 10 %, 3-4: 10 %, 1-2: 20 % |
| Alcohol | Nunca 40 %, 1-2 v/sem 45 %, 3-4: 10 %, 5+: 5 % **[S]**. Calibrado a consumo riesgoso en mujeres ≈ 3,3 % **[N] ENS** (40-64 años, ambos sexos: 11,2 %) |
| Marihuana | Nunca 96 %, 1-2 v/sem 3 %, más 1 % **[S]** |

---

## 7. Cuidado de personas y trabajo

### Tareas de cuidado **[S]**, con contexto **[N]**
Las mujeres son el 65,6 % de quienes cuidan a personas dependientes y dedican ~5 h diarias al cuidado
**[N] ENUT 2023**. No hay prevalencia directa para mujeres de 40-60 en Coquimbo.

| Pregunta | Regla |
|---|---|
| Cuida a otras personas | Sí **50 %** (incluye hijos menores) **[S]**; más alto a los 40-49 (hijos) |
| Cuántas personas | 1: 50 %, 2: 30 %, 3+: 20 % |
| A quién cuida (multiselección) | Hijos menores 50 %, hijos adultos dependientes 15 %, padres o suegros 35 %, abuelos/adultos mayores 8 %, pareja dependiente 6 %, otro familiar 6 %, otro 3 %. Hijos menores más a los 40-49; padres más a los 50-60 |
| Sobrecarga física/emocional | Escala 1-5, mayor si además trabaja y si cuida a 2+ personas |

### Sección Trabajo (solo quienes trabajan) **[S]**
Sin datos chilenos; todas dependen del **nivel de síntomas MRS** y del estrés:

| Pregunta | Regla |
|---|---|
| Rendimiento afectado / bienestar afectado | Escala Nada-Mucho; correlación ~0,5 con el MRS total |
| Ausencias o atrasos | Mayoría "Nunca/Rara vez"; "Frecuentemente" solo con MRS severo |
| Lugar de trabajo comprensivo | Centrado en "Neutral", independiente de los síntomas |
| Estrés del entorno laboral | Moda "moderado"; alimenta el dominio psicológico del MRS |

---

## 8. Síntomas MRS

### Objetivo (lo que deben reproducir los datos)
Estudio chileno en mujeres de 40-59 años **[N]** (Rev. Méd. Chile 2008):

| Dominio | Ítems en nuestra encuesta | Media ± DE |
|---|---|---|
| Somático | p1 bochornos, p2 corazón, p3 musculares/articulares, p4 sueño | 5,8 ± 3,5 |
| Psicológico | p5 ánimo depresivo, p6 irritabilidad, p7 ansiedad, p8 cansancio | 7,7 ± 4,4 |
| Urogenital | p9 sexual, p10 orina, p11 sequedad vaginal | 2,7 ± 2,9 |
| **Total** | p1-p11 | **16,2 ± 8,5** |

Otros puntos de control:
- Los síntomas más frecuentes son los **musculares/articulares (~85 %)** y el **cansancio (~80 %)**
  **[N]** (APS Santiago, 1.023 mujeres de 45-64 años).
- El dominio psicológico es el más afectado; las posmenopáusicas puntúan más que las premenopáusicas **[N]**.
- En el estudio multicéntrico latinoamericano el total fue 11,3 ± 8,5 **[L]**. Se usa la cifra chilena como
  objetivo; la latinoamericana es un límite inferior razonable.

### Cómo se generan
Cada mujer tiene un **nivel general de síntomas** más un componente por dominio, para que los ítems se
correlacionen como en la realidad (subescalas con correlación ~0,3-0,5, como en el dataset de Jordania **[L]**).
El nivel sube o baja según:

| Factor | Efecto | Fuente |
|---|---|---|
| Posmenopausia (natural o quirúrgica) | ↑ somático y urogenital (bochornos, sequedad), ↑ moderado psicológico | **[N]** (posmenopausia, mayor deterioro) |
| Perimenopausia | ↑ bochornos, sueño e irritabilidad | **[L]** |
| Terapia hormonal | ↓ bochornos y sequedad | **[L]** |
| Ejercicio ≥3 días | ↓ ~10 % el total | **[L]** Jordania (ejercicio, efecto más claro) y **[N]** APS Santiago |
| Sobrecarga de cuidado / estrés laboral | ↑ psicológico | **[S]** |
| Obesidad | ↑ leve musculares/articulares | **[S]** |
| Tabaquismo | ↑ leve total | **[N]** APS Santiago (fumadoras con peor calidad de vida) |

Cada ítem se convierte a la escala de la encuesta (0 Ninguna … 4 Muy intensa). Se ajusta la calibración
hasta que las medias por dominio coincidan con la tabla objetivo (±10 %).

### Variables que dependen del MRS
| Pregunta | Regla |
|---|---|
| Usa antidepresivos o medicamentos para dormir | 15 % **[S]**; probabilidad sube con el dominio psicológico y el ítem de sueño |
| Tiene pareja | 65 % **[S]** |
| Cambio en la relación de pareja por la menopausia (Nada-Mucho) | Ligado al dominio urogenital y psicológico **[S]** |
| Tiene actividad sexual | 60 % **[S]**; baja sin pareja, con la edad y con sequedad vaginal alta |
| Evacuación intestinal | 1 vez al día 50 %, cada 2 días 25 %, >1 al día 10 %, 3+ días 15 % **[S]** |
| Distensión abdominal | Nunca/casi nunca 35 %, a veces 40 %, frecuentemente 18 %, siempre 7 % **[S]** |

---

## 9. Conocimiento del sistema de salud

Casi toda la sección aparece **solo si la previsión es Fonasa** (~81 %). Sin estadísticas chilenas
específicas: **todo [S]**, con este contexto **[N]**: la aplicación del MRS en APS cubría ~62,6 % de las mujeres
de 45-64 en un estudio comunitario, y solo ~1 de cada 10 mujeres con síntomas accede a terapia hormonal (MUSA 2025).

| Pregunta | Regla **[S]** |
|---|---|
| Conoce atención pública para climaterio | Sí 35 %, No 45 %, No sabe 20 % |
| Ha escuchado del Programa de Climaterio | Sí 30 % |
| Sabe dónde acudir | Sí 45 % |
| Ha consultado por síntomas | Sí 30 %; más con MRS alto |
| Evaluación de la atención (si consultó) | Muy mala 5, mala 15, ni buena ni mala 35, buena 35, muy buena 10 % |
| En control en algún programa del consultorio | Sí si es hipertensa o diabética con 70 % (→ "Programa de Salud Cardiovascular"); resto 10 % ("Programa de la Mujer") |
| Información suficiente (Nada-Mucho) | Moda "Poco" |
| Qué tan informada sobre servicios | Moda "Poco informada" |
| Conoce recursos / prestaciones | Sí 45 %, No 40 %, No sabe 15 % |
| Dificultades de acceso | Sí 40 %, No 45 %, No sabe 15 % |
| Principales dificultades (multiselección) | Obtener horas 60 %, falta de información 45 %, horarios incompatibles 35 % (más si trabaja), no saber dónde consultar 30 %, minimización de síntomas 25 %, falta de especialistas 25 %, costos 10 %, otra 3 % |
| Síntomas tomados en serio (Nada-Mucho; para todas) | Moda "Poco"/"Moderadamente" |
| Desea más información/apoyo (para todas) | Sí 80 % |
| Tipo de apoyo (multiselección) | Manejo de síntomas 60 %, información general 50 %, salud mental 40 %, atención ginecológica 35 %, terapia hormonal 30 %, nutrición 30 %, actividad física 25 %, apoyo laboral 15 % (solo si trabaja), otro 2 % |

Los campos "Otro, especifique" se llenan con textos cortos de una lista fija (por ejemplo "Vecina", "Cuñada").

---

## 10. Validación (para el Paso 3)

Con los datos generados se comprobará que se reproducen estas cifras (tolerancia ±5 puntos porcentuales
o ±10 % de la media):

| Indicador | Objetivo |
|---|---|
| Edad media | ~49-50 años |
| Coquimbo + La Serena | ~62 % |
| Posmenopausia (natural + quirúrgica) | ~50 % |
| MRS total / somático / psicológico / urogenital | 16,2 / 5,8 / 7,7 / 2,7 |
| Hipertensión / diabetes / obesidad (≥30) | ~30 % / ~13 % / ~41 % |
| Fuma | ~27 % |
| Ejercicio ≥3 días | ~13 % |
| Fonasa | ~81 % |
| Condicionales | 0 respuestas en preguntas que no debían mostrarse |
| Estructura | 250 encuestas, 50 personas con 2 rondas separadas ≥15 días, 30 % con EMPA clínico |

---

## 11. Fuentes

| Etiqueta | Fuente | Uso |
|---|---|---|
| [C] | INE, Censo 2024: población de la Región de Coquimbo por sexo, edad y comuna (vía telencuestas.com; **verificar contra la publicación oficial del INE**) | Edad, comuna |
| [C] | Casen 2022, Encuesta Longitudinal Regional de Coquimbo (Encuestas UC, `elr_cpquimbo.pdf`) | Escolaridad 12,6 años, migrantes, pueblos originarios por provincia |
| [C] | Casen 2022, Resultados Pueblos Indígenas (Ministerio de Desarrollo Social) | Composición por pueblo |
| [C] | INE, Encuesta Nacional de Empleo, boletín Coquimbo may-jul 2026 (`datos/fuentes/`) | Ocupación de mujeres 44,5 % |
| [N] | Casen 2022, Resultados de Salud, rev. 2025 (`datos/fuentes/`) | Previsión de las mujeres |
| [N] | Minsal, ENS 2016-2017 Primeros resultados (`datos/fuentes/`) | HTA, DM, IMC, tabaco, alcohol, sedentarismo, frutas y verduras |
| [N] | Evaluación de la calidad de vida en mujeres de 40 a 59 años mediante la escala MRS. Rev. Méd. Chile 2008;136(12) | Objetivo MRS por dominio |
| [N] | López F, Soares De Lorenzi D, d'Andretta Tanaka A. Calidad de vida de mujeres en fase de transición menopáusica evaluado por la MRS. Rev. Chil. Obstet. Ginecol. 2010 | Pre vs. posmenopausia, dominio psicológico |
| [N] | López F, Soares De Lorenzi D. Síntomas climatéricos y estilos de vida de usuarias de APS, Santiago. Rev. Méd. Chile 2011 | Síntomas más frecuentes, sedentarismo, tabaco |
| [N] | ENUT 2023 y estudios sobre cuidadoras (OCEC-UDP 2026) | Contexto de cuidado |
| [N] | Estudio MUSA 2025 (reportado en La Tercera) | Acceso a terapia hormonal |
| [L] | REDLINC, estudio multicéntrico latinoamericano MRS (n = 8.373) | MRS 11,3 ± 8,5; 48,8 % posmenopáusicas; edad de menopausia |
| [L] | Assaf et al., figshare 20822032 (Jordania), ver `perfil_dataset_referencia.md` | Tamaño de efectos y correlación entre subescalas |

## 12. Pendientes antes del Paso 2

1. Verificar la tabla de edad y comuna contra la publicación oficial del INE (Censo 2024).
2. Extraer de la ENS colesterol total alto, HDL bajo y talla promedio de mujeres para reemplazar supuestos de §5.
3. Revisión de la profesora, en especial de todo lo marcado **[S]** en §7, §8 y §9.
