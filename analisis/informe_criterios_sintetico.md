# Criterios del conjunto sintético de la usuaria común

> Reúne en un solo documento todos los criterios y características que se establecieron para generar el
> conjunto sintético de la usuaria común (Fase 34A, reunión con la profesora del 20-10-2026).
> Los valores son los que usa hoy el generador (`analisis/simulacion/parametros.py`). El detalle de
> cada fuente está en `analisis/supuestos_simulacion.md` y la validación en `analisis/informe_sintetico.md`.
> Fecha: 2026-10-26 · Rama `datos-simulados`.

## 1. Propósito

El conjunto de la profesora (`dataset_menopausia_sucio.csv`) mostraba efectos incoherentes con la
realidad chilena (por ejemplo, más pan, dulces o alcohol se asociaban con **menos** síntomas). Por eso la
profesora pidió un **conjunto sintético nuevo** que:

- represente solo a la **usuaria común** que responde la **primera encuesta** de la plataforma;
- sea **coherente con Chile** y con la Región de Coquimbo;
- tome como base el dataset *Menopause* (figshare 20822032) y los patrones de las respuestas reales
  guardadas en la plataforma;
- venga **sucio** (inconsistencias, valores imposibles, formatos mezclados) para limpiarlo en el EDA,
  y conserve los atípicos **plausibles**.

El análisis del conjunto de la profesora (Fases 32-34) queda como anexo.

## 2. Cómo leer las fuentes

| Etiqueta | Nivel | Significado |
|---|---|---|
| **[C]** | Región de Coquimbo | Dato oficial de la región |
| **[N]** | Chile | Dato nacional, cuando no hay dato regional |
| **[L]** | Latinoamérica / internacional | Literatura o el dataset de Jordania (sobre todo para relaciones entre variables) |
| **[R]** | Respuestas reales | Patrón observado en las 5 respuestas reales de la plataforma |
| **[S]** | Supuesto propio | Sin fuente directa; valor razonable que **debe validar la profesora** |

## 3. Diseño de la muestra

| Criterio | Valor | Motivo |
|---|---|---|
| Participantes | **N = 550**, una encuesta cada una | Decisión de la usuaria (22-10) |
| Rondas | Solo la **primera encuesta** (sin ronda 2) | Pedido de la profesora |
| Quién responde | Solo la **usuaria común** (`origen_registro = AUTO`) | Pedido de la profesora |
| Campos del servicio de salud | **Vacíos**: presión arterial, glicemia, colesterol, HDL, triglicéridos, PAP, mamografía, VDRL, riesgo cardiovascular, talla máxima | Solo los llena el personal de salud; quedan para un futuro panel del servicio |
| Edad | 40-65 años | Regla de la plataforma (`forms.EDAD_MAXIMA = 65`, Fase 11) |
| Excepción de edad | 4 % de 36-39 años: 60 % quirúrgica, 40 % ausencia prolongada de menstruación **[S]** | La plataforma admite menores de 40 con excepción |
| Fechas de respuesta | 2 de marzo a 30 de septiembre de 2026 | Igual que el conjunto de la profesora |
| Región | Solo Coquimbo, comunas según su población | Decisión propia, consistente con el estudio |
| Semilla | 2029 | Primera semilla (desde 2026) cuya muestra cumple todos los controles de §11 |
| Reproducibilidad | Misma semilla → mismos datos | `python analisis/generar_sintetico.py` |

## 4. Cadena de generación

Las respuestas no se sortean pregunta por pregunta: cada bloque depende de los anteriores, para que no
salgan personas incoherentes.

```
1. Perfil base        edad, comuna, origen, pueblo originario, educación, trabajo, previsión
        │
2. Etapa reproductiva pre / peri / posmenopausia natural / quirúrgica
        │              → última menstruación, útero, ovarios, anticonceptivos
3. Salud crónica      hipertensión, IMC, diabetes → medicamentos
        │
4. Estilo de vida     ejercicio, agua, alimentación, tabaco, alcohol, marihuana
        │
5. Cuidado y trabajo  cuida a otras personas, sobrecarga, estrés, lugar comprensivo
        │
6. Síntomas MRS       nivel latente ← etapa, terapia hormonal, factores validados
        │
7. Consecuencias      rendimiento, bienestar laboral, ausencias, pareja, antidepresivos
```

