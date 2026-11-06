# Complemento de la Fase 35B: informe consolidado de la estabilidad con las 33 variables finales

*Redactado el 06-11-2026 a partir de los resultados de la corrida del 05-11-2026. No se volvió a ejecutar ningún remuestreo ni se recalculó ningún resultado. Todas las cifras se leyeron de los archivos ya guardados en esta carpeta.*

**Fuentes usadas:**
- `remuestreos/progreso.log` y `remuestreos/ejecucion.json`;
- `remuestreos/cache/rem_0000.json` a `rem_0499.json`;
- `resultados/*.csv` y `resultados/resultado_global.json`;
- `comparacion/*.csv`;
- `configuracion/candidatas_y_exclusiones.csv`;
- `pruebas/*.csv`;
- `integridad/*.json`;
- `protocolo/01_revision_y_configuracion.md`;
- `fase36/configuracion_fase36.py`, solo para la composición de las matrices.

---

## Resumen

- Los **500 remuestreos terminaron** el 05-11 a las 22:42. Las **19 pruebas** se superaron y los **23 controles negativos** detectaron su error.
- La **estabilidad de la selección es baja**:
  - Nogueira = **0,129** (IC 95 %: 0,118–0,139) en la variante adaptada y 0,128 en la estándar.
  - **Ninguna variable** se seleccionó en el 50 % o más de los remuestreos.
- Las cuatro variables de la selección definitiva son las **más frecuentes** de la variante adaptada: IMC 39,0 %, fuerza 35,2 %, trabaja 32,6 % y lugar comprensivo 31,4 %. Aun así, ningún remuestreo reprodujo exactamente esa selección.
- La **relevancia es mucho más estable que la selección**. La señal asociada al ejercicio aparece casi siempre (98,6 %), pero FCBF elige una representante distinta según la muestra.
- El resultado **no invalida** las Fases 36 y 37. Sus matrices no se construyeron a partir de la selección de FCBF. Lo que sí limita es la interpretación: las cuatro variables no deben presentarse como determinantes estables.
- Los **5.977 archivos protegidos siguen intactos**: se volvió a comprobar hoy, sin cambios.

---

## 1. Ejecución, pruebas y controles

### 1.1 Remuestreos

| Control | Resultado | Fuente |
|---|---|---|
| Remuestreos terminados | **500 de 500** (`rem 000` a `rem 499`) | `progreso.log` |
| Archivos de remuestreo | 500, de `rem_0000.json` a `rem_0499.json`, sin huecos ni archivos vacíos | `remuestreos/cache/` |
| Archivos legibles | Los 500 JSON se abrieron el 06-11 y todos son válidos y tienen la misma estructura | Revisión del 06-11 |
| Inicio y fin | 21:40:23 a 22:42:00 (3.697 s, 61,6 min; unos 7,4 s por remuestreo) | `ejecucion.json` |
| Parámetros | 5.000 permutaciones por remuestreo, q < 0,10, un solo proceso, identificador de análisis 1 | `ejecucion.json` |
| Memoria libre mínima | 1.224 MB. El corte de seguridad (400 MB) no se activó | `ejecucion.json` |
| Errores en el registro | Ninguno: no hay excepciones, errores de memoria ni procesos terminados por el sistema | `progreso.log` |
| Tabla de remuestreos | `remuestreos_33.csv` con 1.000 filas (500 remuestreos × 2 variantes) | `remuestreos/` |

Los últimos archivos del resumen, las pruebas y la integridad se escribieron entre las 22:49 y las 22:51. El computador se congeló **después** de esa hora, así que el cálculo no se vio afectado.

### 1.2 Pruebas (19 de 19 superadas)

El detalle está en `02_informe_pruebas.md`. Lo esencial:
- **Variables:** exactamente las 33 candidatas. `doble_carga`, `prevision` y las variables del MRS no entran (pruebas 1–3 y 8).
- **Poblaciones:** 529 personas (281 severas y 248 no severas), 287 trabajadoras y 239 cuidadoras (prueba 4).
- **Remuestreo:** bootstrap estratificado con reemplazo. Cada muestra tiene entre 314 y 358 personas distintas, con media de 335. Son las mismas 500 muestras de la corrida antigua (pruebas 5–7).
- **Procedimiento:** completo en cada remuestreo. Los remuestreos 0, 250 y 499 se recalcularon desde cero y dieron lo mismo (prueba 9).
- **Reproducibilidad:** el remuestreo 7 da lo mismo dos veces. La función nueva coincide exactamente con la original y el código antiguo reproduce los remuestreos antiguos 0 y 1 (pruebas 14–15).
- **Integridad:** las Fases 34 a 39, Django y los 6 archivos históricos de estabilidad no cambiaron (pruebas 16–18).
- **Lectura de la selección definitiva:** coincide con el registro del 03-11 (prueba 19).

### 1.3 Controles negativos (23 de 23 detectados)

Se introdujeron errores a propósito en copias de los objetos, y las pruebas detectaron cada uno:
- candidatas extra o faltantes;
- una población alterada;
- índices fuera de rango;
- un remuestreo sin estratificar o sin reemplazo;
- 499 remuestreos en vez de 500;
- umbrales o parámetros cambiados;
- frecuencias mal contadas;
- un remuestreo guardado alterado;
- un archivo de una fase anterior o de Django modificado.

