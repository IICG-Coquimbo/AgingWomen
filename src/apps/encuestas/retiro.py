"""
Retiro del estudio (Fase 23). La participante puede retirarse cuando quiera:
se eliminan TODAS sus respuestas (Identificación y, en cascada, todas las
secciones de todas las rondas y su evaluación de satisfacción) y se reinicia
su consentimiento. La cuenta de acceso se conserva, por si cambia de opinión.

Fase 40, Etapa 2: también se elimina su consentimiento presencial, y la participante
recibe un comprobante firmado del retiro (apps.usuarios.constancia_retiro) que el
servidor no guarda.

Fase 40 (pendientes de consentimiento): retiro presencial de una mujer SIN cuenta,
registrado por una profesional (`retiro_presencial`). Mismo borrado y mismo
comprobante; la autorización se acredita con el documento de revocación firmado por
ella (folio y custodia), la declaración de la profesional y la contraseña de la propia
profesional (con límite de intentos). Los envíos antiguos no restauran nada: la ficha
desaparece y, si vuelve a consentir, su participación es otra (sync.py).
"""
import re

from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache

from apps.usuarios import constancia_retiro, intentos
from apps.usuarios.decorators import requiere_profesional
from apps.usuarios.models import ConsentimientoPresencial, Usuario
from apps.usuarios.rut import hash_rut, validar_rut

from .models import Identificacion


def borrar_participacion(rut_hash, usuario=None):
    """
    Único borrado del retiro: la ficha (y en cascada respuestas, rondas, resultados y
    eventos) y el consentimiento presencial. Con cuenta, también su consentimiento en línea.
    Incluye la ficha que una profesional registró con su RUT antes de que ella tuviera cuenta
    (sin dueña), para que ningún dato de salud quede atrás. Devuelve cuántas fichas borró.
    """
    with transaction.atomic():
        fichas = Identificacion.objects.filter(rut_hash=rut_hash, usuario__isnull=True)
        if usuario is not None:
            fichas = fichas | Identificacion.objects.filter(usuario=usuario)
        n = fichas.count()
        Identificacion.objects.filter(pk__in=list(fichas.values_list('pk', flat=True))).delete()
        ConsentimientoPresencial.objects.filter(rut_hash=rut_hash).delete()
        if usuario is not None:
            usuario.consentimiento_aceptado_en = None
            usuario.save(update_fields=['consentimiento_aceptado_en'])
    return n


@login_required
def retirarse(request):
    if request.user.es_profesional:
        return redirect('buscar_paciente')

    error = None
    if request.method == 'POST':
        if request.POST.get('entiendo') == 'on':
            borrar_participacion(request.user.rut_hash, usuario=request.user)
            datos, comprobante = constancia_retiro.emitir(request.user.rut_hash)
            response = render(request, 'encuestas/retirado.html', {'constancia': datos, 'comprobante': comprobante})
            response['Cache-Control'] = 'no-store'
            return response
        error = 'Marca la casilla para confirmar que entiendes lo que se eliminará.'

    return render(request, 'encuestas/retirarse.html', {'error': error})


FOLIO = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._/-]{2,39}$')


class RetiroPresencialForm(forms.Form):
    rut = forms.CharField(label='RUT de la participante', max_length=12,
                          widget=forms.TextInput(attrs={'autocomplete': 'off', 'data-rut': 'true',
                                                        'placeholder': '12.345.678-9'}))
    folio_revocacion = forms.CharField(
        label='Folio o código del documento de revocación firmado por la participante', max_length=40,
        help_text='El identificador escrito en el documento en papel (por ejemplo, RV-2026-0012).')
    custodia = forms.CharField(
        label='Dónde queda custodiado el documento de revocación', max_length=120, min_length=3,
        help_text='No escribas datos personales ni clínicos.')
    declaracion = forms.BooleanField(
        label='Declaro que la participante pidió retirarse del estudio y firmó el documento de revocación '
              'en mi presencia, de forma libre.')
    confirmo = forms.BooleanField(
        label='Entiendo que se eliminarán definitivamente su ficha, todas sus respuestas, rondas y resultados, '
              'y su consentimiento presencial. No se puede deshacer.')
    clave_profesional = forms.CharField(
        label='Tu contraseña (para confirmar que eres tú quien registra el retiro)',
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

    def clean_rut(self):
        rut = self.cleaned_data['rut'].strip()
        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')
        return rut

    def clean_folio_revocacion(self):
        folio = self.cleaned_data['folio_revocacion'].strip()
        if not FOLIO.match(folio):
            raise forms.ValidationError('Usa de 3 a 40 letras, números, guiones, puntos o barras.')
        return folio


@never_cache
@login_required
@requiere_profesional
def retiro_presencial(request):
    """El RUT llega solo por POST (nunca en la URL). Sin caché: la página no queda en el navegador."""
    form = RetiroPresencialForm(request.POST or None)
    estado = 200
    if request.method == 'POST':
        estado = 400
        # 1. La profesional confirma su identidad (límite de intentos) antes de revelar nada.
        error_clave = None
        if request.POST.get('clave_profesional'):
            error_clave = intentos.verificar_clave(request.user, request.POST['clave_profesional'], request.user)
        form.is_valid()
        if error_clave:
            form.add_error('clave_profesional', error_clave)
            if error_clave == intentos.MENSAJE_BLOQUEO:
                estado = 429
        if form.is_valid():
            rut_hash = hash_rut(form.cleaned_data['rut'])
            cuenta = Usuario.objects.filter(rut_hash=rut_hash).first()
            hay_datos = (Identificacion.objects.filter(rut_hash=rut_hash).exists()
                         or ConsentimientoPresencial.objects.filter(rut_hash=rut_hash).exists())
            if cuenta is not None:
                # Con cuenta, el retiro lo hace ella desde su cuenta: una profesional no borra
                # la participación de una cuenta ajena.
                form.add_error('rut', 'Esta persona tiene cuenta en la plataforma: debe retirarse ella misma '
                                      'desde su cuenta («Retirarme del estudio»).')
            elif not hay_datos:
                form.add_error('rut', 'No hay datos ni consentimiento registrados con ese RUT. No hay nada que retirar.')
            else:
                borrar_participacion(rut_hash)
                datos, comprobante = constancia_retiro.emitir(rut_hash, presencial={
                    'folio': form.cleaned_data['folio_revocacion'], 'custodia': form.cleaned_data['custodia'].strip(),
                    'profesional': request.user.pk})
                response = render(request, 'encuestas/retiro_presencial.html',
                                  {'constancia': datos, 'comprobante': comprobante})
                response['Cache-Control'] = 'no-store'
                return response
    return render(request, 'encuestas/retiro_presencial.html', {'form': form}, status=estado)
