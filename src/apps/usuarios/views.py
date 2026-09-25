from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import check_password, make_password
from datetime import timedelta
import secrets
from django.views.generic import TemplateView

from .forms import RegistroForm
from .models import PerfilMedico, PerfilUsuaria, RegistroOTP, Usuario
from .rut import hash_rut, validar_rut
from apps.encuestas.models import Identificacion, MRS, SegmentoEMPA
from .permissions import solo_medico


def enviar_password_email(usuario, password):
    """Envía las credenciales mediante el backend de correo configurado."""
    tipo_perfil = (
        'Usuaria (Participante del estudio)'
        if usuario.es_usuaria_comun else 'Personal Médico'
    )
    send_mail(
        subject='Bienvenida al Observatorio Integral de la Mujer',
        message=(
            'Estimada/o participante:\n\n'
            'Tu registro en el Observatorio Integral de la Mujer en peri y menopausia '
            'se completó correctamente.\n\n'
            f'Tipo de perfil: {tipo_perfil}\n'
            f'Correo registrado: {usuario.email}\n'
            f'Contraseña de acceso: {password}\n\n'
            'Puedes ingresar con tu RUT y esta contraseña. Por seguridad, no compartas '
            'estas credenciales.'
        ),
        from_email=None,  # usa DEFAULT_FROM_EMAIL
        recipient_list=[usuario.email],
        fail_silently=False,
    )


def registro(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            otp_id = request.session.get('registro_otp_id')
            otp = RegistroOTP.objects.filter(
                id=otp_id,
                email=datos['email'],
                rut_hash=hash_rut(datos['rut']),
                tipo_cuenta=Usuario.Rol.USUARIA_COMUN,
                validado_en__isnull=False,
            ).first()
            if otp is None:
                form.add_error('codigo_verificacion', 'Primero debes validar el código enviado a tu correo.')
                return render(request, 'usuarios/registro.html', {'form': form})
            with transaction.atomic():
                usuario = Usuario.objects.create_user(
                    rut=datos['rut'],
                    email=datos['email'],
                    password=datos['password'],
                    rol=Usuario.Rol.USUARIA_COMUN,
                )
                PerfilUsuaria.objects.create(
                    usuario=usuario,
                )
            enviar_password_email(usuario, datos['password'])
            request.session.pop('registro_otp_id', None)
            return redirect('registro_enviado')
    else:
        form = RegistroForm()

    return render(request, 'usuarios/registro.html', {'form': form})


@require_POST
def enviar_codigo(request):
    """Genera y envía un OTP de seis dígitos sin crear todavía la cuenta."""
    rut = (request.POST.get('rut') or '').strip()
    email = (request.POST.get('email') or '').strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'ok': False, 'error': 'Ingresa un correo electrónico válido.'}, status=400)
    if not rut or not validar_rut(rut):
        return JsonResponse({'ok': False, 'error': 'El RUT no es válido. Usa, por ejemplo, 12345678-9.'}, status=400)
    if Usuario.objects.filter(rut_hash=hash_rut(rut)).exists():
        return JsonResponse({'ok': False, 'error': 'Ya existe una cuenta con ese RUT.'}, status=400)
    if Usuario.objects.filter(email__iexact=email).exists():
        return JsonResponse({'ok': False, 'error': 'Ya existe una cuenta con ese correo.'}, status=400)
    codigo = f'{secrets.randbelow(1000000):06d}'
    otp = RegistroOTP.objects.create(
        email=email,
        rut_hash=hash_rut(rut),
        tipo_cuenta=Usuario.Rol.USUARIA_COMUN,
        codigo_hash=make_password(codigo),
        expira_en=timezone.now() + timedelta(minutes=10),
    )
    request.session['registro_otp_id'] = otp.id
    send_mail(
        'Código de verificación de registro',
        f'Tu código de verificación para el Observatorio Integral de la Mujer es: {codigo}\n\nVence en 10 minutos.',
        None,
        [email],
        fail_silently=False,
    )
    return JsonResponse({'ok': True, 'message': 'Código enviado. Revisa tu correo.'})


@require_POST
def validar_codigo(request):
    otp = RegistroOTP.objects.filter(
        id=request.session.get('registro_otp_id'), validado_en__isnull=True,
    ).first()
    codigo = (request.POST.get('codigo') or '').strip()
    if otp is None or not otp.esta_vigente():
        return JsonResponse({'ok': False, 'error': 'El código expiró. Solicita uno nuevo.'}, status=400)
    otp.intentos += 1
    if otp.intentos > 5 or not check_password(codigo, otp.codigo_hash):
        otp.save(update_fields=['intentos'])
        return JsonResponse({'ok': False, 'error': 'El código no es válido.'}, status=400)
    otp.validado_en = timezone.now()
    otp.save(update_fields=['intentos', 'validado_en'])
    return JsonResponse({'ok': True, 'message': 'Correo verificado correctamente.'})


class RegistroEnviadoView(TemplateView):
    template_name = 'usuarios/registro_enviado.html'


@login_required
def home(request):
    if request.user.es_admin_tecnico:
        return redirect('/admin/')
    if request.user.es_profesional:
        return redirect('panel_medico')
    return render(request, 'home.html')


@solo_medico
def panel_medico(request):
    return render(request, 'usuarios/panel_medico.html')


@solo_medico
def buscar_paciente(request):
    rut = (request.GET.get('rut') or '').strip()
    participante = Identificacion.objects.filter(rut_hash=hash_rut(rut)).first()
    if participante is None:
        return render(request, 'usuarios/paciente_ficha.html', {
            'participante': None, 'historial_total': 0,
        })
    historial_total = sum(modelo.objects.filter(participante=participante).count()
                          for modelo in (MRS, SegmentoEMPA))
    return render(request, 'usuarios/paciente_ficha.html', {
        'participante': participante, 'historial_total': historial_total,
    })


@solo_medico
def estadisticas_medico(request):
    participantes = Identificacion.objects.all()
    presion_alta = SegmentoEMPA.objects.filter(presion_sistolica__gte=140).count()
    edades = [participante.edad for participante in participantes]
    return render(request, 'usuarios/estadisticas_medico.html', {
        'total_participantes': participantes.count(),
        'edad_promedio': round(sum(edades) / len(edades), 1) if edades else None,
        'presion_alta': presion_alta,
        'total_mrs': MRS.objects.count(),
    })
