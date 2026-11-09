"""
Etapa 5B-3: una página con una copia antigua no puede borrar respuestas ya guardadas.
docker compose exec web python manage.py test apps.encuestas.test_concurrencia_5b3
"""
from decimal import Decimal
from uuid import uuid4

from django.test import override_settings

from apps.rondas.models import EstadoRonda, RondaEvaluacion
from apps.rondas.test_40b3 import bloque_mrs, payload

from .forms import SegmentoEMPAForm
from .models import MRS, Identificacion, SegmentoEMPA
from .sync import ConflictoRonda, _canonico, estado_ronda, sincronizar_payload
from .test_contexto_participante import CERO, BaseG, bloque_actividad, seccion_grupo
from .test_orientaciones import ACTIVAS, respuestas

ITEMS = {f'pregunta_{i}': 1 for i in range(1, 12)}
SIN_VERSION = object()


class BaseVersiones(BaseG):
    def setUp(self):
        super().setUp()
        self.uuid = str(uuid4())

    def enviar(self, datos, base=SIN_VERSION, sin_confirmar=None, finalizar=False, parcial=True):
        bloque = bloque_mrs(datos, uuid_local=self.uuid, parcial=parcial)
        if base is not SIN_VERSION:
            bloque['version_base'] = base
        if sin_confirmar is not None:
            bloque['sin_confirmar'] = sin_confirmar
        p = payload([bloque], ronda=1, finalizar=finalizar)
        return sincronizar_payload(self.usuaria, p)

    @staticmethod
    def version_de(res):
        return next(r['version'] for r in res['resultados'] if r['seccion'] == 'mrs')

    def primera_version(self):
        return self.version_de(self.enviar(dict(ITEMS), base=None))

    @staticmethod
    def mrs():
        return MRS.objects.get()


class PaginaAntiguaTest(BaseVersiones):
    def test_01_pagina_antigua_no_borra_ni_escribe(self):
        v1 = self.primera_version()
        self.enviar({**ITEMS, 'tiene_pareja': 'SI'}, base=v1)        # la otra pestaña guarda más
        antes = MRS.objects.filter().values().get()
        with self.assertRaises(ConflictoRonda) as ctx:
            self.enviar({'pregunta_1': 4}, base=v1)                   # la página antigua solo conoce esto
        self.assertEqual(ctx.exception.codigo, 'version_desactualizada')
        self.assertEqual(ctx.exception.extra['secciones'], ['mrs'])
        self.assertEqual(MRS.objects.filter().values().get(), antes, 'no se escribió nada')

    def test_02_la_identificacion_antigua_tampoco_escribe_y_el_rechazo_es_total(self):
        v1 = self.primera_version()
        p = payload([bloque_mrs({**ITEMS, 'tiene_pareja': 'SI'}, uuid_local=self.uuid)], ronda=1)
        res = sincronizar_payload(self.usuaria, p)
        v2 = self.version_de(res)
        ficha = Identificacion.objects.get(usuario=self.usuaria)
        comuna = ficha.comuna
        p = payload([bloque_mrs(ITEMS, uuid_local=self.uuid)], ronda=1)
        p['identificacion']['version_base'] = 'huella-antigua'
        p['identificacion']['datos']['comuna'] = 'Otra'
        p['secciones'][0]['version_base'] = v1                        # además, sección antigua
        with self.assertRaises(ConflictoRonda) as ctx:
            sincronizar_payload(self.usuaria, p)
        self.assertEqual(sorted(ctx.exception.extra['secciones']), ['identificacion', 'mrs'])
        ficha.refresh_from_db()
        self.assertEqual(ficha.comuna, comuna)
        self.assertEqual(self.mrs().tiene_pareja, 'SI')
        self.assertEqual(estado_ronda(ficha)['secciones']['mrs']['version'], v2)

    def test_03_no_se_fusiona_una_respuesta_distinta(self):
        v1 = self.primera_version()
        self.enviar({**ITEMS, 'pregunta_1': 2}, base=v1)
        with self.assertRaises(ConflictoRonda):
            self.enviar({**ITEMS, 'pregunta_1': 3}, base=v1)
        self.assertEqual(self.mrs().pregunta_1, 2)

    def test_04_pagina_que_creia_no_haber_nada(self):
        self.primera_version()
        with self.assertRaises(ConflictoRonda):
            self.enviar({'pregunta_1': 4}, base=None)
        self.assertEqual(self.mrs().pregunta_11, 1)

    def test_05_cierre_desde_pagina_antigua_no_cierra(self):
        v1 = self.primera_version()
        self.enviar({**ITEMS, 'tiene_pareja': 'SI'}, base=v1)
        with self.assertRaises(ConflictoRonda):
            self.enviar(dict(ITEMS), base=v1, finalizar=True, parcial=False)
        ficha = Identificacion.objects.get(usuario=self.usuaria)
        self.assertEqual(ficha.ronda_actual, 1)
        self.assertEqual(self.mrs().tiene_pareja, 'SI')

    def test_06_decision_explicita_reemplaza_con_la_version_del_conflicto(self):
        v1 = self.primera_version()
        self.enviar({**ITEMS, 'tiene_pareja': 'SI'}, base=v1)
        with self.assertRaises(ConflictoRonda) as ctx:
            self.enviar(dict(ITEMS), base=v1)
        self.enviar(dict(ITEMS), base=ctx.exception.extra['versiones']['mrs'])
        self.assertIn(self.mrs().tiene_pareja, (None, ''))


