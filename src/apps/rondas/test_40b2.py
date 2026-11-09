"""
Pruebas de la Fase 40B-2: MRS con respuestas ausentes y cierre seguro de las rondas.

Corren en PostgreSQL (docker compose exec web python manage.py test). La numeración
sigue la lista de pruebas obligatorias del encargo 40B-2 (§7); las pruebas del
cliente (11 y 12) están en apps/encuestas/pruebas_js y corren con Node.
"""
import json
import threading
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest import mock
from uuid import uuid4

from django.core.management import call_command
from django.db import connection, connections
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.encuestas.esquema import construir_esquema
from apps.encuestas.models import MRS, EvaluacionTrabajo, Identificacion, SegmentoEMPA
from apps.encuestas.sync import ConflictoRonda, ErrorSincronizacion, estado_ronda, sincronizar_payload
from apps.usuarios.models import Usuario
from apps.usuarios.rut import hash_rut

from apps.rondas.pruebas_comunes import con_participacion
from . import completitud
from .cierre import puntaje_mrs_definitivo, ronda_es_historica_no_verificable
from .models import EstadoRonda, EventoRonda, MRSAnterior40B2, RolCierre, RondaEvaluacion, TipoEventoRonda
from .proteccion import RespuestaHistoricaProtegida
from .pruebas_comunes import EMPA_PROFESIONAL, consentimiento_presencial

IDENT = {
    'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
    'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
    'comuna': 'Santiago', 'region_residencia': '13',
}
ITEMS = [f'pregunta_{i}' for i in range(1, 12)]
TODOS_CERO = {i: 0 for i in ITEMS}


def mrs(datos, uuid_local=None, parcial=True, confirmados=None):
    bloque = {'tipo': 'mrs', 'uuid_local': uuid_local or str(uuid4()), 'parcial': parcial, 'datos': dict(datos)}
    if confirmados is not None:
        bloque['confirmados'] = confirmados
    return bloque


def payload(secciones=(), ronda=1, finalizar=False, id_cierre=None, ident=None, **extra):
    p = {'identificacion': ident or {'uuid_local': str(uuid4()), 'datos': dict(IDENT)},
         'secciones': list(secciones), 'ronda': ronda}
    if finalizar:
        p['finalizar'] = True
        p['id_cierre'] = str(id_cierre or uuid4())
    p.update(extra)
    return p


def _pasar_plazo():
    Identificacion.objects.update(ultima_finalizacion_en=timezone.now() - timedelta(days=16))


class Base(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.prof = Usuario.objects.create_user(rut='22.222.222-2', email='p@e.cl',
                                                rol=Usuario.Rol.PROFESIONAL_SALUD)

    def ficha(self):
        return Identificacion.objects.get(usuario=self.usuaria)


# 1 y 2 ---------------------------------------------------------------------------------
class CeroYAusenteTest(Base):
    def test_01_cero_explicito_distinto_de_respuesta_ausente(self):
        res = sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 0, 'pregunta_2': 3})]))
        self.assertTrue(res['ok'], res)
        fila = MRS.objects.get()
        self.assertEqual(fila.pregunta_1, 0)            # eligió «Ninguna»
        self.assertEqual(fila.pregunta_2, 3)
        for item in ITEMS[2:]:
            self.assertIsNone(getattr(fila, item), item)  # no respondió: nulo, no 0
        self.assertEqual(fila.items_sin_responder, ITEMS[2:])
        # Al volver a abrir la encuesta, el 0 vuelve como respuesta y los nulos no vuelven.
        datos = estado_ronda(self.ficha())['secciones']['mrs']['datos']
        self.assertEqual(datos['pregunta_1'], 0)
        self.assertNotIn('pregunta_3', datos)

    def test_01b_un_guardado_parcial_no_borra_lo_ya_respondido(self):
        u = str(uuid4())
        sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 2}, u)]))
        sincronizar_payload(self.usuaria, payload([mrs({'pregunta_2': 1}, u)]))  # otro dispositivo
        fila = MRS.objects.get()
        self.assertEqual((fila.pregunta_1, fila.pregunta_2), (2, 1))

    def test_02_valores_validos_de_0_a_4(self):
        for valor in range(5):
            with self.subTest(valor=valor):
                MRS.objects.all().delete()
                res = sincronizar_payload(self.usuaria, payload([mrs({'pregunta_4': valor})]))
                self.assertTrue(res['ok'], res)
                self.assertEqual(MRS.objects.get().pregunta_4, valor)
        for invalido in (5, -1, 'x', 2.5):
            with self.subTest(invalido=invalido):
                MRS.objects.all().delete()
                res = sincronizar_payload(self.usuaria, payload([mrs({'pregunta_4': invalido})]))
                self.assertFalse(res['ok'])
                self.assertIn('pregunta_4', res['resultados'][1]['errores'])
                self.assertFalse(MRS.objects.exists())

    def test_02b_sin_valor_por_defecto_en_el_modelo(self):
        self.assertIsNone(MRS(participante_id=1).pregunta_1)
        for item in ITEMS:
            campo = MRS._meta.get_field(item)
            self.assertTrue(campo.null, item)
            self.assertFalse(campo.blank, item)  # en un envío completo sigue siendo obligatoria


