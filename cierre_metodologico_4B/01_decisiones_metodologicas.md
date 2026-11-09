# Etapa 4B · Documento 01 · Registro de decisiones metodológicas

**Fecha:** 2026-11-09 · **Rama:** `datos-simulados` · **HEAD:** `573d3a31100c03519d47e220f4a065df3e9caf9a`
**Alcance:** registro documental. No se ejecutó ningún análisis ni se modificó ningún archivo existente.
**Rutas:** relativas a la raíz del repositorio. Las abreviaturas `35B/`, `38R/` y `39R/` se definen abajo.

| Abreviatura | Ruta |
|---|---|
| `REV33/` | `analisis/reunion_2026-11-03/revision_33_variables/` |
| `BOOT/` | `analisis/complemento_bootstrap_33/` |
| `37C/` | `analisis/fase37/37C_comparacion_seleccion/` |
| `37CC/` | `analisis/fase37/37C_complemento_tres_preguntas/` |
| `37D/` | `analisis/fase37/37D_caracterizacion/` |
| `38R/` | `analisis/fase38/38R_reglas_asociacion_corregidas/` |
| `39R/` | `analisis/fase39/39R_asociaciones_condicionadas_corregidas/` |

**Estados usados en este documento**

| Estado | Significado |
|---|---|
| **Documentada** | Consta en una fuente del proyecto citada aquí. |
| **Verificada en código** | Se comprobó leyendo el código actual, sin ejecutarlo. |
| **Pendiente de ratificación** | Se aplica, pero falta su motivo o la confirmación de la responsable. |
| **Requiere confirmación** | Las fuentes se contradicen o no permiten afirmarla sin matices. |

---

## A. Exclusión de `prevision`

**Estado: decisión metodológica vigente con justificación pendiente de ratificación. No consta como formalmente aprobada.**

### A.1 Qué está establecido

| # | Punto | Estado | Fuente |
|---|---|---|---|
| 1 | `prevision` no forma parte del universo de 33 variables. | Documentada | `REV33/fase35a/predictores_elegibles_33.csv` (33 filas, sin `prevision`); `analisis/cierre_fases_34_35/informes/informe_preprocesamiento_fase35_revisado.md:181`; `REV33/protocolo_revision_33.md:13,42` |
| 2 | La exclusión se mantiene en las Fases 36 a 39R. | Documentada | `analisis/fase36/configuracion_fase36.py:79`; `analisis/fase36/informes/fuentes/01_protocolo_fase36A_ajustado.md:79`; `38R/protocolo/01_protocolo_38R.md:29` («Exclusiones definitivas»); `39R/protocolo/01_protocolo_39R.md` §3 |
| 3 | Puede aparecer en descriptivos sin ser predictora. | Documentada | `analisis/protocolo_fase35b.md:13` («sigue en el conjunto limpio y el EDA, y su SU es descriptiva»); `analisis/fase37/37D_caracterizacion/protocolo/01_protocolo_37D.md:35,66` |
| 4 | Su dominancia de 82,2 % no justifica la exclusión por el umbral de 85 %. | Documentada | `analisis/cierre_fases_34_35/informes/informe_preprocesamiento_fase35_revisado.md:67,171` («Variable de control (acceso a salud); no supera el 85 %…»). FONASA 82,2 %; entropía 0,88 |

**Excepción histórica.** La Fase 38 original sí incluyó `prevision` (`analisis/fase38/38_reglas_asociacion_generales/protocolo/01_protocolo_38.md:39,49`). La 38R corrigió ese punto y es la versión vigente.

### A.2 Trayectoria documental

| Momento | Situación registrada | Fuente |
|---|---|---|
| 28-oct | Se revisa y se decide conservarla como variable de control. | `informe_preprocesamiento_fase35_revisado.md:67,171` |
| Sin fecha exacta | Nota de trabajo: la usuaria consultaría a la profesora si se dejaba para 35B o se sacaba. | Solo en la memoria de trabajo del asistente, no en el proyecto |
| 2-nov | Protocolo 35B: «Pendiente (1)». No pasa a la Fase 36 ni entra al filtro. | `analisis/protocolo_fase35b.md:13,17,131,137`; `analisis/preprocesamiento/configuracion.py:31,92,99,201` |
| 2-nov | Informe 35B: «queda pendiente de consultar a la profesora». Su SU es descriptiva: «no decide». | `analisis/informe_seleccion_fase35b.md:9,69,195` |
| 3-nov | La redacción cambia de «pendiente» a «excluida». | `analisis/reunion_2026-11-03/protocolo_revision_35b.md:49`; `analisis/reunion_2026-11-03/informe_integrado/informe_fase35b_integrado.md:19` |
| 5-nov | Bootstrap la clasifica como exclusión «Definitiva», mientras su propia tabla conserva «(protocolo 35B, pendiente)». | `BOOT/protocolo/01_revision_y_configuracion.md:66`; `BOOT/configuracion/candidatas_y_exclusiones.csv` |
| 5 a 8-nov | Se aplica como exclusión en 36, 38R y 39R. | Ver A.1, punto 2 |

