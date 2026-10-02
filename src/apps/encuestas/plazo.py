"""
Plazo entre rondas (Fase 31): tras finalizar una ronda, la usuaria puede volver
a responder la encuesta recién después de DIAS_ENTRE_RONDAS días calendario
(hora de Chile). El plazo corre también si la ronda la finalizó el personal de
salud. El personal de salud no tiene esta restricción.
"""
from datetime import timedelta

from django.utils import timezone

DIAS_ENTRE_RONDAS = 15


def disponible_desde(ident):
    """Fecha desde la que puede responder otra ronda, o None si no hay espera."""
    if ident is None or ident.ultima_finalizacion_en is None:
        return None
    return timezone.localdate(ident.ultima_finalizacion_en) + timedelta(days=DIAS_ENTRE_RONDAS)


def encuesta_bloqueada(ident):
    fecha = disponible_desde(ident)
    return fecha is not None and timezone.localdate() < fecha


def dias_restantes(ident):
    fecha = disponible_desde(ident)
    return (fecha - timezone.localdate()).days if fecha else 0


def mensaje_espera(ident):
    fecha = disponible_desde(ident)
    dias = dias_restantes(ident)
    return (f'Podrás volver a responder la encuesta a partir del {fecha:%d-%m-%Y} '
            f'(en {dias} día{"s" if dias != 1 else ""}).')
