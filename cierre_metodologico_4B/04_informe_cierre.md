# Etapa 4B · Documento 04 · Informe de cierre documental

**Fecha:** 2026-11-09 · **Rama:** `datos-simulados` · **HEAD:** `573d3a31100c03519d47e220f4a065df3e9caf9a`

---

## A. Resumen ejecutivo

**La Etapa 4 puede considerarse documentalmente cerrada.** La metodología queda registrada y ningún hallazgo obliga a recalcular resultados.

Quedan dos asuntos por atender antes de continuar con la Fase 40: autorizar el respaldo de 38R y 39R, y decidir si B1 se sigue mostrando a la participante.

| Tema | Resultado |
|---|---|
| `prevision` | Exclusión vigente. Su justificación sustantiva y su aprobación **no están documentadas**, así que queda pendiente de ratificación |
| Segmentaciones A y B1 | Ambas exploratorias; ninguna adoptada como modelo definitivo. B1 no interviene en la selección de orientaciones |
| **Discrepancia nueva** | **La plataforma muestra B1 a la participante**, y varios documentos dicen que no. La expresión «exclusivamente contextual» debe precisarse |
| S7a-263 | No ejecutada, opcional, sin resultados conocidos y no condiciona el cierre |
| Reproducibilidad | Fuente de variables, dependencias, semillas y huellas registradas. El entorno está sin fijar y falta en 37C, 37D y 39R |
| Respaldo | Plan listo y **sin ejecutar**. Inventario: 1.900 archivos, ≈ 418 MB |
| **Riesgo nuevo** | Un clon en Windows con `autocrlf=true` alteraría las huellas de los protocolos sellados |
| Integridad | Sin cambios fuera de los cuatro documentos nuevos |

---

## B. Decisiones registradas

Detalle y citas en `01_decisiones_metodologicas.md`.

### `prevision`

- No pertenece al universo de 33 y sigue excluida de las Fases 36 a 39R. Puede aparecer en descriptivos.
- Su dominancia (82,2 %) no alcanza el umbral de 85 %, así que ese umbral no explica la exclusión.
- Los documentos pasan de «pendiente de consultar a la profesora» (2-nov) a «excluida» (3-nov) sin que conste una respuesta ni un motivo.
- Las medidas descriptivas existentes no se citan como motivo en ningún documento, y aquí no se usan como justificación.

### A y B1

| Afirmación | Resultado |
|---|---|
| Ninguna segmentación es modelo definitivo | Documentada en los análisis; la plataforma requiere confirmación |
| A y B1 son exploratorias | Documentada |
| B1 no participa en la selección de orientaciones | Verificada en código |
| B1 se usa exclusivamente como información contextual | **Requiere confirmación:** se muestra a la participante y genera promedios profesionales de MRS por grupo |
| No hay evidencia suficiente de grupos naturales diferenciados | Documentada |
| Eso no demuestra que no existan | Documentada |

### S7a-263

Registrada como posibilidad futura. No se afirma nada sobre sus resultados.

---

## C. Reproducibilidad

Detalle en `02_guia_reproducibilidad.md`.

**Qué se puede reproducir conceptualmente:** la cadena completa 35B → Random Forest y bootstrap → 36 → 37 → 38R → 39R. Hay ruta del universo definitivo, tabla de dependencias, parámetros, semillas y 13 huellas registradas.

**Qué sigue incompleto:**

| Pendiente | Efecto |
|---|---|
| 38R y 39R sin control de versiones | No se pueden reconstruir desde un clon limpio |
| Sin archivo de entorno fijado para el análisis | La instalación depende de los registros dispersos |
| Versiones no verificadas en 37C, complemento, 37D y 39R, y parciales en 35B, Random Forest y bootstrap | No se acredita igualdad de entorno en esas fases |
| Configuraciones históricas que reintroducen variables (H-05) | Riesgo de usar la lista equivocada. Mitigado con la advertencia de la guía; no se modificaron |
| Finales de línea en un clon | Las huellas pueden no coincidir |
| Identidad numérica de los resultados | No verificada en esta etapa, porque no se ejecutó nada |

---

## D. Respaldo

Detalle en `03_plan_respaldo.md`.

**Inventario:** 38R 330 archivos / 117,03 MB; 39R 1.570 archivos / 301,14 MB. Sin archivos de más de 50 MB, sin temporales y sin `.env` dentro de las carpetas. `node_modules` (22,89 MB) ya está ignorado.

**Acciones que requieren autorización, ninguna ejecutada:**

1. Generar el manifiesto completo.
2. Crear `.gitattributes` en ambas carpetas.
3. Hacer `git add` por rutas exactas y los commits, mostrando antes el mensaje exacto.
4. Verificar con un clon limpio.
5. Hacer push.
6. Hacer copia externa.

---

## E. Pendientes de aprobación

### E.1 Confirmadas por instrucción de la responsable

| Decisión | Origen |
|---|---|
| S7a-263 es opcional y no condiciona el cierre | Instrucción Etapa 4B |
| `prevision` se registra como vigente con justificación pendiente, sin presentarla como aprobada | Instrucción Etapa 4B |
| La Tesis Ver.11 queda reservada para las observaciones finales de la profesora guía | Instrucciones Etapas 4A y 4B |

