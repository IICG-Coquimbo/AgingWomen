# AgingWomen — Plataforma de Investigación de Menopausia

Aplicación web/móvil (Django + Docker) para una investigación sobre menopausia y
climaterio en Chile. Encuesta multisección con soporte offline, control de acceso
por RUT (hasheado) y roles.

## Puesta en marcha

Requiere Docker y Docker Compose.

```bash
docker compose up -d db          # base de datos PostgreSQL
docker compose build web         # instala dependencias (Django, bcrypt, ...)
docker compose run --rm web python manage.py migrate
docker compose up -d             # levanta la app en http://localhost:8000
```

### Crear cuentas

```bash
# Personal del servicio de salud (rol PROFESIONAL). Imprime la contraseña generada.
docker compose run --rm web python manage.py crear_profesional 11.111.111-1 profesional@ejemplo.cl

# Superusuario para el panel /admin (en el prompt "RUT" se escribe un RUT válido)
docker compose run --rm web python manage.py createsuperuser
```

Las **usuarias comunes** se registran solas en `/cuenta/registro/` (solo RUT +
correo). En desarrollo, la contraseña autogenerada se imprime en la consola del
servidor (`docker compose logs web`).

### Tests

```bash
docker compose run --rm web python manage.py test
```

## Estructura

| App | Rol |
|---|---|
| `apps.usuarios` | modelo `Usuario` (login por `rut_hash`), roles, registro/login, recuperación de contraseña |
| `apps.encuestas` | modelos de las 8 secciones, formularios por rol, esquema JSON (`/api/esquema/`), sincronización (`/api/sincronizar/`), app cliente offline |

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
| `/admin/` | panel de administración |

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
