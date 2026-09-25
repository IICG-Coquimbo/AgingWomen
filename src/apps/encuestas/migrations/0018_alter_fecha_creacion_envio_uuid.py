from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('encuestas', '0017_envio_historico_fecha_creacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actividadfisica',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='conocimientosistema',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='envioencuesta',
            name='envio_uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
        migrations.AlterField(
            model_name='evaluaciontrabajo',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='habitosdevida',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='identificacion',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='mrs',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='segmentoempa',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='tareascuidado',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
