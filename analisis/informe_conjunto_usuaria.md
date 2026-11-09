# Informe del conjunto de datos de la usuaria común (Fases 34A y 34B)

Este informe resume cómo se construyó el conjunto de datos sintético de la usuaria común
(Fase 34A) y cómo se limpió (Fase 34B). Describe su tamaño, su organización, los tipos de
datos que contiene y sus valores resumidos. Explica también qué valores faltaban o estaban
duplicados y qué tratamiento recibió cada caso.

Al final se agregan las herramientas y los comandos usados para leer los datos, detectar
faltantes y duplicados y hacer el análisis exploratorio (sección 11), y los tipos de análisis
realizados (sección 12).

Los detalles completos están en `analisis/informe_sintetico.md` (Fase 34A),
`analisis/informe_limpieza_usuaria.md` (Fase 34B) y `analisis/informe_eda_usuaria.md` (Fase 34C).

## 1. Qué se hizo en cada fase

**Fase 34A: generación del conjunto sintético.** La profesora pidió el 20-10 un conjunto nuevo,
coherente con la realidad chilena, que incluyera solo a la usuaria común y su primera encuesta
(sin la segunda ronda ni el personal de salud). Se generó con `analisis/generar_sintetico.py`
a partir del conjunto de datos Menopause (figshare) y de los patrones observados en las
respuestas reales de la plataforma. El resultado son tres archivos:

| Archivo | Contenido |
|---|---|
| `dataset_usuaria_verdad.csv` | 550 participantes sin errores (la "verdad"). |
| `dataset_usuaria_sucio.csv` | El mismo conjunto con errores agregados a propósito: 565 filas. |
| `bitacora_suciedad.csv` | Registro de cada error agregado: 3.533 entradas. |

Los efectos sobre los síntomas siguen lo validado por la profesora:

- **Aumentan la severidad:** IMC, diabetes, doble carga (trabajo y cuidado), estrés laboral, sobrecarga, tabaco, alcohol y marihuana.
- **La reducen:** lugar de trabajo comprensivo, días de ejercicio y vasos de agua.
- **Sin efecto:** la alimentación no es protectora en ningún caso.

Los campos del servicio de salud quedan vacíos.

**Fase 34B: limpieza.** El script `analisis/limpiar_dataset.py` toma el conjunto sucio y produce
`datos/limpio_usuaria/dataset_usuaria_limpio.csv`. Los códigos válidos y la lógica condicional
de las preguntas se leen del código de la plataforma, así la limpieza nunca contradice lo que
la encuesta acepta. Como existe la versión verdadera, se pudo medir qué tan bien funciona la
limpieza (sección 8).

## 2. Tamaño del conjunto de datos

| | Conjunto sucio (entrada) | Conjunto limpio (salida) |
|---|---|---|
| Filas | 565 | **546** |
| Columnas | 128 | **176** |
| Participantes distintas | 550 (con 15 filas repetidas) | 546 |
| Filas con MRS completo | — | 529 |

- **Filas:** se excluyeron 19 (15 repetidas y 4 por edad; ver sección 7).
- **Columnas:** la limpieza agregó 48:
  - 15 variables derivadas, como edad, puntajes MRS, severidad, IMC y etapa menopáusica;
  - 31 marcas `<variable>_imputado`;
  - 2 marcas de incoherencia.

## 3. Cómo está organizado

Cada **fila es una participante** y su primera encuesta (ronda 1). Todas están autoaplicadas
(`origen_registro = AUTO`), viven en la Región de Coquimbo y respondieron entre el 2 de marzo
y el 30 de septiembre de 2026.

Las **columnas siguen las secciones de la encuesta de la plataforma**. De las 128 columnas
originales, 101 son variables de respuesta (están descritas en
`datos/limpio_usuaria/diccionario_variables.csv`). Las 27 restantes son:

- identificadores y metadatos (id, RUT cifrado, fechas de registro);
- fechas;
- comuna;
- textos libres del tipo "otro, ¿cuál?".

