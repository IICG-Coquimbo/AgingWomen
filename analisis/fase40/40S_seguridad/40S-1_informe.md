# Fase 40S-1 — Primera implementación de seguridad

Fecha: 2026-11-06 · Rama `datos-simulados` · Punto de partida `573d3a3` · Sin commit ni push.

Este informe no contiene ningún valor secreto. Donde hizo falta comparar valores, se compararon dentro de un programa y solo se informa si son iguales.

## Resumen

**Cambios principales:**

- Los secretos ya no están escritos en el código ni en `docker-compose.yml`.
- `DEBUG` queda desactivado salvo que el entorno lo pida.
- Sin `DEBUG`, el sistema exige una configuración de producción segura y se niega a arrancar con los valores de desarrollo.
- La API de escritura rechaza con 403 a la usuaria sin consentimiento vigente.

**Desarrollo:** sigue funcionando con **los mismos valores que usaba**. Las huellas de `SECRET_KEY`, del pepper, de la clave de la base y del hash de un RUT de prueba son idénticas antes y después. Las sesiones y el ingreso por RUT no cambian.

**Pruebas:** las 185 pruebas de Django que había pasan, y pasan 25 nuevas: 210/210 en PostgreSQL. Los resultados históricos, los modelos, `sync.py`, las migraciones y los datos están intactos.

**Actualización de cierre (2026-11-06):**

- **Prueba de la 40B-0 corregida:** `test_plataforma_sin_cambios` ahora verifica solo los cuatro archivos fuente de la limpieza. Resultado: 15/15, y el control negativo falla como debe (§5.4).
- **Propuesta de consentimiento:** las reglas quedaron documentadas, sin implementar, en `40S-1_propuesta_consentimiento.md` (§11).
- **Riesgos detallados:** los del RUT en la URL, `mi_evaluacion` y el acceso profesional están en §8.1.
- **Verificación:** se repitieron las pruebas y las comprobaciones de integridad.

---

## 1. Problemas corregidos

| Hallazgo | Antes | Ahora |
|---|---|---|
| H-12: `SECRET_KEY` literal | Escrita en `settings.py`, que **no la leía del entorno**. El `SECRET_KEY` de `docker-compose.yml` nunca se usaba | Solo del entorno, sin valor por defecto |
| H-12: pepper y clave de la base con valores por defecto literales | `os.environ.get(..., '<literal>')` en `settings.py` | Solo del entorno, sin valor por defecto |
| **Nuevo (no estaba en la 40A):** secretos literales en `docker-compose.yml` | `SECRET_KEY`, `RUT_HASH_PEPPER`, `DB_PASSWORD` y `POSTGRES_PASSWORD` escritos en el archivo | Se leen de `.env.desarrollo` (privado) con `env_file` |
| H-12: `DEBUG = True` fijo | Siempre activado | Desactivado por defecto; `DEBUG=1` solo en desarrollo, puesto por docker-compose |
| S-2: arranque sin variables | Arrancaba con los valores literales | Si falta una variable obligatoria, Django no arranca (`ImproperlyConfigured`) |
| S-4: perfil de producción | No existía | Sin `DEBUG`: cookies de sesión y CSRF `Secure`, más validación de producción (§3) |
| **Nuevo:** correo de consola en producción | Sin correo real, los códigos OTP, los enlaces de recuperación y las contraseñas temporales de profesionales se escribían en los registros | En producción el correo real es obligatorio |
| H-11 / S-5: API sin consentimiento | `/api/sincronizar/` solo exigía haber iniciado sesión | Sin consentimiento vigente: 403 en JSON y no se guarda nada |

## 2. Archivos modificados

