"""
Fase 40, pendientes de consentimiento (datos ficticios, base de pruebas aislada):
1. retiro presencial de una mujer sin cuenta;
2. registros presenciales antiguos sin constancia verificable;
3. límite de intentos de contraseña en los formularios presenciales.
"""
import time
from io import StringIO
from uuid import uuid4

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.encuestas.estadisticas import motivo_exclusion
from apps.encuestas.models import MRS, Identificacion
from apps.encuestas.sync import ConflictoRonda, ErrorSincronizacion, sincronizar_payload
from apps.rondas.pruebas_comunes import con_participacion, consentimiento_presencial, sincronizar_como_cliente
from apps.rondas.test_40b3 import IDENT, bloque_mrs

from . import constancia_retiro, intentos
from .models import ConsentimientoPresencial, Usuario
from .privacidad import participacion_paciente, sin_consentimiento_vigente
from .rut import hash_rut

RUT = '9.876.543-3'
RUT_OTRA = '7.654.321-6'
CLAVE_PROF = 'Clave-profesional-ficticia-2026'
CLAVE_USUARIA = 'Clave-usuaria-ficticia-2026'
URL_RETIRO = '/profesional/retiro-presencial/'
URL_CONSENT = '/profesional/consentimiento-presencial/'


class Base(TestCase):
    def setUp(self):
        cache.clear()
        self.prof = Usuario.objects.create_user(rut='22.222.222-2', email='p@ficticio.cl', password=CLAVE_PROF,
                                                rol=Usuario.Rol.PROFESIONAL_SALUD)
        self.client.force_login(self.prof)

    def payload(self, ident, mrs=None):
        return {'protocolo': 2, 'identificacion': ident, 'secciones': [bloque_mrs(mrs or {'pregunta_1': 2})]}

    def registrar_paciente_sin_cuenta(self, rut=RUT):
        consentimiento_presencial(rut, self.prof)
        res = sincronizar_como_cliente(self.prof, self.payload({'uuid_local': str(uuid4()), 'rut': rut,
                                                                 'datos': dict(IDENT)}))
        self.assertTrue(res['ok'], res)
        return Identificacion.objects.get(pk=res['paciente_id'])

    def retiro(self, **extra):
        datos = dict({'rut': RUT, 'folio_revocacion': 'RV-2026-0001', 'custodia': 'Archivo ficticio',
                      'declaracion': 'on', 'confirmo': 'on', 'clave_profesional': CLAVE_PROF}, **extra)
        return self.client.post(URL_RETIRO, {k: v for k, v in datos.items() if v is not None})


