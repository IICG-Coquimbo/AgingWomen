"""
Fase 40B-1: mantiene RondaEvaluacion al día sin modificar sync.py.

Escucha post_save de Identificacion, que es por donde pasan los dos momentos
relevantes de hoy:
- creación de la ficha (sync.py:142, ident.save()) → se abre la ronda 1;
- cierre (sync.py:242-244, ronda_actual += 1 y ultima_finalizacion_en) →
  se cierra la ronda abierta, se registra la verificación de completitud en
  modo observación y se abre la siguiente.

Fase 40B-2: el cierre normal lo hace ahora apps.rondas.cierre, de forma
explícita y validada (cierra la ronda, abre la siguiente y recién entonces
avanza ronda_actual), así que esta señal ve «sin_cambio». La rama de cierre de
la señal queda solo como respaldo si algún camino ajeno al servicio avanza
ronda_actual; ese cierre se marca con via='senal_fuera_del_servicio'.

Nunca impide el guardado: si algo falla, se registra en el log (sin datos de
la participante) y la encuesta sigue igual que antes. La incoherencia, si la
hay, la detecta `manage.py verificar_rondas`.
"""
import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.encuestas.models import Identificacion

from .models import (VERSION_CUESTIONARIO_ACTUAL, EstadoRonda, EventoRonda, OrigenRonda, RolCierre,
                     RondaEvaluacion, TipoEventoRonda)

logger = logging.getLogger(__name__)


def _abrir(participante, numero, momento, actor=None, actor_rol=RolCierre.NO_REGISTRADO):
    ronda = RondaEvaluacion.objects.create(
        participante=participante, numero=numero, estado=EstadoRonda.ABIERTA, origen=OrigenRonda.NORMAL,
        abierta_en=momento, version_cuestionario=VERSION_CUESTIONARIO_ACTUAL,
    )
    EventoRonda.objects.create(ronda=ronda, tipo=TipoEventoRonda.APERTURA, actor=actor, actor_rol=actor_rol)
    return ronda


def actualizar_registro(participante):
    """Alinea el registro con participante.ronda_actual. Devuelve lo que hizo (para pruebas)."""
    from .completitud import evaluar  # import diferido: evita ciclos al cargar las apps

    abierta = (RondaEvaluacion.objects.select_for_update()
               .filter(participante=participante, estado=EstadoRonda.ABIERTA).first())
    actual = participante.ronda_actual

    if abierta is None:
        if RondaEvaluacion.objects.filter(participante=participante, numero=actual).exists():
            ronda = RondaEvaluacion.objects.get(participante=participante, numero=actual)
            EventoRonda.objects.create(ronda=ronda, tipo=TipoEventoRonda.INCOHERENCIA,
                                       datos={'ronda_actual': actual, 'ronda_abierta': None})
            return 'incoherencia'
        _abrir(participante, actual, timezone.now())
        return 'apertura'

    if abierta.numero == actual:
        return 'sin_cambio'

    if actual == abierta.numero + 1:
        # Cierre: lo hizo sync.py en este mismo save. La hora es la que sync.py registró.
        cerrada_en = participante.ultima_finalizacion_en
        observacion = evaluar(participante, abierta.numero)
        abierta.estado = EstadoRonda.CERRADA
        abierta.cerrada_en = cerrada_en
        abierta.cerrada_por_rol = RolCierre.NO_REGISTRADO
        if cerrada_en is None:
            abierta.observaciones = {**abierta.observaciones, 'cerrada_en': 'no_registrada'}
        abierta.save(update_fields=['estado', 'cerrada_en', 'cerrada_por_rol', 'observaciones'])
        EventoRonda.objects.create(ronda=abierta, tipo=TipoEventoRonda.CIERRE, actor_rol=RolCierre.NO_REGISTRADO,
                                   datos={'completitud': observacion, 'via': 'senal_fuera_del_servicio'})
        if not observacion['completa']:
            # Solo se informa: en la 40B-1 el cierre no se rechaza.
            logger.info('rondas: cierre que la 40B-2 rechazaría (ficha %s, ronda %s, %s secciones con faltantes)',
                        participante.pk, abierta.numero, len(observacion['faltantes']))
        _abrir(participante, actual, cerrada_en or timezone.now())
        return 'cierre'

    EventoRonda.objects.create(ronda=abierta, tipo=TipoEventoRonda.INCOHERENCIA,
                               datos={'ronda_actual': actual, 'ronda_abierta': abierta.numero})
    return 'incoherencia'


@receiver(post_save, sender=Identificacion, dispatch_uid='rondas_actualizar_registro')
def al_guardar_identificacion(sender, instance, created, raw=False, **kwargs):
    if raw:  # carga de fixtures
        return
    try:
        with transaction.atomic():
            actualizar_registro(instance)
    except Exception:  # noqa: BLE001  (el registro nunca debe impedir guardar la encuesta)
        logger.exception('rondas: no se pudo actualizar el registro de la ficha %s', instance.pk)
