# Módulo de cuidados: versión complementaria exploratoria de FCBF

*Registrado el 03-11-2026, después de conocer la ejecución oficial de la Fase 35B y su análisis complementario, y antes de ejecutar esta versión.*

## 1. Carácter

Este análisis es **exploratorio y posterior a los resultados anteriores**. No sustituye el resultado oficial de la Fase 35B: 0 variables seleccionadas con 5.000 permutaciones y q < 0,05 (commit `745d689937a18c35b62fd25eccc401b169b20e11`, protocolo `analisis/protocolo_fase35b.md`). Tampoco sustituye el análisis complementario `analisis/protocolo_complementario_35b.md`.

La decisión de incorporar la sobrecarga se tomó conociendo esos resultados y diagnósticos previos de esta variable, de modo que sus resultados no son confirmatorios.

## 2. Pregunta

¿Cómo cambian la relevancia, la redundancia y la selección si `sobrecarga_fisica_emocional` compite como candidata, con un tratamiento válido de su cobertura, junto con `doble_carga`, `cantidad_personas_cuida` y las demás candidatas?

Las tres variables quedan **disponibles como candidatas; ninguna tiene la selección garantizada**. Cada una puede resultar no relevante, redundante o seleccionada, y esa decisión se informa sin alterarla.

## 3. Conjunto analizado

- **Candidatas:** las 30 de la Fase 35B más `sobrecarga_fisica_emocional`, en total 31.
- **Controles:** `edad`, `imc`, `usa_medicamentos_diabetes` y `trabaja_actualmente`. Pasan sin filtro y no compiten.
- **Fuera:** `prevision` sigue pendiente; `etapa_menopausica` y las preguntas menstruales no se reincorporan.
- **Vista temporal:** se construye en memoria con `datos/analitico/dataset_fase35.csv`, `datos/limpio_usuaria/dataset_usuaria_limpio.csv` y `datos/sintetico/dataset_usuaria_sucio.csv`. No se genera ni se modifica ningún dataset.

## 4. Poblaciones

Las poblaciones se definen solo con los datos actuales.

| Población | n | Condición |
|---|---:|---|
| Todas | 529 | `dataset_fase35.csv` |
| Laboral | 287 | Con valor en ambas preguntas laborales en el conjunto limpio (máscara de la Fase 35B, sin cambios) |
| Cuidadoras | 251 | `cuida_otras_personas` = SI en el conjunto limpio |
| **Sobrecarga observada (principal)** | **239** | Cuidadora con respuesta válida de 1 a 5 en el conjunto sucio, idéntica en el conjunto limpio |
| Sobrecarga observada y laboral | 130 | Intersección de las dos anteriores |
| Cuidadoras y laboral | 137 | Solo para la sensibilidad con 251 |

Cada medición usa las personas con cobertura común de las variables que participan. Si cualquiera de los tamaños de control cambia, el programa se detiene.

## 5. «No aplica» no es cero

Quienes no cuidan no tienen sobrecarga, ni siquiera mínima. La escala va de 1 a 5, y 1 significa «Nunca o casi nunca». Por eso:

- Fuera de su población, la sobrecarga queda vacía. El programa rechaza cualquier valor, incluido 0.
- Nunca entra una categoría «no aplica» en una SU, una prueba o un promedio.
- La única excepción es una fila de referencia de `relacion_cuidados.csv`, rotulada como tal, que documenta el artefacto de usar ceros. No interviene en ninguna decisión.

La alternativa con categoría «no aplica» no se ejecuta. Para SU equivale a usar 0, porque produce la misma partición, y mezclaría cuidar o no cuidar con el grado de sobrecarga.

## 6. Adaptación de FCBF: tercera etapa de cobertura

Esta es la **única adaptación nueva**. Las etapas 1 y 2 usan sin cambios la función congelada `fcbf.seleccionar`, con los q calculados en la familia de 31.

