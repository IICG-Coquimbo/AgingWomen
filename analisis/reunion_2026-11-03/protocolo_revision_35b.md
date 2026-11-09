# Revisión de la Fase 35B según la reunión del 03-11-2026

*Registrado el 03-11-2026, antes de calcular cualquier resultado de esta revisión y después de conocer las ejecuciones anteriores (5.000 y 50.000 permutaciones). El SHA-256 de este archivo queda en el registro de la ejecución.*

## 1. Carácter

Esta revisión es **exploratoria e informativa**. Los resultados entrópicos **no eliminan variables de la Fase 36**. No se sobrescriben los resultados ni los protocolos anteriores (`protocolo_fase35b.md`, `protocolo_complementario_35b.md`, `protocolo_cuidados_35b.md`). Tampoco se regeneran conjuntos de datos, se hace commit o push, se ejecuta Random Forest ni se avanza a la Fase 36.

**Límite de la preespecificación:** la lista de variables y el umbral se fijaron conociendo resultados anteriores de casi todas estas variables, de modo que nada de esta revisión es confirmatorio.

## 2. Medida: entropía de Shannon

La profesora recomendó explícitamente la **entropía de Shannon**. La implementación existente (`preprocesamiento/entropia.py`) ya la usa, por lo que **no se modifica**. Ese archivo está congelado por hash en el commit `745d689`. El nombre queda explícito en este protocolo, en `revision_35b_reunion_1103.py` y en el informe.

Con frecuencias observadas p, logaritmo en **base 2** (resultado en bits) y 0·log₂0 = 0:

| Medida | Fórmula |
|---|---|
| Entropía de Shannon | H(X) = −Σₓ p(x) log₂ p(x) |
| Entropía conjunta | H(X,Y) = −Σₓ Σᵧ p(x,y) log₂ p(x,y) |
| Información mutua | I(X;Y) = H(X) + H(Y) − H(X,Y) |
| Symmetrical Uncertainty | SU(X,Y) = 2·I(X;Y) / [H(X) + H(Y)], acotada a [0, 1] |

No se aplica corrección de sesgo. `shannon_componentes.csv` informa H(X), H(severidad), H(X,severidad), I y SU de las 34 variables.

**Variables constantes.** Si H(X) = 0 o H(Y) = 0, entonces SU = 0 y p = 1. Por ejemplo, `trabaja_actualmente` es constante entre las 287 y entre las 130. Si X es constante, I = 0 y no hay variación que evaluar.

**Numéricas y categóricas.** SU usa categorías sin orden:

| Tipo | Variables | Tratamiento para SU |
|---|---|---|
| Continua | `edad` | Tramos fijos 36–39, 40–44, 45–49, 50–54, 55–59, 60–65 |
| Continua | `imc` | Categorías OMS: < 18,5; 18,5–24,9; 25–29,9; 30–34,9; 35–39,9; ≥ 40 |
| Discreta amplia | `horas_sedentarismo` | Cuartiles 5, 6 y 8, tramos (a, b] |
| Ordinal, binaria, nominal | Las demás | Sus categorías tal como están; SU ignora el orden |

La discretización es solo para SU. Spearman usa los valores originales.

**Faltantes y «no aplica».** Nunca entran como categoría:

- **`lugar_trabajo_comprensivo`, `estres_entorno_laboral`:** solo las 287. El 0 de quienes no trabajan queda fuera, igual que los 22 con mediana imputada y sin ninguna respuesta laboral.
- **`sobrecarga_fisica_emocional`:** solo las 239 observadas. Queda vacía para quienes no cuidan y para las 12 cuidadoras sin respuesta válida.
- **Imputaciones de la Fase 34B:** se conservan como en los análisis anteriores, sin modificar ningún registro. Dentro de las 287, 271 tienen `lugar_trabajo_comprensivo` observada, 277 `estres_entorno_laboral` y 263 ambas.
- **`imc`:** 262 de 529 valores están imputados y caen en 25–29,9. La familia usa las 529, como los análisis anteriores; la versión con n = 267 observadas se informa aparte.
- **Ceros con significado real:** en `frecuencia_aerobico`, `frecuencia_bajo_impacto` y `frecuencia_fuerza`, 0 = no lo realiza. En `cantidad_personas_cuida`, 0 = no cuida, y 21 de esos ceros provienen de `cuida_otras_personas` imputada como «No».

## 3. Variables y poblaciones

**34 variables:** las 30 candidatas actualizadas (las 30 anteriores, sin `doble_carga` y con `sobrecarga_fisica_emocional`) y las cuatro antiguas de control. `prevision` queda excluida.

