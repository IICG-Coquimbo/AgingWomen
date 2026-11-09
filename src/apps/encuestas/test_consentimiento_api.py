"""
Fase 40S-1 (H-11): la API de escritura exige el consentimiento vigente.

Cubre: 403 en JSON sin consentimiento (nunca aceptado o retirado), que nada se
guarde en ese caso, los casos autorizados (usuaria con consentimiento y
personal de salud) y que el resto de la API siga igual.
"""
import json
from unittest import mock
from uuid import uuid4

from django.test import Client, TestCase, override_settings
from django.utils import timezone

from apps.usuarios.models import Usuario

from apps.rondas.pruebas_comunes import con_participacion

from .models import MRS, EvaluacionTrabajo, Identificacion, TareasCuidado

URL = '/api/sincronizar/'
IDENT = {
    'fecha_nacimiento': '1975-05-20', 'genero': 'F', 'nivel_educacion': 'M_COM',
    'origen_procedencia': 'CL', 'pueblo_originario_afro': 'NINGUNO',
    'comuna': 'Santiago', 'region_residencia': '13',
}


def _payload(**extra):
    datos = {
        'identificacion': {'uuid_local': str(uuid4()), 'datos': dict(IDENT)},
        'secciones': [{'tipo': 'mrs', 'uuid_local': str(uuid4()), 'parcial': True,
                       'datos': {'pregunta_1': 2}}],
    }
    datos.update(extra)
    return datos


class ConsentimientoApiTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.client.force_login(self.usuaria)

    def _post(self, obj):
        return self.client.post(URL, data=json.dumps(con_participacion(self.usuaria, obj)),
                                content_type='application/json')

    def _aceptar(self):
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save(update_fields=['consentimiento_aceptado_en'])

    def test_sin_consentimiento_responde_403_en_json_y_no_guarda(self):
        resp = self._post(_payload(finalizar=True))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp['Content-Type'], 'application/json')
        cuerpo = resp.json()
        self.assertFalse(cuerpo['ok'])
        self.assertEqual(cuerpo['codigo'], 'consentimiento_requerido')
        self.assertFalse(Identificacion.objects.exists())
        self.assertFalse(MRS.objects.exists())

    def test_403_aun_con_json_invalido(self):
        # El consentimiento se revisa antes de leer el cuerpo.
        resp = self.client.post(URL, data='no-json', content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_tras_retirarse_vuelve_a_responder_403(self):
        self._aceptar()
        self.assertEqual(self._post(_payload()).status_code, 200)
        self.client.post('/retirarse/', {'entiendo': 'on'})
        self.assertFalse(Identificacion.objects.exists())
        resp = self._post(_payload())
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Identificacion.objects.exists())
        self.assertFalse(MRS.objects.exists())

    def test_con_consentimiento_guarda_igual_que_antes(self):
        self._aceptar()
        resp = self._post({
            'identificacion': {'uuid_local': str(uuid4()), 'datos': dict(IDENT)},
            'secciones': [{'tipo': 'tareas_cuidado', 'uuid_local': str(uuid4()), 'parcial': True,
                           'datos': {'cuida_otras_personas': 'SI'}}],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['ok'])
        self.assertEqual(TareasCuidado.objects.count(), 1)

    def test_aceptar_despues_habilita_la_escritura(self):
        self.assertEqual(self._post(_payload()).status_code, 403)
        self._aceptar()
        self.assertEqual(self._post(_payload()).status_code, 200)

    def test_sin_sesion_sigue_redirigiendo_al_login(self):
        self.client.logout()
        resp = self._post(_payload())
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/cuenta/', resp.url)

    def test_get_sigue_siendo_405(self):
        self.assertEqual(self.client.get(URL).status_code, 405)

    def test_lecturas_no_cambian(self):
        # Las lecturas propias no escriben y siguen disponibles (alcance de H-11: escritura).
        self.assertEqual(self.client.get('/api/esquema/').status_code, 200)
        self.assertEqual(self.client.get('/api/estado/').status_code, 200)
        self.assertEqual(self.client.get('/api/ronda-actual/').status_code, 200)

    def test_csrf_sigue_activo(self):
        self._aceptar()
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuaria)
        resp = cliente.post(URL, data=json.dumps(_payload()), content_type='application/json')
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Identificacion.objects.exists())


class ProfesionalSinConsentimientoTest(TestCase):
    """El personal de salud no participa del estudio: como en /encuesta/, no se le exige."""

    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save(update_fields=['consentimiento_aceptado_en'])
        self.client.force_login(self.usuaria)
        self.client.post(URL, data=json.dumps(con_participacion(self.usuaria, _payload())),
                         content_type='application/json')
        self.paciente = Identificacion.objects.get()
        self.prof = Usuario.objects.create_user(
            rut='22.222.222-2', email='p@e.cl', rol=Usuario.Rol.PROFESIONAL_SALUD)
        self.assertIsNone(self.prof.consentimiento_aceptado_en)
        self.client.force_login(self.prof)

    def test_profesional_guarda_por_una_paciente(self):
        resp = self.client.post(URL, data=json.dumps(con_participacion(self.prof, {
            'identificacion': {'paciente_id': self.paciente.pk, 'datos': {}},
            'secciones': [{'tipo': 'trabajo', 'uuid_local': str(uuid4()), 'parcial': False,
                           'datos': {'rendimiento_afectado': 3, 'bienestar_trabajo_afectado': 2,
                                     'frecuencia_ausencias': 1, 'lugar_trabajo_comprensivo': 4}}],
        })), content_type='application/json')
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(EvaluacionTrabajo.objects.count(), 1)

    def test_profesional_con_payload_erroneo_sigue_en_400(self):
        resp = self.client.post(URL, data=json.dumps({'identificacion': {'datos': dict(IDENT)}}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class ErroresSinDatosSensiblesTest(TestCase):
    """Con DEBUG desactivado, un error interno no devuelve el contenido de la petición."""

    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut='11.111.111-1', email='u@e.cl')
        self.usuaria.consentimiento_aceptado_en = timezone.now()
        self.usuaria.save(update_fields=['consentimiento_aceptado_en'])

    @override_settings(DEBUG=False)
    def test_error_500_generico(self):
        cliente = Client(raise_request_exception=False)
        cliente.force_login(self.usuaria)
        marcador = 'MARCADOR-SALUD-40S1'
        payload = _payload()
        payload['secciones'][0]['datos']['observacion'] = marcador
        with mock.patch('apps.encuestas.api.sincronizar_payload', side_effect=RuntimeError('fallo simulado')), \
                self.assertLogs('django.request', level='ERROR') as registro:
            resp = cliente.post(URL, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 500)
        texto = resp.content.decode('utf-8', 'replace')
        self.assertNotIn(marcador, texto)
        self.assertNotIn('Traceback', texto)
        self.assertNotIn('fallo simulado', texto)
        # El registro nombra la ruta, no el cuerpo de la petición.
        self.assertFalse(any(marcador in r.getMessage() for r in registro.records))
