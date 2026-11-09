"""
Fase 40B-2: ayuda para las pruebas que necesitan CERRAR una ronda.

Desde la 40B-2 una ronda solo se cierra completa y con el protocolo 2
(`ronda` en el payload). Muchas pruebas anteriores usaban el cierre solo como
paso previo («pasar a la ronda 2») con un MRS de un ítem, que era justamente
el defecto RC-1 de la 40A. `protocolo2()` deja intacto lo que la prueba envía
y solo agrega:
- `ronda`: la ronda abierta de la ficha (o None si la ficha aún no existe);
- si `finalizar` es verdadero, lo obligatorio que falte: los 11 ítems MRS.
  (Revisión correctiva 40B-2: el EMPA ya no es obligatorio para nadie, así
  que no se completa; `EMPA_PROFESIONAL` queda solo como dato de ejemplo.)
No es código de la plataforma: solo lo importan las pruebas.
"""
from copy import deepcopy
from uuid import uuid4

from apps.encuestas.sync import _localizar_ficha
from apps.usuarios.privacidad import participacion_de

MRS_COMPLETO = {f'pregunta_{i}': 1 for i in range(1, 12)}
EMPA_PROFESIONAL = {'talla_actual_cm': '160', 'peso_kg': '65', 'presion_sistolica': 120,
                    'presion_diastolica': 80}


def _agregar(secciones, tipo, valores, tipos=None):
    tipos = tipos or (tipo,)
    bloques = [b for b in secciones if isinstance(b, dict) and b.get('tipo') in tipos]
    presentes = set()
    for b in bloques:
        presentes |= set((b.get('datos') or {}).keys())
    faltan = {k: v for k, v in valores.items() if k not in presentes}
    if not faltan:
        return
    if bloques:
        bloques[0].setdefault('datos', {}).update(faltan)
    else:
        secciones.append({'tipo': tipo, 'uuid_local': str(uuid4()), 'parcial': False, 'datos': faltan})


def _agregar_participacion_paciente(usuario, p):
    """Fase 40: como encuesta.js en modo profesional, la participación vigente de la paciente."""
    from apps.encuestas.models import Identificacion
    from apps.usuarios.privacidad import participacion_paciente
    from apps.usuarios.rut import hash_rut
    ident = p.get('identificacion')
    if not usuario.es_profesional or not isinstance(ident, dict) or 'participacion_paciente' in ident:
        return
    rut = (ident.get('datos') or {}).get('rut') or ident.get('rut')
    vigente = None
    if ident.get('paciente_id'):
        ficha = Identificacion.objects.filter(pk=ident['paciente_id']).first()
        if ficha is not None:
            vigente = participacion_paciente(ficha.rut_hash, usuario_id=ficha.usuario_id)
    elif rut:
        vigente = participacion_paciente(hash_rut(rut))
    if vigente:
        ident['participacion_paciente'] = vigente


def con_participacion(usuario, payload):
    """Copia del payload con la participación vigente de la usuaria (como el cliente real)."""
    p = deepcopy(payload)
    if not isinstance(p, dict):
        return p
    usuario.refresh_from_db(fields=['consentimiento_aceptado_en'])
    if not usuario.es_profesional and participacion_de(usuario):
        p.setdefault('participacion', participacion_de(usuario))
    _agregar_participacion_paciente(usuario, p)
    return p


def sincronizar_como_cliente(usuario, payload):
    """sincronizar_payload con la participación vigente, como la envía encuesta.js (Fase 40)."""
    from apps.encuestas.sync import sincronizar_payload
    return sincronizar_payload(usuario, con_participacion(usuario, payload))


def protocolo2(usuario, payload, ronda='actual'):
    p = deepcopy(payload)
    if ronda == 'actual':
        ficha = _localizar_ficha(usuario, p.get('identificacion'))
        p['ronda'] = ficha.ronda_actual if ficha else None
    else:
        p['ronda'] = ronda
    if 'participacion' not in p and not usuario.es_profesional:
        usuario.refresh_from_db(fields=['consentimiento_aceptado_en'])
        if participacion_de(usuario):
            p['participacion'] = participacion_de(usuario)
    _agregar_participacion_paciente(usuario, p)
    if p.get('finalizar'):
        secciones = p.setdefault('secciones', [])
        _agregar(secciones, 'mrs', MRS_COMPLETO, tipos=('mrs', 'mrs_complementario'))
    return p


def consentimiento_presencial(rut, profesional, folio=None):
    """Fase 40, Etapa 2: consentimiento presencial ficticio (paciente sin cuenta) para las pruebas."""
    from apps.usuarios.models import ConsentimientoPresencial
    from apps.usuarios.rut import hash_rut
    return ConsentimientoPresencial.objects.create(
        rut_hash=hash_rut(rut), version='prueba', folio_documento=folio or f'PRUEBA-{uuid4().hex[:12]}',
        verificacion=ConsentimientoPresencial.Verificacion.DOCUMENTO_FIRMADO,
        custodia='Archivo ficticio de prueba', registrado_por=profesional)