| Archivo | Cambio |
|---|---|
| `src/Encuesta_integral/settings.py` | Lectura obligatoria de `SECRET_KEY`, `RUT_HASH_PEPPER` y `DB_PASSWORD`; `DEBUG` por entorno; `CSRF_TRUSTED_ORIGINS`; cookies y cabeceras explícitas; perfil y validación de producción |
| `docker-compose.yml` | Sin secretos literales; `env_file: .env.desarrollo` en `db` y `web` |
| `.env.example` | Solo nombres y ejemplos: correo, `.env.desarrollo` y producción |
| `README.md` | Paso previo `.env.desarrollo` y tabla de variables actualizada |
| `src/apps/usuarios/decorators.py` | Nuevo `requiere_consentimiento_api` (403 en JSON) |
| `src/apps/encuestas/api.py` | `@requiere_consentimiento_api` en `sincronizar` y docstring |
| `src/apps/encuestas/tests.py` | Solo `SincronizarEndpointTest.setUp`: la usuaria de prueba acepta el consentimiento. Sus pruebas existían para una usuaria habilitada y ahora la regla lo exige |
| `src/apps/encuestas/test_consentimiento_api.py` | Nuevo: 12 pruebas |
| `src/apps/usuarios/test_seguridad_config.py` | Nuevo: 13 pruebas |
| `analisis/fase40/40S_seguridad/40S-1_informe.md` | Este informe |
| `analisis/fase40/40S_seguridad/40S-1_propuesta_consentimiento.md` | Cierre: reglas de consentimiento propuestas, sin implementar |
| `analisis/fase40/40B_implementacion/pruebas/test_40b0_definiciones.py` | Cierre: solo `test_plataforma_sin_cambios`, acotada (§5.4) |

**Fuera de Git:**

- `.env.desarrollo`: nuevo y privado, ignorado por la regla `.env.*` de `.gitignore`.
  - Contiene los cuatro valores de desarrollo que ya estaban activos, copiados por un programa que no los mostró.
  - Permisos: solo SYSTEM, Administradores y la cuenta `scarl`.
- `.env`: **no se modificó**; su SHA-256 es igual antes y después.

No se modificaron:

- `models.py` (de ninguna app), `sync.py`, `rut.py` ni `backends.py`;
- las migraciones ni la base de datos;
- `datos/` ni `analisis/` (salvo este informe).

## 3. Cómo se maneja cada variable

| Variable | Desarrollo | Producción (sin `DEBUG`) |
|---|---|---|
| `SECRET_KEY` | Obligatoria, de `.env.desarrollo` | Obligatoria. Se rechaza si empieza con `django-insecure`, si tiene menos de 50 caracteres o si tiene menos de 5 caracteres distintos |
| `RUT_HASH_PEPPER` | Obligatoria, de `.env.desarrollo` | Obligatoria, mínimo 32 caracteres |
| `DB_PASSWORD` | Obligatoria, de `.env.desarrollo` | Obligatoria |
| `POSTGRES_PASSWORD` | De `.env.desarrollo` (contenedor `db`), igual a `DB_PASSWORD` | La define el servidor de base de datos |
| `DB_NAME`, `DB_USER`, `DB_HOST`, `DB_PORT` | De `docker-compose.yml` (no son secretos) | Del servidor |
| `DEBUG` | `DEBUG=1` en `docker-compose.yml` | Ausente o `0` |
| `ALLOWED_HOSTS` | Por defecto `localhost,127.0.0.1` | Obligatorio sin `*` |
| `CSRF_TRUSTED_ORIGINS` | Vacío | Lista de orígenes `https://…` |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | Desde `.env` (sin cambios); vacíos significa correo por consola | **Obligatorias** |
| `SECURE_SSL_REDIRECT`, `DETRAS_DE_PROXY_HTTPS`, `SECURE_HSTS_SECONDS` | No se aplican | Apagadas por defecto. **No se activaron**: dependen del despliegue (Fase 18, DR-2) |

**Reglas comunes:**

- Un valor vacío o con solo espacios cuenta como ausente.
- Si `DEBUG` tiene un valor no reconocido, Django no arranca.
- Los mensajes de error nombran la variable, nunca su valor.

