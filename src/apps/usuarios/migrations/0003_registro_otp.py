from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_usuario_consentimiento_aceptado_en'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut_hash', models.CharField(max_length=64)),
                ('email', models.EmailField(max_length=254)),
                ('password_hash', models.CharField(max_length=128)),
                ('codigo_hash', models.CharField(max_length=64)),
                ('intentos', models.PositiveSmallIntegerField(default=0)),
                ('enviado_en', models.DateTimeField()),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'registro pendiente de verificación',
                'verbose_name_plural': 'registros pendientes de verificación',
            },
        ),
    ]
