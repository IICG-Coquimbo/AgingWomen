from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from .models import Usuario
from .rut import hash_rut, validar_rut


class RegistroUsuariaForm(forms.Form):
    """
    Registro de usuaria común (regla 1.2): solo se pide RUT y correo.
    No se solicitan nombres ni apellidos.
    """

    rut = forms.CharField(
        label='RUT',
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': '12.345.678-9',
            'autofocus': True,
            'data-rut': 'true',
            'maxlength': '12',
            'inputmode': 'text',
        }),
        help_text='Será tu nombre de usuario. Se guarda cifrado.',
    )
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.cl'}),
        help_text='Solo se usa para enviarte y recuperar tu contraseña.',
    )

    def clean_rut(self):
        rut = self.cleaned_data['rut']
        if not validar_rut(rut):
            raise forms.ValidationError('El RUT ingresado no es válido.')
        if Usuario.objects.filter(rut_hash=hash_rut(rut)).exists():
            raise forms.ValidationError('Ya existe una cuenta registrada con este RUT.')
        return rut

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email



class RegistroConClaveForm(RegistroUsuariaForm):
    """
    Registro público de usuaria (Fase 21): además de RUT y correo, la persona
    elige su contraseña. El correo se verifica con un código antes de crear la
    cuenta. (El admin sigue usando RegistroUsuariaForm, con clave autogenerada.)
    """

    password1 = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].help_text = (
            'Te enviaremos un código para verificarlo. También sirve para '
            'recuperar tu contraseña.'
        )

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        elif p1:
            # Usuario temporal (no se guarda) para que el validador de
            # similitud compare la contraseña con el correo.
            provisional = Usuario(email=cleaned.get('email') or '')
            try:
                password_validation.validate_password(p1, provisional)
            except forms.ValidationError as error:
                self.add_error('password1', error)
        return cleaned


class VerificarCodigoForm(forms.Form):
    codigo = forms.CharField(
        label='Código de verificación',
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'autofocus': True,
            'placeholder': '123456',
        }),
    )

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].strip()
        if not codigo.isdigit():
            raise forms.ValidationError('El código tiene 6 números.')
        return codigo

class LoginRutForm(AuthenticationForm):
    """Login con RUT + contraseña. El backend hashea el RUT y busca la cuenta."""

    # Fase 28: un único mensaje, exista o no el RUT, para no revelar quién
    # está registrada (la plantilla agrega el enlace a "Crear cuenta").
    error_messages = {
        'invalid_login': 'RUT o contraseña incorrectos.',
        'inactive': 'RUT o contraseña incorrectos.',
    }

    username = forms.CharField(
        label='RUT',
        widget=forms.TextInput(attrs={
            'placeholder': '12.345.678-9',
            'autofocus': True,
            'data-rut': 'true',
            'maxlength': '12',
        }),
    )
