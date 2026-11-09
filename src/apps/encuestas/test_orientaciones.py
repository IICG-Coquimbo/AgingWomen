"""
Pruebas de la Fase 40D: orientaciones educativas personalizadas por respuestas MRS.
docker compose exec web python manage.py test apps.encuestas.test_orientaciones
"""
import json
import re

from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext

from apps.rondas.test_40b3 import ITEMS, bloque_mrs
from apps.rondas.test_40c import Base40C

from . import orientaciones as O

# El runner de Django fuerza DEBUG=False; el modo borrador exige DEBUG=True (piloto local).
ACTIVAS = dict(ORIENTACIONES_HABILITADAS=True, ORIENTACIONES_PERMITIR_BORRADOR=True, DEBUG=True)


def respuestas(**valores):
    base = {i: 0 for i in ITEMS}
    base.update({f'pregunta_{k[1:]}': v for k, v in valores.items()})
    return base


def seccion(html):
    m = re.search(r'<section class="tarjeta orientaciones".*?</section>', html, re.S)
    return m.group(0) if m else ''


def ids_principales(html):
    sec = seccion(html)
    corte = min([i for i in (sec.find('data-otras-orientaciones'), sec.find('data-biblioteca-orientaciones')) if i >= 0])
    return re.findall(r'data-orientacion="(O-\d{2})"', sec[:corte])


class Base40D(Base40C):
    def tablero(self):
        self.client.force_login(self.usuaria)
        return self.client.get('/mi-tablero/').content.decode()


class ActivacionTest(Base40D):
    def test_apagadas_por_defecto_aunque_haya_datos(self):
        self.cerrar(1, respuestas(p1=4))
        self.assertEqual(seccion(self.tablero()), '')

    @override_settings(ORIENTACIONES_HABILITADAS=True, ORIENTACIONES_PERMITIR_BORRADOR=True, DEBUG=False)
    def test_borrador_nunca_se_muestra_con_debug_false_produccion(self):
        self.cerrar(1, respuestas(p1=4))
        self.assertFalse(O.habilitadas())
        self.assertEqual(seccion(self.tablero()), '')

    @override_settings(ORIENTACIONES_HABILITADAS=False, ORIENTACIONES_PERMITIR_BORRADOR=True, DEBUG=True)
    def test_permitir_borrador_sin_habilitar_no_muestra(self):
        self.cerrar(1, respuestas(p1=4))
        self.assertEqual(seccion(self.tablero()), '')

    def test_valores_seguros_por_defecto_del_proyecto(self):
        from importlib import reload
        import os
        from unittest import mock
        import Encuesta_integral.settings as ajustes
        limpio = {k: v for k, v in os.environ.items()
                  if k not in ('ORIENTACIONES_HABILITADAS', 'ORIENTACIONES_PERMITIR_BORRADOR')}
        with mock.patch.dict(os.environ, limpio, clear=True):
            reload(ajustes)
            self.assertFalse(ajustes.ORIENTACIONES_HABILITADAS)
            self.assertFalse(ajustes.ORIENTACIONES_PERMITIR_BORRADOR)
        reload(ajustes)

    @override_settings(ORIENTACIONES_HABILITADAS=True, ORIENTACIONES_PERMITIR_BORRADOR=False, DEBUG=True)
    def test_borrador_no_validado_no_se_muestra_sin_permiso_expreso(self):
        self.assertNotEqual(O.catalogo()['estado'], O.ESTADO_APROBADO)
        self.cerrar(1, respuestas(p1=4))
        self.assertEqual(seccion(self.tablero()), '')

    @override_settings(**ACTIVAS)
    def test_aviso_permanente_sin_confirmaciones_y_marca_de_borrador(self):
        self.cerrar(1, respuestas(p1=4))
        sec = seccion(self.tablero())
        self.assertIn('data-aviso-orientaciones', sec)
        self.assertIn('no son un diagnóstico médico', sec)
        self.assertIn('no reemplazan', sec)
        self.assertIn('SAMU 131', sec)
        self.assertIn('data-aviso-borrador', sec)
        self.assertIn('Versión de prueba, no validada clínicamente.', sec)
        self.assertLess(sec.index('data-aviso-borrador'), sec.index('data-orientacion='))
        self.assertLess(sec.index('data-aviso-orientaciones'), sec.index('data-orientacion='))
        for prohibido in ('<input', '<form', 'checkbox', '<dialog', 'confirm('):
            self.assertNotIn(prohibido, sec)


