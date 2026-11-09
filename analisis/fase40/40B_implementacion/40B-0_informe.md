# Fase 40B-0 — Limpieza histórica independiente de los modelos de Django

Fecha: 2026-11-06 · Rama `datos-simulados` · HEAD `44bfe0b` · Sin commit ni push.

## Resumen

La limpieza histórica (`analisis/limpieza`) ya no lee `src/apps/encuestas`. Ahora usa una
copia congelada y versionada de las definiciones (`analisis/limpieza/definiciones_fase34.py`).
Esa copia es idéntica a lo que la limpieza leía en las Fases 34 y 35, y se comprueba
con una huella SHA-256 cada vez que se carga.

Las seis salidas CSV de la limpieza regeneradas son idénticas byte a byte a las
históricas. Las 15 pruebas nuevas y las 143 pruebas existentes que se ejecutaron pasan.
Django, los datos y las Fases 34 a 39 no cambiaron.

---

## 1. Dependencia encontrada

`analisis/limpieza/catalogo.py` leía en vivo cuatro archivos de la plataforma. Cada
ejecución de `reglas.limpiar()` los volvía a leer:

| Archivo de Django | Cómo se leía | Qué aportaba a la limpieza |
|---|---|---|
| `models.py` | `ast` (sin importarlo) | 130 campos con su modelo, tipo y opciones `{código: etiqueta}`; `MRS.SEVERIDAD_TOTAL` (cortes del MRS) |
| `condicionales.py` | `runpy` (lo **ejecutaba**) | `PREGUNTAS_CONDICIONALES` y `SECCIONES_CONDICIONALES` |
| `campos_por_rol.py` | `runpy` (lo ejecutaba) | `SOLO_PROFESIONAL` (14 campos) |
| `datos_geograficos.py` | `runpy` (lo ejecutaba) | `COMUNAS_POR_REGION` (17 regiones, 346 comunas) |

En la práctica, cualquier cambio en estos archivos alteraba la limpieza de la
Fase 34 sin dejar rastro. Por ejemplo:

- una etiqueta nueva;
- un código renombrado;
- otro corte del MRS;
- un campo profesional agregado.

Además había un riesgo de fallo: una clase de opciones con nombre repetido en
`models.py` hacía que la limpieza se detuviera con `ValueError`.

**Qué se usa realmente.** De los 130 campos del catálogo, la limpieza toca 126: los
que son columnas del conjunto. Pertenecen a 11 modelos y 87 tienen opciones. Los
otros 4 campos (`usuario`, `participante`, `respondida_en`, `actualizada_en`) no
son columnas del conjunto.

Igual se congeló el catálogo completo, por dos razones:

- es exactamente lo que se leía;
- otros scripts históricos también lo consumen con `leer_modelos()`:
  - `eda_completo.py`, `eda_univariado.py`, `eda_usuaria.py`;
  - `preprocesar_fase35.py`;
  - `fase36/pruebas_fase36.py`;
  - `fase36_diseno/.../generar_tablas_diseno.py`;
  - `cierre_fases_34_35/.../test_h11_h13.py`.

Si se recortaba el catálogo, `campos.get(c)` cambiaría de resultado para esos scripts.

**Versión de origen.** Los cuatro archivos no cambian desde el 2026-10-01 o antes:

| Archivo | Último cambio |
|---|---|
| `models.py` | `32c399d` |
| `condicionales.py` | `ac1c49b` |
| `campos_por_rol.py` | `6c70527` |
| `datos_geograficos.py` | `a563d66` |

Esas fechas son anteriores a la limpieza de la Fase 34B (`32b439c`, 2026-10-24) y a las
salidas en `datos/limpio*` (2026-10-23 y 2026-10-24). Además, el árbol de trabajo
coincide con HEAD. Por lo tanto, la versión de `44bfe0b` es la que usó la Fase 34.

## 2. Solución y por qué

**Qué se hizo:**

- **Copia congelada como literales de Python** (`definiciones_fase34.py`, `VERSION = 'fase34-v1'`).
  - Contiene las seis definiciones exactas.
  - Registra el commit de origen y la SHA-256 de cada archivo fuente.
  - Registra una huella del contenido (`HUELLA_CONTENIDO = 209f52df…1205`).
  - Se eligió Python y no JSON porque JSON convierte las claves enteras (`{1: 'Nunca'}`) en texto y las tuplas en listas. Eso cambiaría los códigos.
