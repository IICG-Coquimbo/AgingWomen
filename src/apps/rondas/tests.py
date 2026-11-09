"""
Pruebas de la Fase 40B-1 (registro de rondas). Corren en PostgreSQL (docker compose).

- RegistroTest: apertura, cierre, invariantes y compatibilidad con el cierre actual.
- ObservacionTest: el verificador de completitud registra pero no rechaza.
- MigracionesTest: retrocarga sin fechas inventadas, sin tocar respuestas, y la
  verificación de duplicados que se detiene antes de imponer la unicidad.
- ConcurrenciaTest: unicidad bajo escrituras simultáneas reales.
"""
import hashlib
import threading
from datetime import timedelta
from io import StringIO
from unittest import mock
from uuid import uuid4

from django.core.management import call_command
from django.db import IntegrityError, connection, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.encuestas.models import MRS, HabitosDeVida, Identificacion
from apps.encuestas.sync import sincronizar_payload
from apps.usuarios.models import Usuario

from . import completitud
from .models import (VERSION_CUESTIONARIO_ACTUAL, EstadoRonda, EventoRonda, EventoRondaInmutable, OrigenRonda,
                     RondaEvaluacion, TipoEventoRonda)
from .senales import actualizar_registro
from .pruebas_comunes import protocolo2


def _sync(usuario, payload):
    """Fase 40B-2: cierre con protocolo 2 y lo obligatorio completo (ver pruebas_comunes)."""
    return sincronizar_payload(usuario, protocolo2(usuario, payload))

IDENT = {
    'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
    'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
    'comuna': 'Santiago', 'region_residencia': '13',
}


def _payload(finalizar=False, **mrs):
    return {
        'identificacion': {'uuid_local': str(uuid4()), 'datos': dict(IDENT)},
        'secciones': [{'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': True,
                       'datos': mrs or {'pregunta_1': 2}}],
        'finalizar': finalizar,
    }


def _pasar_plazo():
    Identificacion.objects.update(ultima_finalizacion_en=timezone.now() - timedelta(days=16))


class RegistroTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')

    def _ficha(self):
        return Identificacion.objects.get(usuario=self.usuaria)

    def test_crear_la_ficha_abre_la_ronda_1(self):
        sincronizar_payload(self.usuaria, _payload())
        ficha = self._ficha()
        ronda = RondaEvaluacion.objects.get(participante=ficha)
        self.assertEqual((ronda.numero, ronda.estado, ronda.origen), (1, EstadoRonda.ABIERTA, OrigenRonda.NORMAL))
        self.assertEqual(ronda.version_cuestionario, VERSION_CUESTIONARIO_ACTUAL)
        self.assertIsNone(ronda.cerrada_en)
        self.assertEqual(list(ronda.eventos.values_list('tipo', flat=True)), [TipoEventoRonda.APERTURA])

    def test_el_cierre_actual_sigue_igual_y_queda_registrado(self):
        res = _sync(self.usuaria, _payload(finalizar=True))
        self.assertTrue(res['ok'])
        self.assertEqual(res['ronda_actual'], 2)          # mismo resultado que antes de la 40B-1
        ficha = self._ficha()
        r1, r2 = RondaEvaluacion.objects.filter(participante=ficha).order_by('numero')
        self.assertEqual(r1.estado, EstadoRonda.CERRADA)
        self.assertEqual(r1.cerrada_en, ficha.ultima_finalizacion_en)   # la hora que registró sync.py
        self.assertEqual(r2.estado, EstadoRonda.ABIERTA)
        self.assertEqual(r2.numero, ficha.ronda_actual)
        self.assertEqual(r2.abierta_en, r1.cerrada_en)
        self.assertEqual(MRS.objects.get().ronda, 1)       # las respuestas no cambian

    def test_varias_rondas_mantienen_la_invariante(self):
        for _ in range(3):
            _sync(self.usuaria, _payload(finalizar=True))
            _pasar_plazo()
        ficha = self._ficha()
        self.assertEqual(ficha.ronda_actual, 4)
        rondas = list(RondaEvaluacion.objects.filter(participante=ficha).order_by('numero'))
        self.assertEqual([r.numero for r in rondas], [1, 2, 3, 4])
        self.assertEqual([r.estado for r in rondas], ['CERRADA'] * 3 + ['ABIERTA'])
        self.assertEqual(RondaEvaluacion.objects.filter(participante=ficha, estado='ABIERTA').count(), 1)
        salida = StringIO()
        call_command('verificar_rondas', stdout=salida)
        self.assertIn('problemas: 0', salida.getvalue())

    def test_guardar_sin_cerrar_no_crea_eventos(self):
        sincronizar_payload(self.usuaria, _payload())
        antes = EventoRonda.objects.count()
        sincronizar_payload(self.usuaria, _payload(pregunta_2=1))
        self.assertEqual(EventoRonda.objects.count(), antes)
        self.assertEqual(RondaEvaluacion.objects.count(), 1)

    def test_ficha_sin_cuenta_creada_por_profesional(self):
        ficha = Identificacion.objects.create(rut_hash='0' * 64, fecha_nacimiento='1975-05-20')
        self.assertIsNone(ficha.usuario_id)
        self.assertEqual(RondaEvaluacion.objects.get(participante=ficha).estado, EstadoRonda.ABIERTA)

    def test_salto_de_ronda_se_registra_como_incoherencia_sin_tocar_nada(self):
        sincronizar_payload(self.usuaria, _payload())
        ficha = self._ficha()
        ficha.ronda_actual = 3
        ficha.save(update_fields=['ronda_actual'])
        ronda = RondaEvaluacion.objects.get(participante=ficha)
        self.assertEqual((ronda.numero, ronda.estado), (1, EstadoRonda.ABIERTA))
        self.assertTrue(ronda.eventos.filter(tipo=TipoEventoRonda.INCOHERENCIA).exists())
        with self.assertRaises(SystemExit):
            call_command('verificar_rondas', stdout=StringIO())

    def test_un_fallo_del_registro_no_impide_guardar(self):
        with mock.patch('apps.rondas.senales.actualizar_registro', side_effect=RuntimeError('fallo simulado')), \
                self.assertLogs('apps.rondas.senales', level='ERROR'):
            res = _sync(self.usuaria, _payload(finalizar=True))
        self.assertTrue(res['ok'])
        self.assertEqual(self._ficha().ronda_actual, 2)

    def test_retiro_borra_el_registro_como_el_resto_de_la_ficha(self):
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save()
        _sync(self.usuaria, _payload(finalizar=True))
        self.client.force_login(self.usuaria)
        self.client.post('/retirarse/', {'entiendo': 'on'})
        self.assertFalse(RondaEvaluacion.objects.exists())
        self.assertFalse(EventoRonda.objects.exists())

    def test_eventos_de_solo_insercion(self):
        sincronizar_payload(self.usuaria, _payload())
        evento = EventoRonda.objects.get()
        evento.datos = {'cambiado': True}
        with self.assertRaises(EventoRondaInmutable):
            evento.save()
        with self.assertRaises(EventoRondaInmutable):
            evento.delete()

    def test_restricciones_de_la_base(self):
        sincronizar_payload(self.usuaria, _payload())
        ficha = self._ficha()
        with self.assertRaises(IntegrityError), transaction.atomic():   # segunda ronda abierta
            RondaEvaluacion.objects.create(participante=ficha, numero=2, estado='ABIERTA', origen='NORMAL',
                                           version_cuestionario='x')
        with self.assertRaises(IntegrityError), transaction.atomic():   # número repetido
            RondaEvaluacion.objects.create(participante=ficha, numero=1, estado='CERRADA', origen='NORMAL',
                                           version_cuestionario='x')
        with self.assertRaises(IntegrityError), transaction.atomic():   # abierta con fecha de cierre
            RondaEvaluacion.objects.filter(participante=ficha).update(cerrada_en=timezone.now())
        with self.assertRaises(IntegrityError), transaction.atomic():   # numeración desde 1
            RondaEvaluacion.objects.create(participante=ficha, numero=0, estado='CERRADA', origen='NORMAL',
                                           version_cuestionario='x')

    def test_unicidad_por_seccion_y_ronda(self):
        sincronizar_payload(self.usuaria, _payload())
        ficha = self._ficha()
        with self.assertRaises(IntegrityError), transaction.atomic():
            MRS.objects.create(participante=ficha, ronda=1, uuid_local=uuid4())
        # HabitosDeVida queda fuera de la restricción por el duplicado de la base de desarrollo.
        HabitosDeVida.objects.create(participante=ficha, ronda=1, uuid_local=uuid4())
        HabitosDeVida.objects.create(participante=ficha, ronda=1, uuid_local=uuid4())


class ObservacionTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')

    def test_la_senal_observa_un_cierre_hecho_fuera_del_servicio(self):
        # 40B-1 observaba el cierre incompleto de encuestas/tests.py:303 sin rechazarlo. Desde la
        # 40B-2 ese cierre se rechaza (RC-1); la señal queda como respaldo si algún camino ajeno al
        # servicio avanza ronda_actual, y entonces sigue registrando la completitud en observación.
        sincronizar_payload(self.usuaria, _payload())
        ficha = Identificacion.objects.get()
        ficha.ronda_actual = 2
        ficha.save(update_fields=['ronda_actual'])
        evento = EventoRonda.objects.get(tipo=TipoEventoRonda.CIERRE)
        self.assertEqual(evento.datos['via'], 'senal_fuera_del_servicio')
        obs = evento.datos['completitud']
        self.assertEqual(obs['modo'], 'observacion')
        self.assertFalse(obs['completa'])
        ausentes = {f['seccion'] for f in obs['faltantes'] if f['motivo'] == 'ausente'}
        self.assertTrue({'empa', 'habitos_de_vida', 'actividad_fisica', 'conocimiento_sistema'} <= ausentes)
        self.assertNotIn('mrs', ausentes)
        self.assertIn('MRS', obs['limitaciones'][0])

    def test_el_evento_no_guarda_valores_de_respuestas(self):
        _sync(self.usuaria, _payload(finalizar=True, pregunta_1=3))
        datos = EventoRonda.objects.get(tipo=TipoEventoRonda.CIERRE).datos
        texto = str(datos)
        for valor in ('1975-05-20', 'Santiago', "'pregunta_1': 3"):
            self.assertNotIn(valor, texto)

    def test_trabajo_solo_si_trabaja(self):
        sincronizar_payload(self.usuaria, _payload())
        ficha = Identificacion.objects.get()
        ficha.trabaja_actualmente = False
        obs = completitud.evaluar(ficha, 1)
        self.assertNotIn('trabajo', {f['seccion'] for f in obs['faltantes']})
        ficha.trabaja_actualmente = True
        obs = completitud.evaluar(ficha, 1)
        self.assertIn('trabajo', {f['seccion'] for f in obs['faltantes']})

    def test_reglas_iguales_a_las_del_cliente(self):
        regla = {'campo': 'cuida_otras_personas', 'valor': 'SI'}
        self.assertTrue(completitud.condicion_cumplida(regla, {'cuida_otras_personas': 'SI'}))
        self.assertFalse(completitud.condicion_cumplida(regla, {'cuida_otras_personas': 'NO'}))
        contiene = {'campo': 'a_quien_cuida', 'operador': 'contiene', 'valor': 'Otro'}
        self.assertTrue(completitud.condicion_cumplida(contiene, {'a_quien_cuida': 'Hijos, Otro'}))
        self.assertFalse(completitud.condicion_cumplida(contiene, {'a_quien_cuida': 'Otros'}))
        meses = {'campo': 'fecha_ultima_menstruacion', 'operador': 'meses_desde_lt', 'valor': 12}
        self.assertTrue(completitud.condicion_cumplida(meses, {'fecha_ultima_menstruacion': 'ilegible'}))
        hace_dos_anios = str(timezone.now().year - 2)
        self.assertFalse(completitud.condicion_cumplida(meses, {'fecha_ultima_menstruacion': hace_dos_anios}))
        # Ocultar en cadena: si la madre está oculta, la hija también.
        seccion = {'preguntas': [
            {'nombre': 'a', 'mostrar_si': {'campo': 'x', 'valor': 'SI'}},
            {'nombre': 'b', 'mostrar_si': {'campo': 'a', 'valor': 'SI'}},
        ]}
        self.assertEqual(completitud.preguntas_visibles(seccion, {'x': 'NO', 'a': 'SI'}), [])


