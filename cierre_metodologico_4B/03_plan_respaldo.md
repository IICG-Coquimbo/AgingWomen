# Etapa 4B · Documento 03 · Plan de respaldo de 38R y 39R

**Fecha:** 2026-11-09 · **Rama:** `datos-simulados` · **HEAD:** `573d3a31100c03519d47e220f4a065df3e9caf9a`

> **Este plan no se ha ejecutado.** No se creó ningún ZIP, copia externa, repositorio, `.gitattributes`, commit ni push. Cada paso de la sección D requiere autorización expresa.

**Motivo.** Las carpetas 38R y 39R no están bajo control de versiones (hallazgo H-01 de la Etapa 4A). Hoy existen solo en este equipo.

| Abreviatura | Ruta |
|---|---|
| `38R/` | `analisis/fase38/38R_reglas_asociacion_corregidas/` |
| `39R/` | `analisis/fase39/39R_asociaciones_condicionadas_corregidas/` |

**Origen del inventario.** Solo metadatos (nombre, tamaño y fecha) y `git`. No se calcularon huellas nuevas.

---

## A. Inventario

### A.1 Resumen

| Carpeta | Archivos | Tamaño | Mayor archivo | Ruta más larga |
|---|---|---|---|---|
| 38R, sin `node_modules` | 330 | 117,03 MB | `reglas_S3-bajo.csv`, 15,24 MB | 145 caracteres |
| 39R | 1.570 | 301,14 MB | `reglas/reglas_todos_estratos.csv`, 33,66 MB | 159 caracteres |
| **Total** | **1.900** | **≈ 418 MB** | | |

Además, `38R/documentos_definitivos/herramientas_word/node_modules/` tiene 235 archivos y 22,89 MB. Está ignorado por el `.gitignore` de `herramientas_word/` (comprobado con `git check-ignore`).

### A.2 Por categoría

| # | Categoría | 38R (archivos / MB) | 39R (archivos / MB) |
|---|---|---|---|
| 1 | **Necesarios para conservar resultados** | `reglas` 12 / 8,18 · `comparacion` 14 / 1,49 · `estabilidad` 3 / 2,8 · `referencia_nula` 11 / 0,1 · `sensibilidades` 185 / 94,51 | `reglas` 13 / 66,63 · `comparacion` 51 / 3,21 · `estabilidad` 18 / 6,41 · `referencia_nula` 100 / 0,91 · `sensibilidades` 1.140 / 205,82 · `resultados` 1 · `redundancia` 2 / 7,59 |
| 2 | **Protocolos y registros de integridad** | `protocolo` 2 / 0,01 · `integridad` 11 / 1,72 · `preparacion` 18 / 1,23 · `documentos_definitivos/validacion` | `protocolo` 3 / 0,01 · `integridad` 10 / 2,19 · `preparacion` 28 / 0,71 · `documentos_definitivos/validacion` |
| 3 | **Scripts y dependencias** | `scripts` 12 / 0,09 · `pruebas` 3 / 0,01 · `documentos_definitivos/scripts` · `herramientas_word` sin `node_modules` | `scripts` 14 / 0,12 · `pruebas` 3 / 0,02 · `documentos_definitivos/scripts` |
| 4 | **Tablas, figuras e informes** | `informes` 1 / 0,01 · `documentos_definitivos/{figuras,fuentes,word}` y su informe. Total de `documentos_definitivos`: 58 / 6,88 | `informes` 1 / 0,02 · `ab1` 117 / 4,21 · `comparacion_historica` 21 / 0,07 · `exploratorio_posterior_al_sello` 2 / 0,59 · `documentos_definitivos/{figuras,fuentes,word}` y su informe. Total de `documentos_definitivos`: 46 / 2,62 |

**Por extensión**

| Extensión | 38R | 39R |
|---|---|---|
| csv | 94 / 111,43 MB | 227 / 292,06 MB |
| npz | 160 / 0,81 MB | 1.277 / 6,4 MB |
| docx | 14 / 2,6 MB | 16 / 1,58 MB |
| png | 8 / 1,45 MB | 6 / 0,71 MB |
| py | 17 / 0,21 MB | 16 / 0,19 MB |
| md | 18 / 0,13 MB | 20 / 0,16 MB |
| json | 14 / 0,05 MB | 8 / 0,04 MB |
| txt | 2 / 0,35 MB | no se registró |

### A.3 Temporales o excluibles (sin eliminar nada)