# ---------------------------------------------------------------------------
# 1. Retiro presencial de una mujer sin cuenta
# ---------------------------------------------------------------------------
class RetiroPresencialTest(Base):
    def test_permisos_y_rut_fuera_de_la_url(self):
        self.client.logout()
        self.assertEqual(self.client.post(URL_RETIRO, {'rut': RUT}).status_code, 302)          # anónima
        comun = Usuario.objects.create_user(rut='11.111.111-1', email='u@ficticio.cl')
        self.client.force_login(comun)
        self.assertEqual(self.client.post(URL_RETIRO, {'rut': RUT}).status_code, 403)          # usuaria común
        self.client.force_login(self.prof)
        resp = self.client.get(URL_RETIRO)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'method="post"')
        self.assertIn('no-cache', resp['Cache-Control'])
        self.assertContains(self.client.post('/profesional/buscar/', {'rut': RUT}), 'data-enlace-retiro-presencial')

    def test_sin_autorizacion_completa_no_borra_nada(self):
        ficha = self.registrar_paciente_sin_cuenta()
        for faltante in ('folio_revocacion', 'custodia', 'declaracion', 'confirmo', 'clave_profesional'):
            self.assertEqual(self.retiro(**{faltante: None}).status_code, 400, faltante)
        self.assertEqual(self.retiro(folio_revocacion='x').status_code, 400)
        resp = self.retiro(clave_profesional='incorrecta')
        self.assertEqual(resp.status_code, 400)
        self.assertContains(resp, intentos.MENSAJE_CLAVE_INCORRECTA, status_code=400)
        self.assertTrue(Identificacion.objects.filter(pk=ficha.pk).exists())
        self.assertEqual(MRS.objects.filter(participante=ficha).count(), 1)
        self.assertTrue(ConsentimientoPresencial.objects.filter(rut_hash=hash_rut(RUT)).exists())

    def test_retiro_borra_todo_y_entrega_comprobante_verificable(self):
        ficha = self.registrar_paciente_sin_cuenta()
        otra = self.registrar_paciente_sin_cuenta(RUT_OTRA)
        resp = self.retiro()
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-retiro-registrado')
        self.assertIn('no-store', resp['Cache-Control'])
        self.assertFalse(Identificacion.objects.filter(pk=ficha.pk).exists())
        self.assertEqual(MRS.objects.filter(participante_id=ficha.pk).count(), 0)
        self.assertFalse(ConsentimientoPresencial.objects.filter(rut_hash=hash_rut(RUT)).exists())
        self.assertTrue(sin_consentimiento_vigente(hash_rut(RUT)))
        # La otra persona no se toca.
        self.assertTrue(Identificacion.objects.filter(pk=otra.pk).exists())
        self.assertEqual(MRS.objects.filter(participante=otra).count(), 1)
        # Comprobante firmado, verificable con su RUT, sin datos de salud ni RUT en claro.
        comprobante = resp.context['comprobante']
        datos = constancia_retiro.verificar(comprobante, rut=RUT)
        self.assertEqual((datos['modalidad'], datos['folio_revocacion'], datos['profesional']),
                         ('presencial', 'RV-2026-0001', self.prof.pk))
        self.assertIsNone(constancia_retiro.verificar(comprobante, rut=RUT_OTRA))
        self.assertNotIn('9876543', str(datos))
        self.assertNotIn('pregunta', str(datos))
        salida = StringIO()
        call_command('verificar_constancia_retiro', comprobante, rut=RUT, stdout=salida)
        self.assertIn('VÁLIDO', salida.getvalue())
        self.assertIn('RV-2026-0001', salida.getvalue())

    def test_con_cuenta_no_se_retira_por_la_profesional(self):
        usuaria = Usuario.objects.create_user(rut=RUT, email='u@ficticio.cl', password=CLAVE_USUARIA)
        usuaria.consentimiento_aceptado_en = timezone.now()
        usuaria.save()
        self.assertTrue(sincronizar_como_cliente(usuaria, self.payload({'uuid_local': str(uuid4()),
                                                                        'datos': dict(IDENT)}))['ok'])
        resp = self.retiro()
        self.assertContains(resp, 'debe retirarse ella misma', status_code=400)
        self.assertEqual(Identificacion.objects.filter(usuario=usuaria).count(), 1)
        usuaria.refresh_from_db()
        self.assertIsNotNone(usuaria.consentimiento_aceptado_en)

    def test_rut_sin_datos(self):
        self.assertContains(self.retiro(), 'No hay datos', status_code=400)

    def test_envios_antiguos_no_restauran_datos(self):
        ficha = self.registrar_paciente_sin_cuenta()
        # Envíos preparados ANTES del retiro (cola sin conexión de la profesional).
        viejo_ficha = con_participacion(self.prof, self.payload({'paciente_id': ficha.pk, 'datos': {}},
                                                                {'pregunta_2': 3}))
        viejo_rut = con_participacion(self.prof, self.payload({'uuid_local': str(uuid4()), 'rut': RUT,
                                                              'datos': dict(IDENT)}, {'pregunta_2': 3}))
        self.assertTrue(viejo_rut['identificacion']['participacion_paciente'].startswith('p'))
        self.assertEqual(self.retiro().status_code, 200)

        with self.assertRaises(ErrorSincronizacion):
            sincronizar_payload(self.prof, viejo_ficha)
        with self.assertRaises(ConflictoRonda) as c:
            sincronizar_payload(self.prof, viejo_rut)
        self.assertEqual(c.exception.codigo, 'participacion_anterior')
        self.assertFalse(Identificacion.objects.filter(rut_hash=hash_rut(RUT)).exists())

        # Vuelve a consentir (documento nuevo): la cola antigua sigue sin poder escribir.
        time.sleep(0.002)
        consentimiento_presencial(RUT, self.prof)
        with self.assertRaises(ConflictoRonda) as c:
            sincronizar_payload(self.prof, viejo_rut)
        self.assertEqual(c.exception.codigo, 'participacion_anterior')
        self.assertFalse(Identificacion.objects.filter(rut_hash=hash_rut(RUT)).exists())
        # Un envío sin participación (cliente antiguo) tampoco escribe.
        sin_part = self.payload({'uuid_local': str(uuid4()), 'rut': RUT, 'datos': dict(IDENT)})
        with self.assertRaises(ConflictoRonda) as c:
            sincronizar_payload(self.prof, sin_part)
        self.assertEqual(c.exception.codigo, 'cliente_desactualizado')
        # La participación nueva sí registra, desde cero.
        res = sincronizar_como_cliente(self.prof, self.payload({'uuid_local': str(uuid4()), 'rut': RUT,
                                                                 'datos': dict(IDENT)}))
        self.assertTrue(res['ok'])
        self.assertEqual(MRS.objects.filter(participante_id=res['paciente_id']).count(), 1)

    def test_la_pagina_de_la_encuesta_lleva_la_participacion(self):
        ficha = self.registrar_paciente_sin_cuenta()
        resp = self.client.get(f'/profesional/paciente/{ficha.pk}/encuesta/')
        self.assertContains(resp, f'data-participacion-paciente="{participacion_paciente(ficha.rut_hash)}"')

    def test_retiro_propio_borra_tambien_la_ficha_registrada_antes_de_la_cuenta(self):
        ficha = self.registrar_paciente_sin_cuenta()            # la registró la profesional, sin dueña
        usuaria = Usuario.objects.create_user(rut=RUT, email='u@ficticio.cl', password=CLAVE_USUARIA)
        usuaria.consentimiento_aceptado_en = timezone.now()
        usuaria.save()
        self.client.force_login(usuaria)
        self.assertEqual(self.client.post('/retirarse/', {'entiendo': 'on'}).status_code, 200)
        self.assertFalse(Identificacion.objects.filter(pk=ficha.pk).exists())
        self.assertEqual(MRS.objects.filter(participante_id=ficha.pk).count(), 0)