---

## 2. Qué mide el índice de Nogueira y cómo leer 0,129

**Qué mide.** El índice de Nogueira, Sechidis y Brown (2018) resume, en un solo número, cuánto se parecen entre sí las selecciones obtenidas en los 500 remuestreos. Además corrige la coincidencia que se esperaría por puro azar dado el tamaño de las selecciones.

- **1** significa que el procedimiento elige siempre exactamente las mismas variables.
- **0** significa que las selecciones coinciden lo mismo que si se eligieran variables al azar, en igual número.
- Los valores intermedios se leen de forma parecida al kappa de concordancia. Los propios autores proponen la escala de Fleiss como orientación: bajo 0,40 es baja concordancia, de 0,40 a 0,75 es intermedia a buena y sobre 0,75 es excelente. La escala es solo **orientativa**; el protocolo no fijó ningún umbral de aceptación.

**Cómo leer 0,129.** La selección coincide entre muestras **un poco más de lo que coincidiría por azar**, pero muy lejos de una selección reproducible. Dicho de otra forma: si se tomara otra muestra de 529 mujeres del mismo origen, lo más probable es que FCBF eligiera otro conjunto de variables, aunque con alguna preferencia por las mismas.

**El intervalo de confianza (0,118–0,139).** Es el rango de valores compatibles con los datos para la estabilidad del procedimiento. Tres lecturas:
1. **Es estrecho** (±0,01). La conclusión de estabilidad baja no se debe a haber hecho pocos remuestreos; con más remuestreos no cambiaría de forma apreciable.
2. **No incluye el 0.** La selección es algo mejor que el azar.
3. **Queda muy por debajo de 0,40.** La selección no alcanza ni siquiera la concordancia intermedia de la escala orientativa.

**Indicadores complementarios** (`resultado_global.json`):

| Indicador | Adaptada | Estándar |
|---|---:|---:|
| Nogueira (IC 95 %) | 0,129 (0,118–0,139) | 0,128 (0,118–0,138) |
| Jaccard promedio entre pares de remuestreos | 0,140 | 0,133 |
| Tamaño medio de la selección (DE; mínimo–máximo) | 3,65 (1,20; 1–7) | 2,65 (1,06; 1–6) |
| Tamaño de la selección definitiva | 4 | 2 |
| Jaccard medio con la selección definitiva | 0,239 | 0,183 |
| Remuestreos iguales a la selección definitiva | **0 %** | 3,6 % |
| Variables relevantes por remuestreo (media; mínimo–máximo) | 13,2 (2–21) | 13,2 (2–21) |
| Nogueira de la **relevancia** (filtro SU, antes de FCBF) | **0,337** | 0,337 |

El Jaccard mide la proporción de variables compartidas entre dos selecciones. Que dos remuestreos compartan en promedio el 14 % de sus variables confirma la lectura del índice.

---

## 3. Las 33 candidatas y sus frecuencias de selección

**Cómo leer las columnas:**
- **% relevante:** porcentaje de remuestreos en que la variable superó el filtro SU (q < 0,10).
- **% sel. adaptada** y **% sel. estándar:** porcentaje de los 500 remuestreos en que FCBF la retuvo en cada variante.
- **Sobrevive si relevante:** de los remuestreos en que fue relevante, porcentaje en que FCBF la retuvo (adaptada).
- **Eliminadora principal:** la variable que más veces la declaró redundante (adaptada).
- **Definitiva:** estado en la selección definitiva, adaptada/estándar. S = seleccionada, R = relevante pero redundante, NR = no relevante.
- **Fase 36:** dónde entra la variable en las matrices de agrupamiento.

Todas las variables quedan en la banda descriptiva «< 50 %» del protocolo 35B, en las dos variantes. Fuente: `resultados/frecuencias_seleccion.csv`, `resultados/resultados_fcbf.csv` y `configuracion/candidatas_y_exclusiones.csv`.

