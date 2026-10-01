"""
Endpoints HTTP de sincronización offline-first (Sección 5.1 del spec).

- POST /api/sincronizar/  -> recibe el payload acumulado en el dispositivo.
- GET  /api/estado/       -> qué secciones ya tiene registradas la usuaria.
- GET  /api/ronda-actual/ -> respuestas de la ronda en curso (propias, o de una
                             paciente con ?paciente=<id> si es personal de salud).

Requieren sesión iniciada (regla 1.1). El CSRF sigue activo: el cliente debe
enviar el header `X-CSRFToken` con el valor de la cookie `csrftoken`.
"""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .esquema import construir_esquema
from .models import Identificacion
from .sync import (
    SECCIONES, ErrorSincronizacion, estado_ronda, identificacion_de_usuaria, sincronizar_payload,
)


@login_required
@require_GET
def esquema(request):
    """Estructura completa de la encuesta para que el cliente la renderice offline."""
    return JsonResponse(construir_esquema(request.user.rol))


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
    else:
        if request.user.es_profesional:
            return JsonResponse({'error': "Indica la paciente con '?paciente=<id>'."}, status=400)
        ident = identificacion_de_usuaria(request.user)
        if ident is None:
            return JsonResponse({'paciente_id': None, 'ronda_actual': 1,
                                 'identificacion': None, 'secciones': {}})
    return JsonResponse(estado_ronda(ident))


@login_required
@require_POST
def sincronizar(request):
    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'El cuerpo no es JSON válido.'}, status=400)

    try:
        resultado = sincronizar_payload(request.user, payload)
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