| Etapa | Variables | Población |
|---|---|---|
| 1 | No laborales | 529 |
| 2 | Laborales | 287; solo se pueden eliminar laborales |
| 3 | `sobrecarga_fisica_emocional` | 239, o 130 al compararla con una laboral |

**Regla de la Etapa 3.** Si la sobrecarga es relevante, se compara con cada variable Z seleccionada en las etapas anteriores. Z la elimina solo si se cumplen todas estas condiciones, medidas en la población común de Z y la sobrecarga:

1. SU(Z, severidad) ≥ SU(sobrecarga, severidad).
2. SU(Z, sobrecarga) ≥ SU(sobrecarga, severidad).
3. Solo en la variante adaptada, q del par por debajo del umbral. La variante estándar no exige q en el par, igual que en las etapas anteriores.

Si varias Z pueden eliminarla, se registra la de mayor SU con severidad en su población común; un empate se resuelve por orden alfabético.

**La sobrecarga nunca elimina a otra variable.** Se evalúa al final y su cobertura es menor. Si habría podido eliminar a una variable, el caso se informa en `pares_no_eliminados_sobrecarga.csv` y no cambia ninguna decisión.

**Lo que se conserva:** definición de SU con log₂ y sin corrección de sesgo, permutaciones y p = (1 + k)/(n + 1), comparación estricta de q, orden por SU con desempate alfabético, tolerancia absoluta 1e-12 en sus dos usos, discretizaciones y codificación de las 30 candidatas.

## 7. Familia de corrección

- **Relevancia:** Benjamini-Hochberg sobre las **31 candidatas en una misma familia**, aunque tengan distinta población. La sobrecarga no recibe una familia propia.
- **Pares:** una sola familia con todos los pares de variables relevantes, igual que en la Fase 35B.

Agregar una prueba multiplica cada q por 31/30 si no cambia su rango, y puede alterar rangos. `efecto_familia.csv` compara q con 30 y 31 usando los mismos p, para separar este efecto del de la Etapa 3.

## 8. Permutaciones, umbrales y escenarios

| Escenario | Sobrecarga | n | Permutaciones | q < | Función | Referencia |
|---|---|---:|---:|---:|---|---|
| C3 | Observadas | 239 | 50.000 | 0,05 | Principal, criterio habitual | E3 |
| C4 | Observadas | 239 | 50.000 | 0,10 | Principal exploratorio | E4 |
| S3 | Cuidadoras | 251 | 50.000 | 0,05 | Sensibilidad con 12 valores imputados | E3 |
| S4 | Cuidadoras | 251 | 50.000 | 0,10 | Sensibilidad con 12 valores imputados | E4 |

Cada escenario recalcula relevancia, pares y FCBF. La sensibilidad se informa y no modifica los escenarios principales. El programa no admite otra semilla, otras permutaciones ni otros umbrales por consola.

No se ejecutan bootstrap, remuestreos, las sensibilidades S1-S5 ni Random Forest. Los resultados de E1, E3 y E4 se leen de sus archivos y no se recalculan como escenarios.

## 9. Semillas

La clave de cada prueba es `SeedSequence(42, spawn_key=(0, 0, tipo, índice))`. `Escenario.indice()` numera en orden alfabético, y agregar la sobrecarga correría el índice de 5 candidatas (`tabaco_frecuencia`, `tiene_actividad_sexual`, `tiene_pareja`, `usa_medicamentos_presion`, `vasos_agua_dia`) y la clave de 135 de los 435 pares posibles.

Por eso, las 30 candidatas conservan su índice original y la sobrecarga recibe el **índice fijo 30**. Las claves de sus pares siguen la regla `índice_a × 1000 + índice_b`, con a antes que b en orden alfabético.

En cada escenario, SU y p de las 30 candidatas, q con la familia de 30, y SU, p y n de los pares en común deben coincidir exactamente con E3 o E4. Si no coinciden, el análisis se detiene sin escribir archivos.

## 10. Problemas de imputación detectados

Se documentan aquí y no se corrigen: **no se modifica ningún registro**.

### 10.1 Detectables con los datos actuales

