# Fase 36A: estrategia para PCA y FAMD

**Estado:** propuesta para revisión. No se ajustó PCA ni FAMD, y no se generaron matrices. La decisión por variable está en `matriz_decisiones_variables.csv` y la de cada nivel, en `diccionario_codificacion_fase36.csv`.

## 1. Composición de la capa general

| Tipo | Variables | Cuáles |
|---|---|---|
| Cuantitativas | 3 | `edad`, `imc`, `horas_sedentarismo` |
| Binarias | 5 | `trabaja_actualmente`, `tiene_pareja`, `tiene_actividad_sexual`, `operada_no_mas_hijos`, `usa_medicamentos_presion` |
| Nominal | 1 | `quien_prepara_comidas` |
| Ordinales | 21 | Las demás |

Más tres ordinales de módulo, que no entran a estas matrices: `lugar_trabajo_comprensivo`, `estres_entorno_laboral` y `sobrecarga_fisica_emocional`.

## 2. Ruta PCA

### Decisión por tipo

| Tipo | Representación | Motivo |
|---|---|---|
| Cuantitativa | Valor estandarizado | Escala real |
| Binaria | Una columna 0/1 estandarizada | Dos columnas serían redundantes |
| Nominal | 5 indicadoras centradas, divididas por `√Σ p(1−p)` | Sin orden; distancias iguales; varianza total 1 |
| Ordinal | Código en el orden del instrumento, estandarizado | Conserva el orden con una columna |

**Tamaño esperado:** 34 columnas con IMC y 33 sin IMC. Son las 29 columnas simples más las 5 indicadoras.

### Ordinales

| Opción | Evaluación | Resultado |
|---|---|---|
| **Códigos consecutivos** | Simple, reproducible y conserva el orden; supone pasos iguales | **Principal** |
| **Ridit** (punto medio acumulado de la referencia) | Conserva el orden; los pasos reflejan cuántas personas hay entre niveles; no depende de una distancia inventada | **Sensibilidad S-ORD** |
| One-hot | Pierde el orden, y agregaría decenas de columnas que dominarían la distancia | Rechazada |
| Puntos medios («1-2 veces» = 1,5) | Parece natural, pero exige inventar un valor para «7 o más porciones» y «Diariamente» | Rechazada |
| Correlación policórica | Supone una normal latente; poco directa con ceros estructurales y al transformar a una usuaria nueva | Rechazada |

**Limitación:** los códigos consecutivos no prueban que los niveles sean equidistantes. Si S-ORD cambia mucho los perfiles, la equidistancia no puede sostenerse y debe revisarse la ruta.

### Frecuencias de ejercicio (D-02)

El instrumento admite 1 = «Nunca», pero ninguna de las 529 participantes lo tiene. Quien no realiza el ejercicio queda vacío en el conjunto limpio y con 0 en la Fase 35. Así, los códigos observados son 0, 2, 3, 4 y 5, con un salto artificial.

**Recomendación:** usar el orden `No lo realiza = 0 < Rara vez = 1 < A veces = 2 < Frecuentemente = 3 < Siempre = 4`. Si «Nunca» llegara en la Fase 40, se une a «No lo realiza». No se agrega ninguna categoría nueva: es la misma escala, sin el salto.

`cantidad_personas_cuida` ya es consecutiva: 0, 1, 2 y 3.

### Categorías poco frecuentes

La codificación elegida para la nominal no amplifica las categorías raras, de modo que en PCA **no se agrupan**. Tampoco se agrupan los niveles ordinales raros, porque un código numérico único no les da peso adicional.

### Correlación

Las asociaciones son débiles: 424 de 435 pares están bajo |0,2| y solo 4 superan |0,4|. Tres incluyen `dias_ejercicio_semana` (con bajo impacto, aeróbico y fuerza) y el cuarto es `tiene_pareja` con `tiene_actividad_sexual`. Por esto:

- no se eliminan variables correlacionadas;
- PCA agrupará esa información en los primeros ejes, sobre todo la de ejercicio;
- los ejes explicarán poca varianza cada uno;
- **puede no existir una estructura de clústeres marcada**, y esa posibilidad debe informarse sin forzar el resultado.

### Compatibilidad euclidiana

Todas las columnas quedan en una escala comparable. Ward y K-means operan sobre esta distancia. La matriz sin reducción (R0) tiene la misma estructura, así que es comparable.

## 3. Ruta FAMD

### Regla por variable

FAMD trata una variable categórica por sus niveles, sin saber que tienen orden. **No conserva el orden automáticamente.** Por eso una ordinal solo pasa a categórica si hay un motivo:

1. Tiene un nivel estructural de «no realiza» o «no cuida», porque pasar a hacerlo es un cambio cualitativo: `frecuencia_aerobico`, `frecuencia_bajo_impacto`, `frecuencia_fuerza`, `cantidad_personas_cuida`.
2. Es bimodal, con dos modos de al menos 5 % separados por niveles menores: solo `tabaco_frecuencia` (Nunca 75,4 %, Diariamente 15,5 %).

Las otras 16 ordinales siguen como cuantitativas.

| Rol en FAMD | n | Variables |
|---|---|---|
| Cuantitativa | 19 | 3 cuantitativas y 16 ordinales |
| Categórica | 11 | 5 binarias, 1 nominal y 5 ordinales |

### Agrupación de niveles raros (solo en FAMD)

Las indicadoras se dividen por √p, de modo que una categoría rara pesa mucho: OTRO quedaría en 8,6. Regla determinista: mientras un nivel tenga menos de 5 %, se une al vecino menor; el nivel estructural no se une a otro.

| Variable | Niveles finales |
|---|---|
| `frecuencia_aerobico` | No realiza · Rara vez y A veces · Frecuentemente y Siempre |
| `frecuencia_bajo_impacto` | No realiza · Rara vez · A veces · Frecuentemente y Siempre |
| `frecuencia_fuerza` | No realiza · Rara vez y A veces · Frecuentemente y Siempre |
| `cantidad_personas_cuida` | 0 · 1 · 2 · 3 o más (sin cambios) |
| `tabaco_frecuencia` | Nunca · 1 a 6 veces por semana · Diariamente |
| `quien_prepara_comidas` | Yo · Compartido · Otra persona del hogar · Compro u otro |

La nominal no tiene vecinos, así que se unen sus dos categorías raras: COMPRO (4,2 %) y OTRO (1,3 %) suman 5,5 %. El 5 % es una convención de los análisis de correspondencias, no un resultado de estos datos: se contrasta con S-RARA. Las variables originales se mantienen intactas para caracterizar.

### Equilibrio

- Cada cuantitativa aporta inercia 1 (IMC: 0,505).
- Cada categórica aporta K − 1: una binaria aporta 1; una variable de 4 niveles, 3.
- Una categórica aporta más inercia total, pero en cada eje ninguna variable puede contribuir más de 1. Por eso FAMD equilibra por eje, no por total.

**Inercia total esperada:** 38,505 con IMC y 38 sin IMC.
**Tamaño esperado:** 50 columnas con IMC (19 cuantitativas y 31 indicadoras) y 49 sin IMC.

### Comprobar el orden

Después de ajustar, en la Fase 37, se revisa si las coordenadas de los niveles de cada ordinal categórica siguen su orden. Si no lo siguen, se informa como relación no lineal, sin corregirla.

### Implementación (D-12)

**Recomendación:** implementar la transformación como `(I − p)/√p` para indicadoras y z para cuantitativas, y aplicar después PCA de scikit-learn 1.6.1. Es la formulación de Pagès, permite transformar a una usuaria nueva con parámetros en JSON y no agrega dependencias: `prince` no está instalado.

## 4. Diferencias esperadas entre rutas