# 3 a 7 ---------------------------------------------------------------------------------
class CierreTest(Base):
    def _completo(self, **cambios):
        return dict({i: 1 for i in ITEMS}, **cambios)

    def test_03_rechaza_un_cierre_incompleto_y_dice_que_falta(self):
        res = sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 2})], finalizar=True))
        self.assertFalse(res['ok'])
        self.assertTrue(res['guardado'])
        self.assertEqual(res['cierre']['estado'], 'rechazado')
        self.assertEqual(res['ronda_actual'], 1)
        faltan = {f['seccion']: f for f in res['cierre']['faltantes']}
        self.assertEqual(faltan['mrs']['preguntas'], ITEMS[1:])
        ficha = self.ficha()
        self.assertEqual(ficha.ronda_actual, 1)
        self.assertIsNone(ficha.ultima_finalizacion_en)  # el plazo de 15 días no empieza
        ronda = RondaEvaluacion.objects.get(participante=ficha)
        self.assertEqual(ronda.estado, EstadoRonda.ABIERTA)
        evento = ronda.eventos.get(tipo=TipoEventoRonda.CIERRE_RECHAZADO)
        self.assertEqual(evento.actor, self.usuaria)
        self.assertNotIn("'pregunta_1': 2", str(evento.datos))  # sin valores

    def test_03b_por_la_api_el_rechazo_es_200_con_el_detalle(self):
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save()
        self.client.force_login(self.usuaria)
        resp = self.client.post('/api/sincronizar/', data=json.dumps(con_participacion(
            self.usuaria, payload([mrs({'pregunta_1': 2})], finalizar=True))), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        cuerpo = resp.json()
        self.assertEqual((cuerpo['ok'], cuerpo['guardado'], cuerpo['protocolo']), (False, True, 2))
        self.assertEqual(cuerpo['cierre']['estado'], 'rechazado')

    def test_04_acepta_un_cierre_completo_y_registra_quien_cerro(self):
        id_cierre = uuid4()
        res = sincronizar_payload(self.usuaria, payload([mrs(self._completo(pregunta_3=0), parcial=False)],
                                                        finalizar=True, id_cierre=id_cierre))
        self.assertTrue(res['ok'], res)
        self.assertEqual(res['cierre'], {'estado': 'cerrada', 'ronda': 1, 'id_cierre': str(id_cierre)})
        self.assertEqual(res['ronda_actual'], 2)
        r1, r2 = RondaEvaluacion.objects.filter(participante=self.ficha()).order_by('numero')
        self.assertEqual((r1.estado, r1.cerrada_por, r1.cerrada_por_rol, r1.id_cierre),
                         (EstadoRonda.CERRADA, self.usuaria, RolCierre.USUARIA, id_cierre))
        self.assertEqual(r1.cerrada_en, self.ficha().ultima_finalizacion_en)
        self.assertEqual(r2.estado, EstadoRonda.ABIERTA)
        cierre = r1.eventos.get(tipo=TipoEventoRonda.CIERRE)
        self.assertEqual(cierre.datos['via'], 'cierre_validado_40B2')
        self.assertEqual(cierre.datos['completitud']['modo'], 'obligatorio')
        self.assertTrue(cierre.datos['completitud']['completa'])

    def test_04b_sin_id_cierre_el_servidor_genera_uno(self):
        p = payload([mrs(self._completo())], finalizar=True)
        del p['id_cierre']
        res = sincronizar_payload(self.usuaria, p)
        self.assertTrue(res['ok'], res)
        self.assertIsNotNone(RondaEvaluacion.objects.get(numero=1).id_cierre)

    def test_05_las_condicionales_que_no_corresponden_no_se_exigen(self):
        # Trabaja: la sección Trabajo aplica, pero no tiene preguntas obligatorias.
        ident = {'uuid_local': str(uuid4()), 'datos': dict(IDENT, trabaja_actualmente=True)}
        res = sincronizar_payload(self.usuaria, payload([mrs(self._completo())], ident=ident, finalizar=True))
        self.assertTrue(res['ok'], res)
        self.assertFalse(EvaluacionTrabajo.objects.exists())

    def test_05b_una_obligatoria_condicional_solo_se_exige_si_se_muestra(self):
        original = construir_esquema

        def esquema_con_condicional_obligatoria(rol):
            e = original(rol)
            for s in e['secciones']:
                for p in s['preguntas']:
                    if p['nombre'] == 'tipo_metodo_anticonceptivo':  # solo se muestra si usa método
                        p['obligatoria'] = True
            return e

        sincronizar_payload(self.usuaria, payload([mrs(self._completo(usa_metodo_anticonceptivo='NO',
                                                                      fecha_ultima_menstruacion='2026'))]))
        with mock.patch('apps.rondas.completitud.construir_esquema', esquema_con_condicional_obligatoria):
            ficha = self.ficha()
            obs = completitud.evaluar(ficha, 1, modo='obligatorio')
            self.assertTrue(obs['completa'], obs)
            MRS.objects.update(usa_metodo_anticonceptivo='SI')
            obs = completitud.evaluar(ficha, 1, modo='obligatorio')
            self.assertEqual(obs['faltantes'], [{'seccion': 'mrs_complementario', 'motivo':
                                                 'obligatorias_sin_responder',
                                                 'preguntas': ['tipo_metodo_anticonceptivo']}])

    def test_06_el_borrador_se_conserva_y_luego_se_puede_cerrar(self):
        u = str(uuid4())
        sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 4}, u)], finalizar=True))
        self.assertEqual(MRS.objects.get().pregunta_1, 4)       # nada se perdió al rechazar
        res = sincronizar_payload(self.usuaria, payload([mrs(self._completo(pregunta_1=4), u)],
                                                        ronda=1, finalizar=True))
        self.assertTrue(res['ok'], res)
        self.assertEqual(MRS.objects.count(), 1)                # la misma fila, sin duplicar
        self.assertEqual(MRS.objects.get().pregunta_1, 4)

    def test_07_el_puntaje_solo_es_definitivo_con_la_ronda_completa_y_cerrada(self):
        u = str(uuid4())
        sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 4, 'pregunta_2': 0}, u)]))
        fila = MRS.objects.get()
        self.assertIsNone(fila.puntaje_total)                   # faltan ítems: no hay puntaje
        self.assertIsNone(puntaje_mrs_definitivo(fila))
        sincronizar_payload(self.usuaria, payload([mrs(self._completo(pregunta_1=4, pregunta_2=0), u)]))
        fila.refresh_from_db()
        self.assertEqual(fila.puntaje_total, 13)                 # completo, pero la ronda sigue abierta
        self.assertIsNone(puntaje_mrs_definitivo(fila))
        sincronizar_payload(self.usuaria, payload([mrs(self._completo(pregunta_1=4, pregunta_2=0), u)],
                                                  ronda=1, finalizar=True))
        fila.refresh_from_db()
        self.assertEqual(puntaje_mrs_definitivo(fila), 13)

    def test_07b_el_tablero_marca_como_provisional_el_puntaje_de_la_ronda_en_curso(self):
        sincronizar_payload(self.usuaria, payload([mrs(self._completo())]))
        self.client.force_login(self.usuaria)
        self.assertContains(self.client.get('/mi-tablero/'), 'provisional')