| N.º | Variable | Población | % relevante | % sel. adaptada | % sel. estándar | Sobrevive si relevante | Eliminadora principal | Definitiva | Fase 36 |
|---:|---|---|---:|---:|---:|---:|---|:---:|---|
| 1 | **imc** | General | 86,2 | **39,0** | 29,2 | 45,2 | frecuencia_fuerza | S / R | P1 y F1 (fuera de P2 y F2) |
| 2 | **frecuencia_fuerza** | General | 83,8 | **35,2** | 32,6 | 42,0 | dias_ejercicio_semana | S / S | Matriz global |
| 3 | **trabaja_actualmente** | General | 67,0 | **32,6** | 33,6 | 48,7 | frecuencia_fuerza | S / R | Matriz global |
| 4 | **lugar_trabajo_comprensivo** | Laboral (287) | 82,2 | **31,4** | 20,4 | 38,2 | tabaco_frecuencia | S / S | Módulo laboral |
| 5 | tabaco_frecuencia | General | 63,8 | 28,8 | 16,4 | 45,1 | frecuencia_fuerza | NR / NR | Matriz global |
| 6 | dias_ejercicio_semana | General | 91,0 | 22,0 | 19,0 | 24,2 | frecuencia_fuerza | R / R | Matriz global |
| 7 | frecuencia_bajo_impacto | General | 88,0 | 21,8 | 18,6 | 24,8 | frecuencia_fuerza | R / R | Matriz global |
| 8 | sobrecarga_fisica_emocional | Cuidadoras (239) | 65,4 | 20,4 | 11,8 | 31,2 | frecuencia_fuerza | NR / NR | Módulo de cuidados |
| 9 | quien_prepara_comidas | General | 67,4 | 17,0 | 12,6 | 25,2 | frecuencia_fuerza | NR / NR | Matriz global |
| 10 | usa_medicamentos_presion | General | 41,0 | 15,6 | 14,8 | 38,0 | frecuencia_fuerza | NR / NR | Matriz global |
| 11 | tiene_pareja | General | 29,4 | 14,2 | 12,0 | 48,3 | imc | NR / NR | Matriz global |
| 12 | estres_entorno_laboral | Laboral (287) | 67,6 | 9,8 | 9,6 | 14,5 | frecuencia_fuerza | NR / NR | Módulo laboral |
| 13 | falta_tiempo_influye | General | 47,8 | 9,4 | 5,2 | 19,7 | imc | NR / NR | Matriz global |
| 14 | pescado_semana | General | 31,8 | 9,2 | 3,4 | 28,9 | frecuencia_fuerza | NR / NR | Matriz global |
| 15 | frutas_dia | General | 22,4 | 7,6 | 2,6 | 33,9 | imc | NR / NR | Matriz global |
| 16 | distension_abdominal | General | 30,8 | 5,8 | 2,0 | 18,8 | frecuencia_fuerza | NR / NR | Matriz global |
| 17 | cantidad_personas_cuida | General | 59,6 | 5,6 | 3,8 | 9,4 | frecuencia_fuerza | NR / NR | Matriz global |
| 18 | frecuencia_aerobico | General | 49,0 | 5,2 | 4,8 | 10,6 | frecuencia_fuerza | NR / NR | Matriz global |
| 19 | alcohol_frecuencia | General | 35,4 | 5,0 | 1,6 | 14,1 | imc | NR / NR | Matriz global |
| 20 | vasos_agua_dia | General | 58,6 | 4,4 | 1,2 | 7,5 | imc | NR / NR | Matriz global |
| 21 | frecuencia_comida_fuera | General | 31,8 | 4,0 | 0,8 | 12,6 | imc | NR / NR | Matriz global |
| 22 | operada_no_mas_hijos | General | 8,0 | 3,8 | 2,8 | 47,5 | frecuencia_fuerza | NR / NR | Matriz global |
| 23 | horas_sedentarismo | General | 17,2 | 3,2 | 0,6 | 18,6 | frecuencia_fuerza | NR / NR | Matriz global |
| 24 | legumbres_semana | General | 17,0 | 3,2 | 1,2 | 18,8 | frecuencia_fuerza | NR / NR | Matriz global |
| 25 | tiene_actividad_sexual | General | 7,6 | 3,2 | 2,4 | 42,1 | quien_prepara_comidas | NR / NR | Matriz global |
| 26 | platos_verduras_dia | General | 12,8 | 1,8 | 0,2 | 14,1 | frecuencia_fuerza | NR / NR | Matriz global |
| 27 | lacteos_dia | General | 6,2 | 1,6 | 1,0 | 25,8 | quien_prepara_comidas | NR / NR | Matriz global |
| 28 | evacuacion_intestinal | General | 8,0 | 1,2 | 0,0 | 15,0 | frecuencia_bajo_impacto | NR / NR | Matriz global |
| 29 | jugos_gaseosas_dia | General | 12,8 | 1,0 | 0,6 | 7,8 | frecuencia_fuerza | NR / NR | Matriz global |
| 30 | panes_dia | General | 7,4 | 1,0 | 0,2 | 13,5 | imc | NR / NR | Matriz global |
| 31 | carnes_semana | General | 8,2 | 0,8 | 0,2 | 9,8 | frecuencia_fuerza | NR / NR | Matriz global |
| 32 | golosinas_semana | General | 4,2 | 0,4 | 0,0 | 9,5 | imc | NR / NR | Matriz global |
| 33 | edad | General | 9,4 | 0,2 | 0,0 | 2,1 | frecuencia_fuerza | NR / NR | Matriz global |

**Excluidas del filtro desde el principio**, por decisiones previas y no por este análisis:
- `doble_carga`, porque se deriva de trabajo y cuidado;
- `prevision`, pendiente según el protocolo 35B;
- `usa_medicamentos_diabetes`, por dominancia superior al 85 %.

**Observaciones:**
- **En la variante adaptada todas las variables se seleccionaron al menos una vez.** En la estándar nunca se seleccionaron `edad`, `evacuacion_intestinal` ni `golosinas_semana`.
- **Dos variables no relevantes en la definitiva aparecen con frecuencia:** `tabaco_frecuencia` (28,8 %) y `sobrecarga_fisica_emocional` (20,4 %). Sus q en la definitiva fueron 0,188, no muy lejos del corte de 0,10. Una parte de su frecuencia se explica por la facilidad de significancia del bootstrap (sección 10, limitación 1).
- **La frecuencia de las variables laborales y de cuidados no depende del tamaño de su subpoblación** en cada muestra:
  - lugar comprensivo y número de trabajadoras: r = −0,08;
  - estrés laboral y número de trabajadoras: r = −0,04;
  - sobrecarga y número de cuidadoras: r = −0,11.

