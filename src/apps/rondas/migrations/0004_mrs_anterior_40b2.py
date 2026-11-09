"""
Fase 40B-2: marca los registros MRS existentes como anteriores a la 40B-2.

No lee ni cambia ningún valor de respuesta: solo crea una fila de marca por
cada registro MRS que ya existía (sus ceros no se pueden verificar). Los MRS
creados después no llevan marca: sus ítems sin respuesta quedan nulos.
Reversa: se niega si hay marcas. Borrarlas haría pasar los ceros no
verificables por respuestas reales, sin que quede rastro.
"""
from django.db import migrations, models
import django.db.models.deletion


def marcar(apps, schema_editor):
    MRS = apps.get_model('encuestas', 'MRS')
    Marca = apps.get_model('rondas', 'MRSAnterior40B2')
    ids = list(MRS.objects.order_by('id').values_list('id', flat=True))
    Marca.objects.bulk_create([Marca(mrs_id=i, items_confirmados=[]) for i in ids])
    print(f'\n  Marca 40B-2: {len(ids)} registros MRS anteriores marcados como no verificables (sin cambiar valores)')


def desmarcar(apps, schema_editor):
    n = apps.get_model('rondas', 'MRSAnterior40B2').objects.count()
    if n:
        raise RuntimeError(
            f'Reversa rondas 0004 detenida: {n} registros MRS están marcados como anteriores a la 40B-2. '
            'Borrar las marcas haría pasar sus ceros no verificables por respuestas reales.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0020_mrs_items_sin_respuesta_nulos'),
        ('rondas', '0003_unicidad_secciones'),
    ]

    operations = [
        migrations.CreateModel(
            name='MRSAnterior40B2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('items_confirmados', models.JSONField(blank=True, default=list)),
                ('registrada_en', models.DateTimeField(auto_now_add=True)),
                ('confirmado_en', models.DateTimeField(blank=True, help_text='Cuándo quedaron confirmados todos sus ceros (si ocurrió).', null=True)),
                ('mrs', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='marca_anterior_40b2', to='encuestas.mrs')),
            ],
            options={
                'verbose_name': 'MRS anterior a la 40B-2',
                'verbose_name_plural': 'MRS anteriores a la 40B-2',
            },
        ),
        migrations.RunPython(marcar, desmarcar),
    ]
