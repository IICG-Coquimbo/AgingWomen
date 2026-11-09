from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from .forms import RegistroUsuariaForm
from .models import Usuario
from .views import enviar_activacion_email


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('rut_hash_corto', 'email', 'rol', 'is_active', 'is_staff', 'date_joined', 'consentimiento_aceptado_en')
    list_filter = ('rol', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'rut_hash')
    ordering = ('-date_joined',)
    readonly_fields = ('rut_hash', 'password', 'last_login', 'date_joined', 'consentimiento_aceptado_en')
    actions = ['promover_a_profesional', 'revocar_a_usuaria_comun']

    fieldsets = (
        (None, {'fields': ('rut_hash', 'email', 'password')}),
        ('Rol y permisos', {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Fechas', {'fields': ('last_login', 'date_joined', 'consentimiento_aceptado_en')}),
    )

    @admin.display(description='RUT (hash)')
    def rut_hash_corto(self, obj):
        return f'{obj.rut_hash[:12]}…'

    def has_add_permission(self, request):
        # No se pueden crear cuentas con el formulario estándar del admin (el
        # RUT en claro y la contraseña no son campos de edición directa). La
        # usuaria común se crea por el registro público; el personal de salud
        # se crea con la vista "Crear cuenta de personal de salud" de abajo.
        return False

    @admin.action(description='Promover a profesional de salud')
    def promover_a_profesional(self, request, queryset):
        actualizados = queryset.update(rol=Usuario.Rol.PROFESIONAL_SALUD)
        self.message_user(request, f'{actualizados} cuenta(s) promovida(s) a profesional de salud.')

    @admin.action(description='Revocar a usuaria común')
    def revocar_a_usuaria_comun(self, request, queryset):
        actualizados = queryset.update(rol=Usuario.Rol.USUARIA_COMUN)
        self.message_user(request, f'{actualizados} cuenta(s) revocada(s) a usuaria común.')

    def get_urls(self):
        propias = [
            path(
                'crear-profesional/',
                self.admin_site.admin_view(self.crear_profesional_view),
                name='usuarios_usuario_crear_profesional',
            ),
        ]
        return propias + super().get_urls()

    def crear_profesional_view(self, request):
        if not request.user.is_superuser:
            messages.error(request, 'Solo un superusuario puede crear cuentas de personal de salud.')
            return redirect('admin:index')

        if request.method == 'POST':
            form = RegistroUsuariaForm(request.POST)
            if form.is_valid():
                usuario = Usuario.objects.create_user(
                    rut=form.cleaned_data['rut'],
                    email=form.cleaned_data['email'],
                    rol=Usuario.Rol.PROFESIONAL_SALUD,
                )
                enviar_activacion_email(request, usuario)
                messages.success(
                    request,
                    f'Cuenta de personal de salud creada. Enlace de activación enviado a {usuario.email}.',
                )
                return redirect('admin:usuarios_usuario_changelist')
        else:
            form = RegistroUsuariaForm()

        return render(request, 'admin/usuarios/crear_profesional.html', {
            'form': form,
            'opts': self.model._meta,
            'title': 'Crear cuenta de personal de salud',
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'has_permission': True,
        })