| Aspecto | PCA | FAMD |
|---|---|---|
| Ordinal con quiebre | Escala lineal | Niveles separados; capta relaciones no lineales |
| Orden | Se conserva por construcción | No está garantizado en las 5 categóricas |
| Categorías raras | No se amplifican | Pesan más; por eso se agrupan |
| Peso de la nominal | Total 1 | Inercia total 3 |
| Ejercicio y cuidado | Una dimensión de «cuánto» | Puede separar «hacer o no hacer» de «cuánto» |
| Inercia total | 29,505 | 38,505 |
| Interpretación | Cargas | Correlaciones, razones de correlación y coordenadas |

Con 16 ordinales iguales en ambas rutas, es esperable que coincidan en parte. Si dan perfiles muy distintos, la causa más probable son las cinco ordinales categóricas y conviene examinarlas con S-FAMD.

## 5. Compatibilidad con la Fase 37

| Algoritmo | PCA y FAMD | Referencia sin reducción |
|---|---|---|
| K-means | Sobre coordenadas | Sobre la matriz PCA de 34 columnas |
| Jerárquico aglomerativo | Ward sobre coordenadas | Ward sobre la misma matriz |

Solo es comparable una referencia euclidiana. **Gower con enlace promedio** (D-11) es una referencia adicional para datos mixtos: no sirve con K-means ni con Ward, porque estos requieren distancia euclidiana.

El número de componentes no se decide aquí. Debe fijarse antes de ejecutar la Fase 37.

### Asignación de una usuaria nueva

- **K-means:** centroide más cercano.
- **Aglomerativo:** no tiene `predict`. Se define con el centroide más cercano de los clústeres formados, y hay que informar cuánto concuerda esa regla con la asignación original.

## 6. Artefactos que deberá guardar la Fase 36B

Formato principal: **JSON con parámetros, no objetos serializados con pickle**, para que sobrevivan a un cambio de versión y sean revisables.

```text
analisis/fase36/artefactos/<escenario>/
  esquema_variables.json    variable, tipo, población, rol, niveles admitidos y significado
  orden_columnas.json       lista exacta de columnas de salida
  codificadores.json        mapa de cada nivel a su código, indicadora o grupo
  escaladores.json          media, DE y p de cada columna; referencia usada
  valores_desconocidos.json regla por variable para vacíos y niveles no admitidos
  procedencia.json          recuentos esperados de observadas, deducidas e imputadas
  entorno.json              versiones, semilla 42, commit y fecha
  huellas.json              SHA-256 de los archivos de entrada y de cada artefacto
```

### Valores desconocidos

| Caso | Regla propuesta |
|---|---|
| Nivel que el instrumento no admite | Error; no se asigna perfil |
| Nivel válido no observado | Se transforma normalmente (por ejemplo, `frutas_dia = 5`) |
| Pregunta no mostrada por condición | Nivel estructural (`realiza = NO` → 0; `cuida = NO` → 0) |
| IMC ausente | z = 0, con marca |
| Otra respuesta general ausente | Valor de referencia congelado, con marca y aviso. El límite de respuestas ausentes queda pendiente (D-09) |

### Flujo de la Fase 40

```text
respuestas → validar esquema → aplicar reglas condicionales → codificar con mapas guardados
→ completar con valores congelados y marcar → escalar con parámetros guardados
→ ordenar columnas → proyectar → asignar perfil → usar módulos solo si aplican
```

Los parámetros no se vuelven a ajustar al llegar una usuaria. Los módulos no alteran el perfil general: solo orientan las recomendaciones cuando corresponden.

## 7. Referencias metodológicas

- Pagès, J. (2004). Analyse factorielle de données mixtes. *Revue de Statistique Appliquée*, 52(4).
- Bross, I. D. J. (1958). How to use ridit analysis. *Biometrics*, 14(1).
- Gower, J. C. (1971). A general coefficient of similarity and some of its properties. *Biometrics*, 27(4).
- Murtagh, F., y Legendre, P. (2014). Ward's hierarchical agglomerative clustering method. *Journal of Classification*, 31.

Estas referencias se citan de memoria: conviene verificarlas antes de incluirlas en la tesis.