---

## 4. Variante estándar frente a variante adaptada

**Diferencia de procedimiento.** Las dos variantes parten de las mismas variables relevantes. Difieren en cómo se declara la redundancia entre dos variables:
- La **estándar** aplica el criterio clásico de FCBF: una variable es redundante si su SU con otra ya elegida es mayor o igual que su SU con el objetivo.
- La **adaptada** exige además que la asociación del par sea significativa (q del par < 0,10). Eso evita eliminar una variable por una redundancia que podría ser ruido.

**Resultados:**

| Aspecto | Adaptada | Estándar |
|---|---|---|
| Nogueira | 0,129 | 0,128 |
| Tamaño medio | 3,65 | 2,65 |
| Selección definitiva | IMC, fuerza, trabaja, lugar comprensivo | Fuerza, lugar comprensivo |
| Variable más frecuente | IMC (39,0 %) | Trabaja (33,6 %) |
| Iguales a la definitiva | 0 % | 3,6 % |
| Al menos una del bloque de ejercicio seleccionada | 78,8 % | 70,0 % |
| IMC o trabaja seleccionada | 56,4 % | 51,0 % |
| Lugar comprensivo o estrés laboral seleccionada | 41,2 % | 30,0 % |

**Lectura.**
1. **Las dos variantes son igual de inestables.** Sus índices son prácticamente idénticos y los intervalos se superponen casi por completo. La exigencia de significancia en los pares no corrige la inestabilidad ni la empeora.
2. **La estándar elimina más.** Retiene en promedio una variable menos y casi nunca más de cinco. En la definitiva declara redundantes a IMC y a trabaja; en los remuestreos, en cambio, trabaja es su variable más frecuente.
3. **El orden de las cuatro variables cambia entre variantes.** No hay una «ganadora» común: en la adaptada lidera el IMC y en la estándar lidera trabaja, seguida de fuerza.
4. **La relevancia es idéntica en las dos variantes** (Nogueira 0,337), porque el filtro SU es común. Todas las diferencias vienen de la etapa de redundancia.

La variante **adaptada** sigue siendo la principal, como fijó el protocolo 35B. La estándar se informa como sensibilidad y no altera ninguna conclusión.

---

## 5. Las cuatro variables de la selección definitiva

| Variable | % relevante | % seleccionada (adaptada) | Sobrevive si relevante | q en la definitiva (50.000 perm.) | SU en la definitiva | Principales eliminadoras (adaptada) |
|---|---:|---:|---:|---:|---:|---|
| IMC | 86,2 | 39,0 | 45,2 % | 0,081 | 0,0176 | fuerza (76), días de ejercicio (53), quién prepara (25) |
| Frecuencia de fuerza | 83,8 | 35,2 | 42,0 % | 0,089 | 0,0193 | días de ejercicio (67), bajo impacto (58), IMC (44) |
| Trabaja actualmente | 67,0 | 32,6 | 48,7 % | 0,089 | 0,0083 | fuerza (81), tabaco (23), falta de tiempo (16) |
| Lugar de trabajo comprensivo | 82,2 | 31,4 | 38,2 % | 0,089 | 0,0205 | tabaco (47), IMC (46), fuerza (42) |

**Lo que se puede sostener:**
- **Son las cuatro más frecuentes** de la variante adaptada. La selección definitiva no es un resultado extraño dentro de la distribución bootstrap: es su moda por variable.
- **Su relevancia es bastante consistente.** IMC, fuerza y lugar comprensivo superan el filtro en el 82 % al 86 % de las muestras. Trabaja lo hace en el 67 %.
- **El 56,4 % de los remuestreos retiene IMC o trabaja.** Solo en el 15,2 % retiene las dos a la vez. FCBF suele tratarlas como intercambiables, y la eliminadora principal de trabaja es la fuerza.

**Lo que no se puede sostener:**
- **Que sean estables.** Cada una queda fuera de la selección en más del 60 % de las muestras. Cuando son relevantes, sobreviven a FCBF menos de la mitad de las veces.
- **Que formen un conjunto.** Ningún remuestreo reprodujo las cuatro juntas. El Jaccard medio con la definitiva es 0,24: en promedio, una muestra comparte una de cada cuatro variables con ella.
- **Que tengan un efecto fuerte.** Sus SU son del orden de 0,01–0,02, muy pequeñas, y sus q definitivos están entre 0,081 y 0,089, cerca del corte de 0,10.

**Caso del lugar de trabajo comprensivo.** Se mide solo en las 287 trabajadoras y no compite con las generales en la etapa laboral. Lo eliminan sobre todo tabaco, IMC y fuerza, que son variables generales retenidas antes. Su frecuencia no depende del número de trabajadoras de cada muestra (r = −0,08).

**Dependencia de personas concretas** (`dependencia_de_participantes.csv`, solo variante adaptada y descriptivo):
- Para las cuatro variables, el número de personas cuya presencia o ausencia cambia la frecuencia de selección de forma destacada (|z| > 3) va de 2 a 3. Por azar se esperarían 1,4.
- La mayor diferencia en la frecuencia según una persona esté o no en la muestra es de 15 a 17 puntos.

No hay evidencia de que una sola participante sostenga por sí misma la selección de ninguna de las cuatro.

---

## 6. Por qué ninguna variable llegó al 50 %

