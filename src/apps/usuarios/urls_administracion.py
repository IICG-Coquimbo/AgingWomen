from django.urls import path

from . import administracion

# Fase 30: administración de cuentas dentro del sistema (solo superusuario).
urlpatterns = [
    path('', administracion.panel, name='admin_panel'),
    path('crear-profesional/', administracion.crear_profesional, name='admin_crear_profesional'),
    path('cuenta/<int:cuenta_id>/', administracion.cuenta, name='admin_cuenta'),
    path('cuenta/<int:cuenta_id>/rol/', administracion.cambiar_rol, name='admin_cambiar_rol'),
    path('cuenta/<int:cuenta_id>/eliminar/', administracion.eliminar, name='admin_eliminar'),
]
