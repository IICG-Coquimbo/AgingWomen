"""
Fase 40C: evolución del resultado MRS entre rondas (tablero de la usuaria y
ficha profesional, con el mismo componente).

Solo reordena lo que ya calculó `construir_historial` con la regla única de
apps.rondas.resultado_mrs; no lee respuestas por su cuenta. Reglas:

- Solo aportan puntos las rondas CERRADAS con resultado DEFINITIVO.
- La ronda en curso nunca entra en el gráfico (su suma es provisional).
- Una ronda cerrada sin resultado definitivo (histórica no verificable) queda
  en el eje como hueco: no se le asigna valor (ni cero) y las líneas no la
  cruzan; los tramos se cortan allí.
- El eje horizontal es el NÚMERO de ronda. La fecha solo se muestra como
  etiqueta cuando el cierre quedó registrado al ocurrir (ver historial.py).
- Con menos de dos rondas verificables seguidas no hay línea de evolución.
- Nada aquí interpreta los valores: no hay severidad, mejoría ni empeoramiento.

La geometría del SVG se calcula aquí para que la plantilla no haga cuentas.
"""
from apps.rondas.resultado_mrs import DIMENSIONES, MAXIMO

from .historial import FINALIZADA_VERIFICABLE

ANCHO, ALTO = 320, 170
IZQ, DER, ARR, ABA = 34, 14, 12, 30

EXPLICACION_TOTAL = (
    'Suma de las 11 preguntas de la escala MRS, de 0 a 44. Un número más alto significa '
    'que en esa ronda se informaron molestias más intensas en conjunto.'
)
EXPLICACIONES = {
    'somatica': 'Bochornos, molestias al corazón, molestias musculares y articulares, y '
                'dificultades del sueño (preguntas 1 a 4; de 0 a 16).',
    'psicologica': 'Ánimo depresivo, irritabilidad, ansiedad y cansancio físico y mental '
                   '(preguntas 5 a 8; de 0 a 16).',
    'urogenital': 'Problemas sexuales, problemas con la orina y sequedad vaginal '
                  '(preguntas 9 a 11; de 0 a 12).',
}
NOTA_GENERAL = (
    'Solo se grafican rondas finalizadas con resultado verificable. Los gráficos describen '
    'lo informado en cada ronda: no son un diagnóstico ni indican mejoría o empeoramiento.'
)


def _num(v):
    """Coordenada con un decimal (texto estable para el SVG y las pruebas)."""
    return f'{v:.1f}'


