"""
Fase 40B-1: verificación de completitud de una ronda, en MODO OBSERVACIÓN.

Fase 40B-2: además existe el MODO OBLIGATORIO, que es el que usa el cierre
(apps.rondas.cierre). Diferencias con la observación:
- solo exige lo obligatorio aplicable: una sección sin preguntas obligatorias
  visibles no se exige aunque no tenga fila (el cliente igual la envía);
- un ítem MRS nulo es una pregunta sin responder (desde la 0020 los ítems
  admiten nulo);
- en un MRS anterior a la 40B-2 (apps.rondas.MRSAnterior40B2), cada 0 sin
  confirmar se informa como «por_confirmar»: puede ser un valor por defecto.
El modo observación se conserva igual para no cambiar el significado de los
eventos CIERRE ya registrados.

Evalúa lo que la 40B-2 exigiría para cerrar (las mismas reglas que usa el
cliente: el esquema de esquema.py, la visibilidad de condicionales.py con
ocultar en cadena y las secciones condicionales), pero NUNCA rechaza: el
resultado solo se guarda en el evento CIERRE. El cierre sigue igual que antes.

Limitación conocida (40A, RC-1): los 11 ítems del MRS tienen valor por defecto
0, así que un ítem omitido es indistinguible de un 0 respondido. Este
verificador no puede detectarlo; se corrige en la 40B-2, junto con el
validador obligatorio. Por eso el modo observación tiende a declarar
«completa» una ronda con ceros fantasma.

El resultado contiene solo nombres de secciones y de preguntas, nunca valores.
"""
from apps.encuestas.esquema import construir_esquema
from apps.encuestas.models import Identificacion, meses_desde_texto_fecha
from apps.encuestas.sync import SECCIONES
from apps.usuarios.models import Usuario

MODO = 'observacion'
MODO_OBLIGATORIO = 'obligatorio'
LIMITACIONES = ['MRS: los ceros por defecto no se distinguen de respuestas omitidas (se corrige en la 40B-2)']
LIMITACIONES_OBLIGATORIO = ['MRS anteriores a la 40B-2: un 0 solo cuenta si se confirmó en la encuesta']


def _vacio(valor):
    return valor is None or valor == ''


def _lista_contiene(valor, item):
    return str(item) in [s.strip() for s in str('' if valor is None else valor).split(',')]


def condicion_cumplida(regla, datos):
    """Misma regla que condicionCumplida() de encuesta.js."""
    if not regla:
        return True
    actual = datos.get(regla['campo'])
    operador = regla.get('operador', 'igual')
    if operador == 'meses_desde_lt':
        meses = meses_desde_texto_fecha(actual)
        return meses is None or meses < regla['valor']  # fecha ilegible: se muestra
    if operador == 'contiene':
        return _lista_contiene(actual, regla['valor'])
    if isinstance(regla['valor'], bool) or isinstance(actual, bool):
        return actual is regla['valor'] or actual == regla['valor']
    return str(actual) == str(regla['valor'])


def preguntas_visibles(seccion, datos):
    """Misma regla que preguntasVisibles() de encuesta.js (ocultar en cadena)."""
    por_nombre = {p['nombre']: p for p in seccion['preguntas']}
    memo = {}

    def visible(p):
        if p['nombre'] in memo:
            return memo[p['nombre']]
        memo[p['nombre']] = True  # corta ciclos accidentales
        ok = condicion_cumplida(p['mostrar_si'], datos)
        madre = p['mostrar_si'] and por_nombre.get(p['mostrar_si']['campo'])
        if ok and madre:
            ok = visible(madre)
        memo[p['nombre']] = ok
        return ok

    return [p for p in seccion['preguntas'] if visible(p)]


def _datos(instancia):
    if instancia is None:
        return {}
    return {f.name: getattr(instancia, f.name) for f in instancia._meta.fields}


def rol_evaluado(participante):
    """Rol con el que se evalúa: el de la cuenta de la ficha; sin cuenta, la registró una profesional."""
    if participante.usuario_id is None:
        return Usuario.Rol.PROFESIONAL_SALUD
    return participante.usuario.rol


def _ceros_por_confirmar(mrs):
    if mrs is None:
        return []
    from .models import MRSAnterior40B2
    marca = MRSAnterior40B2.objects.filter(mrs=mrs).first()
    return marca.ceros_por_confirmar(mrs) if marca else []


def evaluar(participante: Identificacion, numero: int, rol=None, modo=MODO):
    """
    Qué faltaría para cerrar la ronda `numero`. Devuelve un dict serializable:
    {'modo', 'completa', 'faltantes': [{'seccion', 'motivo', 'preguntas'?}], 'rol_evaluado', 'limitaciones'}.

    `modo`: 'observacion' (40B-1, solo registra) u 'obligatorio' (40B-2, decide el cierre).
    `motivo`: 'ausente', 'obligatorias_sin_responder' o 'por_confirmar' (solo obligatorio).
    """
    obligatorio = modo == MODO_OBLIGATORIO
    rol = rol or rol_evaluado(participante)
    esquema = construir_esquema(rol)
    filas = {}
    for tipo, (modelo, _form) in SECCIONES.items():
        filas[tipo] = modelo.objects.filter(participante=participante, ronda=numero).order_by('id').first()
    datos_por_seccion = {'identificacion': _datos(participante)}
    datos_por_seccion.update({tipo: _datos(fila) for tipo, fila in filas.items()})

    faltantes = []
    for seccion in esquema['secciones']:
        tipo = seccion['tipo']
        modelo_tipo = 'mrs' if tipo == 'mrs_complementario' else tipo
        regla = seccion.get('mostrar_si')
        if regla and not condicion_cumplida({'campo': regla['campo'], 'valor': regla['valor']},
                                            datos_por_seccion.get(regla['seccion'], {})):
            continue  # sección no aplicable (p. ej. Trabajo sin trabajar)
        if modelo_tipo != 'identificacion' and filas.get(modelo_tipo) is None:
            if obligatorio:
                # Solo se exige la fila si la sección tiene algo obligatorio que responder.
                exigidas = [p['nombre'] for p in preguntas_visibles(seccion, {}) if p['obligatoria']]
                if exigidas:
                    faltantes.append({'seccion': tipo, 'motivo': 'obligatorias_sin_responder',
                                      'preguntas': exigidas})
            elif tipo != 'mrs_complementario':  # el MRS ausente se informa una sola vez
                faltantes.append({'seccion': tipo, 'motivo': 'ausente'})
            continue
        datos = datos_por_seccion[modelo_tipo]
        sin_responder = [p['nombre'] for p in preguntas_visibles(seccion, datos)
                         if p['obligatoria'] and _vacio(datos.get(p['nombre']))]
        if sin_responder:
            faltantes.append({'seccion': tipo, 'motivo': 'obligatorias_sin_responder', 'preguntas': sin_responder})
        if obligatorio and tipo == 'mrs':
            por_confirmar = _ceros_por_confirmar(filas.get('mrs'))
            if por_confirmar:
                faltantes.append({'seccion': tipo, 'motivo': 'por_confirmar', 'preguntas': por_confirmar})

    return {'modo': modo, 'completa': not faltantes, 'faltantes': faltantes, 'rol_evaluado': rol,
            'limitaciones': LIMITACIONES_OBLIGATORIO if obligatorio else LIMITACIONES}