Después se borra lo que la encuesta real no mostraría (preguntas condicionales y campos del personal de
salud), igual que en la plataforma. Al final se agrega la suciedad (§10).

## 5. Perfil base (sección Identificación)

| Variable | Criterio | Fuente |
|---|---|---|
| Edad | Proporcional a las mujeres de la región por tramo: 40-44 (30.220), 45-49 (29.334), 50-54 (28.170), 55-59 (27.740), 60-64 (24.500), 65 (4.600); edad uniforme dentro del tramo | **[C]** Censo 2024; 60-65 estimados **[S]** |
| Comuna | Proporcional a la población femenina de las 15 comunas (Coquimbo y La Serena ≈ 62 %) | **[C]** Censo 2024 |
| Género | Femenino 99 %, "Prefiero no decirlo" 1 % | **[S]** |
| Origen | Extranjera según provincia: Elqui 3,9 %, Limarí 2,2 %, Choapa 4,2 %. Países: Venezuela 35 %, Perú 15 %, Colombia 15 %, Bolivia 10 %, Haití 10 %, Argentina 5 %, Ecuador 3 %, otro 7 % | **[C]** Casen 2022; países **[S]** |
| Pueblo originario | Elqui 5,6 %, Limarí 9,4 %, Choapa 5,0 %. Diaguita 57,8 %, Mapuche 25,5 %, Aymara 6,9 %, Chango 4,5 %, Colla 1,9 %, Quechua 0,9 %, otro 2,5 % | **[C]** Casen 2022 |
| Nivel educacional | Calibrado a 12,6 años de estudio promedio, algo más bajo por generación (media completa 32 %, universitaria completa 15 %…). **No entra al análisis** (decisión de la usuaria 22-10) | **[C]** Casen 2022 + **[S]** |
| Trabaja | Base 61 %; +1,2 puntos por año de estudio sobre 12; −15 puntos desde los 55 años | **[C]** INE-ENE (ocupación 44,5 %) ajustada a 40-65 **[S]** |
| Previsión | Fonasa 81,2 %, Isapre 13,8 %, FF.AA. 1,5 %, ninguna 2,6 %, no sabe 0,9 %. Isapre más probable con estudios universitarios (×1,8) y si trabaja (×1,3) | **[N]** Casen 2022; ajustes **[S]** |

## 6. Etapa reproductiva

### 6.1 Cómo se genera la etapa de cada participante

El generador sortea una **edad de menopausia natural** para cada mujer: normal con media **49 años** y
DE 3,5, recortada entre 40 y 58 **[L]** (REDLINC; estudio chileno). Con ella asigna la etapa
**verdadera**:

| Etapa simulada | Regla |
|---|---|
| Premenopausia | Edad < edad de menopausia − 4 años |
| Perimenopausia | Dentro de los 4 años previos a la menopausia **[S]** |
| Posmenopausia natural | Edad ≥ edad de menopausia |
| Quirúrgica | 7 % de las mujeres (histerectomía y/o ooforectomía) **[S]**, más las excepciones quirúrgicas de 36-39 años |
| Ausencia prolongada (excepción < 40) | Menopausia precoz sin cirugía: se trata como posmenopausia |

### 6.2 Preguntas que salen de la etapa

| Pregunta | Criterio | Fuente |
|---|---|---|
| Fecha de la última menstruación (FUM) | Pre: hace 3-40 días. Peri: hace 15-330 días. Post/quirúrgica: el año en que cumplió la edad de menopausia, siempre con ≥ 12 meses de distancia. Si fue hace ≥ 2 años, el 30 % responde **solo el año** | **[S]** |
| Menstruación llega | Pre: regular 75 %, irregular 20 %, no sabe 5 %. Peri: regular 20 %, irregular 75 %, no sabe 5 % | **[S]** |
| Tipo de sangrado | Pre: moderado 45 %, leve 25 %, abundante 15 %, muy leve 8 %, muy abundante 7 %. En peri sube lo abundante (23 % + 12 %) | **[S]** |
| Usa anticonceptivo | 40 % de quienes menstrúan. DIU 30 %, oral 20 %, preservativo 20 %, implante 10 %, inyectable 10 %, otro 5 %, no sabe 5 % | **[S]** |
| Operada para no tener más hijos | 20 % (esterilización tubaria) | **[S]** |
| Tiene útero | No en las quirúrgicas | — |
| Tiene al menos un ovario | No en el 40 % de las quirúrgicas (ooforectomía bilateral) | **[S]** |
| Terapia hormonal | Post o quirúrgica 10 %, peri 3 %, pre 0 %. ×1,5 con Isapre, ×1,5 con muchos síntomas (×0,8 si no), ×0,5 si fuma | **[N]** MUSA 2025; ajustes **[S]** |

