from functools import wraps
from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


def requiere_consentimiento(view_func):
    """
    Exige que el usuario haya aceptado el consentimiento informado antes de
    entrar a la vista. Se usa junto a @login_required (debe ir por dentro,
    ya que asume que request.user está autenticado).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.consentimiento_aceptado_en:
            destino = reverse('consentimiento') + '?' + urlencode({'next': request.get_full_path()})
            return redirect(destino)
        return view_func(request, *args, **kwargs)
    return wrapper
