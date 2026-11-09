from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from . import limite_ingreso
from .forms import RegistroConClaveForm, VerificarCodigoForm
from .models import RegistroOTP, Usuario
from .rut import hash_rut

SESION_REGISTRO = 'registro_otp_id'


def enviar_activacion_email(request, usuario):
    """Enlace de un solo uso y con vencimiento para definir la contraseña; nunca envía una contraseña."""
    enlace = request.build_absolute_uri(reverse('password_reset_confirm', kwargs={
        'uidb64': urlsafe_base64_encode(force_bytes(usuario.pk)),
        'token': default_token_generator.make_token(usuario),
    }))
    horas = settings.PASSWORD_RESET_TIMEOUT // 3600
    send_mail(
        subject='Activa tu cuenta de profesional - Observatorio Integral de la Mujer',
        message=(
            'Se ha creado tu cuenta en el Observatorio Integral de la Mujer '
            'en peri y menopausia.\n\n'
            'Abre este enlace para crear tu contraseña:\n\n'
            f'    {enlace}\n\n'
            f'El enlace sirve una sola vez y vence en {horas} horas. Si venció, solicita '
            'otro con «Olvidé mi contraseña», usando este mismo correo.\n\n'
            'Después podrás ingresar con tu RUT y la contraseña que elijas.'
        ),
        from_email=None,  # usa DEFAULT_FROM_EMAIL
        recipient_list=[usuario.email],
        fail_silently=False,
    )


def enviar_codigo_email(email, codigo):
    send_mail(
        subject='Código de verificación - Observatorio Integral de la Mujer',
        message=(
            'Tu código para verificar tu correo es:\n\n'
            f'    {codigo}\n\n'
            f'Vence en {int(RegistroOTP.VIGENCIA.total_seconds() // 60)} minutos. '
            'Si no solicitaste crear una cuenta, ignora este mensaje.'
        ),
        from_email=None,
        recipient_list=[email],
        fail_silently=False,
    )


def enviar_bienvenida_email(usuario):
    """Confirma el registro. No incluye la contraseña: la eligió la usuaria."""
    send_mail(
        subject='Tu cuenta fue creada - Observatorio Integral de la Mujer',
        message=(
            'Tu registro en el Observatorio Integral de la Mujer en peri y '
            'menopausia se completó correctamente.\n\n'
            'Ingresa con tu RUT y la contraseña que elegiste. Si la olvidas, '
            'puedes recuperarla desde la pantalla de ingreso.'
        ),
        from_email=None,
        recipient_list=[usuario.email],
        fail_silently=False,
    )