### A.3 Qué evidencia existe y cuál no

**Existe:**

- Registro de que la variable se dejó fuera del filtro y del modelado desde el protocolo 35B, antes de ejecutar el filtro.
- Medidas descriptivas: SU 0,0082 y p 0,296 (`informe_seleccion_fase35b.md:69`); Kruskal-Wallis n = 527, ε² 0,002, p 0,429 (`analisis/informe_eda_usuaria.md:1000`); ε² 0,0028, p 0,175, q 0,344 en la 37D, modelo F1.
- En limpieza: 19 valores imputados con la moda (FONASA) y 2 deducidos (`informe_limpieza_usuaria.md:217,265`).

**No existe o no se encontró:**

- Respuesta de la profesora sobre `prevision`.
- Motivo sustantivo escrito para excluirla.
- Acta o registro formal que convierta el «pendiente» en «excluida». El cambio ocurre solo en la redacción de los documentos del 3-nov en adelante.

**Advertencia.** Las medidas descriptivas anteriores **no se citan en ningún documento como motivo de la exclusión**. Usarlas ahora como justificación sería una razón estadística construida a posteriori. Además, el protocolo 35B estableció que su SU es descriptiva y no decide. Por eso este registro no las presenta como fundamento.

### A.4 Texto propuesto para el registro

> `prevision` queda fuera del universo de predictoras y se conserva como variable descriptiva. La exclusión está vigente en las Fases 36 a 39R. No se debe al umbral de dominancia (82,2 % < 85 %). Su justificación sustantiva y su aprobación formal no están documentadas y quedan pendientes de ratificación por la responsable del proyecto.

**Efecto de una decisión distinta.** Si se resolviera incorporar `prevision`, cambiaría el universo de 33 variables y habría que repetir las fases dependientes. El protocolo 35B ya previó que la familia pasaría a 31 pruebas (`analisis/protocolo_fase35b.md:17`). Este documento no propone ese cambio.

---

## B. Segmentaciones A y B1

- **A:** `P2_c12_km_k4`, K-means con 4 grupos sobre 12 componentes de P2. Tamaños 150/76/132/171.
- **B1:** regla de 4 pasos sobre trabajo, pareja y días de ejercicio. Tamaños 150/79/126/174. ARI A–B1 de 0,688.

### B.1 Verificación de cada afirmación

| # | Afirmación | Resultado | Fuente y observación |
|---|---|---|---|
| 1 | No se adoptó ninguna segmentación como modelo definitivo. | **Documentada** en análisis. **Requiere confirmación** en plataforma | `37C/seleccion/decision_final_37C.json`: «PROVISIONAL. La decisión final queda en manos de la responsable del proyecto»; `37D/informes/fuentes/15_informe_final_37D.md:113` deja por decidir A, B1 o ninguna. No se encontró una decisión final posterior. La plataforma ya muestra B1 (ver punto 4) |
| 2 | A es exploratoria. | **Documentada** | `39R/protocolo/01_protocolo_39R.md` §6; `39R/documentos_definitivos/fuentes/15_comparacion_exploratoria_A_B1.md:7`; `39R/documentos_definitivos/fuentes/20_nota_logica_tablero.md`: no se recomienda llevarla a producción |
| 3 | B1 es exploratoria. | **Documentada** | Mismas fuentes. `15_comparacion_exploratoria_A_B1.md:64`: ninguna diferencia supera la nula. El aviso de la plataforma también la llama exploratoria |
| 4 | B1 se utiliza en la plataforma exclusivamente como información contextual. | **Requiere confirmación** | Es correcta respecto a las orientaciones, pero incompleta. Ver B.2 |
| 5 | B1 no participa en la selección de orientaciones. | **Verificada en código** | `src/apps/encuestas/orientaciones.py:94` solo guarda `grupo_b1` en `contexto_exploratorio`. `nota_actividad` solo usa `contexto['sin_ejercicio']`, un dato individual de 0 días. Las plantillas no hacen referencia al grupo. Existe la prueba `test_contexto_participante.py:155` (`test_seleccion_igual_con_y_sin_contexto`), que no se ejecutó en esta etapa |
| 6 | No hay evidencia suficiente de grupos naturales claramente diferenciados. | **Documentada** | `37C/informes/fuentes/14_informe_cierre_37C.md` |
| 7 | Eso no demuestra que los grupos no existan. | **Documentada** | Mismo informe: los resultados son compatibles con un continuo, y la potencia frente a grupos débiles no se evaluó |

### B.2 Discrepancia: B1 se muestra a la participante

**El código actual presenta B1 a la participante, y varios documentos dicen que eso no ocurre.**

**Lo que hace el código:**

