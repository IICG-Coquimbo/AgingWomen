from django.urls import path

from . import api, profesional, retiro, tablero, views

urlpatterns = [
    path('encuesta/', views.encuesta, name='encuesta'),
    path('api/esquema/', api.esquema, name='esquema'),
    path('api/sincronizar/', api.sincronizar, name='sincronizar'),
    path('api/estado/', api.estado_sincronizacion, name='estado_sincronizacion'),
    path('api/ronda-actual/', api.ronda_actual, name='ronda_actual'),
    path('profesional/buscar/', profesional.buscar_paciente, name='buscar_paciente'),
    path('profesional/paciente/<int:identificacion_id>/', profesional.ficha_paciente, name='ficha_paciente'),
    path('profesional/paciente/<int:identificacion_id>/encuesta/', profesional.encuesta_paciente,
         name='encuesta_paciente'),
    path('profesional/paciente/nueva/', profesional.nueva_paciente, name='nueva_paciente'),
    path('profesional/estadisticas/', profesional.estadisticas, name='estadisticas'),
    path('mi-tablero/', tablero.mi_tablero, name='mi_tablero'),
    path('mi-evaluacion/', tablero.mi_evaluacion, name='mi_evaluacion'),
    path('retirarse/', retiro.retirarse, name='retirarse'),
]
