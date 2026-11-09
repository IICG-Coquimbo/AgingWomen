# Informe de la Etapa 5B-3: correcciones de la encuesta

Fecha: 2026-11-09. Rama `datos-simulados`, HEAD `573d3a31100c03519d47e220f4a065df3e9caf9a`. Sin commits ni pushes.

## Conclusión

Los tres defectos quedaron corregidos y sus pruebas de regresión pasan en bases temporales y en Chrome real. Una página antigua ya no puede borrar respuestas guardadas sin que la participante lo decida. Con trabajo, pareja y ejercicio conservados, la ronda cierra, el MRS definitivo aparece y B1 se muestra con su advertencia.

Tres límites importantes:

- **Lo ya perdido no se recupera.** La corrección protege de aquí en adelante. Los campos que ya estén en blanco en una ficha siguen en blanco.
- **La ficha 14 no se tocó ni se revisó.** Que allí haya ocurrido este defecto sigue siendo una hipótesis.
- **El código nuevo ya está activo en desarrollo.** El contenedor `agingwomen-web-1` monta `./src` y recarga solo. No hace falta migración y no se escribió en esa base. Falta que alguien pruebe la encuesta allí a mano.

## A. Resumen de defectos

| Defecto | Gravedad | Qué veía la participante | Estado |
|---|---|---|---|
| DF-1 | Crítica | Volvía con «Atrás» o usaba otra pestaña, guardaba, y las respuestas que esa página no tenía quedaban en blanco. En la ronda cerrada podía salir «Grupo aún no disponible». | Corregido |
| DF-2 | Alta | Lo respondido mientras se guardaba quedaba marcado como enviado sin haberse enviado, y se perdía al recargar. | Corregido |
| DF-3 | Media | Tras escribir la fecha, el primer clic en otra pregunta no hacía nada. | Corregido |
| Prueba P6 | Intermitente | No se ve en pantalla. Al borrar por retiro podían quedar dos datos locales. | Causa identificada y corregida |

## B. Causa raíz de cada defecto

**DF-1.** Cada guardado reemplaza la sección completa, y un campo que no llega queda vacío. Eso es intencional: así se vacían las preguntas que dejaron de aplicar (`encuesta.js`, `construirPayload`). El problema era que el servidor no podía saber si la página conocía lo último guardado. Una página antigua enviaba solo lo que tenía en memoria y el servidor borraba lo demás. No se cambió esa regla de vaciado porque otras funciones dependen de ella.

**DF-2.** Al recibir la respuesta, la línea antigua `encuesta.js:1406` marcaba todo como enviado, sin mirar si hubo cambios durante el envío. Al recargar, como no había nada pendiente, mandaba la copia del servidor. Además, varios guardados podían salir a la vez.

**DF-3.** Al salir del campo de fecha, la encuesta redibujaba el formulario justo entre presionar y soltar el ratón. El elemento presionado desaparecía y el clic se perdía. La fecha sí controla tres preguntas (`menstruacion_llega`, `tipo_sangrado`, `usa_metodo_anticonceptivo`), así que a veces el redibujo es necesario, pero no en ese momento. La barra de progreso tenía el mismo riesgo.

**Prueba P6.** Se reprodujo de forma determinista en una copia sin corregir, retrasando el cifrado: 4 de 4 intentos dejaron las claves `envio_final` e `id_cierre`. Una escritura local ya iniciada terminaba después del borrado por retiro. Por eso fallaba solo con el equipo ocupado. Era un defecto real, de bajo impacto porque la llave de descifrado sí se borraba.

## C. Archivos modificados

| Archivo | Cambio | Líneas |
|---|---|---|
| `src/apps/encuestas/sync.py` | Control de versiones en el servidor | +97 / −4 |
| `src/static/js/encuesta.js` | Las tres correcciones y P6 | +222 / −18 |
| `src/static/js/sw.js` | Versión de caché v20 → v21, requerida por `encuesta.js` | +1 / −1 |
| `src/apps/rondas/test_40c.py` | Espera la versión v21 | +1 / −1 |
| `src/apps/encuestas/pruebas_js/test_encuesta_sync.mjs` | 14 pruebas nuevas y dobles de prueba | +285 / −5 |
| `src/apps/encuestas/test_concurrencia_5b3.py` | Archivo nuevo, 15 pruebas | 184 |

No se agregaron dependencias ni migraciones. No se tocó el cálculo de B1 ni la obligatoriedad de ninguna pregunta.

## D. Correcciones implementadas

**DF-1: control de versiones con detección de conflicto, sin fusión.**

- El servidor calcula una huella del contenido de cada sección (`sync.py:342`). Se eligió la huella para evitar una migración, porque no se pueden migrar datos persistentes.
- Cada envío indica sobre qué versión se preparó. Si lo guardado ya no es esa versión, el servidor responde 409 y no escribe nada en ninguna sección (`sync.py:366`, `:553`). Esto también impide cerrar la ronda desde una página antigua.
- La participante ve una pantalla con dos opciones (`encuesta.js:1590`):
  - **«Ver lo último guardado»** (recomendada): carga lo guardado y descarta lo no guardado de esa página.
  - **«Guardar lo de esta página»**: reemplaza lo guardado, con aviso expreso de que lo que falte quedará en blanco.
