from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0013_texto_recursos_conocidos'),
    ]

    operations = [
        migrations.AddField(
            model_name='identificacion',
            name='consentimiento_aceptado',
            field=models.BooleanField(
                default=False,
                help_text='La participante aceptó participar voluntariamente en el estudio',
            ),
        ),
        migrations.AddField(
            model_name='identificacion',
            name='consentimiento_aceptado_en',
            field=models.DateTimeField(
                blank=True,
                help_text='Fecha y hora en que se registró la aceptación del consentimiento',
                null=True,
            ),
        ),
    ]