No es un fallo de cálculo: las pruebas 9, 11 y 12 lo descartan. Cuatro mecanismos, que se refuerzan entre sí, explican el resultado.

1. **La señal es débil y está cerca del umbral.**
   - Las asociaciones con la severidad del MRS son pequeñas: SU máxima de 0,02 en la definitiva.
   - Las cuatro seleccionadas tienen q entre 0,081 y 0,089, justo bajo el corte de 0,10.
   - En una muestra nueva basta un cambio pequeño para que crucen el umbral en uno u otro sentido.
   - Por eso, incluso la variable más relevante, `dias_ejercicio_semana`, no supera el filtro en el 9 % de las muestras.
2. **Hay variables muy relacionadas que compiten por el mismo lugar.**
   - FCBF retiene **una representante** por grupo de variables redundantes.
   - Las tres variables de ejercicio (fuerza, días y bajo impacto) son relevantes, alguna de ellas, en el 98,6 % de los remuestreos.
   - FCBF retiene alguna en el 78,8 % y dos o más solo en el 0,2 %.
   - Qué variable gana depende de diferencias mínimas de SU que cambian de una muestra a otra. Así, la señal del ejercicio se reparte entre tres variables y ninguna se acerca al 50 %.
   - Lo mismo ocurre, en menor grado, entre IMC y trabaja (56,4 % al menos una; 15,2 % ambas) y entre las dos laborales (41,2 % al menos una; nunca las dos).
3. **El bootstrap aumenta la competencia.**
   - Las personas repetidas en cada muestra facilitan la significancia: en promedio resultan relevantes 13,2 variables, frente a 6 en la muestra original.
   - Más variables relevantes significa más candidatas compitiendo por el primer lugar y más ocasiones de que una variable quede desplazada.
   - Esto reduce la frecuencia de cada variable y explica por qué `tabaco_frecuencia` o `sobrecarga_fisica_emocional` aparecen tanto sin ser relevantes en la definitiva.
4. **FCBF es una búsqueda en orden, que amplifica las diferencias pequeñas.**
   - La variable con mayor SU en cada muestra elimina a las que se le parecen.
   - Si el primer lugar cambia, cambia en cadena todo lo que viene después. Por eso `frecuencia_fuerza` es la eliminadora principal de 20 de las 33 variables en la variante adaptada.

**Conclusión de esta sección.** La inestabilidad está sobre todo en **cuál** variable representa a cada grupo, no en **si** hay señal. La relevancia (Nogueira 0,337) es más de dos veces más estable que la selección (0,129). Aun así, la propia relevancia es solo moderadamente reproducible: solo el 34,4 % de las muestras reproduce las seis relevantes definitivas a la vez.

---

## 7. Comparación con la corrida anterior (02-11-2026)

### 7.1 Qué cambió entre las dos corridas

| Atributo | Corrida anterior | Complemento de 33 |
|---|---|---|
| Candidatas | 30, con `doble_carga`. Edad, IMC, trabaja y diabetes estaban fuera como control y la sobrecarga no existía | 33, sin `doble_carga` ni diabetes. Edad, IMC y trabaja compiten y se incluye la sobrecarga |
| Familia BH | 30 pruebas | 33 pruebas |
| Umbral de relevancia y de pares | q < 0,05 | q < 0,10 |
| Etapas FCBF | General y laboral | General, laboral y cuidadoras |
| Remuestreo | Bootstrap estratificado con reemplazo, 500 muestras | **Las mismas 500 muestras** (misma semilla) |
| Permutaciones por remuestreo | 5.000 | 5.000 |
| Procesos | 11 | 1 |

### 7.2 Qué comparación es válida

Cambiaron a la vez **el universo de candidatas, el umbral y una etapa**. Por eso ninguna diferencia se puede atribuir a una sola causa, y la comparación es **solo descriptiva**, como fijó el protocolo antes de ver los resultados (§5).

A favor de la validez, la comparación es **pareada**: el remuestreo i contiene exactamente las mismas personas en las dos corridas. La prueba 7 lo verifica, porque el n laboral coincide en los 500 casos. Así, las diferencias no se deben a haber sacado muestras distintas.

Sí es válido:
- comparar los índices globales como descripción de dos configuraciones distintas;
- comparar, variable por variable, las **29 variables comunes**;
- medir cuánto coinciden las dos corridas en cada muestra.

No es válido:
- atribuir la diferencia de Nogueira a una causa concreta, sea el umbral, las nuevas candidatas o la Etapa 3;
- comparar las variables que solo existen en una de las corridas: IMC, trabaja, edad y sobrecarga solo en la nueva, y `doble_carga` solo en la antigua.

### 7.3 Resultados

| Indicador | Anterior | Complemento |
|---|---:|---:|
| Nogueira (adaptada) | 0,121 | 0,129 |
| Nogueira (estándar) | 0,126 | 0,128 |
| Jaccard promedio (adaptada) | 0,133 | 0,140 |
| Tamaño medio (adaptada) | 3,14 | 3,65 |
| Tamaño medio (estándar) | 2,30 | 2,65 |
| Jaccard pareado entre corridas, misma muestra (adaptada) | — | 0,486 |
| Jaccard pareado entre corridas, misma muestra (estándar) | — | 0,599 |

