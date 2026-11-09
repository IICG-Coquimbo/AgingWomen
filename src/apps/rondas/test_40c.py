"""
Pruebas de la Fase 40C: tablero individual de resultados y evolución MRS.

La numeración sigue la lista del encargo 40C (pruebas 1 a 16). Corren en PostgreSQL:
docker compose exec web python manage.py test apps.rondas.test_40c

La 15 (suites de Django y JS) y la 16 (integridad de las Fases 34-39) se completan
fuera de Django con las suites indicadas en el informe 40C; aquí quedan sus partes
verificables desde la plataforma.
"""
import re
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.encuestas.evolucion import construir_evolucion
from apps.encuestas.historial import construir_historial
from apps.encuestas.models import MRS, Identificacion
from apps.usuarios.models import Usuario

from . import resultado_mrs as R
from .cierre import puntaje_mrs_definitivo
from .models import EstadoRonda, MRSAnterior40B2, OrigenRonda, RondaEvaluacion
from .test_40b3 import CATEGORIAS, IDENT, ITEMS, Base, bloque_mrs, payload, resultados_en

SRC = Path(settings.BASE_DIR)

# Valores asimétricos: si una dimensión tomara las preguntas equivocadas, la suma cambiaría.
VALORES = {'pregunta_1': 4, 'pregunta_2': 0, 'pregunta_3': 3, 'pregunta_4': 1,     # somática 8
           'pregunta_5': 2, 'pregunta_6': 0, 'pregunta_7': 0, 'pregunta_8': 1,     # psicológica 3
           'pregunta_9': 4, 'pregunta_10': 2, 'pregunta_11': 0}                    # urogenital 6


def seccion_evolucion(html):
    m = re.search(r'<section class="tarjeta evolucion-mrs".*?</section>', html, re.S)
    return m.group(0) if m else ''


def figura(html, clave):
    m = re.search(rf'<figure class="grafico-mrs" data-grafico-mrs="{clave}">.*?</figure>', html, re.S)
    return m.group(0) if m else ''


def puntos(fig):
    return [(int(r), int(v)) for r, v in re.findall(r'data-ronda="(\d+)" data-valor="(\d+)"', fig)]


def tramos(fig):
    return re.findall(r'<polyline class="grafico-mrs__linea" data-tramo points="([^"]+)"', fig)


def excluidas(fig):
    return [int(n) for n in re.findall(r'data-ronda-excluida="(\d+)"', fig)]


def estados_historial(html):
    return [(int(n), e) for n, e in re.findall(r'data-ronda-historial="(\d+)" data-estado-ronda="([a-z_]+)"', html)]


class Base40C(Base):
    def cerrar(self, numero, valores):
        """Cierra la ronda `numero` por el cierre validado de la 40B-2."""
        if numero > 1:
            from .test_40b2 import _pasar_plazo
            _pasar_plazo()
        self.sync(bloque_mrs(valores, parcial=False), ronda=numero, finalizar=True)
        self.assertEqual(self.ficha().ronda_actual, numero + 1)

    def cerrar_antigua(self, numero, valores):
        """Ronda cerrada como antes de la 40B-2: ceros que nadie confirmó, cierre por la señal."""
        if numero > 1:
            from .test_40b2 import _pasar_plazo
            _pasar_plazo()
        self.sync(bloque_mrs(valores), ronda=numero)
        fila = MRS.objects.get(participante=self.ficha(), ronda=numero)
        MRSAnterior40B2.objects.create(mrs=fila, items_confirmados=[])
        ficha = self.ficha()
        ficha.ronda_actual = numero + 1
        ficha.save()
        self.assertEqual(RondaEvaluacion.objects.get(participante=ficha, numero=numero).estado,
                         EstadoRonda.CERRADA)

    def evolucion(self):
        return construir_evolucion(construir_historial(self.ficha()))


