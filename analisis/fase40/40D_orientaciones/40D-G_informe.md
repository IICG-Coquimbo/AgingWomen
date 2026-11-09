# Fase 40D-G — Grupos y personalización contextual (informe único)

> **Nota de actualización (2026-11-09):** B1 sí se muestra a la participante en su tablero, por decisión de la responsable para la revisión de la profesora guía (Fase 40D-H), con la advertencia de que es exploratorio y no es un diagnóstico. Sigue sin seleccionar ni modificar orientaciones (C-5) y no aparece en la ficha individual del profesional. Donde este informe dice que B1 no se muestra, describe el estado anterior a la 40D-H.

Fecha: 2026-11-06 · Rama `datos-simulados` · Sin commit ni push · Catálogo sigue en `borrador_no_validado`.

## 1. Qué se implementó

| Archivo | Cambio |
|---|---|
| `src/apps/encuestas/contexto_participante.py` (nuevo) | Asignación B1 y adaptación por actividad física |
| `src/apps/encuestas/orientaciones.py` | Llama al contexto sobre la misma ronda de referencia (R-1); agrega `contexto_exploratorio` (no se muestra) y `nota_contexto`/`destacar` por tarjeta |
| `src/apps/rondas/cierre.py` | El evento CIERRE guarda `contexto.trabaja_actualmente` (foto del dato al cerrar) |
| `_orientaciones.html`, `_orientacion.html`, `tema.css`, `sw.js` (v16) | Nota breve y medida destacada en la tarjeta |
| `src/apps/encuestas/test_contexto_participante.py` (nuevo) | 15 pruebas |

Sin migraciones (el evento usa el JSON existente). Fases 34–39 sin cambios.

## 2. Grupo B1: contexto exploratorio

- **Definición reutilizada, sin recalcular:** mapa de 20 celdas de `fase37/37C_complemento_tres_preguntas/definiciones/definicion_B1_B2.json` (regla de 4 pasos: ejercicio ≥ 3 días → S1; si no, sin pareja → S0; si no, no trabaja → S2; si no → S3). Una prueba compara el mapa con el JSON y otra con la regla de 4 pasos.
- **Variables y su origen por ronda:** `tiene_pareja` (MRS de la ronda) y `dias_ejercicio_semana` (Actividad física de la ronda) se guardan por ronda. `trabaja_actualmente` vive en la ficha única y se sobrescribe. Por eso desde ahora se guarda su valor en el evento de cierre, y solo ese valor se usa.
- **Sin grupo artificial:** si falta cualquiera de las tres, si la ronda no es cerrada y verificable, o si el cierre es anterior a esta fase (no tiene la foto de «trabaja»), el grupo queda vacío y se registra qué variable falta. No se usa el valor actual de la ficha ni se imputa nada.
- **Uso:** solo queda en `contexto_exploratorio` (para una vista profesional futura, 40E). **No selecciona, ordena ni modifica orientaciones** y no aparece en la página de la participante.

## 3. Qué características personalizan realmente

| Característica | ¿Personaliza? | Justificación |
|---|---|---|
| Respuestas MRS (ítems 1–11) | **Sí** (sin cambios, R-1 a R-7) | Base de la 40D |
| Días de ejercicio = **0** en la ronda de referencia | **Sí, solo resalta** | En O-03, O-05, O-06, O-07 y O-08 el autocuidado ya recomienda actividad física regular, con fuente (F06, F03/F08, F03, F11, F12). Se resalta esa medida y se explica por qué («En tu ronda N indicaste que en una semana habitual no haces ejercicio…»). No hay consejo nuevo ni relación causal |
| Días de ejercicio 1–2 o ≥ 3 | No | El dato son días y no minutos. Sin una fuente sobre dosis no se puede decir si cumple o no |
| Bochornos (O-01) con 0 días | No | F17: el ejercicio no ha demostrado reducir los bochornos por sí mismo |
| Trabajo, pareja | No | Fases 38–39: ninguna asociación supera la nula, y el catálogo no tiene fuentes para adaptar contenido por estas variables |
| Grupo B1 | No | 37D: ε² del MRS total 0,027 y más del 96 % de la variación queda dentro de los grupos. 39: resultado C |

## 4. Pruebas (datos sintéticos)

- Nuevas 40D-G, 15:
  - asignación reproducible;
  - variables ausentes (incluidos valores inválidos y cierre sin foto);
  - ronda abierta;
  - cambios entre rondas (cambiar «trabaja» en la ronda abierta no altera el grupo de la ronda cerrada);
  - separación de participantes;
  - selección idéntica con o sin contexto (principales, otras, motivos);
  - O-01 sin adaptar;
  - la biblioteca nunca se adapta;
  - 1–2 días sin nota;
  - sin etiquetas ni términos estadísticos para la participante;
  - avisos C-1 y de borrador presentes;
  - piloto apagado: no calcula ni muestra.

  1 prueba se omite en Docker porque `analisis/` no está montado. Se verificó aparte, en el equipo, que el mapa es idéntico al JSON.
- **Suite Django completa: 335/335 OK** (1 omitida, la anterior). Pruebas JavaScript 12/12. Pruebas 40B-0 15/15.
- No se repitió la prueba en Chrome: el piloto se comprobó renderizando `/mi-tablero/` en las pruebas Django.

## 5. Limitaciones

1. B1 viene de 529 participantes **sintéticas**. Es una aproximación a la segmentación A (84 % de coincidencia fuera de muestra) y no un grupo natural. Antes de usarla con datos reales habría que repetir el análisis.
2. Las rondas cerradas antes de esta fase no tienen grupo, porque no guardaron «trabaja».
3. La adaptación por actividad física solo resalta contenido existente. El catálogo sigue **sin validación clínica** y necesita una revisión profesional de la nota.
4. Una adaptación por pareja (por ejemplo, el ítem de consejería de pareja en O-09) o por dosis de ejercicio quedaría para una decisión posterior con fuente específica. No se implementó.
5. Las ediciones directas de la ficha desde el administrador de Django no pasan por el cierre. El grupo usa siempre la foto del cierre, así que no le afectan.