| Elemento | Cantidad | Recomendación |
|---|---|---|
| `node_modules` | 235 archivos / 22,89 MB | **Excluir.** Se regenera con `npm ci` a partir de `package-lock.json` |
| `__pycache__` | 0 | No aplica |
| Temporales (`~$`, `.tmp`, `.bak`, `.log`) | 0 | No aplica |
| Lotes `.npz` de control (`sensibilidades/lotes*`, `referencia_nula/lotes`) | ≈ 7,2 MB en total | **Conservar.** Ocupan poco y permiten retomar y auditar las ejecuciones |

### A.4 Tamaño para Git

| Control | Resultado |
|---|---|
| Archivos > 25 MB | 1 (`reglas_todos_estratos.csv`, 33,66 MB) |
| Archivos > 50 MB (GitHub advierte) | 0 |
| Archivos > 100 MB (GitHub rechaza) | 0 |
| Git LFS | No es necesario por tamaño |
| Tamaño actual del repositorio (`git count-objects`) | 147,72 MiB empaquetados |
| Crecimiento previsto | Hasta ≈ 418 MB sin comprimir. Con compresión debería ser menor, pero la cifra **no se verificó** |
| Longitud de rutas | Máximo 159 caracteres relativos. `core.longpaths` no está definido, así que conviene clonar en una ruta raíz corta (Windows limita a 260) |

### A.5 Relación con las fases históricas

| Dependencia | Detalle |
|---|---|
| 38R → Fase 38 histórica | `nucleo_38r.py` importa `algoritmos_38`, `evaluacion_38` y `nucleo_38`. `38R/integridad/archivos_leidos.csv` lista 34 archivos, todos rastreados y sin modificar |
| 39R → 38R, 38 y 39 | `nucleo_39r.py` carga los scripts de las tres. **39R depende de 38R, que no está rastreada: hay que incorporar 38R antes o junto con 39R** |
| 39R → registros de lectura | `39R/integridad/archivos_leidos.csv` tiene 5.351 entradas. 19 no están rastreadas: 4 de 38R y 15 de `src/`, pendientes de la Fase 40. Además, hay 13 archivos de `src/` modificados. Probablemente proceden de un control de integridad amplio y no de una dependencia analítica, pero eso **no se verificó** |
| Archivos en Git hoy | `fase36` 259 · `fase37` 2.263 · `fase38` 276 · `fase39` 1.544 · `datos` 511 |

---

## B. Riesgos que el procedimiento debe resolver

### B.1 Finales de línea y huellas selladas (alta)

`core.autocrlf=true` y no hay `.gitattributes`. Los protocolos de 38R y 39R están en LF (`w/lf`).

**Consecuencia.** Un clon nuevo en Windows con esa configuración convertiría LF en CRLF. Los SHA-256 de los protocolos sellados dejarían de coincidir, aunque el contenido no hubiera cambiado.

| Clase de fin de línea | 38R | 39R |
|---|---|---|
| Binario (`-text`) | 182 | 1.299 |
| LF | 143 | 266 |
| CRLF | 4 | 4 |
| Sin fin de línea | 1 | 1 |

Los cuatro CRLF de cada carpeta están en `documentos_definitivos/validacion/`.

| Opción | Efecto | Valoración |
|---|---|---|
| `.gitattributes` con `* -text` dentro de `38R/` y `39R/`, añadido **antes** del `git add` | Git guarda y restaura byte a byte, también con `autocrlf=true` | **Recomendada** |
| Solo `core.autocrlf=false` al clonar | Funciona, pero depende de recordarlo en cada clon | Complementaria |
| Comparar huellas normalizando finales de línea | Evita falsos errores, pero no conserva los bytes | No recomendada |

Los protocolos históricos ya rastreados tienen el mismo riesgo en un clon nuevo. Para verificarlos, se debe clonar con `core.autocrlf=false`. Este plan no los toca.

### B.2 Rutas de secretos en registros (media)

- No hay archivos `.env*` dentro de 38R ni de 39R, ni rutas absolutas `C:\Users`.
- `38R/documentos_definitivos/validacion/huellas_final.csv` registra `.env` y `.env.desarrollo` con su SHA-256. Es una huella, no el contenido, pero queda ligada a un archivo con secretos.
- Las coincidencias de `SECRET_KEY` y `password` en otros registros son nombres de plantillas o menciones en informes («rotación de `SECRET_KEY`»). La revisión de valores **no se hizo de forma exhaustiva**.

**La decisión corresponde a la responsable (R-3).** Alterar ese registro rompería la correspondencia con la validación documental. Las alternativas están en la sección E.

### B.3 Manifiesto incompleto (media)

