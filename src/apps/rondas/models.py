"""
Fase 40B-1: infraestructura del historial de rondas (sin cambio de comportamiento).

- RondaEvaluacion: una fila por ronda de cada participante, con su número,
  su estado y lo que se sabe de ella. Identificacion.ronda_actual se conserva
  por compatibilidad y debe coincidir siempre con la ronda ABIERTA.
- EventoRonda: registro de solo inserción de lo que le pasa a cada ronda,
  sin contenido de las respuestas de salud.

Lo que no se sabe queda nulo y marcado: nunca se deduce (ver retrocarga,
migración 0002). Los nombres de las clases de opciones son únicos en todo el
proyecto (regla de la 40A, §3.4).
"""
from django.conf import settings
from django.db import models
from django.db.models import Q

# Versión del cuestionario para las rondas que se abren desde la 40B-1: la
# vigente desde el último cambio del cuestionario (models.py y esquema.py en
# 32c399d, 2026-10-01). Si el cuestionario cambia, se crea un valor nuevo.
VERSION_CUESTIONARIO_ACTUAL = '2026-10-01'
# Rondas existentes antes de la 40B-1: no se sabe con qué versión se respondieron.
VERSION_DESCONOCIDA = 'DESCONOCIDA_ANTERIOR_40B'


class EstadoRonda(models.TextChoices):
    ABIERTA = 'ABIERTA', 'Abierta'
    CERRADA = 'CERRADA', 'Cerrada'
    ANULADA = 'ANULADA', 'Anulada'


class OrigenRonda(models.TextChoices):
    NORMAL = 'NORMAL', 'Registrada al ocurrir'
    RETROCARGA = 'RETROCARGA', 'Reconstruida de datos anteriores a la 40B-1'


class RolCierre(models.TextChoices):
    USUARIA = 'USUARIA', 'Usuaria común'
    PROFESIONAL = 'PROFESIONAL', 'Profesional de salud'
    # La 40B-1 registra el cierre sin tocar sync.py, así que no sabe quién cerró.
    NO_REGISTRADO = 'NO_REGISTRADO', 'No registrado (40B-1)'
    DESCONOCIDO = 'DESCONOCIDO', 'Desconocido (anterior a la 40B-1)'


class RondaEvaluacion(models.Model):
    participante = models.ForeignKey(
        'encuestas.Identificacion', on_delete=models.CASCADE, related_name='rondas_evaluacion',
        help_text='El retiro del estudio borra la ficha y, con ella, este registro (sin cambios en el retiro).',
    )
    numero = models.PositiveIntegerField()
    estado = models.CharField(max_length=10, choices=EstadoRonda.choices)
    origen = models.CharField(max_length=12, choices=OrigenRonda.choices)
    abierta_en = models.DateTimeField(null=True, blank=True, help_text='Nulo si no se sabe.')
    cerrada_en = models.DateTimeField(null=True, blank=True, help_text='Nulo si está abierta o no se sabe.')
    cerrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    cerrada_por_rol = models.CharField(max_length=14, choices=RolCierre.choices, blank=True)
    # Clave de idempotencia del cierre: la usará la 40B-2. Nula en la 40B-1.
    id_cierre = models.UUIDField(null=True, blank=True, unique=True)
    version_cuestionario = models.CharField(max_length=40)
    # Qué se sabe y qué no de la ronda (secciones presentes, limitaciones). Sin respuestas.
    observaciones = models.JSONField(default=dict, blank=True)
    registrada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ronda de evaluación'
        verbose_name_plural = 'rondas de evaluación'
        ordering = ['participante_id', 'numero']
        constraints = [
            models.UniqueConstraint(fields=['participante', 'numero'], name='ronda_numero_unico_por_participante'),
            models.UniqueConstraint(fields=['participante'], condition=Q(estado='ABIERTA'),
                                    name='una_ronda_abierta_por_participante'),
            models.CheckConstraint(condition=Q(numero__gte=1), name='ronda_numero_desde_1'),
            models.CheckConstraint(condition=~Q(estado='ABIERTA') | Q(cerrada_en__isnull=True),
                                   name='ronda_abierta_sin_fecha_de_cierre'),
        ]

    def __str__(self):
        return f'Ronda {self.numero} ({self.get_estado_display()}) de la ficha {self.participante_id}'


