from django.db import migrations, models
import django.db.models.deletion


def crear_perfiles_existentes(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    PerfilUsuaria = apps.get_model('usuarios', 'PerfilUsuaria')
    PerfilMedico = apps.get_model('usuarios', 'PerfilMedico')
    for usuario in Usuario.objects.all().iterator():
        modelo = PerfilMedico if usuario.rol == 'PROFESIONAL' else PerfilUsuaria
        defaults = {} if modelo is PerfilMedico else {}
        modelo.objects.get_or_create(usuario_id=usuario.pk, defaults=defaults)


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='PerfilUsuaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_nacimiento', models.DateField(blank=True, null=True)),
                ('fecha_ultimo_periodo_menstrual', models.DateField(blank=True, null=True)),
                ('menopausia_quirurgica_inducida', models.BooleanField(blank=True, null=True)),
                ('fupm_no_aplica_por_cirugia', models.BooleanField(default=False)),
                ('edad_calculada', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('validacion_inicial_en', models.DateTimeField(blank=True, null=True)),
                ('consentimiento_aceptado', models.BooleanField(default=False)),
                ('consentimiento_aceptado_en', models.DateTimeField(blank=True, null=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_usuaria', to='usuarios.usuario')),
            ],
            options={'verbose_name': 'perfil de usuaria', 'verbose_name_plural': 'perfiles de usuarias'},
        ),
        migrations.CreateModel(
            name='PerfilMedico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('especialidad', models.CharField(max_length=120)),
                ('registro_medico', models.CharField(max_length=80, unique=True)),
                ('institucion', models.CharField(max_length=160)),
                ('aprobado', models.BooleanField(default=False)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_medico', to='usuarios.usuario')),
            ],
            options={'verbose_name': 'perfil médico', 'verbose_name_plural': 'perfiles médicos'},
        ),
        migrations.RunPython(crear_perfiles_existentes, migrations.RunPython.noop),
    ]