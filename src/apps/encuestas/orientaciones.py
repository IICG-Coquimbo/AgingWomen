"""
Fase 40D: orientaciones educativas personalizadas por las respuestas MRS.

Contenido: orientaciones_catalogo.json, generado desde el borrador 40D-1
(analisis/fase40/40D_orientaciones/generar_catalogo_json.py). Mientras el
catálogo no esté aprobado clínicamente NO se muestra a nadie, salvo que el
entorno lo permita expresamente para pruebas (ORIENTACIONES_PERMITIR_BORRADOR).

Reglas (40D-1_reglas_personalizacion.md, R-1 a R-7), sin consultas propias:
reutiliza la salida de construir_historial y la regla única de resultado_mrs.
- R-1: ronda de referencia = la última ronda cerrada; solo si su MRS es
  DEFINITIVO. Si no, no hay selección personalizada (no se usa una anterior).
- R-2: se destaca O-i si la respuesta a pregunta_i es >= UMBRAL_DESTACAR.
- R-3: orden por respuesta (desc.) y número de pregunta; máximo MAXIMO_PRINCIPALES.
- R-4: mensaje de apoyo primero si pregunta_5 >= UMBRAL_APOYO.
- R-7: cada orientación dice por qué aparece, con la intensidad «X de 4».
No usa el puntaje total, las dimensiones, la severidad, la comparación entre
rondas ni grupos de caracterización (criterios C-3 y C-5).

Fase 40D-G (contexto_participante.py): el grupo B1 de la ronda de referencia se
calcula como contexto exploratorio (`contexto_exploratorio`, no se muestra dentro
de las orientaciones ni cambia la selección; el tablero lo presenta aparte, Fase 40D-H). La única adaptación del contenido es por una característica
individual con respaldo: si en esa ronda respondió 0 días de ejercicio, se destaca
la medida de actividad física ya presente (y con fuente) en ciertas tarjetas.
"""
import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from .contexto_participante import contexto_de_ronda, nota_actividad, ronda_de_referencia

CATALOGO = Path(__file__).with_name('orientaciones_catalogo.json')
ESTADO_APROBADO = 'aprobado'

# Valores propuestos en la 40D-1 (pendientes de aprobación: R-2 y R-4).
UMBRAL_DESTACAR = 2
UMBRAL_APOYO = 3
MAXIMO_PRINCIPALES = 3
PREGUNTA_APOYO = 'pregunta_5'


@lru_cache(maxsize=1)
def catalogo():
    datos = json.loads(CATALOGO.read_text(encoding='utf-8'))
    datos['por_pregunta'] = {o['pregunta']: o for o in datos['orientaciones']}
    for o in datos['orientaciones']:
        # Fuentes de la tarjeta (C-6): todas las citadas en sus secciones, en orden y sin repetir.
        ids = []
        for seccion in (o['que_es'], o['relacion'], o['autocuidado'],
                        o['cuando_consultar']['items'], o['senales_alerta']['items']):
            for it in seccion:
                ids += [f for f in it['fuentes'] if f not in ids]
        o['fuentes_usadas'] = [dict(datos['fuentes'][f], id=f) for f in sorted(ids)]
    return datos


def habilitadas():
    """
    Solo se muestran si están activadas y el catálogo está aprobado, o si el entorno
    permite el borrador. El borrador exige además DEBUG=True: en producción
    (DEBUG=False) nunca se muestra, aunque las variables queden activadas por error.
    """
    if not getattr(settings, 'ORIENTACIONES_HABILITADAS', False):
        return False
    if catalogo()['estado'] == ESTADO_APROBADO:
        return True
    return bool(getattr(settings, 'ORIENTACIONES_PERMITIR_BORRADOR', False) and settings.DEBUG)


def _tarjeta(orientacion, motivo, contexto, intensidad=None):
    destacar, nota = nota_actividad(orientacion, contexto)
    return {'orientacion': orientacion, 'intensidad': intensidad, 'motivo': motivo,
            'destacar': destacar, 'nota_contexto': nota}


def seleccionar(rondas):
    """Contexto de encuestas/_orientaciones.html, o None si las orientaciones no están habilitadas."""
    if not habilitadas():
        return None
    cat = catalogo()
    base = {'version': cat['version'], 'borrador': cat['estado'] != ESTADO_APROBADO,
            'aviso': cat['aviso'], 'biblioteca': cat['orientaciones'], 'fuentes': cat['fuentes'],
            'personalizada': False, 'apoyo': None, 'principales': [], 'otras': [], 'ronda': None,
            'contexto_exploratorio': None}
    ronda, mrs = ronda_de_referencia(rondas)
    if mrs is None:
        base['motivo'] = 'sin_rondas' if ronda is None else 'sin_ronda_verificable'
        return base
    numero = ronda['numero']
    contexto = contexto_de_ronda(ronda)
    # Solo para uso interno/profesional futuro (40E); la plantilla de la participante no lo usa.
    base['contexto_exploratorio'] = {'grupo_b1': contexto['grupo_b1'], 'faltantes': contexto['faltantes'],
                                     'ronda': numero}

    destacadas = []
    for pregunta, orientacion in cat['por_pregunta'].items():
        valor = getattr(mrs, pregunta)
        if valor is not None and valor >= UMBRAL_DESTACAR:
            destacadas.append((valor, int(pregunta.split('_')[1]), orientacion))
    destacadas.sort(key=lambda t: (-t[0], t[1]))
    apoyo_valor = getattr(mrs, PREGUNTA_APOYO)
    if apoyo_valor is not None and apoyo_valor >= UMBRAL_APOYO:
        # R-4: la orientación de ánimo va primero, fuera del máximo, y no se repite abajo.
        base['apoyo'] = _tarjeta(cat['por_pregunta'][PREGUNTA_APOYO],
                                 f'Aparece primero porque en tu ronda {numero} marcaste el ánimo decaído '
                                 f'con intensidad {apoyo_valor} de 4.', contexto, apoyo_valor)
        destacadas = [d for d in destacadas if d[2]['pregunta'] != PREGUNTA_APOYO]
    tarjetas = [_tarjeta(o, f'Aparece porque en tu ronda {numero} marcaste esta molestia con intensidad {v} de 4.',
                         contexto, v)
                for v, _n, o in destacadas]

    base.update(personalizada=True, ronda=numero, principales=tarjetas[:MAXIMO_PRINCIPALES],
                otras=tarjetas[MAXIMO_PRINCIPALES:], motivo='personalizada' if (tarjetas or base['apoyo']) else 'sin_destacadas')
    return base
