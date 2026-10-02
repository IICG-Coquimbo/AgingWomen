from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import redirect, render

from apps.usuarios.decorators import requiere_consentimiento

from .plazo import encuesta_bloqueada, mensaje_espera
from .sync import identificacion_de_usuaria


@requiere_consentimiento
def _encuesta_propia(request):
    return render(request, 'encuesta.html')


@login_required
def encuesta(request):
    """Shell de la app cliente de la encuesta. El contenido lo arma encuesta.js."""
    if request.user.es_profesional:
        # Fase 29: el personal de salud responde siempre por una paciente.
        return redirect('buscar_paciente')
    propia = identificacion_de_usuaria(request.user)
    if encuesta_bloqueada(propia):
        messages.info(request, mensaje_espera(propia))
        return redirect('home')
    return _encuesta_propia(request)


def service_worker(request):
    """
    Sirve sw.js desde la raíz del sitio para que su alcance sea todo el dominio
    (un service worker solo controla rutas bajo su propia URL).
    """
    ruta = settings.BASE_DIR / 'static' / 'js' / 'sw.js'
    return FileResponse(ruta.open('rb'), content_type='application/javascript')
