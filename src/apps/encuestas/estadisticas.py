"""
Fase 40C-P: tablero estadístico global para profesionales («Estadísticas generales»).

Solo agrega lo que ya calculan las reglas existentes; no lee respuestas por su cuenta:
- el historial y el resultado MRS de cada ronda salen de `construir_historial`
  (regla única de apps.rondas.resultado_mrs);
- el grupo B1 sale de `contexto_participante.contexto_de_ronda` (regla de la 37C, sin cambios).

Población:
- Se incluye una ficha solo si tiene consentimiento vigente: la de una CUENTA de usuaria
  con `consentimiento_aceptado_en`, o (Etapa 2) un registro presencial sin cuenta con su
  consentimiento presencial registrado. Las retiradas no aparecen: el retiro borra la ficha.
- Cada mujer aporta UNA ronda: la última cerrada y verificable (estado
  FINALIZADA_VERIFICABLE, es decir, con resultado MRS definitivo). Sin ninguna, queda fuera.
- La edad es la edad al cierre de esa ronda y solo se calcula si el cierre tiene fecha
  verificable (historial.fecha_cierre_verificable); nunca la edad de hoy.
- La etapa menopáusica no existe en la plataforma (se calcula solo en los análisis, como
  variable descriptiva; decisión del 2026-11-01), así que se informa como no disponible.

Protección de celdas pequeñas (UMBRAL = 5):
- Con menos de UMBRAL participantes incluidas no se publica ninguna cifra.
- En cada distribución se ocultan las celdas de 1 a UMBRAL-1. Si con eso una celda
  oculta se pudiera deducir restando del total, se ocultan además las celdas más pequeñas
  que se ven, hasta que las ocultas sean al menos dos y sumen UMBRAL o más (y no puedan
  ser todas de 1). Los ceros se muestran. Si no se puede cumplir, se oculta la distribución.
- Una estadística (promedio) de un grupo solo se publica si la celda del grupo se publica.
"""
from datetime import date
from statistics import mean, median

from apps.rondas.resultado_mrs import DIMENSIONES, MAXIMO

from apps.usuarios.privacidad import sin_consentimiento_vigente

from .contexto_participante import GRUPOS_B1, GRUPOS_VISIBLES, contexto_de_ronda
from .historial import FINALIZADA_VERIFICABLE, construir_historial
from .models import Identificacion

UMBRAL = 5

TRAMOS_EDAD = (('<40', 'Menos de 40', None, 39), ('40-44', '40 a 44', 40, 44), ('45-49', '45 a 49', 45, 49),
               ('50-54', '50 a 54', 50, 54), ('55-59', '55 a 59', 55, 59), ('60-65', '60 a 65', 60, 65),
               ('>65', 'Más de 65', 66, None))
SIN_EDAD = ('sin_edad', 'Sin edad verificable (ronda sin fecha de cierre registrada)')
SIN_GRUPO = ('sin_grupo', 'Sin grupo verificable')
TRAMOS_MRS = tuple((f'{a}-{a + 4}', f'{a} a {a + 4}', a, a + 4) for a in range(0, MAXIMO - 4 + 1, 5))
# 0-4, 5-9, ..., 40-44 (9 tramos que cubren 0..44)
assert TRAMOS_MRS[-1][3] == MAXIMO


def _edad(nacimiento, dia):
    return dia.year - nacimiento.year - ((dia.month, dia.day) < (nacimiento.month, nacimiento.day))


def _tramo(valor, tramos):
    for clave, _etiqueta, desde, hasta in tramos:
        if (desde is None or valor >= desde) and (hasta is None or valor <= hasta):
            return clave
    raise ValueError(valor)


def _decimal(v, d=1):
    return f'{v:.{d}f}'.replace('.', ',')


def motivo_exclusion(ficha):
    """None si la ficha tiene base de consentimiento verificable; si no, la clave del motivo."""
    cuenta = ficha.usuario
    if cuenta is None:
        # Etapa 2: un registro presencial entra solo con su consentimiento presencial registrado.
        return 'presencial' if sin_consentimiento_vigente(ficha.rut_hash) else None
    if cuenta.es_profesional or not cuenta.consentimiento_aceptado_en:
        return 'sin_consentimiento'
    return None


def participante_incluida(ficha):
    """Datos agregables de una ficha o (None, motivo). Nunca incluye identificadores."""
    motivo = motivo_exclusion(ficha)
    if motivo:
        return None, motivo
    rondas = construir_historial(ficha)
    verificables = [r for r in rondas if r['estado'] == FINALIZADA_VERIFICABLE
                    and r['resultado_mrs'] is not None and r['resultado_mrs'].es_definitivo]
    if not verificables:
        return None, 'sin_ronda_verificable'
    ref = max(verificables, key=lambda r: r['numero'])
    res = ref['resultado_mrs']
    edad = _edad(ficha.fecha_nacimiento, ref['fecha_cierre']) if ref['fecha_cierre'] else None
    return {
        'total': res.puntaje,
        'dimensiones': {d.clave: d.puntaje for d in res.dimensiones},
        'rondas_verificables': len(verificables),
        'tramo_edad': _tramo(edad, TRAMOS_EDAD) if edad is not None else SIN_EDAD[0],
        'grupo': contexto_de_ronda(ref)['grupo_b1'] or SIN_GRUPO[0],
    }, None