### E.2 Propuestas pendientes de ratificación

| Id | Asunto | Recomendación | ¿Bloquea la Fase 40? |
|---|---|---|---|
| P-1 | **Visualización de B1 a la participante:** mantener, retirar u ocultar hasta validar con datos reales | Decidir antes de las pruebas integrales | **Sí** |
| P-2 | **Tabla profesional** de MRS por grupo | Decidir junto con P-1 | **Sí** |
| P-3 | Si sigue vigente la condición «solo si la profesora lo decide» | Decidir junto con P-1 | **Sí** |
| P-4 | Corregir los textos desactualizados de la Fase 40 según P-1 | Una vez decidido P-1 | Parte de P-1 |
| P-5 | **Respaldo de 38R y 39R:** autorizar el plan y resolver R-1 a R-6 | Autorizar antes de tocar la Fase 40 | **Sí, por prudencia** |
| P-6 | Ratificar `prevision` y su motivo sustantivo | Antes de la versión final de la tesis | No |
| P-7 | Elección final entre A, B1 o ninguna | Antes de la versión final de la tesis | No, salvo que P-1 la requiera |
| P-8 | Atender los hallazgos H-05 a H-13 con notas o correcciones | Junto con la tesis | No |
| P-9 | Tesis Ver.11, no disponible en el repositorio (H-02) | Cuando estén las observaciones de la profesora guía | No |
| P-10 | Fijar el entorno de análisis (H-06) | Antes de cualquier reejecución | No |
| P-11 | S7a-263 como investigación futura | Opcional | No |

---

## F. Integridad

| Control | Inicio | Final | Resultado |
|---|---|---|---|
| Rama | `datos-simulados` | `datos-simulados` | Igual |
| HEAD | `573d3a31…f9a` | `573d3a31…f9a` | Igual |
| Stash | 0 | 0 | Igual |
| Índice (`git diff --cached`) | Vacío | Vacío | Igual |
| `git status --porcelain` | 91 líneas | 92 líneas | Única diferencia: `?? cierre_metodologico_4B/` |
| Metadatos (tamaño y fecha) | 7.022 archivos | 7.022 archivos | 0 nuevos, 0 retirados, 0 cambiados |

**Método.** Se compararon tamaño y fecha de modificación, sin abrir contenidos ni calcular huellas. Abarcó las Fases 36 a 39, Random Forest, bootstrap, revisión de 33 variables, las dos auditorías y las entradas de `git status`.

**Restricciones cumplidas:**

- No se abrieron los cuatro archivos vedados, ni se incluyeron en recorridos, búsquedas o huellas.
- No se repitió la incidencia de la Etapa 4A.
- No se ejecutaron análisis, modelos, pruebas, S7a-263 ni instalaciones.
- No se recalcularon huellas de protocolos ni de datos.
- No hubo commits, pushes, merges, resets, stashes ni limpiezas.
- No se modificaron la Fase 40, las Fases 34 a 39R ni las tesis.

**Nota de transparencia.** Al revisar `38R/documentos_definitivos/validacion/huellas_final.csv`, la salida de la sesión mostró las huellas registradas de `.env` y `.env.desarrollo`. Son registros preexistentes; los archivos `.env` no se abrieron, y esas huellas no se copiaron a estos documentos.

**No verificado:**

| Aspecto | Motivo |
|---|---|
| Estado de los cuatro archivos vedados | Excluidos de todo control, por instrucción |
| Identidad byte a byte de los archivos controlados | Control solo por metadatos |
| Archivos ignorados fuera de las raíces controladas | No se recorrió todo el repositorio, por instrucción |
| Coincidencia actual de las huellas selladas | No se recalcularon; constan 13 de 13 en la Etapa 4A |
| Ausencia exhaustiva de valores secretos en registros | Revisión por patrones |
| Ausencia de datos personales archivo por archivo | Queda para el paso 2 del plan |
| Motivo de las 19 entradas no rastreadas de `archivos_leidos.csv` de 39R | Inferido, no comprobado |
| Equivalencia de la cobertura del manifiesto por ruta | Comprobada solo por recuento |

**Entregables.** Únicamente los cuatro archivos de `cierre_metodologico_4B/`.

---

## G. Recomendación final

**La Etapa 4 puede considerarse documentalmente cerrada.** Las decisiones están registradas con su estado real, la guía de reproducibilidad está completa con lo que se puede acreditar y el plan de respaldo está listo.

**Antes de continuar con la Fase 40 se necesita:**

1. **Autorizar y ejecutar el respaldo de 38R y 39R (P-5).** Los resultados definitivos existen en una sola copia local, sin control de versiones. La recomendación es no intervenir la Fase 40 antes de protegerlos.
2. **Decidir la visualización de B1 y la tabla profesional (P-1 a P-3).** Es la única decisión metodológica que cambia lo que se debe probar y dejar en la plataforma.

La ratificación de `prevision`, la elección final de segmentación y los hallazgos H-05 a H-13 no bloquean la Fase 40, pero conviene resolverlos antes de la versión final de la tesis.

La Tesis Ver.11 permanece reservada para las observaciones finales de la profesora guía.
