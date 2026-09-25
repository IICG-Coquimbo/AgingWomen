from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

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

    @property
    def es_admin_tecnico(self):
        return self.is_staff or self.is_superuser


class PerfilUsuaria(models.Model):
    """Perfil independiente de una participante del estudio."""

    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name='perfil_usuaria',
    )
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_ultimo_periodo_menstrual = models.DateField(null=True, blank=True)
    menopausia_quirurgica_inducida = models.BooleanField(null=True, blank=True)
    fupm_no_aplica_por_cirugia = models.BooleanField(default=False)
    edad_calculada = models.PositiveSmallIntegerField(null=True, blank=True)
    validacion_inicial_en = models.DateTimeField(null=True, blank=True)
    consentimiento_aceptado = models.BooleanField(default=False)
    consentimiento_aceptado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'perfil de usuaria'
        verbose_name_plural = 'perfiles de usuarias'


class PerfilMedico(models.Model):
    """Perfil independiente del personal médico."""

    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name='perfil_medico',
    )
    especialidad = models.CharField(max_length=120)
    registro_medico = models.CharField(max_length=80, unique=True)
    institucion = models.CharField(max_length=160)
    aprobado = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'perfil médico'
        verbose_name_plural = 'perfiles médicos'


class RegistroOTP(models.Model):
    """Código temporal para verificar el correo antes de crear una cuenta."""

    email = models.EmailField()
    rut_hash = models.CharField(max_length=64)
    tipo_cuenta = models.CharField(max_length=12, choices=Usuario.Rol.choices)
    codigo_hash = models.CharField(max_length=128)
    expira_en = models.DateTimeField()
    intentos = models.PositiveSmallIntegerField(default=0)
    validado_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def esta_vigente(self):
        return self.validado_en is None and timezone.now() < self.expira_en