class MismoDispositivoTest(BaseVersiones):
    def test_07_guardados_consecutivos_con_la_version_devuelta(self):
        v = self.primera_version()
        for i in range(2, 5):
            res = self.enviar({**ITEMS, 'pregunta_1': i}, base=v)
            self.assertTrue(res['ok'], res)
            v = self.version_de(res)
        ficha = Identificacion.objects.get(usuario=self.usuaria)
        self.assertEqual(estado_ronda(ficha)['secciones']['mrs']['version'], v)

    def test_08_respuesta_perdida_el_reintento_igual_no_es_conflicto(self):
        v1 = self.primera_version()
        self.enviar({**ITEMS, 'tiene_pareja': 'SI'}, base=v1)        # se guardó, pero la respuesta se perdió
        res = self.enviar({**ITEMS, 'tiene_pareja': 'SI'}, base=v1)
        self.assertTrue(res['ok'], res)

    def test_09_respuesta_perdida_y_mas_cambios_se_reconoce_lo_propio(self):
        v1 = self.primera_version()
        enviado = {**ITEMS, 'tiene_pareja': 'SI'}
        self.enviar(enviado, base=v1)
        res = self.enviar({**enviado, 'pregunta_2': 3}, base=v1, sin_confirmar=[enviado])
        self.assertTrue(res['ok'], res)
        self.assertEqual(self.mrs().pregunta_2, 3)

    def test_10_lo_no_confirmado_no_sirve_si_guardo_otra_persona(self):
        v1 = self.primera_version()
        self.enviar({**ITEMS, 'tiene_pareja': 'NO'}, base=v1)
        with self.assertRaises(ConflictoRonda):
            self.enviar(dict(ITEMS), base=v1, sin_confirmar=[{**ITEMS, 'tiene_pareja': 'SI'}])
        self.assertEqual(self.mrs().tiene_pareja, 'NO')

    def test_11_lo_oculto_se_sigue_vaciando_con_la_version_vigente(self):
        v1 = self.primera_version()
        v2 = self.version_de(self.enviar({**ITEMS, 'tiene_pareja': 'SI'}, base=v1))
        self.enviar(dict(ITEMS), base=v2)
        self.assertIn(self.mrs().tiene_pareja, (None, ''))

    def test_12_cliente_antiguo_sin_version_no_se_comprueba(self):
        self.primera_version()
        self.assertTrue(self.enviar({**ITEMS, 'pregunta_1': 4})['ok'])

    def test_13_version_estable_ante_decimales_equivalentes(self):
        a = SegmentoEMPA(peso_kg=Decimal('70.50'))
        b = SegmentoEMPA(peso_kg=Decimal('70.5'))
        self.assertEqual(_canonico(a, SegmentoEMPAForm), _canonico(b, SegmentoEMPAForm))

    def test_14_la_version_no_expone_contenido(self):
        self.assertRegex(self.primera_version(), r'^[0-9a-f]{32}$')


@override_settings(**ACTIVAS)
class CierreYB1Test(BaseVersiones):
    def test_15_tras_el_rechazo_la_ronda_cierra_y_b1_aparece(self):
        datos = {**respuestas(p3=3), 'tiene_pareja': 'SI'}
        act = bloque_actividad(CERO)
        p = payload([bloque_mrs(datos, uuid_local=self.uuid, parcial=False), act], ronda=1)
        p['identificacion']['datos']['trabaja_actualmente'] = True
        res = sincronizar_payload(self.usuaria, p)
        vigente = next(r['version'] for r in res['resultados'] if r['seccion'] == 'mrs')
        with self.assertRaises(ConflictoRonda):                       # la página antigua, sin pareja
            self.enviar(respuestas(p3=3), base='huella-antigua', finalizar=True, parcial=False)
        self.assertEqual(self.mrs().tiene_pareja, 'SI')

        cierre = payload([{**bloque_mrs(datos, uuid_local=self.uuid, parcial=False), 'version_base': vigente}, act],
                         ronda=1, finalizar=True)
        cierre['identificacion']['datos']['trabaja_actualmente'] = True
        res = sincronizar_payload(self.usuaria, cierre)
        self.assertEqual(res['cierre']['estado'], 'cerrada', res)
        self.assertEqual(RondaEvaluacion.objects.get(numero=1).estado, EstadoRonda.CERRADA)
        contexto = self.seleccion()['contexto_exploratorio']
        self.assertEqual(contexto['faltantes'], [])
        self.assertEqual(contexto['grupo_b1'], 'S3')
        sec = seccion_grupo(self.tablero_de(self.usuaria))
        self.assertIn('data-grupo-nombre', sec)
        self.assertIn('data-aviso-grupo', sec)
