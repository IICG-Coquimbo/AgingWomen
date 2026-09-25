from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0002_perfiles_registro'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('rut_hash', models.CharField(max_length=64)),
                ('tipo_cuenta', models.CharField(choices=[('USUARIA', 'Usuaria común'), ('PROFESIONAL', 'Profesional / Personal del servicio de salud')], max_length=12)),
                ('codigo_hash', models.CharField(max_length=128)),
                ('expira_en', models.DateTimeField()),
                ('intentos', models.PositiveSmallIntegerField(default=0)),
                ('validado_en', models.DateTimeField(blank=True, null=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