# 8 a 10 --------------------------------------------------------------------------------
class IdempotenciaYTardiasTest(Base):
    def _cerrar(self, id_cierre, **cambios):
        datos = dict({i: 2 for i in ITEMS}, **cambios)
        return sincronizar_payload(self.usuaria, payload([mrs(datos, self.u)], ronda=1, finalizar=True,
                                                         id_cierre=id_cierre))

    def setUp(self):
        super().setUp()
        self.u = str(uuid4())

    def test_08_cierre_repetido_sin_duplicar(self):
        id_cierre = uuid4()
        primero = self._cerrar(id_cierre)
        self.assertEqual(primero['cierre']['estado'], 'cerrada')
        _pasar_plazo()  # aun dentro o fuera del plazo, el reintento responde igual
        segundo = self._cerrar(id_cierre, pregunta_1=4)   # el reintento trae un valor distinto
        self.assertTrue(segundo['ok'])
        self.assertEqual(segundo['cierre'], {'estado': 'repetido', 'ronda': 1, 'id_cierre': str(id_cierre)})
        self.assertEqual(segundo['ronda_actual'], 2)
        self.assertEqual(self.ficha().ronda_actual, 2)
        self.assertEqual(RondaEvaluacion.objects.count(), 2)
        self.assertEqual(EventoRonda.objects.filter(tipo=TipoEventoRonda.CIERRE).count(), 1)
        self.assertEqual(EventoRonda.objects.filter(tipo=TipoEventoRonda.REINTENTO_IDEMPOTENTE).count(), 1)
        self.assertEqual(MRS.objects.get().pregunta_1, 2)  # el reintento no escribe nada

    def test_08b_reintento_dentro_del_plazo_de_15_dias(self):
        id_cierre = uuid4()
        self._cerrar(id_cierre)
        self.assertEqual(self._cerrar(id_cierre)['cierre']['estado'], 'repetido')  # sin error de plazo

    def test_08c_id_cierre_de_otra_participante(self):
        id_cierre = uuid4()
        self._cerrar(id_cierre)
        otra = Usuario.objects.create_user(rut='12.345.678-5', email='o@e.cl')
        with self.assertRaises(ErrorSincronizacion):
            sincronizar_payload(otra, payload([mrs({i: 1 for i in ITEMS})], finalizar=True, id_cierre=id_cierre))

    def test_10_solicitud_tardia_despues_del_cierre(self):
        self._cerrar(uuid4())
        _pasar_plazo()
        antes = list(MRS.objects.values())
        # Llega tarde un guardado de la ronda 1 desde otro dispositivo, con un uuid nuevo:
        # sin el control de ronda se habría escrito en la ronda 2.
        with self.assertRaises(ConflictoRonda) as ctx:
            sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 0})], ronda=1))
        self.assertEqual((ctx.exception.codigo, ctx.exception.ronda_actual), ('ronda_cerrada', 2))
        self.assertEqual(list(MRS.objects.values()), antes)
        self.assertFalse(MRS.objects.filter(ronda=2).exists())
        rechazo = EventoRonda.objects.get(tipo=TipoEventoRonda.ESCRITURA_RECHAZADA_RONDA_CERRADA)
        self.assertEqual((rechazo.ronda.numero, rechazo.datos['secciones']), (1, ['mrs']))
        # Un cierre tardío con otro id tampoco cierra nada.
        with self.assertRaises(ConflictoRonda):
            sincronizar_payload(self.usuaria, payload([mrs({i: 1 for i in ITEMS})], ronda=1, finalizar=True))
        self.assertEqual(self.ficha().ronda_actual, 2)

    def test_10b_la_api_responde_409_con_el_codigo(self):
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save()
        self._cerrar(uuid4())
        _pasar_plazo()
        self.client.force_login(self.usuaria)
        resp = self.client.post('/api/sincronizar/', data=json.dumps(con_participacion(
            self.usuaria, payload([mrs({'pregunta_1': 1})], ronda=1))), content_type='application/json')
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['codigo'], 'ronda_cerrada')
        self.assertEqual(resp.json()['ronda_actual'], 2)

    def test_10c_ronda_desconocida_o_inexistente(self):
        sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 1})]))  # crea la ficha (ronda null: ok)
        for ronda, codigo in ((None, 'ronda_desconocida'), (3, 'ronda_inexistente')):
            with self.subTest(ronda=ronda), self.assertRaises(ConflictoRonda) as ctx:
                sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 3})], ronda=ronda))
            self.assertEqual(ctx.exception.codigo, codigo)
        self.assertEqual(MRS.objects.get().pregunta_1, 1)

    def test_10d_cliente_antiguo_guarda_borradores_pero_no_puede_cerrar(self):
        antiguo = payload([mrs({'pregunta_1': 1})])
        del antiguo['ronda']
        self.assertTrue(sincronizar_payload(self.usuaria, antiguo)['ok'])   # compatibilidad
        antiguo = payload([mrs({i: 1 for i in ITEMS})], finalizar=True)
        del antiguo['ronda']
        with self.assertRaises(ConflictoRonda) as ctx:
            sincronizar_payload(self.usuaria, antiguo)
        self.assertEqual(ctx.exception.codigo, 'cliente_desactualizado')
        self.assertEqual(self.ficha().ronda_actual, 1)

    def test_10e_formato_de_ronda_e_id_cierre(self):
        for valor in ('1', 0, True, 1.5):
            with self.subTest(ronda=valor), self.assertRaises(ErrorSincronizacion):
                sincronizar_payload(self.usuaria, payload([], ronda=valor))
        with self.assertRaises(ErrorSincronizacion):
            sincronizar_payload(self.usuaria, payload([], finalizar=True, id_cierre='no-es-uuid'))