# 1 y 2 ---------------------------------------------------------------------------------
class PuntajesTest(Base40C):
    def test_1_puntaje_total(self):
        self.cerrar(1, VALORES)
        evo = self.evolucion()
        self.assertEqual(evo['filas'][0]['total'], sum(VALORES.values()))   # 17
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            self.assertEqual(puntos(figura(html, 'total')), [(1, 17)])
            self.assertIn('17 de 44', seccion_evolucion(html))

    def test_2_tres_dimensiones_por_contenido_de_cada_pregunta(self):
        # La correspondencia se comprueba por el síntoma, no por el número del campo.
        sintomas = {
            'somatica': ('Bochornos', 'corazón', 'musculares y articulares', 'sueño'),
            'psicologica': ('depresivo', 'Irritabilidad', 'Ansiedad', 'Cansancio físico y mental'),
            'urogenital': ('Problemas sexuales', 'Problemas con la orina', 'Sequedad vaginal'),
        }
        for clave, _nombre, campos in R.DIMENSIONES:
            textos = [MRS._meta.get_field(c).help_text for c in campos]
            self.assertEqual(len(textos), len(sintomas[clave]))
            for sintoma in sintomas[clave]:
                self.assertEqual(sum(sintoma in t for t in textos), 1, (clave, sintoma))
        self.cerrar(1, VALORES)
        res = R.resultado_mrs(MRS.objects.get(participante=self.ficha(), ronda=1))
        dims = {d.clave: (d.puntaje, d.maximo) for d in res.dimensiones}
        self.assertEqual(dims, {'somatica': (8, 16), 'psicologica': (3, 16), 'urogenital': (6, 12)})
        self.assertEqual(sum(p for p, _ in dims.values()), res.puntaje)
        tablero, _ = self.paginas()
        for clave, valor in (('somatica', 8), ('psicologica', 3), ('urogenital', 6)):
            self.assertEqual(puntos(figura(tablero, clave)), [(1, valor)])


# 3 -------------------------------------------------------------------------------------
class CoherenciaReglaUnicaTest(Base40C):
    def test_3_coherencia_con_resultado_mrs(self):
        self.cerrar(1, VALORES)
        self.cerrar(2, {i: 2 for i in ITEMS})
        from .test_40b2 import _pasar_plazo
        _pasar_plazo()
        self.sync(bloque_mrs({i: 1 for i in ITEMS}, parcial=False), ronda=3)   # en curso, provisional
        ficha = self.ficha()
        evo = self.evolucion()
        for f in evo['filas']:
            res = R.resultado_mrs(MRS.objects.get(participante=ficha, ronda=f['numero']))
            self.assertEqual(f['total'], res.puntaje)
            self.assertEqual(f['total'], puntaje_mrs_definitivo(MRS.objects.get(participante=ficha,
                                                                               ronda=f['numero'])))
            self.assertEqual(sum(f['valores_dimensiones']), f['total'])
        provisional = R.resultado_mrs(MRS.objects.get(participante=ficha, ronda=3))
        self.assertEqual(provisional.estado, R.PROVISIONAL)
        self.assertEqual(provisional.dimensiones, ())        # sin dimensiones fuera de DEFINITIVO


# 4 y 5 ---------------------------------------------------------------------------------
class RondasTest(Base40C):
    def test_4_una_sola_ronda_sin_tendencia(self):
        self.cerrar(1, VALORES)
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            fig = figura(html, 'total')
            self.assertEqual(len(puntos(fig)), 1)
            self.assertEqual(tramos(fig), [])
            self.assertIn('Hay una sola ronda con resultado verificable', html)
        self.assertFalse(self.evolucion()['hay_tendencia'])

    def test_5_varias_rondas_una_linea_en_orden(self):
        self.cerrar(1, VALORES)
        self.cerrar(2, {i: 2 for i in ITEMS})
        self.cerrar(3, {i: 1 for i in ITEMS})
        tablero, _ = self.paginas()
        fig = figura(tablero, 'total')
        self.assertEqual(puntos(fig), [(1, 17), (2, 22), (3, 11)])
        self.assertEqual(len(tramos(fig)), 1)
        xs = [float(p.split(',')[0]) for p in tramos(fig)[0].split()]
        self.assertEqual(xs, sorted(xs))
        self.assertEqual(len(xs), 3)
        for clave, valores in (('somatica', [8, 8, 4]), ('psicologica', [3, 8, 4]), ('urogenital', [6, 6, 3])):
            self.assertEqual([v for _, v in puntos(figura(tablero, clave))], valores)
        self.assertNotIn('una sola ronda', tablero)