**Lectura:**
- **Las dos corridas llegan a la misma conclusión: estabilidad baja.** Con la configuración definitiva el índice no mejora de forma apreciable: los intervalos se superponen.
- **Las selecciones son más grandes en el complemento** (3,65 frente a 3,14). Es coherente con un umbral más permisivo y con tres variables nuevas que compiten.
- **Sobre la misma muestra, las dos corridas comparten en promedio la mitad de sus variables** (adaptada 0,49; estándar 0,60). El cambio de configuración sí cambió qué se selecciona en cada muestra.
- **En las 29 variables comunes las diferencias de frecuencia son pequeñas.** En la adaptada van de −6,4 puntos (`quien_prepara_comidas`) a +3,6 (`usa_medicamentos_presion`). En la estándar, de −3,8 a +3,6.
  - Fuerza: 38,6 % → 35,2 %.
  - Lugar comprensivo: 34,0 % → 31,4 %.
  - Tabaco: 28,8 % → 28,8 %.
- `doble_carga`, que ya no es candidata, aparecía en la corrida antigua en el 26,8 % de los remuestreos (adaptada).

**Consecuencia para la tesis.** Las cifras 0,121 y 0,126 y la figura `analisis/figuras/seleccion_35b/estabilidad_seleccion.png` corresponden a la lista preliminar de 30 candidatas con q < 0,05. No describen la selección definitiva y deben sustituirse por las de este informe, o presentarse como estimación preliminar.

---

## 8. Candidatas, seleccionadas y variables de las Fases 36 y 37

Son tres conjuntos distintos y no deben confundirse:

| Conjunto | Qué es | Variables | Para qué se usó |
|---|---|---|---|
| **33 candidatas** | Entrada del filtro SU y de FCBF | Las 33 de la tabla de la sección 3 | Medir la relevancia de cada variable para la severidad del MRS (MRS ≥ 16) |
| **Selección definitiva** | Salida de FCBF con 50.000 permutaciones | Adaptada: IMC, fuerza, trabaja y lugar comprensivo (4). Estándar: fuerza y lugar comprensivo (2) | **Informativa.** Según `protocolo_revision_33.md` §2, FCBF «no elimina variables» |
| **Matrices de la Fase 36 y modelos de la Fase 37** | Variables de agrupamiento, **sin el MRS** | **30 generales** en la matriz global. P1 y F1 incluyen el IMC (30 variables). P2 y F2 no lo incluyen (29). Las 3 variables de **módulo** se analizan aparte y no entran al PCA: lugar comprensivo y estrés laboral en las 287 trabajadoras, sobrecarga en las 239 cuidadoras | PCA y FAMD (37A), K-means y aglomerativo (37B), selección `P2_c12_km_k4` (37C) |

**Puntos clave:**
- **Las matrices de la Fase 36 no se construyeron a partir de la selección.** Las 30 generales entran sean o no seleccionadas por FCBF; por ejemplo, entran `edad`, con 0,2 %, y `golosinas_semana`, con 0,4 %.
- **El modelo elegido en la 37C (`P2_c12_km_k4`, PCA sin IMC, 12 componentes, K-means con k = 4) contiene solo dos de las cuatro seleccionadas: fuerza y trabaja.** El IMC queda fuera por diseño del escenario P2, y el lugar comprensivo pertenece al módulo laboral.
- **El MRS no participó en la formación de los grupos.** La selección mide asociación con la severidad del MRS; el agrupamiento busca estructura entre las variables sin mirar el MRS. Son preguntas distintas.

---

## 9. Consecuencias para PCA y K-means

**Lo que el bootstrap no implica:**
- **No invalida automáticamente los modelos de la Fase 37.**
  - PCA, FAMD y K-means no usaron la selección de FCBF como entrada.
  - La inestabilidad del selector no se transmite de forma mecánica a las matrices ni a los grupos.
  - Cambiar las cuatro variables seleccionadas no cambiaría ninguna columna de P2.
- **No mide la estabilidad de los grupos.** La estabilidad de la segmentación es otra pregunta y se evaluó por separado en las Fases 37B y 37C, con remuestreos y comparaciones propias.

**Lo que el bootstrap sí aporta, como contexto:**
1. **Es coherente con lo que mostró la Fase 37.** La 37B no encontró grupos naturales claros, y en la 37D las diferencias de MRS entre segmentos fueron pequeñas. Que la asociación de cada variable con la severidad del MRS sea débil y cambie de una muestra a otra es compatible con esos resultados. Ninguno de los dos hallazgos depende del otro.
2. **Limita cómo se interpretan los segmentos.** Si los segmentos de `P2_c12_km_k4` se describen con variables, no conviene destacar las cuatro de FCBF como «las variables que explican la severidad». Es más defendible hablar de **bloques**, como «actividad física» o «situación laboral», que de variables individuales.
3. **Respalda que el MRS no se haya usado para formar los grupos.** Con una señal tan inestable, construir los segmentos a partir de variables seleccionadas por su relación con el MRS habría producido grupos dependientes de la muestra concreta.
4. **No obliga a rehacer las Fases 36 a 39.** El protocolo de este complemento prohibió recalcular PCA, FAMD, K-means o Ward, y la integridad confirma que no se tocaron. Revisar la Fase 37 sería una decisión metodológica de la responsable del proyecto; este análisis no la exige.

---

## 10. Limitaciones

