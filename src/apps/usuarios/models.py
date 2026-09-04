from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UsuarioManager


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Cuenta de acceso a la plataforma (regla 1.1: no existe modo invitado).

    No se guardan nombres ni apellidos (regla 1.2). El RUT solo se almacena
    hasheado en `rut_hash`, que además es el identificador de acceso.
    """

    class Rol(models.TextChoices):
        USUARIA_COMUN = 'USUARIA', 'Usuaria común'
        PROFESIONAL_SALUD = 'PROFESIONAL', 'Profesional / Personal del servicio de salud'

    rut_hash = models.CharField(
        'RUT',
        max_length=64,
        unique=True,
        editable=False,
        help_text='HMAC-SHA256 del RUT normalizado. El RUT en claro no se almacena.',
    )
    email = models.EmailField(
        'correo electrónico',
        unique=True,
        help_text='Se usa exclusivamente para el envío y la recuperación de la contraseña.',
    )
    rol = models.CharField(
        max_length=12,
        choices=Rol.choices,
        default=Rol.USUARIA_COMUN,
    )

    is_active = models.BooleanField('activo', default=True)
    is_staff = models.BooleanField('acceso al panel de administración', default=False)
    date_joined = models.DateTimeField('fecha de registro', auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'rut_hash'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_rol_display()} ({self.rut_hash[:8]}…)'

    @property
    def es_profesional(self):
        return self.rol == self.Rol.PROFESIONAL_SALUD

    @property
    def es_usuaria_comun(self):
        return self.rol == self.Rol.USUARIA_COMUN