| Población | n | Variables | Número |
|---|---:|---|---:|
| General | 529 | Las demás, incluidas `edad`, `imc`, `usa_medicamentos_diabetes` y `trabaja_actualmente` | 31 |
| Laboral | 287 | `lugar_trabajo_comprensivo`, `estres_entorno_laboral` | 2 |
| Cuidadoras con sobrecarga observada | 239 | `sobrecarga_fisica_emocional` | 1 |

Cada medición entre dos variables usa la cobertura común: 287 o 130 si participa una laboral con la sobrecarga, 239 con la sobrecarga. Si cambia un tamaño o la lista, el programa se detiene.

## 4. Primera ejecución: 10.000 permutaciones

1. Se permuta `severo_mrs` entre las personas de la población de cada variable, 10.000 veces.
2. **p = (1 + k) / 10.001**, donde k = número de permutaciones con SU ≥ SU observada − 1e-12.
3. **Benjamini-Hochberg sobre una única familia de 34 pruebas**, recalculada. No se reutiliza ningún q anterior.
4. **Relevancia exploratoria: q < 0,10**, comparación estricta. q < 0,05 se informa como referencia y no decide nada.
5. Se informan las 34 variables, incluidas las que no superen el criterio.

**Semillas.** Clave `SeedSequence(42, spawn_key=(1103, 0, tipo, índice))`, con índice alfabético entre las 34. Es una corriente **nueva, fijada antes de calcular**. Reutilizar la de las ejecuciones anteriores habría repetido sus primeras permutaciones y no aportaría una estimación independiente. SU no depende de la semilla, y por eso debe coincidir con los valores guardados.

**Comprobaciones antes de escribir:** dos corridas idénticas; SU igual a la guardada en las 29 variables comunes, la sobrecarga y las 4 antiguas de control; SU igual a una implementación independiente con tolerancia 1e-10.

## 5. FCBF informativo y redundancia

Se reutilizan las reglas validadas, sin cambios: etapas 1 y 2 de `fcbf.seleccionar` y Etapa 3 de cuidados.

- **Etapa 1:** las 31 generales relevantes, ahora con las cuatro antiguas de control compitiendo.
- **Etapa 2:** laborales relevantes, con las 287. Una laboral nunca elimina a una general.
- **Etapa 3:** sobrecarga relevante, en su población común. Nunca elimina a otra variable.
- **Pares:** todos los pares de relevantes, con 10.000 permutaciones, una sola familia BH y q < 0,10 para la variante adaptada. La variante estándar no exige q del par.

Además, se informa la SU de **las 561 parejas** de las 34 variables en su cobertura común, sin permutaciones, solo para describir redundancia.

«Seleccionada» y «redundante» son rótulos descriptivos: **ninguna variable sale de la Fase 36 por este resultado**.

## 6. Dirección de la asociación

SU no indica dirección. Se complementa así, en la población de cada variable y sin afectar a q:

**Orientación de las escalas.** Se comprueba contra `src/apps/encuestas/models.py` antes de interpretar signos. **`evacuacion_intestinal` es inversa a la frecuencia:** 1 = más de una vez al día y 4 = 3 o más días entre evacuaciones.

**Medidas por variable:**

- Spearman de cada variable con `mrs_total` (ρ) y con `severo_mrs` (no aplicable a `quien_prepara_comidas`, nominal).
- IC 95 % de ρ con `mrs_total`: bootstrap percentil de 2.000 remuestreos, pareado, en la población.
- q de Spearman: BH sobre las 33 no nominales, a partir del p asintótico.
- Kruskal-Wallis con su p y ε² = H/(n−1).
- Por categoría: n, MRS medio con IC 95 % t, mediana y cuartiles, y % de severas con IC 95 % de Wilson.
- Categoría más baja frente a la más alta entre las que tengan n ≥ 10: diferencia de MRS medio (IC de Welch) y de % de severas (IC de Newcombe). No aplica a la nominal.

**Regla de dirección, fijada de antemano:**

| Dirección | Condición |
|---|---|
| Positiva | IC 95 % de ρ sobre 0 y ρ con `severo_mrs` > 0 |
| Negativa | IC 95 % de ρ bajo 0 y ρ con `severo_mrs` < 0 |
| Mixta | IC excluye 0 pero el signo con `severo_mrs` es opuesto; o IC incluye 0 y Kruskal-Wallis p < 0,05; o nominal con Kruskal-Wallis p < 0,05 |
| Poco clara | Las demás |

**Clasificación descriptiva, fijada de antemano.** El factor se lee según el significado de un valor mayor en cada escala:

| Clase | Condición |
|---|---|
| Posible factor de riesgo / protección | q de SU < 0,10 y dirección positiva / negativa |
| Indicio de riesgo / protección (solo orden) | q de SU ≥ 0,10, q de Spearman < 0,10 y dirección positiva / negativa |
| Asociación sin dirección clara | q de SU < 0,10 y dirección mixta o poco clara |
| Sin respaldo tras la corrección | Las demás |

