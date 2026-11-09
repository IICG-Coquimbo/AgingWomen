"""
Pruebas de la Fase 40B-3: visualización segura del resultado MRS.

La numeración sigue la lista mínima del encargo 40B-3 (§5). Corren en PostgreSQL:
docker compose exec web python manage.py test apps.rondas.test_40b3
"""
import json
import re
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.encuestas.esquema import construir_esquema
from apps.encuestas.models import MRS, Identificacion
from apps.encuestas.sync import sincronizar_payload
from apps.usuarios.models import Usuario

from . import resultado_mrs as R
from .cierre import puntaje_mrs_definitivo
from .models import EstadoRonda, MRSAnterior40B2, RondaEvaluacion

IDENT = {
    'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
    'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
    'comuna': 'Santiago', 'region_residencia': '13',
}
ITEMS = [f'pregunta_{i}' for i in range(1, 12)]
CATEGORIAS = [t for _, t in MRS.SEVERIDAD_TOTAL]   # 'Sin síntomas o muy leves', 'Leve', 'Moderada', 'Severa'
SRC = Path(settings.BASE_DIR)


def bloque_mrs(datos, uuid_local=None, parcial=True, confirmados=None):
    b = {'tipo': 'mrs', 'uuid_local': uuid_local or str(uuid4()), 'parcial': parcial, 'datos': dict(datos)}
    if confirmados is not None:
        b['confirmados'] = confirmados
    return b


def payload(secciones=(), ronda=1, finalizar=False):
    p = {'protocolo': 2, 'identificacion': {'uuid_local': str(uuid4()), 'datos': dict(IDENT)},
         'secciones': list(secciones), 'ronda': ronda}
    if finalizar:
        p['finalizar'] = True
        p['id_cierre'] = str(uuid4())
    return p


def resultados_en(html):
    """Lista de (estado, texto) de los resultados MRS de una página, en orden."""
    return [(e, re.sub(r'\s+', ' ', t).strip())
            for e, t in re.findall(r'data-resultado-mrs="([a-z_]+)">([^<]*)<', html)]


