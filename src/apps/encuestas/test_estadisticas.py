"""Fase 40C-P: tablero estadístico profesional («Estadísticas generales»). Datos ficticios."""
import itertools
import re
from uuid import uuid4

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.rondas.models import EventoRonda, MRSAnterior40B2, OrigenRonda, RondaEvaluacion
from apps.rondas.pruebas_comunes import sincronizar_como_cliente
from apps.rondas.test_40b2 import _pasar_plazo
from apps.usuarios.models import Usuario

from apps.usuarios.models import ConsentimientoPresencial

from .estadisticas import UMBRAL, construir_estadisticas, proteger
from .models import MRS, Identificacion

URL = '/profesional/estadisticas/'
IDENT = {'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM', 'origen_procedencia': 'CL',
         'pueblo_originario_afro': 'NINGUNO', 'comuna': 'Santiago', 'region_residencia': '13'}


def rut(numero):
    s, m = 0, 2
    for d in reversed(str(numero)):
        s += int(d) * m
        m = 2 if m == 7 else m + 1
    dv = 11 - s % 11
    return f'{numero}-' + {11: '0', 10: 'K'}.get(dv, str(dv))


def mrs(valores, pareja='SI'):
    datos = dict(valores)
    if pareja:
        datos['tiene_pareja'] = pareja
    return {'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': False, 'datos': datos}


def items(somatica, psicologica, urogenital):
    """Reparte los puntos de cada dimensión en sus ítems (máx. 4 por ítem)."""
    v = {}
    for campos, total in ((range(1, 5), somatica), (range(5, 9), psicologica), (range(9, 12), urogenital)):
        for i in campos:
            v[f'pregunta_{i}'] = min(4, total)
            total -= v[f'pregunta_{i}']
        assert total == 0
    return v


def consentimiento_presencial_ficticio(ficha, profesional):
    return ConsentimientoPresencial.objects.create(
        rut_hash=ficha.rut_hash, version='prueba', folio_documento=f'PRUEBA-{ficha.pk}',
        verificacion=ConsentimientoPresencial.Verificacion.DOCUMENTO_FIRMADO, custodia='Archivo ficticio',
        registrado_por=profesional)


class BaseEst(TestCase):
    contador = itertools.count(10_000_000)

    def setUp(self):
        self.prof = Usuario.objects.create_user(rut='22.222.222-2', email='p@ficticio.cl',
                                                rol=Usuario.Rol.PROFESIONAL_SALUD)

    def usuaria(self, consentimiento=True):
        n = next(self.contador)
        u = Usuario.objects.create_user(rut=rut(n), email=f'u{n}@ficticio.cl')
        if consentimiento:
            u.consentimiento_aceptado_en = timezone.now()
            u.save(update_fields=['consentimiento_aceptado_en'])
        return u

    def ronda(self, u, valores, ronda=1, dias=1, pareja='SI', trabaja=True, finalizar=True):
        secciones = [mrs(valores, pareja)]
        if dias:
            secciones.append({'tipo': 'actividad_fisica', 'uuid_local': str(uuid4()), 'parcial': False,
                              'datos': {'dias_ejercicio_semana': dias}})
        p = {'protocolo': 2, 'ronda': ronda, 'secciones': secciones,
             'identificacion': {'uuid_local': str(uuid4()), 'datos': dict(IDENT, trabaja_actualmente=trabaja)}}
        if finalizar:
            p.update(finalizar=True, id_cierre=str(uuid4()))
        if ronda > 1:
            _pasar_plazo()
        res = sincronizar_como_cliente(u, p)
        self.assertTrue(res['ok'], res)

    def participante(self, total=(4, 4, 4), **kw):
        u = self.usuaria()
        self.ronda(u, items(*total), **kw)
        return u

    def presencial(self, total):
        """Registro presencial sin cuenta: la cuenta temporal con la que se respondió deja de existir."""
        u = self.participante(total)
        ficha = Identificacion.objects.get(usuario=u)
        Identificacion.objects.filter(pk=ficha.pk).update(usuario=None)
        u.delete()
        return Identificacion.objects.get(pk=ficha.pk)

    def ver(self, usuario=None):
        self.client.force_login(usuario or self.prof)
        return self.client.get(URL)


