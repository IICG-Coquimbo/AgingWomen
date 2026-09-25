from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0014_identificacion_consentimiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='identificacion', name='edad_calculada',
            field=models.PositiveSmallIntegerField(blank=True, editable=False, null=True,
                help_text='Edad calculada al pasar la validación inicial'),
        ),
        migrations.AddField(
            model_name='identificacion', name='menopausia_quirurgica_inducida',
            field=models.BooleanField(blank=True, null=True,
                help_text='Menopausia quirúrgica o inducida por tratamiento médico'),
        ),
        migrations.AddField(
            model_name='identificacion', name='fecha_ultimo_periodo_menstrual',
            field=models.DateField(blank=True, null=True,
                help_text='Fecha del último periodo menstrual informada en la validación inicial'),
        ),
        migrations.AddField(
            model_name='identificacion', name='fupm_no_aplica_por_cirugia',
            field=models.BooleanField(default=False,
                help_text='La FUPM no aplica por cirugía o menopausia quirúrgica'),
        ),
        migrations.AddField(
            model_name='identificacion', name='validacion_inicial_en',
            field=models.DateTimeField(blank=True, null=True,
                help_text='Fecha y hora de la validación inicial'),
        ),
    ]