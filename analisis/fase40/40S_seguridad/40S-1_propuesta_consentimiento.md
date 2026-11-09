# Propuesta de reglas de consentimiento informado

Fecha: 2026-11-06 · Cierre de la Fase 40S-1 · **Propuesta, sin implementar.**

Este documento fija una decisión de diseño. No cambia el sistema: no se implementa la reincorporación, no se modifica el retiro y no se crean modelos ni migraciones. La implementación necesitará una fase autorizada aparte.

## 1. Criterios acordados

1. Una participante con consentimiento vigente puede completar varias rondas sin aceptarlo nuevamente cada vez.
2. Una profesional puede registrar el consentimiento obtenido presencialmente y después ingresar las respuestas, sin exigir que la mujer tenga una cuenta propia.
3. Antes de registrar nuevas respuestas de investigación debe existir consentimiento vigente, pero se puede preparar una ficha administrativa sin comenzar la encuesta.
4. Una mujer que se retiró puede solicitar reincorporarse mediante una nueva aceptación.
5. El retiro no debe producir automáticamente la pérdida de datos históricos que corresponda conservar, y la reincorporación no debe recuperar datos eliminados.
6. No imponer formularios repetitivos ni bloqueos innecesarios.
7. Registrar los cambios de consentimiento de forma sencilla y trazable.
8. Conservar el funcionamiento actual cuando sea compatible con estos principios.

Principio general: **cuidadoso, pero sencillo y proporcional.**

## 2. Cómo funciona hoy

| Aspecto | Hoy | Dónde |
|---|---|---|
| Dónde se guarda | Una sola fecha en la **cuenta**: `Usuario.consentimiento_aceptado_en`. Se sobrescribe y no deja historial | `usuarios/models.py`, `usuarios/views.py:consentimiento` |
| Cuándo se pide | Una vez, al entrar a `/encuesta/`. Vale para todas las rondas | `views.py:13`, `@requiere_consentimiento` |
| API de escritura | Desde la 40S-1, 403 sin consentimiento para la usuaria común | `api.py`, `@requiere_consentimiento_api` |
| Profesional | No se le exige nada. Puede crear la ficha de una paciente sin cuenta (`usuario` nulo) y registrar respuestas. **No queda registro del consentimiento de esa paciente** | `profesional.py:nueva_paciente`, `sync.py` |
| Ficha | La `Identificacion` nace con el primer guardado e incluye los datos sociodemográficos de la encuesta | `sync.py:_resolver_identificacion` |
| Retiro | Borra la ficha y, en cascada, todas sus secciones y rondas. Además borra la fecha de consentimiento | `retiro.py` |
| Reincorporación | Técnicamente posible: tras el retiro, la usuaria puede volver a aceptar en `/cuenta/consentimiento/` y empieza desde cero (sus datos ya no existen) | `usuarios/views.py:consentimiento` |

### Comparación con los criterios

| Criterio | Estado actual | Comentario |
|---|---|---|
| 1. Varias rondas sin reaceptar | ✅ Cumple | No se vuelve a pedir en cada ronda |
| 2. Consentimiento presencial registrado por la profesional | ❌ No cumple | La profesional escribe sin que quede registro del consentimiento de la paciente (riesgo R-4 de la 40S-1) |
| 3. Consentimiento antes de datos de investigación; ficha administrativa previa | ◐ Parcial | Se cumple para la usuaria con cuenta, pero no para la paciente registrada por una profesional. No existe una ficha administrativa separada de la encuesta |
| 4. Reincorporación con nueva aceptación | ◐ Parcial | Puede volver a aceptar, pero no queda registrado como reincorporación |
| 5. El retiro no borra automáticamente lo que corresponda conservar | ❌ No cumple | El retiro borra todo en cascada. La segunda mitad sí se cumple: no se recupera nada |
| 6. Sin formularios repetitivos ni bloqueos innecesarios | ✅ Cumple | Una aceptación; el 403 de la API solo afecta a quien no tiene consentimiento |
| 7. Registro sencillo y trazable | ❌ No cumple | Una sola fecha sobrescrita; no queda historial de otorgamiento, retiro ni reincorporación |
| 8. Conservar lo compatible | — | Ver §4 |

## 3. Reglas propuestas