class AccesoTest(BaseEst):
    def test_solo_profesionales(self):
        self.assertEqual(self.client.get(URL).status_code, 302)                    # anónima -> login
        self.assertEqual(self.ver(self.usuaria()).status_code, 403)                # usuaria común
        resp = self.ver()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Cache-Control'], 'no-store')
        self.assertContains(resp, 'Estadísticas generales')

    def test_sin_datos_suficientes_no_publica_cifras(self):
        for _ in range(UMBRAL - 1):
            self.participante()
        resp = self.ver()
        self.assertContains(resp, 'data-sin-datos')
        self.assertNotContains(resp, 'data-indicador')
        self.assertIsNone(resp.context['est']['n'])
        self.assertNotContains(resp, 'data-distribucion="mrs"')


class PoblacionTest(BaseEst):
    def test_poblacion_calculos_y_una_ronda_por_mujer(self):
        # 5 participantes con una ronda: totales 6, 9, 12, 15, 30.
        for t in ((2, 2, 2), (3, 3, 3), (4, 4, 4), (5, 5, 5), (10, 10, 10)):
            self.participante(t)
        # Una con dos rondas cerradas: cuenta una vez, con la última (total 3).
        doble = self.participante((10, 10, 10))
        self.ronda(doble, items(1, 1, 1), ronda=2)
        # Excluidas:
        retirada = self.participante((16, 16, 12))                               # consentimiento retirado
        Usuario.objects.filter(pk=retirada.pk).update(consentimiento_aceptado_en=None)
        sin_cuenta = self.presencial((16, 16, 12))                                 # presencial sin consentimiento
        con_presencial = self.presencial((16, 16, 12))                             # presencial con consentimiento (E2)
        consentimiento_presencial_ficticio(con_presencial, self.prof)
        abierta = self.usuaria()                                                   # ronda abierta (provisional)
        self.ronda(abierta, items(16, 16, 12), finalizar=False)
        antigua = self.participante((16, 16, 12))                                  # cerrada no verificable
        MRSAnterior40B2.objects.create(mrs=MRS.objects.get(participante__usuario=antigua),
                                       items_confirmados=[])
        MRS.objects.filter(participante__usuario=antigua).update(pregunta_1=0)

        self.assertFalse(sin_cuenta.usuario_id or con_presencial.usuario_id)
        est = construir_estadisticas()
        self.assertEqual(est['n'], 7)
        self.assertEqual(est['rondas_verificables'], 8)
        totales = [6, 9, 12, 15, 30, 3, 44]
        self.assertEqual(est['promedio_total'], f'{sum(totales) / 7:.1f}'.replace('.', ','))   # 17,0
        self.assertEqual(est['mediana_total'], '12,0')
        self.assertEqual({d['clave']: d['promedio'] for d in est['dimensiones']},
                         {'somatica': '5,9', 'psicologica': '5,9', 'urogenital': '5,3'})
        excl = {e['clave']: e['n'] for e in est['exclusiones']}
        # 1 presencial, 1 sin consentimiento, 2 sin ronda verificable: se publican como «menos de 5».
        self.assertEqual(excl, {'presencial': None, 'sin_consentimiento': None, 'sin_ronda_verificable': None})
        # Las 6 incluidas tienen fecha de cierre verificable: 51 años al cierre (nacidas en 1975).
        edad = {f['clave']: f['n'] for f in est['dist_edad']['filas']}
        self.assertEqual(edad['50-54'], 7)
        self.assertEqual(est['dist_edad']['denominador'], 7)

    def test_ronda_sin_fecha_de_cierre_no_tiene_edad(self):
        for _ in range(UMBRAL):
            self.participante()
        RondaEvaluacion.objects.update(origen=OrigenRonda.RETROCARGA, cerrada_en=None, id_cierre=None)
        est = construir_estadisticas()
        self.assertEqual(est['n'], UMBRAL)          # siguen siendo resultados definitivos (regla 40B-3)
        edad = {f['clave']: f['n'] for f in est['dist_edad']['filas']}
        self.assertEqual(edad['sin_edad'], UMBRAL)
        self.assertEqual(edad['50-54'], 0)