class ConcurrenciaCierreTest(TransactionTestCase):
    """9: dos cierres simultáneos reales (dos conexiones a PostgreSQL)."""

    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        sincronizar_payload(self.usuaria, payload([mrs({i: 1 for i in ITEMS}, parcial=False)]))
        self.ficha = Identificacion.objects.get()

    def _en_paralelo(self, funciones):
        barrera = threading.Barrier(len(funciones))
        resultados = [None] * len(funciones)

        def correr(i, f):
            try:
                barrera.wait()
                resultados[i] = f()
            except ConflictoRonda as exc:
                resultados[i] = exc.codigo
            finally:
                connections.close_all()

        hilos = [threading.Thread(target=correr, args=(i, f)) for i, f in enumerate(funciones)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        return resultados

    def _cierre(self, id_cierre):
        return lambda: sincronizar_payload(self.usuaria, payload([mrs({i: 2 for i in ITEMS})], ronda=1,
                                                                 finalizar=True, id_cierre=id_cierre))['cierre']['estado']

    def _comprobar_un_solo_cierre(self):
        self.ficha.refresh_from_db()
        self.assertEqual(self.ficha.ronda_actual, 2)
        self.assertEqual(RondaEvaluacion.objects.filter(participante=self.ficha).count(), 2)
        self.assertEqual(RondaEvaluacion.objects.filter(participante=self.ficha, estado='ABIERTA').count(), 1)
        self.assertEqual(EventoRonda.objects.filter(tipo=TipoEventoRonda.CIERRE).count(), 1)
        self.assertEqual(MRS.objects.count(), 1)

    def test_09_dos_dispositivos_cierran_a_la_vez(self):
        resultados = self._en_paralelo([self._cierre(uuid4()), self._cierre(uuid4())])
        self.assertEqual(sorted(resultados), ['cerrada', 'ronda_cerrada'])
        self._comprobar_un_solo_cierre()

    def test_09b_el_mismo_cierre_enviado_dos_veces_a_la_vez(self):
        id_cierre = uuid4()
        resultados = self._en_paralelo([self._cierre(id_cierre), self._cierre(id_cierre)])
        self.assertEqual(sorted(resultados), ['cerrada', 'repetido'])
        self._comprobar_un_solo_cierre()


# 13 ------------------------------------------------------------------------------------
class UsuariaYProfesionalTest(Base):
    def _paciente_de_la_profesional(self):
        consentimiento_presencial('9.876.543-3', self.prof)   # Fase 40, Etapa 2
        res = sincronizar_payload(self.prof, payload([], ident={'uuid_local': str(uuid4()), 'rut': '9.876.543-3',
                                                                 'datos': dict(IDENT)}))
        self.assertTrue(res['ok'], res)
        return Identificacion.objects.get(rut_hash=hash_rut('9.876.543-3'))

    # Revisión correctiva 40B-2: el EMPA es complementario y no bloquea el cierre,
    # tampoco cuando lo registra una profesional. El MRS sigue siendo obligatorio.
    EMPA_CAMPOS = tuple(EMPA_PROFESIONAL)

    def _cierre_profesional(self, datos_empa):
        paciente = self._paciente_de_la_profesional()
        ident = {'paciente_id': paciente.pk, 'datos': {}}
        secciones = [mrs({i: 1 for i in ITEMS}, parcial=False)]
        if datos_empa is not None:
            secciones.append({'tipo': 'empa', 'uuid_local': str(uuid4()), 'parcial': False, 'datos': datos_empa})
        res = sincronizar_payload(self.prof, payload(secciones, ident=ident, ronda=1, finalizar=True))
        self.assertTrue(res['ok'], res)
        self.assertEqual(res['cierre']['estado'], 'cerrada', res)
        ronda = RondaEvaluacion.objects.get(participante=paciente, numero=1)
        self.assertEqual(ronda.estado, EstadoRonda.CERRADA)
        self.assertEqual((ronda.cerrada_por, ronda.cerrada_por_rol), (self.prof, RolCierre.PROFESIONAL))
        return paciente

    def test_13_la_profesional_cierra_con_empa_completo(self):
        paciente = self._cierre_profesional(EMPA_PROFESIONAL)
        empa = SegmentoEMPA.objects.get(participante=paciente, ronda=1)
        self.assertEqual((empa.talla_actual_cm, float(empa.peso_kg), empa.presion_sistolica,
                          empa.presion_diastolica), (160, 65.0, 120, 80))

    def test_13_la_profesional_cierra_con_empa_parcial(self):
        paciente = self._cierre_profesional({'peso_kg': '65', 'presion_sistolica': 120})
        empa = SegmentoEMPA.objects.get(participante=paciente, ronda=1)
        self.assertEqual((float(empa.peso_kg), empa.presion_sistolica), (65.0, 120))
        # Lo no registrado queda nulo: no se imputan ceros ni otros valores.
        self.assertIsNone(empa.talla_actual_cm)
        self.assertIsNone(empa.presion_diastolica)
        self.assertIsNone(empa.glicemia_mg_dl)

    def test_13_la_profesional_cierra_sin_empa(self):
        paciente = self._cierre_profesional(None)
        self.assertFalse(SegmentoEMPA.objects.filter(participante=paciente).exists())

    def test_13_la_profesional_cierra_con_empa_vacio(self):
        paciente = self._cierre_profesional({})
        for empa in SegmentoEMPA.objects.filter(participante=paciente):
            for campo in self.EMPA_CAMPOS:
                self.assertIsNone(getattr(empa, campo), campo)

    def test_13_el_empa_completo_no_reemplaza_al_mrs_obligatorio(self):
        paciente = self._paciente_de_la_profesional()
        ident = {'paciente_id': paciente.pk, 'datos': {}}
        res = sincronizar_payload(self.prof, payload(
            [mrs({i: 1 for i in ITEMS[:10]}),
             {'tipo': 'empa', 'uuid_local': str(uuid4()), 'parcial': False, 'datos': EMPA_PROFESIONAL}],
            ident=ident, ronda=1, finalizar=True))
        self.assertEqual(res['cierre']['estado'], 'rechazado')
        secciones = {f['seccion']: f['preguntas'] for f in res['cierre']['faltantes']}
        self.assertEqual(secciones.get('mrs'), ['pregunta_11'])
        self.assertNotIn('empa', secciones)
        ronda = RondaEvaluacion.objects.get(participante=paciente, numero=1)
        self.assertEqual(ronda.estado, EstadoRonda.ABIERTA)

    def test_13_el_esquema_profesional_no_marca_obligatorio_el_empa(self):
        esquema = construir_esquema(Usuario.Rol.PROFESIONAL_SALUD)
        empa = next(s for s in esquema['secciones'] if s['tipo'] == 'empa')
        nombres = {p['nombre'] for p in empa['preguntas']}
        self.assertTrue(set(self.EMPA_CAMPOS) <= nombres)   # la profesional sigue viendo los campos
        self.assertEqual([p['nombre'] for p in empa['preguntas'] if p['obligatoria']], [])
        # El MRS sigue obligatorio en el mismo esquema.
        mrs_s = next(s for s in esquema['secciones'] if s['tipo'] == 'mrs')
        self.assertTrue(set(ITEMS) <= {p['nombre'] for p in mrs_s['preguntas'] if p['obligatoria']})

    def test_13b_la_usuaria_no_necesita_los_campos_clinicos(self):
        res = sincronizar_payload(self.usuaria, payload([mrs({i: 0 for i in ITEMS})], finalizar=True))
        self.assertTrue(res['ok'], res)
        self.assertFalse(SegmentoEMPA.objects.exists())

    def test_13c_la_profesional_cierra_la_ronda_de_una_paciente_con_cuenta(self):
        self.usuaria.consentimiento_aceptado_en = timezone.now()   # Fase 40 (P7)
        self.usuaria.save(update_fields=['consentimiento_aceptado_en'])
        sincronizar_payload(self.usuaria, con_participacion(self.usuaria, payload([mrs({'pregunta_1': 3})])))
        ident = {'paciente_id': self.ficha().pk, 'datos': {}}
        res = sincronizar_payload(self.prof, payload(
            [mrs({i: 1 for i in ITEMS[1:]}), {'tipo': 'empa', 'uuid_local': str(uuid4()), 'parcial': False,
                                              'datos': EMPA_PROFESIONAL}], ident=ident, ronda=1, finalizar=True))
        self.assertTrue(res['ok'], res)
        self.assertEqual(MRS.objects.get().pregunta_1, 3)   # lo de la usuaria se conserva
        # La usuaria, en su dispositivo, todavía cree estar en la ronda 1: su envío se rechaza.
        _pasar_plazo()
        with self.assertRaises(ConflictoRonda):
            sincronizar_payload(self.usuaria, con_participacion(self.usuaria, payload([mrs({'pregunta_1': 0})], ronda=1)))
        self.assertEqual(MRS.objects.get().pregunta_1, 3)


# 14 ------------------------------------------------------------------------------------
class HistoricoProtegidoTest(Base):
    def setUp(self):
        super().setUp()
        sincronizar_payload(self.usuaria, payload([mrs({i: 1 for i in ITEMS})], finalizar=True))
        self.cerrado = MRS.objects.get(ronda=1)

    def test_14_una_ronda_cerrada_no_se_modifica_por_ningun_camino_con_save(self):
        self.cerrado.pregunta_1 = 4
        with self.assertRaises(RespuestaHistoricaProtegida):
            self.cerrado.save()
        with self.assertRaises(RespuestaHistoricaProtegida):
            MRS.objects.create(participante=self.ficha(), ronda=1, uuid_local=uuid4())
        self.cerrado.refresh_from_db()
        self.cerrado.ronda = 2
        with self.assertRaises(RespuestaHistoricaProtegida):
            self.cerrado.save()
        self.assertEqual(MRS.objects.get(pk=self.cerrado.pk).pregunta_1, 1)

    def test_14b_la_sincronizacion_con_uuid_antiguo_no_toca_la_ronda_cerrada(self):
        _pasar_plazo()
        res = sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 4}, str(self.cerrado.uuid_local))],
                                                        ronda=2))
        self.assertFalse(res['ok'])
        self.assertEqual(MRS.objects.get(pk=self.cerrado.pk).pregunta_1, 1)

    def test_14c_el_retiro_sigue_borrando_todo(self):
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save()
        self.client.force_login(self.usuaria)
        self.client.post('/retirarse/', {'entiendo': 'on'})
        self.assertFalse(MRS.objects.exists())
        self.assertFalse(RondaEvaluacion.objects.exists())


