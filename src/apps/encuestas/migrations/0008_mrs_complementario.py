# Fase 2 — MRS y Cuestionario Complementario.
#
# - MRS: nuevas preguntas `evacuacion_intestinal` y `distension_abdominal`;
#   método anticonceptivo suma "No sé" y campo libre `tipo_metodo_anticonceptivo_otro`.
# - Se quita de MRS `control_otros_programas` (+ `_cual`): la pregunta se
#   reformula y se traslada a Conocimiento del Sistema como
#   `en_control_programa_consultorio` (+ `en_control_programa_cual`).
#
# El MRS se parte en dos pantallas ('mrs' / 'mrs_complementario') solo a nivel
# de esquema y cliente: sigue siendo un único modelo/tabla, así que aquí no hay
# operaciones por esa división.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0007_escalas_y_vocabulario'),
    ]

    operations = [
        migrations.RemoveField(model_name='mrs', name='control_otros_programas'),
        migrations.RemoveField(model_name='mrs', name='control_otros_programas_cual'),
        migrations.AddField(
            model_name='mrs',
            name='tipo_metodo_anticonceptivo_otro',
            field=models.CharField(
                blank=True, max_length=100, null=True,
                help_text='Si seleccionó "Otro", ¿cuál método anticonceptivo?',
            ),
        ),
        migrations.AddField(
            model_name='mrs',
            name='evacuacion_intestinal',
            field=models.IntegerField(
                blank=True, null=True,
                choices=[
                    (1, 'Más de una vez al día'), (2, '1 vez al día'),
                    (3, 'Cada 2 días'), (4, '3 o más días entre evacuaciones'),
                ],
                help_text='¿Con qué frecuencia tiene evacuación intestinal?',
            ),
        ),
        migrations.AddField(
            model_name='mrs',
            name='distension_abdominal',
            field=models.IntegerField(
                blank=True, null=True,
                choices=[
                    (1, 'Nunca o casi nunca'), (2, 'A veces'),
                    (3, 'Frecuentemente'), (4, 'Siempre'),
                ],
                help_text='¿Con qué frecuencia siente distensión o hinchazón abdominal?',
            ),
        ),
        migrations.AlterField(
            model_name='mrs',
            name='tipo_metodo_anticonceptivo',
            field=models.CharField(
                blank=True, max_length=12, null=True,
                choices=[
                    ('ORAL', 'Oral'), ('INYECTABLE', 'Inyectable'), ('DIU', 'DIU'),
                    ('IMPLANTE', 'Implante'), ('PRESERVATIVO', 'Preservativo'),
                    ('NO_SE', 'No sé'), ('OTRO', 'Otro'),
                ],
                help_text='Si la respuesta es sí, ¿qué tipo utiliza?',
            ),
        ),
        migrations.AddField(
            model_name='conocimientosistema',
            name='en_control_programa_consultorio',
            field=models.CharField(
                blank=True, max_length=2, null=True,
                choices=[('SI', 'Sí'), ('NO', 'No')],
                help_text='¿Está en control en algún programa de su consultorio?',
            ),
        ),
        migrations.AddField(
            model_name='conocimientosistema',
            name='en_control_programa_cual',
            field=models.CharField(
                blank=True, max_length=255, null=True,
                help_text='Si es sí, ¿en cuál programa?',
            ),
        ),
    ]
