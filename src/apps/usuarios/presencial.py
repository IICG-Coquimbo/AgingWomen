"""
Fase 40, Etapa 2: registro del consentimiento presencial por una profesional.

La profesional no puede «marcar» un consentimiento: debe acreditar la aceptación con
- el folio del documento de consentimiento firmado por la participante (único: un
  mismo documento no sirve para dos personas) y dónde queda custodiado;
- su declaración de que la participante lo leyó, aclaró sus dudas y lo firmó en su presencia;
- si la persona ya tiene cuenta: su propia contraseña, ingresada por ella. Así una
  profesional no puede reactivar sola un consentimiento retirado; después de un retiro
  la persona debe aceptar de nuevo, en línea o presencialmente con su contraseña.

No se guardan fotografías, documentos de identidad ni datos clínicos. El RUT llega solo
por POST y se guarda pseudonimizado (rut_hash), igual que en el resto de la plataforma.
"""
import re

from django import forms
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from . import intentos
from .decorators import requiere_profesional
from .models import ConsentimientoPresencial, Usuario
from .privacidad import sin_consentimiento_vigente, version_consentimiento
from .rut import hash_rut, normalizar_rut, validar_rut

FOLIO = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._/-]{2,39}$')


class ConsentimientoPresencialForm(forms.Form):
    folio_documento = forms.CharField(
        label='Folio o código del documento de consentimiento firmado', max_length=40,
        help_text='El identificador escrito en el documento en papel (por ejemplo, CI-2026-0147).')
    custodia = forms.CharField(
        label='Dónde queda custodiado el documento firmado', max_length=120, min_length=3,
        help_text='Por ejemplo: «Archivo del proyecto, oficina de la investigadora responsable». '
                  'No escribas datos personales ni clínicos.')
    declaracion = forms.BooleanField(
        label='Declaro que la participante leyó el consentimiento, se respondieron sus dudas y lo '
              'firmó en mi presencia de forma libre y expresa.')
    clave_participante = forms.CharField(
        label='Contraseña de la cuenta de la participante (la escribe ella)', required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}))

    def __init__(self, *args, cuenta=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cuenta = cuenta
        if cuenta is None:
            del self.fields['clave_participante']
        else:
            self.fields['clave_participante'].required = True

    def clean_folio_documento(self):
        folio = self.cleaned_data['folio_documento'].strip()
        if not FOLIO.match(folio):
            raise forms.ValidationError('Usa de 3 a 40 letras, números, guiones, puntos o barras.')
        if ConsentimientoPresencial.objects.filter(folio_documento=folio).exists():
            raise forms.ValidationError('Ese folio ya está registrado para otra aceptación.')
        return folio

    # La contraseña se comprueba en la vista, con el límite de intentos (apps.usuarios.intentos),
    # y nunca se conserva.


@never_cache
@login_required
@requiere_profesional
@require_POST
def consentimiento_presencial(request):
    rut = request.POST.get('rut', '').strip()
    if not validar_rut(rut):
        return render(request, 'encuestas/buscar_paciente.html',
                      {'rut': '', 'resultado': None, 'error': 'El RUT ingresado no es válido.'}, status=400)
    rut_hash = hash_rut(rut)
    cuenta = Usuario.objects.filter(rut_hash=rut_hash).first()
    if cuenta is not None and cuenta.es_profesional:
        cuenta = None
    contexto = {'rut': normalizar_rut(rut), 'cuenta': cuenta, 'version': version_consentimiento()}
    if not sin_consentimiento_vigente(rut_hash):
        return render(request, 'usuarios/consentimiento_presencial.html', dict(contexto, ya_vigente=True))

    form = ConsentimientoPresencialForm(request.POST if 'registrar' in request.POST else None, cuenta=cuenta)
    estado = 400
    if form.is_bound and cuenta is not None and request.POST.get('clave_participante'):
        # Límite de intentos en el servidor: mientras hay bloqueo la contraseña no se comprueba.
        # Mensajes genéricos: no dicen cuántos intentos quedan ni nada de la cuenta.
        error_clave = intentos.verificar_clave(cuenta, request.POST['clave_participante'], request.user)
        if error_clave:
            form.is_valid()
            form.add_error('clave_participante', error_clave)
            if error_clave == intentos.MENSAJE_BLOQUEO:
                estado = 429
    if form.is_bound and form.is_valid():
        try:
            with transaction.atomic():
                # Una fila anterior solo puede quedar si no hay consentimiento vigente: se reemplaza.
                ConsentimientoPresencial.objects.filter(rut_hash=rut_hash).delete()
                ahora = timezone.now()
                ConsentimientoPresencial.objects.create(
                    rut_hash=rut_hash, usuario=cuenta, version=contexto['version'],
                    verificacion=(ConsentimientoPresencial.Verificacion.CLAVE_CUENTA if cuenta
                                  else ConsentimientoPresencial.Verificacion.DOCUMENTO_FIRMADO),
                    folio_documento=form.cleaned_data['folio_documento'],
                    custodia=form.cleaned_data['custodia'].strip(),
                    registrado_por=request.user, registrado_en=ahora)
                if cuenta is not None:
                    # Nueva participación (nuevo identificador): nada de una participación anterior se recupera.
                    cuenta.consentimiento_aceptado_en = ahora
                    cuenta.save(update_fields=['consentimiento_aceptado_en'])
        except IntegrityError:
            form.add_error('folio_documento', 'Ese folio ya está registrado para otra aceptación.')
        else:
            return render(request, 'usuarios/consentimiento_presencial.html', dict(contexto, registrado=True))
    return render(request, 'usuarios/consentimiento_presencial.html', dict(contexto, form=form),
                  status=estado if form.is_bound else 200)
