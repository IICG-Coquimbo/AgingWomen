"""
Fase 40B-2: cierre validado, transaccional e idempotente de una ronda.

Lo llama apps.encuestas.sync dentro de su transacción, con la ficha ya
bloqueada (SELECT ... FOR UPDATE), así que dos cierres simultáneos de la misma
participante se ordenan: el segundo ve la ronda ya cerrada.

Reglas (aprobadas en el plan 40A/40B):
- Solo se cierra si están completas las respuestas obligatorias aplicables
  (completitud en modo obligatorio, con el esquema del rol de quien cierra).
- Un cierre incompleto se rechaza SIN perder nada: las secciones del mismo
  envío ya quedaron guardadas como borrador; se informa qué falta.
- `id_cierre` (UUID que genera el cliente al pulsar Finalizar) hace el cierre
  idempotente: repetir la misma solicitud devuelve el mismo resultado sin
  volver a escribir.
- Quién cerró (cuenta y rol) queda registrado en la ronda y en el evento.

Los eventos guardan nombres de secciones y preguntas, nunca valores.
"""
import uuid

from django.utils import timezone

from apps.encuestas.models import Identificacion

from .completitud import MODO_OBLIGATORIO, evaluar
from .models import EstadoRonda, EventoRonda, RolCierre, RondaEvaluacion, TipoEventoRonda
from .senales import _abrir


def rol_de(usuario):
    return RolCierre.PROFESIONAL if usuario.es_profesional else RolCierre.USUARIA


def ronda_abierta(ficha, usuario=None):
    """La ronda ABIERTA de la ficha, bloqueada. Si el registro no la tiene (incoherencia), se crea."""
    abierta = (RondaEvaluacion.objects.select_for_update()
               .filter(participante=ficha, estado=EstadoRonda.ABIERTA).first())
    if abierta is not None and abierta.numero == ficha.ronda_actual:
        return abierta
    if abierta is not None:
        # Registro desalineado con ronda_actual: no se adivina qué pasó; se informa.
        EventoRonda.objects.create(ronda=abierta, tipo=TipoEventoRonda.INCOHERENCIA,
                                   datos={'ronda_actual': ficha.ronda_actual, 'ronda_abierta': abierta.numero,
                                          'detectada_en': 'cierre_40B2'})
        return None
    existente = RondaEvaluacion.objects.filter(participante=ficha, numero=ficha.ronda_actual).first()
    if existente is not None:
        EventoRonda.objects.create(ronda=existente, tipo=TipoEventoRonda.INCOHERENCIA,
                                   datos={'ronda_actual': ficha.ronda_actual, 'ronda_abierta': None,
                                          'detectada_en': 'cierre_40B2'})
        return None
    return _abrir(ficha, ficha.ronda_actual, timezone.now(),
                  actor=usuario, actor_rol=rol_de(usuario) if usuario else RolCierre.NO_REGISTRADO)


def cierre_previo(ficha, id_cierre):
    """La ronda ya cerrada con este id_cierre, o None. Lanza ValueError si es de otra participante."""
    if id_cierre is None:
        return None
    previa = RondaEvaluacion.objects.filter(id_cierre=id_cierre).first()
    if previa is not None and (ficha is None or previa.participante_id != ficha.pk):
        raise ValueError('id_cierre de otra participante')
    return previa


def registrar_reintento(ronda, usuario):
    EventoRonda.objects.create(ronda=ronda, tipo=TipoEventoRonda.REINTENTO_IDEMPOTENTE, actor=usuario,
                               actor_rol=rol_de(usuario), datos={'id_cierre': str(ronda.id_cierre)})


