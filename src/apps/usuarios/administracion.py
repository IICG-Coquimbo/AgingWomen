"""
Administración de cuentas dentro del sistema (Fase 30), solo para el
superusuario: buscar cuentas por RUT, listarlas, cambiar el rol entre usuaria
común y personal de salud, eliminarlas y crear cuentas de personal de salud.
Reemplaza el uso del admin de Django, que queda solo como respaldo técnico.

Eliminar una cuenta borra también todas sus respuestas de encuesta (todas las
rondas y su evaluación), igual que "Retirarse del estudio" (Fase 23).
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RegistroUsuariaForm
from .models import Usuario
from .rut import hash_rut, validar_rut
from .views import enviar_activacion_email

CUENTAS_POR_PAGINA = 25


def requiere_superusuario(view_func):
    """Restringe la vista al superusuario. Va por dentro de @login_required."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('Esta sección es solo para la administración del sistema.')
        return view_func(request, *args, **kwargs)
    return wrapper


def _identificaciones_de(cuenta):
    # Import local: la app encuestas ya depende de usuarios.
    from apps.encuestas.models import Identificacion
    return Identificacion.objects.filter(Q(usuario=cuenta) | Q(rut_hash=cuenta.rut_hash))


def _protegida(request, cuenta):
    """La propia cuenta y las de otros superusuarios no se modifican desde aquí."""
    return cuenta.pk == request.user.pk or cuenta.is_superuser


@login_required
@requiere_superusuario
def panel(request):
    # Fase 40 (R-2): el RUT solo por POST con CSRF; la cuenta encontrada se abre por su id.
    rut = request.POST.get('rut', '').strip() if request.method == 'POST' else ''
    rol = request.GET.get('rol', '')
    error = None

    if rut:
        if not validar_rut(rut):
            error = 'El RUT ingresado no es válido.'
        else:
            cuenta = Usuario.objects.filter(rut_hash=hash_rut(rut)).first()
            if cuenta:
                return redirect('admin_cuenta', cuenta_id=cuenta.pk)
            error = 'No hay ninguna cuenta con ese RUT.'

    cuentas = Usuario.objects.order_by('-date_joined')
    if rol in Usuario.Rol.values:
        cuentas = cuentas.filter(rol=rol)
    pagina = Paginator(cuentas, CUENTAS_POR_PAGINA).get_page(request.GET.get('pagina'))

    return render(request, 'usuarios/admin_panel.html', {
        'rut': rut, 'rol': rol, 'error': error, 'pagina': pagina,
        'roles': Usuario.Rol.choices,
    })


@login_required
@requiere_superusuario
def cuenta(request, cuenta_id):
    cuenta = get_object_or_404(Usuario, pk=cuenta_id)
    identificacion = _identificaciones_de(cuenta).first()
    return render(request, 'usuarios/admin_cuenta.html', {
        'cuenta': cuenta,
        'identificacion': identificacion,
        'rondas_finalizadas': identificacion.ronda_actual - 1 if identificacion else 0,
        'protegida': _protegida(request, cuenta),
    })


@login_required
@requiere_superusuario
@require_POST
def cambiar_rol(request, cuenta_id):
    cuenta = get_object_or_404(Usuario, pk=cuenta_id)
    if _protegida(request, cuenta):
        messages.error(request, 'No se puede cambiar el rol de esta cuenta.')
        return redirect('admin_cuenta', cuenta_id=cuenta.pk)

    nuevo = request.POST.get('rol')
    if nuevo not in Usuario.Rol.values:
        messages.error(request, 'Rol no válido.')
    else:
        cuenta.rol = nuevo
        cuenta.save(update_fields=['rol'])
        messages.success(request, f'Rol actualizado a «{cuenta.get_rol_display()}».')
    return redirect('admin_cuenta', cuenta_id=cuenta.pk)


@login_required
@requiere_superusuario
def eliminar(request, cuenta_id):
    cuenta = get_object_or_404(Usuario, pk=cuenta_id)
    if _protegida(request, cuenta):
        messages.error(request, 'Esta cuenta no se puede eliminar.')
        return redirect('admin_cuenta', cuenta_id=cuenta.pk)

    error = None
    if request.method == 'POST':
        if request.POST.get('entiendo') == 'on':
            correo = cuenta.email
            with transaction.atomic():
                _identificaciones_de(cuenta).delete()  # en cascada: rondas y evaluación
                cuenta.delete()
            messages.success(request, f'Se eliminó la cuenta {correo} y todos sus datos.')
            return redirect('admin_panel')
        error = 'Marca la casilla para confirmar que entiendes lo que se eliminará.'

    return render(request, 'usuarios/admin_eliminar.html', {
        'cuenta': cuenta,
        'tiene_datos': _identificaciones_de(cuenta).exists(),
        'error': error,
    })


@login_required
@requiere_superusuario
def crear_profesional(request):
    if request.method == 'POST':
        form = RegistroUsuariaForm(request.POST)
        if form.is_valid():
            nueva = Usuario.objects.create_user(
                rut=form.cleaned_data['rut'],
                email=form.cleaned_data['email'],
                rol=Usuario.Rol.PROFESIONAL_SALUD,
            )
            enviar_activacion_email(request, nueva)
            messages.success(
                request,
                f'Cuenta de personal de salud creada. Enlace de activación enviado a {nueva.email}.',
            )
            return redirect('admin_cuenta', cuenta_id=nueva.pk)
    else:
        form = RegistroUsuariaForm()
    return render(request, 'usuarios/admin_crear_profesional.html', {'form': form})
