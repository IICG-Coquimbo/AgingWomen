from django.contrib.auth import authenticate, get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .rut import hash_rut, normalizar_rut, validar_rut

Usuario = get_user_model()


class RutUtilsTest(TestCase):
    def test_normalizar_rut(self):
        self.assertEqual(normalizar_rut(' 12.345.678-9 '), '123456789')
        self.assertEqual(normalizar_rut('7.654.321-k'), '7654321K')

    def test_validar_rut(self):
        self.assertTrue(validar_rut('11.111.111-1'))
        self.assertFalse(validar_rut('11.111.111-2'))
        self.assertFalse(validar_rut('abc'))

    def test_hash_rut_es_deterministico_e_independiente_del_formato(self):
        self.assertEqual(hash_rut('12.345.678-9'), hash_rut('123456789'))
        self.assertNotEqual(hash_rut('11.111.111-1'), hash_rut('22.222.222-2'))
        self.assertEqual(len(hash_rut('11.111.111-1')), 64)


class RegistroTest(TestCase):
    def test_registro_crea_usuaria_y_envia_password(self):
        resp = self.client.post(
            reverse('registro'),
            {'rut': '11.111.111-1', 'email': 'nueva@example.com'},
        )
        self.assertRedirects(resp, reverse('registro_enviado'))

        usuario = Usuario.objects.get(email='nueva@example.com')
        self.assertEqual(usuario.rol, Usuario.Rol.USUARIA_COMUN)
        self.assertEqual(usuario.rut_hash, hash_rut('11111111-1'))
        self.assertTrue(usuario.has_usable_password())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('nueva@example.com', mail.outbox[0].to)

    def test_registro_rechaza_rut_invalido(self):
        resp = self.client.post(
            reverse('registro'),
            {'rut': '11.111.111-2', 'email': 'x@example.com'},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='x@example.com').exists())

    def test_registro_rechaza_rut_duplicado(self):
        Usuario.objects.create_user(rut='11.111.111-1', email='a@example.com')
        resp = self.client.post(
            reverse('registro'),
            {'rut': '11111111-1', 'email': 'b@example.com'},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Usuario.objects.filter(email='b@example.com').exists())


class LoginPorRutTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            rut='11.111.111-1', email='a@example.com', password='clave-de-prueba-123',
        )

    def test_authenticate_con_rut_correcto(self):
        user = authenticate(rut='11111111-1', password='clave-de-prueba-123')
        self.assertEqual(user, self.usuario)

    def test_authenticate_con_password_incorrecta(self):
        self.assertIsNone(authenticate(rut='11.111.111-1', password='mala'))

    def test_authenticate_con_rut_inexistente(self):
        self.assertIsNone(authenticate(rut='22.222.222-2', password='clave-de-prueba-123'))

    def test_login_view_por_rut(self):
        resp = self.client.post(
            reverse('login'),
            {'username': '11.111.111-1', 'password': 'clave-de-prueba-123'},
        )
        self.assertRedirects(resp, reverse('home'))


class AccesoRestringidoTest(TestCase):
    def test_home_redirige_a_login_si_anonimo(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp.url)


