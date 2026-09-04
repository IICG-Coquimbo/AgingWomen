from django.contrib import admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('rut_hash_corto', 'email', 'rol', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('rol', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'rut_hash')
    ordering = ('-date_joined',)
    readonly_fields = ('rut_hash', 'password', 'last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('rut_hash', 'email', 'password')}),
        ('Rol y permisos', {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )

    @admin.display(description='RUT (hash)')
    def rut_hash_corto(self, obj):
        return f'{obj.rut_hash[:12]}…'

    def has_add_permission(self, request):
        # Las cuentas se crean por el registro público (usuaria común) o por el
        # comando `crear_profesional` (personal de salud).
        return False
