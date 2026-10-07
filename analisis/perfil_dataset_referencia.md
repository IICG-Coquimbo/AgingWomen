# Perfil del dataset de referencia

> Fuente: figshare 20822032 "Data Set Menopause Women" (Assaf et al., Jordania), CC BY 4.0, DOI 10.6084/m9.figshare.20822032.v4. Generado por `analisis/perfil_referencia.py`.

## 1. Tamaño

- **200 filas × 61 columnas**, una fila por mujer, sin ID.
- Población: mujeres trabajadoras o jubiladas de Jordania, **45-60 años** (media 50.5, DE 4.9).
- Todo está codificado numéricamente (sin etiquetas). El significado se infiere de `cuestionario.docx`.
- Nulos: solo `Loss menstuartion` (62 = 31%), que es condicional (solo la responde quien ya está en menopausia). **No hay errores, duplicados ni outliers**: es un dataset ya limpio.

- **Importante:** el cuestionario original tenía 27 síntomas (bochornos, sudores, sueño, ánimo, urinarios, sexuales…) pero **esos ítems no vienen en el Excel**. Tampoco trae MRS, peso, talla, presión ni laboratorio. Lo único "de síntomas" es la escala de calidad de vida UQOL (Utian).

## 2. Columnas

| columna | tipo | significado probable | nulos | distribución | equivalente en nuestra encuesta |
|---|---|---|---|---|---|
| `Age` | numérica | Edad en años | 0% | 45-60, media 50.5 (DE 4.9) | fecha_nacimiento → edad |
| `City` | nominal | Gobernación de Jordania (1 Irbid/Norte, 2 Amán, 3 Zarqa, 4 Karak/Sur) | 0% | 1:45, 2:103, 3:18, 4:34 | region_residencia / comuna (solo como forma de la distribución) |
| `profession working` | nominal | Situación laboral (1 trabaja, 2 jubilada) | 0% | 1:117, 2:83 | trabaja_actualmente |
| `Unnamed: 3` | nominal | Tipo de trabajo (1 administrativo, 2 académico, 3 profesional, 4 salud, 5 otro) | 0% | 1:40, 2:49, 3:9, 4:47, 5:55 | estamento (no está en models.py) |
| `Increase Bp Thyroid gland` | nominal | Hipertensión (1 sí) | 0% | 1:58, 2:142 | usa_medicamentos_presion / presión EMPA |
| `Unnamed: 5` | nominal | Enfermedad tiroidea (1 sí) | 0% | 1:20, 2:180 | — |
| `Back pain` | nominal | Dolor de espalda severo (1 sí) | 0% | 1:51, 2:149 | MRS p4 (molestias musculares y articulares), aproximado |
| `DM` | nominal | Diabetes (1 sí) | 0% | 1:33, 2:167 | usa_medicamentos_diabetes / glicemia EMPA |
| `Heart disease` | nominal | Cardiopatía (1 sí) | 0% | 1:8, 2:192 | — |
| `Varcoise` | nominal | Várices (1 sí) | 0% | 1:29, 2:171 | — |
| `Constipation` | nominal | Constipación/diarrea crónica (1 sí) | 0% | 1:10, 2:190 | evacuacion_intestinal |
| `Respiratory` | nominal | Enfermedad respiratoria crónica (1 sí) | 0% | 1:10, 2:190 | — |
| `Tumors` | nominal | Tumores (1 sí) | 0% | 1:4, 2:196 | — |
| `chronicd` | nominal | Derivada: tiene alguna crónica (0/1) | 0% | 0:71, 1:129 | — |
| `Who give money` | nominal | Sostenedor principal del hogar | 0% | 1:25, 2:111, 3:50, 4:8, 5:6 | — |
| `Social status` | nominal | Estado civil (1 casada, 2 divorciada, 3 viuda, 4 soltera) | 0% | 1:174, 2:11, 3:10, 4:5 | tiene_pareja |
| `Educational degree` | ordinal | Educación (1 escolar, 2 diploma, 3 universitaria, 4 postgrado, 5 técnica) | 0% | 1:43, 2:50, 3:79, 4:24, 5:4 | nivel_educacion |
| `income` | ordinal | Ingreso suficiente (1 sí, 2 más o menos, 3 no) | 0% | 1:39, 2:86, 3:75 | — |
| `How do you evaluate your health status` | ordinal | Autoevaluación de salud (3 niveles, sentido no documentado) | 0% | 1:68, 2:52, 3:80 | — |
| `Loss menstuartion` | nominal | Cómo llegó a la menopausia (1 natural, 2 quirúrgica, 3 tratamiento); vacío = aún no menopausia | 31% | 1:127, 2:8, 3:3 | fecha_ultima_menstruacion (≥12 meses) / tiene_utero / tiene_ovario |
| `Children` | ordinal | N° de hijos vivos (categorizado 1-6) | 0% | 1:6, 2:19, 3:32, 4:57, 5:74, 6:12 | — |
| `Pregnancies` | ordinal | N° de embarazos (categorizado 1-4) | 0% | 1:11, 2:41, 3:71, 4:77 | — |
| `how do you evaluate knowledge about menopause` | ordinal | Conocimiento sobre menopausia (1 muy bueno … 4 malo) | 0% | 1:62, 2:72, 3:38, 4:28 | considera_informacion_suficiente / nivel_informacion_servicios |
| `source of information` | nominal | Fuente de información (1 TV, 2 redes, 3 familia/amigas, 4 salud) | 0% | 1:46, 2:61, 3:54, 4:39 | — |
| `Do you examine breast monthly` | nominal | Autoexamen de mama último año (1 sí) | 0% | 1:63, 2:137 | — |
| `Do you use mamogram` | nominal | Mamografía preventiva último año (1 sí) | 0% | 1:40, 2:160 | fecha_mamografia (EMPA, personal de salud) |
| `Do you use swap` | nominal | PAP último año (1 sí) | 0% | 1:38, 2:162 | fecha_ultimo_pap (EMPA, personal de salud) |
| `Do you apply routine exam` | nominal | Control ginecológico cada 6 meses (1 sí) | 0% | 1:31, 2:169 | fecha_ultimo_empa |
| `preventive` | nominal | Derivada: alguna conducta preventiva (0/1) | 0% | 0:109, 1:91 | — |
| `Do you use contraceptive` | nominal | Usó anticonceptivos hormonales alguna vez (1 sí) | 0% | 1:98, 2:102 | usa_metodo_anticonceptivo (no equivalente: aquí es "alguna vez") |
| `I could control my important things` | ordinal | Ítem UQOL recodificado a 3 niveles: "I could control my important things" | 0% | 1:27, 2:90, 3:83 | ítems de estilo de vida/ánimo (aproximado) |
| `I feel challenges to do my staff` | ordinal | Ítem UQOL recodificado a 3 niveles: "I feel challenges to do my staff" | 0% | 1:37, 2:91, 3:72 | ítems de estilo de vida/ánimo (aproximado) |
| `I think my work benefit my community` | ordinal | Ítem UQOL recodificado a 3 niveles: "I think my work benefit my community" | 0% | 1:20, 2:66, 3:114 | ítems de estilo de vida/ánimo (aproximado) |
| `I feel satisified with sexual life` | ordinal | Ítem UQOL recodificado a 3 niveles: "I feel satisified with sexual life" | 0% | 1:131, 2:53, 3:16 | ítems de estilo de vida/ánimo (aproximado) |
| `I am satisified with my emotional relation` | ordinal | Ítem UQOL recodificado a 3 niveles: "I am satisified with my emotional relation" | 0% | 1:78, 2:78, 3:44 | ítems de estilo de vida/ánimo (aproximado) |
| `I have appreciation from others` | ordinal | Ítem UQOL recodificado a 3 niveles: "I have appreciation from others" | 0% | 1:31, 2:86, 3:83 | ítems de estilo de vida/ánimo (aproximado) |
| `I am not satisified with my shape` | ordinal | Ítem UQOL recodificado a 3 niveles: "I am not satisified with my shape" | 0% | 1:34, 2:56, 3:110 | ítems de estilo de vida/ánimo (aproximado) |
| `I feel my nutritional status is appropriate` | ordinal | Ítem UQOL recodificado a 3 niveles: "I feel my nutritional status is appropriate" | 0% | 1:49, 2:102, 3:49 | ítems de estilo de vida/ánimo (aproximado) |
| `I could control my behavior` | ordinal | Ítem UQOL recodificado a 3 niveles: "I could control my behavior" | 0% | 1:43, 2:110, 3:47 | ítems de estilo de vida/ánimo (aproximado) |
| `I practice exercise 3 times at least` | ordinal | Ítem UQOL recodificado a 3 niveles: "I practice exercise 3 times at least" | 0% | 1:134, 2:55, 3:11 | ítems de estilo de vida/ánimo (aproximado) |
| `I feel moody in general` | ordinal | Ítem UQOL recodificado a 3 niveles: "I feel moody in general" | 0% | 1:29, 2:89, 3:82 | ítems de estilo de vida/ánimo (aproximado) |
| `I feel anxious` | ordinal | Ítem UQOL recodificado a 3 niveles: "I feel anxious" | 0% | 1:39, 2:98, 3:63 | ítems de estilo de vida/ánimo (aproximado) |
| `most things not under my control` | ordinal | Ítem UQOL recodificado a 3 niveles: "most things not under my control" | 0% | 1:35, 2:81, 3:84 | ítems de estilo de vida/ánimo (aproximado) |
| `I am satisified with my spouse relationship` | ordinal | Ítem UQOL recodificado a 3 niveles: "I am satisified with my spouse relationship" | 0% | 1:67, 2:78, 3:55 | ítems de estilo de vida/ánimo (aproximado) |
| `I feel no rest in my emotional life` | ordinal | Ítem UQOL recodificado a 3 niveles: "I feel no rest in my emotional life" | 0% | 1:20, 2:53, 3:127 | ítems de estilo de vida/ánimo (aproximado) |
| `I could not control my health` | ordinal | Ítem UQOL recodificado a 3 niveles: "I could not control my health" | 0% | 1:32, 2:94, 3:74 | ítems de estilo de vida/ánimo (aproximado) |
| `I am proud with my goals` | ordinal | Ítem UQOL recodificado a 3 niveles: "I am proud with my goals" | 0% | 1:23, 2:73, 3:104 | ítems de estilo de vida/ánimo (aproximado) |
| `I encourged in my life` | ordinal | Ítem UQOL recodificado a 3 niveles: "I encourged in my life" | 0% | 1:24, 2:96, 3:80 | ítems de estilo de vida/ánimo (aproximado) |
| `I am continuing identify my personal goal` | ordinal | Ítem UQOL recodificado a 3 niveles: "I am continuing identify my personal goal" | 0% | 1:26, 2:82, 3:92 | ítems de estilo de vida/ánimo (aproximado) |
| `I expect good things to happen in my life` | ordinal | Ítem UQOL recodificado a 3 niveles: "I expect good things to happen in my life" | 0% | 1:23, 2:90, 3:87 | ítems de estilo de vida/ánimo (aproximado) |
| `I feel in good health` | ordinal | Ítem UQOL recodificado a 3 niveles: "I feel in good health" | 0% | 1:26, 2:126, 3:48 | ítems de estilo de vida/ánimo (aproximado) |
| `I feel my physical abilities are high` | ordinal | Ítem UQOL recodificado a 3 niveles: "I feel my physical abilities are high" | 0% | 1:69, 2:103, 3:28 | ítems de estilo de vida/ánimo (aproximado) |
| `I am continuing work on my goals` | ordinal | Ítem UQOL recodificado a 3 niveles: "I am continuing work on my goals" | 0% | 1:39, 2:87, 3:74 | ítems de estilo de vida/ánimo (aproximado) |
| `agecat` | ordinal | Derivada: edad en 3 tramos (45-50, 51-55, 56-60) | 0% | 1:92, 2:60, 3:48 | — |
| `emotional` | numérica | UQOL subescala emocional (suma) | 0% | 6-30, media 22.3 (DE 4.8) | MRS psicológica (sentido inverso, aproximado) |
| `sexual` | numérica | UQOL subescala sexual (suma) | 0% | 3-15, media 7.7 (DE 2.6) | MRS urogenital p10 + tiene_actividad_sexual (aproximado) |
| `health` | numérica | UQOL subescala salud (suma) | 0% | 7-35, media 21.6 (DE 5.1) | MRS somática + hábitos (aproximado) |
| `occupational` | numérica | UQOL subescala ocupacional (suma) | 0% | 9-35, media 26.0 (DE 6.5) | EvaluacionTrabajo (aproximado) |
| `totalqol` | numérica | UQOL total (suma de 23 ítems, mayor = mejor calidad de vida) | 0% | 36-109, media 77.6 (DE 14.5) | MRS total (sentido inverso, aproximado) |
| `educationcat` | nominal | Derivada: educación en 2 grupos | 0% | 1:97, 2:103 | — |
| `finiacialcat` | nominal | Derivada: sostenedor en grupos (1, 2, 4) | 0% | 1:25, 2:161, 4:14 | — |

