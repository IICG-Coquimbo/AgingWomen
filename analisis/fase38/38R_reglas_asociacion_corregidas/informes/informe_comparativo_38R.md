# Fase 38R: informe comparativo

Fecha: 2026-11-08. Rama `datos-simulados`, HEAD `573d3a3`. Sin commits ni pushes. Protocolo sellado antes de calcular: `protocolo/01_protocolo_38R.md`, SHA-256 `32a64ec8d5cdd4ceec8a13f54e44abccfbda689517cf430299eaf6a4b601e867`.

**Resultado en una frase:** retirar `prevision` y `usa_medicamentos_diabetes` reduce el espacio de búsqueda, pero no cambia la conclusión: la señal sigue siendo difusa, sigue habiendo una sola regla de clase 6, y esa regla no es robusta.

## I. Configuración corregida

- **Variables:** 29 generales, que coinciden exactamente con las 30 de población general de la Fase 35 menos `imc`, con el esquema P2 de la Fase 36 y con la lista histórica menos las dos retiradas.
- **Ítems:** 90 (los 94 históricos menos `med_diabetes=NO/SI` y `prevision=FONASA/ISAPRE`). La matriz es idéntica a la histórica sin esas cuatro columnas en las 529 filas.
- **Exclusiones definitivas en las 16 configuraciones:** `prevision`, `usa_medicamentos_diabetes`, `doble_carga`.
- **Reservadas para sensibilidades:** `imc` (S8b), `lugar_trabajo_comprensivo` y `estres_entorno_laboral` (S7a), `sobrecarga_fisica_emocional` (S7b).
- **Sin cambios de método:** consecuente `severo_mrs`; 529 participantes (281 severas, 248 no severas); umbrales `n_A ≥ 53` y `n_AC ≥ 27`; antecedentes de 1 a 3 condiciones; semilla 42; 1.000 permutaciones por configuración; 200 submuestras del 80 %; marcada `|c − p₀| ≥ 0,10`; mejora mínima 0,05; clases 1 a 6. Las funciones históricas se importan sin modificar.
- **Poblaciones verificadas documental y empíricamente:** 287 (S7a), 309 (S7a-309), 239 (S7b), 251 con 12 imputadas (S7b-251), 267 (S8a y S8b).

## II. Verificación de exclusiones

- **Barreras:** 65/65 controles. De ellos, 49 son controles negativos que detienen el proceso cuando se les introduce una variable o población indebida, y 16 son las configuraciones reales, que pasan. Comprueban nombre y contenido de cada ítem, incluidas formas transformadas y complementos.
- **Barrido de resultados:** 69 archivos revisados, 0 apariciones de las variables excluidas. La única mención está en el registro `preparacion/verificacion_preparacion.json`, que documenta qué ítems se retiraron.
- **Tablas de reglas:** las 16 pasan `verificar_reglas`.
- **Antecedentes prohibidos** (MRS, posteriores a síntomas, etiquetas de segmentación): ninguno. Coincidencia declarada en el protocolo: en S2b, `dias_ejercicio=3_o_mas_dias` es idéntico por definición al primer paso de la regla B1; es un ítem de ejercicio y existe igual en la Fase 38.
- **Algoritmos:** Apriori, FP-Growth y enumeración exhaustiva coinciden (42.937 conjuntos; 9.761 reglas; 0 diferencias).
- **Pruebas:** 20/20; control de mutaciones 11/11.

## III. Comparación de resultados

### Análisis principal

