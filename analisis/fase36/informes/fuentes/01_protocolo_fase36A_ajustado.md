# 1. Estado y alcance

Este protocolo incorpora los ajustes pedidos tras la revisión del diseño de la Fase 36A. **Prevalece sobre `analisis/fase36_diseno/` donde difieran.** Esa carpeta no se modificó y conserva la versión anterior.

- **Alcance:** codificar y escalar las 30 variables generales de 529 participantes, y preparar los módulos y las sensibilidades.
- **Fuera de alcance:** no se ajusta PCA ni FAMD, no se ejecuta K-means ni el método aglomerativo, y no se forman clústeres ni reglas. Eso corresponde a la Fase 37 y siguientes.
- **Datos:** nunca se usa la verdad del simulador ni su bitácora. Las 529 filas se conservan en todos los escenarios principales.

# 2. Decisiones confirmadas

| ID | Decisión | Texto final |
|---|---|---|
| D-01 | Ordinales en la ruta PCA | Códigos consecutivos en la ruta principal y ridit como sensibilidad (S-ORD). Los mapas respetan el orden y los niveles del instrumento. **Supuesto explícito:** los códigos consecutivos suponen pasos iguales entre niveles. Es un supuesto de trabajo, no un hecho de los datos, y S-ORD lo contrasta. |
| D-03 | Roles en FAMD | 19 cuantitativas y 11 categóricas, incluidas cinco ordinales categóricas. S-FAMD examina esa clasificación al pasarlas todas a cuantitativas. |
| D-05 | Parámetros del IMC | Media y DE de las 267 con IMC observado. La varianza final en las 529 es 267/529 = 0,5047. No se aplica una segunda estandarización en ninguna ruta. |
| D-07 | Peso de los bloques | La ruta principal no lleva ponderación adicional. S-BLOQUE queda preparada, sin ejecutar sobre clústeres. |
| D-08 | Procedencia por celda | Se reconstruye en memoria repitiendo la limpieza sobre el conjunto sucio, sin leer la verdad del simulador. Los recuentos se contrastan con las auditorías históricas, y una diferencia detiene la construcción. |

Las recomendaciones técnicas D-02, D-04, D-06, D-10, D-11, D-12 y D-14 se aplican como estaban propuestas. D-09, D-13 y D-15 siguen abiertas (sección 11).

# 3. Correcciones técnicas

## RobustScaler

**Corrección.** El diseño decía que RobustScaler «no está definido» si el rango intercuartílico es cero. Es impreciso: scikit-learn sustituye esa escala por 1 y no falla. Se comprobó con datos de ejemplo en la versión 1.6.1.

La justificación de StandardScaler es **la adecuación al diseño**, no un fallo del escalador alternativo:

- **Peso desigual:** 9 de las 28 columnas numéricas con referencia en las 529 tienen rango intercuartílico cero y conservarían su unidad original. Sobre esas 28 columnas, la varianza tras RobustScaler iría de 0,14 (`usa_medicamentos_presion`) a 2,26 (`tabaco_frecuencia`), de modo que el peso en la distancia dependería de la forma de la distribución y no de una decisión. Con StandardScaler todas tienen varianza 1.
- **Coherencia con FAMD:** el método define las cuantitativas estandarizadas, de modo que cada una aporta inercia 1 y es comparable con la inercia de las categóricas.
- **Sin necesidad de robustez:** los extremos son niveles reales del instrumento, y las tres cuantitativas casi no tienen atípicos.

## «Nunca» y «No lo realiza»

Se unifican **solo** en `frecuencia_aerobico`, `frecuencia_bajo_impacto` y `frecuencia_fuerza`, donde ambos representan frecuencia efectiva cero.

- **Mapa:** 0 y 1 → 0; 2 → 1; 3 → 2; 4 → 3; 5 → 4.
- **Dónde no se aplica:** en las otras nueve variables con un nivel «Nunca» o «Nunca o casi nunca» dentro de la capa general, como `tabaco_frecuencia` o `alcohol_frecuencia`, ese nivel conserva su código: allí es un punto real de la escala.
- **Preservación:** `procedencia_celdas.csv` guarda el valor original y su estado. El código unificado solo existe en la transformación. Una participante nueva con «Nunca» recibe una marca `nunca_unificado`.

## Grupos fijos para FAMD

Los grupos están escritos en `configuracion_fase36.py` y en `artefactos/agrupaciones_categorias.csv`; no se recalculan al construir. La regla del 5 % solo se usa en una prueba para comprobar que reproduce esa tabla. Las sensibilidades de proyección usan los mismos grupos, aunque cambien sus proporciones.