Nota: los 23 ítems UQOL vienen recodificados a **3 niveles**, pero las subescalas suman el original de 5 niveles (p. ej. `emotional` va de 6 a 30 = 6 ítems × 1-5). Sirve la subescala, no el ítem suelto.

## 3. Distribuciones clave

| index | mean | std | min | 25% | 50% | 75% | max |
|---|---|---|---|---|---|---|---|
| emotional | 22.3 | 4.8 | 6.0 | 19.8 | 22.0 | 26.0 | 30.0 |
| sexual | 7.7 | 2.6 | 3.0 | 6.0 | 7.5 | 9.0 | 15.0 |
| health | 21.6 | 5.1 | 7.0 | 18.0 | 21.0 | 25.0 | 35.0 |
| occupational | 26.0 | 6.5 | 9.0 | 22.0 | 27.0 | 31.0 | 35.0 |
| totalqol | 77.6 | 14.5 | 36.0 | 68.0 | 78.5 | 87.2 | 109.0 |
| Age | 50.5 | 4.9 | 45.0 | 46.0 | 50.0 | 54.0 | 60.0 |

**Etapa:**

| Loss menstuartion | n | pct |
|---|---|---|
| posmenopausia natural | 127 | 64.0 |
| pre/perimenopausia | 62 | 31.0 |
| quirúrgica | 8 | 4.0 |
| por tratamiento | 3 | 2.0 |