Estos hechos se comprueban con el conjunto sucio, el limpio y el diccionario de limpieza.

- **`trabaja_actualmente`:** 22 respuestas vacías, sin ninguna respuesta en la sección Trabajo, se imputaron como True por moda. No tienen marca de imputación porque están bajo el 5 %, y no tienen valor en las preguntas laborales, de modo que quedan fuera de las 287.
- **`doble_carga`:** el cálculo es correcto y coincide siempre con `trabaja_actualmente` y `cuida_otras_personas` del conjunto limpio. Pero **10 registros con `doble_carga` = 1 dependen de `trabaja_actualmente` imputada**, y con los datos actuales no se puede saber cuáles son incorrectos.
- **`cuida_otras_personas`:** **21 respuestas vacías, sin ninguna pregunta dependiente respondida, se imputaron como «No»** por moda, sin marca. Esas personas tienen `cantidad_personas_cuida` = 0 y `doble_carga` = 0, por lo que ese 0 no es necesariamente una respuesta. Otras 4 se dedujeron como «Sí» porque respondieron preguntas que solo ve quien cuida; una deducción lógica no es una imputación.
- **`sobrecarga_fisica_emocional`:** 12 cuidadoras sin respuesta válida recibieron la mediana 3, sin marca. Quedan fuera del análisis principal y solo entran en la sensibilidad con 251.
- **`cantidad_personas_cuida`:** 7 valores imputados con la mediana 1, sin marca. No se pueden excluir sin cambiar la candidata general.
- **Preguntas laborales:** de las 287 personas de la Etapa 2, 271 tienen `lugar_trabajo_comprensivo` observada, 277 tienen `estres_entorno_laboral` observada y **263 tienen ambas**. Las restantes tienen algún valor imputado con la mediana 3. Entre las 130, 122 tienen ambas observadas. Las 287 no son todas «respuestas reales», aunque así lo describen el protocolo y el código originales. Las 287 se mantienen para reproducir E3 y E4.

### 10.2 Conocidos solo por la versión verdadera del simulador

Estos hechos se obtuvieron en diagnósticos separados. **La versión verdadera no se usa para definir poblaciones, corregir registros ni decidir nada**, y el programa no la lee. En datos reales esta información no existiría.

- De los 10 registros con `doble_carga` = 1 dependientes de `trabaja_actualmente` imputada, 5 no trabajan (id 15, 47, 153, 270 y 546).
- De las 22 imputaciones de `trabaja_actualmente`, 12 son incorrectas.
- De las 21 imputaciones de `cuida_otras_personas`, 14 corresponden a personas que cuidan. Su efecto sobre `doble_carga`: 4 valores 0 deberían ser 1.
- En total, `doble_carga` difiere en 9 de 529 filas: 5 valores 1 y 4 valores 0.

### 10.3 Consecuencias para la Etapa 3

- Las 21 personas imputadas como «No» no tienen respuesta de sobrecarga, de modo que **no entran ni en las 239 ni en las 251**. No alteran la definición de la población.
- La Etapa 3 describe a **quienes se identifican como cuidadoras y respondieron**, no a todas las que cuidan.
- Ninguna de las 239 depende de un valor imputado de sobrecarga ni de `cuida_otras_personas`: 236 respondieron que cuidan y 3 se dedujeron.
- 10 de las 239 tienen `trabaja_actualmente` imputada. Esto no define su pertenencia a la población, pero sí su `doble_carga`. Ninguna de las 130 la tiene imputada.

## 11. Limitaciones de interpretación

- Una SU con 239 o 130 personas no se compara directamente con una SU con 529.
- SU trata la escala de 1 a 5 como nominal e ignora su orden. La fuerza de la relación ordinal se describe aparte y no decide.
- En las 130, el nivel 1 de sobrecarga tiene solo 1 persona; esa comparación tiene poca información.
- Entre cuidadoras, `doble_carga` es idéntica a `trabaja_actualmente`. La comparación con la sobrecarga en esa población mide en la práctica la condición laboral.
- La pregunta de sobrecarga menciona «su trabajo» y se muestra también a cuidadoras que no trabajan: 99 de las 239. Es un problema de validez para consultar a la profesora.
- FCBF selecciona por asociación marginal con la severidad y no ajusta por los controles.
- Seleccionada no significa causal, eliminada no significa irrelevante, y los datos son sintéticos.

