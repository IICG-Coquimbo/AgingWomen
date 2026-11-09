"""
Fase 40 — privacidad: clave local, participación (retiro y reingreso), consentimiento de la
paciente para la profesional y búsquedas por RUT sin el RUT en la URL. Datos ficticios.
docker compose exec web python manage.py test apps.usuarios.test_privacidad
"""
import json
import re
from uuid import uuid4

from django.test import Client, TestCase
from django.utils import timezone

from apps.encuestas.models import MRS, EvaluacionTrabajo, Identificacion
from apps.encuestas.sync import ConflictoRonda, sincronizar_payload
from apps.rondas.models import RondaEvaluacion
from apps.rondas.pruebas_comunes import con_participacion, consentimiento_presencial

from .models import Usuario
from .privacidad import clave_local, cuenta_local, participacion_de
from .rut import hash_rut

RUT_U = '11.111.111-1'
RUT_PACIENTE = '9.876.543-3'
IDENT = {
    'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
    'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
    'comuna': 'Santiago', 'region_residencia': '13',
}
MRS_COMPLETO = {f'pregunta_{i}': 1 for i in range(1, 12)}


def payload(secciones=(), ident=None, ronda=1, finalizar=False):
    p = {'protocolo': 2, 'ronda': ronda, 'identificacion': ident or {'uuid_local': str(uuid4()), 'datos': dict(IDENT)},
         'secciones': list(secciones)}
    if finalizar:
        p['finalizar'] = True
        p['id_cierre'] = str(uuid4())
    return p


def mrs(datos):
    return {'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': len(datos) < 11, 'datos': dict(datos)}


class Base(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut=RUT_U, email='u@e.cl')
        self.prof = Usuario.objects.create_user(rut='22.222.222-2', email='p@e.cl', rol=Usuario.Rol.PROFESIONAL_SALUD)

    def aceptar(self, usuario=None):
        u = usuario or self.usuaria
        u.consentimiento_aceptado_en = timezone.now()
        u.save(update_fields=['consentimiento_aceptado_en'])

    def post_api(self, usuario, cuerpo):
        self.client.force_login(usuario)
        return self.client.post('/api/sincronizar/', data=json.dumps(cuerpo), content_type='application/json')

    def retirarse(self):
        self.client.force_login(self.usuaria)
        return self.client.post('/retirarse/', {'entiendo': 'on'})


class ClaveLocalTest(Base):
    URL = '/api/clave-local/'

    def test_sin_sesion_401_en_json_sin_redireccion(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['codigo'], 'sin_sesion')

    def test_usuaria_sin_consentimiento_403(self):
        self.client.force_login(self.usuaria)
        self.assertEqual(self.client.get(self.URL).status_code, 403)

    def test_entrega_clave_sin_cache_ni_datos_personales(self):
        self.aceptar()
        self.client.force_login(self.usuaria)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('no-store', resp['Cache-Control'])
        cuerpo = resp.json()
        self.assertEqual(cuerpo['cuenta'], cuenta_local(self.usuaria))
        self.assertEqual(cuerpo['participacion'], participacion_de(self.usuaria))
        self.assertTrue(cuerpo['expira'])
        texto = json.dumps(cuerpo)
        for dato in (RUT_U, self.usuaria.rut_hash, f'"{self.usuaria.pk}"'):
            self.assertNotIn(dato, texto)

    def test_clave_distinta_por_cuenta_y_por_participacion(self):
        otra = Usuario.objects.create_user(rut='33.333.333-3', email='o@e.cl')
        self.aceptar()
        self.aceptar(otra)
        self.assertNotEqual(clave_local(self.usuaria), clave_local(otra))
        self.assertNotEqual(cuenta_local(self.usuaria), cuenta_local(otra))
        antes = clave_local(self.usuaria)
        self.retirarse()
        self.usuaria.refresh_from_db()
        self.assertIsNone(clave_local(self.usuaria))
        self.aceptar()
        self.assertNotEqual(clave_local(self.usuaria), antes)   # lo cifrado con la anterior queda ilegible
        self.assertEqual(cuenta_local(self.usuaria), cuenta_local(self.usuaria))

    def test_pagina_con_sesion_lleva_la_cuenta_y_sin_sesion_no(self):
        self.aceptar()
        self.client.force_login(self.usuaria)
        html = self.client.get('/mi-tablero/').content.decode()
        self.assertIn(f'data-cuenta="{cuenta_local(self.usuaria)}"', html)
        self.assertIn('/static/js/sesion.js', html)
        self.assertIn('data-salir', html)
        self.client.logout()
        login = self.client.get('/cuenta/ingresar/').content.decode()
        self.assertNotIn('data-cuenta=', login)
        self.assertIn('/static/js/sesion.js', login)   # limpia claves de sesiones terminadas


