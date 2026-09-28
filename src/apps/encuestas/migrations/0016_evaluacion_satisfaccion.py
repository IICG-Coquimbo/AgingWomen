import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0015_actividadfisica_ronda_conocimientosistema_ronda_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluacionSatisfaccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facilidad_uso', models.PositiveSmallIntegerField(choices=[(1, '😡 Muy difícil'), (2, '😕 Difícil'), (3, '😐 Normal'), (4, '🙂 Fácil'), (5, '😍 Muy fácil')], help_text='¿Cómo evalúas la facilidad para responder el cuestionario?')),
                ('fatiga_mental', models.PositiveSmallIntegerField(choices=[(1, 'Ninguno'), (2, 'Poco'), (3, 'Moderado'), (4, 'Mucho')], help_text='¿Sentiste fatiga o cansancio mental al responder la encuesta?')),
                ('comodidad_diseno', models.PositiveSmallIntegerField(choices=[(1, '★'), (2, '★★'), (3, '★★★'), (4, '★★★★'), (5, '★★★★★')], help_text='¿Qué tan cómodo te pareció el diseño y la navegación de la plataforma?')),
                ('recomendaria', models.CharField(choices=[('SI', 'Definitivamente sí'), ('TAL_VEZ', 'Tal vez'), ('NO', 'No')], help_text='¿Recomendarías este Observatorio a otras mujeres en etapa de peri o menopausia?', max_length=7)),
                ('incomodidad', models.CharField(choices=[('SI', 'Sí'), ('NO', 'No')], help_text='¿Hubo alguna pregunta que te generara incomodidad o confusión?', max_length=2)),
                ('comentario_incomodidad', models.TextField(blank=True, help_text='Cuál pregunta o por qué (obligatorio si respondió Sí)')),
                ('respondida_en', models.DateTimeField(auto_now_add=True)),
                ('actualizada_en', models.DateTimeField(auto_now=True)),
                ('participante', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='evaluacion_satisfaccion', to='encuestas.identificacion')),
            ],
            options={
                'verbose_name': 'evaluación de satisfacción',
                'verbose_name_plural': 'evaluaciones de satisfacción',
            },
        ),
    ]
