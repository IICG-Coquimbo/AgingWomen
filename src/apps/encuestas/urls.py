from django.urls import path

from . import api, views

urlpatterns = [
    path('encuesta/', views.encuesta, name='encuesta'),
    path('api/esquema/', api.esquema, name='esquema'),
    path('api/sincronizar/', api.sincronizar, name='sincronizar'),
    path('api/estado/', api.estado_sincronizacion, name='estado_sincronizacion'),
]