class ParticipacionTest(Base):
    def test_envio_sin_participacion_o_con_una_anterior_se_rechaza_sin_escribir(self):
        self.aceptar()
        resp = self.post_api(self.usuaria, payload([mrs({'pregunta_1': 2})]))
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['codigo'], 'cliente_desactualizado')
        cuerpo = payload([mrs({'pregunta_1': 2})])
        cuerpo['participacion'] = '123'
        resp = self.post_api(self.usuaria, cuerpo)
        self.assertEqual(resp.json()['codigo'], 'participacion_anterior')
        self.assertFalse(Identificacion.objects.exists())

    def test_retiro_y_reingreso_parte_de_cero_y_rechaza_envios_antiguos(self):
        self.aceptar()
        anterior = participacion_de(self.usuaria)
        resp = self.post_api(self.usuaria, con_participacion(self.usuaria, payload([mrs(MRS_COMPLETO)], finalizar=True)))
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(Identificacion.objects.get().ronda_actual, 2)

        self.retirarse()   # elimina respuestas, rondas y resultados
        self.assertFalse(Identificacion.objects.exists())
        self.assertFalse(MRS.objects.exists())
        self.assertFalse(RondaEvaluacion.objects.exists())

        # Dispositivo 2 desactualizado: antes del nuevo consentimiento, 403; después, 409.
        viejo = payload([mrs({'pregunta_1': 4})])
        viejo['participacion'] = anterior
        self.assertEqual(self.post_api(self.usuaria, viejo).status_code, 403)
        self.client.force_login(self.usuaria)
        self.client.post('/cuenta/consentimiento/', {'decision': 'acepto', 'leido': 'on'})   # consentimiento nuevo
        self.usuaria.refresh_from_db()
        self.assertIsNotNone(self.usuaria.consentimiento_aceptado_en)
        self.assertNotEqual(participacion_de(self.usuaria), anterior)
        resp = self.post_api(self.usuaria, viejo)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['codigo'], 'participacion_anterior')
        self.assertFalse(Identificacion.objects.exists(), 'el envío antiguo no recrea la ficha')

        # Participación nueva: ficha nueva desde la ronda 1, sin nada de lo anterior.
        resp = self.post_api(self.usuaria, con_participacion(self.usuaria, payload([mrs({'pregunta_2': 3})])))
        self.assertEqual(resp.status_code, 200, resp.content)
        ficha = Identificacion.objects.get()
        self.assertEqual(ficha.ronda_actual, 1)
        self.assertEqual(MRS.objects.count(), 1)
        self.assertIsNone(MRS.objects.get().pregunta_1)


class ProfesionalYConsentimientoTest(Base):
    def _ficha_de_la_usuaria(self):
        self.aceptar()
        sincronizar_payload(self.usuaria, con_participacion(self.usuaria, payload([mrs({'pregunta_1': 1})])))
        return Identificacion.objects.get(usuario=self.usuaria)

    def test_con_consentimiento_vigente_la_profesional_registra(self):
        ficha = self._ficha_de_la_usuaria()
        res = sincronizar_payload(self.prof, con_participacion(self.prof, payload(
            [{'tipo': 'trabajo', 'uuid_local': str(uuid4()), 'parcial': False,
              'datos': {'rendimiento_afectado': 3, 'bienestar_trabajo_afectado': 2, 'frecuencia_ausencias': 1,
                        'lugar_trabajo_comprensivo': 4}}], ident={'paciente_id': ficha.pk, 'datos': {}})))
        self.assertTrue(res['ok'], res)
        self.client.force_login(self.prof)
        self.assertEqual(self.client.get(f'/profesional/paciente/{ficha.pk}/encuesta/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/ronda-actual/?paciente={ficha.pk}').status_code, 200)

    def test_sin_consentimiento_no_crea_ni_modifica(self):
        ficha = self._ficha_de_la_usuaria()
        self.usuaria.consentimiento_aceptado_en = None   # p. ej., cuenta sin consentimiento vigente
        self.usuaria.save(update_fields=['consentimiento_aceptado_en'])
        with self.assertRaises(ConflictoRonda) as ctx:
            sincronizar_payload(self.prof, payload([mrs({'pregunta_3': 2})], ident={'paciente_id': ficha.pk, 'datos': {}}))
        self.assertEqual(ctx.exception.codigo, 'consentimiento_paciente')
        self.assertIsNone(MRS.objects.get().pregunta_3)
        self.client.force_login(self.prof)
        self.assertEqual(self.client.get(f'/profesional/paciente/{ficha.pk}/encuesta/').status_code, 403)
        self.assertEqual(self.client.get(f'/api/ronda-actual/?paciente={ficha.pk}').status_code, 403)
        resp = self.post_api(self.prof, payload([mrs({'pregunta_3': 2})], ident={'paciente_id': ficha.pk, 'datos': {}}))
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['codigo'], 'consentimiento_paciente')

    def test_retirada_no_reaparece_por_registro_presencial(self):
        """P7: tras el retiro, una ficha nueva con su RUT se rechaza (no queda una ficha sin dueña)."""
        Usuario.objects.filter(pk=self.usuaria.pk).update(rut_hash=hash_rut(RUT_PACIENTE))
        self.usuaria.refresh_from_db()
        self._ficha_de_la_usuaria()
        self.retirarse()
        with self.assertRaises(ConflictoRonda):
            sincronizar_payload(self.prof, payload(ident={'uuid_local': str(uuid4()), 'rut': RUT_PACIENTE,
                                                          'datos': dict(IDENT)}))
        self.assertFalse(Identificacion.objects.exists())
        self.client.force_login(self.prof)
        resp = self.client.post('/profesional/paciente/nueva/', {'rut': RUT_PACIENTE})
        self.assertEqual(resp.status_code, 403)
        self.assertContains(resp, 'no tiene un consentimiento vigente', status_code=403)

    def test_registro_presencial_sin_cuenta_exige_consentimiento_presencial(self):
        # Etapa 2: sin consentimiento presencial registrado, no se crea nada.
        with self.assertRaises(ConflictoRonda) as ctx:
            sincronizar_payload(self.prof, payload([mrs({'pregunta_1': 2})], ident={
                'uuid_local': str(uuid4()), 'rut': RUT_PACIENTE, 'datos': dict(IDENT)}))
        self.assertEqual(ctx.exception.codigo, 'consentimiento_paciente')
        self.assertFalse(Identificacion.objects.exists())
        consentimiento_presencial(RUT_PACIENTE, self.prof)
        res = sincronizar_payload(self.prof, con_participacion(self.prof, payload([mrs({'pregunta_1': 2})], ident={
            'uuid_local': str(uuid4()), 'rut': RUT_PACIENTE, 'datos': dict(IDENT)})))
        self.assertTrue(res['ok'], res)
        self.assertTrue(Identificacion.objects.filter(rut_hash=hash_rut(RUT_PACIENTE)).exists())
        trabajo = {'tipo': 'trabajo', 'uuid_local': str(uuid4()), 'parcial': False, 'datos': {}}
        self.assertTrue(sincronizar_payload(self.prof, con_participacion(self.prof, payload([trabajo], ident={
            'paciente_id': Identificacion.objects.get().pk, 'datos': {}})))['ok'])
        self.assertEqual(EvaluacionTrabajo.objects.count(), 1)