| Sección | Variables | Contenido |
|---|---|---|
| Identificación | 7 | género, nivel educacional, origen, pueblo originario, región, trabajo, excepción de edad |
| MRS (síntomas y salud ginecológica) | 27 | las 11 preguntas MRS, menstruación, anticoncepción, terapia hormonal, útero/ovario, pareja, medicamentos, digestión |
| Segmento EMPA | 13 | peso, talla, cintura; el resto (laboratorio, presión, PAP, mamografía) es solo para personal de salud |
| Conocimiento del sistema | 15 | previsión, conocimiento del programa de climaterio, acceso, información deseada |
| Evaluación del trabajo | 5 | rendimiento, bienestar, ausencias, lugar comprensivo, estrés (solo quien trabaja) |
| Tareas de cuidado | 4 | si cuida, a cuántas personas, a quién, sobrecarga |
| Actividad física | 8 | días de ejercicio, tipos (aeróbico, bajo impacto, fuerza) y su frecuencia, horas sentada |
| Hábitos de vida | 17 | alimentación, agua, comida fuera, falta de tiempo, tabaco, marihuana, alcohol |
| Evaluación de satisfacción | 5 | encuesta voluntaria sobre la plataforma |

Algunas preguntas **no aplican a todas** porque la encuesta solo las muestra según respuestas
anteriores:

- la sección Trabajo aplica a 298 participantes;
- Cuidado, a 257;
- las preguntas de menstruación, a 204 (quienes informaron fecha de última menstruación);
- la encuesta de satisfacción la respondieron 264.

## 4. Tipos de datos

Según su naturaleza (diccionario de variables, 101 variables de respuesta):

| Tipo | Variables | Ejemplos |
|---|---|---|
| Ordinal (escala con orden) | 49 | preguntas MRS (0-4), frecuencias de consumo (1 = nunca … 5 = diariamente), porciones (1 = no consumo … 5 = 7 o más), días de ejercicio (1 = 0 días … 5 = todos los días), escalas de acuerdo |
| Categórica (sin orden) | 38 | sí/no, previsión, nivel educacional, tipo de anticonceptivo |
| Continua (numérica) | 11 | peso (kg), talla (cm), cintura (cm), presión y laboratorio (vacíos) |
| Selección múltiple | 3 | a quién cuida, principales dificultades, tipo de información deseada |

Las escalas ordinales se guardan con el **código numérico de la plataforma**. Por ejemplo,
en días de ejercicio el 1 significa "0 días", no "1 día".

Según el formato de almacenamiento en el CSV limpio:

| Formato | Columnas |
|---|---|
| Número entero | 64 |
| Número decimal | 51 |
| Texto | 60 |
| Lógico (verdadero/falso) | 1 |

## 5. Valores resumidos básicos (conjunto limpio)

### 5.1 Variables numéricas

| Variable | n | Media | Desv. est. | Mín. | Mediana | Máx. |
|---|---|---|---|---|---|---|
| Edad (años) | 546 | 51,0 | 7,7 | 36 | 50 | 65 |
| Peso (kg) | 290 | 71,3 | 16,0 | 40,4 | 69,4 | 122,8 |
| Talla (cm) | 331 | 155,6 | 5,8 | 140 | 156 | 176 |
| IMC (kg/m²) | 277 | 29,2 | 6,3 | 18,2 | 28,5 | 45,7 |
| Cintura (cm) | 260 | 93,4 | 16,5 | 61 | 93 | 138 |
| Horas sentada al día | 546 | 6,3 | 2,4 | 1 | 6 | 14 |
| Meses desde la última menstruación | 524 | 56,6 | 64,0 | 0 | 33 | 293 |
| MRS total (0-44) | 529 | 16,4 | 9,3 | 0 | 16 | 42 |
| MRS somático | 529 | 5,9 | 4,1 | 0 | 5 | 16 |
| MRS psicológico | 529 | 7,7 | 4,2 | 0 | 8 | 16 |
| MRS urogenital | 529 | 2,7 | 2,5 | 0 | 2 | 12 |

Las 22 participantes menores de 40 años no son un error. La encuesta admite una excepción de
edad: 13 por menopausia quirúrgica y 9 por ausencia de menstruación.

### 5.2 Severidad de los síntomas (MRS)