| Indicador | Fase 38 | Fase 38R |
|---|---:|---:|
| Variables | 31 | 29 |
| Ítems | 94 | 90 |
| Conjuntos frecuentes | 52.685 | 42.937 |
| Antecedentes evaluados | 12.325 | 9.865 |
| Reglas totales | 12.201 | 9.761 |
| Hacia síntomas severos | 6.275 | 5.319 |
| Hacia no severos | 5.926 | 4.442 |
| Marcadas | 1.119 | 971 |
| Marcadas no redundantes | 193 | 184 |
| Nula: media de marcadas | 649,98 | 543,56 |
| Nula: percentil 95 de marcadas | 970,05 | 811,25 |
| p del exceso de marcadas | 0,0150 | 0,0130 |
| Nula: percentil 95 del máximo z | 4,106 | 4,085 |
| Compatibles con la nula (marcadas no redundantes) | 192 | 183 |
| Superan la nula | 1 | 1 |
| Clase 2, asociación débil | 11.082 | 8.790 |
| Clase 3, redundante | 926 | 787 |
| Clase 4, compatible con la nula | 192 | 183 |
| Clase 6, relativamente más marcada | 1 | 1 |
| **Robustas** | **0** | **0** |

### Reglas conservadas

- 9.761 reglas conservadas, 0 perdidas, 0 nuevas; 2.440 retiradas (contenían una variable excluida).
- 0 diferencias en las 29 métricas propias de cada regla.
- 0 reglas cambian de clase.
- p ajustado por búsqueda: nunca sube (9.698 iguales; baja máxima 0,049). Al haber menos reglas, en 171 de 1.000 permutaciones el máximo z es menor.
- q de BH: 7.834 bajan o se mantienen (732 iguales) y 1.927 suben, porque la corrección se recalcula sobre otra familia de reglas.

### Estabilidad

| Indicador | Fase 38 | Fase 38R |
|---|---:|---:|
| Reglas estables | 535 | 480 |
| Familias evaluadas | 1.089 | 944 |
| Reaparición media por familia | 0,716 | 0,723 |
| Marcadas por submuestra (media) | 1.410,8 | 1.211,8 |

La estabilidad es idéntica en las 9.761 reglas conservadas; la baja de 535 a 480 corresponde a las reglas retiradas. Las submuestras se recalcularon, no se reutilizaron.

### Sensibilidades

Reglas / marcadas / superan la nula. Todas recalculadas con su propia referencia nula.

| Config. | n | Fase 38 | Fase 38R |
|---|---:|---|---|
| S1, sin imputados | 529 | 7.542 / 889 / 0 | 7.542 / 889 / 0 |
| S2a, categorías originales | 529 | 11.602 / 972 / 1 | 9.269 / 853 / 1 |
| S2b, agrupación gruesa | 529 | 16.126 / 1.595 / 10 | 13.639 / 1.386 / 2 |
| S3-bajo | 529 | 27.767 / 5.389 / 0 | 23.025 / 4.519 / 0 |
| S3-alto | 529 | 6.488 / 321 / 0 | 4.938 / 278 / 0 |
| S4-1, una condición | 529 | 81 / 4 / 0 | 77 / 3 / 0 |
| S4-2, hasta dos | 529 | 1.565 / 104 / 0 | 1.401 / 91 / 0 |
| S5, sin frecuencias de ejercicio | 529 | 9.002 / 789 / 0 | 6.955 / 657 / 0 |
| S6, sin variables próximas a síntomas | 529 | 9.033 / 834 / 0 | 7.072 / 716 / 0 |
| S7a, laboral | 287 | sin equivalente | 10.435 / 2.700 / 0 |
| S7a-309, laboral ampliada | 309 | 12.772 / 3.041 / 0 | 10.178 / 2.568 / 0 |
| S7b, sobrecarga observada | 239 | sin equivalente | 11.315 / 3.249 / 1 |
| S7b-251, sobrecarga con imputadas | 251 | 13.401 / 3.480 / 1 | 10.747 / 2.942 / 1 |
| S8a, IMC observado sin IMC | 267 | 12.287 / 2.800 / 0 | 9.808 / 2.359 / 0 |
| S8b, IMC observado con IMC | 267 | 13.479 / 3.389 / 0 | 10.798 / 2.855 / 0 |

