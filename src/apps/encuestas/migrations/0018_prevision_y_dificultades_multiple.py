from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0017_tipo_informacion_apoyo_multiple'),
    ]

    operations = [
        migrations.AddField(
            model_name='conocimientosistema',
            name='prevision',
            field=models.CharField(blank=True, choices=[('FONASA', 'Fonasa'), ('ISAPRE', 'Isapre'), ('FFAA', 'FF.AA. y de Orden (Capredena, Dipreca)'), ('NINGUNA', 'Ninguna (particular)'), ('NS', 'No sé')], help_text='¿Qué previsión de salud tiene?', max_length=7, null=True),
        ),
        migrations.AlterField(
            model_name='conocimientosistema',
            name='principales_dificultades',
            field=models.TextField(blank=True, help_text='¿Cuáles han sido las principales dificultades? (marque todas las opciones que apliquen)', null=True),
        ),
        migrations.AddField(
            model_name='conocimientosistema',
            name='principales_dificultades_otra',
            field=models.CharField(blank=True, help_text='Si marcó "Otra", ¿cuál?', max_length=200, null=True),
        ),
    ]
