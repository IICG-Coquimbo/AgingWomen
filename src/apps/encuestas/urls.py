from django.urls import path

from . import api, profesional, views

urlpatterns = [
    path('encuesta/', views.encuesta, name='encuesta'),
    path('api/esquema/', api.esquema, name='esquema'),
    path('api/sincronizar/', api.sincronizar, name='sincronizar'),
    path('api/estado/', api.estado_sincronizacion, name='estado_sincronizacion'),
    path('profesional/buscar/', profesional.buscar_paciente, name='buscar_paciente'),
    path('profesional/paciente/<int:identificacion_id>/', profesional.ficha_paciente, name='ficha_paciente'),
]
