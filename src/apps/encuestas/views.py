from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import render
from apps.usuarios.permissions import solo_paciente


@solo_paciente
def encuesta(request):
    """Shell de la app cliente de la encuesta. El contenido lo arma encuesta.js."""
    return render(request, 'encuesta.html')


def service_worker(request):
    """
    Sirve sw.js desde la raíz del sitio para que su alcance sea todo el dominio
    (un service worker solo controla rutas bajo su propia URL).
    """
    ruta = settings.BASE_DIR / 'static' / 'js' / 'sw.js'
    return FileResponse(ruta.open('rb'), content_type='application/javascript')
