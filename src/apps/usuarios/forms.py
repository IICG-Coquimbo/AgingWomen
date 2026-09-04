from django import forms
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


class LoginRutForm(AuthenticationForm):
    """Login con RUT + contraseña. El backend hashea el RUT y busca la cuenta."""

    username = forms.CharField(
        label='RUT',
        widget=forms.TextInput(attrs={
            'placeholder': '12.345.678-9',
            'autofocus': True,
            'data-rut': 'true',
            'maxlength': '12',
        }),
    )
