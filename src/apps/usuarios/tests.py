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