- Ninguna opción se aplica sola, y los valores nunca se combinan.
- Si la respuesta de un guardado se pierde, el reintento muestra lo enviado y el servidor lo reconoce como propio. Así un corte de red no genera un conflicto falso.
- Al volver con «Atrás» desde la caché del navegador, la página se recarga (`encuesta.js:1807`).

**DF-2.**

- Cada respuesta incrementa un contador. Solo se marca como enviado si el contador no cambió durante el envío (`encuesta.js:1520`, `:1536`). Si cambió, se envía de nuevo sin esperar otra acción.
- Los envíos salen de a uno (`encuesta.js:1441`).
- Si la red falla, ahora se avisa que las respuestas siguen en el dispositivo.
- Al pulsar «Finalizar» los controles se desactivan hasta recibir respuesta. Lo cambiado durante un cierre no alcanzaría a esa ronda. Si aun así ocurre, queda apartado localmente.

**DF-3.**

- Solo se redibuja si cambian las preguntas visibles (`encuesta.js:1176`).
- Si hay que redibujar con el botón presionado, se espera a soltarlo (`encuesta.js:1182`, `:1190`). El guardado no bloquea otros controles.

**P6.** La encuesta queda cerrada antes de borrar, y cada escritura vuelve a comprobarlo tras cifrar (`encuesta.js:293`, `:1651`).

## E. Pruebas de regresión

Todas en bases temporales. Chrome se ejecutó con PostgreSQL en memoria y cuentas ficticias.

| # | Prueba pedida | Evidencia | Resultado |
|---|---|---|---|
| 1 | «Atrás» a una página antigua | R1 con caché atrás/adelante; Django 01, 03-05 | 12 de 12 respuestas visibles; tras completar, 16 de 16 y ronda cerrada |
| 2 | Dos pestañas | R2, R2b; Django 01, 02, 06 | Respuesta 409; el servidor conservó 12; la decisión expresa funciona |
| 3 | Cambiar respuestas mientras se guarda | R3; 3 pruebas JS | 2 envíos, 16 de 16 en el servidor |
| 4 | Recargar tras guardado concurrente | R4; 2 pruebas JS | 16 de 16, sin conflicto falso |
| 5 | Interrumpir y recuperar la conexión | R5, E6; Django 08-09; JS corte de red | 16 de 16, sin conflicto falso |
| 6 | Fecha y clic inmediato | R6; 2 pruebas JS | Marcado al primer clic; sin redibujo innecesario; navegación activa durante el guardado |
| 7 | Cerrar ronda y consultar B1 | R1, E1-E4; Django 15 | Ronda cerrada, MRS definitivo, B1 visible con advertencia |

En la primera corrida de R1, Chrome descartó la caché por presión de memoria. Se repitió y en la segunda no hubo ningún aviso de caché descartada, así que esa corrida sí ejercitó la ruta de «Atrás» con caché.

También se repitieron sin error E1-E6, D1-D3, S (salir y «Atrás»), P (permisos) y F (vista profesional). R2 y R3 sustituyen a los escenarios D4-D7 de la 5B-2, cuyo resultado esperado cambió.

La respuesta perdida justo después de guardar se comprobó con Django y JavaScript. En Chrome no se pudo forzar de forma exacta.

## F. Resultados Django y JavaScript

| Comprobación | Resultado |
|---|---|
| Django completo (copia aislada) | 410 ejecutadas: 409 correctas, 1 omitida |
| `manage.py check` y `makemigrations --check` | Sin problemas, sin cambios |
| JavaScript | 35 de 35 |
| 40B-0, versión segura | 15 de 15 |
| 40B-1, versión segura | 5 de 5, con 6.455 huellas |
| B1, batería combinada | 44 ejecutadas: 43 correctas, 1 omitida |

La omitida es `test_mapa_identico_a_la_definicion_documentada`, que necesita `analisis/` y esa carpeta no está en el entorno aislado. Las 40B-0 y 40B-1 originales no se ejecutaron porque abren un archivo protegido.

**Prueba intermitente P6:** causa identificada (sección B) y corregida. Una prueba nueva, que retrasa el cifrado, la cubre siempre que corre. Sobre los archivos finales, y con el equipo cargado a propósito, se ejecutaron 30 corridas simultáneas: 6 de 6 suites completas y 24 de 24 con solo las pruebas P6, sin fallos. Una repetición secuencial de 25 corridas se detuvo sin completarse porque cada una tardaba más de minuto y medio, y su resultado no se cuenta.

## G. Verificación de MRS y B1

| Condición | Resultado |
|---|---|
| La ronda cierra | Sí (R1, E1-E4, Django 15) |
| MRS definitivo visible | Sí |
| B1 aparece cuando corresponde | Sí, grupo S3 («Grupo 4 — Entre múltiples actividades») |
| B1 no aparece si falta un dato | Sí, 8 de 8 condiciones |
| Advertencias exploratorias visibles | Sí, en el tablero y en la vista profesional |
| B1 no altera las orientaciones | Sí, pruebas existentes de `test_contexto_participante` |
| Promedios agregados por grupo | Sí, 4 grupos; 1 fila publicada y 3 ocultas por protección de grupos pequeños |
| Sin B1 en la ficha individual | Sí, sin cambios en esa vista |