**Prevalencias (sí):** hipertensión 29%, diabetes 16%, tiroides 10%, dolor espalda 26%, várices 14%, cardiopatía 4%, mamografía año 20%, PAP año 19%, anticonceptivo alguna vez 49%, trabaja 58%, casada 87%.

Ejercicio ≥3 veces/semana: no es cierto 67%, algo 28%, muy cierto 6%.

## 4. Correlaciones relevantes (Spearman)

Mayor UQOL = mejor calidad de vida (sentido opuesto al MRS). * p<0.05, ** p<0.01.

| index | emotional | sexual | health | occupational | totalqol |
|---|---|---|---|---|---|
| edad | +0.02 | -0.22** | -0.03 | -0.12 | -0.10 |
| posmenopausia | -0.07 | -0.18* | -0.04 | -0.06 | -0.10 |
| trabaja | +0.13 | +0.23** | +0.10 | +0.19** | +0.22** |
| ejercicio_3v | +0.21** | +0.18* | +0.55** | +0.16* | +0.36** |
| educacion | +0.13 | +0.42** | +0.11 | +0.23** | +0.27** |
| ingreso_insuf | -0.06 | +0.07 | +0.01 | +0.14 | +0.07 |
| n_cronicas | -0.12 | -0.16* | -0.18* | -0.15* | -0.20** |
| casada | -0.02 | +0.32** | +0.00 | +0.09 | +0.09 |
| animo_inv | +0.74** | +0.34** | +0.38** | +0.28** | +0.56** |
| ansiedad_inv | +0.73** | +0.30** | +0.37** | +0.24** | +0.53** |

