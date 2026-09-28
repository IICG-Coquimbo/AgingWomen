import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

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
    consentimiento_aceptado_en = models.DateTimeField(
        'consentimiento informado aceptado el',
        null=True,
        blank=True,
        help_text='Se completa automáticamente al aceptar la pantalla de consentimiento. Bloquea el acceso a la encuesta mientras esté vacío.',
    )

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


class RegistroOTP(models.Model):
    """
    Registro pendiente de verificación de correo (Fase 21). La cuenta recién
    se crea cuando la persona ingresa el código de 6 dígitos que se le envió.
    El código y la contraseña elegida se guardan solo hasheados.
    """

    VIGENCIA = timedelta(minutes=10)
    MAX_INTENTOS = 5
    ESPERA_REENVIO = timedelta(minutes=1)

    rut_hash = models.CharField(max_length=64)
    email = models.EmailField()
    password_hash = models.CharField(max_length=128)
    codigo_hash = models.CharField(max_length=64)
    intentos = models.PositiveSmallIntegerField(default=0)
    enviado_en = models.DateTimeField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'registro pendiente de verificación'
        verbose_name_plural = 'registros pendientes de verificación'

    @staticmethod
    def _hash_codigo(codigo):
        return salted_hmac('usuarios.RegistroOTP', codigo).hexdigest()

    def nuevo_codigo(self):
        """Genera un código nuevo (reinicia vigencia e intentos) y lo devuelve en claro."""
        codigo = f'{secrets.randbelow(10 ** 6):06d}'
        self.codigo_hash = self._hash_codigo(codigo)
        self.intentos = 0
        self.enviado_en = timezone.now()
        return codigo

    @property
    def vencido(self):
        return timezone.now() > self.enviado_en + self.VIGENCIA

    @property
    def agotado(self):
        return self.intentos >= self.MAX_INTENTOS

    @property
    def puede_reenviar(self):
        return timezone.now() >= self.enviado_en + self.ESPERA_REENVIO

    def codigo_correcto(self, codigo):
        return constant_time_compare(self._hash_codigo((codigo or '').strip()), self.codigo_hash)
