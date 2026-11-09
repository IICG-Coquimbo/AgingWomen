# Fase 40: cierre de los pendientes de consentimiento (informe único)

Fecha: 2026-11-07 · Rama `datos-simulados` · Sin commit ni push · `SECRET_KEY` sin rotar · Fases 34–39 intactas · **Sin migraciones nuevas** · La base de desarrollo no se modificó.

## 1. Retiro presencial de una mujer sin cuenta: implementado

**Ruta:** `/profesional/retiro-presencial/` (vista `retiro_presencial` en `apps/encuestas/retiro.py`). También hay un enlace en el buscador y en la ficha de un registro sin consentimiento.

**Autorización:** se exigen todas estas condiciones, comprobadas en el servidor:
- rol profesional (`@requiere_profesional`); la anónima y la usuaria común quedan fuera;
- RUT solo por POST, nunca en la URL, y página sin caché;
- folio del **documento de revocación** firmado por ella, y lugar de custodia;
- declaración de la profesional de que la participante lo pidió y lo firmó en su presencia;
- confirmación expresa de que el borrado es definitivo;
- **la contraseña de la propia profesional**, con límite de intentos (§3). Se comprueba antes de revelar si hay datos con ese RUT.

**Casos rechazados:**
- **La persona tiene cuenta:** se rechaza. Ella se retira desde su cuenta; una profesional no borra la participación de una cuenta ajena.
- **No hay datos ni consentimiento con ese RUT:** se rechaza y no se borra nada.

**Borrado:** una sola función, `borrar_participacion`, compartida con el retiro de la usuaria. Elimina:
- la ficha y, en cascada, las respuestas, las rondas, los resultados y los eventos;
- el consentimiento presencial.

**Comprobante:** el mismo comprobante firmado de la Etapa 2, que el servidor no guarda. Además lleva:
- `modalidad: presencial`;
- el folio de revocación y la custodia;
- el identificador de la cuenta profesional.

Se verifica con `verificar_constancia_retiro`, que ahora muestra también el folio.

**Envíos antiguos:** se agregó la *participación de la paciente* (`participacion_paciente` en `privacidad.py`), definida así:
- **con cuenta:** la participación de su cuenta;
- **sin cuenta:** el momento en que se registró su consentimiento presencial.

Cambia con cada retiro y con cada consentimiento nuevo. No se guarda nada de lo eliminado.

**Cómo se usa:**
- **Página:** la encuesta profesional recibe la participación (`data-participacion-paciente`).
- **JS:** `encuesta.js` la guarda junto con lo pendiente y la envía en el bloque de identificación. Lo que estaba pendiente sale siempre con la participación con que se guardó, aunque la página traiga otra.
- **Servidor** (`sync.py`, `_verificar_participacion_paciente`):
  - si la participación no coincide, responde 409 `participacion_anterior` y no escribe nada;
  - si falta, responde 409 `cliente_desactualizado`.
- **Respuesta del JS al 409:** borra solo los datos de esa paciente en ese dispositivo. La clave de la profesional y los datos de las demás pacientes no se tocan.
- **Caché:** el Service Worker pasa a v20.

**Corrección asociada:** el retiro de una usuaria con cuenta ahora borra también la ficha que una profesional registró con su RUT antes de que ella creara la cuenta (una ficha sin dueña). Antes esa ficha quedaba sin borrar.

## 2. Registros presenciales antiguos sin constancia: tratados, sin inventar ni borrar

**Sigue igual:** estos registros quedan **fuera de las estadísticas** (`motivo_exclusion`) y **bloqueados para respuestas nuevas** en la encuesta profesional, la sincronización y la API.

**Nuevo:**
- **Ficha:** muestra el aviso «Registro sin consentimiento verificable» y oculta «Completar encuesta». El aviso indica las dos vías posibles:
  - registrar un consentimiento presencial válido, con el RUT y el documento firmado;
  - registrar el retiro presencial, si ella lo pide.
- **Comando** `python manage.py registros_sin_consentimiento`: informe **de solo lectura** con el número de ficha, la ronda y el motivo. No muestra RUT ni datos de salud, y no modifica nada.

**No se crea ningún consentimiento automático ni se borra ningún registro.**

## 3. Límite de intentos de contraseña: implementado

**Módulo:** `apps/usuarios/intentos.py`, en el servidor. Se usa en el consentimiento presencial con cuenta y en el retiro presencial.

