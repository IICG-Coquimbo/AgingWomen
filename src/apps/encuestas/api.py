"""
Endpoints HTTP de sincronización offline-first (Sección 5.1 del spec).

- POST /api/sincronizar/  -> recibe el payload acumulado en el dispositivo.
- GET  /api/estado/       -> qué secciones ya tiene registradas la usuaria.

Requieren sesión iniciada (regla 1.1). El CSRF sigue activo: el cliente debe
enviar el header `X-CSRFToken` con el valor de la cookie `csrftoken`.
"""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .esquema import construir_esquema
from .models import Identificacion
from .sync import SECCIONES, ErrorSincronizacion, sincronizar_payload
from apps.usuarios.permissions import paciente_o_medico, solo_paciente


@paciente_o_medico
@require_GET
def esquema(request):
    """Estructura completa de la encuesta para que el cliente la renderice offline."""
    return JsonResponse(construir_esquema(request.user.rol))


@paciente_o_medico
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


@paciente_o_medico
@require_POST
def retirar(request):
    """Anula la participación y elimina los datos no finalizados del estudio."""
    ident = Identificacion.objects.filter(usuario=request.user).first()
    if ident is None and request.user.es_profesional:
        try:
            payload = json.loads(request.body or b'{}')
        except json.JSONDecodeError:
            payload = {}
        uuid_local = payload.get('uuid_local') if isinstance(payload, dict) else None
        if uuid_local:
            ident = Identificacion.objects.filter(uuid_local=uuid_local).first()
    if ident is not None:
        ident.delete()
    return JsonResponse({'ok': True})


@solo_paciente
@require_GET
def estado_sincronizacion(request):
    """Resumen de lo que la usuaria ya tiene guardado, para que el cliente sepa qué falta."""
    if request.user.es_profesional:
        return JsonResponse(
            {'error': 'El estado por usuario solo aplica a la usuaria común.'}, status=400
        )

    ident = Identificacion.objects.filter(usuario=request.user).first()
    if ident is None:
        return JsonResponse({'identificacion': False, 'secciones': {}})

    conteos = {
        tipo: modelo.objects.filter(participante=ident).count()
        for tipo, (modelo, _form) in SECCIONES.items()
    }
    return JsonResponse({'identificacion': True, 'secciones': conteos})