# 6 y 7 ---------------------------------------------------------------------------------
class ExclusionesTest(Base40C):
    def test_6_ronda_abierta_no_entra_en_los_graficos(self):
        self.cerrar(1, VALORES)
        from .test_40b2 import _pasar_plazo
        _pasar_plazo()
        self.sync(bloque_mrs({i: 4 for i in ITEMS}, parcial=False), ronda=2)   # 44 provisional
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            evo = seccion_evolucion(html)
            self.assertEqual(puntos(figura(html, 'total')), [(1, 17)])
            self.assertNotIn('44 de 44', evo)
            self.assertIn('La ronda 2 está en curso', evo)
            self.assertIn(('provisional', 'Suma provisional: 44 de 44 (la ronda no está cerrada)'),
                          resultados_en(html))
            self.assertEqual(estados_historial(html), [(2, 'en_curso'), (1, 'finalizada_verificable')])

    def test_7_no_verificable_queda_como_hueco_y_corta_la_linea(self):
        self.cerrar(1, VALORES)                                         # 17
        self.cerrar(2, {i: 2 for i in ITEMS})                           # 22
        self.cerrar_antigua(3, dict({i: 0 for i in ITEMS}, pregunta_1=3))   # no verificable
        self.cerrar(4, {i: 1 for i in ITEMS})                           # 11
        self.cerrar(5, {i: 3 for i in ITEMS})                           # 33
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            fig = figura(html, 'total')
            self.assertEqual(puntos(fig), [(1, 17), (2, 22), (4, 11), (5, 33)])
            self.assertEqual(excluidas(fig), [3])
            t = tramos(fig)
            self.assertEqual(len(t), 2)                       # 1-2 y 4-5, nunca 2-4
            self.assertEqual([len(x.split()) for x in t], [2, 2])
            x3 = re.search(r'data-ronda-excluida="3" x1="([\d.]+)"', fig).group(1)
            self.assertNotIn(x3 + ',', ' '.join(t))
            self.assertNotRegex(seccion_evolucion(html), r'(?<!\d)3 de 44')   # ni el 3 de la ronda antigua
            self.assertIn('Histórica no verificable: sin resultado verificable', seccion_evolucion(html))
            self.assertIn((3, 'historica_no_verificable'), estados_historial(html))
            for clave in ('somatica', 'psicologica', 'urogenital'):
                self.assertEqual(excluidas(figura(html, clave)), [3])
                self.assertNotIn(3, [r for r, _ in puntos(figura(html, clave))])

    def test_7b_verificables_no_seguidas_se_muestran_sin_unir(self):
        self.cerrar(1, VALORES)
        self.cerrar_antigua(2, dict({i: 0 for i in ITEMS}, pregunta_2=1))
        self.cerrar(3, {i: 1 for i in ITEMS})
        tablero, _ = self.paginas()
        fig = figura(tablero, 'total')
        self.assertEqual(puntos(fig), [(1, 17), (3, 11)])
        self.assertEqual(tramos(fig), [])
        self.assertIn('no son seguidas', tablero)

    def test_7c_solo_rondas_no_verificables_no_muestran_grafico(self):
        self.cerrar_antigua(1, dict({i: 0 for i in ITEMS}, pregunta_1=2))
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            self.assertEqual(figura(html, 'total'), '')
            self.assertIn('Ninguna ronda finalizada tiene un resultado verificable', html)
            self.assertEqual(resultados_en(html), [('no_verificable', 'Resultado histórico no verificable')])