- **`catalogo.py`:** `leer_modelos()`, `leer_condicionales()`, `leer_solo_profesional()` y `leer_comunas()` mantienen su nombre y sin argumentos devuelven lo mismo, pero ahora leen la copia congelada.
  - Antes de devolverla verifican la huella. Si alguien edita el archivo a mano, la limpieza se detiene con `RuntimeError`.
  - Entregan copias (`deepcopy`), así nadie puede alterar la definición en memoria.
  - Por eso no hubo que tocar `reglas.py`, `informe.py`, `limpiar_dataset.py` ni ningún script dependiente.
- **Lectura de la plataforma solo para auditoría.** La lectura antigua quedó como `leer_*_plataforma(ruta)` y `leer_plataforma(directorio)`.
  - Ahora acepta cualquier ruta, para comparar contra una copia o un commit.
  - La limpieza ya no la llama. Así, ni `ast.parse` ni `runpy` se ejecutan sobre Django al limpiar.
- **Generador de una sola vez** (`congelar_definiciones_fase34.py`):
  - extrae los cuatro archivos con `git show 44bfe0b:` (no del árbol de trabajo);
  - los lee en un directorio temporal y escribe la copia congelada;
  - se niega a sobrescribirla;
  - con `--verificar` solo comprueba que el archivo coincide.

**Por qué así:**

- Se cambió lo mínimo dentro de `analisis/limpieza`: un archivo modificado y uno nuevo.
- La interfaz pública es la misma.
- La procedencia queda documentada y verificable.
- Cuando la plataforma cambie, la limpieza histórica no la sigue. Una limpieza nueva necesitará otra versión congelada con su propio nombre.

## 3. Archivos nuevos o modificados

| Archivo | Estado | Contenido |
|---|---|---|
| `analisis/limpieza/catalogo.py` | modificado | lectura congelada con huella y lectura `*_plataforma` para auditoría |
| `analisis/limpieza/definiciones_fase34.py` | nuevo, generado | las seis definiciones, procedencia y huellas (926 líneas) |
| `analisis/fase40/40B_implementacion/scripts/congelar_definiciones_fase34.py` | nuevo | generador y verificador |
| `analisis/fase40/40B_implementacion/pruebas/test_40b0_definiciones.py` | nuevo | 15 pruebas |
| `analisis/fase40/40B_implementacion/40B-0_informe.md` | nuevo | este informe |

No se modificaron:

- `reglas.py`, `informe.py`, `evaluacion.py`, `limpiar_dataset.py`;
- Django, migraciones ni la base de datos;
- los datos;
- las Fases 35 a 39;
- los dos informes de la Fase 40A.