`38R/documentos_definitivos/validacion/huellas_final.csv` cubre 272 archivos de 38R y 1.524 de 39R. Las diferencias con el inventario (58 y 46) coinciden con el número de archivos de `documentos_definitivos` de cada carpeta. La coincidencia es de recuento; **no se comprobó por ruta**. Falta, por tanto, un manifiesto de los documentos definitivos.

---

## C. Criterios del procedimiento

| Requisito | Cómo se cumple |
|---|---|
| Verificar integridad | Manifiesto SHA-256 antes de incorporar; comparación con un clon limpio |
| Mantener rutas y dependencias | Mismas rutas relativas; 38R antes o junto con 39R |
| No mezclar pendientes de Fase 40 | `git add` solo con las rutas exactas de las carpetas; nunca `-A` ni `.` |
| Excluir vedados | Están fuera de 38R y 39R. El recorrido no los incluye, y los manifiestos excluyen esos nombres por lista |
| Evitar secretos | Excluir `.env*`; revisar coincidencias antes del commit |
| Datos sensibles | Según sus informes, los datos son sintéticos. No se revisó archivo por archivo: incluir en la verificación previa |
| Incorporación controlada | Pasos separados, cada uno con autorización |

---

## D. Procedimiento propuesto (no ejecutado)

**Todos los pasos requieren autorización expresa.** Rama de trabajo: `datos-simulados`.

| Paso | Acción | Criterio para continuar |
|---|---|---|
| 0 | Confirmar rama, HEAD e índice vacío: `git diff --cached --quiet`. Registrar `git status --porcelain` | Índice vacío; rama y HEAD esperados |
| 1 | Generar un manifiesto SHA-256 de `38R/` y `39R/`, sin `node_modules` y con la lista de exclusión | Número de archivos igual a 330 y 1.570, salvo cambios justificados |
| 2 | Revisar secretos y datos sensibles en ambas carpetas. Aplicar la decisión R-3 | Sin secretos; sin datos personales |
| 3 | Crear `.gitattributes` con `* -text` en `38R/` y `39R/`, si se aprueba R-1 | Archivos nuevos y limitados a esas carpetas |
| 4 | `git add -- <38R>` y, por separado o después, `git add -- <39R>` | `git diff --cached --name-only` solo lista esas carpetas; 0 en `src/`, `auditoria_*` y `cierre_metodologico_4B`; 0 `node_modules` |
| 5 | **Mostrar el mensaje exacto del commit** y esperar aprobación. Sin línea `Co-Authored-By` | Aprobación de la usuaria |
| 6 | Commit de 38R y luego de 39R, o uno conjunto si así se decide (R-2) | HEAD nuevo registrado |
| 7 | Comprobar que los pendientes de Fase 40 siguen igual | Únicas diferencias: las carpetas incorporadas |
| 8 | Clonar en una ruta temporal corta y comparar con el manifiesto del paso 1 | 100 % de coincidencia byte a byte; 13 de 13 sellos correctos |
| 9 | Push a `origin/datos-simulados`, solo con aprobación aparte | Remoto actualizado; sin advertencias de tamaño |
| 10 | Copia externa, si se decide (R-5), con el manifiesto incluido | Huellas verificadas en destino |

**Separaciones obligatorias.** `auditoria_tesis_v9/`, `auditoria_metodologica_final/` y `cierre_metodologico_4B/` quedan fuera de los commits de 38R y 39R. La Fase 40 tampoco entra. Si la responsable desea respaldarlos, se tratan en commits separados.

**Reversión.** Si falla el paso 8 antes del push, se corrige en local sin destruir archivos de trabajo. Cualquier deshacer con `reset` u otra operación de Git se consultará antes.

---

## E. Decisiones necesarias antes de ejecutar

| Id | Decisión | Recomendación |
|---|---|---|
| R-1 | ¿Agregar `.gitattributes` con `* -text` en 38R y 39R? | Sí |
| R-2 | ¿Un commit por carpeta o uno conjunto? | Uno por carpeta, 38R primero |
| R-3 | ¿Qué hacer con la huella de `.env` y `.env.desarrollo` en el registro de validación? | Revisarla y decidir entre (a) mantenerla, porque es un hash y no contiene el secreto; o (b) dejar ese archivo fuera de Git y conservarlo solo en copia privada. La opción (a) mantiene la cadena de validación completa, siempre que `SECRET_KEY` se rote como ya está previsto en la Fase 40 |
| R-4 | ¿Conservar los lotes `.npz`? | Sí |
| R-5 | ¿Hacer copia externa además de Git? ¿En qué destino? | Sí, una copia privada; el destino lo define la responsable |
| R-6 | ¿Autorizar el push a GitHub? El repositorio remoto es de una organización | Decisión de la responsable, una vez verificado el clon |
