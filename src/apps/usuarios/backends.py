from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .rut import hash_rut


class RutBackend(ModelBackend):
    """
    Autenticación con el RUT en claro: lo normaliza, lo hashea y busca la
    cuenta por `rut_hash`. Nunca se compara ni se almacena el RUT en claro.
    """

    def authenticate(self, request, rut=None, password=None, **kwargs):
        if rut is None:
            rut = kwargs.get('username')
        if rut is None or password is None:
            return None

        Usuario = get_user_model()
        try:
            usuario = Usuario.objects.get(rut_hash=hash_rut(rut))
        except Usuario.DoesNotExist:
            # Ejecuta el hasher de todos modos para no filtrar por tiempo de
            # respuesta si un RUT existe o no.
            Usuario().set_password(password)
            return None

        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
