# Fase 3 — EMPA y Registro de Talla.
#
# El consumo de alcohol y tabaco sale del EMPA: pasa a la sección "Hábitos de
# vida" (regla de la profesora). Los campos se recrean allí en la Fase 4.
#
# La visibilidad/obligatoriedad por rol (mamografía, PAP, VDRL, riesgo CV, talla
# máxima ocultos para la usuaria común) se maneja en `campos_por_rol.py`, no en
# el esquema de base de datos: no genera operaciones de migración.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('encuestas', '0008_mrs_complementario'),
    ]

    operations = [
        migrations.RemoveField(model_name='segmentoempa', name='consumo_alcohol'),
        migrations.RemoveField(model_name='segmentoempa', name='consumo_tabaco'),
    ]