# 8 -------------------------------------------------------------------------------------
class FechasTest(Base40C):
    def test_8_fechas_solo_si_son_verificables(self):
        self.cerrar(1, VALORES)
        self.cerrar(2, {i: 2 for i in ITEMS})
        self.cerrar_antigua(3, dict({i: 0 for i in ITEMS}, pregunta_1=1))
        ficha = self.ficha()
        # La ronda 2 como si viniera de la retrocarga 40B-1: sin fecha de cierre conocida.
        RondaEvaluacion.objects.filter(participante=ficha, numero=2).update(
            origen=OrigenRonda.RETROCARGA, cerrada_en=None, id_cierre=None)
        # La fecha de creación de la fila MRS no es la fecha de la ronda: nunca se muestra como cierre.
        MRS.objects.filter(participante=ficha, ronda=2).update(fecha_evaluacion='2019-03-07')
        hoy = timezone.localdate().strftime('%d-%m-%Y')
        tablero, _ = self.paginas()
        evo = seccion_evolucion(tablero)
        tabla = re.search(r'data-tabla-evolucion="total".*?</table>', evo, re.S).group(0)
        filas = dict(re.findall(r'<tr data-fila-ronda="(\d+)">\s*<th scope="row">\d+</th>\s*<td>([^<]*)</td>', tabla))
        self.assertEqual(filas, {'1': hoy, '2': 'Fecha no registrada', '3': 'Fecha no registrada'})
        self.assertNotIn('07-03-2019', evo)
        self.assertNotIn('Cierre: 07-03-2019', tablero)
        self.assertIn('Cierre: Fecha no registrada', tablero)
        # La ronda retrocargada con MRS completo sigue siendo un resultado definitivo (regla 40B-3).
        self.assertEqual(puntos(figura(tablero, 'total')), [(1, 17), (2, 22)])
        # El eje es el número de ronda: no aparecen fechas dentro del SVG.
        self.assertIsNone(re.search(r'\d{2}-\d{2}-\d{4}', figura(tablero, 'total')))


    def test_8b_retrocargada_abierta_y_cerrada_despues_con_cierre_validado_tiene_fecha(self):
        """Corrección: el origen RETROCARGA describe la apertura; la fecha la da el cierre validado."""
        self.sync(bloque_mrs({i: 2 for i in ITEMS}, parcial=False), ronda=1)
        ficha = self.ficha()
        RondaEvaluacion.objects.filter(participante=ficha, numero=1).update(origen=OrigenRonda.RETROCARGA)
        self.cerrar(1, {i: 2 for i in ITEMS})
        registro = RondaEvaluacion.objects.get(participante=ficha, numero=1)
        self.assertEqual((registro.origen, registro.estado), (OrigenRonda.RETROCARGA, EstadoRonda.CERRADA))
        hoy = timezone.localdate().strftime('%d-%m-%Y')
        tablero, ficha_prof = self.paginas()
        for html in (tablero, ficha_prof):
            tabla = re.search(r'data-tabla-evolucion="total".*?</table>', seccion_evolucion(html), re.S).group(0)
            self.assertIn(f'<td>{hoy}</td>', tabla)
            self.assertIn(f'Cierre: {hoy}', html)
            self.assertNotIn('Fecha no registrada', tabla)


# 9 -------------------------------------------------------------------------------------
class SinRespuestasTest(Base40C):
    def test_9_sin_ficha_y_sin_rondas_finalizadas(self):
        self.client.force_login(self.usuaria)
        html = self.client.get('/mi-tablero/').content.decode()
        self.assertIn('Todavía no has respondido la encuesta', html)
        self.assertEqual(seccion_evolucion(html), '')
        self.sync(bloque_mrs({'pregunta_1': 2}), ronda=1)    # ficha con la ronda 1 en curso
        tablero, ficha = self.paginas()
        for html in (tablero, ficha):
            evo = seccion_evolucion(html)
            self.assertIn('Todavía no hay rondas finalizadas', evo)
            self.assertNotIn('<svg', evo)
            self.assertNotIn('<table', evo)


# 10 ------------------------------------------------------------------------------------
class SeparacionTest(Base40C):
    def test_10_cada_participante_ve_solo_lo_suyo(self):
        self.cerrar(1, {i: 3 for i in ITEMS})                      # 33, propio de la usuaria A
        otra = Usuario.objects.create_user(rut='33.333.333-3', email='o@e.cl')
        from apps.encuestas.sync import sincronizar_payload
        p = payload([bloque_mrs({i: 1 for i in ITEMS}, parcial=False)], finalizar=True)
        self.assertTrue(sincronizar_payload(otra, p)['ok'])        # 11, de la usuaria B
        ficha_b = Identificacion.objects.get(usuario=otra)
        self.client.force_login(otra)
        html_b = self.client.get('/mi-tablero/').content.decode()
        self.assertEqual(puntos(figura(html_b, 'total')), [(1, 11)])
        self.assertNotIn('33 de 44', html_b)
        # B no puede abrir la ficha profesional de A ni de nadie.
        r = self.client.get(f'/profesional/paciente/{self.ficha().pk}/')
        self.assertNotEqual(r.status_code, 200)
        self.assertNotIn('33 de 44', r.content.decode())
        # La ficha profesional de A muestra solo los datos de A.
        _, ficha_a = self.paginas()
        self.assertEqual(puntos(figura(ficha_a, 'total')), [(1, 33)])
        self.assertNotIn('11 de 44', ficha_a)
        self.assertNotEqual(ficha_b.pk, self.ficha().pk)
        # Sin identificadores ni valores nuevos en las URL: el tablero sigue siendo /mi-tablero/.
        self.assertNotRegex(html_b, r'href="[^"]*(puntaje|mrs|resultado)[^"]*\d')


