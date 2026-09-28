# AgingWomen — Observatorio Integral de la Mujer en peri y menopausia

Aplicación web/móvil (Django + Docker) para una investigación sobre menopausia y
climaterio en Chile. Encuesta multisección con soporte offline, control de acceso
por RUT (hasheado) y roles.

Al abrir la encuesta se muestran las definiciones de perimenopausia y menopausia
y un **filtro de edad**: solo pueden participar personas de **40 a 60 años**
(bajo 40 solo con excepción por menopausia quirúrgica o ausencia prolongada de
menstruación; se valida también en el servidor).

## Puesta en marcha

Requiere Docker y Docker Compose.

```bash
docker compose up -d db          # base de datos PostgreSQL
docker compose build web         # instala dependencias (Django, bcrypt, ...)
docker compose run --rm web python manage.py migrate
docker compose up -d             # levanta la app en http://localhost:8000
```

### Correo (opcional)

Las credenciales de correo **no van en el repositorio**. Copia `.env.example`
como `.env` (en la raíz, junto a `docker-compose.yml`) y completa
`EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` (en Gmail, una *contraseña de
aplicación*, no la contraseña normal). `.env` está en `.gitignore`. Luego
`docker compose up -d` para que tome los valores. Sin `.env`, los correos
(código OTP, bienvenida, recuperación) se imprimen en `docker compose logs web`.

### Crear cuentas

```bash
# Personal del servicio de salud (rol PROFESIONAL). Imprime la contraseña generada.
docker compose run --rm web python manage.py crear_profesional 11.111.111-1 profesional@ejemplo.cl

# Superusuario para el panel /admin (en el prompt "RUT" se escribe un RUT válido)
docker compose run --rm web python manage.py createsuperuser
```

Las **usuarias comunes** se registran solas en `/cuenta/registro/`: RUT, correo
y contraseña elegida, confirmando el correo con un código OTP (en desarrollo, el
código se imprime en `docker compose logs web`).

### Tests

```bash
docker compose run --rm web python manage.py test
```

## Estructura

| App | Rol |
|---|---|
| `apps.usuarios` | modelo `Usuario` (login por `rut_hash`), roles, registro/login, recuperación de contraseña |
| `apps.encuestas` | modelos de las secciones (Identificación, Trabajo, Tareas de cuidado, MRS, EMPA, Hábitos de vida, Actividad física, Conocimiento del sistema), formularios por rol, esquema JSON (`/api/esquema/`), sincronización (`/api/sincronizar/`), app cliente offline. La encuesta se presenta en 9 pantallas (el MRS y su cuestionario complementario van separados). |

### Endpoints principales

| Ruta | Descripción |
|---|---|
| `/` | inicio (requiere login) |
| `/cuenta/registro/`, `/cuenta/ingresar/`, `/cuenta/salir/` | acceso |
| `/cuenta/clave/...` | recuperar / cambiar contraseña |
| `/encuesta/` | app cliente de la encuesta (offline-first) |
| `/api/esquema/` | estructura de la encuesta como JSON |
| `/api/sincronizar/` | recibe las respuestas acumuladas en el dispositivo (POST) |
| `/api/estado/` | qué secciones ya tiene la usuaria |
| `/sw.js` | service worker (soporte offline) |
| `/admin/` | panel de administración (solo cuentas; los datos clínicos se ven en el panel profesional) |

## Configuración

Variables de entorno relevantes (ver `docker-compose.yml`):

| Variable | Uso |
|---|---|
| `RUT_HASH_PEPPER` | secreto para el hash HMAC-SHA256 del RUT. **En producción debe ser un valor secreto y estable** (si cambia, los RUT dejan de coincidir). |
| `SECRET_KEY`, `DB_*`, `DEBUG` | estándar de Django |

## Personalización visual

Toda la paleta está en `src/static/css/tema.css` (bloque `:root`). Ver
`src/static/PALETA.md` para cambiar el color corporativo sin tocar HTML.

## Notas técnicas

- El RUT **nunca** se guarda en claro: solo su hash (`apps/usuarios/rut.py`).
- Las contraseñas usan bcrypt (`PASSWORD_HASHERS` en `settings.py`).
- `django-fernet-encrypted-fields` sigue como dependencia porque la migración
  histórica `encuestas/0001` lo referencia, aunque ya no se usa en el código.
  Se puede eliminar con un *squash* de migraciones.
- Cambiar `AUTH_USER_MODEL` obligó a recrear la base de datos; si se clona el
  repo, basta con `migrate` sobre una BD vacía.