**Valores fijos en ambos perfiles** (casi todos coinciden con el valor por defecto de Django):

| Ajuste | Valor |
|---|---|
| `SESSION_COOKIE_HTTPONLY` | `True` |
| `CSRF_COOKIE_HTTPONLY` | `False` (`encuesta.js` lee el token) |
| `SameSite` | `Lax` |
| `nosniff` | activado |
| `Referrer-Policy` | `same-origin` |
| `COOP` | `same-origin` |
| `X-Frame-Options` | `DENY` |

**Sobre el valor de `SECRET_KEY`:** a `.env.desarrollo` se copió la `SECRET_KEY` de `settings.py`, que era la única activa, y no la de `docker-compose.yml`, que Django ignoraba. El pepper y la clave de la base se copiaron de `docker-compose.yml`, porque eran los que usaba el contenedor. Por eso nada cambió para las sesiones ni para los hashes de RUT.

**Consentimiento:**

- `/api/sincronizar/` (POST): una usuaria común sin `consentimiento_aceptado_en` recibe 403 con `{"ok": false, "codigo": "consentimiento_requerido", "error": …}`.
  - El consentimiento se revisa antes de leer el cuerpo de la petición.
  - El cliente (`encuesta.js`) ya trata cualquier respuesta no 200 conservando las respuestas en el dispositivo como pendientes, así que no se pierden datos ni hubo que cambiar el cliente.
- **Personal de salud:** queda fuera de la regla, igual que en `/encuesta/`. No participa del estudio y responde siempre por una paciente. No es una excepción nueva.
- **Administración:** se maneja con `is_staff` y no es un rol de la API. Una cuenta de administración con rol de usuaria sigue la regla de usuaria.
- **Lecturas** (`/api/esquema/`, `/api/estado/`, `/api/ronda-actual/`): no cambian. Solo muestran lo propio y no escriben, y el alcance de H-11 es la escritura.

## 4. Pruebas ejecutadas y resultados

Entorno: Docker Desktop (motor iniciado para esta fase), `postgres:15-alpine`, imagen `agingwomen-web`. Las pruebas de Django usan una base temporal (`test_django_db`) que se crea y se destruye; la base de desarrollo no se leyó ni se escribió.

| N.º | Prueba obligatoria | Cómo | Resultado |
|---|---|---|---|
| 1 | Secretos fuera de los archivos activos | Búsqueda de los 7 valores (los activos, los viejos y la contraseña de correo) en `settings.py`, `docker-compose.yml`, `.env.example`, los archivos tocados y las líneas agregadas del diff; además, una prueba de Django sobre `settings.py` | **0 apariciones**; prueba OK |
| 2 | Variables leídas correctamente | `ValoresActivosTest`: `settings` es igual a `os.environ`, sin comillas ni espacios añadidos | OK |
| 3 | Desarrollo arranca con su configuración privada | `docker compose up -d web`, más `/cuenta/ingresar/` (200), estáticos (200), `manage.py check` sin problemas y `migrate --check` sin migraciones pendientes | OK |
| 4 | Producción rechaza configuraciones incompletas o inseguras | Ver detalle debajo de la tabla | OK |
| 5 | Sesiones y RUT sin cambio de claves | Huellas SHA-256 calculadas dentro del contenedor antes y después: `SECRET_KEY`, pepper, clave de la base y `hash_rut('11.111.111-1')` | **Idénticas** |
| 6 | API rechaza escrituras sin consentimiento | Usuaria que nunca aceptó y usuaria que se retiró: 403 en JSON y 0 filas guardadas; también 403 con JSON inválido | OK |
| 7 | Operaciones autorizadas siguen funcionando | Ver detalle debajo de la tabla | OK |
| 8 | Sin secretos ni respuestas sensibles en registros | Ver detalle debajo de la tabla | OK |
| 9 | Django con PostgreSQL | Suite completa en PostgreSQL y `ENGINE` verificado | OK |
| 10 | Resultados históricos intactos | Huellas de 898 archivos protegidos (`datos/` completo, modelos, `sync.py`, `rut.py`, `backends.py`, migraciones y `.env`) iguales antes y después; `git diff` vacío en `analisis/` y `datos/` | OK |
| 11 | Pruebas existentes | 185 de antes de la fase: 185/185 antes y después | OK (ver §5.4) |
| 12 | Git sin `.env` ni credenciales nuevas | `git ls-files` solo muestra `.env.example`; `.env.desarrollo` aparece como ignorado; 0 secretos en el diff | OK |