| Severidad (cortes estándar) | Participantes | % |
|---|---|---|
| Sin síntomas o muy leves (0-4) | 56 | 10,6 |
| Leve (5-8) | 74 | 14,0 |
| Moderada (9-15) | 118 | 22,3 |
| Severa (16-44) | 281 | 53,1 |

### 5.3 Variables categóricas principales

| Variable | Distribución |
|---|---|
| Tramo de edad | <40: 22 · 40-44: 105 · 45-49: 124 · 50-54: 116 · 55-59: 83 · 60-65: 96 |
| Etapa menopáusica | posmenopausia 323 (59 %) · premenopausia 100 (18 %) · perimenopausia 82 (15 %) · quirúrgica 19 · indeterminada 22 |
| Trabaja actualmente | sí 320 (59 %) · no 226 |
| Cuida a otras personas | sí 257 (47 %) · no 289 |
| Doble carga (trabaja y cuida) | sí 150 (27 %) · no 396 |
| Tiene pareja | sí 367 (67 %) · no 179 |
| Previsión | FONASA 447 (82 %) · ISAPRE 75 · ninguna 15 · FF. AA. 7 · no sabe 2 |
| Categoría de IMC | no informado 269 (49 %) · obesidad 106 · sobrepeso 105 · normal 64 · bajo peso 2 |
| Usa medicamentos para diabetes | sí 67 (12 %) · no 479 |
| Tabaco | nunca 413 (76 %) · alguna vez por semana 49 · diariamente 84 (15 %) |
| Alcohol | nunca 199 (36 %) · 1-2 veces por semana 274 (50 %) · más seguido 73 |

## 6. Valores faltantes

### 6.1 Cuánto faltaba

El conjunto sucio tiene 72.320 celdas (565 × 128), de las cuales 22.744 estaban vacías (31 %).
No todos esos vacíos son un problema. Se distinguen tres casos:

1. **Vacíos esperados ("no aplica").** La encuesta no habría mostrado la pregunta. Por ejemplo:
   - la sección Trabajo para quien no trabaja;
   - la sobrecarga para quien no cuida;
   - las 14 columnas del servicio de salud (laboratorio, presión, PAP, mamografía, talla
     máxima), que están vacías en todas las filas porque las encuestas son autoaplicadas.

   **Tratamiento:** se dejan vacíos, no se imputan y no cuentan como faltantes.
2. **Faltantes reales.** La pregunta aplicaba y no se respondió. La bitácora registra 2.259
   celdas omitidas, más 343 omisiones "en cascada": si falta la respuesta que abre una
   pregunta, las preguntas que dependen de ella también quedan vacías.
3. **Faltantes disfrazados.** Celdas con un valor que en realidad significa "sin dato":
   - 105 celdas con texto: "N/A", "NA", "-", "sin dato";
   - 98 con números centinela: -1, 99, 999, 9999.

   **Tratamiento:** se convirtieron en vacíos y después se trataron como faltantes reales.

El porcentaje de faltantes de cada variable se calcula **solo sobre las filas donde la
pregunta aplica**.

### 6.2 Reglas de tratamiento

| Situación | Tratamiento |
|---|---|
| Faltan menos del 5 % | Se imputa: la **moda** en categóricas y la **mediana** en ordinales y continuas. |
| Faltan entre el 5 % y el 30 % | Se imputa igual y se agrega la marca `<variable>_imputado` (1 = imputado), para poder controlar su efecto en el análisis. |
| Faltan más del 30 % | No se imputa y la variable no se usa para modelar. |
| Preguntas MRS | **Nunca se imputan**, porque son la variable resultado. |
| Selección múltiple y encuesta de satisfacción | No se imputan. |
| Pregunta que depende de una fecha de última menstruación vacía | No se imputa, porque no se sabe si la pregunta aplicaba (22 casos). |

### 6.3 Resultado por variable

**Más del 30 % faltante: no se imputan**

| Variable | Aplica a | Faltan | % |
|---|---|---|---|
| Cintura | 546 | 286 | 52,4 |
| Peso | 546 | 256 | 46,9 |
| Talla | 546 | 215 | 39,4 |