### 6.3 Etapa menopáusica derivada en la limpieza (STRAW+10 simplificado)

La etapa del §6.1 es interna del generador y **no aparece en el conjunto**: la encuesta no pregunta la
etapa. En la limpieza (Fase 32, `limpieza/reglas.py`) se **reconstruye** a partir de las respuestas,
como se haría con datos reales, y queda en la columna `etapa_menopausica`. Se usa como **variable de
control** en el análisis (decisión de la usuaria del 26-10).

**FUM** = fecha de la última menstruación (en inglés *LMP* o *FMP*). Con ella se calcula
`meses_desde_fum`, los meses entre la FUM y la fecha de la encuesta.

**STRAW+10** (*Stages of Reproductive Aging Workshop + 10*) es la clasificación de referencia
internacional de las etapas del envejecimiento reproductivo femenino. La primera versión es de 2001 y la
revisión actual se acordó en 2011:

> Harlow SD, Gass M, Hall JE, Lobo R, Maki P, Rebar RW, Sherman S, Sluss PM, de Villiers TJ; STRAW + 10
> Collaborative Group. Executive summary of the Stages of Reproductive Aging Workshop + 10: addressing
> the unfinished agenda of staging reproductive aging. *Menopause*. 2012;19(4):387-395.
> doi:10.1097/gme.0b013e31824d8f40. (Publicado también en *J Clin Endocrinol Metab*, *Fertil Steril* y
> *Climacteric* en 2012.)

La definición de menopausia como **12 meses seguidos sin menstruación** es también la de la OMS:

> World Health Organization. *Research on the menopause in the 1990s: report of a WHO Scientific Group.*
> WHO Technical Report Series 866. Geneva: WHO; 1996.

La versión completa de STRAW+10 ordena las etapas alrededor del período menstrual final (etapa 0):

| Etapa STRAW+10 | Nombre | Criterio principal |
|---|---|---|
| −5 a −3 | Etapa reproductiva | Ciclos regulares (en −3 empiezan cambios sutiles y hormonales) |
| −2 | Transición menopáusica temprana | La duración de ciclos seguidos varía en ≥ 7 días |
| −1 | Transición menopáusica tardía | Un período de ≥ 60 días sin menstruar |
| 0 | Período menstrual final | Solo se confirma después, con 12 meses sin menstruar |
| +1a, +1b, +1c | Posmenopausia temprana | Primeros años tras el período final |
| +2 | Posmenopausia tardía | Resto de la vida |

En STRAW+10 los criterios **principales** son los menstruales. Los hormonales (FSH, hormona
antimülleriana, recuento de folículos antrales) son de **apoyo**.

**Adaptación propia ("simplificado").** La encuesta solo pregunta la FUM, si la menstruación llega
regular o irregular, y si tiene útero y ovarios. Con eso se definió esta regla, que **es nuestra y debe
validar la profesora**:

| Etapa derivada | Regla | Relación con STRAW+10 |
|---|---|---|
| quirúrgica | No tiene ovarios | **No es una etapa de STRAW**, que excluye estos casos. Corresponde a la menopausia quirúrgica de la práctica clínica |
| posmenopausia | ≥ 12 meses desde la FUM | Etapas +1 y +2; criterio de STRAW+10 y de la OMS |
| premenopausia | < 12 meses desde la FUM y menstruación **regular** | Aproxima la etapa reproductiva (−5 a −3) |
| perimenopausia | < 12 meses desde la FUM y menstruación **irregular** o no segura | Aproxima la transición (−2 y −1); la encuesta no distingue la temprana de la tardía |
| indeterminada | Sin FUM utilizable | Sin criterio menstrual no se puede clasificar |
| indeterminada (histerectomía) | Sin FUM y sin útero | STRAW+10 indica usar marcadores hormonales, que la encuesta no tiene |

