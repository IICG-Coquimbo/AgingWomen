# Fase 5 — Trabajo y Tareas de Cuidado (doble carga).
#
# - EvaluacionTrabajo: nueva pregunta `estres_entorno_laboral`.
# - TareasCuidado: se reemplaza el booleano `mas_de_una_persona_a_cargo` por
#   `cantidad_personas_cuida` (1/2/3+), `a_quien_cuida` (selección múltiple,
#   texto separado por comas) y `a_quien_cuida_otro`; se agrega la pregunta de
#   cierre `sobrecarga_fisica_emocional` y se reformula `cuida_otras_personas`.

from django.db import migrations, models

_ESTRES = [
    (1, 'Nada de estrés'), (2, 'Estrés leve'), (3, 'Estrés moderado'),
    (4, 'Estrés alto'), (5, 'Estrés extremo'),
]
_CANTIDAD = [(1, '1 persona'), (2, '2 personas'), (3, '3 o más personas')]
_SUBJETIVA = [
    (1, 'Nunca o casi nunca'), (2, 'Rara vez'), (3, 'A veces'),
    (4, 'Frecuentemente'), (5, 'Siempre'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0010_habitos_de_vida'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluaciontrabajo',
            name='estres_entorno_laboral',
            field=models.IntegerField(
                blank=True, null=True, choices=_ESTRES,
                help_text='¿Su entorno laboral le genera niveles de estrés que intensifiquen sus síntomas?',
            ),
        ),
        migrations.AlterField(
            model_name='tareascuidado',
            name='cuida_otras_personas',
            field=models.CharField(
                blank=True, null=True, max_length=2, choices=[('SI', 'Sí'), ('NO', 'No')],
                help_text=('¿Tiene a su cargo el cuidado directo de otras personas '
                           '(hijos, adultos mayores, familiares dependientes)?'),
            ),
        ),
        migrations.RemoveField(model_name='tareascuidado', name='mas_de_una_persona_a_cargo'),
        migrations.AddField(
            model_name='tareascuidado',
            name='cantidad_personas_cuida',
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, choices=_CANTIDAD,
                help_text='Si respondió "Sí", ¿a cuántas personas cuida de forma directa?',
            ),
        ),
        migrations.AddField(
            model_name='tareascuidado',
            name='a_quien_cuida',
            field=models.TextField(
                blank=True, null=True,
                help_text='¿A quién cuida? (marque todas las opciones que apliquen)',
            ),
        ),
        migrations.AddField(
            model_name='tareascuidado',
            name='a_quien_cuida_otro',
            field=models.CharField(
                blank=True, null=True, max_length=200,
                help_text='Si marcó "Otro", especifique a quién cuida',
            ),
        ),
        migrations.AddField(
            model_name='tareascuidado',
            name='sobrecarga_fisica_emocional',
            field=models.IntegerField(
                blank=True, null=True, choices=_SUBJETIVA,
                help_text=('¿Siente que la combinación entre su trabajo y las tareas de '
                           'cuidado le genera una sobrecarga física o emocional?'),
            ),
        ),
    ]