**Ninguna asociación se interpreta como causal.** Los datos son sintéticos y reflejan lo programado en el simulador. Algunas variables pueden ser consecuencia o parte del cuadro de síntomas, como la distensión abdominal o el uso de medicamentos.

## 7. Regla para recomendar 50.000 permutaciones

**Fijada antes de ver resultados.** El azar de las permutaciones es independiente entre variables, porque cada una tiene su propia corriente. Dado el valor p exacto, k sigue una binomial.

**Cuantificación.**

1. Para cada variable, se representa su p exacto desconocido con Beta(k + 0,5; N − k + 0,5), la posterior de Jeffreys.
2. Se extraen 20.000 vectores de 34 valores p, con la semilla `(1103, 0, 4, 0)`.
3. Se aplica BH a cada vector, lo que propaga también los cambios de rango.
4. Para cada variable se informa el error estándar de p, su intervalo de Monte Carlo al 95 %, los percentiles 2,5 y 97,5 de q, y la probabilidad de q < 0,10.

**Cercanía al umbral.** Una variable está **cercana** si el intervalo de Monte Carlo al 95 % de su q contiene 0,10. Es decir, q₂,₅ ≤ 0,10 ≤ q₉₇,₅.

**Recomendación.**

- **Se recomienda 50.000** si al menos una variable está cercana, porque la incertidumbre Monte Carlo puede modificar su clasificación.
- **También se puede recomendar** si hay inestabilidad numérica comprobable: dos corridas distintas o SU que no coincide con la implementación independiente.
- **En otro caso, no se recomienda.** No se recomiendan más permutaciones porque una variable esperada no resultó relevante.

La proyección de la precisión con 50.000 se informa como referencia y no interviene en la regla. La cercanía a 0,05 tampoco interviene.

## 8. Sensibilidad, fuera de la familia

No cambian ningún resultado principal:

- **`imc` con n = 267 observadas** y **`sobrecarga_fisica_emocional` con n = 251:** SU, p con 10.000 permutaciones y el q que tendría al reemplazar su p en la familia.
- **`q_familia_30`:** q de las 30 candidatas sin las cuatro antiguas de control, con los mismos p. Separa el efecto de haberlas agregado a la familia.

## 9. Comparación con resultados anteriores

Se leen de sus archivos, sin recalcular:

| Referencia | Permutaciones | Familia |
|---|---:|---:|
| E1 (oficial) | 5.000 | 30 |
| E3 / E4 | 50.000 | 30, con `doble_carga` y sin sobrecarga |
| C3 / C4 | 50.000 | 31, con `doble_carga` y con sobrecarga |

Las SU de las cuatro antiguas de control se comparan con las descriptivas guardadas; esas variables no tenían q.

## 10. Segunda ejecución de 50.000: no autorizada

**No se ejecuta sin autorización expresa de la usuaria.** El programa solo admite 10.000. Si se autoriza, se mantendrán las mismas 34 variables, reglas, q < 0,10 y claves de semilla. Como `prueba_permutacion` baraja por lotes de 1.000 y 10.000 y 50.000 son múltiplos, **las primeras 10.000 permutaciones de 50.000 serán exactamente estas**, lo que se comprueba en las pruebas. Se recalcularán p y q y se compararán ambas ejecuciones.

## 11. Separación e integridad

- Salidas solo en `analisis/reunion_2026-11-03/permutaciones_10000/`, con lista cerrada y sin sobrescribir. Todo se calcula y comprueba antes de escribir.
- Se vigilan por hash los datasets, los resultados, los protocolos y el código anteriores, incluidos los de Random Forest.

**Condiciones para ejecutar.** Requiere `--autorizado-por-usuaria`, y se detiene si:

1. Falla alguna prueba de `test_entropia`, `test_complementario_35b`, `test_complementario_cuidados` o `test_revision_35b`.
2. HEAD no es `745d689`, hay cambios en archivos versionados o difieren los hashes del respaldo.
3. Cambian las 34 variables o un tamaño de población.
4. No se cumple alguna comprobación de la sección 4.
5. Cambia algún archivo vigilado.

## 12. Limitaciones

- SU trata las escalas como nominales; por eso Spearman puede detectar tendencias que SU no detecta, y al revés.
- Una SU con 239 o 287 personas no se compara directamente con una con 529.
- Agregar a la familia variables con p muy bajo o muy alto cambia los q de las demás.
- Los IC y los p de Spearman y Kruskal-Wallis son descriptivos, y sus muchas comparaciones por categoría no están corregidas.
- La pregunta de sobrecarga menciona «su trabajo» y se muestra también a cuidadoras que no trabajan.
- `q < 0,10` tolera que, en promedio, cerca de 1 de cada 10 declaradas relevantes sea un falso positivo.
