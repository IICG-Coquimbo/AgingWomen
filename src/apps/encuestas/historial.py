"""
Construye el historial de rondas de una participante: qué secciones tiene
guardadas en cada ronda, con qué fecha, y su registro (para que la plantilla
saque de ahí resúmenes). Lo usan tanto el tablero de la usuaria (Fase 15)
como la ficha del profesional (Fase 16).

Fase 40B-3: el resultado MRS de cada ronda se calcula aquí, una sola vez, con
la regla única de apps.rondas.resultado_mrs; las plantillas solo muestran su
texto (encuestas/_resultado_mrs.html) y no leen `puntaje_total`.

Fase 40C: cada ronda lleva además su estado para el historial (en curso /
finalizada y verificable / histórica no verificable), derivado SOLO de ese
resultado, y su fecha de cierre únicamente cuando es verificable (cierre normal
registrado desde la 40B-2). Nunca se usa la fecha de creación de una fila como
fecha de la ronda, ni datos actuales de la participante como datos de la ronda.
"""
from django.utils import timezone

from apps.rondas.models import EstadoRonda, RolCierre, RondaEvaluacion
from apps.rondas.resultado_mrs import resultado_mrs

# Estados de una ronda en el historial (Fase 40C).
EN_CURSO = 'en_curso'
FINALIZADA_VERIFICABLE = 'finalizada_verificable'
HISTORICA_NO_VERIFICABLE = 'historica_no_verificable'
TEXTO_ESTADO = {
    EN_CURSO: 'En curso',
    FINALIZADA_VERIFICABLE: 'Finalizada y verificable',
    HISTORICA_NO_VERIFICABLE: 'Histórica no verificable',
}
TEXTO_SIN_FECHA = 'Fecha no registrada'

from .esquema import ORDEN_SECCIONES
from .models import MRS
from .sync import SECCIONES


def fecha_cierre_verificable(registro):
    """
    Fecha local del cierre solo si lo hizo el cierre validado de la 40B-2 (CERRADA, con
    cerrada_en, id_cierre y el rol de quien cerró). Solo ese cierre asigna id_cierre.
    Lo que cuenta es cómo se CERRÓ la ronda, no cómo se creó su registro: una ronda que
    la retrocarga 40B-1 registró abierta y que después se cerró con el cierre validado
    tiene una fecha real. Las retrocargadas ya cerradas no tienen fecha, y el cierre por
    la señal antigua copia `ultima_finalizacion_en` (puede ser de otra ronda) sin
    id_cierre: tampoco se muestra. En esos casos, None.
    """
    if (registro is None or registro.estado != EstadoRonda.CERRADA or registro.cerrada_en is None
            or registro.id_cierre is None
            or registro.cerrada_por_rol in (RolCierre.NO_REGISTRADO, RolCierre.DESCONOCIDO, '')):
        return None
    return timezone.localdate(registro.cerrada_en)


def estado_de_ronda(numero, ronda_actual, resultado):
    """En curso si es la ronda actual; si está cerrada, verificable solo con resultado MRS definitivo."""
    if numero >= ronda_actual:
        return EN_CURSO
    if resultado is not None and resultado.es_definitivo:
        return FINALIZADA_VERIFICABLE
    # Cerrada sin un resultado definitivo (ceros antiguos sin confirmar, registro que no
    # dice CERRADA, MRS incompleto o ausente): solo pudo cerrarse por la vía anterior.
    return HISTORICA_NO_VERIFICABLE


def construir_historial(paciente):
    rondas = []
    registros = {r.numero: r for r in RondaEvaluacion.objects.filter(participante=paciente)}
    estados = {n: r.estado for n, r in registros.items()}
    for numero in range(1, paciente.ronda_actual + 1):
        secciones = []
        resultado_ronda = None
        for tipo, titulo, _form_cls, _parte in ORDEN_SECCIONES:
            if tipo not in SECCIONES:
                continue  # 'identificacion' y 'mrs_complementario' no son secciones propias
            modelo, _form = SECCIONES[tipo]
            registro = modelo.objects.filter(participante=paciente, ronda=numero).first()
            fecha = None
            if registro is not None:
                fecha = getattr(registro, 'fecha_evaluacion', None) or getattr(registro, 'fecha_registro', None)
            resultado = (resultado_mrs(registro, ronda_actual=paciente.ronda_actual, estados=estados)
                         if modelo is MRS else None)
            if resultado is not None:
                resultado_ronda = resultado
            secciones.append({'titulo': titulo, 'registro': registro, 'fecha': fecha,
                              'resultado_mrs': resultado})
        estado = estado_de_ronda(numero, paciente.ronda_actual, resultado_ronda)
        rondas.append({
            'numero': numero,
            'secciones': secciones,
            'es_actual': numero == paciente.ronda_actual,
            'resultado_mrs': resultado_ronda,
            'estado': estado,
            'estado_texto': TEXTO_ESTADO[estado],
            'fecha_cierre': (fecha_cierre_verificable(registros.get(numero))
                             if estado != EN_CURSO else None),
        })
    rondas.reverse()  # ronda más reciente primero
    return rondas
