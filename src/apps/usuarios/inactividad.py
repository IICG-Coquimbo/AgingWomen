"""
Fase 40, Etapa 2: cierre de sesión por inactividad, aplicado en el SERVIDOR.

- `SESION_INACTIVIDAD_SEGUNDOS` (30 min por defecto, configurable por entorno):
  si desde la última actividad pasó más que eso, la sesión se cierra en el servidor
  antes de atender la solicitud. La API responde 401 `sesion_vencida` en JSON; las
  páginas redirigen al ingreso con `?inactividad=1`.
- Solo cuenta como actividad lo que hace la persona: cargar una página, enviar un
  formulario o el aviso de actividad que manda sesion.js cuando hay interacción real.
  Las solicitudes automáticas de la encuesta llevan `X-Segundo-Plano: 1` y no
  extienden la sesión.
- La marca se guarda en la sesión como mucho una vez por `REESCRITURA` segundos
  para no escribir en cada solicitud; el margen queda del lado seguro (la sesión
  puede vencer hasta REESCRITURA segundos antes, nunca después).
"""
import time

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

CLAVE = 'aw_ultima_actividad'
REESCRITURA = 30


def limite():
    return int(getattr(settings, 'SESION_INACTIVIDAD_SEGUNDOS', 1800))


def es_segundo_plano(request):
    return request.headers.get('X-Segundo-Plano') == '1'


@receiver(user_logged_in)
def _al_ingresar(sender, request, user, **kwargs):
    if request is not None and hasattr(request, 'session'):
        request.session[CLAVE] = int(time.time())


class InactividadMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, 'user', None)
        if usuario is not None and usuario.is_authenticated:
            ahora = int(time.time())
            ultima = request.session.get(CLAVE)
            if ultima is not None and ahora - int(ultima) > limite():
                logout(request)
                if request.path.startswith('/api/') or request.path == reverse('actividad'):
                    return JsonResponse({'ok': False, 'codigo': 'sesion_vencida',
                                         'error': 'La sesión se cerró por inactividad.'}, status=401)
                return redirect(reverse('login') + '?inactividad=1')
            renovar = not es_segundo_plano(request) and (
                ahora - int(ultima or 0) >= REESCRITURA or request.path == reverse('actividad'))
            if ultima is None or renovar:
                request.session[CLAVE] = ahora
        return self.get_response(request)


@require_POST
def actividad(request):
    """Aviso de actividad real (sesion.js). El middleware ya renovó la marca; aquí solo se confirma."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'codigo': 'sesion_vencida'}, status=401)
    return HttpResponse(status=204)


def contexto(request):
    """Context processor: límites para sesion.js (atributos de <body>)."""
    usuario = getattr(request, 'user', None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    return {'sesion_inactividad': limite(), 'sesion_aviso': int(getattr(settings, 'SESION_AVISO_SEGUNDOS', 120))}