# 11 ------------------------------------------------------------------------------------
class AdaptableTest(Base40C):
    def test_11_componente_adaptable_y_accesible(self):
        self.cerrar(1, VALORES)
        self.cerrar(2, {i: 2 for i in ITEMS})
        tablero, _ = self.paginas()
        self.assertIn('name="viewport"', tablero)
        fig = figura(tablero, 'total')
        svg = re.search(r'<svg[^>]*>', fig).group(0)
        self.assertIn('viewBox="0 0 320 170"', svg)
        self.assertNotRegex(svg, r'\s(width|height)=')               # escala con el ancho de la pantalla
        self.assertIn('role="img"', svg)
        self.assertIn('aria-labelledby="evo-total-t evo-total-d"', svg)
        self.assertIn('<desc id="evo-total-d">Puntaje MRS total por ronda: ronda 1: 17 de 44; ronda 2: 22 de 44.</desc>', fig)
        evo = seccion_evolucion(tablero)
        self.assertEqual(evo.count('<table'), 2)                       # tablas equivalentes a los gráficos
        self.assertEqual(evo.count('<caption'), 2)
        self.assertIn('<details class="dimensiones-mrs">', evo)       # dimensiones en segundo plano
        self.assertLess(evo.index('data-grafico-mrs="total"'), evo.index('<details'))
        css = (SRC / 'static' / 'css' / 'tema.css').read_text(encoding='utf-8')
        bloque = css[css.index('Fase 40C'):]
        self.assertIn('.grafico-mrs__svg { display: block; width: 100%;', bloque)
        self.assertIn('@media (max-width: 480px)', bloque)


# 12 ------------------------------------------------------------------------------------
class CoherenciaPantallasTest(Base40C):
    def test_12_tablero_y_ficha_muestran_lo_mismo(self):
        self.cerrar(1, VALORES)
        self.cerrar_antigua(2, dict({i: 0 for i in ITEMS}, pregunta_1=3))
        self.cerrar(3, {i: 2 for i in ITEMS})
        from .test_40b2 import _pasar_plazo
        _pasar_plazo()
        self.sync(bloque_mrs({'pregunta_1': 4}), ronda=4)
        tablero, ficha = self.paginas()
        self.assertEqual(seccion_evolucion(tablero), seccion_evolucion(ficha))
        self.assertEqual(estados_historial(tablero), estados_historial(ficha))
        self.assertEqual(estados_historial(tablero), [(4, 'en_curso'), (3, 'finalizada_verificable'),
                                                      (2, 'historica_no_verificable'),
                                                      (1, 'finalizada_verificable')])
        self.assertEqual(resultados_en(tablero), resultados_en(ficha))
        for html in (tablero, ficha):
            self.assertIn('Datos actuales', html)


# 13 ------------------------------------------------------------------------------------
class SinSeveridadNiInterpretacionTest(Base40C):
    def test_13_sin_severidad_ni_conclusiones_clinicas(self):
        self.cerrar(1, {i: 4 for i in ITEMS})            # 44: antes «Severa»
        self.cerrar(2, {i: 1 for i in ITEMS})            # 11: antes «Moderada»
        self.cerrar(3, {i: 0 for i in ITEMS})            # 0
        tablero, ficha = self.paginas()
        prohibidas = CATEGORIAS + ['Severidad', 'severidad', 'ha mejorado', 'ha empeorado', 'mejoró',
                                   'empeoró', 'empeorando', 'mejorando', 'riesgo', 'alerta', 'diagnosticad',
                                   'tendencia al alza', 'tendencia a la baja', 'grupo de caracterización',
                                   'clúster', 'cluster']
        # Fase 40D-H: la sección «Mi grupo de caracterización» (autorizada) se revisa en sus propias pruebas.
        tablero = re.sub(r'<section class="tarjeta mi-grupo".*?</section>', '', tablero, flags=re.S)
        for html in (tablero, ficha):
            for palabra in prohibidas:
                self.assertNotIn(palabra, html, palabra)
            self.assertIn('no son un diagnóstico ni indican mejoría o empeoramiento', html)
        self.assertEqual(MRS.SEVERIDAD_TOTAL, ((4, 'Sin síntomas o muy leves'), (8, 'Leve'),
                                               (15, 'Moderada'), (44, 'Severa')))