def proteger(conteos, umbral=UMBRAL):
    """
    conteos: {clave: n}. Devuelve el conjunto de claves a ocultar, o None si hay que
    ocultar la distribución completa (ver docstring del módulo).
    """
    ocultas = {k for k, n in conteos.items() if 0 < n < umbral}
    if not ocultas:
        return set()

    def segura():
        suma = sum(conteos[k] for k in ocultas)
        return len(ocultas) >= 2 and suma >= umbral and suma > len(ocultas)

    candidatas = sorted((n, k) for k, n in conteos.items() if n > 0 and k not in ocultas)
    while not segura():
        if not candidatas:
            return None
        ocultas.add(candidatas.pop(0)[1])
    return ocultas


def distribucion(clave, titulo, unidad, explicacion, categorias, valores):
    """categorias: [(clave, etiqueta)]; valores: lista de claves (una por participante)."""
    n = len(valores)
    conteos = {c: valores.count(c) for c, _ in categorias}
    ocultas = proteger(conteos)
    filas = []
    for c, etiqueta in categorias:
        visible = ocultas is not None and c not in ocultas
        cuenta = conteos[c] if visible else None
        filas.append({'clave': c, 'etiqueta': etiqueta, 'n': cuenta, 'oculta': not visible,
                      'porcentaje': _decimal(100 * cuenta / n) if visible and n else None,
                      'ancho': f'{100 * cuenta / n:.1f}' if visible and n else '0'})
    return {'clave': clave, 'titulo': titulo, 'unidad': unidad, 'explicacion': explicacion,
            'denominador': n, 'filas': filas, 'oculta': ocultas is None,
            'hay_ocultas': bool(ocultas) or ocultas is None, 'ocultas': ocultas or set()}


def construir_estadisticas(fichas=None):
    fichas = Identificacion.objects.select_related('usuario') if fichas is None else fichas
    incluidas, excluidas = [], {'presencial': 0, 'sin_consentimiento': 0, 'sin_ronda_verificable': 0}
    for ficha in fichas:
        datos, motivo = participante_incluida(ficha)
        if datos is None:
            excluidas[motivo] += 1
        else:
            incluidas.append(datos)

    n = len(incluidas)
    exclusiones = [{'clave': k, 'etiqueta': ETIQUETAS_EXCLUSION[k],
                    'n': v if v == 0 or v >= UMBRAL else None} for k, v in excluidas.items()]
    base = {'umbral': UMBRAL, 'exclusiones': exclusiones, 'suficiente': n >= UMBRAL,
            'nota_descriptiva': NOTA_DESCRIPTIVA, 'fecha': date.today()}
    if n < UMBRAL:
        return dict(base, n=None)

    totales = [p['total'] for p in incluidas]
    dims = [{'clave': clave, 'nombre': nombre, 'maximo': 4 * len(campos),
             'promedio': _decimal(mean(p['dimensiones'][clave] for p in incluidas)),
             'ancho': f'{100 * mean(p["dimensiones"][clave] for p in incluidas) / (4 * len(campos)):.1f}'}
            for clave, nombre, campos in DIMENSIONES]

    grupos_cat = [(g, f'{GRUPOS_VISIBLES[g][0]} — {GRUPOS_VISIBLES[g][1]}') for g in GRUPOS_B1] + [SIN_GRUPO]
    dist_grupos = distribucion(
        'grupos', 'Participantes por grupo de caracterización (B1)', 'participantes',
        'Grupo de la ronda de referencia de cada participante (regla de la Fase 37C). Es una '
        'descripción de hábitos y contexto, no una categoría clínica.',
        grupos_cat, [p['grupo'] for p in incluidas])
    tabla_grupos = []
    for fila in dist_grupos['filas']:
        if fila['clave'] == SIN_GRUPO[0]:
            continue
        miembros = [p['total'] for p in incluidas if p['grupo'] == fila['clave']]
        visible = not fila['oculta'] and len(miembros) >= UMBRAL
        tabla_grupos.append(dict(fila, promedio_mrs=_decimal(mean(miembros)) if visible else None))

    return dict(
        base, n=n,
        rondas_verificables=sum(p['rondas_verificables'] for p in incluidas),
        promedio_total=_decimal(mean(totales)), mediana_total=_decimal(median(totales)),
        maximo=MAXIMO, dimensiones=dims,
        dist_mrs=distribucion(
            'mrs', 'Distribución del puntaje MRS total', 'participantes',
            'Puntaje total (de 0 a 44) de la ronda de referencia de cada participante, agrupado de 5 en 5.',
            [(c, e) for c, e, _a, _b in TRAMOS_MRS], [_tramo(t, TRAMOS_MRS) for t in totales]),
        dist_edad=distribucion(
            'edad', 'Participantes por tramo de edad', 'participantes',
            'Edad cumplida al cierre de la ronda de referencia. Si ese cierre no tiene fecha registrada, '
            'la edad no se calcula (no se usa la edad de hoy).',
            [(c, e) for c, e, _a, _b in TRAMOS_EDAD] + [SIN_EDAD], [p['tramo_edad'] for p in incluidas]),
        dist_grupos=dist_grupos, tabla_grupos=tabla_grupos,
        sin_grupo=next(f for f in dist_grupos['filas'] if f['clave'] == SIN_GRUPO[0]),
    )


ETIQUETAS_EXCLUSION = {
    'presencial': 'Registros presenciales sin cuenta y sin consentimiento presencial registrado',
    'sin_consentimiento': 'Fichas de cuentas sin consentimiento vigente',
    'sin_ronda_verificable': 'Con consentimiento, pero sin ninguna ronda cerrada con resultado MRS definitivo',
}
NOTA_DESCRIPTIVA = (
    'Resultados descriptivos de las participantes incluidas. No son un diagnóstico, no comparan '
    'grupos como categorías clínicas ni indican causas. Las Fases 37D a 39 no encontraron '
    'diferencias del MRS entre grupos que sean útiles para orientar.'
)