def _huella_respuestas(apps):
    h = hashlib.sha256()
    for nombre in ('Identificacion', 'MRS', 'HabitosDeVida', 'TareasCuidado'):
        for fila in apps.get_model('encuestas', nombre).objects.order_by('pk').values():
            h.update(repr(sorted(fila.items())).encode())
    return h.hexdigest()


class MigracionesTest(TransactionTestCase):
    """Retrocarga y unicidad sobre PostgreSQL, partiendo del esquema anterior a la 40B-1."""

    def _migrar(self, destino):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(destino)
        # El estado «sin rondas» se obtiene del último nodo anterior a la app.
        nodos = [('encuestas', '0019_ultima_finalizacion') if n == ('rondas', None) else n for n in destino]
        return MigrationExecutor(connection).loader.project_state(nodos).apps

    def setUp(self):
        self.apps = self._migrar([('rondas', None)])

    def tearDown(self):
        self._migrar(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def _datos_anteriores(self, con_duplicado=False):
        Ident = self.apps.get_model('encuestas', 'Identificacion')
        Mrs = self.apps.get_model('encuestas', 'MRS')
        Hab = self.apps.get_model('encuestas', 'HabitosDeVida')
        fin = timezone.now() - timedelta(days=40)
        tres = Ident.objects.create(rut_hash='a' * 64, ronda_actual=3, ultima_finalizacion_en=fin,
                                    fecha_nacimiento='1975-05-20')
        Mrs.objects.create(participante=tres, ronda=1, uuid_local=uuid4(), pregunta_1=3)
        Hab.objects.create(participante=tres, ronda=2, uuid_local=uuid4())      # ronda 2 sin MRS
        nueva = Ident.objects.create(rut_hash='b' * 64, ronda_actual=1, fecha_nacimiento='1970-01-01')
        Mrs.objects.create(participante=nueva, ronda=1, uuid_local=uuid4(), pregunta_1=1)
        if con_duplicado:
            Mrs.objects.create(participante=nueva, ronda=1, uuid_local=uuid4(), pregunta_1=2)
        return tres.pk, nueva.pk, fin

    def test_retrocarga_sin_inventar_y_sin_tocar_respuestas(self):
        tres, nueva, fin = self._datos_anteriores()
        antes = _huella_respuestas(self.apps)
        apps = self._migrar([('rondas', '0003_unicidad_secciones')])
        Ronda = apps.get_model('rondas', 'RondaEvaluacion')
        self.assertEqual(_huella_respuestas(apps), antes)                      # respuestas intactas
        self.assertEqual(apps.get_model('encuestas', 'Identificacion').objects.count(), 2)

        rondas = list(Ronda.objects.filter(participante_id=tres).order_by('numero'))
        self.assertEqual([(r.numero, r.estado) for r in rondas], [(1, 'CERRADA'), (2, 'CERRADA'), (3, 'ABIERTA')])
        for r in rondas:
            self.assertIsNone(r.abierta_en)                                     # sin fechas inventadas
            self.assertIsNone(r.cerrada_en)
            self.assertIsNone(r.cerrada_por_id)
            self.assertEqual(r.origen, 'RETROCARGA')
            self.assertEqual(r.version_cuestionario, 'DESCONOCIDA_ANTERIOR_40B')
            self.assertFalse(r.observaciones['instantanea_disponible'])
        self.assertEqual([r.cerrada_por_rol for r in rondas], ['DESCONOCIDO', 'DESCONOCIDO', ''])
        self.assertEqual(rondas[1].observaciones['ultima_finalizacion_registrada_referencial'], fin.isoformat())
        self.assertNotIn('ultima_finalizacion_registrada_referencial', rondas[0].observaciones)
        self.assertEqual(rondas[0].observaciones['secciones_presentes'], ['mrs'])
        self.assertTrue(rondas[1].observaciones['sin_mrs'])
        self.assertTrue(rondas[2].observaciones['vacia'])
        self.assertEqual(Ronda.objects.get(participante_id=nueva).estado, 'ABIERTA')
        self.assertEqual(apps.get_model('rondas', 'EventoRonda').objects.filter(tipo='RETROCARGA').count(), 4)

    def test_duplicados_detienen_la_unicidad_sin_cambiar_nada(self):
        self._datos_anteriores(con_duplicado=True)
        self._migrar([('rondas', '0002_retrocarga')])
        antes = _huella_respuestas(self.apps)
        with self.assertRaisesMessage(RuntimeError, 'hay secciones duplicadas'):
            self._migrar([('rondas', '0003_unicidad_secciones')])
        with connection.cursor() as c:
            c.execute("SELECT count(*) FROM pg_indexes WHERE indexname LIKE '%%participante_ronda_uniq'")
            self.assertEqual(c.fetchone()[0], 0)
        self.assertEqual(_huella_respuestas(self.apps), antes)
        self.assertEqual(self.apps.get_model('encuestas', 'MRS').objects.count(), 3)  # nada se borró
        # Para que tearDown pueda volver al esquema completo.
        self.apps.get_model('encuestas', 'MRS').objects.filter(pregunta_1=2).delete()

    def test_reversa_limpia(self):
        self._datos_anteriores()
        antes = _huella_respuestas(self.apps)
        self._migrar([('rondas', '0003_unicidad_secciones')])
        apps = self._migrar([('rondas', None)])
        self.assertEqual(_huella_respuestas(apps), antes)
        with connection.cursor() as c:
            c.execute("SELECT count(*) FROM pg_tables WHERE tablename LIKE 'rondas_%%'")
            self.assertEqual(c.fetchone()[0], 0)


class ConcurrenciaTest(TransactionTestCase):
    """Escrituras simultáneas reales en PostgreSQL (un hilo = una conexión)."""

    def _en_paralelo(self, funcion, n=2):
        barrera = threading.Barrier(n)
        resultados = []

        def correr():
            try:
                barrera.wait()
                funcion()
                resultados.append('ok')
            except IntegrityError:
                resultados.append('integrity')
            finally:
                connections.close_all()

        hilos = [threading.Thread(target=correr) for _ in range(n)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        return sorted(resultados)

    def test_dos_mrs_simultaneos_para_la_misma_ronda(self):
        ficha = Identificacion.objects.create(rut_hash='c' * 64, fecha_nacimiento='1975-05-20')
        res = self._en_paralelo(lambda: MRS.objects.create(participante_id=ficha.pk, ronda=1, uuid_local=uuid4()))
        self.assertEqual(res, ['integrity', 'ok'])
        self.assertEqual(MRS.objects.filter(participante=ficha, ronda=1).count(), 1)

    def test_dos_aperturas_simultaneas(self):
        ficha = Identificacion.objects.create(rut_hash='d' * 64, fecha_nacimiento='1975-05-20')
        RondaEvaluacion.objects.filter(participante=ficha).delete()

        def abrir():
            with transaction.atomic():
                actualizar_registro(Identificacion.objects.get(pk=ficha.pk))

        self._en_paralelo(abrir)
        self.assertEqual(RondaEvaluacion.objects.filter(participante=ficha, estado='ABIERTA').count(), 1)
