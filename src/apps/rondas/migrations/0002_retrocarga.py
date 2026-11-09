"""
Fase 40B-1: crea el registro de las rondas que ya existían, SIN INVENTAR NADA.

Por cada ficha (Identificacion):
- Rondas 1 a ronda_actual − 1 → CERRADA, origen RETROCARGA.
- Ronda ronda_actual → ABIERTA, origen RETROCARGA.

Lo que no se sabe queda nulo y marcado en `observaciones`:
- abierta_en y cerrada_en: NULL en todas (no hay fecha por ronda). La
  ultima_finalizacion_en de la ficha se copia como dato REFERENCIAL en la ronda
  ronda_actual − 1, sin usarla como fecha de cierre (40A, revisión correctiva §4).
- quién cerró: cerrada_por NULL y cerrada_por_rol DESCONOCIDO.
- versión del cuestionario: DESCONOCIDA_ANTERIOR_40B.
- características al cierre (trabajo, región…): no se reconstruyen con los
  valores actuales; instantánea no disponible.
- secciones presentes, rondas vacías, sin MRS y duplicados: se marcan; no se
  anula, corrige ni borra nada.

Solo lee las tablas de la encuesta. La reversa borra únicamente las filas
creadas aquí (origen RETROCARGA).
"""
from django.db import migrations

VERSION_DESCONOCIDA = 'DESCONOCIDA_ANTERIOR_40B'
SECCIONES = {
    'mrs': 'MRS', 'empa': 'SegmentoEMPA', 'conocimiento_sistema': 'ConocimientoSistema',
    'trabajo': 'EvaluacionTrabajo', 'tareas_cuidado': 'TareasCuidado',
    'habitos_de_vida': 'HabitosDeVida', 'actividad_fisica': 'ActividadFisica',
}
LIMITACIONES = [
    'fechas de apertura y cierre desconocidas',
    'quién cerró: desconocido',
    'versión del cuestionario desconocida',
    'características al cierre no reconstruibles (no se usan los valores actuales)',
    'MRS: los ceros por defecto no se distinguen de respuestas omitidas',
]


def retrocargar(apps, schema_editor):
    Identificacion = apps.get_model('encuestas', 'Identificacion')
    Ronda = apps.get_model('rondas', 'RondaEvaluacion')
    Evento = apps.get_model('rondas', 'EventoRonda')

    # (participante, ronda) → {tipo: cantidad de filas}
    presentes = {}
    for tipo, nombre in SECCIONES.items():
        modelo = apps.get_model('encuestas', nombre)
        for pid, ronda in modelo.objects.values_list('participante_id', 'ronda'):
            conteo = presentes.setdefault((pid, ronda), {})
            conteo[tipo] = conteo.get(tipo, 0) + 1

    resumen = {'fichas': 0, 'cerradas': 0, 'abiertas': 0, 'omitidas_ya_registradas': 0,
               'secciones_fuera_de_rango': 0, 'pares_duplicados': 0}
    for ident in Identificacion.objects.order_by('pk'):
        if Ronda.objects.filter(participante_id=ident.pk).exists():
            resumen['omitidas_ya_registradas'] += 1
            continue
        resumen['fichas'] += 1
        fuera = sorted(r for (pid, r) in presentes if pid == ident.pk and (r > ident.ronda_actual or r < 1))
        resumen['secciones_fuera_de_rango'] += len(fuera)
        for numero in range(1, ident.ronda_actual + 1):
            conteo = presentes.get((ident.pk, numero), {})
            duplicadas = sorted(t for t, n in conteo.items() if n > 1)
            resumen['pares_duplicados'] += len(duplicadas)
            abierta = numero == ident.ronda_actual
            obs = {
                'secciones_presentes': sorted(conteo),
                'vacia': not conteo,
                'sin_mrs': 'mrs' not in conteo,
                'secciones_duplicadas': duplicadas,
                'instantanea_disponible': False,
                'limitaciones': LIMITACIONES,
            }
            if numero == ident.ronda_actual - 1:
                obs['ultima_finalizacion_registrada_referencial'] = (
                    ident.ultima_finalizacion_en.isoformat() if ident.ultima_finalizacion_en else None)
            if abierta and fuera:
                obs['secciones_con_ronda_fuera_de_rango'] = fuera
            ronda = Ronda.objects.create(
                participante_id=ident.pk, numero=numero,
                estado='ABIERTA' if abierta else 'CERRADA', origen='RETROCARGA',
                abierta_en=None, cerrada_en=None, cerrada_por=None,
                cerrada_por_rol='' if abierta else 'DESCONOCIDO',
                version_cuestionario=VERSION_DESCONOCIDA, observaciones=obs,
            )
            Evento.objects.create(ronda=ronda, tipo='RETROCARGA',
                                  datos={'migracion': 'rondas.0002_retrocarga', 'estado': ronda.estado})
            resumen['abiertas' if abierta else 'cerradas'] += 1
    print(f"\n  Retrocarga 40B-1: {resumen}")


def deshacer(apps, schema_editor):
    apps.get_model('rondas', 'RondaEvaluacion').objects.filter(origen='RETROCARGA').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('rondas', '0001_initial'),
        ('encuestas', '0019_ultima_finalizacion'),
    ]

    operations = [
        migrations.RunPython(retrocargar, deshacer),
    ]
