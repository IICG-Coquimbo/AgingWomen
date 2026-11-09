"""
Fase 40B-2: las respuestas de una ronda cerrada no cambian en silencio.

Una señal pre_save sobre las 7 secciones de la encuesta impide, desde
cualquier camino que use save() (sincronización, shell, código futuro):

- modificar una fila que pertenece a una ronda ya cerrada;
- mover una fila a otra ronda o a otra participante;
- crear una fila nueva en una ronda ya cerrada.

La sincronización ya rechazaba esos casos (uuid de ronda cerrada, control de
ronda); esto es la segunda barrera. Una corrección administrativa futura
deberá hacerse a propósito, dentro de `correccion_administrativa()`, y
registrar un evento CORRECCION_ADMIN (aún no existe esa funcionalidad).

El borrado no se bloquea: el retiro del estudio elimina la ficha y todo lo
suyo en cascada, como está definido.
"""
from contextlib import contextmanager
from contextvars import ContextVar

from django.db.models.signals import pre_save

from apps.encuestas.models import Identificacion
from apps.encuestas.sync import SECCIONES

_correccion = ContextVar('rondas_correccion_administrativa', default=False)


class RespuestaHistoricaProtegida(Exception):
    """Intento de cambiar respuestas de una ronda cerrada."""


@contextmanager
def correccion_administrativa():
    """Único camino previsto para corregir una ronda cerrada (no se usa todavía)."""
    marca = _correccion.set(True)
    try:
        yield
    finally:
        _correccion.reset(marca)


def proteger_ronda_cerrada(sender, instance, raw=False, **kwargs):
    if raw or _correccion.get():
        return
    actual = (Identificacion.objects.filter(pk=instance.participante_id)
              .values_list('ronda_actual', flat=True).first())
    if instance.pk is None:
        if actual is not None and instance.ronda < actual:
            raise RespuestaHistoricaProtegida(
                f'No se crean respuestas en la ronda {instance.ronda}: ya está cerrada.')
        return
    anterior = sender.objects.filter(pk=instance.pk).values('ronda', 'participante_id').first()
    if anterior is None:
        return
    if anterior['participante_id'] != instance.participante_id or anterior['ronda'] != instance.ronda:
        raise RespuestaHistoricaProtegida('Una respuesta guardada no cambia de ronda ni de participante.')
    actual_anterior = (Identificacion.objects.filter(pk=anterior['participante_id'])
                       .values_list('ronda_actual', flat=True).first())
    if actual_anterior is not None and anterior['ronda'] < actual_anterior:
        raise RespuestaHistoricaProtegida(
            f'La ronda {anterior["ronda"]} está cerrada: sus respuestas no se modifican.')


def conectar():
    for modelo, _form in SECCIONES.values():
        pre_save.connect(proteger_ronda_cerrada, sender=modelo,
                         dispatch_uid=f'rondas_proteger_{modelo._meta.label_lower}')