## H. Riesgos pendientes

1. **Respuestas ya vacías:** no se recuperan. Si se quiere saber cuántas fichas están afectadas, hace falta una autorización específica.
2. **Páginas abiertas antes de este cambio:** el código antiguo no envía versión y el servidor no la exige, hasta que esa página se recargue. Exigirla rompería la compatibilidad con clientes antiguos.
3. **Primer envío tras la actualización:** quien tenga cambios pendientes sin versión conocida verá la pantalla de conflicto una vez. Es molesto, pero seguro.
4. **«Guardar lo de esta página»** puede dejar campos en blanco. Es una acción expresa y avisada, pero una persona podría elegirla por error.
5. **Conflictos falsos raros:** si el personal de salud cambia un campo que la participante no ve, ella recibirá el aviso. No se pierde nada.
6. **Teclado:** si se sale de la fecha con Tab y cambian las preguntas visibles, se sigue redibujando y puede perderse el foco.
7. **Sin registro de auditoría:** los rechazos por versión no quedan en `EventoRonda`, porque el tipo de evento existente es específico de rondas cerradas.
8. **DR-1:** siguen sin resolver los indicios de datos reales en la base de desarrollo.

## I. Control de integridad

| Control | Resultado |
|---|---|
| Respaldo 5B-1, antes de modificar | 2.034 archivos, 0 faltantes, 0 distintos, manifiesto OK |
| Rama, HEAD, stash, índice | Sin cambios: `datos-simulados`, `573d3a3`, 0, 0 |
| `git status --porcelain` | De 93 a 94 líneas; la única nueva es `test_concurrencia_5b3.py`, antes de contar este informe, que queda dentro de una carpeta ya listada |
| Metadatos, 7.026 archivos frente a 5B-2 | 5 modificados (los de la sección C), 1 nuevo de esta etapa, y el informe 5B-2 que ya existía |
| Fases 34-39R y tesis | Sin cambios |
| Archivos protegidos y `.env` | No se abrieron |
| Base de desarrollo y registros reales | No se consultaron ni modificaron |

Huellas finales SHA-256 (primeros 16 caracteres):

| Archivo | Huella |
|---|---|
| `encuesta.js` | `38a9c3d0f1fe9bdd` |
| `sw.js` | `56387f1880ae76b0` |
| `sync.py` | `f362d9ac228a45ed` |
| `test_40c.py` | `e8af5e97bb87c498` |
| `test_encuesta_sync.mjs` | `e112cfb058f6d45a` |
| `test_concurrencia_5b3.py` | `c17af1fb64c510d7` |

El respaldo 5B-1 refleja el estado previo a estas correcciones. Sirve para revertirlas, pero no las contiene.

## J. Recomendaciones para la siguiente subetapa

### Plan de seguridad (sin implementar)

| Tema | Situación actual | Corrección propuesta | Decisión necesaria |
|---|---|---|---|
| Límite de intentos de inicio de sesión | Sin límite en el login general (`usuarios/urls.py:14-22`, `forms.py:109`); `intentos.py` solo cubre el flujo presencial | Reutilizar la lógica de `intentos.py`, limitar por RUT y por IP, con bloqueo temporal y mensaje que no revele si la cuenta existe. Probar solo con simulación, sin fuerza bruta | Número de intentos y duración del bloqueo |
| Contraseñas temporales | Se generan en `usuarios/views.py:18-32` sin exigir cambio | Marcar la cuenta, obligar el cambio en el primer ingreso y hacer que la temporal caduque. Requiere un campo nuevo y, por tanto, una migración autorizada | Autorizar la migración y fijar la vigencia |
| Caché del navegador | `tablero.py:33` y `profesional.py:105` responden sin `Cache-Control`; hay `no-store` o `@never_cache` solo en algunas vistas | Aplicar `no-store` a toda vista con datos personales, de forma centralizada, y comprobar «Atrás» tras salir | Ninguna |
| Cifrado de información clínica | `django-fernet-encrypted-fields` está instalado pero sin uso; los volcados no se cifran | Definir primero el alcance: disco, volcados o campos. Cifrar los volcados y el disco es lo menos invasivo. Cifrar por campo impide filtrar y calcular estadísticas en SQL | Alcance y custodia de las claves |

El orden sugerido es caché, límite de intentos, contraseñas temporales y por último cifrado, de menor a mayor impacto. La rotación de secretos sigue siendo condición previa para usar la plataforma con participantes reales, junto con la validación clínica del catálogo y la validación ético-jurídica.

### Otros pasos

1. Probar la encuesta a mano en desarrollo: «Atrás», dos pestañas y la pantalla de conflicto, para validar que el texto se entienda.
2. Decidir si se revisa cuántas fichas tienen respuestas vacías por DF-1.
3. Autorizar el commit de estas correcciones y un nuevo respaldo.
4. Continuar con las pruebas integrales restantes.