1. **El bootstrap facilita la significancia.** Las personas repetidas se tratan como observaciones distintas, también en las permutaciones. En promedio resultan relevantes 13,2 variables por remuestreo, frente a 6 en la muestra original. Los porcentajes se interpretan solo de forma **descriptiva**, nunca como probabilidades de que una variable «sea relevante».
2. **Se usaron 5.000 permutaciones por remuestreo**, como en la corrida histórica, y no las 10.000 o 50.000 de la selección definitiva. Con q cercanos a 0,10, el error de Monte Carlo puede cambiar la decisión de relevancia en casos límite.
3. **Los datos son sintéticos.** El resultado describe el comportamiento del procedimiento en este conjunto y **no es una validación clínica** de ninguna variable.
4. **Se hizo después del cierre de las Fases 36 a 39.** El protocolo se selló antes de ejecutar (sha 4fe67949…, 21:40), pero el análisis en sí es retrospectivo.
5. **La comparación con la corrida anterior es solo descriptiva**, porque cambiaron tres elementos a la vez (sección 7).
6. **La dependencia de personas concretas** se calculó solo para la variante adaptada y para las variables con frecuencia entre 5 % y 95 %. Sus |z| no están corregidos por las 529 comparaciones de cada variable.
7. **Las bandas de frecuencia** (≥ 80 %, 50–79 %, < 50 %) son las del protocolo 35B y solo descriptivas. No se crearon umbrales nuevos.
8. **La escala de lectura del índice de Nogueira es orientativa.** El protocolo no fijó un valor de aceptación.

---

## 11. Conclusiones para la tesis

1. La selección de variables por SU y FCBF tiene **estabilidad baja** (Nogueira 0,129; IC 95 % 0,118–0,139), en las dos variantes y con las 33 variables finales.
2. Las cuatro variables de la selección definitiva son **las más frecuentes**, pero **ninguna es estable** (31 % al 39 %), y el conjunto no se reproduce en ninguna muestra.
3. La **relevancia** es más estable que la selección: la señal asociada a la actividad física aparece en casi todas las muestras. Lo que varía es la representante que elige FCBF.
4. Con la configuración definitiva la estabilidad no mejora respecto de la estimación preliminar de 30 candidatas, aunque las selecciones concretas sí cambian.
5. La selección de FCBF debe presentarse como **orientativa**. No se debe decir que sus variables son «estables», «robustas» ni «determinantes».
6. El resultado **no modifica las Fases 36 a 39**. Sus matrices no dependen de la selección y la estabilidad de los segmentos se evaluó por separado. Sí aconseja describir los segmentos por bloques de variables y no por las cuatro seleccionadas.

---

## 12. Texto propuesto para el apartado 3.6

*Este texto actualiza el de `04_nota_tesis.md`. Puede insertarse después del párrafo que describe la selección definitiva por SU y FCBF.*

