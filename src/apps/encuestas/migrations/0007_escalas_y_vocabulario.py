# Fase 1 — Escalas compartidas y vocabulario.
#
# - Renombra los campos `usa_remedios_*` a `usa_medicamentos_*` (regla de la
#   profesora: reemplazar "remedios" por "medicamentos"/"tratamiento").
# - Actualiza el help_text de `usa_antidepresivos` y `usa_terapia_hormonal`.
#
# Las nuevas clases de opciones (EscalaPorciones, EscalaFrecuenciaSubjetiva,
# EscalaEstresLaboral, FrecuenciaEvacuacionIntestinal, FrecuenciaDistensionAbdominal,
# CantidadPersonasCuidado) todavía no se usan en ningún campo, por lo que no
# generan operaciones aquí. El renombre de `EscalaConsumoSemanal` a
# `EscalaFrecuenciaSemanal` no cambia valores ni etiquetas: tampoco genera SQL.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0006_actividadfisica_sincronizado_en_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='mrs',
            old_name='usa_remedios_diabetes',
            new_name='usa_medicamentos_diabetes',
        ),
        migrations.RenameField(
            model_name='mrs',
            old_name='usa_remedios_presion',
            new_name='usa_medicamentos_presion',
        ),
        migrations.AlterField(
            model_name='mrs',
            name='usa_medicamentos_diabetes',
            field=models.CharField(
                blank=True, choices=[('SI', 'Sí'), ('NO', 'No')],
                help_text='¿Usa medicamentos para la diabetes?', max_length=2, null=True,
            ),
        ),
        migrations.AlterField(
            model_name='mrs',
            name='usa_medicamentos_presion',
            field=models.CharField(
                blank=True, choices=[('SI', 'Sí'), ('NO', 'No')],
                help_text='¿Usa medicamentos para la presión arterial?', max_length=2, null=True,
            ),
        ),
        migrations.AlterField(
            model_name='mrs',
            name='usa_antidepresivos',
            field=models.CharField(
                blank=True, choices=[('SI', 'Sí'), ('NO', 'No')],
                help_text='¿Usa antidepresivos o medicamentos para dormir?', max_length=2, null=True,
            ),
        ),
        migrations.AlterField(
            model_name='mrs',
            name='usa_terapia_hormonal',
            field=models.CharField(
                blank=True, choices=[('SI', 'Sí'), ('NO', 'No')],
                help_text='¿Usa tratamiento de terapia hormonal?', max_length=2, null=True,
            ),
        ),
    ]
