"""
Motor de sincronización offline-first (Sección 5.1 del spec).

`sincronizar_payload(usuario, payload)` recibe lo que el dispositivo acumuló sin
conexión y lo guarda de forma idempotente (por `uuid_local`), aplicando las
reglas de campos por rol (Fase 5B). No conoce HTTP: eso es la Fase 6B.

Convención: el dispositivo envía SIEMPRE el estado completo de cada sección que
tiene guardado localmente. `parcial=True` solo significa "esta sección aún no
está terminada", no "envío únicamente los campos que cambiaron".
"""
from django.utils import timezone

from apps.usuarios.rut import hash_rut

from .forms import (
    ActividadFisicaForm,
    ConocimientoSistemaForm,
    EvaluacionTrabajoForm,
    HabitosDeVidaForm,
    IdentificacionForm,
    MRSForm,
    SegmentoEMPAForm,
    TareasCuidadoForm,
)
from .models import (
    ActividadFisica,
    ConocimientoSistema,
    EvaluacionTrabajo,
    HabitosDeVida,
    Identificacion,
    MRS,
    SegmentoEMPA,
    TareasCuidado,
)

# tipo de sección -> (modelo, formulario)
SECCIONES = {
    'mrs': (MRS, MRSForm),
    'empa': (SegmentoEMPA, SegmentoEMPAForm),
    'conocimiento_sistema': (ConocimientoSistema, ConocimientoSistemaForm),
    'trabajo': (EvaluacionTrabajo, EvaluacionTrabajoForm),
    'tareas_cuidado': (TareasCuidado, TareasCuidadoForm),
    'habitos_de_vida': (HabitosDeVida, HabitosDeVidaForm),
    'actividad_fisica': (ActividadFisica, ActividadFisicaForm),
}


class ErrorSincronizacion(Exception):
    """Error de nivel payload (formato, permisos), no de validación de un campo."""


def _fusionar_bloques_mrs(secciones):
    """
    El MRS se responde en dos pantallas ('mrs' = 11 ítems Likert,
    'mrs_complementario' = cuestionario complementario) pero es un solo
    registro. El cliente normalmente ya envía un único bloque 'mrs' con todo;
    esta función combina los bloques por si llegan separados (p. ej. desde una
    caché offline antigua): un solo bloque 'mrs', datos unidos, `parcial` = True
    si cualquiera de las partes venía incompleta.
    """
    combinado = None
    resto = []
    for bloque in secciones:
        tipo = bloque.get('tipo') if isinstance(bloque, dict) else None
        if tipo not in ('mrs', 'mrs_complementario'):
            resto.append(bloque)
            continue
        if combinado is None:
            combinado = {'tipo': 'mrs', 'uuid_local': None, 'datos': {}, 'parcial': False}
            resto.append(combinado)
        combinado['uuid_local'] = combinado['uuid_local'] or bloque.get('uuid_local')
        combinado['datos'].update(bloque.get('datos') or {})
        combinado['parcial'] = combinado['parcial'] or bool(bloque.get('parcial', True))
    return resto


def _resolver_identificacion(usuario, bloque):
    bloque = bloque or {}
    datos = dict(bloque.get('datos') or {})
    uuid_local = bloque.get('uuid_local')
    rut = datos.pop('rut', None) or bloque.get('rut')

    if usuario.es_profesional:
        if not rut:
            raise ErrorSincronizacion("El profesional debe indicar el 'rut' de la paciente.")
        existente = Identificacion.objects.filter(rut_hash=hash_rut(rut)).first()
    else:
        if rut:
            raise ErrorSincronizacion(
                "Una usuaria común no puede sincronizar datos por RUT de otra persona."
            )
        existente = Identificacion.objects.filter(usuario=usuario).first()

    if not datos:
        if existente:
            return existente, {'seccion': 'identificacion', 'estado': 'sin_cambios', 'id': existente.id}
        raise ErrorSincronizacion("Falta el bloque 'identificacion' con los datos demográficos.")

    form = IdentificacionForm(data=datos, instance=existente, rol=usuario.rol)
    if not form.is_valid():
        return None, {'seccion': 'identificacion', 'estado': 'error', 'errores': form.errors}

    ident = form.save(commit=False)
    if usuario.es_profesional:
        ident.rut_hash = hash_rut(rut)
    else:
        ident.usuario = usuario
        ident.rut_hash = usuario.rut_hash
    if uuid_local:
        ident.uuid_local = uuid_local
    ident.sincronizado_en = timezone.now()
    ident.save()
    return ident, {
        'seccion': 'identificacion',
        'estado': 'actualizado' if existente else 'creado',
        'id': ident.id,
    }


