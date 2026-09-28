# Corrección de texto: se pidió mantener el enunciado completo con la lista
# de recursos como ejemplo (igual al original, sin la nota de implementación
# que ya se había quitado). La pregunta sigue siendo Sí/No/No sé.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0012_ajustes_finales'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conocimientosistema',
            name='conoce_recursos_disponibles',
            field=models.CharField(
                blank=True, null=True, max_length=2,
                choices=[('SI', 'Sí'), ('NO', 'No'), ('NS', 'No sabe')],
                help_text=(
                    '¿Conoce alguno de los siguientes recursos o prestaciones? '
                    '(Atención médica en APS/CESFAM, Controles ginecológicos, Terapia hormonal, '
                    'Atención psicológica, Consejería en salud mental, Orientación nutricional, '
                    'Programas de actividad física, No conozco prestaciones relacionadas).'
                ),
            ),
        ),
    ]
