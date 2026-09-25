from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Usuario
from .rut import hash_rut, validar_rut


class RegistroForm(forms.Form):
    """Registro público: todas las cuentas nuevas son usuarias comunes."""

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
        help_text='Aquí recibirás tus credenciales de acceso.',
    )

    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput,
    )
    password_confirm = forms.CharField(
        label='Confirmar contraseña',
        strip=False,
        widget=forms.PasswordInput,
    )

    codigo_verificacion = forms.CharField(
        label='Código de verificación', max_length=6, required=False,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'autocomplete': 'one-time-code'}),
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

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            self.add_error('password_confirm', 'Las contraseñas no coinciden.')
        return cleaned


# Compatibilidad con imports históricos.
RegistroUsuariaForm = RegistroForm


class LoginRutForm(AuthenticationForm):
    """Ingreso sin selector de rol: acepta RUT o correo electrónico."""

    username = forms.CharField(
        label='RUT o correo electrónico',
        widget=forms.TextInput(attrs={
            'placeholder': '12.345.678-9 o correo@ejemplo.cl',
            'autofocus': True,
        }),
    )
