"""
Fase 40B-1: unicidad (participante, ronda) en las secciones de la encuesta.

1. Verifica, en SOLO LECTURA, que no haya dos filas de una misma sección para
   la misma participante y ronda. Si las hay en alguna de las tablas a
   proteger, SE DETIENE con un informe (conteos, sin datos) y no cambia nada:
   ningún duplicado se elige, corrige ni borra automáticamente.
2. Si no hay, crea un índice único (participante_id, ronda) en cada tabla.

`encuestas_habitosdevida` queda FUERA a propósito: la base de desarrollo tiene
un par duplicado (ronda abierta, dos filas con contenido distinto) que debe
resolver una persona. Su índice irá en una migración posterior, cuando eso se
decida (informe 40B-1).

Los índices se crean con SQL y no en el Meta de los modelos, para no modificar
apps/encuestas/models.py (lo leen la limpieza histórica y las pruebas de las
Fases 35-39). Django no los conoce en su estado; cuando la 40B-2 cambie ese
archivo podrán pasar al Meta con SeparateDatabaseAndState.
"""
from django.db import migrations

TABLAS = [
    'encuestas_mrs', 'encuestas_segmentoempa', 'encuestas_conocimientosistema',
    'encuestas_evaluaciontrabajo', 'encuestas_tareascuidado', 'encuestas_actividadfisica',
]
FUERA = ['encuestas_habitosdevida']


def _duplicados(cursor, tabla):
    cursor.execute(f'SELECT count(*) FROM (SELECT 1 FROM {tabla} GROUP BY participante_id, ronda '
                   f'HAVING count(*) > 1) d')
    return cursor.fetchone()[0]


def verificar(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        encontrados = {t: _duplicados(cursor, t) for t in TABLAS}
        fuera = {t: _duplicados(cursor, t) for t in FUERA}
    if any(encontrados.values()):
        raise RuntimeError(
            'Fase 40B-1: hay secciones duplicadas por (participante, ronda); no se crean las '
            f'restricciones y no se modificó nada. Pares duplicados por tabla: {encontrados}. '
            'Resolverlos manualmente (con respaldo) antes de volver a migrar.')
    print(f'\n  Unicidad 40B-1: sin duplicados en {len(TABLAS)} tablas; '
          f'fuera de la restricción (pares duplicados): {fuera}')


def _sql(tabla):
    return f'CREATE UNIQUE INDEX {tabla}_participante_ronda_uniq ON {tabla} (participante_id, ronda)'


class Migration(migrations.Migration):

    dependencies = [
        ('rondas', '0002_retrocarga'),
        ('encuestas', '0019_ultima_finalizacion'),
    ]

    operations = [
        migrations.RunPython(verificar, migrations.RunPython.noop),
        *[migrations.RunSQL(_sql(t), f'DROP INDEX IF EXISTS {t}_participante_ronda_uniq') for t in TABLAS],
    ]