Diferencias con STRAW+10 que conviene declarar en la tesis:

1. En STRAW+10 la perimenopausia incluye también los primeros 12 meses después del período final; aquí
   no, porque al momento de la encuesta no se puede saber si esa fue la última menstruación.
2. "Regular / irregular" es autodeclarado; STRAW+10 usa la variación de ≥ 7 días y las amenorreas de
   ≥ 60 días.
3. La categoría quirúrgica se basa solo en los ovarios: una mujer con histerectomía que conserva los
   ovarios se clasifica por su FUM.
4. Con los porcentajes del §6.2, el 20 % de las perimenopáusicas simuladas declara menstruación regular y
   se clasifica como premenopausia, y el 20 % de las premenopáusicas declara irregular y se clasifica
   como perimenopausia. Es el mismo error de clasificación que tendría la regla con datos reales.

## 7. Salud crónica

| Variable | Criterio | Fuente |
|---|---|---|
| Hipertensión | Sube con la edad: 15 % a los 40 → 45 % a los 60; ×1,25 con < 8 años de estudio | **[N]** ENS 2016-17 |
| Medicamentos para la presión | 65 % de las hipertensas | **[S]** |
| IMC | Bajo peso 0,5 %, normal 20 %, sobrepeso 38 %, obesidad 37 %, obesidad mórbida 4,5 %; obesidad algo más frecuente con la edad (+1 % por año sobre 50) y con baja educación. IMC uniforme dentro de cada categoría (17-46) | **[N]** ENS 2016-17 |
| Talla | Normal 156 cm, DE 6 (140-178) | **[S]** |
| Peso | Talla² × IMC sorteado | — |
| Cintura | ≈ 2,3 × IMC + 25 cm, DE 6 (60-150) | **[S]** |
| Diabetes | 6 % a los 40 → 20 % a los 60; ×1,25 con baja educación; **×1,8 con IMC ≥ 30** | **[N]** ENS; **[L]** relación con obesidad |
| Medicamentos para la diabetes | 75 % de las diabéticas | **[S]** |

El IMC se conserva en el análisis porque se calcula con peso y talla **autodeclarados**. La cintura
también la puede declarar la usuaria, pero queda fuera del análisis primario.

## 8. Estilo de vida, cuidado y trabajo

### 8.1 Actividad física y alimentación

| Variable | Criterio | Fuente |
|---|---|---|
| Días de ejercicio (código 1-5) | 0 días 55 %, 1-2 días 32 %, 3-4 días 8 %, 5-6 días 3 %, todos 2 %. ×1,5 los niveles ≥ 3 con > 12 años de estudio; ×0,6 los niveles ≥ 2 con IMC ≥ 30 | **[N]** ENS (sedentarismo 90-93 %); ajustes **[L]/[S]** |
| Vasos de agua | 1-2: 30 %, 3-4: 37 %, 5-6: 18 %, 7+: 10 %, no consume 5 %. Quien hace ejercicio ≥ 1-2 días sube un nivel con probabilidad 0,6 | **[S]** |
| Frutas y verduras | 14,5 % cumple 5 porciones (×1,3 con > 12 años de estudio) | **[N]** ENS (16 %) |
| Panes / día | No 10 %, 1-2: 65 %, 3-4: 22 %, 5+: 3 % | **[S]** |
| Lácteos / día | No 15 %, 1-2: 65 %, 3-4: 18 %, 5+: 2 % | **[S]** |
| Jugos y bebidas / día | No 30 %, 1-2: 50 %, 3-4: 15 %, 5+: 5 % | **[S]** |
| Bebidas energéticas | No 93 %, 1-2: 7 % | **[S]** |
| Pescado / semana | Nunca 35 %, 1-2: 55 %, 3+: 10 % | **[S]** |
| Legumbres / semana | Nunca 10 %, 1-2: 65 %, 3+: 25 % | **[S]** |
| Carnes / semana | Nunca 5 %, 1-2: 30 %, 3-4: 45 %, 5-6: 15 %, diario 5 % | **[S]** |
| Golosinas / semana | Nunca 15 %, 1-2: 40 %, 3-4: 30 %, 5-6: 10 %, diario 5 % | **[S]** |
| Quién prepara las comidas | Yo la mayoría 65 %, compartido 20 %, otra persona del hogar 10 %, compro 4 %, otro 1 % | **[S]** |