class MRSAnteriorTest(Base):
    """Ceros de registros anteriores a la 40B-2: nunca se convierten; se confirman o quedan marcados."""

    def _mrs_antiguo(self, ronda_abierta=True):
        sincronizar_payload(self.usuaria, payload([mrs(dict(TODOS_CERO, pregunta_1=3))]))
        fila = MRS.objects.get()
        MRSAnterior40B2.objects.create(mrs=fila)  # lo que hace la migración 0004 con los MRS existentes
        return fila

    def test_14d_los_ceros_antiguos_no_se_presentan_como_respondidos_ni_se_cambian(self):
        fila = self._mrs_antiguo()
        estado = estado_ronda(self.ficha())
        self.assertEqual(estado['mrs_por_confirmar'], ITEMS[1:])
        self.assertEqual(estado['secciones']['mrs']['datos'].get('pregunta_1'), 3)
        self.assertNotIn('pregunta_2', estado['secciones']['mrs']['datos'])
        fila.refresh_from_db()
        self.assertEqual(fila.pregunta_2, 0)  # el valor guardado sigue igual
        self.assertTrue(ronda_es_historica_no_verificable(fila))

    def test_14e_no_se_cierra_con_ceros_sin_confirmar(self):
        fila = self._mrs_antiguo()
        u = str(fila.uuid_local)
        res = sincronizar_payload(self.usuaria, payload([mrs(dict(TODOS_CERO, pregunta_1=3), u)], ronda=1,
                                                        finalizar=True))
        self.assertEqual(res['cierre']['estado'], 'rechazado')
        self.assertEqual(res['cierre']['faltantes'], [{'seccion': 'mrs', 'motivo': 'por_confirmar',
                                                       'preguntas': ITEMS[1:]}])
        # La persona elige de nuevo las 10 respuestas (todas «Ninguna»): ahora sí se cierra.
        res = sincronizar_payload(self.usuaria, payload([mrs(dict(TODOS_CERO, pregunta_1=3), u,
                                                             confirmados=ITEMS[1:])], ronda=1, finalizar=True))
        self.assertTrue(res['ok'], res)
        marca = MRSAnterior40B2.objects.get()
        self.assertEqual(marca.items_confirmados, sorted(ITEMS[1:]))
        self.assertIsNotNone(marca.confirmado_en)

    def test_14f_confirmados_que_no_vienen_en_los_datos_no_cuentan(self):
        fila = self._mrs_antiguo()
        sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 3}, str(fila.uuid_local),
                                                       confirmados=ITEMS)]))
        # Solo cuenta lo que vino respondido en este envío (pregunta_1); los otros 10 no.
        self.assertEqual(MRSAnterior40B2.objects.get().items_confirmados, ['pregunta_1'])
        self.assertEqual(MRSAnterior40B2.objects.get().ceros_por_confirmar(), ITEMS[1:])