def _grafico(clave, titulo, explicacion, maximo, filas):
    """filas: [(numero, valor | None)] de las rondas cerradas, en orden ascendente."""
    n = len(filas)
    ancho_util, alto_util = ANCHO - IZQ - DER, ALTO - ARR - ABA

    def x(i):
        return IZQ + (ancho_util / 2 if n == 1 else i * ancho_util / (n - 1))

    def y(v):
        return ARR + alto_util * (1 - v / maximo)

    paso = 1 if n <= 12 else -(-n // 12)        # con muchas rondas se rotula una de cada `paso`
    puntos, excluidas, etiquetas, tramos, tramo = [], [], [], [], []
    for i, (numero, valor) in enumerate(filas):
        if i % paso == 0 or i == n - 1:
            etiquetas.append({'x': _num(x(i)), 'numero': numero})
        if valor is None:
            excluidas.append({'x': _num(x(i)), 'numero': numero})
            if tramo:
                tramos.append(tramo)
            tramo = []
            continue
        punto = {'x': _num(x(i)), 'y': _num(y(valor)), 'valor': valor, 'numero': numero}
        puntos.append(punto)
        tramo.append(punto)
    if tramo:
        tramos.append(tramo)

    lineas_y = [{'y': _num(y(v)), 'valor': v} for v in sorted({0, maximo // 2, maximo})]
    descripcion = '; '.join(
        f'ronda {numero}: {valor} de {maximo}' if valor is not None
        else f'ronda {numero}: sin resultado verificable'
        for numero, valor in filas)
    return {
        'clave': clave, 'titulo': titulo, 'explicacion': explicacion, 'maximo': maximo,
        'ancho': ANCHO, 'alto': ALTO, 'x_inicio': IZQ, 'x_fin': ANCHO - DER,
        'y_base': _num(ALTO - ABA), 'y_etiqueta': _num(ALTO - ABA + 16),
        'y_arriba': ARR,
        'lineas_y': lineas_y, 'etiquetas_x': etiquetas, 'excluidas': excluidas, 'puntos': puntos,
        # Solo los tramos de 2 o más puntos se dibujan como línea.
        'tramos': [' '.join(f"{p['x']},{p['y']}" for p in t) for t in tramos if len(t) > 1],
        'descripcion': f'{titulo} por ronda: {descripcion}.',
    }


def construir_evolucion(rondas):
    """
    `rondas` es la salida de construir_historial (más reciente primero).
    Devuelve el contexto del componente encuestas/_evolucion_mrs.html.
    """
    ordenadas = sorted(rondas, key=lambda r: r['numero'])
    cerradas = [r for r in ordenadas if not r['es_actual']]
    en_curso = next((r['numero'] for r in ordenadas if r['es_actual']), None)

    filas = []
    for r in cerradas:
        res = r['resultado_mrs']
        definitivo = r['estado'] == FINALIZADA_VERIFICABLE and res is not None and res.es_definitivo
        filas.append({
            'numero': r['numero'], 'estado': r['estado'], 'estado_texto': r['estado_texto'],
            'fecha_cierre': r['fecha_cierre'],
            'total': res.puntaje if definitivo else None,
            'dimensiones': ({d.clave: d.puntaje for d in res.dimensiones} if definitivo else None),
            # Mismo orden que DIMENSIONES, para la tabla de la plantilla.
            'valores_dimensiones': [d.puntaje for d in res.dimensiones] if definitivo else [],
        })

    verificables = [f for f in filas if f['total'] is not None]
    total = _grafico('total', 'Puntaje MRS total', EXPLICACION_TOTAL, MAXIMO,
                     [(f['numero'], f['total']) for f in filas])
    dimensiones = [
        _grafico(clave, nombre, EXPLICACIONES[clave], 4 * len(campos),
                 [(f['numero'], f['dimensiones'][clave] if f['dimensiones'] else None) for f in filas])
        for clave, nombre, campos in DIMENSIONES
    ]
    hay_tendencia = bool(total['tramos'])
    hay_huecos = len(verificables) < len(filas)

    if not filas:
        aviso = ('Todavía no hay rondas finalizadas. Los resultados aparecerán aquí cuando '
                 'se finalice la primera ronda.')
    elif not verificables:
        aviso = ('Ninguna ronda finalizada tiene un resultado verificable, por eso no se '
                 'muestra ningún gráfico.')
    elif len(verificables) == 1:
        aviso = 'Hay una sola ronda con resultado verificable: todavía no se puede mostrar una evolución.'
    elif not hay_tendencia:
        aviso = ('Las rondas con resultado verificable no son seguidas: los puntos se muestran '
                 'sin unir porque entre ellas hay rondas sin resultado verificable.')
    elif hay_huecos:
        aviso = ('La línea no cruza las rondas sin resultado verificable (marcadas con una línea '
                 'punteada): se interrumpe en ellas.')
    else:
        aviso = ''

    return {
        'filas': filas,   # ascendente: se lee de la primera a la última
        'n_cerradas': len(filas),
        'n_verificables': len(verificables),
        'hay_grafico': bool(verificables),
        'hay_tendencia': hay_tendencia,
        'en_curso': en_curso,
        'aviso': aviso,
        'nota': NOTA_GENERAL,
        'total': total,
        'dimensiones': dimensiones,
        'nombres_dimensiones': [(clave, nombre, 4 * len(campos)) for clave, nombre, campos in DIMENSIONES],
    }
