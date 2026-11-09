"""
Fase 40B-3: única regla para PRESENTAR el resultado MRS de una ronda.

Todas las pantallas (tablero de la usuaria, ficha profesional y cualquier
resumen futuro) deben pasar por `resultado_mrs()`, para que no haya criterios
distintos entre ellas. Solo lee: nunca modifica respuestas, no reconstruye
valores históricos ni convierte ceros antiguos en nulos.

Estados:
- DEFINITIVO: ronda cerrada, los 11 ítems respondidos y ningún cero anterior a
  la 40B-2 sin confirmar. Es el único estado que muestra un puntaje como resultado.
- PROVISIONAL: ronda abierta con los 11 ítems respondidos. Suma provisional.
- PARCIAL: ronda abierta a la que le faltan ítems. Suma parcial, con cuántos
  ítems lleva. Los ceros anteriores sin confirmar cuentan como sin responder.
- NO_VERIFICABLE: ronda cerrada con ceros anteriores a la 40B-2 que nadie
  confirmó (o cuyo registro de ronda no dice CERRADA). No se muestra ningún número.
- INCOMPLETO: ronda cerrada a la que le faltan ítems (no debería ocurrir desde
  la 40B-2; se informa en vez de mostrar una suma).
- SIN_DATOS: la ronda no tiene MRS.

Fase 40C: las dimensiones (somática, psicológica, urogenital) se calculan aquí
mismo y SOLO para un resultado DEFINITIVO; en cualquier otro estado no existen.
Su correspondencia con los campos del cuestionario se verificó por el contenido
de cada síntoma (ver analisis/fase40/40C_tablero/40C_informe.md, §2):

  escala original (Heinemann)        campo en AgingWomen
  1  bochornos, sudoración           pregunta_1   somática
  2  molestias al corazón            pregunta_2   somática
  11 molestias musculares/articul.   pregunta_3   somática
  3  problemas de sueño              pregunta_4   somática
  4  ánimo depresivo                 pregunta_5   psicológica
  5  irritabilidad                   pregunta_6   psicológica
  6  ansiedad                        pregunta_7   psicológica
  7  agotamiento físico y mental     pregunta_8   psicológica
  8  problemas sexuales              pregunta_9   urogenital
  9  problemas de vejiga (orina)     pregunta_10  urogenital
  10 sequedad vaginal                pregunta_11  urogenital

No hay categoría de severidad: los cortes de `MRS.SEVERIDAD_TOTAL` son los
históricos de las Fases 34 a 39 y no están validados para mostrarse en la
plataforma (decisión de la 40B-3).
"""
from dataclasses import dataclass

from apps.encuestas.models import Identificacion

ITEMS = tuple(f'pregunta_{i}' for i in range(1, 12))
MAXIMO = 4 * len(ITEMS)

DEFINITIVO = 'definitivo'
PROVISIONAL = 'provisional'
PARCIAL = 'parcial'
NO_VERIFICABLE = 'no_verificable'
INCOMPLETO = 'incompleto'
SIN_DATOS = 'sin_datos'

TEXTO_NO_VERIFICABLE = 'Resultado histórico no verificable'

# Fase 40C. (clave, nombre, campos). Se agrupan por el CONTENIDO de cada pregunta
# (tabla del docstring); que en este cuestionario queden en bloques seguidos es
# consecuencia del orden del formulario, no una suposición.
DIMENSIONES = (
    ('somatica', 'Somática', ('pregunta_1', 'pregunta_2', 'pregunta_3', 'pregunta_4')),
    ('psicologica', 'Psicológica', ('pregunta_5', 'pregunta_6', 'pregunta_7', 'pregunta_8')),
    ('urogenital', 'Urogenital', ('pregunta_9', 'pregunta_10', 'pregunta_11')),
)
# Las dimensiones reparten los 11 ítems sin repetir ni omitir ninguno: su suma es el total.
assert sorted(c for _, _, cs in DIMENSIONES for c in cs) == sorted(ITEMS)


@dataclass(frozen=True)
class Dimension:
    clave: str
    nombre: str
    puntaje: int
    maximo: int