Las fotos de verificación quedaron fuera del repositorio, en
`C:\Users\scarl\AppData\Local\Temp\claude\c9607f9123dc8896\849f5933-394c-45ea-9b3d-3ba961ee9b2f\scratchpad\40b0`
(subcarpetas `antes\` y `despues\`).

## 4. Cómo se compararon las definiciones

1. **Forma canónica estricta.** `catalogo._canonico` convierte cada definición en una estructura que conserva:
   - el orden de las claves;
   - el tipo de cada valor: entero o texto, tupla o lista, conjunto.

   Sobre eso se calcula la SHA-256. Así, un `1` y un `'1'` no se confunden, ni un reordenamiento pasa inadvertido.
2. **Comparación con la plataforma actual:** idéntica.
3. **Comparación con la plataforma en tres commits** (extraídos con `git show` a temporales): idéntica en los tres.
   - `32b439c`: Fase 34B, limpieza del conjunto de la usuaria;
   - `745d689`: Fase 35B;
   - `44bfe0b`: respaldo.
4. **Campo a campo.** Para los 130 campos coinciden el modelo, el tipo y cada par (tipo del código, código, etiqueta), en el mismo orden.
5. **Cortes del MRS:** `((4, 'Sin síntomas o muy leves'), (8, 'Leve'), (15, 'Moderada'), (44, 'Severa'))`, es decir 0-4 / 5-8 / 9-15 / 16-44.
   - Además se comprobó que cada `mrs_severidad` de `datos/limpio_usuaria/dataset_usuaria_limpio.csv` corresponde a su `mrs_total` con esos cortes.
6. **Foto antes y después.** La representación completa de las seis definiciones tiene la misma SHA-256 con el código anterior y con el nuevo: `b905837c…a1d`.

**Nota sobre las huellas de origen.** Git guarda los archivos con fin de línea LF y la copia de
trabajo de Windows usa CRLF. Por eso hay dos huellas distintas para `models.py`, aunque el contenido es el mismo:

- en git (la registrada): `cc53575a…3f16`;
- en disco: `aeb1fded…f78`.

## 5. Pruebas ejecutadas y resultados

**Pruebas nuevas:** `python -m unittest analisis/fase40/40B_implementacion/pruebas/test_40b0_definiciones.py`. Resultado: **15/15 OK**.

| Grupo | Pruebas |
|---|---|
| Definiciones idénticas | huella registrada; igual a la plataforma actual; igual a 3 commits; huellas de origen; el generador reproduce el archivo |
| Códigos y cortes | cortes del MRS; categorías históricas siguen los cortes; tamaños (130 campos, 14 profesionales, 346 comunas); códigos y etiquetas campo a campo; un archivo alterado se detecta; las copias son independientes |
| Independencia | una copia **temporal modificada** de la plataforma no cambia la limpieza; la limpieza no toca la plataforma ni la verdad |
| Reproducción | salidas idénticas a las históricas; `src/` sin cambios |

**Copia temporal modificada.** Se copiaron los cuatro archivos a un temporal y se alteraron:

- en `models.py`: corte Moderada 15 → 12 y etiqueta «Leve» → «Leve (modificada)»;
- en `campos_por_rol.py`: un campo profesional nuevo.

Con esa copia:

- `leer_plataforma()` sí cambia;
- aun con `catalogo.ENCUESTAS` apuntando al temporal, la huella congelada y las tres salidas de la limpieza siguen idénticas a las históricas;
- el `models.py` real quedó intacto (SHA-256 verificada).

**Sin acceso a la plataforma ni a la verdad.** Durante `limpiar()` se bloquearon `runpy.run_path` y `ast.parse`, y se registraron todos los `open`:

- ningún archivo abierto está en `src/apps`;
- ninguno contiene «verdad» ni «bitacora»;
- Django no se importó.

**Pruebas existentes que consumen el catálogo** (en memoria o en temporales):

| Prueba | Resultado |
|---|---|
| `cierre_fases_34_35/scripts/test_h11_h13.py` | 21/21 OK |
| `preprocesamiento/test_revision_35b.py` | 43/43 OK |
| `preprocesamiento/test_entropia.py` | 79/79 OK |
| `preprocesamiento/test_informe_word_33.py` | 11 omitidas: falta `python-docx`; no depende de esta fase |

**No se ejecutó `fase36/pruebas_fase36.py`**, porque escribe en `fase36/pruebas/` y sobrescribiría archivos históricos. Recibe exactamente las mismas definiciones (punto 4), así que su resultado no puede cambiar por esta fase.

## 6. Equivalencia de la reproducción

`limpiar()` se ejecutó con el código anterior (foto «antes») y con el nuevo (foto «después»).

- Se usó solo el archivo **sucio** de cada conjunto.
- No se ejecutó `limpiar_dataset.py`, porque este carga automáticamente la verdad y la bitácora si están junto a la entrada.
- Todo se escribió en el scratchpad.

| Salida | SHA-256 | Antes = después = histórico |
|---|---|---|
| `limpio_usuaria/dataset_usuaria_limpio.csv` | `4ecfd516…5fd1` | sí, byte a byte |
| `limpio_usuaria/excluidas.csv` | `bddfe415…8d8f` | sí |
| `limpio_usuaria/diccionario_variables.csv` | `2495c9f2…3be1` | sí |
| `limpio/dataset_menopausia_limpio.csv` | `2678c4f6…8853` | sí |
| `limpio/excluidas.csv` | `3e37031a…bb95` | sí |
| `limpio/diccionario_variables.csv` | `6c54db94…e53d` | sí |
| Informe Markdown sin evaluación (cada conjunto) | `67f70dcd…` / `0a54357c…` | antes = después (sin diferencias en todo el directorio) |

**Informes históricos.** Los informes Markdown no se pueden comparar con su versión histórica:

- `informe_limpieza_usuaria.md` incluye la evaluación contra la verdad, que esta fase no puede leer.
- `informe_limpieza.md` es del 2026-10-18, anterior a la Fase 34B, y ya no correspondía al código. No tiene que ver con 40B-0.

Por eso, para los informes la comparación válida es antes contra después.

Ninguno de los dos informes históricos se modificó.

## 7. Django intacto

- `git status --porcelain -- src` está vacío.
- Las SHA-256 de los cuatro archivos de `src/apps/encuestas` son iguales antes y después.
- No hay migraciones ni cambios en la base de datos.
- Django no está instalado en este entorno y nunca se importó.

## 8. Fases 34 a 39 intactas

`git status` muestra solo:

- `M analisis/limpieza/catalogo.py`;
- `?? analisis/limpieza/definiciones_fase34.py`;
- `?? analisis/fase40/`.

Además:

- **Datos:** no hay cambios en archivos versionados de `datos/` ni en los informes de limpieza. `datos/limpio/`, que no está versionado, tiene las mismas SHA-256.
- **Modelos:** no se recalculó PCA, K-means, Random Forest ni reglas de asociación.
- **Fase 40A:** los dos informes conservan sus huellas:
  - `informe_fase40A.md`: `185c83ae…017a`;
  - `01_revision_correctiva_40A.md`: `78628e74…d8f5`.

## 9. Riesgos metodológicos pendientes

1. **Texto del informe de limpieza desactualizado.** `informe.py` dice que los códigos «se leen del código de la plataforma (`models.py`, …)». No se cambió, para que los informes sigan siendo idénticos. Si el informe se regenera, conviene actualizar esa frase para citar `definiciones_fase34.py`. Es un cambio de texto que cambiaría la huella del informe.
2. **Otras lecturas directas de `models.py` fuera de la limpieza.** Siguen en las Fases 35 a 39 y no se tocaron por la restricción:
   - `preprocesamiento/test_revision_35b.py:245` lee el texto con expresiones regulares;
   - `revision_35b_reunion_1103.py` también lo lee;
   - `fase38/.../integridad_38.py` y `fase39/.../integridad_39.py`, `pruebas_39.py` comparan la huella de `models.py`.

   Si la plataforma cambia, esas pruebas fallarán o leerán otra cosa. Habría que pasarlas a la copia congelada en una fase autorizada.
3. **La copia congelada no sigue a la plataforma, a propósito.** Los datos nuevos que lleguen con otro cuestionario deben limpiarse con una versión nueva (por ejemplo, `fase40-v1`), comparándola explícitamente con `leer_plataforma()`. Si no, se arriesga aplicar códigos viejos a datos nuevos.
4. **La huella protege contra errores, no contra mala fe.** Quien edite el archivo y recalcule `HUELLA_CONTENIDO` pasará la verificación. La protección real es el control de versiones y el generador `--verificar`, que reconstruye desde git.
5. **Evaluación contra la verdad no reverificada.** La sección del informe de la usuaria que compara con la verdad del simulador no se volvió a generar, porque esta fase no puede leer la verdad. Como las salidas CSV son idénticas, esa evaluación no puede haber cambiado.
6. **Pruebas sin ejecutar:**
   - `fase36/pruebas_fase36.py`, porque escribe en carpetas históricas;
   - `test_informe_word_33.py`, porque falta `python-docx`.

## 10. ¿Está completa la Fase 40B-0?

**Sí.** La limpieza histórica ya no depende de `models.py` ni de los otros tres archivos de Django:

- usa una definición congelada, versionada y verificable;
- las categorías, los códigos, las etiquetas y los cortes del MRS son idénticos a los de la Fase 34;
- las salidas son las mismas byte a byte;
- todas las pruebas ejecutadas pasan.

**Pendiente:**

- la revisión de la usuaria;
- la decisión de commit;
- autorizar o no las siguientes fases (40S-1 o 40B-1).

No se inició ninguna otra fase.