class BusquedaSinRutEnUrlTest(Base):
    def setUp(self):
        super().setUp()
        consentimiento_presencial(RUT_PACIENTE, self.prof)   # Fase 40, Etapa 2
        sincronizar_payload(self.prof, con_participacion(self.prof, payload(ident={
            'uuid_local': str(uuid4()), 'rut': RUT_PACIENTE, 'datos': dict(IDENT)})))
        self.ficha = Identificacion.objects.get()
        self.admin = Usuario.objects.create_superuser(rut_hash='7.654.321-6', email='a@e.cl', password='x-clave-larga-9')

    def _sin_rut_en_urls(self, html):
        urls = re.findall(r'(?:href|action)="([^"]*)"', html)
        for u in urls:
            self.assertNotIn('rut', u.lower(), u)
            self.assertNotIn('9876543', u.replace('.', ''), u)

    def test_buscar_paciente_por_post_con_csrf(self):
        self.client.force_login(self.prof)
        resp = self.client.post('/profesional/buscar/', {'rut': RUT_PACIENTE})
        self.assertEqual(resp.context['resultado'], self.ficha)
        html = resp.content.decode()
        self.assertIn('method="post"', html)
        self.assertIn(f'/profesional/paciente/{self.ficha.pk}/', html)
        self._sin_rut_en_urls(html)
        # Por GET el RUT se ignora: no se procesa ni se devuelve.
        resp = self.client.get('/profesional/buscar/', {'rut': RUT_PACIENTE})
        self.assertIsNone(resp.context['resultado'])
        self.assertNotIn(RUT_PACIENTE, resp.content.decode())
        # Sin token CSRF, el POST se rechaza.
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.prof)
        self.assertEqual(cliente.post('/profesional/buscar/', {'rut': RUT_PACIENTE}).status_code, 403)
        # La usuaria común no accede a la búsqueda ni a la ficha de destino.
        self.aceptar()
        self.client.force_login(self.usuaria)
        self.assertEqual(self.client.post('/profesional/buscar/', {'rut': RUT_PACIENTE}).status_code, 403)
        self.assertEqual(self.client.get(f'/profesional/paciente/{self.ficha.pk}/').status_code, 403)

    def test_panel_de_administracion_por_post(self):
        self.client.force_login(self.admin)
        resp = self.client.post('/administracion/', {'rut': '22.222.222-2'})
        self.assertRedirects(resp, f'/administracion/cuenta/{self.prof.pk}/', fetch_redirect_response=False)
        self.assertNotIn('rut', resp['Location'])
        resp = self.client.get('/administracion/', {'rut': '22.222.222-2'})
        self.assertEqual(resp.status_code, 200)   # por GET el RUT se ignora
        self.assertNotIn('22.222.222-2', resp.content.decode())
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.admin)
        self.assertEqual(cliente.post('/administracion/', {'rut': '22.222.222-2'}).status_code, 403)
