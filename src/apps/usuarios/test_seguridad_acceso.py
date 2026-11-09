"""
Seguridad del acceso: límite de intentos, activación por enlace y caché del navegador.
docker compose exec web python manage.py test apps.usuarios.test_seguridad_acceso
No envía correos reales (Django usa un buzón en memoria durante las pruebas).
"""
import re
import time
from io import StringIO

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import Usuario

RUT, OTRO_RUT, RUT_NUEVO = '12.345.678-5', '7.654.321-6', '9.876.543-3'
CLAVE = 'Clave-Sintetica-48291'
NUEVA = 'Otra-Clave-Sintetica-77310'


@override_settings(LIMITES_ACTIVOS=True, LIMITE_INGRESO_RUT=3, LIMITE_INGRESO_IP=6)
class LimiteIngresoTest(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.usuaria = Usuario.objects.create_user(rut=RUT, email='u@ficticio.cl', password=CLAVE)

    def ingresar(self, rut=RUT, clave='incorrecta'):
        return self.client.post(reverse('login'), {'username': rut, 'password': clave})

    def fallar(self, veces, rut=RUT):
        for _ in range(veces):
            self.ingresar(rut)

    def conectada(self):
        return '_auth_user_id' in self.client.session

    def test_01_al_llegar_al_limite_ni_la_clave_correcta_entra(self):
        self.fallar(3)
        resp = self.ingresar(clave=CLAVE)
        self.assertContains(resp, 'Demasiados intentos')
        self.assertFalse(self.conectada())

    def test_02_antes_del_limite_se_puede_entrar_y_el_acierto_reinicia(self):
        self.fallar(2)
        self.ingresar(clave=CLAVE)
        self.assertTrue(self.conectada())
        self.client.logout()
        self.fallar(2)
        self.ingresar(clave=CLAVE)
        self.assertTrue(self.conectada())

    def test_03_un_rut_inexistente_se_comporta_igual(self):
        self.fallar(3, OTRO_RUT)
        self.assertContains(self.ingresar(OTRO_RUT), 'Demasiados intentos')

    def test_04_el_bloqueo_de_un_rut_no_afecta_a_otra_cuenta(self):
        Usuario.objects.create_user(rut=OTRO_RUT, email='o@ficticio.cl', password=CLAVE)
        self.fallar(3)
        self.ingresar(OTRO_RUT, CLAVE)
        self.assertTrue(self.conectada())

    def test_05_limite_por_direccion_ip(self):
        for rut in ('1.111.111-4', '2.222.222-8', '3.333.333-1', '4.444.444-5', '5.555.555-9', '6.666.666-2'):
            self.ingresar(rut)
        self.ingresar(clave=CLAVE)
        self.assertFalse(self.conectada())

    @override_settings(LIMITE_VENTANA=1)
    def test_06_el_bloqueo_termina_solo(self):
        self.fallar(3)
        self.assertContains(self.ingresar(clave=CLAVE), 'Demasiados intentos')
        time.sleep(1.2)
        self.ingresar(clave=CLAVE)
        self.assertTrue(self.conectada())

    def test_07_recuperar_la_contrasena_desbloquea(self):
        self.fallar(3)
        self.client.post(reverse('password_reset'), {'email': 'u@ficticio.cl'})
        enlace = re.search(r'/cuenta/clave/recuperar/\S+', mail.outbox[0].body).group(0)
        resp = self.client.get(enlace, follow=True)
        destino = resp.redirect_chain[-1][0]
        self.client.post(destino, {'new_password1': NUEVA, 'new_password2': NUEVA})
        self.ingresar(clave=NUEVA)
        self.assertTrue(self.conectada())

    def test_08_el_mensaje_de_bloqueo_no_revela_si_la_cuenta_existe(self):
        self.fallar(3)
        self.fallar(3, OTRO_RUT)
        a, b = self.ingresar(), self.ingresar(OTRO_RUT)
        extraer = lambda r: re.search(r'acceso-error.*?</div>', r.content.decode(), re.S).group(0)
        self.assertEqual(extraer(a), extraer(b))

    def test_09_las_solicitudes_de_recuperacion_tienen_limite_y_no_cambian_la_respuesta(self):
        for _ in range(5):
            resp = self.client.post(reverse('password_reset'), {'email': 'u@ficticio.cl'})
            self.assertRedirects(resp, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 3)

    @override_settings(LIMITE_REGISTRO_IP=2)
    def test_10_el_registro_tiene_limite_por_conexion(self):
        for i, rut in enumerate(('1.111.111-4', '2.222.222-8', '3.333.333-1')):
            self.client.logout()
            resp = self.client.post(reverse('registro'), {
                'rut': rut, 'email': f'r{i}@ficticio.cl', 'email2': f'r{i}@ficticio.cl',
                'password1': CLAVE, 'password2': CLAVE})
        self.assertContains(resp, 'Demasiados intentos de registro')
        self.assertLessEqual(len(mail.outbox), 2)


class ActivacionProfesionalTest(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.admin = Usuario.objects.create_superuser(
            rut_hash='11.111.111-1', email='admin@ficticio.cl', password=CLAVE)
        self.client.force_login(self.admin)

    def crear(self):
        self.client.post(reverse('admin_crear_profesional'), {'rut': RUT_NUEVO, 'email': 'p@ficticio.cl'})
        self.client.logout()
        cuenta = Usuario.objects.get(email='p@ficticio.cl')
        return cuenta, re.search(r'https?://\S+', mail.outbox[0].body).group(0)

    def activar(self, enlace, clave=NUEVA):
        resp = self.client.get(enlace, follow=True)
        return resp, self.client.post(resp.redirect_chain[-1][0], {'new_password1': clave, 'new_password2': clave})

    def test_01_el_correo_trae_un_enlace_y_ninguna_contrasena(self):
        cuenta, enlace = self.crear()
        cuerpo = mail.outbox[0].body
        self.assertEqual(cuenta.rol, Usuario.Rol.PROFESIONAL_SALUD)
        self.assertIn('/cuenta/clave/recuperar/', enlace)
        self.assertNotIn('contraseña temporal', cuerpo.lower())
        self.assertFalse(hasattr(cuenta, 'password_generada'))

    def test_02_el_enlace_permite_definir_la_contrasena_e_ingresar(self):
        _cuenta, enlace = self.crear()
        self.activar(enlace)
        self.client.post(reverse('login'), {'username': RUT_NUEVO, 'password': NUEVA})
        self.assertIn('_auth_user_id', self.client.session)

    def test_03_el_enlace_es_de_un_solo_uso(self):
        _cuenta, enlace = self.crear()
        self.activar(enlace)
        self.client.logout()
        self.assertContains(self.client.get(enlace, follow=True), 'Enlace no válido')

    def test_04_el_enlace_vence(self):
        _cuenta, enlace = self.crear()
        with override_settings(PASSWORD_RESET_TIMEOUT=-1):
            self.assertContains(self.client.get(enlace, follow=True), 'Enlace no válido')

    def test_05_un_enlace_vencido_se_reemplaza_con_la_recuperacion_normal(self):
        cuenta, _enlace = self.crear()
        mail.outbox.clear()
        self.client.post(reverse('password_reset'), {'email': 'p@ficticio.cl'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(cuenta.has_usable_password())

    def test_06_un_token_alterado_no_sirve(self):
        cuenta, _enlace = self.crear()
        uid = urlsafe_base64_encode(force_bytes(cuenta.pk))
        token = default_token_generator.make_token(cuenta)[:-1] + 'x'
        url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        self.assertContains(self.client.get(url, follow=True), 'Enlace no válido')

    def test_07_el_comando_no_muestra_ninguna_contrasena(self):
        salida = StringIO()
        call_command('crear_profesional', RUT_NUEVO, 'c@ficticio.cl', stdout=salida)
        self.assertNotIn('Contraseña generada', salida.getvalue())
        self.assertIn('Olvidé mi contraseña', salida.getvalue())


class SinCacheTest(TestCase):
    def setUp(self):
        self.usuaria = Usuario.objects.create_user(rut=RUT, email='u@ficticio.cl', password=CLAVE)

    def test_01_las_paginas_con_sesion_no_se_guardan(self):
        self.client.force_login(self.usuaria)
        for ruta in ('/', '/mi-tablero/', '/encuesta/', '/api/ronda-actual/', '/api/estado/'):
            resp = self.client.get(ruta, follow=False)
            self.assertIn('no-store', resp['Cache-Control'], ruta)

    def test_02_las_vistas_profesionales_no_se_guardan(self):
        prof = Usuario.objects.create_user(rut=OTRO_RUT, email='p@ficticio.cl', password=CLAVE,
                                           rol=Usuario.Rol.PROFESIONAL_SALUD)
        self.client.force_login(prof)
        for ruta in ('/profesional/buscar/', '/profesional/estadisticas/'):
            self.assertIn('no-store', self.client.get(ruta)['Cache-Control'], ruta)

    def test_03_tras_salir_las_paginas_redirigen_al_ingreso(self):
        self.client.force_login(self.usuaria)
        self.client.post(reverse('logout'))
        resp = self.client.get('/mi-tablero/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/cuenta/ingresar/', resp['Location'])

    def test_04_el_service_worker_no_se_marca(self):
        self.client.force_login(self.usuaria)
        self.assertNotIn('no-store', self.client.get('/sw.js').get('Cache-Control', ''))
