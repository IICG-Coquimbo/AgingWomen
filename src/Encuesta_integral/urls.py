"""
URL configuration for Encuesta_integral project.
"""
from django.contrib import admin
from django.urls import include, path

from apps.encuestas.views import service_worker
from apps.usuarios.views import home

admin.site.site_header = 'Observatorio Integral de la Mujer en peri y menopausia'
admin.site.site_title = 'Observatorio Mujer'
admin.site.index_title = 'Administración de cuentas'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', service_worker, name='service_worker'),
    path('cuenta/', include('apps.usuarios.urls')),
    path('', include('apps.encuestas.urls')),
    path('', home, name='home'),
]
