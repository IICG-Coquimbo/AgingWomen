"""
Fase 40B-1: verificación de SOLO LECTURA del registro de rondas.

    python manage.py verificar_rondas            # resumen y problemas
    python manage.py verificar_rondas --json     # lo mismo, en JSON

Solo informa conteos e identificadores internos de ficha; nunca respuestas ni
datos personales. Termina con código 1 si alguna invariante falla.
"""
import json

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Count

from apps.encuestas.models import Identificacion
from apps.encuestas.sync import SECCIONES

from ...models import EstadoRonda, EventoRonda, OrigenRonda, RondaEvaluacion, TipoEventoRonda


def verificar():
    problemas = []
    fichas = list(Identificacion.objects.values_list('id', 'ronda_actual'))
    rondas = {}
    for r in RondaEvaluacion.objects.values('participante_id', 'numero', 'estado', 'origen',
                                            'abierta_en', 'cerrada_en'):
        rondas.setdefault(r['participante_id'], []).append(r)

    for pid, actual in fichas:
        propias = rondas.get(pid, [])
        abiertas = [r for r in propias if r['estado'] == EstadoRonda.ABIERTA]
        if len(abiertas) != 1:
            problemas.append({'ficha': pid, 'problema': 'rondas_abiertas', 'cantidad': len(abiertas)})
        elif abiertas[0]['numero'] != actual:
            problemas.append({'ficha': pid, 'problema': 'ronda_actual_distinta_de_la_abierta',
                              'ronda_actual': actual, 'ronda_abierta': abiertas[0]['numero']})
        numeros = sorted(r['numero'] for r in propias)
        if numeros != list(range(1, actual + 1)):
            problemas.append({'ficha': pid, 'problema': 'numeracion_incompleta',
                              'esperadas': actual, 'registradas': len(numeros)})
        for r in propias:
            if r['numero'] < actual and r['estado'] != EstadoRonda.CERRADA:
                problemas.append({'ficha': pid, 'problema': 'ronda_anterior_no_cerrada', 'numero': r['numero']})
            if r['origen'] == OrigenRonda.RETROCARGA and (r['abierta_en'] or r['cerrada_en']):
                problemas.append({'ficha': pid, 'problema': 'retrocarga_con_fecha', 'numero': r['numero']})

    sin_ficha = RondaEvaluacion.objects.exclude(participante_id__in=[f for f, _ in fichas]).count()
    if sin_ficha:
        problemas.append({'problema': 'rondas_sin_ficha', 'cantidad': sin_ficha})

    duplicados = {}
    for tipo, (modelo, _f) in SECCIONES.items():
        duplicados[tipo] = (modelo.objects.order_by().values('participante_id', 'ronda')
                            .annotate(n=Count('id')).filter(n__gt=1).count())

    with connection.cursor() as c:
        c.execute("SELECT indexname FROM pg_indexes WHERE indexname LIKE 'encuestas_%%_participante_ronda_uniq'")
        indices = sorted(f[0] for f in c.fetchall())

    cierres = EventoRonda.objects.filter(tipo=TipoEventoRonda.CIERRE)
    observados = [e.datos.get('completitud', {}) for e in cierres]
    resumen = {
        'fichas': len(fichas),
        'rondas': RondaEvaluacion.objects.count(),
        'por_estado': dict(RondaEvaluacion.objects.order_by().values_list('estado').annotate(n=Count('id'))),
        'por_origen': dict(RondaEvaluacion.objects.order_by().values_list('origen').annotate(n=Count('id'))),
        'retrocarga_vacias': RondaEvaluacion.objects.filter(origen=OrigenRonda.RETROCARGA,
                                                            observaciones__vacia=True).count(),
        'retrocarga_sin_mrs': RondaEvaluacion.objects.filter(origen=OrigenRonda.RETROCARGA,
                                                             observaciones__sin_mrs=True).count(),
        'cierres_registrados_desde_40B1': len(observados),
        'cierres_que_la_40B2_rechazaria': sum(1 for o in observados if o and not o.get('completa')),
        'eventos_incoherencia': EventoRonda.objects.filter(tipo=TipoEventoRonda.INCOHERENCIA).count(),
        'pares_duplicados_por_seccion': duplicados,
        'indices_unicos_de_seccion': indices,
    }
    return resumen, problemas


class Command(BaseCommand):
    help = 'Verifica (solo lectura) el registro de rondas de la Fase 40B-1.'

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true')

    def handle(self, *args, **opciones):
        with transaction.atomic():
            with connection.cursor() as c:
                c.execute('SET TRANSACTION READ ONLY')
            resumen, problemas = verificar()
        if opciones['json']:
            self.stdout.write(json.dumps({'resumen': resumen, 'problemas': problemas},
                                         ensure_ascii=False, indent=1, default=str))
        else:
            for k, v in resumen.items():
                self.stdout.write(f'{k}: {v}')
            self.stdout.write(f'problemas: {len(problemas)}')
            for p in problemas:
                self.stdout.write(f'  - {p}')
        if problemas:
            raise SystemExit(1)