### 8.2 Tabaco, alcohol y marihuana

| Variable | Criterio | Fuente |
|---|---|---|
| Tabaco | Fuma 27 %. Entre fumadoras: diario 60 %, 5-6 v/sem 10 %, 3-4: 10 %, 1-2: 20 % | **[N]** ENS |
| Alcohol | No fumadoras: nunca 40 %, 1-2 v/sem 45 %, 3-4: 10 %, 5-6: 3 %, diario 2 %. Fumadoras: más consumo (nunca 25 %) | **[S]**; **[L]** tabaco y alcohol van juntos |
| Marihuana | No fumadoras: nunca 94 %. Fumadoras: nunca 80 % | **[S]** (ENPG: uso bajo en 40-65) |
| Tabaco y hormonas | Las fumadoras usan menos terapia hormonal (×0,5) y menos píldora (×0,3), porque los estrógenos combinados están contraindicados en fumadoras mayores de 35 años | **[L]** criterios OMS |

### 8.3 Cuidado de otras personas y trabajo

| Variable | Criterio | Fuente |
|---|---|---|
| Cuida a otras personas | 58 % a los 40-49 años, 42 % desde los 50 | **[S]**, contexto **[N]** ENUT 2023 |
| Cuántas personas | 1: 50 %, 2: 30 %, 3+: 20 % | **[S]** |
| A quién cuida (multiselección; 40-49 / 50+) | Hijos menores 70 % / 25 %; hijos adultos dependientes 10 % / 20 %; padres o suegros 25 % / 50 %; abuelos u otros adultos mayores 8 %; pareja dependiente 4 % / 9 %; otro familiar 6 %; otro 3 % | **[S]** |
| Sobrecarga física y emocional (1-5) | Media 2,6; +0,8 si además trabaja; +0,6 si cuida a 2 o más | **[S]** |
| Estrés del entorno laboral (1-5, quien trabaja) | 1: 10 %, 2: 25 %, 3: 35 %, 4: 20 %, 5: 10 % | **[S]** |
| Lugar de trabajo comprensivo (1-5) | Media 3,3, DE 1,0; baja 0,35 por cada punto de estrés sobre 3 | **[S]** |
| Doble carga | Trabaja **y** cuida a otras personas (variable derivada) | Factor validado por la profesora |

## 9. Síntomas MRS

### 9.1 Objetivo

| Dominio | Ítems | Media chilena | Fuente |
|---|---|---|---|
| Somático | p1 bochornos, p2 corazón, p3 musculares/articulares, p4 sueño | 5,8 | **[N]** Rev. Méd. Chile 2008 (40-59 años) |
| Psicológico | p5 ánimo depresivo, p6 irritabilidad, p7 ansiedad, p8 cansancio | 7,7 | ídem |
| Urogenital | p9 sexual, p10 orina, p11 sequedad vaginal | 2,7 | ídem |
| **Total** | p1-p11 | **16,2** | ídem |

Cortes de severidad del total, confirmados por la profesora el 20-10 como estándar de la escala:
**0-4** sin síntomas o muy leve, **5-8** leve, **9-15** moderado, **16-44** severo (Heinemann K et al.
The Menopause Rating Scale (MRS) scale: a methodological review. *Health Qual Life Outcomes*.
2004;2:45).

### 9.2 Modelo de generación

Cada ítem tiene una intensidad continua (latente) que después se redondea a la escala 0-4:

```
intensidad = base del ítem
           + 0,75 × nivel general de síntomas de la mujer     (común a los 11 ítems)
           + 0,55 × nivel de su dominio                        (somático, psicológico o urogenital)
           + efecto de la etapa + efecto de la terapia hormonal
           + efecto de los factores de estilo de vida (§9.3)
           + ruido (DE 0,55)
```