- **S1 es igual byte a byte a la histórica** (reglas y nula). No es reutilización: se recalculó, y la S1 histórica ya excluía ambas variables por tener valores imputados.
- **S2b baja de 10 a 2** reglas que superan la nula, de las cuales 1 no es redundante (la histórica tenía 2 no redundantes). La regla histórica con `prevision=FONASA` desaparece.
- **Reglas que superan la nula en sensibilidades:**
  - S2a: la regla de clase 6 de la principal (p 0,036).
  - S2b: `comida_fuera=nunca_o_1-2 & dias_ejercicio=3_o_mas` → no severo (p 0,031); y `bajo_impacto=rara_vez_a_siempre & med_presion=NO & tabaco=nunca` → no severo (p 0,049, redundante).
  - S7b y S7b-251: `aerobico=no & agua=3-4 & sobrecarga=frecuente_o_siempre` → severo (n 34, confianza 0,912; p 0,038 y 0,027). Solo existe en las submuestras de cuidadoras.
- **287 frente a 309:** 2.700 y 2.568 marcadas; 2.225 en ambas. **239 frente a 251:** 3.249 y 2.942; 2.568 en ambas.
- Lectura de las 971 marcadas en cada sensibilidad: `comparacion/lectura_principal_en_sensibilidades.csv`.

## IV. Regla originalmente clase 6

`bajo_impacto=no_lo_realiza_o_nunca & distension=nunca_o_casi_nunca & trabaja=SI` → `severo_mrs=SI`

| Métrica | Fase 38 | Fase 38R |
|---|---:|---:|
| Casos con antecedente / con consecuente | 57 / 46 | 57 / 46 |
| Confianza (IC 95 %) | 0,807 (0,687–0,889) | 0,807 (0,687–0,889) |
| Lift | 1,519 | 1,519 |
| z | 4,173 | 4,173 |
| Mejora | 0,119 | 0,119 |
| Reaparición / dirección en submuestras | 0,885 / 1,0 | 0,885 / 1,0 |
| q (BH) | 0,0960 | 0,0768 |
| p ajustado por búsqueda | 0,0380 | 0,0330 |
| Clase | 6 | 6 |

Las métricas propias no cambian porque la regla no usa las variables retiradas. El q y el p ajustado mejoran solo porque se busca entre menos reglas.

En las 15 sensibilidades, 8 son evaluables:

- **Se mantiene (4):** S2a (supera la nula), S3-bajo, S7b y S7b-251 (estas tres, compatibles con la nula).
- **Desaparece por falta de casos (4):** S1 (n 52), S3-alto, S8a, S8b (n 23).
- **No evaluable (7):** S2b, S4-1, S4-2, S5, S6, S7a, S7a-309.

**No se declara robusta.** Sigue en clase 6 por los criterios sellados, pero es frágil: no sobrevive a la mitad de las sensibilidades evaluables y solo supera la nula en una de ellas.

## V. Impacto en la tesis (identificado, no modificado)

No hay borrador de tesis en el repositorio. Solo hay dos notas: `analisis/nota_tesis_etapa_menopausica.md` y `analisis/complemento_bootstrap_33/informes/04_nota_tesis.md`, y ninguna cita cifras de la Fase 38.

Si el texto externo de la tesis cita la Fase 38, debe revisarse:

- 31 variables → 29; 94 ítems → 90; 12.201 reglas → 9.761.
- 1.119 marcadas frente a 650 esperadas → 971 frente a 544.
- Clases, estabilidad y sensibilidades según la sección III.
- Descripción de la matriz: `prevision` y `usa_medicamentos_diabetes` no deben figurar como predictoras.
- La regla de clase 6: q 0,0768 y p ajustado 0,0330. Su interpretación no cambia.

Documentos del proyecto con cifras derivadas de la Fase 38, sin tocar:

