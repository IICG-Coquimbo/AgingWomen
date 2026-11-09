from django.contrib.auth.base_user import BaseUserManager
from django.utils.crypto import get_random_string

from .rut import hash_rut, validar_rut

# Alfabeto sin caracteres ambiguos (0/O, 1/l/I) para contraseñas autogeneradas.
_ALFABETO_PASSWORD = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789'


def generar_password(longitud=10):
    """Genera una contraseña aleatoria legible para enviar por correo."""
    return get_random_string(longitud, _ALFABETO_PASSWORD)


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def _crear(self, rut, email, password, rol, **extra):
        if not rut:
            raise ValueError('El RUT es obligatorio')
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        usuario = self.model(
            rut_hash=hash_rut(rut),
            email=self.normalize_email(email),
            rol=rol,
            **extra,
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, rut, email, password=None, rol=None, **extra):
        """
        Crea una cuenta. Si no se entrega contraseña, se genera una al azar que no
        se guarda ni se comunica a nadie: la persona define la suya con el enlace
        de activación o con «Olvidé mi contraseña».
        """
        from .models import Usuario

        extra.setdefault('is_staff', False)
        extra.setdefault('is_superuser', False)
        if rol is None:
            rol = Usuario.Rol.USUARIA_COMUN

        if password is None:
            password = generar_password()

        return self._crear(rut, email, password, rol, **extra)

    def create_superuser(self, rut_hash=None, email=None, password=None, **extra):
        """
        Usado por `manage.py createsuperuser`. El valor que se escribe en el
        prompt "RUT" llega como `rut_hash` (nombre del USERNAME_FIELD) pero es
        el RUT en claro: aquí se normaliza y se hashea.
        """
        from .models import Usuario

        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('rol', Usuario.Rol.PROFESIONAL_SALUD)
        if extra.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True')
        if extra.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True')
        if not password:
            raise ValueError('El superusuario requiere una contraseña explícita')
        if not validar_rut(rut_hash or ''):
            raise ValueError('RUT inválido: revisa el dígito verificador.')

        rol = extra.pop('rol')
        return self._crear(rut_hash, email, password, rol, **extra)