# 15 ------------------------------------------------------------------------------------
class IntegridadRegistroTest(Base):
    def test_15_el_registro_de_rondas_sigue_coherente(self):
        for i in range(3):
            sincronizar_payload(self.usuaria, payload([mrs({'pregunta_1': 1})], ronda=None if i == 0 else i + 1,
                                                      finalizar=True))        # rechazado (incompleto)
            res = sincronizar_payload(self.usuaria, payload([mrs({x: 1 for x in ITEMS})], ronda=i + 1,
                                                            finalizar=True))
            self.assertTrue(res['ok'], res)
            _pasar_plazo()
        salida = StringIO()
        call_command('verificar_rondas', stdout=salida)
        self.assertIn('problemas: 0', salida.getvalue())
        rondas = list(RondaEvaluacion.objects.order_by('numero'))
        self.assertEqual([r.estado for r in rondas], ['CERRADA'] * 3 + ['ABIERTA'])
        self.assertTrue(all(r.id_cierre for r in rondas[:3]))
        self.assertEqual(EventoRonda.objects.filter(tipo=TipoEventoRonda.CIERRE_RECHAZADO).count(), 3)

    def test_15b_el_esquema_que_usan_las_pruebas_del_cliente_esta_al_dia(self):
        carpeta = Path(__file__).resolve().parents[1] / 'encuestas' / 'pruebas_js'
        for rol, nombre in ((Usuario.Rol.USUARIA_COMUN, 'usuaria'), (Usuario.Rol.PROFESIONAL_SALUD, 'profesional')):
            with self.subTest(rol=nombre):
                guardado = json.loads((carpeta / f'esquema_{nombre}.json').read_text(encoding='utf-8'))
                self.assertEqual(guardado, json.loads(json.dumps(construir_esquema(rol))))