@override_settings(**ACTIVAS)
class ReglasTest(Base40D):
    def test_r1_ronda_abierta_no_personaliza(self):
        self.sync(bloque_mrs(respuestas(p1=4, p2=4), parcial=False), ronda=1)
        html = self.tablero()
        self.assertIn('data-motivo-orientaciones="sin_rondas"', html)
        self.assertEqual(ids_principales(html), [])

    def test_r1_ultima_cerrada_no_verificable_no_usa_una_anterior(self):
        self.cerrar(1, respuestas(p1=4))
        self.cerrar_antigua(2, respuestas(p3=3))
        html = self.tablero()
        self.assertIn('data-motivo-orientaciones="sin_ronda_verificable"', html)
        self.assertEqual(ids_principales(html), [])

    def test_r2_r3_orden_maximo_y_motivo(self):
        self.cerrar(1, respuestas(p1=3, p3=4, p10=4, p11=2, p4=1))
        html = self.tablero()
        self.assertEqual(ids_principales(html), ['O-03', 'O-10', 'O-01'])
        otras = seccion(html).split('data-otras-orientaciones')[1].split('data-biblioteca-orientaciones')[0]
        self.assertEqual(re.findall(r'data-orientacion="(O-\d{2})"', otras), ['O-11'])
        self.assertIn('Aparece porque en tu ronda 1 marcaste esta molestia con intensidad 4 de 4.', html)
        self.assertNotIn('data-orientacion="O-04"', html.split('data-biblioteca-orientaciones')[0])

    def test_r3_determinista(self):
        self.cerrar(1, respuestas(p2=2, p6=2, p7=2, p9=2))
        primera, segunda = self.tablero(), self.tablero()
        self.assertEqual(seccion(primera), seccion(segunda))
        self.assertEqual(ids_principales(primera), ['O-02', 'O-06', 'O-07'])

    def test_r4_mensaje_de_apoyo_primero_y_sin_repetir(self):
        self.cerrar(1, respuestas(p5=4, p1=4, p2=4, p3=4))
        html = self.tablero()
        sec = seccion(html)
        apoyo = sec.split('data-mensaje-apoyo')[1]
        self.assertTrue(apoyo.lstrip('>').lstrip().startswith('<article class="orientacion" data-orientacion="O-05"'))
        self.assertIn('*4141', apoyo)
        self.assertEqual(ids_principales(html), ['O-05', 'O-01', 'O-02', 'O-03'])   # O-05 = apoyo
        self.assertEqual(sec.split('data-biblioteca-orientaciones')[0].count('data-orientacion="O-05"'), 1)

    def test_r6_sin_destacadas_y_el_total_no_decide(self):
        self.cerrar(1, {i: 1 for i in ITEMS})            # 11 puntos, ninguna respuesta >= 2
        html = self.tablero()
        self.assertIn('data-motivo-orientaciones="sin_destacadas"', html)
        self.assertEqual(ids_principales(html), [])
        self.assertIn('data-biblioteca-orientaciones', html)

    def test_usa_la_ultima_ronda_y_no_compara_rondas(self):
        self.cerrar(1, respuestas(p1=4))
        self.cerrar(2, respuestas(p11=3))
        html = self.tablero()
        self.assertEqual(ids_principales(html), ['O-11'])
        self.assertIn('en tu ronda 2', html)
        for palabra in ('mejoraste', 'empeoraste', 'empeoró', 'mejoró', 'sigue igual', 'se ha mantenido', 'Severa', 'Moderada',
                        'Leve', 'severidad', 'grupo de caracterización', 'segmento'):
            self.assertNotIn(palabra, seccion(html), palabra)

    def test_cada_participante_ve_su_seleccion_y_no_escribe_nada(self):
        self.cerrar(1, respuestas(p10=4))
        with CaptureQueriesContext(connection) as consultas:
            html = self.tablero()
        escrituras = [q['sql'] for q in consultas.captured_queries
                      if re.match(r'\s*(INSERT|UPDATE|DELETE)', q['sql'], re.I)
                      and 'django_session' not in q['sql'] and 'usuarios_usuario' not in q['sql']]
        self.assertEqual(escrituras, [])
        self.assertEqual(ids_principales(html), ['O-10'])
        self.client.force_login(self.prof)
        ficha = self.client.get(f'/profesional/paciente/{self.ficha().pk}/').content.decode()
        self.assertEqual(seccion(ficha), '')   # la 40D solo agrega la sección al tablero de la participante