**IMC:** como peso y talla faltan en casi la mitad de las participantes, el IMC **no se
imputa**. Se usa como categoría (`imc_categoria`), con un nivel adicional "no informado"
(269 participantes, 49 %). Inventar el peso de tantas participantes cambiaría justamente el
factor más fuerte. Este nivel de faltantes es realista: en las respuestas reales de la
plataforma, solo 2 de 5 participantes informaron peso y talla.

**Entre el 5 % y el 30 %: imputadas con marca (31 variables)**

| Variable | Faltan | % | Valor imputado |
|---|---|---|---|
| Tipo de sangrado | 33 de 204 | 16,2 | moda: moderado |
| Regularidad de la menstruación | 27 de 204 | 13,2 | moda: regular |
| Usa método anticonceptivo | 25 de 204 | 12,3 | moda: no |
| Evaluación de la atención recibida | 11 de 127 | 8,7 | mediana: 3 |
| Tipo de método anticonceptivo | 6 de 73 | 8,2 | moda: DIU |
| Días de ejercicio | 37 de 546 | 6,8 | mediana: 1-2 días |
| Cambio en la relación de pareja | 23 de 339 | 6,8 | mediana: 2 |
| Frecuencia de comida fuera | 35 de 546 | 6,4 | mediana: 2 |
| Alimentación (panes, verduras, lácteos, jugos, carnes) | 31 a 33 de 546 | 5,7-6,0 | mediana de cada una |
| Sección Trabajo (bienestar, ausencias, lugar comprensivo) | 16-17 de 298 | 5,4-5,7 | mediana |
| Otras: actividad sexual, presión, digestión, pareja, alcohol, aeróbico, fuerza, conocimiento del sistema | 23-31 | 5,1-6,8 | moda o mediana |

**Menos del 5 %: imputadas sin marca.** Se imputaron 32 variables con entre 2 y 27 faltantes
cada una. Entre ellas están tabaco, marihuana, agua, frutas, previsión, terapia hormonal,
medicamentos para diabetes, trabaja actualmente y cuida a otras personas. La lista completa
está en el informe de limpieza.

**No se imputan**

| Variables | Faltan | Motivo |
|---|---|---|
| Preguntas MRS | 1 a 4 por pregunta | Las **17 participantes** con alguna pregunta MRS vacía o fuera de rango quedan sin puntaje y fuera del análisis de severidad (529 de 546 con MRS completo). |
| Selección múltiple: a quién cuida, dificultades, información deseada | 7 a 20 | No se imputan. |
| Encuesta de satisfacción | 1 a 3 | Es voluntaria. |

Otras 19 variables no tenían ningún faltante.

### 6.4 Faltantes deducidos (no imputados)

Antes de imputar, se recuperaron valores que se pueden deducir de otras respuestas:

| Caso | Valor deducido | Celdas |
|---|---|---|
| Responde cuántas personas cuida, pero "cuida a otras personas" está vacía | sí | 4 |
| Indica un tipo de anticonceptivo, pero "usa método anticonceptivo" está vacía | sí | 5 |
| Región vacía o mal escrita, con comuna informada | región deducida desde la comuna | 8 |
| Respondió la sección Trabajo, pero "trabaja actualmente" está vacía | sí | 1 |
| Otros casos equivalentes: fuerza, control en el consultorio, consulta por síntomas, previsión | según la respuesta relacionada | 5 |

## 7. Valores duplicados

El conjunto sucio tenía **15 filas repetidas** de dos tipos. Ambos tipos se detectaron con el
RUT cifrado (`rut_hash`), que identifica a cada participante sin guardar su RUT:

| Tipo | Filas | Cómo se detectó | Tratamiento |
|---|---|---|---|
| Duplicado exacto | 8 | La fila es idéntica a otra en todas sus columnas: el mismo envío guardado dos veces. | Se conserva una y se **elimina la copia**. |
| RUT repetido (versión anterior) | 7 | La misma participante tiene dos encuestas distintas: una versión antigua y otra corregida. | Se conserva la **más reciente** y se elimina la antigua. |

