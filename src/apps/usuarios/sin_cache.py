"""
El navegador no debe guardar ninguna página de una sesión iniciada: tablero, fichas,
resultados MRS, estadísticas y API. Así «Atrás» después de «Salir» vuelve a pedir la
página al servidor, que redirige al ingreso.

Va como middleware para que una vista nueva no quede sin protección. No afecta a la
encuesta sin conexión: su copia la guarda el Service Worker en CacheStorage, y sesion.js
la borra al salir. Los estáticos y /sw.js no llevan datos personales y quedan fuera.
"""
from django.conf import settings


class SinCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        usuario = getattr(request, 'user', None)
        if (usuario is not None and usuario.is_authenticated
                and not request.path.startswith(settings.STATIC_URL) and request.path != '/sw.js'
                and 'no-store' not in response.get('Cache-Control', '')):
            response['Cache-Control'] = 'no-store, private'
        return response
