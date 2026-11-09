# Etapa 5B-1 — Informe de respaldo previo a las pruebas finales

**Fecha:** 2026-11-09 · **Rama:** `datos-simulados` · **HEAD:** `573d3a31100c03519d47e220f4a065df3e9caf9a`

**Resultado: respaldo completo y verificado.** Se copiaron 2.034 archivos (446.163.899 bytes, 425,49 MB) y las 2.034 huellas SHA-256 coinciden entre origen y copia. No hubo commits ni pushes, y no se modificó ningún archivo existente.

---

## A. Alcance del respaldo

| Incluido | Criterio |
|---|---|
| `analisis/fase38/38R_reglas_asociacion_corregidas/` | Carpeta completa, sin `node_modules` |
| `analisis/fase39/39R_asociaciones_condicionadas_corregidas/` | Carpeta completa |
| Pendientes de la Fase 40 | Según `git ls-files -m` y `git ls-files -o --exclude-standard`, limitados a `src/`, `analisis/fase40/`, `README.md` y `docker-compose.yml` |

No se incorporó el resto del repositorio. La copia se hizo byte a byte, sin transformar finales de línea, y conserva la fecha de modificación de cada archivo.

---

## B. Ubicación de destino

`C:\Users\scarl\Respaldos_AgingWomen\2026-11-09_etapa5B1\`

| Comprobación previa | Resultado |
|---|---|
| Fuera del repositorio y de los directorios de trabajo | Sí |
| Fuera de OneDrive | Sí |
| Carpeta real, sin enlace simbólico ni punto de unión | Sí |
| Antecedente | Es la carpeta privada ya usada en las Fases 40B-1 y 40B-2 |
| Permisos | Solo SYSTEM, Administradores y la cuenta `scarl` |
| Sin sobrescritura | Subcarpeta nueva. El script falla si la carpeta o un archivo ya existen |
| Respaldos anteriores | Los 4 archivos existentes conservan nombre, tamaño y fecha |

**Estructura**

| Carpeta | Contenido |
|---|---|
| `38R/` | 38R, sin los dos registros separados |
| `39R/` | 39R |
| `FASE40/` | Pendientes de la Fase 40 |
| `REGISTROS_CON_HUELLAS_SECRETOS/` | Registros de validación separados (sección D.2) |
| `MANIFIESTO/` | Manifiesto SHA-256, su huella, exclusiones, estado de Git inicial y verificación |

Dentro de cada carpeta se mantiene la ruta relativa al repositorio.

---

## C. Inventario de archivos

| Bloque | Archivos | Bytes | MB |
|---|---|---|---|
| 38R | 328 | 120.144.779 | 114,58 |
| Registros separados de 38R | 2 | 2.571.658 | 2,45 |
| 39R | 1.570 | 315.769.043 | 301,14 |
| Fase 40 | 134 | 7.678.419 | 7,32 |
| **Total** | **2.034** | **446.163.899** | **425,49** |

38R y 39R suman 330 y 1.570 archivos, las cifras previstas en el plan de la Etapa 4B. El recorrido de esas carpetas coincide exactamente con lo que Git ve como no rastreado.

**Detalle de la Fase 40**

| Grupo | Archivos |
|---|---|
| `src/` | 87 |
| `analisis/fase40/` | 45 |
| `README.md` y `docker-compose.yml` | 2 |
| *De ellos, modificados / nuevos* | *33 / 101* |

**Por tipo (total):** 1.437 `.npz`, 321 `.csv`, 95 `.py`, 59 `.md`, 32 `.json`, 30 `.docx`, 29 `.png`, 20 `.html`, 4 `.js`, 2 `.txt` y 5 de otros tipos. No hay enlaces simbólicos ni archivos de base de datos, volcados o claves.

---

## D. Exclusiones

### D.1 Excluidos de la copia

| Elemento | Motivo |
|---|---|
| Los cuatro archivos protegidos | Instrucción vigente. Están fuera de las rutas respaldadas; además, el script los rechaza por nombre. No se abrieron |
| Archivos `.env` y `.env.*` | Instrucción vigente. No se abrieron |
| `.env.example` | Aplicando la misma regla, aunque es una plantilla y tiene cambios pendientes. Ver sección G |
| `node_modules` de `herramientas_word` | Se regenera desde `package-lock.json`. La carpeta no se recorrió |
| `__pycache__` | Archivos generados |

**Comprobación en destino:** 0 archivos protegidos, 0 `.env*` y 0 `node_modules`.

### D.2 Registros conservados por separado

Dos registros de `38R/documentos_definitivos/validacion/` asocian huellas SHA-256 a `.env` y `.env.desarrollo`. Están únicamente en `REGISTROS_CON_HUELLAS_SECRETOS/`, y no en `38R/`. Los originales siguen intactos en el repositorio.

Esta separación afecta solo al respaldo. La decisión R-3 del plan, sobre qué hacer con ellos en Git, sigue pendiente.

### D.3 Revisión de secretos y datos personales

La revisión se hizo por patrones sobre los archivos de texto, sin mostrar valores.

| Revisión | Resultado |
|---|---|
| URL con clave, claves privadas y tokens | 0 |
| Prefijo `django-insecure-` | 2 líneas de `test_seguridad_config.py`: una búsqueda y un valor generado al azar. Ninguna contiene una clave |
| Asignaciones de clave con valor literal | 9 candidatas, todas en archivos de prueba; 0 fuera de ellos |
| RUT con formato, fuera de pruebas | 12 apariciones en 8 archivos, todas con forma evidente de ejemplo |
| Correos no ficticios | 1 dirección en `settings.py`; no es una credencial |

**Límite:** los archivos `.docx`, `.png` y `.npz` no se revisaron por contenido. Esta revisión tampoco demuestra la ausencia absoluta de datos sensibles.

---

## E. Resultado de la verificación de integridad

| Comprobación | Resultado |
|---|---|
| Archivos con huella distinta entre origen y copia | **0 de 2.034** |
| Diferencias de tamaño | 0 |
| Origen modificado durante la copia (tamaño, fecha y huella releída) | 0 |
| Fecha de modificación distinta en la copia | 0 |
| Archivos de más o de menos en destino | 0 y 0 |
| Huella del manifiesto comprobada con `sha256sum -c` | Correcta |

**Método:** se calculó la huella del origen, se copió y luego se releyeron origen y copia para volver a calcularla.

**SHA-256 del manifiesto:** `caaca819e2cd583fc7ce9dc44e38425c1dc5e5b74327f55b3d4fc91f8a668099`

**No verificado:** la fecha de último acceso de los originales, que el sistema puede actualizar al leerlos.

---

## F. Estado de Git

| Control | Antes | Después de copiar | Resultado |
|---|---|---|---|
| Rama | `datos-simulados` | `datos-simulados` | Igual |
| HEAD | `573d3a31…f9a` | `573d3a31…f9a` | Igual |
| Stash | 0 | 0 | Igual |
| Índice | Vacío | Vacío | Igual |
| `git status --porcelain` | 93 líneas | 93 líneas | Idéntico |
| SHA-256 del estado | `0ce6e412…8c54` | `0ce6e412…8c54` | Igual |

Este informe queda dentro de `40_validacion_final/`, carpeta que ya figuraba como no rastreada, así que no agrega líneas al estado.

---

## G. Incidencias y pendientes

**Incidencias:** ninguna.

**Limitaciones de este respaldo**

| Limitación | Consecuencia |
|---|---|
| Está en el mismo disco que el repositorio | Protege ante errores de trabajo o de Git, **no ante una falla del disco o la pérdida del equipo** |
| No está cifrado | Lo protegen solo los permisos de Windows |
| `.env.example` no se copió | Sus cambios pendientes existen solo en el repositorio |
| Este informe no está en el respaldo | Se escribió después de cerrar el manifiesto |

**Quedó fuera por no formar parte del alcance**

- `auditoria_metodologica_final/`, `auditoria_tesis_v9/`, `cierre_metodologico_4B/` y `Tesis Ver.9.pdf`.
- La base de desarrollo, porque no se autorizó consultar registros. El volcado más reciente que se conoce es del 2026-11-07 y está en `datos/respaldos/2026-11-07_antes_usuarios_0004/`, dentro del repositorio y sin rastrear por Git. No se abrió.

**Pendientes que requieren decisión**

| Id | Asunto |
|---|---|
| P-1 | Autorización para comenzar la Etapa 5B-2 |
| P-2 | Copia externa cifrada, en otro medio (R-5 del plan) |
| P-3 | Respaldo de `.env.example` y de las carpetas de auditoría y cierre |
| P-4 | Incorporación a Git de 38R y 39R (R-1 a R-4 y R-6 del plan), que este respaldo no reemplaza |