Además, se excluyeron 4 filas por edad:

| Motivo | Filas | Tratamiento |
|---|---|---|
| Mayor de 65 años (68, 69 y 71 años) | 3 | Fuera del criterio de inclusión (40-65 años, o menor de 40 con excepción): se excluye. |
| Fecha de nacimiento imposible (posterior a la evaluación) | 1 | La edad no se puede verificar: se excluye. |

Todas las filas excluidas están en `datos/limpio_usuaria/excluidas.csv`, con su motivo.
Después de la limpieza no queda ninguna participante repetida.

## 8. Otros errores corregidos

Además de los faltantes y duplicados, el conjunto sucio traía errores de formato y de coherencia:

| Error | Celdas | Tratamiento |
|---|---|---|
| Códigos escritos de otra forma ("Sí", "si", "S", "Femenino", "TRUE") | 268 | Recodificados al código de la plataforma. |
| Espacios sobrantes | 166 | Eliminados. |
| Fechas en formato DD/MM/AAAA o solo el año | 108 | Normalizadas a AAAA-MM-DD (nacimiento) y AAAA-MM o AAAA (última menstruación). |
| Unidad escrita en el valor ("80 cm") o coma decimal ("72,0") | 51 | Se quitó la unidad y se cambió la coma por punto. |
| Talla en metros (1,55) | 8 | Multiplicada por 100. |
| Talla imposible (1565, sin punto decimal) | 2 | Vaciada, porque no se sabe cuál era el valor. |
| Cintura 0 en vez de vacía | 30 | Vaciada. |
| Cintura incoherente con el IMC (75 cm con IMC 43) | 1 | Vaciada. |
| Respuesta a una pregunta que no aplicaba (p. ej., sobrecarga sin cuidar a nadie) | 32 | Borrada. |
| Pregunta MRS fuera de rango (5 o 9 en una escala 0-4) | 17 | Vaciada; la participante queda sin puntaje MRS. |
| Ejercicio al menos 1 día sin marcar ningún tipo | 4 filas | Se conserva y se marca en `incoherencia_ejercicio`, porque no se sabe cuál de los dos datos está mal. |
| Píldora anticonceptiva y terapia hormonal a la vez | 2 filas | Se conserva y se marca en `incoherencia_pildora_th`. |

**Regla propia del análisis:** el cambio en la relación de pareja se dejó como "no aplica" en
las 196 participantes sin pareja. La plataforma muestra esa pregunta a todas.

## 9. Qué tan bien funcionó la limpieza

Al comparar el conjunto limpio con la versión verdadera:

- **Errores de formato y coherencia:** se recupera el **83 %** de los errores agregados.
- **Omisiones:** no se pueden recuperar con certeza; solo se imputan o se deducen. Contando
  también las omisiones, el 41,6 % de las 3.518 celdas alteradas volvió a su valor verdadero.
- **Celdas correctas cambiadas por error:** de 65.353 celdas que venían bien, solo cambió 1
  (una cintura válida que se marcó como incoherente).
- **Filas excluidas:** las 19 eran efectivamente erróneas (copias, versiones antiguas o edades
  alteradas por el error).

## 10. Decisiones que conviene validar con la profesora

- IMC sin imputar, usado como categoría con el nivel "no informado" (49 %).
- El cambio en la relación de pareja como "no aplica" sin pareja.
- La definición de etapa menopáusica (STRAW+10 simplificado).
- Las correcciones de unidad (talla en metros multiplicada por 100).

## 11. Herramientas y comandos utilizados

Esta sección describe los comandos usados en la generación (34A), la limpieza (34B) y el
análisis exploratorio (34C). No se usó Google Colab: los scripts se ejecutan localmente desde
la carpeta `analisis/` del proyecto.

### 11.1 Bibliotecas

| Biblioteca | Versión | Uso |
|---|---|---|
| pandas | 2.2.3 | Lectura, limpieza, conteos y tablas de los conjuntos de datos |
| NumPy | 2.2.4 | Cálculos numéricos y generación aleatoria del conjunto sintético |
| SciPy | 1.15.2 | Pruebas estadísticas (Spearman, chi², Mann-Whitney, Kruskal-Wallis, FDR) |
| Matplotlib | 3.10.1 | Todas las figuras |
| scikit-learn | 1.6.1 | Random Forest de la Fase 33 (anexo); escalado, PCA y clústeres en las fases siguientes |