**Detalle de la prueba 4 (producción):**

- `DEBUG=0` con los valores de desarrollo: no arranca. El mensaje indica que la clave es de desarrollo y que el pepper es corto, sin mostrar valores.
- Sin `SECRET_KEY`: «Falta la variable de entorno SECRET_KEY».
- Pruebas en procesos aparte que rechazan cada caso:
  - falta de cualquiera de los tres secretos, con y sin `DEBUG`;
  - clave de desarrollo o corta;
  - pepper corto;
  - `ALLOWED_HOSTS=*`;
  - producción sin correo real.

**Detalle de la prueba 7 (operaciones autorizadas):**

- Una usuaria con consentimiento guarda igual que antes.
- Tras aceptar el consentimiento, puede escribir.
- El profesional guarda por una paciente (200), y un payload erróneo de profesional sigue dando 400.
- Sin sesión sigue habiendo redirección al ingreso (302), GET sigue dando 405 y CSRF sigue activo.

**Detalle de la prueba 8 (registros):**

- Búsqueda de los secretos en `docker compose logs`: 0.
- Con `DEBUG` desactivado, un error 500 simulado durante la sincronización devuelve una página genérica, sin traza, sin el mensaje del error y sin un marcador de salud puesto en el payload. El registro de `django.request` tampoco lo contiene.
- Sin `DEBUG`, la consola de Django no imprime trazas (filtro `RequireDebugTrue`) y no hay `ADMINS`.

**Suite de Django:** `docker compose run --rm web python manage.py test`, **210/210 OK**: 185 que ya existían y 25 nuevas.

**`check --deploy`** con un perfil de producción completo y valores de prueba (generados al momento y desechados):

- Solo quedan **W004** (HSTS) y **W008** (`SECURE_SSL_REDIRECT`). Ambas son esperadas, porque esos ajustes no se activan hasta confirmar el despliegue.
- Con HTTPS y HSTS pedidos por el entorno quedan W005 y W021 (subdominios y *preload*), que se dejan desactivados a propósito.
- **No hay advertencias de cookies, `DEBUG`, `SECRET_KEY` ni `ALLOWED_HOSTS`.**

**Pruebas de la 40B-0:** `test_40b0_definiciones.py` dio 14/15 tras los cambios de la 40S-1 y, una vez corregida la prueba, **15/15**. Detalle en §5.4.

**Repetición al cierre:**

| Prueba | Resultado |
|---|---|
| Suite de Django | 210/210 OK |
| 40B-0 | 15/15 |
| `test_h11_h13` | OK |
| `test_revision_35b` | OK |
| `test_entropia` | OK |
| Huellas de los 898 archivos protegidos | Idénticas a la línea base |
| Cambios en `analisis/` | Ninguno, salvo `fase40/` |
| Cambios en `datos/` | Ninguno |

## 5. Compatibilidad

### 5.1 Línea base

Antes de cambiar nada se registraron:

- la suite completa (185/185);
- las huellas de la configuración activa dentro del contenedor (solo SHA-256);
- las huellas de 898 archivos protegidos;
- el índice de Git.

### 5.2 Mismos valores activos