class Base(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.prof = Usuario.objects.create_user(rut='22.222.222-2', email='p@e.cl',
                                                rol=Usuario.Rol.PROFESIONAL_SALUD)

    def ficha(self):
        return Identificacion.objects.get(usuario=self.usuaria)

    def sync(self, *bloques, ronda=1, finalizar=False):
        res = sincronizar_payload(self.usuaria, payload(bloques, ronda=ronda, finalizar=finalizar))
        self.assertTrue(res['ok'], res)
        return res

    def cerrar_ronda_1(self, valores):
        self.sync(bloque_mrs(valores, parcial=False), finalizar=True)
        return MRS.objects.get(participante=self.ficha(), ronda=1)

    def mrs_anterior_cerrado(self, valores, confirmados=()):
        """
        Un MRS como los de antes de la 40B-2: se guardó con ceros que nadie eligió y la
        ronda se cerró por la vía antigua (el registro lo cierra la señal, sin validar).
        """
        self.sync(bloque_mrs(valores))
        fila = MRS.objects.get(participante=self.ficha(), ronda=1)
        MRSAnterior40B2.objects.create(mrs=fila, items_confirmados=list(confirmados))
        ficha = self.ficha()
        ficha.ronda_actual = 2
        ficha.save()   # la señal de la 40B-1 cierra la ronda 1 en el registro (vía antigua)
        self.assertEqual(RondaEvaluacion.objects.get(participante=ficha, numero=1).estado, EstadoRonda.CERRADA)
        return MRS.objects.get(pk=fila.pk)

    def paginas(self):
        self.client.force_login(self.usuaria)
        tablero = self.client.get('/mi-tablero/').content.decode()
        self.client.force_login(self.prof)
        ficha = self.client.get(f'/profesional/paciente/{self.ficha().pk}/').content.decode()
        return tablero, ficha


# 1 -------------------------------------------------------------------------------------
class CerradaVerificableTest(Base):
    def test_1_ronda_cerrada_verificable_muestra_el_puntaje_definitivo(self):
        valores = dict({i: 2 for i in ITEMS}, pregunta_1=0)          # el 0 lo eligió la persona
        fila = self.cerrar_ronda_1(valores)
        r = R.resultado_mrs(fila)
        self.assertEqual((r.estado, r.puntaje, r.suma), (R.DEFINITIVO, 20, None))
        self.assertTrue(r.es_definitivo)
        self.assertEqual(r.texto, 'Puntaje MRS: 20 de 44')
        self.assertEqual(puntaje_mrs_definitivo(fila), 20)
        tablero, ficha = self.paginas()
        self.assertIn(('definitivo', 'Puntaje MRS: 20 de 44'), resultados_en(tablero))
        self.assertIn(('definitivo', 'Puntaje MRS: 20 de 44'), resultados_en(ficha))

    def test_1b_ceros_antiguos_confirmados_antes_de_cerrar_si_son_definitivos(self):
        fila = self.mrs_anterior_cerrado(dict({i: 0 for i in ITEMS}, pregunta_1=3), confirmados=ITEMS)
        self.assertEqual((R.resultado_mrs(fila).estado, R.resultado_mrs(fila).puntaje), (R.DEFINITIVO, 3))


# 2 -------------------------------------------------------------------------------------
class HistoricaNoVerificableTest(Base):
    def test_2_ronda_cerrada_con_ceros_anteriores_sin_confirmar(self):
        valores = dict({i: 0 for i in ITEMS}, pregunta_1=3, pregunta_2=4)   # 9 ceros sin confirmar
        fila = self.mrs_anterior_cerrado(valores, confirmados=['pregunta_3'])
        self.assertEqual(fila.puntaje_total, 7)                 # la suma cruda existe…
        r = R.resultado_mrs(fila)
        self.assertEqual(r.estado, R.NO_VERIFICABLE)
        self.assertIsNone(r.puntaje)                            # …pero no se presenta como resultado
        self.assertIsNone(r.suma)
        self.assertEqual(r.ceros_sin_confirmar, 8)
        self.assertEqual(r.texto, 'Resultado histórico no verificable')
        self.assertIsNone(puntaje_mrs_definitivo(fila))
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            self.assertIn(('no_verificable', 'Resultado histórico no verificable'), resultados_en(html))
            self.assertNotIn('Puntaje MRS: 7', html)
            self.assertNotIn(': 7 de 44', html)
        # Nada se reconstruye ni se convierte: los ceros antiguos siguen siendo 0 (no nulos).
        fila.refresh_from_db()
        self.assertEqual({i: getattr(fila, i) for i in ITEMS}, valores)
        self.assertEqual(MRSAnterior40B2.objects.get(mrs=fila).items_confirmados, ['pregunta_3'])

    def test_2b_registro_de_ronda_que_no_dice_cerrada_tampoco_es_definitivo(self):
        fila = self.cerrar_ronda_1({i: 1 for i in ITEMS})
        RondaEvaluacion.objects.filter(participante=self.ficha(), numero=1).update(estado=EstadoRonda.ANULADA)
        self.assertEqual(R.resultado_mrs(fila).estado, R.NO_VERIFICABLE)
        self.assertIsNone(puntaje_mrs_definitivo(fila))

    def test_2c_ronda_cerrada_a_la_que_le_faltan_items_no_muestra_suma(self):
        self.sync(bloque_mrs({'pregunta_1': 2}))
        ficha = self.ficha()
        ficha.ronda_actual = 2
        ficha.save()                                            # cierre antiguo, sin validar
        r = R.resultado_mrs(MRS.objects.get(participante=ficha, ronda=1))
        self.assertEqual((r.estado, r.puntaje, r.suma), (R.INCOMPLETO, None, None))
        self.assertEqual(r.texto, 'Resultado incompleto: 1 de 11 preguntas respondidas')


# 3 y 4 ---------------------------------------------------------------------------------
class RondaAbiertaTest(Base):
    def test_3_ronda_abierta_con_mrs_parcial_nunca_es_definitiva(self):
        self.sync(bloque_mrs({'pregunta_1': 0, 'pregunta_2': 3}))
        fila = MRS.objects.get()
        r = R.resultado_mrs(fila)
        self.assertEqual((r.estado, r.puntaje, r.suma, r.respondidas), (R.PARCIAL, None, 3, 2))
        self.assertFalse(r.es_definitivo)
        self.assertEqual(r.texto, 'Suma parcial: 3 (2 de 11 preguntas respondidas; la ronda no está cerrada)')
        self.assertIsNone(puntaje_mrs_definitivo(fila))
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            self.assertEqual([e for e, _ in resultados_en(html)], ['parcial'])

    def test_3b_ronda_abierta_con_ceros_antiguos_los_cuenta_como_sin_responder(self):
        self.sync(bloque_mrs(dict({i: 0 for i in ITEMS}, pregunta_1=3)))
        fila = MRS.objects.get()
        MRSAnterior40B2.objects.create(mrs=fila)
        r = R.resultado_mrs(fila)
        self.assertEqual((r.estado, r.respondidas, r.suma, r.ceros_sin_confirmar), (R.PARCIAL, 1, 3, 10))

    def test_4_ronda_abierta_con_mrs_completo_sigue_provisional(self):
        self.sync(bloque_mrs({i: 2 for i in ITEMS}, parcial=False))
        fila = MRS.objects.get()
        self.assertEqual(fila.puntaje_total, 22)
        r = R.resultado_mrs(fila)
        self.assertEqual((r.estado, r.puntaje, r.suma), (R.PROVISIONAL, None, 22))
        self.assertEqual(r.texto, 'Suma provisional: 22 de 44 (la ronda no está cerrada)')
        self.assertIsNone(puntaje_mrs_definitivo(fila))
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            self.assertIn(('provisional', 'Suma provisional: 22 de 44 (la ronda no está cerrada)'),
                          resultados_en(html))
            self.assertNotIn('Puntaje MRS: 22', html)


# 5 -------------------------------------------------------------------------------------
class ConsistenciaTest(Base):
    def test_5_tablero_y_ficha_muestran_lo_mismo_en_cada_ronda(self):
        # Ronda 1 cerrada y verificable; ronda 2 abierta y parcial.
        self.cerrar_ronda_1({i: 1 for i in ITEMS})
        from .test_40b2 import _pasar_plazo
        _pasar_plazo()
        self.sync(bloque_mrs({'pregunta_1': 4}), ronda=2)
        tablero, ficha = self.paginas()
        self.assertEqual(resultados_en(tablero), resultados_en(ficha))
        self.assertEqual(resultados_en(tablero), [
            ('parcial', 'Suma parcial: 4 (1 de 11 preguntas respondidas; la ronda no está cerrada)'),
            ('definitivo', 'Puntaje MRS: 11 de 44'),
        ])

    def test_5b_tambien_coinciden_con_un_resultado_historico_no_verificable(self):
        self.mrs_anterior_cerrado(dict({i: 0 for i in ITEMS}, pregunta_1=2))
        tablero, ficha = self.paginas()
        self.assertEqual(resultados_en(tablero), resultados_en(ficha))
        self.assertEqual(resultados_en(tablero), [('no_verificable', 'Resultado histórico no verificable')])

    def test_5c_ninguna_plantilla_ni_vista_lee_el_puntaje_por_su_cuenta(self):
        # La única fuente para presentar el resultado es apps.rondas.resultado_mrs.
        plantillas = [p for p in (SRC / 'templates').rglob('*.html')]
        self.assertTrue(plantillas)
        for p in plantillas:
            self.assertNotIn('puntaje_total', p.read_text(encoding='utf-8'), p.name)
        for p in (SRC / 'apps').rglob('*.py'):
            if 'migrations' in p.parts or p.name.startswith('test') or p.name in ('models.py', 'resultado_mrs.py'):
                continue
            self.assertNotIn('.puntaje_total', p.read_text(encoding='utf-8'), str(p.relative_to(SRC)))

    def test_5d_las_api_no_entregan_puntajes(self):
        self.cerrar_ronda_1({i: 1 for i in ITEMS})
        self.client.force_login(self.usuaria)
        for url in ('/api/estado/', '/api/ronda-actual/', '/api/esquema/'):
            contenido = self.client.get(url).content.decode()
            self.assertNotIn('puntaje', contenido.lower(), url)


# 6 -------------------------------------------------------------------------------------
class SinSeveridadTest(Base):
    def test_6_no_se_muestran_categorias_de_severidad(self):
        self.cerrar_ronda_1({i: 4 for i in ITEMS})                # 44 puntos: antes «Severa»
        from .test_40b2 import _pasar_plazo
        _pasar_plazo()
        self.sync(bloque_mrs({i: 1 for i in ITEMS}, parcial=False), ronda=2)   # 11: antes «Moderada»
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            for categoria in CATEGORIAS + ['Severidad', 'severidad']:
                self.assertNotIn(categoria, html, categoria)
        for rol in (Usuario.Rol.USUARIA_COMUN, Usuario.Rol.PROFESIONAL_SALUD):
            esquema = json.dumps(construir_esquema(rol), ensure_ascii=False)
            # Los cortes del total ya no se publican («Leve» puede seguir siendo la opción de
            # respuesta de otra pregunta, que no es una categoría del puntaje MRS).
            self.assertNotIn('mrs_severidad', esquema)
            self.assertNotIn('"hasta"', esquema)
            self.assertNotIn('Sin síntomas o muy leves', esquema)
        js = (SRC / 'static' / 'js' / 'encuesta.js').read_text(encoding='utf-8')
        self.assertNotIn('mrs_severidad', js)
        self.assertNotIn("'Severidad: '", js)

    def test_6b_los_cortes_historicos_siguen_intactos(self):
        # No se modifican los cortes que usaron las Fases 34-39 (también los protege la 40B-0).
        self.assertEqual(MRS.SEVERIDAD_TOTAL, ((4, 'Sin síntomas o muy leves'), (8, 'Leve'),
                                               (15, 'Moderada'), (44, 'Severa')))


# 7 -------------------------------------------------------------------------------------
class IntegridadTest(Base):
    def test_7_presentar_el_resultado_no_escribe_nada(self):
        fila = self.mrs_anterior_cerrado(dict({i: 0 for i in ITEMS}, pregunta_1=3))
        antes = list(MRS.objects.values())
        marcas = list(MRSAnterior40B2.objects.values('mrs_id', 'items_confirmados', 'confirmado_en'))
        self.client.force_login(self.prof)
        with CaptureQueriesContext(connection) as consultas:
            R.resultado_mrs(fila)
            puntaje_mrs_definitivo(fila)
            self.client.get(f'/profesional/paciente/{self.ficha().pk}/')
        escrituras = [q['sql'] for q in consultas.captured_queries
                      if re.match(r'\s*(INSERT|UPDATE|DELETE)', q['sql'], re.I)
                      and 'django_session' not in q['sql'] and 'usuarios_usuario' not in q['sql']]
        self.assertEqual(escrituras, [])
        self.assertEqual(list(MRS.objects.values()), antes)
        self.assertEqual(list(MRSAnterior40B2.objects.values('mrs_id', 'items_confirmados', 'confirmado_en')), marcas)
