from django.contrib.auth import views as auth_views
from django.urls import path

from . import inactividad, views
from . import vistas_clave
from .forms import LoginRutForm

urlpatterns = [
    # --- Registro (usuaria común) ---
    path('registro/', views.registro, name='registro'),
    path('registro/verificar/', views.verificar_registro, name='registro_verificar'),
    path('registro/reenviar/', views.reenviar_codigo, name='registro_reenviar'),

    # --- Ingreso / salida ---
    path(
        'ingresar/',
        auth_views.LoginView.as_view(
            template_name='usuarios/login.html',
            authentication_form=LoginRutForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('actividad/', inactividad.actividad, name='actividad'),   # Fase 40 E2

    # --- Consentimiento informado (previo al ingreso a la encuesta) ---
    path('consentimiento/', views.consentimiento, name='consentimiento'),

    # --- Recuperación de contraseña (por correo) ---
    path(
        'clave/recuperar/',
        vistas_clave.RecuperarClaveView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
        ),
        name='password_reset',
    ),
    path(
        'clave/recuperar/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'clave/recuperar/<uidb64>/<token>/',
        vistas_clave.ConfirmarClaveView.as_view(
            template_name='registration/password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path(
        'clave/recuperada/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),

    # --- Cambio de contraseña (con sesión iniciada) ---
    path(
        'clave/cambiar/',
        auth_views.PasswordChangeView.as_view(
            template_name='registration/password_change_form.html',
        ),
        name='password_change',
    ),
    path(
        'clave/cambiada/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html',
        ),
        name='password_change_done',
    ),
]
