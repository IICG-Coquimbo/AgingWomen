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
from django.utils.dateparse import parse_datetime
from uuid import UUID

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
    EvaluacionSatisfaccion,
    EnvioEncuesta,
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
    validacion_inicial_en = parse_datetime(datos.get('validacion_inicial_en', '') or '')
    uuid_local = bloque.get('uuid_local')
    rut = datos.pop('rut', None) or bloque.get('rut')
    consentimiento = datos.pop('consentimiento', None) or bloque.get('consentimiento')

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
    nacimiento = ident.fecha_nacimiento
    hoy = timezone.localdate()
    ident.edad_calculada = hoy.year - nacimiento.year - (
        (hoy.month, hoy.day) < (nacimiento.month, nacimiento.day)
    )
    if validacion_inicial_en and timezone.is_naive(validacion_inicial_en):
        validacion_inicial_en = timezone.make_aware(validacion_inicial_en)
    ident.validacion_inicial_en = (
        ident.validacion_inicial_en or validacion_inicial_en or timezone.now()
    )
    if usuario.es_profesional:
        ident.rut_hash = hash_rut(rut)
    else:
        ident.usuario = usuario
        ident.rut_hash = usuario.rut_hash
    if uuid_local:
        ident.uuid_local = uuid_local
    if consentimiento and consentimiento.get('aceptado'):
        ident.consentimiento_aceptado = True
        ident.consentimiento_aceptado_en = ident.consentimiento_aceptado_en or timezone.now()
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

    form = form_cls(data=datos, instance=instancia, rol=usuario.rol, parcial=parcial)
    if not form.is_valid():
        return {'seccion': tipo, 'estado': 'error', 'errores': form.errors}

    obj = form.save(commit=False)
    obj.participante = identificacion
    obj.uuid_local = uuid_local
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
    ``{'ok': bool, 'resultados': [ {seccion, estado, ...}, ... ]}``.

    Cada sección se guarda de forma independiente: un error de validación en una
    no impide guardar las demás (semántica offline: guarda lo válido, informa lo
    que no). Lanza `ErrorSincronizacion` solo ante problemas de formato o permisos.
    """
    if not isinstance(payload, dict):
        raise ErrorSincronizacion("El cuerpo debe ser un objeto JSON.")

    resultados = []
    ident, res_ident = _resolver_identificacion(usuario, payload.get('identificacion'))
    resultados.append(res_ident)
    if ident is None:
        return {'ok': False, 'resultados': resultados}

    evaluacion = payload.get('evaluacion_satisfaccion')
    if evaluacion:
        campos = (
            'facilidad_uso', 'fatiga_mental', 'comodidad_diseno',
            'recomendaria', 'incomodidad',
        )
        faltantes = [campo for campo in campos if evaluacion.get(campo) in (None, '')]
        if faltantes:
            resultados.append({
                'seccion': 'satisfaccion',
                'estado': 'error',
                'errores': {'campos': ['Faltan respuestas obligatorias.']},
            })
        elif evaluacion.get('incomodidad') == 'SI' and not str(
                evaluacion.get('comentario_incomodidad') or '').strip():
            resultados.append({
                'seccion': 'satisfaccion',
                'estado': 'error',
                'errores': {'comentario_incomodidad': ['Describe la incomodidad o confusión.']},
            })
        else:
            evaluacion_obj, creado = EvaluacionSatisfaccion.objects.update_or_create(
                participante=ident,
                defaults={
                    'facilidad_uso': evaluacion['facilidad_uso'],
                    'fatiga_mental': evaluacion['fatiga_mental'],
                    'comodidad_diseno': evaluacion['comodidad_diseno'],
                    'recomendaria': evaluacion['recomendaria'],
                    'incomodidad': evaluacion['incomodidad'],
                    'comentario_incomodidad': evaluacion.get('comentario_incomodidad', ''),
                },
            )
            resultados.append({
                'seccion': 'satisfaccion',
                'estado': 'creado' if creado else 'actualizado',
                'id': evaluacion_obj.id,
            })

    if payload.get('envio_final') and payload.get('envio_uuid'):
        try:
            envio_uuid = UUID(str(payload['envio_uuid']))
        except (TypeError, ValueError):
            resultados.append({
                'seccion': 'envio_final', 'estado': 'error',
                'errores': {'envio_uuid': ['UUID inválido.']},
            })
        else:
            envio, creado = EnvioEncuesta.objects.get_or_create(
                envio_uuid=envio_uuid,
                defaults={
                    'participante': ident,
                    'payload': payload,
                    'creado_por': usuario,
                },
            )
            if not creado and envio.participante_id != ident.id:
                resultados.append({
                    'seccion': 'envio_final', 'estado': 'error',
                    'errores': {'envio_uuid': ['El envío pertenece a otra participante.']},
                })
            else:
                resultados.append({
                    'seccion': 'envio_final',
                    'estado': 'creado' if creado else 'existente',
                    'id': envio.id,
                })
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
    return {'ok': ok, 'resultados': resultados}