### 11.2 Lectura del conjunto de datos

| Comando | Función |
|---|---|
| `pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding='utf-8-sig')` | Lee el CSV y lo carga en un DataFrame de pandas. |
| `dtype=str` | Lee todas las columnas como texto, para que pandas no "adivine" tipos. Así un "Sí" mal escrito, un "999" o un "80 cm" no se transforman ni se pierden antes de que la limpieza los detecte. |
| `keep_default_na=False` | Impide que pandas convierta por su cuenta "NA" o "N/A" en vacíos. Esos textos son faltantes disfrazados, y la limpieza necesita verlos para contarlos y registrarlos. |
| `encoding='utf-8-sig'` | Lee bien las tildes y la ñ, y quita la marca inicial (BOM) que Excel agrega a los CSV. |
| `.replace('', np.nan)` | En el conjunto limpio, convierte las celdas vacías en faltantes reales (`NaN`) para los cálculos. |
| `pd.to_numeric(serie, errors='coerce')` | Convierte a número solo las columnas que se van a calcular. |

**Verificación de la carga.** En vez de `df.head()` y `print(...)`, cada script escribe un
informe con el número de filas y columnas leídas (`df.shape`), las filas excluidas con su motivo
y el conteo de faltantes por variable. Así la verificación queda documentada y se puede
reproducir.

### 11.3 Duplicados

| Comando | Función |
|---|---|
| `df.duplicated(subset=columnas, keep='first')` | Marca como duplicada cada fila idéntica a una anterior en todas las columnas, salvo el identificador interno. `keep='first'` conserva la primera aparición. |
| `df.sort_values('sincronizado_en')` | Ordena las encuestas por fecha de envío. |
| `orden.duplicated(subset=['rut_hash'], keep='last')` | Marca las encuestas de un RUT que ya aparece. `keep='last'` conserva la más reciente y marca las antiguas. |
| `df[~dup]` y `df.drop(index=...)` | Quita del conjunto las filas marcadas. |
| `.assign(motivo_exclusion=...)` y `pd.concat(...)` | Guarda las filas quitadas, con su motivo, en `excluidas.csv`. |

### 11.4 Valores faltantes

**Detectar faltantes disfrazados**

| Comando | Función |
|---|---|
| `df[c].map(lambda v: plano(v) in CENTINELAS_TEXTO)` | Detecta textos que significan "sin dato" ("N/A", "NA", "-", "sin dato"), sin importar mayúsculas, tildes ni espacios. |
| `df[c].map(lambda v: a_numero(v) in {-1, 99, 999, 9999})` | Detecta números centinela. Respeta el 99 cuando es una opción válida de la encuesta. |
| `df.loc[es_centinela, c] = pd.NA` | Convierte esos valores en faltantes reales. |

**Contar faltantes**

| Comando | Función |
|---|---|
| `df[c].isna()` y `df[c].notna()` | Identifican las celdas vacías y las respondidas. |
| `aplica & df[c].isna()` y `.sum()` | Cuentan los faltantes solo en las filas donde la pregunta aplica. `aplica` sale de la lógica condicional de la plataforma. |
| `100 * faltan / filas_aplica` | Calcula el porcentaje de faltantes que decide el tratamiento (< 5 %, 5-30 % o > 30 %). |
| `df[TRABAJO].notna().any(axis=1)` | Detecta si una participante respondió alguna pregunta de una sección; sirve para deducir respuestas vacías (sección 6.4). |

**Imputar y marcar**

| Comando | Función |
|---|---|
| `valores.mode()` | Calcula la moda, que se usa en las categóricas. |
| `np.percentile(numeros, 50, method='lower')` | Calcula la mediana de las ordinales como un valor real de la escala (sin decimales intermedios). |
| `numeros.median()` | Calcula la mediana de las continuas. |
| `df.loc[faltante, c] = valor` | Reemplaza los faltantes por el valor imputado. |
| `df[f'{c}_imputado'] = faltante.map(int)` | Crea la marca de imputación (1 = imputado, 0 = original). |