## Niveles válidos no observados y frecuencia cero

Hay 13 niveles admitidos por el instrumento sin ninguna observación.

| Caso | Tratamiento |
|---|---|
| Ordinal representada como número (10 niveles) | Se transforma con los parámetros congelados, queda fuera del rango de referencia y recibe marca |
| «Nunca» en las frecuencias de ejercicio (3 niveles) | Se une a «No lo realiza»; no tiene columna propia |
| Categoría de FAMD con frecuencia cero | Calibrar se detiene con error, porque dividiría por √0. Debe unirse a un grupo con observaciones |
| Nivel no admitido por el instrumento | Error, sin perfil |

## Congelación

Los transformadores y las reglas de imputación permanecen congelados al procesar nuevas participantes. Medias, DE, proporciones, grupos y valores congelados se calculan una sola vez. El transformador no tiene método de ajuste. Cambiar cualquiera de ellos exige una versión nueva de los parámetros y de los perfiles.

# 4. Precisiones a cifras del diseño

| Tema | El diseño decía | Precisión |
|---|---|---|
| Imputaciones en las generales | 665 de 15.870 (4,2 %) | Esa cifra cuenta solo la limpieza 34B. Con las 262 del IMC de la Fase 35A son **927 (5,8 %)**. Más 100 valores estructurales heredados |
| Varianza del IMC | 0,505 | Valor exacto 267/529 = 0,5047 |
| Inercia total | 29,505 y 38,505 | 29,5047 y 38,5047 |
| Estados de una celda | Cuatro | Se agrega `faltante`: las 22 con trabajo imputado como Sí no tienen respuestas laborales, aunque sí les aplicaban. No es lo mismo que «no aplica» |

# 5. Variables de la capa general

| Tipo | n | Variables | Rol en FAMD |
|---|---|---|---|
| Cuantitativas | 3 | `edad`, `imc`, `horas_sedentarismo` | Cuantitativa |
| Binarias | 5 | `trabaja_actualmente`, `tiene_pareja`, `tiene_actividad_sexual`, `operada_no_mas_hijos`, `usa_medicamentos_presion` | Categórica |
| Nominal | 1 | `quien_prepara_comidas` | Categórica |
| Ordinales categóricas | 5 | `frecuencia_aerobico`, `frecuencia_bajo_impacto`, `frecuencia_fuerza`, `cantidad_personas_cuida`, `tabaco_frecuencia` | Categórica |
| Otras ordinales | 16 | `alcohol_frecuencia`, `carnes_semana`, `dias_ejercicio_semana`, `distension_abdominal`, `evacuacion_intestinal`, `falta_tiempo_influye`, `frecuencia_comida_fuera`, `frutas_dia`, `golosinas_semana`, `jugos_gaseosas_dia`, `lacteos_dia`, `legumbres_semana`, `panes_dia`, `pescado_semana`, `platos_verduras_dia`, `vasos_agua_dia` | Cuantitativa |

**No entran:** `lugar_trabajo_comprensivo`, `estres_entorno_laboral`, `sobrecarga_fisica_emocional`, `usa_medicamentos_diabetes`, `doble_carga`, `prevision`, `etapa_menopausica`, `cuida_otras_personas`, `realiza_*`, preguntas menstruales, MRS y severidad, consecuencias, identificadores y marcas de auditoría. Las preguntas `realiza_*` y `cuida_otras_personas` solo se leen como contexto, para decidir si una pregunta condicional aplicó.

# 6. Ruta PCA

| Tipo | Representación |
|---|---|
| Cuantitativa, ordinal y binaria | Una columna `(x − media) / DE` |
| Nominal | Cinco indicadoras `(I − p) / √Σp(1−p)`; varianza total 1 y distancia² igual entre categorías (4,1067) |

Tamaño: 34 columnas con IMC (P1) y 33 sin IMC (P2). La referencia sin reducción R0 usa estas mismas matrices.

# 7. Ruta FAMD

Las cuantitativas se estandarizan. Cada categoría se representa como `(I − p) / √p`, de modo que su varianza es 1 − p y cada variable aporta K − 1.