> **3.6.x Evaluación retrospectiva de la estabilidad de la selección**
>
> La estabilidad del procedimiento de selección se estimó inicialmente el 2 de noviembre de 2026 sobre una lista preliminar de 30 candidatas, que incluía la variable derivada de doble carga y usaba un umbral de relevancia q < 0,05. La configuración definitiva modificó posteriormente esa lista. Se excluyeron la doble carga, por derivarse de otras dos variables, y el uso de medicamentos para la diabetes, por una dominancia superior al 85 %. La edad, el IMC y la situación laboral pasaron de variables de control a candidatas. Se incorporó la sobrecarga de las cuidadoras en una tercera etapa y el umbral de relevancia pasó a q < 0,10. Como la estimación preliminar dejó de corresponder a la configuración definitiva, la evaluación se repitió con las 33 variables finales. **Esta repetición se ejecutó el 5 de noviembre de 2026, después del cierre de las Fases 36 a 39, y no modificó ninguno de sus resultados.** El protocolo de la repetición se registró y selló antes de la ejecución.
>
> Se generaron 500 remuestreos bootstrap estratificados por la severidad sintomática (MRS ≥ 16), con reemplazo y conservando 281 casos severos y 248 no severos. En cada remuestreo se repitió el procedimiento completo. Primero se estimó la incertidumbre simétrica con la severidad mediante 5.000 permutaciones por variable y se aplicó la corrección de Benjamini-Hochberg sobre la familia de 33 pruebas, con relevancia en q < 0,10. Después se evaluó la redundancia entre todos los pares de variables relevantes y se aplicó FCBF en tres etapas (población general, mujeres trabajadoras y cuidadoras), en sus variantes adaptada y estándar. Las subpoblaciones laboral y de cuidadoras acompañaron a cada persona remuestreada. Se usaron las mismas semillas de remuestreo que en la estimación preliminar, de modo que ambas se basan en las mismas 500 muestras. La estabilidad se resumió con el índice de Nogueira, Sechidis y Brown (2018), que vale 1 cuando se seleccionan siempre las mismas variables y 0 cuando la coincidencia no supera la esperada por azar. Se acompañó de su intervalo de confianza al 95 %, del índice de Jaccard entre remuestreos y de la frecuencia de selección de cada variable.
>
> La estabilidad de la selección fue baja. El índice de Nogueira fue 0,129 (IC 95 %: 0,118–0,139) en la variante adaptada y 0,128 en la estándar. El Jaccard promedio entre remuestreos fue 0,14. Ninguna variable se seleccionó en la mitad o más de los remuestreos. Las cuatro variables de la selección definitiva (IMC, frecuencia de ejercicio de fuerza, situación laboral y lugar de trabajo comprensivo) fueron las más frecuentes, con 39,0 %, 35,2 %, 32,6 % y 31,4 %. Sin embargo, ningún remuestreo reprodujo exactamente esa selección, y el Jaccard medio con ella fue 0,24. Respecto de la estimación preliminar (Nogueira 0,121 y 0,126), la estabilidad no mejoró de forma apreciable. Como entre ambas estimaciones cambiaron simultáneamente las candidatas, el umbral y una etapa, esta comparación se presenta solo de forma descriptiva.
>
> La relevancia fue considerablemente más estable que la selección (Nogueira 0,337). Cinco de las seis variables relevantes en la configuración definitiva superaron el filtro en el 82 % al 91 % de los remuestreos, y la sexta, la situación laboral, en el 67 %. La inestabilidad se concentró en la elección de una representante dentro de grupos de variables relacionadas. Las tres variables de actividad física fueron relevantes, al menos una de ellas, en el 98,6 % de los remuestreos, y FCBF retuvo una de ellas en el 78,8 % y casi nunca más de una (0,2 %). La variable retenida, en cambio, cambió de una muestra a otra. La debilidad de las asociaciones, con incertidumbres simétricas del orden de 0,01 a 0,02 y valores q de las variables seleccionadas entre 0,081 y 0,089, explica que pequeñas variaciones muestrales alteren el orden de las variables y, con él, la selección.
>
> Tres advertencias limitan esta interpretación. Primero, en el bootstrap las observaciones repetidas se tratan como independientes, también en las permutaciones, lo que facilita la significancia: en promedio resultaron relevantes 13,2 variables por remuestreo, frente a 6 en la muestra original. Por ello las frecuencias se interpretan de forma descriptiva. Segundo, se usaron 5.000 permutaciones por remuestreo, como en la estimación preliminar, y no las 50.000 de la selección definitiva. Tercero, los datos son sintéticos, por lo que el resultado describe el comportamiento del procedimiento de selección en este conjunto y no constituye una validación clínica de ninguna variable.
>
> En consecuencia, la selección obtenida por FCBF se interpreta como orientativa, y sus variables no se describen como estables ni determinantes de la severidad sintomática. Esta evaluación no altera las Fases 36 y 37. En la configuración definitiva FCBF tiene carácter informativo y no elimina variables. Las matrices de reducción de dimensionalidad se construyeron con las 30 variables generales, independientemente de la selección y sin el MRS. El modelo elegido (PCA sin IMC, 12 componentes y K-means con k = 4) incluye solo dos de las cuatro variables seleccionadas. La estabilidad del selector no debe confundirse con la estabilidad de los agrupamientos, que se evaluó por separado en la Fase 37. No obstante, la baja estabilidad de la selección aconseja describir los segmentos mediante bloques de variables, como la actividad física o la situación laboral, y no mediante variables individuales.

**Correcciones al texto existente de la tesis:**
- Si el apartado 3.6 o un anexo muestra la figura `estabilidad_seleccion.png` o los índices 0,121 y 0,126, debe indicarse que corresponden a la lista preliminar de 30 candidatas con q < 0,05. Otra opción es reemplazarlos por `figuras/f01_estabilidad_33_variables_finales.png` y los valores de este informe.
- El término «bootstrap» es correcto en las dos corridas.

---

## 13. Integridad de los archivos históricos

**Al terminar la corrida** (05-11, 22:50; `integridad/integridad_final.json`):
- 5.977 archivos protegidos comparados: todo `analisis/` salvo esta carpeta, todo `src/` (Django) y `datos/` salvo los datos reales y el archivo de verdad del simulador;
- 0 cambiados, 0 eliminados y 0 nuevos fuera de esta carpeta.

**Al redactar este informe** (06-11) se repitió la comparación con el manifiesto original:
- Se hizo en modo de solo lectura, con un script en la carpeta temporal de la sesión, sin sobrescribir `integridad_final.json`.
- Resultado: **5.977 archivos, 0 cambiados, 0 eliminados y 0 nuevos**.
- El congelamiento del computador no dañó ningún archivo protegido.

**Archivos históricos de estabilidad**, verificados uno por uno por la prueba 18, con la misma huella:
- `analisis/resultados/usuaria/estabilidad_remuestreos.csv`
- `analisis/resultados/usuaria/estabilidad_fcbf.csv`
- `analisis/resultados/usuaria/estabilidad_global.csv`
- `analisis/resultados/usuaria/log_seleccion_fase35b.txt`
- `analisis/figuras/seleccion_35b/estabilidad_seleccion.png`
- `analisis/reunion_2026-11-03/revision_33_variables/log_revision_33.txt`

**Repositorio:** HEAD sigue en `745d689`, rama `datos-simulados`. No se hizo commit ni push.

**Esta carpeta:** los resultados, las pruebas y los informes 02 a 04 conservan las fechas de la corrida del 05-11; el último archivo se escribió a las 22:51:38. **El único archivo nuevo es este informe** (`informes/05_informe_consolidado.md`). No se modificó ningún resultado, registro ni remuestreo guardado.