Los cuatro valores se copiaron a `.env.desarrollo` desde `HEAD` con un programa que:

- verificó antes que Git ignora el destino y que el destino no existía;
- rechaza valores con comillas o saltos de línea;
- escribe los valores entre comillas simples, para que Docker Compose los tome literalmente;
- nunca los imprimió.

Después del cambio, las huellas de la configuración activa (incluido el hash de un RUT de prueba) son idénticas a las de la línea base. Por lo tanto:

- las cookies de sesión firmadas siguen siendo válidas;
- los enlaces de recuperación ya emitidos siguen siendo válidos;
- las cuentas siguen entrando con su RUT;
- `Identificacion.rut_hash` sigue coincidiendo.

### 5.3 Comportamiento sin cambios

- Desarrollo sigue con `DEBUG=1`, correo por consola o real según `.env`, y cookies sin `Secure`.
- Las encuestas, el cliente, la sincronización y las rondas no cambian. Solo se agrega el 403 por consentimiento.

### 5.4 Prueba de la 40B-0: corregida al cierre

**Problema.** `Reproduccion.test_plataforma_sin_cambios` exigía que `git status -- src` estuviera vacío. Esa condición describía el estado al cerrar la 40B-0 y la rompía cualquier cambio legítimo en `src/` ajeno a la limpieza, como `settings.py` o `api.py`.

**Corrección acotada.** Solo se cambió esa prueba. Ahora comprueba que los cuatro archivos de los que se generaron las definiciones congeladas (`models.py`, `condicionales.py`, `campos_por_rol.py`, `datos_geograficos.py`):

- son iguales, en el árbol de trabajo y en `HEAD`, a los del commit de origen `44bfe0b` (`git diff --quiet --ignore-cr-at-eol`, para que no influya el fin de línea de Windows);
- conservan en git las SHA-256 registradas en `definiciones_fase34.SHA256_ORIGEN`.

La verificación es más precisa que antes: además de detectar cambios sin commit, ahora también detecta un cambio ya commiteado en esos archivos.

**Verificaciones históricas.** Las otras 14 pruebas no se tocaron:

- definiciones idénticas a la plataforma actual y a los commits `32b439c`, `745d689` y `44bfe0b`;
- códigos y cortes del MRS;
- independencia de la limpieza ante una copia alterada de la plataforma;
- salidas byte a byte iguales a las históricas.

**Resultados:**

- **15/15.**
- **Control negativo:** en una copia temporal del repositorio (`git worktree`, eliminada después), con una línea agregada a `models.py`, la prueba corregida **falla**, como corresponde.

**Nota para el futuro.** Cuando se cambie `models.py` de forma autorizada, esta prueba y `test_igual_a_la_plataforma_actual` avisarán, a propósito, que la plataforma ya no coincide con la copia congelada. Eso no significa que la limpieza esté mal; significa que se debe decidir si se crea una versión nueva de las definiciones. Ese día habrá que actualizar esas dos pruebas para que comparen contra el commit de origen y no contra el árbol actual. Es parte de la advertencia R-13.

## 6. Secretos en el historial

**Siguen comprometidos.** Los valores activos de desarrollo están en el historial de Git y en la punta de todas las ramas, salvo `datos-simulados` después de esta fase, cuando se haga el commit:

| Valor | Primer commit en que aparece |
|---|---|
| `SECRET_KEY` | `422d23e` (2026-07-14) |
| `DB_PASSWORD` | `422d23e` (2026-07-14) |
| `RUT_HASH_PEPPER` activo | `a563d66` (2026-09-04) |

Ramas que contienen esos valores: `main`, `datos-simulados`, `ronda3`, `Scarleth29`, `respaldo-antes-coautoria` y las remotas `origin/main`, `origin/datos-simulados`, `origin/ronda3`, `origin/Scarleth29` y **`origin/valeAW`**. Esto responde en parte a S-8: las otras ramas tienen los mismos valores, sin secretos adicionales en estos archivos.