@dataclass(frozen=True)
class ResultadoMRS:
    estado: str
    puntaje: int | None = None          # solo DEFINITIVO
    suma: int | None = None             # PROVISIONAL o PARCIAL (nunca un resultado)
    respondidas: int = 0
    ceros_sin_confirmar: int = 0
    dimensiones: tuple = ()             # solo DEFINITIVO (Fase 40C): tupla de Dimension

    @property
    def es_definitivo(self):
        return self.estado == DEFINITIVO

    @property
    def texto(self):
        if self.estado == DEFINITIVO:
            return f'Puntaje MRS: {self.puntaje} de {MAXIMO}'
        if self.estado == PROVISIONAL:
            return f'Suma provisional: {self.suma} de {MAXIMO} (la ronda no está cerrada)'
        if self.estado == PARCIAL:
            return (f'Suma parcial: {self.suma} ({self.respondidas} de {len(ITEMS)} preguntas respondidas; '
                    'la ronda no está cerrada)')
        if self.estado == NO_VERIFICABLE:
            return TEXTO_NO_VERIFICABLE
        if self.estado == INCOMPLETO:
            return f'Resultado incompleto: {self.respondidas} de {len(ITEMS)} preguntas respondidas'
        return ''

    def como_dict(self):
        return {'estado': self.estado, 'puntaje': self.puntaje, 'suma': self.suma,
                'respondidas': self.respondidas, 'texto': self.texto,
                'dimensiones': {d.clave: d.puntaje for d in self.dimensiones}}


def _ceros_sin_confirmar(mrs):
    from .models import MRSAnterior40B2
    marca = MRSAnterior40B2.objects.filter(mrs=mrs).first()
    return marca.ceros_por_confirmar(mrs) if marca else []


def estados_registro(participante_id):
    """{número de ronda: estado del registro 40B-1} de una participante (una consulta)."""
    from .models import RondaEvaluacion
    return dict(RondaEvaluacion.objects.filter(participante_id=participante_id)
                .values_list('numero', 'estado'))


def resultado_mrs(mrs, ronda_actual=None, estados=None):
    """
    Resultado presentable del MRS `mrs`. `ronda_actual` y `estados` (de
    `estados_registro`) se pueden pasar para no repetir consultas; si faltan, se leen.
    """
    if mrs is None:
        return ResultadoMRS(SIN_DATOS)
    from .models import EstadoRonda
    if ronda_actual is None:
        ronda_actual = (Identificacion.objects.filter(pk=mrs.participante_id)
                        .values_list('ronda_actual', flat=True).first())
    if estados is None:
        estados = estados_registro(mrs.participante_id)
    # Misma regla que la barrera de protección (proteccion.py): cerrada = anterior a la ronda actual.
    cerrada = ronda_actual is not None and mrs.ronda < ronda_actual
    sin_confirmar = set(_ceros_sin_confirmar(mrs))
    valores = {i: getattr(mrs, i) for i in ITEMS}
    respondidos = [i for i in ITEMS if valores[i] is not None and i not in sin_confirmar]
    suma = sum(valores[i] for i in respondidos)
    n = len(respondidos)

    if cerrada:
        registro = estados.get(mrs.ronda)
        if sin_confirmar or (registro is not None and registro != EstadoRonda.CERRADA):
            return ResultadoMRS(NO_VERIFICABLE, respondidas=n, ceros_sin_confirmar=len(sin_confirmar))
        if n < len(ITEMS):
            return ResultadoMRS(INCOMPLETO, respondidas=n)
        dimensiones = tuple(Dimension(clave, nombre, sum(valores[c] for c in campos), 4 * len(campos))
                            for clave, nombre, campos in DIMENSIONES)
        return ResultadoMRS(DEFINITIVO, puntaje=suma, respondidas=n, dimensiones=dimensiones)
    if n < len(ITEMS):
        return ResultadoMRS(PARCIAL, suma=suma, respondidas=n, ceros_sin_confirmar=len(sin_confirmar))
    return ResultadoMRS(PROVISIONAL, suma=suma, respondidas=n)