| Variable | Grupos finales (código original) |
|---|---|
| `frecuencia_aerobico` | 0 y 1 · 2 y 3 · 4 y 5 |
| `frecuencia_bajo_impacto` | 0 y 1 · 2 · 3 · 4 y 5 |
| `frecuencia_fuerza` | 0 y 1 · 2 y 3 · 4 y 5 |
| `cantidad_personas_cuida` | 0 · 1 · 2 · 3 |
| `tabaco_frecuencia` | 1 · 2, 3 y 4 · 5 |
| `quien_prepara_comidas` | YO_MAYORIA · COMPARTIDO · OTRA_HOGAR · COMPRO y OTRO |

Tamaño: 50 columnas con IMC (F1) y 49 sin IMC (F2).

**Condición de validez.** La transformación solo puede llamarse FAMD si supera la validación matemática con datos de prueba. El resultado está en el informe técnico. **Precisión sobre F1:** el IMC entra con varianza 0,5047, y no 1. Por tanto, F1 es una FAMD con peso reducido en el IMC, mientras que F2 es una FAMD estándar. Esta diferencia es deliberada y se validó con su propia comprobación.

# 8. IMC, cuidados y ejercicio

- **IMC:** 262 valores imputados quedan en z = 0. La marca no entra a ninguna matriz.
- **Cuidados:** cantidad = 0 es un nivel válido, no una ausencia, y no significa sobrecarga 0. 21 de esos ceros dependen de `cuida_otras_personas` imputada.
- **Ejercicio:** 29, 22 y 28 ceros dependen de una pregunta `realiza_*` imputada. Su unión son 75 participantes.

# 9. Procedencia

Cada celda de las 33 variables tiene uno de cinco estados: observada, deducida, imputada, no aplicable o faltante, más una marca de pregunta previa imputada. La tabla se guarda aparte: **ninguna marca entra a las matrices**.

# 10. Módulos y sensibilidades

**Módulos.** No forman clústeres, no se escalan y no alimentan el perfil general.

| Módulo | Principal | Sensibilidad |
|---|---|---|
| Laboral | 287 | 263 con ambas respuestas observadas |
| Cuidados | 239 con sobrecarga observada | 251 cuidadoras, con 12 imputadas |

`cantidad_personas_cuida` sigue entre las 30. `cuida_otras_personas` no vuelve como variable de agrupamiento.

**Sensibilidades.** Se preparan, no se ejecutan.

| ID | Factor | Preparación |
|---|---|---|
| S-ORD | Ridit en vez de códigos consecutivos | Matrices y parámetros en 4 rutas |
| S-FAMD | Las 5 ordinales categóricas pasan a cuantitativas | Matrices en 2 rutas (38 y 37 columnas) |
| S-RARA | FAMD sin agrupar categorías raras | Matrices en 2 rutas (58 y 57 columnas) |
| S-TRA | 22 con trabajo imputado | Ajuste 507 y proyección 22, en 4 rutas |
| S-CUI | 21 con cuidado imputado | Ajuste 508 y proyección 21, en 4 rutas |
| S-EJE | 75 con ceros de ejercicio heredados | Ajuste 454 y proyección 75, en 4 rutas |
| S-BLOQUE | Misma inercia total por bloque | Multiplicadores en `pesos_bloques.json` |
| S-EDAD, S-SOLAPE | Sin edad; sin dos variables con posible solape | Columnas a omitir, indicadas en el catálogo |

Las variantes B de «punto de quiebre» de S-TRA y S-CUI siguen siendo opcionales y no se prepararon.

# 11. Decisiones que siguen abiertas

| ID | Decisión | Cuándo |
|---|---|---|
| D-13 | Rango de clústeres, número de componentes, tamaño mínimo, estabilidad y cambio relevante | Antes de ejecutar la Fase 37 |
| D-09 | Límite de respuestas ausentes para asignar un perfil | Antes de la Fase 40 |
| D-15 | Agrupación de ítems de módulos en las reglas | Antes de las Fases 38 y 39 |

# 12. Reproducción y uso

```text
python fase36/construir_fase36.py
python fase36/validar_famd.py [--referencia CARPETA_CON_PRINCE]
python fase36/pruebas_fase36.py [--referencia CARPETA_CON_PRINCE]
python fase36/control_mutaciones.py
```

Flujo para una participante nueva: validar esquema → aplicar reglas condicionales → codificar con mapas guardados → completar con valores congelados y marcar → escalar con parámetros guardados → ordenar columnas → proyectar.

> Las referencias metodológicas (Pagès, 2004; Bross, 1958; Gower, 1971; Murtagh y Legendre, 2014) se citan de memoria: conviene verificarlas antes de incluirlas en la tesis.