### 11.5 Análisis exploratorio (Fase 34C)

| Comando | Función |
|---|---|
| `x.mean()`, `x.std()`, `x.median()`, `x.quantile([.25, .75])`, `x.min()`, `x.max()` | Calculan los descriptivos de las variables numéricas. |
| `df[c].value_counts()` | Cuenta las frecuencias de cada categoría. |
| `df[c].str.split(', ').explode()` | Separa las respuestas de selección múltiple (por ejemplo, a quién cuida) para contar cada opción por separado. |
| `np.floor(x / ancho) * ancho` | Agrupa IMC, peso y talla en intervalos para el histograma. |
| `pd.crosstab(grupo, severidad, normalize='index')` | Arma tablas de contingencia, por ejemplo la severidad por tramo de edad o por situación laboral. |
| `q1 - 1.5 * ric` y `q3 + 1.5 * ric` | Calculan los límites de la regla de Tukey para los atípicos. Los atípicos se informan, pero no se eliminan. |
| `stats.spearmanr(x, y)` | Calcula la correlación de Spearman de cada variable ordinal, continua o binaria con la severidad. |
| `stats.kruskal(*grupos)` | Prueba de Kruskal-Wallis para categóricas de más de dos valores. |
| `stats.chi2_contingency(tabla)` | Prueba chi² de independencia; con ella se calcula la V de Cramér. |
| `stats.mannwhitneyu(a, b)` | Prueba de Mann-Whitney para comparar a quienes trabajan y quienes no en las variables continuas. |
| `stats.false_discovery_control(p, method='bh')` | Corrección de Benjamini-Hochberg (FDR) por hacer muchas pruebas a la vez. |
| `X.corr(method='spearman')` | Calcula la matriz de Spearman entre todas las variables y la severidad. |
| `ax.hist`, `ax.barh`, `ax.boxplot`, `ax.imshow` (Matplotlib) | Dibujan los histogramas, las barras, las cajas y el mapa de calor. |

## 12. Tipos de análisis realizados

| Tipo | Qué se hizo | Dónde |
|---|---|---|
| **Univariado** (una variable a la vez) | Descriptivos de las numéricas; frecuencias de todas las variables, con un gráfico por pregunta (incluye salud ginecológica, medicamentos, digestión, a quién cuida y los 11 síntomas del MRS); histograma del MRS y de IMC, peso y talla; severidad en 4 clases; perfil de los 11 síntomas (% en grado moderado o mayor); faltantes por variable; atípicos con Tukey; variables con poca variación (≥ 90 % en una categoría) | Fase 34C, secciones 2-4; este informe, sección 5 |
| **Bivariado** (dos variables) | Spearman o Kruskal-Wallis de cada variable con la severidad, también para las variables ginecológicas, medicamentos para la presión, evacuación intestinal y distensión (corrección FDR aparte); chi² de severidad por edad y por trabajo; comparación entre trabajadoras y no trabajadoras de cada pregunta y de cada síntoma (chi² y Mann-Whitney); consecuencias según la severidad | Fase 34C, secciones 2.1, 3, 5, 6 y 8 |
| **Multivariado, en su forma descriptiva** | Matriz de Spearman entre todas las variables, para detectar redundancias (cuida, cantidad y sobrecarga, con rho mayor a 0,9 en valor absoluto); severidad cruzada por tramo de edad y situación laboral a la vez | Fase 34C, secciones 5 y 6 |
| **Multivariado, con modelos** | Random Forest con todas las variables juntas, sobre el conjunto de la profesora | Fase 33 (anexo) |

En el conjunto de la usuaria todavía **no se ha hecho un análisis multivariado con modelos**. La
matriz de correlaciones compara las variables de a pares; no modela todas a la vez. El análisis
multivariado propiamente tal corresponde a las fases siguientes del plan de la profesora:

- selección de variables por entropía (Fase 35);
- PCA (Fase 37);
- K-Means y clúster aglomerativo (Fase 37).
