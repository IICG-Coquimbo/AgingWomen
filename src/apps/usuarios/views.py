from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
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


@login_required
def home(request):
    return render(request, 'home.html')