La 40S-1 **no** los rota (instrucción expresa). A partir de esta fase quedan declarados **solo de desarrollo**. El perfil de producción los rechaza: la clave empieza con `django-insecure` y el pepper activo tiene menos de 32 caracteres. Así no pueden llegar por error a un servidor real.

## 7. Qué debe hacerse en la rotación 40S-2

Depende de **DR-1**: ¿hay cuentas o respuestas reales en alguna base? ¿Qué contiene `datos/reales/`?

1. **Si no hay datos reales:** para el primer despliegue, generar una `SECRET_KEY` y un pepper **nuevos** solo en el servidor, nunca en el repositorio, y empezar con la base vacía. Las bases de desarrollo siguen con los valores actuales, declarados como de desarrollo.
2. **Si hay datos reales:**
   - pepper: rotarlo con doble hash (`rut_hash_v2`), migrando al iniciar sesión y en la búsqueda profesional;
   - `SECRET_KEY`: usar `SECRET_KEY_FALLBACKS` para no cerrar todas las sesiones de golpe;
   - evaluar si corresponde notificar, según el protocolo de ética y la Ley 19.628.
3. **Cambiar la contraseña de PostgreSQL** en cada base que la use (`ALTER ROLE`, coordinado con `.env.desarrollo` o el servidor).
4. **Respaldar el pepper nuevo cifrado y fuera del servidor.** Si se pierde, las cuentas pierden su asociación con el RUT.
5. **No reescribir el historial de Git:** basta con rotar.
6. **Coordinar con `valeAW`:** al integrar esta fase, cada integrante necesitará su propio `.env.desarrollo`. Los valores deben pasarse por un canal privado.

## 8. Riesgos que permanecen

| N.º | Riesgo | Severidad | Propuesta |
|---|---|---|---|
| R-1 | Secretos de desarrollo en el historial y en todas las ramas | Crítica antes de usar datos reales | 40S-2 |
| R-2 | **El RUT viaja en la URL** en las búsquedas de `/profesional/buscar/` y `/administracion/` | Alta (privacidad) | Ver §8.1 |
| R-3 | `mi_evaluacion` guarda sin revisar el consentimiento | Baja | Ver §8.1 |
| R-4 | El acceso profesional escribe sin que conste el consentimiento de la paciente | Ética, a decidir | Ver §8.1 y la propuesta (§11) |
| R-5 | HSTS, redirección a HTTPS y proxy apagados | Media al desplegar | Activarlos por entorno cuando se conozca el despliegue (Fase 18, DR-2) |
| R-6 | El contenedor `db` recibe también `SECRET_KEY` y el pepper, porque comparte `env_file` | Baja (solo en local) | Separar en dos archivos si se desea |
| R-7 | `docker compose config` imprime los valores del entorno | Baja | No pegar su salida en chats ni informes |
| R-8 | PostgreSQL publicado en `5432` en todas las interfaces de la máquina | Media en redes compartidas | Enlazar a `127.0.0.1:5432:5432`. No se cambió, porque podría afectar el uso actual |
| R-9 | Sin `DEBUG`, los errores 500 no quedan registrados en ninguna parte (no hay `LOGGING` ni `ADMINS`) | Operativa | Definir registros sin cuerpos de petición al preparar el despliegue |
| R-10 | Sin `DEBUG`, `runserver` no sirve estáticos; producción necesita `collectstatic` y un servidor de estáticos | Operativa al desplegar | Fase de despliegue |
| R-11 | `console.warn(res.cuerpo)` en `encuesta.js` muestra en la consola del navegador los errores de validación (no las respuestas) | Baja | Sin cambio (ya evaluado en la 40A) |
| R-12 | ~~Prueba `test_plataforma_sin_cambios` de la 40B-0 obsoleta~~ | — | **Resuelto al cierre** (§5.4) |
| R-13 | Pruebas de las Fases 35 a 39 que leen `models.py` directamente (advertencia de la 40B-0) | Media antes de cambiar `models.py` | Sin cambios en esta fase |

### 8.1 Detalle de R-2, R-3 y R-4

**R-2. El RUT en la URL.**

- **Dónde:**
  - `templates/encuestas/buscar_paciente.html:14` (`<form method="get">`) y `profesional.py:29` (`request.GET.get('rut')`);
  - `templates/usuarios/admin_panel.html:10` y `administracion.py:53`.
- **Qué pasa:** la búsqueda queda como `/profesional/buscar/?rut=12.345.678-9`. El RUT en claro queda en:
  - el registro de acceso del servidor (`runserver` hoy; `gunicorn` o un proxy en producción);
  - el historial y el autocompletado del navegador del centro de salud;
  - la cabecera `Referer` de la página siguiente (dentro del mismo sitio; `Referrer-Policy: same-origin` impide que salga a otros dominios).
- **Por qué importa:** el sistema guarda el RUT solo como hash para evitar justamente esto (regla 1.2). Los registros del servidor suelen conservarse y copiarse sin las protecciones de la base de datos.
- **Corrección propuesta (no aplicada):**
  - pasar las dos búsquedas a POST, como ya hace `nueva_paciente` (Fase 29);
  - mostrar el resultado en la misma respuesta;
  - para «volver a la ficha», usar el `id` de la ficha, que no es un dato personal.
- **Costo:** dos vistas, dos plantillas y sus pruebas. No requiere migraciones. Cambia el funcionamiento visible del panel, por eso necesita autorización.
- **Mitigación mientras tanto:** en producción, configurar el servidor para que no registre la cadena de consulta, o no habilitar el registro de acceso.

**R-3. `mi_evaluacion` sin consentimiento.**

- **Dónde:** `tablero.py:41`. Exige sesión y que haya una ronda finalizada, pero no revisa el consentimiento vigente.
- **Qué pasa:** en el uso normal no ocurre. Para evaluar hace falta una ficha con al menos una ronda finalizada, y el retiro borra la ficha. El único camino teórico es una usuaria sin consentimiento que se vincula a una ficha creada por una profesional que ya tenía una ronda finalizada (`identificacion_de_usuaria`, `sync.py:84`).
- **Propuesta:** aplicar la regla de un solo punto (C-3 de la propuesta) una vez decidido si la satisfacción cuenta como dato de investigación (DC-4). Mientras tanto no se cambia.

**R-4. Acceso profesional sin consentimiento registrado.**

- **Dónde:** `profesional.py:nueva_paciente` y el modo profesional de `sync.py`. La profesional crea la ficha (`usuario` nulo) y guarda respuestas. La exención del decorador de la 40S-1 mantiene ese funcionamiento.
- **Qué pasa:** el consentimiento presencial puede existir en papel, pero **la plataforma no lo registra**. Además, una profesional puede seguir escribiendo en la ficha de una mujer que se retiró desde su cuenta y luego volvió a ser registrada presencialmente, sin que conste si dio un nuevo consentimiento.
- **Propuesta:** las reglas C-2, C-3 y C-7 de `40S-1_propuesta_consentimiento.md`:
  - la profesional registra el consentimiento presencial en un paso;
  - desde ahí, todo guardado exige consentimiento vigente **de la paciente**, por cualquiera de las dos vías;
  - con eso la exención actual desaparece sin agregar bloqueos.
- **Implementación:** requiere un modelo de eventos y una migración, así que va en una fase autorizada.

## 9. Limitaciones del entorno

