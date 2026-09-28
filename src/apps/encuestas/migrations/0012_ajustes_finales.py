# Ajustes Finales Adicionales (complemento a los requisitos finales).
#
# - MRS.menstruacion_llega: se quita "Ausencia" (la calcula el sistema aparte
#   desde fecha_ultima_menstruacion) y se agrega "No estoy segura / No sé".
# - HabitosDeVida.quien_prepara_comidas: se quita "Generalmente pido delivery".
# - ConocimientoSistema: `recursos_conocidos` (lista de 8 ítems en texto libre)
#   se reemplaza por `conoce_recursos_disponibles`, una pregunta única Sí/No/
#   No sé. Se limpia de paso la nota de implementación ("Guardar como lista
#   separada por comas") que se filtraba también en otros dos help_text.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0011_trabajo_cuidado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mrs',
            name='menstruacion_llega',
            field=models.CharField(
                blank=True, null=True, max_length=10,
                choices=[
                    ('REGULAR', 'Regular (cada 21-35 días)'),
                    ('IRREGULAR', 'Irregular (<21 o >35 días)'),
                    ('NO_SEGURA', 'No estoy segura / No sé'),
                ],
                help_text='Durante el último año, mi menstruación llega',
            ),
        ),
        migrations.AlterField(
            model_name='habitosdevida',
            name='quien_prepara_comidas',
            field=models.CharField(
                blank=True, null=True, max_length=15,
                choices=[
                    ('YO_MAYORIA', 'Yo preparo la mayoría'),
                    ('COMPARTIDO', 'Yo preparo algunas y otras personas otras'),
                    ('OTRA_HOGAR', 'Otra persona de mi hogar prepara la mayoría'),
                    ('COMPRO', 'Generalmente compro comida preparada'),
                    ('OTRO', 'Otro'),
                ],
                help_text='¿Quién prepara habitualmente sus comidas principales?',
            ),
        ),
        migrations.RemoveField(model_name='conocimientosistema', name='recursos_conocidos'),
        migrations.AddField(
            model_name='conocimientosistema',
            name='conoce_recursos_disponibles',
            field=models.CharField(
                blank=True, null=True, max_length=2,
                choices=[('SI', 'Sí'), ('NO', 'No'), ('NS', 'No sabe')],
                help_text='¿Conoce alguno de los recursos o prestaciones disponibles para climaterio/menopausia?',
            ),
        ),
        migrations.AlterField(
            model_name='conocimientosistema',
            name='principales_dificultades',
            field=models.TextField(
                blank=True, null=True,
                help_text=(
                    '¿Cuáles han sido las principales dificultades? Selección múltiple: '
                    'Falta de información / Dificultad para obtener horas / Costos / '
                    'Falta de especialistas / No saber dónde consultar / Minimización de síntomas / '
                    'Horarios incompatibles / Otra.'
                ),
            ),
        ),
        migrations.AlterField(
            model_name='conocimientosistema',
            name='tipo_informacion_apoyo_deseado',
            field=models.TextField(
                blank=True, null=True,
                help_text=(
                    '¿Qué tipo de información o apoyo considera más necesario? Selección múltiple: '
                    'Información general / Salud mental / Nutrición / Actividad física / Manejo de síntomas / '
                    'Atención ginecológica / Terapia hormonal / Apoyo laboral / Otro.'
                ),
            ),
        ),
    ]
