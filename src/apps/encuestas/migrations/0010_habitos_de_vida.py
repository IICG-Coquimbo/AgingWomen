# Fase 4 — Hábitos de Vida (antes "Hábitos alimenticios").
#
# - Renombra el modelo HabitosAlimenticios -> HabitosDeVida (tabla y relación
#   inversa). La sección se presenta antes de "Actividad física" (eso es orden
#   de esquema, no migración).
# - Todas las cantidades/frecuencias pasan a escalas de 5 niveles
#   (EscalaPorciones / EscalaFrecuenciaSemanal / EscalaFrecuenciaSubjetiva).
# - Nuevas preguntas: quien_prepara_comidas_otro (texto libre) y consumo de
#   sustancias tabaco/marihuana/alcohol (trasladado desde el EMPA, Fase 3).

import django.db.models.deletion
from django.db import migrations, models

_PORCIONES = [
    (1, 'No consumo'), (2, '1-2 porciones'), (3, '3-4 porciones'),
    (4, '5-6 porciones'), (5, '7 o más porciones'),
]
_SEMANAL = [
    (1, 'Nunca'), (2, '1-2 veces por semana'), (3, '3-4 veces por semana'),
    (4, '5-6 veces por semana'), (5, 'Diariamente'),
]
_SUBJETIVA = [
    (1, 'Nunca o casi nunca'), (2, 'Rara vez'), (3, 'A veces'),
    (4, 'Frecuentemente'), (5, 'Siempre'),
]
_QUIEN_PREPARA = [
    ('YO_MAYORIA', 'Yo preparo la mayoría'),
    ('COMPARTIDO', 'Yo preparo algunas y otras personas otras'),
    ('OTRA_HOGAR', 'Otra persona de mi hogar prepara la mayoría'),
    ('COMPRO', 'Generalmente compro comida preparada'),
    ('DELIVERY', 'Generalmente pido delivery'),
    ('OTRO', 'Otro'),
]


def _porciones(help_text):
    return models.PositiveSmallIntegerField(
        blank=True, null=True, choices=_PORCIONES, help_text=help_text)


def _semanal(help_text):
    return models.PositiveSmallIntegerField(
        blank=True, null=True, choices=_SEMANAL, help_text=help_text)


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0009_empa_sustancias_fuera'),
    ]

    operations = [
        migrations.RenameModel(old_name='HabitosAlimenticios', new_name='HabitosDeVida'),
        migrations.AlterModelOptions(
            name='habitosdevida',
            options={
                'ordering': ['-fecha_evaluacion'],
                'verbose_name': 'Sección Hábitos de Vida',
                'verbose_name_plural': 'Secciones Hábitos de Vida',
            },
        ),
        migrations.AlterField(
            model_name='habitosdevida',
            name='participante',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='evaluaciones_habitos_de_vida',
                to='encuestas.identificacion',
            ),
        ),
        migrations.AlterField(
            model_name='habitosdevida',
            name='fecha_evaluacion',
            field=models.DateField(
                auto_now_add=True,
                help_text='Fecha en que se responde la sección Hábitos de vida',
            ),
        ),
        migrations.AlterField(
            model_name='habitosdevida',
            name='quien_prepara_comidas',
            field=models.CharField(
                blank=True, null=True, max_length=15, choices=_QUIEN_PREPARA,
                help_text='¿Quién prepara habitualmente sus comidas principales?',
            ),
        ),
        migrations.AddField(
            model_name='habitosdevida',
            name='quien_prepara_comidas_otro',
            field=models.CharField(
                blank=True, null=True, max_length=100,
                help_text='Si seleccionó "Otro", ¿quién prepara sus comidas?',
            ),
        ),
        migrations.AlterField(
            model_name='habitosdevida',
            name='frecuencia_comida_fuera',
            field=models.IntegerField(
                blank=True, null=True, choices=_SEMANAL,
                help_text='¿Con qué frecuencia consume comidas compradas/preparadas fuera del hogar?',
            ),
        ),
        migrations.AlterField(
            model_name='habitosdevida',
            name='falta_tiempo_influye',
            field=models.IntegerField(
                blank=True, null=True, choices=_SUBJETIVA,
                help_text='¿La falta de tiempo influye en su elección de alimentos?',
            ),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='vasos_agua_dia',
            field=_porciones('¿Cuántos vasos de agua toma al día?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='platos_verduras_dia',
            field=_porciones('¿Cuántos platos de verduras o ensaladas come al día?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='frutas_dia',
            field=_porciones('¿Cuántas frutas come cada día?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='panes_dia',
            field=_porciones('¿Cuántos panes (marraqueta, hallulla) come al día?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='lacteos_dia',
            field=_porciones('¿Cuántos productos lácteos come al día?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='jugos_gaseosas_dia',
            field=_porciones('¿Cuántos vasos al día toma de jugos y/o bebidas gaseosas?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='bebidas_energeticas_dia',
            field=_porciones('¿Cuántos vasos al día toma de bebidas energéticas?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='pescado_semana',
            field=_semanal('¿Cuántas veces a la semana come pescado?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='legumbres_semana',
            field=_semanal('¿Cuántas veces a la semana come legumbres?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='carnes_semana',
            field=_semanal('¿Cuántas veces a la semana come carnes (pollo, carne, cerdo)?'),
        ),
        migrations.AlterField(
            model_name='habitosdevida', name='golosinas_semana',
            field=_semanal('¿Cuántas veces a la semana come pasteles, dulces, chocolates, '
                           'golosinas, helados o snacks salados?'),
        ),
        migrations.AddField(
            model_name='habitosdevida', name='tabaco_frecuencia',
            field=_semanal('¿Fuma tabaco o cigarrillo?'),
        ),
        migrations.AddField(
            model_name='habitosdevida', name='marihuana_frecuencia',
            field=_semanal('¿Fuma marihuana?'),
        ),
        migrations.AddField(
            model_name='habitosdevida', name='alcohol_frecuencia',
            field=_semanal('¿Consume bebidas alcohólicas?'),
        ),
    ]