def _guardar_seccion(bloque, identificacion, usuario):
    tipo = bloque['tipo']
    modelo, form_cls = SECCIONES[tipo]
    uuid_local = bloque.get('uuid_local')
    datos = bloque.get('datos') or {}
    parcial = bool(bloque.get('parcial', True))

    if not uuid_local:
        return {'seccion': tipo, 'estado': 'error', 'errores': {'uuid_local': ['Requerido.']}}

    instancia = modelo.objects.filter(uuid_local=uuid_local).first()
    if instancia and instancia.participante_id != identificacion.id:
        return {'seccion': tipo, 'estado': 'error',
                'errores': {'uuid_local': ['Ya pertenece a otro registro.']}}
    if instancia and instancia.ronda != identificacion.ronda_actual:
        # La ronda a la que pertenecía ese uuid_local ya se cerró (se finalizó
        # una ronda posterior): no se sobrescribe historial (Fase 13).
        return {'seccion': tipo, 'estado': 'error',
                'errores': {'uuid_local': ['Pertenece a una ronda ya finalizada.']}}

    form = form_cls(data=datos, instance=instancia, rol=usuario.rol, parcial=parcial)
    if not form.is_valid():
        return {'seccion': tipo, 'estado': 'error', 'errores': form.errors}

    obj = form.save(commit=False)
    obj.participante = identificacion
    obj.uuid_local = uuid_local
    obj.ronda = identificacion.ronda_actual
    if hasattr(obj, 'origen_registro'):
        obj.origen_registro = (
            SegmentoEMPA.OrigenDato.PERSONAL_MEDICO if usuario.es_profesional
            else SegmentoEMPA.OrigenDato.AUTORREPORTADO
        )
    obj.sincronizado_en = timezone.now()
    obj.save()
    return {'seccion': tipo, 'estado': 'actualizado' if instancia else 'creado', 'id': obj.id}


def sincronizar_payload(usuario, payload):
    """
    Procesa un payload de sincronización. Devuelve
    ``{'ok': bool, 'resultados': [...], 'ronda_actual': int}``.

    Cada sección se guarda de forma independiente: un error de validación en una
    no impide guardar las demás (semántica offline: guarda lo válido, informa lo
    que no). Lanza `ErrorSincronizacion` solo ante problemas de formato o permisos.

    Si el payload trae ``finalizar: true`` y todo se guardó sin errores, la
    ronda en curso se sella y ``ronda_actual`` avanza (Fase 13): la próxima
    vez que la participante responda la encuesta, sus respuestas se guardan
    en filas nuevas, sin tocar las de esta ronda.
    """
    if not isinstance(payload, dict):
        raise ErrorSincronizacion("El cuerpo debe ser un objeto JSON.")

    resultados = []
    ident, res_ident = _resolver_identificacion(usuario, payload.get('identificacion'))
    resultados.append(res_ident)
    if ident is None:
        return {'ok': False, 'resultados': resultados}

    for bloque in _fusionar_bloques_mrs(payload.get('secciones') or []):
        if not isinstance(bloque, dict) or bloque.get('tipo') not in SECCIONES:
            resultados.append({
                'seccion': (bloque or {}).get('tipo') if isinstance(bloque, dict) else None,
                'estado': 'error',
                'errores': {'tipo': ['Sección desconocida.']},
            })
            continue
        resultados.append(_guardar_seccion(bloque, ident, usuario))

    ok = all(r['estado'] != 'error' for r in resultados)

    if ok and payload.get('finalizar'):
        ident.ronda_actual += 1
        ident.save(update_fields=['ronda_actual'])

    return {'ok': ok, 'resultados': resultados, 'ronda_actual': ident.ronda_actual}
