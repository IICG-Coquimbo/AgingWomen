"""
Motor de sincronización offline-first (Sección 5.1 del spec).

`sincronizar_payload(usuario, payload)` recibe lo que el dispositivo acumuló sin
conexión y lo guarda de forma idempotente (por `uuid_local`), aplicando las
reglas de campos por rol (Fase 5B). No conoce HTTP: eso es la Fase 6B.

Convención: el dispositivo envía SIEMPRE el estado completo de cada sección que
tiene guardado localmente. `parcial=True` solo significa "esta sección aún no
está terminada", no "envío únicamente los campos que cambiaron".

Protocolo 2 (Fase 40B-2), compatible con el anterior para guardar borradores:
- `ronda`: la ronda a la que pertenecen las respuestas locales (null si el
  dispositivo aún no la conoce). Si no coincide con la ronda abierta, la
  solicitud entera se rechaza con 409 y no se escribe ninguna respuesta: el
  cliente conserva las suyas y se pone al día.
- `id_cierre`: UUID que el cliente genera al pulsar Finalizar y reutiliza en
  cada reintento; hace idempotente el cierre.
- `confirmados` (solo en el bloque 'mrs'): ítems MRS que la persona eligió en
  esta ronda; confirma los ceros de registros anteriores a la 40B-2.
- `finalizar: true` exige `ronda`: un cliente antiguo no puede cerrar (409
  'cliente_desactualizado') y conserva sus datos locales.
Sin `ronda` (cliente antiguo) los borradores se guardan como antes.

Control de versiones (Etapa 5B-3): cada bloque puede traer `version_base`, la
huella del contenido que el dispositivo conocía (null si creía que no había
nada). Si lo guardado ya no es eso, la solicitud entera se rechaza con 409
'version_desactualizada' y no se escribe nada: el dispositivo tiene una copia
antigua y, como cada envío reemplaza la sección completa, dejaría en blanco lo
que no conoce. No se fusiona nada; decide la persona. `sin_confirmar` trae lo
que este mismo dispositivo envió sin llegar a recibir respuesta, para no
confundir su propio guardado con el de otro. Sin `version_base` (cliente
antiguo) no se comprueba.
"""
import hashlib
import json
import uuid
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.forms.models import model_to_dict
from django.utils import timezone

from apps.usuarios.models import Usuario
from apps.usuarios.privacidad import (
    MENSAJE_SIN_CONSENTIMIENTO_PACIENTE, ficha_sin_consentimiento, participacion_de, participacion_paciente,
    sin_consentimiento_vigente,
)
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
from .plazo import disponible_desde, encuesta_bloqueada, mensaje_espera
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


PROTOCOLO = 2
MAX_SIN_CONFIRMAR = 6   # envíos sin respuesta que se aceptan como propios, por bloque
ITEMS_MRS = tuple(f'pregunta_{i}' for i in range(1, 12))


class ErrorSincronizacion(Exception):
    """Error de nivel payload (formato, permisos), no de validación de un campo."""


