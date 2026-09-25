from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginRutForm

urlpatterns = [
    # --- Registro (usuaria común) ---
    path('registro/', views.registro, name='registro'),
    path('registro/enviar-codigo/', views.enviar_codigo, name='registro_enviar_codigo'),
    path('registro/validar-codigo/', views.validar_codigo, name='registro_validar_codigo'),
    path('registro/enviado/', views.RegistroEnviadoView.as_view(), name='registro_enviado'),
    path('panel-medico/', views.panel_medico, name='panel_medico'),
    path('panel-medico/buscar/', views.buscar_paciente, name='buscar_paciente'),
    path('panel-medico/estadisticas/', views.estadisticas_medico, name='estadisticas_medico'),

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

    # --- Recuperación de contraseña (por correo) ---
    path(
        'clave/recuperar/',
        auth_views.PasswordResetView.as_view(
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
        auth_views.PasswordResetConfirmView.as_view(
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
