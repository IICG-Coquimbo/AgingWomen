"""
Construye el historial de rondas de una participante: qué secciones tiene
guardadas en cada ronda, con qué fecha, y su registro (para que la plantilla
saque de ahí resúmenes como el puntaje MRS). Lo usan tanto el tablero de la
usuaria (Fase 15) como la ficha del profesional (Fase 16).
"""
from .esquema import ORDEN_SECCIONES
from .sync import SECCIONES


def construir_historial(paciente):
    rondas = []
    for numero in range(1, paciente.ronda_actual + 1):
        secciones = []
        for tipo, titulo, _form_cls, _parte in ORDEN_SECCIONES:
            if tipo not in SECCIONES:
                continue  # 'identificacion' y 'mrs_complementario' no son secciones propias
            modelo, _form = SECCIONES[tipo]
            registro = modelo.objects.filter(participante=paciente, ronda=numero).first()
            fecha = None
            if registro is not None:
                fecha = getattr(registro, 'fecha_evaluacion', None) or getattr(registro, 'fecha_registro', None)
            secciones.append({'titulo': titulo, 'registro': registro, 'fecha': fecha})
        rondas.append({
            'numero': numero,
            'secciones': secciones,
            'es_actual': numero == paciente.ronda_actual,
        })
    rondas.reverse()  # ronda más reciente primero
    return rondas
