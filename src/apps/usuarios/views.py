from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import TemplateView

from .forms import RegistroUsuariaForm
from .models import Usuario


def enviar_password_email(usuario, password):
    """Envía la contraseña autogenerada. En desarrollo sale por la consola."""
    send_mail(
        subject='Tu acceso a la plataforma de investigación de menopausia',
        message=(
            'Se ha creado tu cuenta en la plataforma.\n\n'
            'Ingresa con tu RUT y esta contraseña temporal:\n\n'
            f'    {password}\n\n'
            'Por seguridad, te recomendamos cambiarla después de ingresar.'
        ),
        from_email=None,  # usa DEFAULT_FROM_EMAIL
        recipient_list=[usuario.email],
        fail_silently=False,
    )


def registro(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistroUsuariaForm(request.POST)
        if form.is_valid():
            usuario = Usuario.objects.create_user(
                rut=form.cleaned_data['rut'],
                email=form.cleaned_data['email'],
                rol=Usuario.Rol.USUARIA_COMUN,
            )
            enviar_password_email(usuario, usuario.password_generada)
            return redirect('registro_enviado')
    else:
        form = RegistroUsuariaForm()

    return render(request, 'usuarios/registro.html', {'form': form})


class RegistroEnviadoView(TemplateView):
    template_name = 'usuarios/registro_enviado.html'


def _destino_seguro(request, next_url):
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return 'home'


@login_required
def consentimiento(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.user.consentimiento_aceptado_en:
        return redirect(_destino_seguro(request, next_url))

    error = None
    if request.method == 'POST':
        if request.POST.get('acepto') == 'on':
            request.user.consentimiento_aceptado_en = timezone.now()
            request.user.save(update_fields=['consentimiento_aceptado_en'])
            return redirect(_destino_seguro(request, next_url))
        error = 'Debes marcar la casilla de aceptación para continuar.'

    return render(request, 'usuarios/consentimiento.html', {'error': error, 'next': next_url})


@login_required
def home(request):
    return render(request, 'home.html')
