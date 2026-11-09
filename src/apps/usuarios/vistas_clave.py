"""Recuperación de contraseña con límite de solicitudes y desbloqueo del ingreso al completarla."""
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect

from . import limite_ingreso


class RecuperarClaveView(auth_views.PasswordResetView):
    def form_valid(self, form):
        if not limite_ingreso.permitir_recuperacion(self.request, form.cleaned_data.get('email')):
            # Misma respuesta que siempre: no se envía otro correo, pero no se revela nada.
            return HttpResponseRedirect(self.get_success_url())
        return super().form_valid(form)


class ConfirmarClaveView(auth_views.PasswordResetConfirmView):
    def form_valid(self, form):
        respuesta = super().form_valid(form)
        limite_ingreso.reiniciar_cuenta(self.user)
        return respuesta