class AdminGestionCuentasTest(TestCase):
    def setUp(self):
        self.superusuario = Usuario.objects.create_superuser(
            rut_hash='11.111.111-1', email='admin@example.com', password='clave-admin-123',
        )
        self.client.login(username='11111111-1', password='clave-admin-123')

    def test_crear_profesional_por_admin_crea_cuenta_y_envia_correo(self):
        url = reverse('admin:usuarios_usuario_crear_profesional')
        resp = self.client.post(url, {'rut': '7.654.321-6', 'email': 'nuevo.profesional@example.com'})
        self.assertRedirects(resp, reverse('admin:usuarios_usuario_changelist'))

        usuario = Usuario.objects.get(email='nuevo.profesional@example.com')
        self.assertEqual(usuario.rol, Usuario.Rol.PROFESIONAL_SALUD)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('nuevo.profesional@example.com', mail.outbox[0].to)

    def test_no_superusuario_no_puede_crear_profesional(self):
        staff = Usuario.objects.create_user(
            rut='9.876.543-3', email='staff@example.com', password='clave-staff-123',
            rol=Usuario.Rol.PROFESIONAL_SALUD, is_staff=True,
        )
        self.client.logout()
        self.client.login(username='98765433', password='clave-staff-123')
        url = reverse('admin:usuarios_usuario_crear_profesional')
        resp = self.client.post(url, {'rut': '7.654.321-6', 'email': 'otro@example.com'})
        self.assertRedirects(resp, reverse('admin:index'))
        self.assertFalse(Usuario.objects.filter(email='otro@example.com').exists())

    def test_promover_y_revocar_por_accion_de_admin(self):
        usuaria = Usuario.objects.create_user(rut='7.654.321-6', email='u@example.com')
        url = reverse('admin:usuarios_usuario_changelist')

        self.client.post(url, {
            'action': 'promover_a_profesional', '_selected_action': [usuaria.pk],
        })
        usuaria.refresh_from_db()
        self.assertEqual(usuaria.rol, Usuario.Rol.PROFESIONAL_SALUD)

        self.client.post(url, {
            'action': 'revocar_a_usuaria_comun', '_selected_action': [usuaria.pk],
        })
        usuaria.refresh_from_db()
        self.assertEqual(usuaria.rol, Usuario.Rol.USUARIA_COMUN)


class ConsentimientoInformadoTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            rut='11.111.111-1', email='a@example.com', password='clave-de-prueba-123',
        )
        self.client.login(username='11111111-1', password='clave-de-prueba-123')

    def test_encuesta_redirige_a_consentimiento_si_no_se_ha_aceptado(self):
        resp = self.client.get(reverse('encuesta'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('consentimiento'), resp.url)

    def test_aceptar_consentimiento_marca_fecha_y_permite_seguir(self):
        resp = self.client.post(
            reverse('consentimiento') + '?next=' + reverse('encuesta'),
            {'leido': 'on', 'decision': 'acepto', 'next': reverse('encuesta')},
        )
        self.assertRedirects(resp, reverse('encuesta'))
        self.usuario.refresh_from_db()
        self.assertIsNotNone(self.usuario.consentimiento_aceptado_en)

    def _sin_consentimiento(self):
        self.usuario.refresh_from_db()
        return self.usuario.consentimiento_aceptado_en is None

    def test_sin_opcion_no_avanza(self):
        resp = self.client.post(reverse('consentimiento'), {'leido': 'on'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Selecciona una opción')
        self.assertTrue(self._sin_consentimiento())

    def test_aceptar_sin_marcar_leido_no_avanza(self):
        resp = self.client.post(reverse('consentimiento'), {'decision': 'acepto'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'leíste y comprendiste')
        self.assertTrue(self._sin_consentimiento())

    def test_no_acepto_o_desisto_muestra_rechazo_sin_guardar(self):
        for decision in ('no_acepto', 'desisto'):
            resp = self.client.post(reverse('consentimiento'), {'leido': 'on', 'decision': decision})
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed(resp, 'usuarios/consentimiento_rechazado.html')
            self.assertTrue(self._sin_consentimiento())
        # Sigue sin poder entrar a la encuesta.
        resp = self.client.get(reverse('encuesta'))
        self.assertIn(reverse('consentimiento'), resp.url)

    def test_texto_aprobado_sin_advertencia_provisional(self):
        resp = self.client.get(reverse('consentimiento'))
        self.assertContains(resp, 'CEC UCN')
        self.assertNotContains(resp, 'provisional')

    def test_consentimiento_ya_aceptado_redirige_directo(self):
        from django.utils import timezone
        self.usuario.consentimiento_aceptado_en = timezone.now()
        self.usuario.save(update_fields=['consentimiento_aceptado_en'])
        resp = self.client.get(reverse('consentimiento'))
        self.assertRedirects(resp, reverse('home'))
