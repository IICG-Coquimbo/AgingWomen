from django.db import migrations, models

# Secciones que se guardan por ronda (mismos modelos que sync.SECCIONES).
MODELOS_SECCION = (
    'MRS', 'SegmentoEMPA', 'ConocimientoSistema', 'EvaluacionTrabajo',
    'TareasCuidado', 'HabitosDeVida', 'ActividadFisica',
)


def rellenar_ultima_finalizacion(apps, schema_editor):
    """
    Rondas finalizadas antes de este cambio: se usa como fecha de finalización
    el último guardado de la ronda ya cerrada (ronda_actual - 1).
    """
    Identificacion = apps.get_model('encuestas', 'Identificacion')
    modelos = [apps.get_model('encuestas', nombre) for nombre in MODELOS_SECCION]
    for ident in Identificacion.objects.filter(ronda_actual__gt=1):
        cerrada = ident.ronda_actual - 1
        fechas = [
            f for modelo in modelos
            for f in modelo.objects.filter(participante=ident, ronda=cerrada)
            .exclude(sincronizado_en=None).values_list('sincronizado_en', flat=True)
        ]
        fecha = max(fechas) if fechas else ident.sincronizado_en
        if fecha:
            ident.ultima_finalizacion_en = fecha
            ident.save(update_fields=['ultima_finalizacion_en'])


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0018_prevision_y_dificultades_multiple'),
    ]

    operations = [
        migrations.AddField(
            model_name='identificacion',
            name='ultima_finalizacion_en',
            field=models.DateTimeField(blank=True, editable=False, help_text='Cuándo se finalizó la última ronda (Fase 31: plazo de 15 días entre rondas).', null=True),
        ),
        migrations.RunPython(rellenar_ultima_finalizacion, migrations.RunPython.noop),
    ]