| Lugar | Comportamiento |
|---|---|
| `src/apps/encuestas/contexto_participante.py` (`GRUPOS_VISIBLES`, `grupo_para_tablero`), `tablero.py:38`, `mi_tablero.html:42`, `_mi_grupo.html` | Muestra a cada participante su grupo: S0 «Bienestar a tu ritmo», S1 «Vida en movimiento», S2 «Equilibrio personal», S3 «Entre múltiples actividades» |
| `_mi_grupo.html` | Avisa: «Es una caracterización exploratoria… No es un diagnóstico ni un indicador de salud» y «tu grupo no explica ni predice este resultado» |
| `src/apps/encuestas/estadisticas.py:161-173`, `estadisticas.html:75-94` | Tabla profesional agregada con MRS promedio por grupo |

**Lo que dicen los documentos:**

| Fuente | Texto | Situación |
|---|---|---|
| Docstring de `contexto_participante.py` | «nunca visible para la participante» | Desactualizado |
| `orientaciones.py:21` | Contexto no visible para la participante | Desactualizado |
| `analisis/fase40/40D_orientaciones/` · `40D-G_informe.md` §2 | «no aparece en la página de la participante» | Desactualizado |
| `analisis/fase40/40D_orientaciones/` · `40D-1_informe.md:96,100` | «No para las participantes»; antes de usarlo con participantes habría que repetir el análisis con datos reales y un protocolo sellado | Contradice el estado actual |
| Criterio C-5 de la Fase 40D | «no mostrar clústeres a la usuaria» | Contradice el estado actual |
| `39R/documentos_definitivos/fuentes/20_nota_logica_tablero.md:21` | «ya presenta su grupo descriptivo B1 (Fase 40D-H, en revisión)» | Coincide con el código |
| Misma nota, tabla «Resumen» | Etiqueta B1: «Solo si la profesora lo decide» | No se encontró esa decisión |

**Autorización.** La memoria de trabajo del asistente registra que la usuaria autorizó esta visualización (Fase 40D-H). No existe informe de la 40D-H en `analisis/fase40`, ni una decisión de la profesora al respecto. Tampoco consta el protocolo sellado con datos reales que pedía el informe 40D-1.

**Redacción recomendada, en lugar de «exclusivamente contextual»:**

> B1 no interviene en la selección de orientaciones. La plataforma la muestra a la participante como caracterización exploratoria, con avisos, y la profesional ve promedios agregados de MRS por grupo. Esta visualización procede de la Fase 40D-H, que sigue en revisión.

**Confirmaciones necesarias de la responsable:**

1. Si se mantiene la visualización de B1 a la participante, se retira o se oculta hasta validarla con datos reales.
2. Si se mantiene la tabla profesional de MRS por grupo.
3. Si la condición «solo si la profesora lo decide» sigue vigente.

Esas respuestas determinan qué documentos de la Fase 40 deben corregirse. Esta etapa no los modifica.

### B.3 Decisiones documentadas y decisiones por confirmar

| Tema | Estado |
|---|---|
| A no se lleva a producción | Recomendación documentada; no consta como decisión final |
| B recomendada frente a A, con C igual de defendible | Recomendación no vinculante (`37CC/informes/fuentes/12_informe_metodologico_final.md`) |
| A y B1 solo como comparación exploratoria en 39R | Documentada en protocolo 39R §6 |
| Elección final entre A, B1 o ninguna | **Requiere confirmación** |
| Visualización de B1 y tabla profesional | **Requiere confirmación** |

---

## C. Sensibilidad S7a-263

**Estado: no ejecutada, opcional y sin resultados conocidos.**

| Punto | Registro | Fuente |
|---|---|---|
| Qué sería | Repetir el análisis laboral solo con las 263 de 287 trabajadoras que tienen observadas ambas variables. Quedarían fuera 24 con alguna imputada (16 en lugar, 10 en estrés y 2 en ambas). | `analisis/fase36/modulos/modulo_laboral.csv`, columna `sensibilidad_ambas_observadas` |
| Preparación | La Fase 36 dejó preparada la columna necesaria. | `analisis/fase36/informes/fuentes/01_protocolo_fase36A_ajustado.md:123` |
| Ejecución | No se ejecutó en la 38R ni en la 39R. | `38R/protocolo/01_protocolo_38R.md:52`; `39R/informes/informe_comparativo_39R.md:32` |
| Carácter | Opcional. | `auditoria_metodologica_final/INFORME_ETAPA_4A.md`, sección F; instrucción de la Etapa 4B |
| Cierre de 38R y 39R | No es condición necesaria. | Instrucción de la Etapa 4B |
| Futuro | Puede plantearse como investigación posterior, con autorización expresa. | Instrucción de la Etapa 4B |

**No se conocen sus resultados.** Ningún documento debe afirmar que la sensibilidad confirma, modifica o deja igual las conclusiones de 38R o 39R.

---

## D. Control de este documento

- Citas tomadas de lecturas directas de las fuentes, sin alterarlas.
- Los archivos vedados no se abrieron ni se consultaron.
- No se calcularon huellas ni se ejecutaron pruebas.