El nivel general y el de dominio hacen que los ítems se correlacionen entre sí como en la realidad
(subescalas con correlación ~0,3-0,5, como en el dataset de Jordania **[L]**). Las bases de cada ítem se
calibraron para acercar las medias por dominio al objetivo chileno.

| Efecto | Ítems | Fuente |
|---|---|---|
| Perimenopausia | ↑ bochornos (+0,45), sueño e irritabilidad (+0,30) | **[L]** |
| Posmenopausia o quirúrgica | ↑ todos; más bochornos (+0,55), sequedad vaginal (+0,70), sexual (+0,45) y orina (+0,35) | **[N]** posmenopáusicas puntúan más |
| Terapia hormonal | ↓ bochornos (−0,60), sequedad (−0,45) y sueño (−0,20) | **[L]** |

### 9.3 Factores que mueven el MRS (validados por la profesora el 20-10)

Cada factor desplaza el nivel de todos los ítems de un dominio, con un peso por dominio. Los valores van
centrados en la situación típica (0 = sin efecto) y un ajuste final devuelve la media al objetivo
chileno.

| Factor | Sentido | Efecto | Forma | Dominio que más mueve |
|---|---|---|---|---|
| IMC | ↑ **el más fuerte** | 0,27 | por cada 5 puntos sobre 27 (gradual) | somático |
| Diabetes | ↑ | 0,38 | sí/no | somático |
| Doble carga (trabaja y cuida) | ↑ | 0,40 | sí/no | psicológico |
| Sobrecarga (quien cuida) | ↑ | 0,14 | por punto sobre 3 | psicológico |
| Estrés laboral (quien trabaja) | ↑ | 0,18 | por punto sobre 3 | psicológico |
| Lugar de trabajo comprensivo | ↓ protector | −0,12 | por punto sobre 3 | psicológico |
| Días de ejercicio | ↓ protector | −0,42 | 0 días = 0; 1-2 días 0,6; 3-4 días 0,8; 5-6 días 0,9; todos 1,0 | todos |
| Vasos de agua | ↓ protector | −0,12 | por nivel sobre 3 | todos |
| Tabaco | ↑ | 0,40 | de nunca (0) a diario (1) | todos |
| Alcohol | ↑ | 0,65 | de nunca (0) a diario (1) | todos |
| Marihuana | ↑ | 0,60 | de nunca (0) a diario (1) | todos |
| Pan, golosinas, jugos | ↑ chico | 0,05 | por nivel sobre el típico | todos |
| Bebidas energéticas | ↑ chico | 0,10 | por nivel sobre "no consume" | todos |
| Frutas, verduras, lácteos, pescado, legumbres, carnes | sin efecto | — | — | — |

Pesos por dominio (somático / psicológico / urogenital): general 1,0 / 1,0 / 0,6; físico 1,3 / 0,7 /
0,6; carga 0,7 / 1,4 / 0,3. Ajuste final: somático −0,50, psicológico −0,40, urogenital −0,30.

Criterios que fijó la profesora: **ningún alimento ni sustancia puede salir protector**, el alcohol
agrava, y el IMC debe ser el factor más fuerte. Los efectos se calibraron con N = 20.000 para que la
correlación de Spearman de cada factor con el MRS total quede en el rango pedido (§11).

### 9.4 Variables que no se vinculan con el MRS

Por indicación de la profesora o por decisión de la usuaria, estas variables se generan con su
distribución propia pero **sin efecto sobre los síntomas**:

- **Conocimiento del sistema de salud** (sección completa): la profesora indicó que no aumenta ni
  disminuye los síntomas. Casi toda la sección aparece solo con Fonasa.
- **Encuesta de satisfacción**: la responde el 45 %, como en la plataforma, donde es opcional.
- Variables ginecológicas, medicamentos para la presión, evacuación intestinal y distensión abdominal.
- Edad: actúa solo a través de la etapa, la hipertensión, la diabetes y el IMC.

## 10. Consecuencias (efecto del MRS, no causa)

La profesora indicó que estas variables son **consecuencia** de los síntomas, así que se generan
**después** del MRS y quedan en un módulo aparte del análisis:

| Variable | Criterio | Fuente |
|---|---|---|
| Rendimiento afectado (1-5, quien trabaja) | Media 1 + 3,5 × (MRS total / 44) | **[S]** |
| Bienestar en el trabajo afectado | Igual, + 0,2 por punto de estrés sobre 3 | **[S]** |
| Frecuencia de ausencias o atrasos | Media 0,7 + 2,5 × (MRS / 44): casi todas "nunca / rara vez" salvo con MRS alto | **[S]** |
| Cambio en la relación de pareja (si tiene pareja, 65 %) | Sube con los dominios urogenital y psicológico | **[S]** |
| Actividad sexual | Con pareja: 80 %, −1 punto por año sobre 40, −10 puntos con sequedad vaginal alta. Sin pareja: 15 % | **[S]** |
| Antidepresivos o medicamentos para dormir | 3 % + 1,5 % por punto del dominio psicológico + 5 % con sueño alterado | **[S]** |

## 11. Controles de validación

Se comprueban sobre el conjunto **verdadero** (antes de ensuciarlo). La semilla 2029 es la primera que
cumple todos a la vez (9 de 20 semillas los cumplen). En los rangos de rho se acepta una tolerancia de
0,03 sobre el límite superior, porque con N = 550 cada muestra varía alrededor del efecto calibrado.

| Control | Criterio | Resultado (semilla 2029) |
|---|---|---|
| MRS total | Cerca de 16,2 | 16,3 ± 9,3 |
| IMC vs. MRS total | rho de Spearman 0,25-0,35 | +0,31 |
| Diabetes | rho 0,10-0,25, positiva | +0,16 |
| Doble carga | ídem | +0,11 |
| Sobrecarga | ídem | +0,21 |
| Estrés laboral | ídem | +0,19 |
| Lugar comprensivo | rho 0,10-0,25, negativa | −0,26 (dentro de la tolerancia de +0,03) |
| Días de ejercicio | rho negativa | −0,15 |
| Vasos de agua | rho negativa | −0,13 |
| Tabaco | rho positiva | +0,14 |
| Alcohol | rho positiva | +0,12 |
| Marihuana | Solo positiva (el 94 % nunca consume) | +0,07 |
| Alimentación | Ninguna correlación negativa significativa (p < 0,05) | Se cumple (p ≥ 0,09) |

Distribución de severidad resultante: 0-4 10,7 %, 5-8 14,2 %, 9-15 21,8 %, 16-44 53,3 %.

## 12. Suciedad agregada

`simulacion/ensuciar.py` toma el conjunto verdadero y agrega errores. Cada cambio queda registrado en
`bitacora_suciedad.csv` (valor verdadero, valor sucio y tipo), lo que permite medir qué tan bien
funciona la limpieza (Fase 34B: recupera el 83 % de los errores).

| Grupo | Errores y tasas |
|---|---|
| Omisiones | Peso en blanco 45 % **[R]** (talla en blanco con él en el 85 % de esos casos) → IMC no calculable en ~48 %; cintura 55 %; fecha del último EMPA 50 %; 4 % del resto de las preguntas opcionales. Si falta una pregunta "madre", sus dependientes también |
| Lógica de la encuesta | Pregunta que no aplica respondida (sobrecarga sin cuidar, sangrado con ≥ 12 meses sin menstruar) 6 % **[R]**; días de ejercicio sin tipo marcado 5 % **[R]**; píldora y terapia hormonal a la vez (15 % de quienes usan píldora) **[R]**; cintura "0.00" 10 % **[R]** |
| Formatos | FUM como dd/mm/aaaa 10 % **[R]**, "julio 2021" 4 % o mm/aaaa 4 %; nacimiento dd/mm/aaaa 8 %; unidades en el texto ("81.0 kg") 3 %; coma decimal 3 %; códigos variantes (Sí/si/S, Femenino/Mujer) 2 %; minúsculas 1 %; espacios sobrantes 1 %; región como nombre 3 % |
| Valores imposibles | Centinelas numéricos (−1, 99, 999, 9999) 0,6 % y de texto (N/A, sin dato, -) 0,4 %; talla en metros 2 % o sin punto 0,4 %; peso con un dígito de más 0,6 %; ítem MRS 5 o 9 0,4 %; fecha de nacimiento imposible 0,6 %; edad fuera de 40-65 sin excepción 0,8 % |
| Filas | Duplicados exactos 1,2 % **[R]**; versión anterior de la misma participante con el mismo RUT 1 % |