**C-1. El consentimiento pertenece a la participante, no a cada ronda.**

- Se otorga una vez y queda vigente para todas las rondas, hasta que ella se retire.
- Solo se vuelve a pedir si cambia de forma sustancial el documento de consentimiento, por decisión del comité o de la responsable. En ese caso se pide una sola vez, al ingresar.

**C-2. Hay dos formas de otorgarlo, y valen lo mismo.**

- (a) **En la plataforma:** la mujer lo acepta desde su cuenta, como hoy.
- (b) **Presencial:** la profesional registra que lo obtuvo en persona. Indica la fecha y la versión del documento y, si el protocolo lo pide, el lugar o el centro.
  - No requiere que la mujer tenga cuenta.
  - Es un solo paso, sin formularios adicionales.

**C-3. El consentimiento vigente se exige solo antes de guardar respuestas de investigación.**

- **Ficha administrativa:** se puede crear sin consentimiento. Contiene lo mínimo para identificarla y retomarla: el hash del RUT y, si corresponde, el centro. No incluye datos de la encuesta.
- **Respuestas de investigación** (todas las secciones, incluida la sociodemográfica): cualquier guardado nuevo, sea de la usuaria o de la profesional, exige consentimiento vigente de esa participante.
- **La regla se verifica en un único lugar del servidor** (la sincronización), no en cada pantalla. Así se evitan bloqueos repetidos.

**C-4. El retiro detiene la recolección; no borra todo automáticamente.**

- Al retirarse, el consentimiento deja de estar vigente y no se aceptan respuestas nuevas.
- Qué pasa con los datos ya entregados lo define el protocolo ético, no la plataforma por defecto. Opciones:
  - (a) conservarlos, seudonimizados, para los análisis en curso;
  - (b) borrarlos si ella lo pide expresamente;
  - (c) una combinación.

  La pantalla de retiro tendría que decir claramente cuál aplica.
- El borrado, si se elige, debe ser una acción explícita y registrada, no un efecto colateral.

**C-5. La reincorporación es una nueva aceptación, no una restauración.**

- Una mujer retirada puede volver a aceptar, por cualquiera de las dos vías de C-2.
- Se registra como reincorporación.
- No recupera datos que se hayan borrado. Si se conservaron datos (C-4a), la decisión de volver a vincularlos queda en manos del protocolo.
- Retoma con la ronda siguiente a la última registrada.

**C-6. Proporcionalidad.**

- No se pide aceptar en cada ronda.
- No se agregan pantallas de confirmación adicionales.
- La profesional no repite el registro en cada visita.
- El único bloqueo es el de C-3: no guardar respuestas nuevas sin consentimiento vigente.

**C-7. Registro de eventos sencillo y trazable.**

- **Cada cambio queda como un evento que no se edita ni se borra:** otorgado, retirado o reincorporado.
- **Datos de cada evento:**
  - fecha;
  - vía (plataforma o presencial);
  - quién lo registró (la propia participante o la profesional, identificada por su cuenta);
  - versión del documento.
- **Sin datos de salud:** el registro no contiene respuestas.
- **Estado vigente:** es simplemente el último evento.
- **Retiro con borrado:** si se borran los datos de la encuesta, el registro de eventos se conserva como respaldo de que el retiro se respetó.

**C-8. Compatibilidad.** Se mantiene lo que ya cumple:

- la aceptación única en la plataforma;
- el 403 de la API para quien no tiene consentimiento;
- la redirección a `/cuenta/consentimiento/`;
- el plazo entre rondas;
- el modo profesional.

Los consentimientos que ya existen (`consentimiento_aceptado_en`) se toman como el primer evento «otorgado, vía plataforma».

## 4. Encaje con lo hecho en la 40S-1

| Elemento de la 40S-1 | Relación con la propuesta |
|---|---|
| 403 en `/api/sincronizar/` sin consentimiento para la usuaria común | **Compatible** con C-1, C-3 y C-6. Se conserva |
| Profesional exento | **Transitorio.** Con C-2 y C-3, la exención se reemplaza por esta regla: la profesional puede escribir si **la paciente** tiene consentimiento vigente, de cualquiera de las dos vías. No se agregó ninguna excepción nueva |
| Verificación sobre `Usuario` | Al implementar la propuesta, la verificación debe pasar a la **participante** (la ficha), para cubrir a las pacientes sin cuenta |
| `mi_evaluacion` sin verificación (R-3) | Con C-3, cabe la misma regla de un solo punto. Habría que decidir si la evaluación de satisfacción cuenta como dato de investigación |

