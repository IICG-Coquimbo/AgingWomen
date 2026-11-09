from functools import wraps
from urllib.parse import urlencode

from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse


def requiere_consentimiento(view_func):
    """
    Exige que el usuario haya aceptado el consentimiento informado antes de
    entrar a la vista. Se usa junto a @login_required (debe ir por dentro,
    ya que asume que request.user está autenticado).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.consentimiento_aceptado_en:
            destino = reverse('consentimiento') + '?' + urlencode({'next': request.get_full_path()})
            return redirect(destino)
        return view_func(request, *args, **kwargs)
    return wrapper


def requiere_consentimiento_api(view_func):
    """
    Versión para la API (Fase 40S-1, H-11): una usuaria común sin
    consentimiento vigente recibe 403 en JSON en vez de una redirección, así
    no puede guardar respuestas con peticiones directas. Incluye a quien se
    retiró del estudio (el retiro borra el consentimiento).

    El personal de salud queda fuera de esta regla, igual que en /encuesta/:
    no participa del estudio y responde siempre por una paciente.

    Se usa junto a @login_required (debe ir por dentro).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.es_profesional and not request.user.consentimiento_aceptado_en:
            return JsonResponse({
                'ok': False,
                'codigo': 'consentimiento_requerido',
                'error': 'Debes aceptar el consentimiento informado antes de enviar respuestas.',
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def requiere_profesional(view_func):
    """
    Restringe la vista al personal de salud (rol PROFESIONAL). Se usa junto a
    @login_required (debe ir por dentro, ya que asume que request.user está
    autenticado).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.es_profesional:
            return HttpResponseForbidden('Esta sección es solo para personal de salud.')
        return view_func(request, *args, **kwargs)
    return wrapper