def registro(request):
    """Paso 1: RUT, correo y contraseña. Envía el código; aún no crea la cuenta."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistroConClaveForm(request.POST)
        if form.is_valid() and not limite_ingreso.permitir_registro(request):
            form.add_error(None, limite_ingreso.MENSAJE_REGISTRO)
        if form.is_valid():
            datos = form.cleaned_data
            rut_hash = hash_rut(datos['rut'])
            # Un solo registro pendiente por RUT/correo: los anteriores se descartan.
            RegistroOTP.objects.filter(rut_hash=rut_hash).delete()
            RegistroOTP.objects.filter(email__iexact=datos['email']).delete()
            otp = RegistroOTP(
                rut_hash=rut_hash,
                email=datos['email'],
                password_hash=make_password(datos['password1']),
            )
            codigo = otp.nuevo_codigo()
            otp.save()
            enviar_codigo_email(otp.email, codigo)
            request.session[SESION_REGISTRO] = otp.pk
            return redirect('registro_verificar')
    else:
        form = RegistroConClaveForm()

    return render(request, 'usuarios/registro.html', {'form': form})


def _otp_de_la_sesion(request):
    pk = request.session.get(SESION_REGISTRO)
    return RegistroOTP.objects.filter(pk=pk).first() if pk else None


def verificar_registro(request):
    """Paso 2: con el código correcto se crea la cuenta y se inicia sesión."""
    if request.user.is_authenticated:
        return redirect('home')
    otp = _otp_de_la_sesion(request)
    if otp is None:
        return redirect('registro')

    error = None
    form = VerificarCodigoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if otp.vencido:
            error = 'El código venció. Solicita uno nuevo.'
        elif otp.agotado:
            error = 'Superaste el número de intentos. Solicita un código nuevo.'
        elif not otp.codigo_correcto(form.cleaned_data['codigo']):
            otp.intentos += 1
            otp.save(update_fields=['intentos'])
            restantes = RegistroOTP.MAX_INTENTOS - otp.intentos
            error = (f'El código no es correcto. Te quedan {restantes} intento(s).'
                     if restantes else
                     'Superaste el número de intentos. Solicita un código nuevo.')
        elif (Usuario.objects.filter(rut_hash=otp.rut_hash).exists()
              or Usuario.objects.filter(email__iexact=otp.email).exists()):
            # Alguien registró ese RUT o correo mientras este código estaba pendiente.
            otp.delete()
            del request.session[SESION_REGISTRO]
            return render(request, 'usuarios/registro.html', {
                'form': RegistroConClaveForm(),
                'aviso': 'Ese RUT o correo ya tiene una cuenta. Ingresa o recupera tu contraseña.',
            })
        else:
            with transaction.atomic():
                usuario = Usuario(
                    rut_hash=otp.rut_hash,
                    email=Usuario.objects.normalize_email(otp.email),
                    rol=Usuario.Rol.USUARIA_COMUN,
                    password=otp.password_hash,
                )
                usuario.save()
                # Fase 29: si el personal de salud ya la había registrado como
                # paciente con este RUT, esa ficha pasa a ser suya.
                from apps.encuestas.models import Identificacion
                Identificacion.objects.filter(
                    rut_hash=usuario.rut_hash, usuario__isnull=True,
                ).update(usuario=usuario)
                otp.delete()
            del request.session[SESION_REGISTRO]
            enviar_bienvenida_email(usuario)
            login(request, usuario, backend='apps.usuarios.backends.RutBackend')
            return redirect('encuesta')

    return render(request, 'usuarios/registro_verificar.html', {
        'form': form, 'error': error, 'email': otp.email,
        'puede_reenviar': otp.puede_reenviar,
    })


@require_POST
def reenviar_codigo(request):
    otp = _otp_de_la_sesion(request)
    if otp is None:
        return redirect('registro')
    if otp.puede_reenviar:
        codigo = otp.nuevo_codigo()
        otp.save(update_fields=['codigo_hash', 'intentos', 'enviado_en'])
        enviar_codigo_email(otp.email, codigo)
    return redirect('registro_verificar')


def _destino_seguro(request, next_url):
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return 'home'


DECISIONES_RECHAZO = ('no_acepto', 'desisto')


@login_required
def consentimiento(request):
    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.user.consentimiento_aceptado_en:
        return redirect(_destino_seguro(request, next_url))

    error = None
    decision = request.POST.get('decision', '')
    leido = request.POST.get('leido') == 'on'
    if request.method == 'POST':
        if decision in DECISIONES_RECHAZO:
            # No se guarda nada: si vuelve más tarde, ve el consentimiento de
            # nuevo y puede aceptar.
            return render(request, 'usuarios/consentimiento_rechazado.html', {
                'desiste': decision == 'desisto',
            })
        if decision == 'acepto':
            if leido:
                request.user.consentimiento_aceptado_en = timezone.now()
                request.user.save(update_fields=['consentimiento_aceptado_en'])
                return redirect(_destino_seguro(request, next_url))
            error = 'Debes indicar que leíste y comprendiste la información del estudio.'
        else:
            error = 'Selecciona una opción para continuar.'

    return render(request, 'usuarios/consentimiento.html', {
        'error': error, 'next': next_url, 'decision': decision, 'leido': leido,
    })


@login_required
def home(request):
    contexto = {}
    if not request.user.es_profesional:
        # Fase 31: la tarjeta de la encuesta se deshabilita durante el plazo entre rondas.
        from apps.encuestas.plazo import encuesta_bloqueada, mensaje_espera
        from apps.encuestas.sync import identificacion_de_usuaria
        propia = identificacion_de_usuaria(request.user)
        if encuesta_bloqueada(propia):
            contexto['espera_encuesta'] = mensaje_espera(propia)
    return render(request, 'home.html', contexto)