- **Docker:** el motor estaba detenido y se inició para esta fase. Al terminar se detuvieron los contenedores `db` y `web`, como estaban. El contenedor `db` se recreó, conservando su volumen, porque cambió su configuración (`env_file`).
- **Django fuera de Docker:** no está instalado; todas las pruebas de Django se corrieron en el contenedor.
- **Producción:** no se probó un servidor real con HTTPS, porque no existe todavía (DR-2). El perfil de producción se probó con `check --deploy` y con procesos aparte, usando valores de prueba.
- **Base de desarrollo:** no se abrió, para evitar tocar posibles datos reales (DR-1). La compatibilidad de sesiones y RUT se demostró por igualdad de huellas, no iniciando sesión con cuentas existentes.
- **Prueba en el navegador:** no se probó el envío de una encuesta completa desde el navegador. El flujo de sincronización está cubierto por las pruebas de Django.

## 10. ¿Se puede cerrar la Fase 40S-1?

**Sí.** Está completo lo autorizado:

- **S-1 a S-5:**
  - los secretos salen del código;
  - el arranque exige las variables;
  - `DEBUG` está apagado por defecto;
  - existe un perfil de producción;
  - la API exige el consentimiento.
- **S-6:** se revisaron los registros. Quedaron los riesgos R-2 y R-9, documentados.
- **S-7:** `check --deploy` está documentado en el README.

Además:

- **Pruebas:** todas pasan (Django 210/210, 40B-0 15/15 y las de análisis relacionadas).
- **Compatibilidad:** la de desarrollo está demostrada.
- **Integridad:** los datos, el resto de Django y las Fases 34 a 39 están intactos.

Lo que queda abierto no bloquea el cierre. Son mejoras que cambian el funcionamiento visible o los modelos (R-2, R-3, R-4), la rotación (40S-2) y decisiones de despliegue (R-5, R-8 a R-10). Cada una necesita su propia autorización.

**Falta para cerrarla formalmente:** tu revisión y la decisión de commit.

No se inició la 40B-1 ni la 40S-2; no se crearon migraciones, no se rotaron secretos y no se hizo commit ni push.

## 11. Propuesta de consentimiento (cierre)

Las reglas acordadas están en **`40S-1_propuesta_consentimiento.md`**. Es una propuesta: no se implementó la reincorporación ni se modificó el retiro.

**Comparación del sistema actual con los ocho criterios:**

| Estado | Criterios |
|---|---|
| Cumple | 1 (varias rondas sin reaceptar) y 6 (sin bloqueos repetidos) |
| Cumple en parte | 3 y 4 |
| No cumple | 2 (consentimiento presencial registrado), 5 (el retiro borra todo en cascada) y 7 (no hay historial: una sola fecha que se sobrescribe) |

**Propuesta:**

- **Un consentimiento por participante:** se otorga en la plataforma o en forma presencial, registrado por la profesional, y vale para todas las rondas.
- **Ficha administrativa:** se puede crear sin consentimiento.
- **Respuestas de investigación:** solo con consentimiento vigente, verificado en un único punto del servidor.
- **Retiro:** detiene la recolección; qué se conserva lo define el protocolo.
- **Reincorporación:** es una nueva aceptación, no una restauración de datos.
- **Registro:** un registro de eventos que solo se amplía (otorgado, retirado, reincorporado), sin datos de salud.

**Encaje con la 40S-1:**

- El 403 de la API **es compatible** con la propuesta y se conserva.
- La exención del profesional es **transitoria**: con la propuesta se reemplaza por «escribir solo si la paciente tiene consentimiento vigente».

**Decisiones pendientes (de la responsable o la profesora): DC-1 a DC-6.**

| N.º | Decisión |
|---|---|
| DC-1 | Qué se conserva tras el retiro |
| DC-2 | Qué contiene la ficha administrativa |
| DC-3 | Qué datos mínimos se registran del consentimiento presencial |
| DC-4 | Si la satisfacción exige consentimiento |
| DC-5 | Cuándo un cambio del documento obliga a pedir el consentimiento de nuevo |
| DC-6 | Si los datos conservados se vuelven a vincular al reincorporarse |