## 12. Separación e integridad

- Salidas solo en `analisis/complementario_cuidados/`, con lista cerrada y sin sobrescribir.
- No se modifica ningún archivo de `analisis/preprocesamiento/` existente, ni `analisis/seleccionar_fase35b.py`, ni `analisis/complementario_fase35b.py`.
- El umbral se cambia solo en memoria y se restaura siempre.
- No se genera dataset, caché ni figuras.
- Todo se calcula y comprueba antes de escribir: si algo falla, no queda ningún archivo.

## 13. Condiciones para ejecutar

La ejecución requiere autorización expresa de la usuaria y el indicador `--autorizado-por-usuaria`. Se detiene si ocurre cualquiera de estas situaciones:

1. Falla alguna prueba de `test_entropia.py`, `test_complementario_35b.py` o `test_complementario_cuidados.py`.
2. HEAD no es el commit original, hay cambios en archivos versionados o difieren los hashes del respaldo.
3. Cambian las candidatas, los controles o algún tamaño de control.
4. Una respuesta observada de sobrecarga difiere entre el conjunto sucio y el limpio, o un participante repetido discrepa.
5. Las 30 candidatas no reproducen E3 o E4.
6. Dos corridas del último escenario no coinciden exactamente.
7. Cambia cualquier archivo vigilado: datasets, resultados, caché, protocolos o código anterior.

`--verificar` ejecuta pruebas y comprueba estado, candidatas y tamaños, sin calcular ninguna SU con los datos reales.

Este código no queda en un commit mientras la usuaria no lo apruebe. Si se hiciera un commit antes de ejecutar, la condición 2 detendría el programa y habría que revisarla expresamente. El registro guarda el commit original y el SHA-256 del programa, de este protocolo y de sus pruebas.

## 14. Salidas previstas

| Archivo | Contenido |
|---|---|
| `poblaciones_cuidados.csv` | Tamaños y dependencia de imputaciones |
| `su_objetivo.csv` | SU, p, q con 31 y con 30, relevancia, por escenario |
| `su_pares.csv` | Pares evaluados, con n, SU, p y q |
| `decisiones_fcbf.csv` | Decisión de cada candidata, variantes adaptada y estándar |
| `pares_no_eliminados_cobertura.csv` | Pares laboral y no laboral que la regla original conserva |
| `pares_no_eliminados_sobrecarga.csv` | Variables que la sobrecarga no puede eliminar |
| `comparacion_resultados.csv` | E1, E3 y E4 guardados, junto con C3, C4, S3 y S4 |
| `efecto_familia.csv` | Cambio de q y de relevancia al pasar de 30 a 31 pruebas |
| `resumen_escenarios.csv` | Resumen por escenario |
| `relacion_cuidados.csv` | Relación entre las tres variables, con la fila de referencia rotulada |
| `sobrecarga_por_nivel.csv` | Severidad y MRS por nivel, solo en la población |
| `informe_cuidados.md` y `log_cuidados.txt` | Informe y registro de la ejecución |

## 15. Decisiones pendientes de la profesora

1. Si la salida de la sobrecarga en la reunión del 27-10 fue decisión suya.
2. Si acepta analizar la sobrecarga solo entre cuidadoras.
3. Si la pregunta debe mostrarse a quienes no trabajan o conviene reformularla.
4. Si `doble_carga` se mantiene como variable propia aunque sea calculada.
5. Si `cuida_otras_personas` y `trabaja_actualmente` vacías deben quedar como desconocidas en vez de imputarse por moda.
6. Si acepta q < 0,10 como criterio exploratorio.