def registrar_escritura_rechazada(ficha, ronda_enviada, usuario, secciones, codigo):
    """Una solicitud llegó para una ronda que no es la abierta (tardía, o de otro dispositivo)."""
    destino = (RondaEvaluacion.objects.filter(participante=ficha, numero=ronda_enviada).first()
               if isinstance(ronda_enviada, int) else None)
    destino = destino or RondaEvaluacion.objects.filter(participante=ficha, estado=EstadoRonda.ABIERTA).first()
    if destino is None:
        return
    EventoRonda.objects.create(
        ronda=destino, tipo=TipoEventoRonda.ESCRITURA_RECHAZADA_RONDA_CERRADA, actor=usuario,
        actor_rol=rol_de(usuario),
        datos={'codigo': codigo, 'ronda_enviada': ronda_enviada, 'ronda_actual': ficha.ronda_actual,
               'secciones': sorted(set(secciones))},
    )


def cerrar(ficha, usuario, id_cierre=None):
    """
    Intenta cerrar la ronda en curso de `ficha` (ya bloqueada por quien llama).

    Devuelve {'estado': 'cerrada' | 'rechazado', 'ronda', 'id_cierre'?, 'faltantes'?}.
    """
    numero = ficha.ronda_actual
    abierta = ronda_abierta(ficha, usuario)
    if abierta is None:
        return {'estado': 'rechazado', 'ronda': numero, 'motivo': 'registro_incoherente',
                'faltantes': []}

    resultado = evaluar(ficha, numero, rol=usuario.rol, modo=MODO_OBLIGATORIO)
    if not resultado['completa']:
        EventoRonda.objects.create(ronda=abierta, tipo=TipoEventoRonda.CIERRE_RECHAZADO, actor=usuario,
                                   actor_rol=rol_de(usuario),
                                   datos={'completitud': resultado,
                                          'id_cierre': str(id_cierre) if id_cierre else None})
        return {'estado': 'rechazado', 'ronda': numero, 'motivo': 'incompleta',
                'faltantes': resultado['faltantes']}

    ahora = timezone.now()
    abierta.estado = EstadoRonda.CERRADA
    abierta.cerrada_en = ahora
    abierta.cerrada_por = usuario
    abierta.cerrada_por_rol = rol_de(usuario)
    abierta.id_cierre = id_cierre or uuid.uuid4()
    abierta.save(update_fields=['estado', 'cerrada_en', 'cerrada_por', 'cerrada_por_rol', 'id_cierre'])
    EventoRonda.objects.create(ronda=abierta, tipo=TipoEventoRonda.CIERRE, actor=usuario, actor_rol=rol_de(usuario),
                               datos={'completitud': resultado, 'via': 'cierre_validado_40B2',
                                      'id_cierre_del_cliente': id_cierre is not None,
                                      # Fase 40D-G: «trabaja» vive en la ficha única y se sobrescribe;
                                      # se guarda su valor al cerrar para no usar un dato actual como
                                      # dato de esta ronda (no es una respuesta de salud).
                                      'contexto': {'trabaja_actualmente': ficha.trabaja_actualmente}})
    # La siguiente ronda se abre ANTES de avanzar ronda_actual: la señal post_save ve «sin_cambio».
    _abrir(ficha, numero + 1, ahora, actor=usuario, actor_rol=rol_de(usuario))
    ficha.ronda_actual = numero + 1
    ficha.ultima_finalizacion_en = ahora
    ficha.save(update_fields=['ronda_actual', 'ultima_finalizacion_en'])
    return {'estado': 'cerrada', 'ronda': numero, 'id_cierre': str(abierta.id_cierre)}


def puntaje_mrs_definitivo(mrs):
    """
    Puntaje MRS que puede presentarse como definitivo: los 11 ítems respondidos,
    la ronda cerrada y (Fase 40B-3) ningún cero anterior a la 40B-2 sin confirmar.
    En cualquier otro caso devuelve None. La regla está en resultado_mrs.py.
    """
    from .resultado_mrs import resultado_mrs
    return resultado_mrs(mrs).puntaje


def ronda_es_historica_no_verificable(mrs):
    """True si el MRS es anterior a la 40B-2 y conserva ceros que nadie confirmó."""
    from .models import MRSAnterior40B2
    marca = MRSAnterior40B2.objects.filter(mrs=mrs).first() if mrs is not None else None
    return bool(marca and marca.ceros_por_confirmar(mrs))