# 14 ------------------------------------------------------------------------------------
class CompatibilidadTest(Base40C):
    def test_14_compatibilidad_con_40b2_y_40b3(self):
        self.cerrar(1, VALORES)
        ficha = self.ficha()
        ronda = RondaEvaluacion.objects.get(participante=ficha, numero=1)
        self.assertEqual((ronda.estado, ronda.origen), (EstadoRonda.CERRADA, OrigenRonda.NORMAL))
        self.assertIsNotNone(ronda.id_cierre)
        fila = MRS.objects.get(participante=ficha, ronda=1)
        res = R.resultado_mrs(fila)
        self.assertEqual((res.estado, res.puntaje, res.texto), (R.DEFINITIVO, 17, 'Puntaje MRS: 17 de 44'))
        self.assertEqual(res.como_dict()['dimensiones'], {'somatica': 8, 'psicologica': 3, 'urogenital': 6})
        # Los estados no definitivos de la 40B-3 siguen sin número y sin dimensiones.
        for estado in (R.PROVISIONAL, R.PARCIAL, R.NO_VERIFICABLE, R.INCOMPLETO, R.SIN_DATOS):
            self.assertEqual(R.ResultadoMRS(estado).dimensiones, ())
        antes = list(MRS.objects.values())
        rondas_antes = list(RondaEvaluacion.objects.values())
        self.client.force_login(self.usuaria)
        with CaptureQueriesContext(connection) as consultas:
            self.client.get('/mi-tablero/')
        self.client.force_login(self.prof)
        with CaptureQueriesContext(connection) as consultas_prof:
            self.client.get(f'/profesional/paciente/{ficha.pk}/')
        escrituras = [q['sql'] for q in consultas.captured_queries + consultas_prof.captured_queries
                      if re.match(r'\s*(INSERT|UPDATE|DELETE)', q['sql'], re.I)
                      and 'django_session' not in q['sql'] and 'usuarios_usuario' not in q['sql']]
        self.assertEqual(escrituras, [])
        self.assertEqual(list(MRS.objects.values()), antes)
        self.assertEqual(list(RondaEvaluacion.objects.values()), rondas_antes)


# 15 y 16 (partes verificables desde la plataforma) ---------------------------------------
class ComponentesTest(Base40C):
    def test_15_componentes_sin_dependencias_externas_ni_calculos_propios(self):
        for nombre in ('_evolucion_mrs.html', '_grafico_mrs.html', '_ronda_historial.html'):
            texto = (SRC / 'templates' / 'encuestas' / nombre).read_text(encoding='utf-8')
            self.assertNotIn('<script', texto, nombre)
            self.assertNotIn('http', texto, nombre)
            self.assertNotIn('puntaje_total', texto, nombre)
            self.assertNotIn('pregunta_', texto, nombre)
        evolucion = (SRC / 'apps' / 'encuestas' / 'evolucion.py').read_text(encoding='utf-8')
        self.assertNotIn('pregunta_', evolucion)          # las dimensiones vienen de resultado_mrs
        self.assertNotIn('objects', evolucion)            # no consulta la base por su cuenta
        sw = (SRC / 'static' / 'js' / 'sw.js').read_text(encoding='utf-8')
        self.assertIn("var CACHE = 'aging-women-v22';", sw)

    def test_16_la_plataforma_no_depende_del_analisis(self):
        # Integridad 34-39: la plataforma no importa ni escribe nada del análisis; las huellas
        # se comprueban con test_40b1_proteccion_historica.py (fuera del contenedor).
        for p in ('apps/rondas/resultado_mrs.py', 'apps/encuestas/evolucion.py', 'apps/encuestas/historial.py'):
            texto = (SRC / p).read_text(encoding='utf-8')
            self.assertNotIn('analisis', texto.replace('analisis/fase40/40C_tablero', ''), p)
            self.assertNotIn('nucleo_37d', texto, p)