# ---------------------------------------------------------------------------
# 2. Registros presenciales antiguos sin constancia verificable
# ---------------------------------------------------------------------------
class RegistroAntiguoSinConstanciaTest(Base):
    def setUp(self):
        super().setUp()
        # Registro presencial anterior a la Etapa 2: ficha con respuestas y sin constancia.
        self.ficha = self.registrar_paciente_sin_cuenta()
        ConsentimientoPresencial.objects.filter(rut_hash=hash_rut(RUT)).delete()
        self.mrs_antes = MRS.objects.filter(participante=self.ficha).count()

    def test_excluido_bloqueado_y_conservado(self):
        self.assertEqual(motivo_exclusion(self.ficha), 'presencial')
        self.assertEqual(self.client.get(f'/profesional/paciente/{self.ficha.pk}/encuesta/').status_code, 403)
        with self.assertRaises(ConflictoRonda) as c:
            sincronizar_como_cliente(self.prof, self.payload({'paciente_id': self.ficha.pk, 'datos': {}}))
        self.assertEqual(c.exception.codigo, 'consentimiento_paciente')
        ficha_html = self.client.get(f'/profesional/paciente/{self.ficha.pk}/')
        self.assertContains(ficha_html, 'data-registro-sin-consentimiento')
        self.assertNotContains(ficha_html, f'/profesional/paciente/{self.ficha.pk}/encuesta/')
        # No se inventa consentimiento ni se elimina nada.
        self.assertFalse(ConsentimientoPresencial.objects.exists())
        self.assertTrue(Identificacion.objects.filter(pk=self.ficha.pk).exists())
        self.assertEqual(MRS.objects.filter(participante=self.ficha).count(), self.mrs_antes)

    def test_informe_de_solo_lectura(self):
        salida = StringIO()
        call_command('registros_sin_consentimiento', stdout=salida)
        texto = salida.getvalue()
        self.assertIn(f'ficha N.º {self.ficha.pk}', texto)
        self.assertIn('Nada se modificó', texto)
        self.assertNotIn(RUT, texto)
        self.assertFalse(ConsentimientoPresencial.objects.exists())
        self.assertEqual(MRS.objects.filter(participante=self.ficha).count(), self.mrs_antes)

    def test_se_regulariza_solo_con_consentimiento_valido(self):
        resp = self.client.post(URL_CONSENT, {'rut': RUT, 'registrar': '1', 'folio_documento': 'CI-2026-0900',
                                              'custodia': 'Archivo ficticio', 'declaracion': 'on'})
        self.assertContains(resp, 'data-registrado')
        self.assertIsNone(motivo_exclusion(self.ficha))
        self.assertEqual(self.client.get(f'/profesional/paciente/{self.ficha.pk}/encuesta/').status_code, 200)

    def test_puede_pedir_su_retiro(self):
        self.assertEqual(self.retiro().status_code, 200)
        self.assertFalse(Identificacion.objects.filter(pk=self.ficha.pk).exists())


# ---------------------------------------------------------------------------
# 3. Límite de intentos de contraseña (consentimiento presencial con cuenta)
# ---------------------------------------------------------------------------
class LimiteIntentosTest(Base):
    def setUp(self):
        super().setUp()
        self.usuaria = Usuario.objects.create_user(rut=RUT, email='u@ficticio.cl', password=CLAVE_USUARIA)

    def consentir(self, clave, rut=RUT, folio=None):
        return self.client.post(URL_CONSENT, {'rut': rut, 'registrar': '1',
                                              'folio_documento': folio or f'CI-{uuid4().hex[:8]}',
                                              'custodia': 'Archivo ficticio', 'declaracion': 'on',
                                              'clave_participante': clave})

    def test_bloqueo_tras_cinco_fallos_incluso_con_la_clave_correcta(self):
        for i in range(4):
            resp = self.consentir('incorrecta')
            self.assertContains(resp, intentos.MENSAJE_CLAVE_INCORRECTA, status_code=400)
        self.assertContains(self.consentir('incorrecta'), intentos.MENSAJE_BLOQUEO, status_code=429)
        resp = self.consentir(CLAVE_USUARIA)                     # correcta, pero bloqueada
        self.assertContains(resp, intentos.MENSAJE_BLOQUEO, status_code=429)
        self.assertFalse(ConsentimientoPresencial.objects.exists())
        self.usuaria.refresh_from_db()
        self.assertIsNone(self.usuaria.consentimiento_aceptado_en)
        # Los mensajes no revelan datos: ni intentos restantes, ni correo, ni RUT.
        for texto in ('restante', 'u@ficticio.cl', '9.876.543', 'no corresponde'):
            self.assertNotIn(texto, resp.content.decode())
        # El bloqueo es de la cuenta: otra profesional tampoco puede seguir probando.
        otra = Usuario.objects.create_user(rut='13.131.313-6', email='p2@ficticio.cl', password=CLAVE_PROF,
                                           rol=Usuario.Rol.PROFESIONAL_SALUD)
        self.client.force_login(otra)
        self.assertContains(self.consentir(CLAVE_USUARIA), intentos.MENSAJE_BLOQUEO, status_code=429)

    @override_settings(INTENTOS_CLAVE_VENTANA=2)
    def test_el_bloqueo_vence_y_un_acierto_reinicia(self):
        # Fallos registrados directamente (comprobar una contraseña tarda más que la ventana de prueba).
        for _ in range(5):
            intentos.registrar_fallo(self.usuaria, self.prof)
        self.assertEqual(self.consentir(CLAVE_USUARIA).status_code, 429)
        time.sleep(2.2)
        self.assertContains(self.consentir(CLAVE_USUARIA), 'data-registrado')
        self.assertFalse(intentos.bloqueado(self.usuaria))

    def test_limite_por_profesional_en_varias_cuentas(self):
        otras = [Usuario.objects.create_user(rut=r, email=f'o{i}@ficticio.cl', password=CLAVE_USUARIA)
                 for i, r in enumerate(['11.111.111-1', '12.345.678-5', '15.555.555-6'])]
        ruts = ['11.111.111-1', '12.345.678-5', '15.555.555-6']
        n = 0
        for rut in ruts:
            for _ in range(4):
                if n < 10:
                    self.consentir('incorrecta', rut=rut)
                    n += 1
        # 10 fallos repartidos (ninguna cuenta llegó a 5): la profesional queda bloqueada.
        self.assertFalse(intentos.bloqueado(otras[0]))
        self.assertContains(self.consentir(CLAVE_USUARIA), intentos.MENSAJE_BLOQUEO, status_code=429)

    def test_contrasena_vacia_no_cuenta_como_intento(self):
        for _ in range(6):
            self.assertEqual(self.consentir('').status_code, 400)
        self.assertContains(self.consentir(CLAVE_USUARIA), 'data-registrado')

    def test_retiro_presencial_tambien_tiene_limite(self):
        self.usuaria.delete()
        self.registrar_paciente_sin_cuenta()
        for _ in range(5):
            self.retiro(clave_profesional='incorrecta')
        self.assertContains(self.retiro(), intentos.MENSAJE_BLOQUEO, status_code=429)
        self.assertTrue(Identificacion.objects.filter(rut_hash=hash_rut(RUT)).exists())
