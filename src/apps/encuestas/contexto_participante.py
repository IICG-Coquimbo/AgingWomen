"""
Fase 40D-G: contexto de la participante para las orientaciones de la Fase 40D.

Dos cosas separadas, ambas sobre la MISMA ronda de referencia de las orientaciones
(la última ronda cerrada con MRS definitivo, R-1):

1. Grupo B1 (contexto exploratorio). La participante lo ve en su tablero, por separado y
   con advertencia (Fase 40D-H, decisión vigente para la revisión de la profesora guía).
   Regla de 4 pasos de la Fase 37C (complemento de tres preguntas), tal cual quedó
   en analisis/fase37/37C_complemento_tres_preguntas/definiciones/definicion_B1_B2.json:
   3 o más días de ejercicio -> S1; si no, sin pareja -> S0; si no, no trabaja -> S2;
   si no -> S3. No se recalcula nada: solo se aplica el mapa de 20 celdas.
   Las Fases 37D-39 no encontraron diferencias del MRS útiles entre grupos (ε² del
   total 0,027; ninguna regla condicionada supera la nula), así que el grupo NO
   selecciona, ordena ni modifica orientaciones (C-5). Si falta una variable o no
   es verificable para esa ronda, no se asigna grupo.

2. Adaptación por una característica individual con respaldo sanitario: la actividad
   física. Si en esa ronda respondió «0 días» de ejercicio en una semana habitual, en
   las tarjetas cuyo autocuidado ya recomienda actividad física regular (con su fuente
   del catálogo) se destaca esa medida y se explica por qué. No se agrega consejo nuevo.
   No se aplica a bochornos (O-01): la fuente F17 indica que el ejercicio no ha
   demostrado reducirlos por sí mismo.
   Trabajo y pareja no adaptan contenido: las asociaciones con el MRS no se
   demostraron (Fases 38-39) y el catálogo no tiene fuentes que lo justifiquen.
"""
from apps.rondas.models import EventoRonda, TipoEventoRonda

from .historial import FINALIZADA_VERIFICABLE
from .models import MRS, ActividadFisica, RespuestaSiNo

# Mapa B1: índice de celda = 10·trabaja + 5·pareja + nivel de días (0..4) -> segmento.
MAPA_B1 = (0, 0, 1, 1, 1, 2, 2, 1, 1, 1,
           0, 0, 1, 1, 1, 3, 3, 1, 1, 1)
GRUPOS_B1 = ('S0', 'S1', 'S2', 'S3')
DIAS_A_NIVEL = {c.value: i for i, c in enumerate(ActividadFisica.DiasEjercicioSemana)}  # 1..5 -> 0..4

# Tarjetas con una medida de actividad física regular en el autocuidado: id -> índice del ítem.
# (Comprobado contra el catálogo en las pruebas.) O-01 se excluye a propósito (F17).
ACTIVIDAD_FISICA_EN_TARJETA = {'O-03': 2, 'O-05': 1, 'O-06': 1, 'O-07': 1, 'O-08': 2}
SIN_EJERCICIO = ActividadFisica.DiasEjercicioSemana.CERO


# Fase 40D-H: nombres y descripciones para la participante. Los códigos S0-S3 y el mapa
# no cambian; la descripción repite en palabras la misma regla de 4 pasos.
GRUPOS_VISIBLES = {
    'S0': ('Grupo 1', 'Bienestar a tu ritmo',
           'Reúne respuestas de mujeres que hacen ejercicio menos de 3 días en una semana habitual '
           'y que actualmente no tienen pareja.'),
    'S1': ('Grupo 2', 'Vida en movimiento',
           'Reúne respuestas de mujeres que hacen ejercicio 3 días o más en una semana habitual, '
           'tengan o no pareja y trabajen o no.'),
    'S2': ('Grupo 3', 'Equilibrio personal',
           'Reúne respuestas de mujeres que hacen ejercicio menos de 3 días en una semana habitual, '
           'tienen pareja y actualmente no trabajan.'),
    'S3': ('Grupo 4', 'Entre múltiples actividades',
           'Reúne respuestas de mujeres que hacen ejercicio menos de 3 días en una semana habitual, '
           'tienen pareja y actualmente trabajan.'),
}


def ronda_de_referencia(rondas):
    """(ronda, registro MRS) de la última ronda cerrada si es verificable; si no, (ronda o None, None)."""
    cerradas = [r for r in rondas if not r['es_actual']]
    if not cerradas:
        return None, None
    ultima = max(cerradas, key=lambda r: r['numero'])
    if ultima['estado'] != FINALIZADA_VERIFICABLE:
        return ultima, None
    for s in ultima['secciones']:
        res = s.get('resultado_mrs')
        if res is not None and res.es_definitivo:
            return ultima, s['registro']
    return ultima, None