def _huella_mrs(apps):
    return [tuple(sorted(f.items())) for f in apps.get_model('encuestas', 'MRS').objects.order_by('pk').values()]


class MigracionesTest(TransactionTestCase):
    """0020 (ítems nulos) y rondas 0004 (marcas) sobre PostgreSQL, desde el esquema anterior."""

    ANTES = [('encuestas', '0019_ultima_finalizacion'), ('rondas', '0003_unicidad_secciones')]

    def _migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        return MigrationExecutor(connection).loader.project_state(destino).apps

    def setUp(self):
        self.apps = self._migrar(self.ANTES)

    def tearDown(self):
        apps = MigrationExecutor(connection).loader.project_state(
            MigrationExecutor(connection).loader.graph.leaf_nodes()).apps
        try:
            apps.get_model('rondas', 'MRSAnterior40B2').objects.all().delete()
        except Exception:  # noqa: BLE001  (la tabla puede no existir todavía)
            pass
        self._migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def _datos_anteriores(self):
        Ident = self.apps.get_model('encuestas', 'Identificacion')
        Mrs = self.apps.get_model('encuestas', 'MRS')
        a = Ident.objects.create(rut_hash='a' * 64, ronda_actual=2, fecha_nacimiento='1975-05-20')
        Mrs.objects.create(participante=a, ronda=1, uuid_local=uuid4(), pregunta_1=3)     # resto: 0 por defecto
        b = Ident.objects.create(rut_hash='b' * 64, ronda_actual=1, fecha_nacimiento='1970-01-01')
        Mrs.objects.create(participante=b, ronda=1, uuid_local=uuid4(), **TODOS_CERO)

    def test_las_migraciones_no_cambian_ningun_valor_y_marcan_lo_existente(self):
        self._datos_anteriores()
        antes = _huella_mrs(self.apps)
        apps = self._migrar([('rondas', '0004_mrs_anterior_40b2')])
        self.assertEqual(_huella_mrs(apps), antes)                      # ningún 0 se volvió nulo
        Mrs = apps.get_model('encuestas', 'MRS')
        self.assertFalse(Mrs.objects.filter(pregunta_2__isnull=True).exists())
        self.assertEqual(apps.get_model('rondas', 'MRSAnterior40B2').objects.count(), 2)
        with connection.cursor() as c:
            c.execute("SELECT is_nullable FROM information_schema.columns "
                      "WHERE table_name='encuestas_mrs' AND column_name LIKE 'pregunta_%%'")
            self.assertEqual({f[0] for f in c.fetchall()}, {'YES'})

    def test_las_reversas_se_niegan_a_perder_informacion(self):
        self._datos_anteriores()
        apps = self._migrar([('rondas', '0004_mrs_anterior_40b2')])
        with self.assertRaisesMessage(RuntimeError, 'Reversa rondas 0004 detenida'):
            self._migrar([('rondas', '0003_unicidad_secciones')])
        self.assertEqual(apps.get_model('rondas', 'MRSAnterior40B2').objects.count(), 2)
        # Sin marcas, la reversa de la 0020 se niega si hay ítems sin respuesta.
        apps.get_model('rondas', 'MRSAnterior40B2').objects.all().delete()
        self._migrar([('rondas', '0003_unicidad_secciones')])
        apps = MigrationExecutor(connection).loader.project_state(
            [('encuestas', '0020_mrs_items_sin_respuesta_nulos'), ('rondas', '0003_unicidad_secciones')]).apps
        apps.get_model('encuestas', 'MRS').objects.filter(pregunta_1=3).update(pregunta_5=None)
        with self.assertRaisesMessage(RuntimeError, 'Reversa 0020 detenida'):
            self._migrar(self.ANTES)
        self.assertEqual(apps.get_model('encuestas', 'MRS').objects.filter(pregunta_5__isnull=True).count(), 1)


# Fase 40: el cliente real siempre envía la participación vigente de la usuaria.
from apps.rondas.pruebas_comunes import sincronizar_como_cliente as sincronizar_payload  # noqa: E402,F811