**Reglas:**
- **Por cuenta:** 5 fallos bloquean esa cuenta, para todas las profesionales.
- **Por profesional:** 10 fallos repartidos entre varias cuentas bloquean a la profesional.
- **Duración:** el bloqueo dura 15 minutos (ventana fija). Se puede ajustar con `INTENTOS_CLAVE_MAX`, `INTENTOS_CLAVE_MAX_PROFESIONAL` e `INTENTOS_CLAVE_VENTANA`.
- **Durante el bloqueo:** la contraseña **no se comprueba**, ni siquiera si es la correcta, y la respuesta es 429.
- **Reinicio:** un acierto reinicia el contador de la cuenta.
- **Contraseña vacía:** no cuenta como intento.

**Mensajes:** son genéricos. No dicen cuántos intentos quedan ni muestran el correo o el RUT, y desapareció «la contraseña no corresponde a la cuenta…».

**Contadores:** se guardan en la caché de Django con claves HMAC, sin identificadores en claro.

## 4. Pruebas (datos ficticios y bases aisladas)

**Dónde se probó:** en la base de pruebas que Django crea y destruye en cada ejecución. No se usó la base de desarrollo.

| Conjunto | Resultado |
|---|---|
| Nuevas, `apps/usuarios/test_pendientes_consentimiento.py` | 17/17 |
| Django, suite completa (regresión, incluye rondas, MRS, estadísticas y Etapa 2) | 387 ejecutadas: 386 OK y 1 omitida (ya existente) |
| JavaScript, `pruebas_js` (3 nuevas de modo profesional) | 21/21 |
| Integridad 40B-0 y 40B-1 (Fases 34–39) | 20/20, 6.457 artefactos intactos |
| `makemigrations --check` | Sin cambios |

**Qué cubren las 17 pruebas nuevas:**
- permisos y RUT fuera de la URL;
- nada se borra si falta folio, custodia, declaración, confirmación o la contraseña correcta;
- borrado completo sin tocar a otra persona;
- comprobante verificable y ligado al RUT;
- una cuenta no puede ser retirada por la profesional;
- RUT sin datos;
- cola antigua por ficha y por RUT, antes y después de un consentimiento nuevo; cliente sin participación; participación nueva desde cero;
- ficha sin dueña borrada en el retiro propio;
- registro antiguo: excluido, bloqueado, conservado, informe de solo lectura, regularización solo con consentimiento válido, y retiro posible;
- límite de intentos:
  - bloqueo con la clave correcta;
  - bloqueo que alcanza a otra profesional;
  - vencimiento y reinicio;
  - límite por profesional;
  - contraseña vacía;
  - límite también en el retiro.

**Pruebas anteriores ajustadas:** 5 envíos profesionales de pruebas antiguas ahora pasan por `con_participacion`, como el cliente real; la ayuda `pruebas_comunes` agrega la participación de la paciente. La versión esperada del Service Worker pasa de v19 a v20. No se relajó ninguna aserción.

**No se ejecutaron** las pruebas en Chrome real ni las pruebas integrales finales; quedan para la etapa siguiente.

## 5. Limitaciones conocidas y decisiones externas

1. **Constancia del retiro en el servidor:** sigue sin guardarse. Depende de la base legal y del plazo de conservación. Por eso no se puede impedir que un mismo folio de revocación se use dos veces; el folio queda dentro del comprobante firmado.
2. **Quién puede registrar retiros:** hoy, cualquier profesional que confirme con su contraseña. Si se quiere limitarlo a algunas profesionales, por ejemplo con un permiso, es una decisión institucional.
3. **Validación ético-jurídica:** del documento de revocación y de los textos de los formularios.
4. **Caché compartida en producción:** con varios procesos, el límite de intentos necesita Redis o la caché en base de datos. Es parte del despliegue (Fase 18). Con `runserver` funciona tal como está.
5. **Paso de registro presencial a cuenta propia:** si una paciente registrada presencialmente crea su cuenta y acepta en línea mientras una profesional tiene envíos sin conexión por ella, esos envíos se rechazan como de una participación anterior y se borran del dispositivo. Los datos ya guardados en el servidor no se pierden.
6. **Registros antiguos:** contactar a esas personas para regularizar o retirar es un procedimiento externo a la plataforma.
