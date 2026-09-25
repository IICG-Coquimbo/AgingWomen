from functools import wraps

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from .models import Usuario


def solo_paciente(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.rol != Usuario.Rol.USUARIA_COMUN:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def solo_medico(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.rol != Usuario.Rol.PROFESIONAL_SALUD:
            raise PermissionDenied
        perfil = getattr(request.user, 'perfil_medico', None)
        if perfil is not None and not perfil.aprobado and not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def paciente_o_medico(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.rol not in (
            Usuario.Rol.USUARIA_COMUN, Usuario.Rol.PROFESIONAL_SALUD,
        ):
            raise PermissionDenied
        if request.user.es_profesional:
            perfil = getattr(request.user, 'perfil_medico', None)
            if perfil is not None and not perfil.aprobado and not request.user.is_superuser:
                raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def solo_admin_tecnico(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped
