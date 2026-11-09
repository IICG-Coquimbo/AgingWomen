"""Fase 40, Etapa 2: consentimiento presencial, constancia del retiro e inactividad. Datos ficticios."""
import time
from uuid import uuid4

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.encuestas.models import MRS, Identificacion
from apps.encuestas.sync import ConflictoRonda
from apps.rondas.pruebas_comunes import sincronizar_como_cliente
from apps.rondas.test_40b3 import IDENT, bloque_mrs

from . import constancia_retiro
from .inactividad import CLAVE
from .models import ConsentimientoPresencial, Usuario
from .privacidad import participacion_de, sin_consentimiento_vigente
from .rut import hash_rut

RUT = '9.876.543-3'
URL = '/profesional/consentimiento-presencial/'
CLAVE_USUARIA = 'Clave-ficticia-2026'


class Base(TestCase):
    def setUp(self):
        self.prof = Usuario.objects.create_user(rut='22.222.222-2', email='p@ficticio.cl',
                                                rol=Usuario.Rol.PROFESIONAL_SALUD)

    def registrar(self, **extra):
        datos = dict({'rut': RUT, 'registrar': '1', 'folio_documento': 'CI-2026-0001',
                      'custodia': 'Archivo del proyecto (ficticio)', 'declaracion': 'on'}, **extra)
        self.client.force_login(self.prof)
        return self.client.post(URL, {k: v for k, v in datos.items() if v is not None})

    def sync_prof(self, ident):
        return sincronizar_como_cliente(self.prof, {'protocolo': 2, 'identificacion': ident, 'secciones': [
            bloque_mrs({'pregunta_1': 2})]})


class PresencialSinCuentaTest(Base):
    def test_sin_constancia_no_se_registra(self):
        for faltante in ('folio_documento', 'custodia', 'declaracion'):
            resp = self.registrar(**{faltante: None})
            self.assertEqual(resp.status_code, 400, faltante)
        self.assertEqual(self.registrar(folio_documento='a').status_code, 400)       # folio inválido
        self.assertFalse(ConsentimientoPresencial.objects.exists())
        self.assertTrue(sin_consentimiento_vigente(hash_rut(RUT)))
        with self.assertRaises(ConflictoRonda):
            self.sync_prof({'uuid_local': str(uuid4()), 'rut': RUT, 'datos': dict(IDENT)})
        self.assertEqual(self.client.post('/profesional/paciente/nueva/', {'rut': RUT}).status_code, 403)

    def test_registro_valido_y_sin_duplicados(self):
        resp = self.registrar()
        self.assertContains(resp, 'data-registrado')
        c = ConsentimientoPresencial.objects.get()
        self.assertEqual((c.rut_hash, c.modalidad, c.verificacion, c.registrado_por, c.folio_documento),
                         (hash_rut(RUT), 'PRESENCIAL', 'DOCUMENTO_FIRMADO', self.prof, 'CI-2026-0001'))
        self.assertTrue(c.version.startswith('sha256:'))
        self.assertIsNone(c.usuario)
        # Ya vigente: no se registra otra vez; el mismo folio no sirve para otra persona.
        self.assertContains(self.registrar(folio_documento='CI-2026-0002'), 'data-ya-vigente')
        self.client.force_login(self.prof)
        otro = self.client.post(URL, {'rut': '7.654.321-6', 'registrar': '1', 'folio_documento': 'CI-2026-0001',
                                      'custodia': 'Archivo', 'declaracion': 'on'})
        self.assertEqual(otro.status_code, 400)
        self.assertEqual(ConsentimientoPresencial.objects.count(), 1)
        # Ahora la profesional puede registrar; dos envíos con el RUT no duplican la ficha.
        self.assertEqual(self.client.post('/profesional/paciente/nueva/', {'rut': RUT}).status_code, 200)
        for _ in range(2):
            self.assertTrue(self.sync_prof({'uuid_local': str(uuid4()), 'rut': RUT, 'datos': dict(IDENT)})['ok'])
        self.assertEqual(Identificacion.objects.filter(rut_hash=hash_rut(RUT)).count(), 1)
        # El buscador ya no ofrece registrar consentimiento.
        self.assertNotContains(self.client.post('/profesional/buscar/', {'rut': RUT}), 'data-sin-consentimiento')

    def test_permisos_y_rut_fuera_de_la_url(self):
        self.assertEqual(self.client.post(URL, {'rut': RUT}).status_code, 302)               # anónima
        comun = Usuario.objects.create_user(rut='11.111.111-1', email='u@ficticio.cl')
        self.client.force_login(comun)
        self.assertEqual(self.client.post(URL, {'rut': RUT, 'registrar': '1'}).status_code, 403)
        self.client.force_login(self.prof)
        self.assertEqual(self.client.get(URL, {'rut': RUT}).status_code, 405)                # solo POST
        resp = self.client.post('/profesional/buscar/', {'rut': RUT})
        self.assertContains(resp, 'data-sin-consentimiento')
        self.assertContains(resp, f'action="{URL}"')
        self.assertFalse(ConsentimientoPresencial.objects.exists())


class PresencialConCuentaYRetiroTest(Base):
    def setUp(self):
        super().setUp()
        self.usuaria = Usuario.objects.create_user(rut=RUT, email='u@ficticio.cl', password=CLAVE_USUARIA)
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save()
        res = sincronizar_como_cliente(self.usuaria, {'protocolo': 2, 'ronda': 1, 'identificacion': {
            'uuid_local': str(uuid4()), 'datos': dict(IDENT)}, 'secciones': [bloque_mrs({'pregunta_1': 3})]})
        self.assertTrue(res['ok'], res)
        self.participacion_anterior = participacion_de(self.usuaria)

    def retirarse(self):
        self.client.force_login(self.usuaria)
        return self.client.post('/retirarse/', {'entiendo': 'on'})

    def test_retiro_borra_salud_y_entrega_constancia_sin_guardarla(self):
        resp = self.retirarse()
        self.assertEqual(Identificacion.objects.count(), 0)
        self.assertEqual(MRS.objects.count(), 0)
        self.usuaria.refresh_from_db()
        self.assertIsNone(self.usuaria.consentimiento_aceptado_en)
        comprobante = resp.context['comprobante']
        self.assertContains(resp, 'data-constancia-retiro')
        self.assertEqual(resp['Cache-Control'], 'no-store')
        datos = constancia_retiro.verificar(comprobante, rut=RUT)
        self.assertEqual(datos['codigo'], resp.context['constancia']['codigo'])
        self.assertNotIn('pregunta', comprobante)
        self.assertIsNone(constancia_retiro.verificar(comprobante, rut='7.654.321-6'))   # otra persona
        self.assertIsNone(constancia_retiro.verificar(comprobante[:-2] + 'xx'))           # alterado

    def test_profesional_no_reactiva_un_retiro_sin_la_persona(self):
        self.retirarse()
        # Sin la contraseña de ella no se registra nada, aunque haya documento.
        self.assertEqual(self.registrar().status_code, 400)
        self.assertEqual(self.registrar(clave_participante='otra-clave').status_code, 400)
        self.usuaria.refresh_from_db()
        self.assertIsNone(self.usuaria.consentimiento_aceptado_en)
        self.assertFalse(ConsentimientoPresencial.objects.exists())
        # Con su contraseña (aceptación expresa en persona): participación NUEVA y sin datos anteriores.
        resp = self.registrar(clave_participante=CLAVE_USUARIA)
        self.assertContains(resp, 'data-registrado')
        self.usuaria.refresh_from_db()
        c = ConsentimientoPresencial.objects.get()
        self.assertEqual((c.usuario, c.verificacion), (self.usuaria, 'CLAVE_CUENTA'))
        self.assertNotEqual(participacion_de(self.usuaria), self.participacion_anterior)
        self.assertEqual(Identificacion.objects.count(), 0)                         # nada se recupera
        # Un envío preparado en la participación anterior (cola offline) se rechaza sin escribir.
        with self.assertRaises(ConflictoRonda) as ctx:
            from apps.encuestas.sync import sincronizar_payload
            sincronizar_payload(self.usuaria, {'protocolo': 2, 'ronda': 1, 'participacion': self.participacion_anterior,
                                               'identificacion': {'uuid_local': str(uuid4()), 'datos': dict(IDENT)},
                                               'secciones': [bloque_mrs({'pregunta_1': 3})]})
        self.assertEqual(ctx.exception.codigo, 'participacion_anterior')
        self.assertEqual(Identificacion.objects.count(), 0)
        # Un nuevo retiro también elimina el consentimiento presencial.
        self.retirarse()
        self.assertFalse(ConsentimientoPresencial.objects.exists())

    def test_contrasena_no_se_guarda(self):
        self.retirarse()
        self.registrar(clave_participante=CLAVE_USUARIA)
        c = ConsentimientoPresencial.objects.values()[0]
        self.assertNotIn(CLAVE_USUARIA, str(c))


@override_settings(SESION_INACTIVIDAD_SEGUNDOS=1800)
class InactividadTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@ficticio.cl', password=CLAVE_USUARIA)
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save()
        self.assertTrue(self.client.login(username='11.111.111-1', password=CLAVE_USUARIA))

    def marca(self, valor=None):
        s = self.client.session
        if valor is not None:
            s[CLAVE] = valor
            s.save()
        return s.get(CLAVE)

    def test_ingreso_marca_y_pagina_informa_el_limite(self):
        self.assertAlmostEqual(self.marca(), time.time(), delta=5)
        resp = self.client.get('/mi-tablero/')
        self.assertContains(resp, 'data-inactividad="1800"')
        self.assertContains(resp, 'data-aviso="120"')

    def test_vence_en_el_servidor_pagina_y_api(self):
        self.marca(int(time.time()) - 1801)
        resp = self.client.get('/mi-tablero/')
        self.assertRedirects(resp, '/cuenta/ingresar/?inactividad=1', fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertContains(self.client.get('/cuenta/ingresar/?inactividad=1'), 'data-aviso-inactividad')
        self.client.login(username='11.111.111-1', password=CLAVE_USUARIA)
        self.marca(int(time.time()) - 1801)
        resp = self.client.get('/api/clave-local/', HTTP_X_SEGUNDO_PLANO='1')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['codigo'], 'sesion_vencida')
        self.assertEqual(self.client.get('/api/clave-local/').status_code, 401)   # sigue cerrada

    def test_segundo_plano_no_extiende_y_la_actividad_si(self):
        viejo = int(time.time()) - 1000
        self.marca(viejo)
        self.assertEqual(self.client.get('/api/clave-local/', HTTP_X_SEGUNDO_PLANO='1').status_code, 200)
        self.assertEqual(self.marca(), viejo)
        self.assertEqual(self.client.post('/cuenta/actividad/').status_code, 204)
        self.assertAlmostEqual(self.marca(), time.time(), delta=5)
        self.client.logout()
        self.assertEqual(self.client.post('/cuenta/actividad/').status_code, 401)

    @override_settings(SESION_INACTIVIDAD_SEGUNDOS=60)
    def test_limite_configurable(self):
        self.marca(int(time.time()) - 61)
        self.assertEqual(self.client.get('/mi-tablero/').status_code, 302)