- Fase 38: `informes/fuentes/` 01, 06 a 12 y 16 (también los Word correspondientes) y las 8 figuras de `figuras/`. **La 38R no regeneró figuras ni documentos Word.**
- Fase 39: `informes/fuentes/` 02, 04, 06, 07 y 19. Sus resultados dependen de la Fase 39R.
- Fase 40: `analisis/fase40/40D_orientaciones/40D-1_informe.md:92,96`. La afirmación sobre la Fase 38 («una sola regla de la clase más marcada, y frágil») sigue siendo válida con la 38R; la de la Fase 39 queda sujeta a la 39R.

## VI. Integridad del proyecto

| Control | Resultado |
|---|---|
| Huellas de `analisis/` (salvo 38R), datos y `src/`: 6.265 archivos | 0 cambiados, 0 nuevos |
| Manifiestos de las Fases 34 a 39: 6.462 archivos | Fases 36 a 39: 0 distintos. Fases 34-35: 4 diferencias en 3 rutas, ya existentes antes de la 38R |
| Diferencias no documentadas | 0 |
| `test_40b1_proteccion_historica.py` | 5/5 OK |
| 134 archivos pendientes de la Fase 40 | 0 distintos |
| `git status` sin la carpeta 38R | 86 líneas, igual al inicial |
| Rama y HEAD | `datos-simulados`, `573d3a3`, sin cambios |
| Stash | vacío |
| `__pycache__` en Fases 36 a 39 | ninguno |
| Escrituras fuera de 38R durante el cálculo | 0 |

- **Respaldo previo:** `datos/respaldos/2026-11-08_antes_38R/`, 134 archivos verificados por SHA-256.
- **Las 4 diferencias de manifiesto** corresponden a `analisis/limpieza/catalogo.py`, `analisis/eda/univariado.py` y `analisis/eda_usuaria.py`, excepciones ya conocidas de `test_40b1`. Son las mismas en la medición inicial y en la final.
- **Control correctivo:** las pruebas históricas p17 y p18 exigen HEAD `745d689` y `src/` sin cambios, por lo que ya no pueden cumplirse. No se desactivaron ni se modificaron; se sustituyeron por `scripts/integridad_38r.py`.
- `integridad_38r.py final` terminó con código 0. Se ejecutó dos veces para capturar ese código; vale la última (10:40:38).

## VII. Incidencias pendientes

### Resultados verificados

- Las exclusiones se cumplen en las 16 configuraciones.
- Las 9.761 reglas conservadas no cambian en métricas ni en clase.
- La conclusión de la Fase 38 se mantiene: señal difusa (971 marcadas frente a 544 esperadas; p 0,013), una regla de clase 6 frágil y 0 robustas.
- Históricos y trabajo pendiente intactos.

### Limitaciones

- Datos sintéticos, análisis no ciego y misma muestra para descubrir y evaluar.
- La convicción se calculó solo como anexo descriptivo (`reglas/conviccion_descriptiva_anexo.csv`), porque el protocolo histórico no la define. No interviene en ninguna clasificación.
- `integridad_inicial.json` se generó antes de añadir el criterio de excepciones documentadas, por lo que no trae ese campo. No se reejecutó, para que la medición inicial siga siendo anterior a los cálculos. Sus 4 diferencias coinciden con la final.
- La Fase 37D sigue usando las dos variables de forma descriptiva; no se revisó en esta fase.

### Requieren tu autorización

1. **Fase 39R.** No se ha iniciado. La Fase 39 hereda la configuración de la Fase 38.
2. **S7a con 263.** De las 287, 263 tienen ambas respuestas laborales observadas; las otras 24 tienen al menos una imputada (lugar 16, estrés 10). La Fase 36 define 263 como sensibilidad. No se ejecutó por no estar solicitada; hay que decidir si se añade y si el rótulo «observada» se reemplaza.
3. **Figuras y Word de la 38R.** ¿Se generan versiones corregidas?
4. **Actualización de la tesis** y de `40D-1_informe.md`.
5. **Commit de la carpeta 38R.** Hoy está sin seguimiento.
6. **Pendientes de la Fase 40, ajenos a la 38R:** pruebas integrales finales, rotación de `SECRET_KEY` y commit.
