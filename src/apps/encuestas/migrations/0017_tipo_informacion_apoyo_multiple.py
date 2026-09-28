from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0016_evaluacion_satisfaccion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conocimientosistema',
            name='tipo_informacion_apoyo_deseado',
            field=models.TextField(blank=True, help_text='¿Qué tipo de información o apoyo considera más necesario? (marque todas las opciones que apliquen)', null=True),
        ),
        migrations.AddField(
            model_name='conocimientosistema',
            name='tipo_informacion_apoyo_otro',
            field=models.CharField(blank=True, help_text='Si marcó "Otro", especifique qué tipo de información o apoyo', max_length=200, null=True),
        ),
    ]