class CatalogoTest(Base40D):
    def test_catalogo_cumple_c1_a_c8(self):
        cat = O.catalogo()
        self.assertEqual(cat['estado'], 'borrador_no_validado')
        self.assertEqual(sorted(o['pregunta'] for o in cat['orientaciones']), sorted(ITEMS))
        for o in cat['orientaciones']:
            consulta = o['cuando_consultar']['items']
            self.assertTrue(consulta, o['id'])                                        # C-2
            self.assertTrue(any(it['fuentes'] for it in consulta), o['id'])
            self.assertTrue(o['fuentes_usadas'], o['id'])                              # C-6
            self.assertTrue(o['senales_alerta']['items'] or o['senales_alerta']['sin_alertas_texto'])
        for fid, f in cat['fuentes'].items():
            self.assertTrue(f['url'].startswith('https://'), fid)
            self.assertEqual(f['fecha_consulta'], '2026-11-06', fid)
        texto = ' '.join(cat['aviso']['parrafos'])
        self.assertIn('no son un diagnóstico médico', texto)                          # C-1
        self.assertIn('no reemplazan', texto)
        contenido = json.dumps({k: cat[k] for k in ('aviso', 'orientaciones')}, ensure_ascii=False)
        for vetada in (r'usted tiene', r'padece', r'diagnóstico de', r'pronóstico', r'\bsuspenda\b',
                       r'\bsuspende\b', r'deje de tomar', r'deja de tomar', r'\d\s?mg\b', r'dosis', r'paracetamol',
                       r'grupo de caracterización', r'clúster', r'Severa', r'peligro', r'!', r'\*\*', r'\[F\d'):
            self.assertIsNone(re.search(vetada, contenido), vetada)                  # C-3, C-5, C-7
        self.assertIn('No lo suspendas por tu cuenta', contenido)                     # C-3: la advertencia sí está

    @override_settings(**ACTIVAS)
    def test_fuentes_visibles_en_cada_tarjeta(self):
        self.cerrar(1, respuestas(p2=3))
        sec = seccion(self.tablero())
        tarjeta = sec.split('data-orientacion="O-02"')[1].split('</article>')[0]
        self.assertIn('data-cuando-consultar', tarjeta)
        self.assertIn('data-senales-alerta', tarjeta)
        self.assertIn('https://www.nhs.uk/conditions/heart-palpitations/', tarjeta)
        self.assertIn('Consultada el 2026-11-06', tarjeta)
        # Las señales de alerta y «¿Cuándo consultar…?» no quedan dentro de un <details> (R-5).
        antes_fuentes = tarjeta.split('data-fuentes')[0]
        self.assertNotIn('<details>', antes_fuentes.split('data-cuando-consultar')[1])