class TipoEventoRonda(models.TextChoices):
    APERTURA = 'APERTURA', 'Apertura'
    CIERRE = 'CIERRE', 'Cierre'
    RETROCARGA = 'RETROCARGA', 'Reconstruida en la migración 40B-1'
    INCOHERENCIA = 'INCOHERENCIA', 'ronda_actual no coincide con el registro'
    # Previstos para la 40B-2 (no se emiten todavía):
    GUARDADO = 'GUARDADO', 'Guardado de secciones'
    CIERRE_RECHAZADO = 'CIERRE_RECHAZADO', 'Cierre rechazado'
    REINTENTO_IDEMPOTENTE = 'REINTENTO_IDEMPOTENTE', 'Reintento idempotente'
    ESCRITURA_RECHAZADA_RONDA_CERRADA = 'ESCRITURA_RECHAZADA', 'Escritura rechazada: ronda cerrada'
    CORRECCION_ADMINISTRATIVA = 'CORRECCION_ADMIN', 'Corrección administrativa'


class EventoRondaInmutable(Exception):
    """Un evento de ronda no se modifica ni se borra uno por uno."""


class EventoRonda(models.Model):
    """Registro de solo inserción. `datos` nunca contiene respuestas de salud."""
    ronda = models.ForeignKey(RondaEvaluacion, on_delete=models.CASCADE, related_name='eventos')
    tipo = models.CharField(max_length=24, choices=TipoEventoRonda.choices)
    momento = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    actor_rol = models.CharField(max_length=14, choices=RolCierre.choices, blank=True)
    datos = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'evento de ronda'
        verbose_name_plural = 'eventos de ronda'
        ordering = ['ronda_id', 'momento', 'id']

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise EventoRondaInmutable('Los eventos de ronda no se modifican.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise EventoRondaInmutable('Los eventos de ronda no se borran uno por uno.')

    def __str__(self):
        return f'{self.get_tipo_display()} — ronda {self.ronda_id}'


class MRSAnterior40B2(models.Model):
    """
    Fase 40B-2: marca de un registro MRS guardado ANTES de que sus ítems admitieran nulo.

    Hasta la 40B-2 un ítem MRS omitido se guardaba como 0, así que en estos
    registros un 0 puede ser una respuesta real («Ninguna») o un valor por
    defecto. No se sabe cuál y no se adivina: el valor se conserva tal cual y
    este registro lo declara.

    - Ronda cerrada: los ceros quedan como históricos no verificables, para siempre
      (la ronda no admite escrituras).
    - Ronda abierta: cada 0 queda «por confirmar» hasta que quien responde lo elija
      explícitamente en la encuesta (`items_confirmados`). La ronda no se puede
      cerrar con ceros sin confirmar.

    Solo guarda nombres de ítems, nunca valores. Se borra junto con el MRS (retiro).
    """
    mrs = models.OneToOneField('encuestas.MRS', on_delete=models.CASCADE, related_name='marca_anterior_40b2')
    items_confirmados = models.JSONField(default=list, blank=True)
    registrada_en = models.DateTimeField(auto_now_add=True)
    confirmado_en = models.DateTimeField(null=True, blank=True,
                                         help_text='Cuándo quedaron confirmados todos sus ceros (si ocurrió).')

    class Meta:
        verbose_name = 'MRS anterior a la 40B-2'
        verbose_name_plural = 'MRS anteriores a la 40B-2'

    def ceros_por_confirmar(self, mrs=None):
        mrs = mrs or self.mrs
        confirmados = set(self.items_confirmados or [])
        return [f'pregunta_{i}' for i in range(1, 12)
                if getattr(mrs, f'pregunta_{i}') == 0 and f'pregunta_{i}' not in confirmados]

    def __str__(self):
        return f'MRS {self.mrs_id} anterior a la 40B-2'