Los atípicos **plausibles** (por ejemplo IMC sobre 40 por obesidad mórbida) no son suciedad: vienen
del conjunto verdadero y la limpieza debe conservarlos.

Resultado: 550 participantes verdaderas → **565 filas sucias** y ~3.570 cambios registrados.

## 13. Archivos generados

| Archivo | Contenido |
|---|---|
| `datos/sintetico/dataset_usuaria_sucio.csv` | Conjunto entregado al EDA (565 filas) |
| `datos/sintetico/dataset_usuaria_verdad.csv` | Conjunto sin errores (550), solo para evaluar la limpieza |
| `datos/sintetico/bitacora_suciedad.csv` | Cada error agregado |
| `analisis/informe_sintetico.md` | Validación de los controles del §11 |

Comando: `python analisis/generar_sintetico.py`.

## 14. Fuentes

| Etiqueta | Fuente | Uso |
|---|---|---|
| [C] | INE, Censo 2024: población de la Región de Coquimbo por sexo, edad y comuna | Edad, comuna |
| [C] | Casen 2022, Encuesta Longitudinal Regional de Coquimbo | Escolaridad, migrantes, pueblos originarios |
| [C] | Casen 2022, Resultados Pueblos Indígenas (Ministerio de Desarrollo Social) | Composición por pueblo |
| [C] | INE, Encuesta Nacional de Empleo, Coquimbo may-jul 2026 | Ocupación de mujeres |
| [N] | Casen 2022, Resultados de Salud | Previsión |
| [N] | Minsal, Encuesta Nacional de Salud 2016-2017 | Hipertensión, diabetes, IMC, tabaco, alcohol, sedentarismo, frutas y verduras |
| [N] | Evaluación de la calidad de vida en mujeres de 40 a 59 años mediante la escala MRS. *Rev Méd Chile*. 2008;136(12) | Objetivo MRS por dominio |
| [N] | López F, Soares De Lorenzi D, d'Andretta Tanaka A. Calidad de vida de mujeres en fase de transición menopáusica evaluado por la MRS. *Rev Chil Obstet Ginecol*. 2010 | Pre vs. posmenopausia |
| [N] | López F, Soares De Lorenzi D. Síntomas climatéricos y estilos de vida de usuarias de APS, Santiago. *Rev Méd Chile*. 2011 | Síntomas frecuentes, sedentarismo, tabaco |
| [N] | ENUT 2023 | Contexto del cuidado |
| [N] | Estudio MUSA 2025 | Acceso a terapia hormonal |
| [L] | REDLINC, estudio multicéntrico latinoamericano con la MRS (n = 8.373) | Edad de menopausia, MRS de referencia |
| [L] | Assaf et al., dataset *Menopause*, figshare 20822032 (Jordania) | Tamaño de efectos, correlación entre subescalas |
| [L] | Harlow SD et al. STRAW+10. *Menopause*. 2012;19(4):387-395 | Etapas del envejecimiento reproductivo (§6.3) |
| [L] | OMS. *Research on the menopause in the 1990s*. TRS 866; 1996 | Menopausia = 12 meses sin menstruación |
| [L] | Heinemann K et al. The MRS scale: a methodological review. *Health Qual Life Outcomes*. 2004;2:45 | Cortes de severidad |
| [R] | 5 respuestas reales de la plataforma (BD local, exportadas sin RUT) | Patrones de suciedad |

## 15. Pendiente de validar con la profesora

1. La definición de **etapa menopáusica** (§6.3): es una adaptación propia de STRAW+10.
2. Los valores marcados **[S]**, en especial cuidado y trabajo (§8.3), los tamaños de los efectos
   (§9.3) y las consecuencias (§10).
3. La ventana de 4 años de perimenopausia que usa el generador (§6.1).
4. Que la región sea solo Coquimbo.