class ConflictoRonda(ErrorSincronizacion):
    """
    Fase 40B-2: la solicitud no corresponde a la ronda abierta (llegó tarde, viene
    de otro dispositivo o de un cliente antiguo). No se escribió ninguna respuesta.
    La API responde 409 con `codigo` y `ronda_actual` para que el cliente se ponga al día.
    """

    def __init__(self, codigo, mensaje, ronda_actual=None, extra=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.ronda_actual = ronda_actual
        self.extra = extra or {}

    def como_json(self):
        return {'ok': False, 'codigo': self.codigo, 'error': str(self), 'ronda_actual': self.ronda_actual,
                'protocolo': PROTOCOLO, **self.extra}


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
        if 'version_base' in bloque:
            combinado['version_base'] = bloque['version_base']
            combinado['sin_confirmar'] = bloque.get('sin_confirmar')
        combinado['datos'].update(bloque.get('datos') or {})
        combinado.setdefault('confirmados', [])
        combinado['confirmados'] += [c for c in (bloque.get('confirmados') or []) if isinstance(c, str)]
        combinado['parcial'] = combinado['parcial'] or bool(bloque.get('parcial', True))
    return resto


def identificacion_de_usuaria(usuario):
    """
    Ficha de la usuaria: la asociada a su cuenta o, si el personal de salud la
    registró antes de que ella creara la cuenta (Fase 29), la de su RUT aún
    sin dueña.
    """
    return (Identificacion.objects.filter(usuario=usuario).first()
            or Identificacion.objects.filter(rut_hash=usuario.rut_hash, usuario__isnull=True).first())


def _localizar_ficha(usuario, bloque):
    """La ficha a la que apunta el payload, sin modificar nada (None si aún no existe)."""
    bloque = bloque if isinstance(bloque, dict) else {}
    if not usuario.es_profesional:
        return identificacion_de_usuaria(usuario)
    paciente_id = bloque.get('paciente_id')
    rut = (bloque.get('datos') or {}).get('rut') or bloque.get('rut')
    if paciente_id:
        return Identificacion.objects.filter(pk=paciente_id).first()
    if rut:
        return Identificacion.objects.filter(rut_hash=hash_rut(rut)).first()
    return None


def _leer_ronda(payload):
    valor = payload.get('ronda')
    if valor is None:
        return None
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
        raise ErrorSincronizacion("'ronda' debe ser un entero mayor o igual a 1, o null.")
    return valor


def _leer_id_cierre(payload):
    valor = payload.get('id_cierre')
    if valor in (None, ''):
        return None
    try:
        return uuid.UUID(str(valor))
    except ValueError:
        raise ErrorSincronizacion("'id_cierre' debe ser un UUID.") from None


def _registrar_confirmados_mrs(obj, bloque):
    """Fase 40B-2: ceros de un MRS anterior a la 40B-2 que la persona eligió explícitamente."""
    from apps.rondas.models import MRSAnterior40B2
    marca = MRSAnterior40B2.objects.filter(mrs=obj).first()
    if marca is None:
        return
    datos = bloque.get('datos') or {}
    nuevos = {c for c in (bloque.get('confirmados') or []) if c in ITEMS_MRS and c in datos}
    antes = sorted(marca.items_confirmados or [])
    confirmados = sorted(set(antes) | nuevos)
    if confirmados == antes:
        return
    marca.items_confirmados = confirmados
    if not marca.ceros_por_confirmar(obj) and marca.confirmado_en is None:
        marca.confirmado_en = timezone.now()
    marca.save(update_fields=['items_confirmados', 'confirmado_en'])


def _resolver_identificacion(usuario, bloque):
    bloque = bloque or {}
    datos = dict(bloque.get('datos') or {})
    uuid_local = bloque.get('uuid_local')
    rut = datos.pop('rut', None) or bloque.get('rut')
    paciente_id = bloque.get('paciente_id')

    if usuario.es_profesional:
        # Fase 29: una paciente ya existente se indica por su ficha (el RUT en
        # claro no se guarda); el RUT solo se usa para registrar una nueva.
        if paciente_id:
            existente = Identificacion.objects.filter(pk=paciente_id).first()
            if existente is None:
                raise ErrorSincronizacion('La paciente indicada no existe.')
        elif rut:
            existente = Identificacion.objects.filter(rut_hash=hash_rut(rut)).first()
        else:
            raise ErrorSincronizacion("El profesional debe indicar la paciente ('paciente_id' o 'rut').")
        # Fase 40 (P7): sin consentimiento vigente de la paciente con cuenta no se registra nada.
        if (ficha_sin_consentimiento(existente) if existente
                else sin_consentimiento_vigente(hash_rut(rut))):
            raise ConflictoRonda('consentimiento_paciente', MENSAJE_SIN_CONSENTIMIENTO_PACIENTE)
        if existente and existente.usuario_id and datos:
            raise ErrorSincronizacion(
                'La identificación de una paciente con cuenta propia solo la puede modificar ella.'
            )
    else:
        if rut or paciente_id:
            raise ErrorSincronizacion(
                "Una usuaria común no puede sincronizar datos de otra persona."
            )
        existente = identificacion_de_usuaria(usuario)

    if not datos:
        if existente:
            return existente, {'seccion': 'identificacion', 'estado': 'sin_cambios', 'id': existente.id}
        raise ErrorSincronizacion("Falta el bloque 'identificacion' con los datos demográficos.")

    form = IdentificacionForm(data=datos, instance=existente, rol=usuario.rol)
    if not form.is_valid():
        return None, {'seccion': 'identificacion', 'estado': 'error', 'errores': form.errors}

    ident = form.save(commit=False)
    if usuario.es_profesional:
        if rut:
            ident.rut_hash = hash_rut(rut)
    else:
        ident.usuario = usuario
        ident.rut_hash = usuario.rut_hash
    if uuid_local:
        ident.uuid_local = uuid_local
    ident.sincronizado_en = timezone.now()
    ident.save()
    ident.refresh_from_db()
    return ident, {
        'seccion': 'identificacion',
        'estado': 'actualizado' if existente else 'creado',
        'id': ident.id,
        'version': _version_de(ident, IdentificacionForm),
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
    if instancia is None:
        # Fase 29: la usuaria y el personal de salud pueden completar la misma
        # ronda desde dispositivos distintos (cada uno con su propio uuid_local).
        # Si la sección ya existe en la ronda en curso, se actualiza esa fila en
        # vez de duplicarla, y se devuelve su uuid_local para que el cliente lo adopte.
        instancia = modelo.objects.filter(
            participante=identificacion, ronda=identificacion.ronda_actual,
        ).first()
        if instancia is not None:
            uuid_local = str(instancia.uuid_local)
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
    if tipo == 'mrs':
        _registrar_confirmados_mrs(obj, bloque)
    obj.refresh_from_db()
    return {'seccion': tipo, 'estado': 'actualizado' if instancia else 'creado', 'id': obj.id,
            'uuid_local': str(obj.uuid_local), 'version': _version_de(obj, form_cls)}


def _guardar_seccion_segura(bloque, identificacion, usuario):
    """Cada sección en su propio punto de guardado: un conflicto en una no deshace las demás."""
    from apps.rondas.proteccion import RespuestaHistoricaProtegida
    try:
        with transaction.atomic():
            return _guardar_seccion(bloque, identificacion, usuario)
    except IntegrityError:
        return {'seccion': bloque['tipo'], 'estado': 'error',
                'errores': {'__all__': ['Otra solicitud guardó esta sección al mismo tiempo. Reintenta.']}}
    except RespuestaHistoricaProtegida as exc:
        return {'seccion': bloque['tipo'], 'estado': 'error', 'errores': {'__all__': [str(exc)]}}


def _canonico(obj, form_cls):
    """Contenido de un registro en forma comparable (texto, sin vacíos), guardado o por guardar."""
    campos = list(form_cls(rol=Usuario.Rol.PROFESIONAL_SALUD).fields)
    salida = {}
    for campo, valor in model_to_dict(obj, fields=campos).items():
        if valor is None or valor == '':
            continue
        salida[campo] = str(valor.normalize()) if isinstance(valor, Decimal) else str(valor)
    return salida


def _version_de(obj, form_cls):
    """Etapa 5B-3: huella del contenido; cambia solo si cambian las respuestas guardadas."""
    texto = json.dumps(_canonico(obj, form_cls), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()[:32]


def _dejaria_igual(obj, form_cls, datos, usuario):
    """¿Guardar `datos` dejaría el registro tal como está? Trabaja sobre una copia: no escribe."""
    copia = type(obj).objects.get(pk=obj.pk)
    form = form_cls(data=datos, instance=copia, rol=usuario.rol, parcial=True)
    return form.is_valid() and _canonico(form.save(commit=False), form_cls) == _canonico(obj, form_cls)


def _bloque_desactualizado(obj, form_cls, bloque, usuario):
    if bloque.get('version_base') == _version_de(obj, form_cls):
        return False
    # Lo guardado puede ser de este mismo dispositivo, si se perdió la respuesta de un envío
    # anterior; repetir exactamente lo que ya está tampoco borra nada.
    previos = bloque.get('sin_confirmar')
    previos = previos[-MAX_SIN_CONFIRMAR:] if isinstance(previos, list) else []
    candidatos = [bloque.get('datos') or {}] + [p for p in previos if isinstance(p, dict)]
    return not any(_dejaria_igual(obj, form_cls, c, usuario) for c in candidatos)


def _conflicto_de_version(ficha, payload, usuario):
    """
    Etapa 5B-3: ConflictoRonda si algún bloque se preparó sobre una copia antigua, o None.
    Se llama con la ficha bloqueada y antes de escribir: una solicitud antigua no guarda nada.
    """
    afectadas, versiones = [], {}
    bloque = payload.get('identificacion')
    if isinstance(bloque, dict) and 'version_base' in bloque and bloque.get('datos'):
        versiones['identificacion'] = _version_de(ficha, IdentificacionForm)
        if _bloque_desactualizado(ficha, IdentificacionForm, bloque, usuario):
            afectadas.append('identificacion')
    for bloque in _fusionar_bloques_mrs(payload.get('secciones') or []):
        if not isinstance(bloque, dict) or bloque.get('tipo') not in SECCIONES or 'version_base' not in bloque:
            continue
        tipo = bloque['tipo']
        modelo, form_cls = SECCIONES[tipo]
        obj = modelo.objects.filter(participante=ficha, ronda=ficha.ronda_actual).first()
        if obj is None:
            versiones[tipo] = None
            continue
        versiones[tipo] = _version_de(obj, form_cls)
        if _bloque_desactualizado(obj, form_cls, bloque, usuario):
            afectadas.append(tipo)
    if not afectadas:
        return None
    return ConflictoRonda(
        'version_desactualizada',
        'Tus respuestas cambiaron en otra pestaña o dispositivo. No se guardó nada desde esta página.',
        ronda_actual=ficha.ronda_actual, extra={'secciones': afectadas, 'versiones': versiones})


def _respuesta(ident, resultados, ok, cierre=None):
    fecha = disponible_desde(ident)
    return {'ok': ok, 'resultados': resultados, 'ronda_actual': ident.ronda_actual,
            'paciente_id': ident.id, 'disponible_desde': fecha.isoformat() if fecha else None,
            'guardado': all(r['estado'] != 'error' for r in resultados),
            'cierre': cierre, 'protocolo': PROTOCOLO}


def _verificar_participacion(usuario, payload):
    """
    Fase 40 (P6): una usuaria con consentimiento vigente debe enviar el identificador de
    su participación actual. Un envío sin él (cliente antiguo) o con el de una
    participación anterior al retiro se rechaza sin escribir nada, para que no vuelva a
    crear datos eliminados. (Sin consentimiento, la API ya responde 403.)
    """
    if usuario.es_profesional or not usuario.consentimiento_aceptado_en:
        return
    enviada = payload.get('participacion')
    if enviada is None:
        raise ConflictoRonda(
            'cliente_desactualizado',
            'Esta versión de la encuesta está desactualizada. Recarga la página con conexión a internet.')
    if str(enviada) != participacion_de(usuario):
        raise ConflictoRonda(
            'participacion_anterior',
            'Estas respuestas pertenecen a una participación anterior que fue retirada del estudio. '
            'No se guardaron.')


def _verificar_participacion_paciente(usuario, payload):
    """
    Fase 40 (retiro presencial): lo mismo que `_verificar_participacion`, para lo que una
    profesional envía por una paciente. El bloque de identificación trae la participación
    de la paciente para la que se prepararon las respuestas (`participacion_paciente`);
    si la paciente se retiró (y quizá volvió a consentir), ya no coincide y nada se escribe:
    así una cola antigua no restaura datos eliminados. Si la paciente no tiene
    consentimiento vigente y el envío no trae participación, sigue la regla general (409
    `consentimiento_paciente`).
    """
    if not usuario.es_profesional:
        return
    bloque = payload.get('identificacion')
    if not isinstance(bloque, dict):
        return
    paciente_id = bloque.get('paciente_id')
    rut = (bloque.get('datos') or {}).get('rut') or bloque.get('rut')
    if paciente_id:
        ficha = Identificacion.objects.filter(pk=paciente_id).only('rut_hash', 'usuario_id').first()
        if ficha is None:
            return   # la ficha no existe (p. ej., se retiró): el flujo normal lo rechaza
        vigente = participacion_paciente(ficha.rut_hash, usuario_id=ficha.usuario_id)
    elif rut:
        vigente = participacion_paciente(hash_rut(rut))
    else:
        return
    enviada = bloque.get('participacion_paciente')
    if enviada is None:
        if vigente is None:
            return   # sin consentimiento: 409 consentimiento_paciente más adelante
        raise ConflictoRonda(
            'cliente_desactualizado',
            'Esta versión de la encuesta está desactualizada. Recarga la página con conexión a internet.')
    if str(enviada) != vigente:
        raise ConflictoRonda(
            'participacion_anterior',
            'Estas respuestas pertenecen a una participación de la paciente que fue retirada del estudio. '
            'No se guardaron.')


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

    Fase 40B-2: todo ocurre en una transacción con la ficha bloqueada, y la
    ronda se cierra solo si está completa (apps.rondas.cierre). Si no lo está,
    lo guardado queda como borrador, ``ok`` es False y ``cierre`` dice qué
    falta. Repetir un cierre ya hecho (mismo ``id_cierre``) devuelve el mismo
    resultado sin escribir respuestas. Lanza `ConflictoRonda` si la solicitud
    no es para la ronda abierta.
    """
    if not isinstance(payload, dict):
        raise ErrorSincronizacion("El cuerpo debe ser un objeto JSON.")

    finalizar = bool(payload.get('finalizar'))
    estricto = 'ronda' in payload  # protocolo 2
    ronda_enviada = _leer_ronda(payload)
    id_cierre = _leer_id_cierre(payload)
    _verificar_participacion(usuario, payload)
    _verificar_participacion_paciente(usuario, payload)
    if finalizar and not estricto:
        raise ConflictoRonda(
            'cliente_desactualizado',
            'Esta versión de la encuesta no puede finalizar de forma segura. Recarga la página: '
            'tus respuestas siguen guardadas en este dispositivo.')

    with transaction.atomic():
        resultado = _sincronizar(usuario, payload, finalizar, estricto, ronda_enviada, id_cierre)
    if isinstance(resultado, ConflictoRonda):
        raise resultado  # fuera de la transacción: el evento de rechazo ya quedó registrado
    return resultado


def _sincronizar(usuario, payload, finalizar, estricto, ronda_enviada, id_cierre):
    from apps.rondas import cierre as servicio_cierre

    ficha = _localizar_ficha(usuario, payload.get('identificacion'))
    if ficha is not None:
        # Bloqueo de la ficha: dos solicitudes de la misma participante se ordenan.
        ficha = Identificacion.objects.select_for_update().get(pk=ficha.pk)

    # 1. Reintento de un cierre ya hecho (antes del plazo entre rondas, que ya corre).
    if finalizar and id_cierre is not None:
        try:
            previa = servicio_cierre.cierre_previo(ficha, id_cierre)
        except ValueError:
            raise ErrorSincronizacion("'id_cierre' no corresponde a esta participante.") from None
        if previa is not None:
            servicio_cierre.registrar_reintento(previa, usuario)
            return _respuesta(ficha, [], True, cierre={'estado': 'repetido', 'ronda': previa.numero,
                                                       'id_cierre': str(previa.id_cierre)})

    # 2. La solicitud debe ser para la ronda abierta (protocolo 2).
    if estricto:
        esperada = ficha.ronda_actual if ficha is not None else 1
        codigo = mensaje = None
        if ficha is not None and ronda_enviada is None:
            codigo, mensaje = 'ronda_desconocida', 'El dispositivo no sabe a qué ronda pertenecen sus respuestas.'
        elif ronda_enviada is not None and ronda_enviada != esperada:
            if ronda_enviada < esperada:
                codigo, mensaje = 'ronda_cerrada', f'La ronda {ronda_enviada} ya está cerrada.'
            else:
                codigo, mensaje = 'ronda_inexistente', f'La ronda {ronda_enviada} no está abierta.'
        if codigo:
            if ficha is not None:
                tipos = [b.get('tipo') for b in payload.get('secciones') or [] if isinstance(b, dict)]
                servicio_cierre.registrar_escritura_rechazada(
                    ficha, ronda_enviada, usuario, [x for x in tipos if isinstance(x, str)], codigo)
            return ConflictoRonda(codigo, mensaje, ronda_actual=esperada)

    if not usuario.es_profesional:
        # Fase 31: dentro del plazo entre rondas la usuaria no puede guardar
        # (el personal de salud no tiene esta restricción).
        if encuesta_bloqueada(ficha):
            raise ErrorSincronizacion(mensaje_espera(ficha))

    if ficha is not None:
        conflicto = _conflicto_de_version(ficha, payload, usuario)
        if conflicto is not None:
            return conflicto

    resultados = []
    ident, res_ident = _resolver_identificacion(usuario, payload.get('identificacion'))
    resultados.append(res_ident)
    if ident is None:
        return {'ok': False, 'resultados': resultados, 'guardado': False, 'cierre': None,
                'protocolo': PROTOCOLO}

    for bloque in _fusionar_bloques_mrs(payload.get('secciones') or []):
        if not isinstance(bloque, dict) or bloque.get('tipo') not in SECCIONES:
            resultados.append({
                'seccion': (bloque or {}).get('tipo') if isinstance(bloque, dict) else None,
                'estado': 'error',
                'errores': {'tipo': ['Sección desconocida.']},
            })
            continue
        resultados.append(_guardar_seccion_segura(bloque, ident, usuario))

    ok = all(r['estado'] != 'error' for r in resultados)
    cierre = None
    if ok and finalizar:
        cierre = servicio_cierre.cerrar(ident, usuario, id_cierre)
        ok = cierre['estado'] == 'cerrada'
    return _respuesta(ident, resultados, ok, cierre)


def _serializar(valor):
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, (list, tuple)):
        return ', '.join(str(v) for v in valor)
    return valor


def _datos_de(obj, form_cls):
    # Todos los campos que puede ver el personal de salud (el máximo de campos).
    campos = list(form_cls(rol=Usuario.Rol.PROFESIONAL_SALUD).fields)
    return {k: _serializar(v) for k, v in model_to_dict(obj, fields=campos).items() if v is not None}


def estado_ronda(ident):
    """
    Respuestas guardadas de la ronda en curso (Fase 29), en el formato que usa
    el cliente: así la encuesta se abre con lo ya respondido (por la usuaria o
    por el personal de salud) y sigue escribiendo en las mismas filas.
    """
    from apps.rondas.models import MRSAnterior40B2

    secciones = {}
    por_confirmar = []
    for tipo, (modelo, form_cls) in SECCIONES.items():
        obj = modelo.objects.filter(participante=ident, ronda=ident.ronda_actual).first()
        if obj is not None:
            datos = _datos_de(obj, form_cls)
            if tipo == 'mrs':
                # Fase 40B-2: un 0 de un MRS anterior a la 40B-2 puede ser un valor por
                # defecto: no se presenta como respondido hasta que se confirme.
                marca = MRSAnterior40B2.objects.filter(mrs=obj).first()
                por_confirmar = marca.ceros_por_confirmar(obj) if marca else []
                for item in por_confirmar:
                    datos.pop(item, None)
            secciones[tipo] = {'uuid_local': str(obj.uuid_local), 'datos': datos,
                               'version': _version_de(obj, form_cls)}
    fecha = disponible_desde(ident)
    return {
        'protocolo': PROTOCOLO,
        'mrs_por_confirmar': por_confirmar,
        'paciente_id': ident.id,
        'ronda_actual': ident.ronda_actual,
        'disponible_desde': fecha.isoformat() if fecha else None,
        'bloqueada': encuesta_bloqueada(ident),
        'identificacion': {
            'uuid_local': str(ident.uuid_local) if ident.uuid_local else None,
            'datos': _datos_de(ident, IdentificacionForm),
            'version': _version_de(ident, IdentificacionForm),
            'bloqueada': ident.usuario_id is not None,
        },
        'secciones': secciones,
    }
