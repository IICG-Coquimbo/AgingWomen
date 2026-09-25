from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('encuestas', '0015_validacion_inicial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluacionSatisfaccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facilidad_uso', models.PositiveSmallIntegerField()),
                ('fatiga_mental', models.PositiveSmallIntegerField()),
                ('comodidad_diseno', models.PositiveSmallIntegerField()),
                ('recomendaria', models.CharField(max_length=20)),
                ('incomodidad', models.CharField(max_length=2)),
                ('comentario_incomodidad', models.TextField(blank=True)),
                ('respondida_en', models.DateTimeField(auto_now_add=True)),
                ('participante', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='evaluacion_satisfaccion', to='encuestas.identificacion')),
            ],
            options={
                'verbose_name': 'evaluación de satisfacción',
                'verbose_name_plural': 'evaluaciones de satisfacción',
            },
        ),
    ]
