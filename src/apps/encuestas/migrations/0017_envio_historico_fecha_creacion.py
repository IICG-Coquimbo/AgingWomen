from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('encuestas', '0016_evaluacion_satisfaccion'),
        ('usuarios', '0003_registro_otp'),
    ]

    operations = [
        migrations.AddField(
            model_name='identificacion', name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='mrs', name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='segmentoempa', name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='conocimientosistema', name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='evaluaciontrabajo', name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='tareascuidado', name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='actividadfisica', name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='habitosdevida', name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.CreateModel(
            name='EnvioEncuesta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('envio_uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('payload', models.JSONField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='envios_encuesta', to='usuarios.usuario')),
                ('participante', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='envios_historicos', to='encuestas.identificacion')),
            ],
            options={'ordering': ['-fecha_creacion']},
        ),
    ]