## 5. Bosquejo de implementación (para una fase futura)

1. Crear un modelo de eventos de consentimiento, ligado a la ficha.
   - Campos: tipo, fecha, vía, versión del documento y quién registró.
   - Solo se agregan filas.
   - **Requiere migración.**
2. Hacer que la ficha administrativa pueda existir sin datos de la encuesta.
   - Hay que revisar `sync.py` y la creación de `Identificacion`, porque hoy nacen juntas.
   - Puede requerir migración.
3. Crear una función única, `consentimiento_vigente(participante)`, que use la sincronización (usuaria y profesional) y, si se decide, `mi_evaluacion`.
4. Agregar un paso de «registrar consentimiento presencial» en la ficha de la paciente, en el panel profesional.
5. Cambiar el retiro según la decisión de C-4 y agregar la reincorporación según C-5.
6. Hacer una migración de datos que convierta `consentimiento_aceptado_en` en eventos iniciales, sin borrar el campo hasta verificarla.

Los puntos 1, 2 y 6 tocan modelos y migraciones. Los puntos 4 y 5 cambian el funcionamiento visible. Todo necesita autorización y, en lo ético, la validación de la responsable o del comité.

## 6. Decisiones pendientes (responsable o profesora)

| N.º | Decisión |
|---|---|
| DC-1 | ¿Qué se conserva tras el retiro (C-4: a, b o c) y qué dice el consentimiento firmado sobre esto? |
| DC-2 | ¿Qué contiene exactamente la ficha administrativa? ¿Los datos sociodemográficos de Identificación son datos de investigación? |
| DC-3 | ¿Qué datos mínimos registra la profesional del consentimiento presencial? ¿Se guarda una referencia al documento firmado en papel? |
| DC-4 | ¿La evaluación de satisfacción exige consentimiento vigente? |
| DC-5 | ¿Cuándo un cambio del documento obliga a pedir de nuevo el consentimiento? |
| DC-6 | En una reincorporación con datos conservados, ¿se vuelven a vincular o se empieza de cero? |

---

## Adenda 2026-11-06 (Fase 40B-2): decisión sobre retiro y reincorporación

El equipo decidió lo siguiente. **Queda pendiente para una etapa específica: no se implementa en la 40B-2 y el procedimiento actual de retiro (`retiro.py`) no cambia.**

1. El consentimiento vigente permite responder varias rondas (sin cambios respecto de C-1).
2. La profesional podrá registrar un consentimiento presencial cuando se implemente esa funcionalidad (C-2, sin cambios).
3. **Retiro:** se eliminan las respuestas, las rondas y los resultados almacenados en la plataforma, conforme al consentimiento y al procedimiento de eliminación establecido. **Esto reemplaza a C-4** (que proponía no borrar todo automáticamente) y **cierra DC-1**: no se conservan datos de investigación tras el retiro.
4. **Reincorporación:** la persona acepta nuevamente el consentimiento y comienza un historial nuevo desde la primera ronda. **Cierra DC-6**: no se vuelven a vincular datos.
5. No se reconstruyen ni se recuperan respuestas eliminadas (igual que C-5).
6. Se mantienen únicamente las constancias administrativas mínimas justificadas, **sin datos de salud** (por ejemplo, que hubo un retiro y cuándo).

Diferencia con lo que hace hoy la plataforma, para la etapa que lo implemente:

- Hoy el retiro ya borra la ficha y en cascada todas sus secciones, sus rondas (`RondaEvaluacion`), los eventos de ronda (`EventoRonda`) y las marcas `MRSAnterior40B2`. Eso coincide con el punto 3.
- Hoy **no queda ninguna constancia** del retiro: se borra también la fecha de consentimiento y los eventos se van con la ficha. El punto 6 requerirá un registro administrativo propio, fuera de la ficha, que no guarde datos de salud.
- Hoy la reincorporación ya parte de cero (los datos no existen), pero no queda registrada como reincorporación.

Siguen abiertas DC-2 a DC-5.