DATOS_DEL_GRUPO = {'trabaja_actualmente': 'si trabajas actualmente', 'tiene_pareja': 'si tienes pareja',
                   'dias_ejercicio_semana': 'cuántos días haces ejercicio en una semana habitual'}


def _sin_grupo(motivo, ronda, datos_faltantes=()):
    """Explica por qué no hay grupo. Solo informa: no interviene en la regla ni en las orientaciones."""
    return {'grupo': None, 'ronda': None, 'resultado_mrs': None, 'motivo': motivo,
            'numero_ronda': ronda['numero'] if ronda else None, 'datos_faltantes': list(datos_faltantes)}


def grupo_para_tablero(rondas):
    """
    Sección «Mi grupo de caracterización» del tablero de la participante (Fase 40D-H).
    Usa la misma ronda de referencia y la misma regla que las orientaciones. Si no hay
    asignación verificable, `grupo` es None («Grupo aún no disponible»); nunca usa datos actuales.
    El resultado MRS es el de esa misma ronda y se muestra aparte.
    """
    ronda, mrs = ronda_de_referencia(rondas)
    if mrs is None:
        return _sin_grupo('no_verificable' if ronda else 'sin_ronda', ronda)
    contexto = contexto_de_ronda(ronda)
    codigo = contexto['grupo_b1']
    if codigo is None:
        faltan = list(contexto['faltantes'])
        if 'tiene_pareja' not in faltan and mrs.tiene_pareja not in (RespuestaSiNo.SI, RespuestaSiNo.NO):
            faltan.append('tiene_pareja')   # respondió «no sabe»: tampoco permite asignar grupo
        return _sin_grupo('faltan_datos', ronda, [DATOS_DEL_GRUPO[f] for f in faltan])
    numero, nombre, descripcion = GRUPOS_VISIBLES[codigo]
    return {'grupo': {'codigo': codigo, 'numero': numero, 'nombre': nombre, 'descripcion': descripcion},
            'ronda': ronda['numero'], 'resultado_mrs': ronda['resultado_mrs']}


def _registro(ronda, modelo):
    for s in ronda['secciones']:
        if isinstance(s['registro'], modelo):
            return s['registro']
    return None


def trabaja_al_cerrar(participante_id, numero):
    """Valor de «trabaja» guardado en el cierre validado de esa ronda; None si no hay registro."""
    evento = (EventoRonda.objects
              .filter(ronda__participante_id=participante_id, ronda__numero=numero, tipo=TipoEventoRonda.CIERRE)
              .order_by('-momento', '-id').values_list('datos', flat=True).first())
    if not evento or 'contexto' not in evento:
        return None
    return evento['contexto'].get('trabaja_actualmente')


def grupo_b1(trabaja, tiene_pareja, dias_ejercicio):
    """Segmento B1 o None si falta cualquiera de las tres variables (no se imputa)."""
    if trabaja is None or tiene_pareja not in (RespuestaSiNo.SI, RespuestaSiNo.NO) \
            or dias_ejercicio not in DIAS_A_NIVEL:
        return None
    celda = 10 * int(bool(trabaja)) + 5 * int(tiene_pareja == RespuestaSiNo.SI) + DIAS_A_NIVEL[dias_ejercicio]
    return GRUPOS_B1[MAPA_B1[celda]]


def contexto_de_ronda(ronda):
    """
    Contexto de la ronda de referencia (ya verificada por quien llama).
    {'grupo_b1': 'S0'..'S3' | None, 'faltantes': [...], 'sin_ejercicio': bool, 'ronda': n}
    """
    mrs = _registro(ronda, MRS)
    actividad = _registro(ronda, ActividadFisica)
    pareja = mrs.tiene_pareja if mrs is not None else None
    dias = actividad.dias_ejercicio_semana if actividad is not None else None
    trabaja = trabaja_al_cerrar(mrs.participante_id, ronda['numero']) if mrs is not None else None
    faltantes = [nombre for nombre, valor in (('trabaja_actualmente', trabaja), ('tiene_pareja', pareja),
                                              ('dias_ejercicio_semana', dias)) if valor is None]
    return {'ronda': ronda['numero'], 'grupo_b1': grupo_b1(trabaja, pareja, dias), 'faltantes': faltantes,
            'sin_ejercicio': dias == SIN_EJERCICIO}


def nota_actividad(orientacion, contexto):
    """(índice del ítem a destacar, texto) si corresponde adaptar la tarjeta; si no, (None, '')."""
    indice = ACTIVIDAD_FISICA_EN_TARJETA.get(orientacion['id'])
    if indice is None or not contexto or not contexto['sin_ejercicio']:
        return None, ''
    return indice, (f'En tu ronda {contexto["ronda"]} indicaste que en una semana habitual no haces ejercicio. '
                    'Por eso te destacamos la actividad física regular, una de las medidas que recomiendan '
                    'las fuentes de salud para este tema.')
