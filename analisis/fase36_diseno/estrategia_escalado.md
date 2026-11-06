# Fase 36A: estrategia de escalado

**Estado:** propuesta para revisión. No se ajustó ningún escalador y no se generaron matrices.
**Cifras:** `apoyo/distribuciones_para_escalado.csv`, calculadas columna por columna sobre `datos/analitico/dataset_fase35.csv` y el conjunto limpio.

## 1. Recomendación

Usar **StandardScaler (media 0, desviación estándar 1, con `ddof = 0`) como regla común**, con dos excepciones justificadas:

| Caso | Tratamiento | Motivo |
|---|---|---|
| Regla común: cuantitativas, ordinales representadas numéricamente y binarias | `(x − media) / DE` | Da la misma varianza a cada variable, de modo que ninguna domine la distancia euclidiana por su unidad |
| `imc` | Media y DE de las **267 observadas** (29,23 y 6,26), aplicadas a las 529 | Evita que la imputación comprima la escala |
| `quien_prepara_comidas` en PCA | Indicadoras centradas, divididas por `√Σ p(1−p)` | Deja igual distancia entre categorías y varianza total 1 |

**Sin transformaciones adicionales:** no se propone logaritmo, recorte ni winsorización. Los extremos son plausibles y ningún criterio de los datos justifica cambiarlos.

## 2. Variables cuantitativas

| Variable | Rango | Asimetría | Curtosis (exceso) | Atípicos de Tukey | Extremos | Decisión |
|---|---|---|---|---|---|---|
| `edad` | 36 a 65 | 0,11 | −1,00 | 0 | Dentro del alcance del estudio | StandardScaler |
| `imc` (267 observadas) | 18,2 a 45,7 | 0,35 | −0,52 | 0 | Plausibles | StandardScaler con parámetros de las observadas |
| `horas_sedentarismo` | 1 a 14 | 0,05 | 0,00 | 2 | Plausibles; se conservan | StandardScaler |

Las medidas de `horas_sedentarismo` incluyen 27 valores imputados (limitación A1), por lo que su forma es aproximada. El efecto no cambia la decisión, porque la asimetría es muy baja.

### Por qué no RobustScaler

RobustScaler divide por el rango intercuartílico. En 9 de las 29 columnas numéricas ese rango es **0**: `frecuencia_aerobico`, `frecuencia_fuerza`, `frutas_dia`, `lacteos_dia`, `operada_no_mas_hijos`, `panes_dia`, `platos_verduras_dia`, `tabaco_frecuencia` y `usa_medicamentos_presion`. En ellas no está definido. Usarlo solo en las tres cuantitativas no se justifica, porque casi no tienen atípicos, y dejaría mezcladas dos escalas distintas.

## 3. IMC: qué parámetros usar

| Opción | Media | DE | Varianza del IMC tras escalar | Efecto |
|---|---|---|---|---|
| **Observadas (recomendada)** | 29,23 | 6,26 | 0,505 | Las diferencias observadas conservan su escala real, y las imputadas quedan en 0 |
| Las 529, con imputadas | 29,23 | 4,45 | 1,000 | Amplifica las diferencias entre observadas en un factor de 1,41 |

Con la opción recomendada, el IMC pesa cerca de la mitad de una variable común. Es coherente con que la mitad de la muestra no aporta información sobre él. En la Fase 40, una usuaria sin IMC recibe z = 0 con la misma regla. Las diferencias entre DE (6,26 aquí y 6,28 en el informe 35A) se deben a `ddof = 0` frente a `ddof = 1`.

**Decisión pendiente D-05.**

## 4. Ordinales y binarias

- **Ordinales (21 generales):** la estandarización no vuelve equidistantes sus niveles; solo iguala la varianza. La equidistancia es un supuesto de trabajo y se contrasta con la sensibilidad ridit (`estrategia_pca_famd.md`).
- **Binarias (5):** una columna 0/1 estandarizada. Es matemáticamente equivalente al bloque de dos indicadoras con varianza total 1. Una categoría minoritaria queda lejos del centro: el «Sí» de presión queda en z = 2,22.
- **Colas largas:** los valores más extremos son `frecuencia_fuerza` (z = 3,79), `alcohol_frecuencia` (3,73) y `dias_ejercicio_semana` (3,60). Son niveles reales del instrumento. La Fase 37 debe vigilar si K-means crea grupos muy pequeños a partir de ellos.

## 5. Nominal en PCA

Con la estandarización común, la categoría OTRO (n = 7) quedaría en z = 8,6 y crearía casos extremos solo por ser rara. Al dividir las indicadoras centradas por `√Σ p(1−p)`, con Σ p(1−p) = 0,487:

- dos participantes con categorías distintas quedan a la misma distancia al cuadrado (4,11), cualquiera sea la categoría;
- la variable suma varianza 1, igual que las demás;
- esa distancia es comparable a la de `trabaja_actualmente` (1/0,243 = 4,11).

## 6. Variables constantes

Ninguna columna de las 29 numéricas es constante en la referencia. Una DE igual a 0 detiene la ejecución con error: no se elimina la variable en silencio, porque cambiaría la lista acordada.

## 7. Efecto sobre distancias y reducción dimensional

- **Distancia euclidiana:** con varianza igual, cada variable aporta en promedio lo mismo, y por eso cada **bloque pesa según su número de variables**. Alimentación tiene 13 de 30 (decisión D-07).
- **PCA:** opera de hecho sobre una matriz de correlaciones. Solo 4 de 435 pares superan |0,4| y 424 están bajo |0,2|. Hay que esperar poca varianza por componente, y que los primeros ejes recojan sobre todo el bloque de ejercicio.
- **Varianza total esperada:** 29,505 con IMC (28 columnas × 1 + IMC 0,505 + nominal 1) y 29 sin IMC.

## 8. Reproducción sobre nuevas usuarias

1. Los parámetros se calculan **una sola vez**, con los datos de referencia de la configuración aprobada, y se guardan en JSON.
2. Una usuaria nueva se transforma con esos parámetros, sin ajustarlos de nuevo.
3. Un nivel válido no observado, como `frutas_dia = 5`, se transforma con los mismos parámetros, aunque quede fuera del rango de referencia.
4. Los modelos de sensibilidad tienen sus propios parámetros, y nunca se usan en la plataforma.
5. Una versión nueva de los parámetros exige una versión nueva de los perfiles.