class GruposTest(BaseEst):
    def test_grupos_b1_tamano_promedio_y_grupos_pequenos(self):
        # 5 en Grupo 2 (nivel de días 3+), 5 en Grupo 4, 2 en Grupo 1 y 1 sin grupo (sin actividad física).
        for _ in range(5):
            self.participante((2, 2, 2), dias=4)
        for _ in range(5):
            self.participante((4, 4, 4), dias=1, pareja='SI', trabaja=True)
        for _ in range(2):
            self.participante((16, 16, 12), dias=1, pareja='NO')
        self.participante((16, 16, 12), dias=None)
        resp = self.ver()
        est = resp.context['est']
        self.assertEqual(est['n'], 13)
        tabla = {g['clave']: (g['n'], g['promedio_mrs']) for g in est['tabla_grupos']}
        self.assertEqual(tabla['S3'], (5, '12,0'))
        # Grupo 1 (2) y sin grupo (1) suman 3 < 5: se oculta además la celda visible más pequeña
        # (Grupo 2, 5) para que no se deduzcan restando del total; su promedio tampoco se publica.
        ocultas = {f['clave'] for f in est['dist_grupos']['filas'] if f['oculta']}
        self.assertEqual(ocultas, {'S0', 'S1', 'sin_grupo'})
        self.assertEqual(tabla['S1'], (None, None))
        self.assertEqual(tabla['S0'], (None, None))
        self.assertEqual(tabla['S2'], (0, None))
        html = resp.content.decode()
        self.assertIn('Grupo 2 — Vida en movimiento', html)
        self.assertIn('Grupo 4 — Entre múltiples actividades', html)
        self.assertIn('No son categorías clínicas', html)
        self.assertIn('data-sin-grupo', html)
        visibles = [f['n'] for f in est['dist_grupos']['filas'] if not f['oculta']]
        self.assertGreaterEqual(est['n'] - sum(visibles), UMBRAL)


class ProteccionTest(TestCase):
    def test_umbral_y_supresion_complementaria(self):
        self.assertEqual(proteger({'a': 10, 'b': 7, 'c': 0}), set())
        self.assertEqual(proteger({'a': 10, 'b': 7, 'c': 1}), {'b', 'c'})       # una sola oculta no basta
        self.assertIsNone(proteger({'a': 1, 'b': 1, 'c': 1, 'd': 1, 'e': 1}))    # todas de 1: se deducirían
        self.assertIsNone(proteger({'a': 3}))

    def test_ninguna_celda_oculta_se_puede_deducir(self):
        for conteos in itertools.product(range(0, 8), repeat=4):
            c = dict(zip('abcd', conteos))
            ocultas = proteger(c)
            if not ocultas:
                continue
            suma = sum(c[k] for k in ocultas)
            self.assertGreaterEqual(len(ocultas), 2, c)
            self.assertGreaterEqual(suma, UMBRAL, c)
            self.assertGreater(suma, len(ocultas), c)
            self.assertTrue(all(c[k] > 0 for k in ocultas), c)


class PrivacidadTest(BaseEst):
    def test_sin_identificadores_y_solo_lectura(self):
        usuarias = [self.participante() for _ in range(UMBRAL)]
        antes = (MRS.objects.count(), RondaEvaluacion.objects.count(), EventoRonda.objects.count(),
                 list(Identificacion.objects.values_list('ronda_actual', flat=True)))
        with CaptureQueriesContext(connection) as q:
            html = self.ver().content.decode()
        escrituras = [x['sql'] for x in q.captured_queries
                      if re.match(r'\s*(INSERT|UPDATE|DELETE)', x['sql'], re.I)
                      and 'django_session' not in x['sql'] and 'last_login' not in x['sql']]
        self.assertEqual(escrituras, [])
        self.assertEqual(antes, (MRS.objects.count(), RondaEvaluacion.objects.count(), EventoRonda.objects.count(),
                                 list(Identificacion.objects.values_list('ronda_actual', flat=True))))
        for u in usuarias:
            self.assertNotIn(u.email, html)
            self.assertNotIn(u.rut_hash, html)
        self.assertNotIn('/profesional/paciente/', html)
        self.assertNotIn('pregunta_', html)
        self.assertNotIn('1975', html)