**Entre subescalas:**

| index | emotional | sexual | health | occupational |
|---|---|---|---|---|
| emotional | 1.0 | 0.32 | 0.52 | 0.48 |
| sexual | 0.32 | 1.0 | 0.25 | 0.48 |
| health | 0.52 | 0.25 | 1.0 | 0.45 |
| occupational | 0.48 | 0.48 | 0.45 | 1.0 |

## 5. Lectura para la simulación

- Efectos **pequeños-moderados** y mucho ruido: el modelo de regresión del análisis anterior explicaba R² ≈ 0.18 de la calidad de vida. Una simulación realista no debería tener efectos más fuertes que eso para las variables de estilo de vida.
- Edad y etapa casi no se asocian con UQOL en este dataset (ver tabla); la literatura MRS sí reporta más síntomas somáticos/urogenitales en posmenopausia → ahí usaremos literatura, marcado como tal.
- Ejercicio (sobre todo con la subescala salud, rho 0.55), trabajar y educación son los factores protectores más claros; las enfermedades crónicas restan un poco. `animo_inv`/`ansiedad_inv` vienen invertidos (mayor = menos síntomas) y son parte de la subescala emocional, por eso correlacionan tanto.
- Edad y etapa solo se asocian (débil) con la subescala sexual.
- Sirve como referencia para: distribución de edad, proporción pre/peri vs posmenopausia (~31/69 %), menopausia quirúrgica (~4 %), prevalencias de HTA/DM, prevención (mamografía/PAP ~20 %), proporción de ejercicio regular, y tamaño de efecto del ejercicio.
- **No sirve** para: ítems MRS, antropometría, laboratorio, hábitos alimentarios, tabaco/alcohol, tareas de cuidado, conocimiento del sistema de salud chileno. Eso irá con literatura o supuestos explícitos (Paso 1).
- Contexto distinto (Jordania 45-60 vs. UCN Coquimbo 40-60): las proporciones deben adaptarse, no copiarse.
