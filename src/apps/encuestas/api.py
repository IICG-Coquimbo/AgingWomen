"""
Endpoints HTTP de sincronización offline-first (Sección 5.1 del spec).

- POST /api/sincronizar/  -> recibe el payload acumulado en el dispositivo.
- GET  /api/estado/       -> qué secciones ya tiene registradas la usuaria.
- GET  /api/ronda-actual/ -> respuestas de la ronda en curso (propias, o de una
                             paciente con ?paciente=<id> si es personal de salud).

Requieren sesión iniciada (regla 1.1). La escritura (/api/sincronizar/) exige
además el consentimiento vigente de la usuaria común: sin él responde 403 en
JSON (Fase 40S-1). Una solicitud para una ronda que no es la abierta recibe
409 con `codigo` (Fase 40B-2). El CSRF sigue activo: el cliente debe
enviar el header `X-CSRFToken` con el valor de la cookie `csrftoken`.
"""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from apps.usuarios.decorators import requiere_consentimiento_api
from apps.usuarios.privacidad import (
    MENSAJE_SIN_CONSENTIMIENTO_PACIENTE, clave_local, cuenta_local, ficha_sin_consentimiento, participacion_de,
)

from .esquema import construir_esquema
from .models import Identificacion
from .sync import (
    SECCIONES, ConflictoRonda, ErrorSincronizacion, estado_ronda, identificacion_de_usuaria, sincronizar_payload,
)


@login_required
@require_GET
def esquema(request):
    """Estructura completa de la encuesta para que el cliente la renderice offline."""
    return JsonResponse(construir_esquema(request.user.rol))


@never_cache
@require_GET
def clave_local_api(request):
    """
    Fase 40 (P1, P3, P6): clave con la que el navegador cifra lo que guarda en IndexedDB.
    Solo con sesión iniciada (sin sesión: 401 en JSON, sin redirección) y, para la usuaria
    común, con consentimiento vigente. Nunca se guarda en la caché del navegador ni del
    Service Worker. `expira` es el fin de la sesión: después, el cliente deja de usarla.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'codigo': 'sin_sesion'}, status=401)
    clave = clave_local(request.user)
    if clave is None:
        return JsonResponse({'ok': False, 'codigo': 'consentimiento_requerido'}, status=403)
    return JsonResponse({'ok': True, 'cuenta': cuenta_local(request.user), 'clave': clave,
                         'participacion': participacion_de(request.user),
                         'expira': request.session.get_expiry_date().isoformat()})


@login_required
@require_GET
def ronda_actual(request):
    """Fase 29: lo ya guardado en la ronda en curso, para precargar la encuesta."""
    paciente_id = request.GET.get('paciente')
    if paciente_id:
        if not request.user.es_profesional:
            return JsonResponse({'error': 'Solo el personal de salud puede ver otra paciente.'}, status=403)
        ident = Identificacion.objects.filter(pk=paciente_id).first()
        if ident is None:
            return JsonResponse({'error': 'La paciente no existe.'}, status=404)
        if ficha_sin_consentimiento(ident):   # Fase 40 (P7)
            return JsonResponse({'ok': False, 'codigo': 'consentimiento_paciente',
                                 'error': MENSAJE_SIN_CONSENTIMIENTO_PACIENTE}, status=403)
    else:
        if request.user.es_profesional:
            return JsonResponse({'error': "Indica la paciente con '?paciente=<id>'."}, status=400)
        ident = identificacion_de_usuaria(request.user)
        if ident is None:
            return JsonResponse({'paciente_id': None, 'ronda_actual': 1, 'disponible_desde': None,
                                 'bloqueada': False, 'identificacion': None, 'secciones': {}})
    estado = estado_ronda(ident)
    if request.user.es_profesional:
        estado['bloqueada'] = False  # Fase 31: sin plazo para el personal de salud
    return JsonResponse(estado)


@login_required
@require_POST
@requiere_consentimiento_api
def sincronizar(request):
    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'El cuerpo no es JSON válido.'}, status=400)

    try:
        resultado = sincronizar_payload(request.user, payload)
    except ConflictoRonda as exc:
        # Fase 40B-2: la solicitud no es para la ronda abierta; no se escribió ninguna respuesta.
        return JsonResponse(exc.como_json(), status=409)
    except ErrorSincronizacion as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)

    # 200 siempre que el payload sea procesable; el detalle por sección va en el cuerpo.
    return JsonResponse(resultado, status=200)


@login_required
@require_GET
def estado_sincronizacion(request):
    """Resumen de lo que la usuaria ya tiene guardado, para que el cliente sepa qué falta."""
    if request.user.es_profesional:
        return JsonResponse(
            {'error': 'El estado por usuario solo aplica a la usuaria común.'}, status=400
        )

    ident = Identificacion.objects.filter(usuario=request.user).first()
    if ident is None:
        return JsonResponse({'identificacion': False, 'secciones': {}, 'ronda_actual': 1})

    conteos = {
        tipo: modelo.objects.filter(participante=ident, ronda=ident.ronda_actual).count()
        for tipo, (modelo, _form) in SECCIONES.items()
    }
    return JsonResponse({
        'identificacion': True,
        'secciones': conteos,
        'ronda_actual': ident.ronda_actual,
    })
