import re
from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import RegistroOTP
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
    """Registro con verificación de correo por código (Fase 21)."""

    CLAVE = 'Violeta-Coquimbo-2026'

    def _datos(self, **extra):
        datos = {
            'rut': '11.111.111-1', 'email': 'nueva@example.com',
            'password1': self.CLAVE, 'password2': self.CLAVE,
        }
        datos.update(extra)
        return datos

    def _paso1(self, **extra):
        return self.client.post(reverse('registro'), self._datos(**extra))

    def _codigo_enviado(self, indice=-1):
        return re.search(r'\b(\d{6})\b', mail.outbox[indice].body).group(1)

    def _verificar(self, codigo):
        return self.client.post(reverse('registro_verificar'), {'codigo': codigo})

    def test_registro_completo_crea_cuenta_con_la_clave_elegida_e_inicia_sesion(self):
        resp = self._paso1()
        self.assertRedirects(resp, reverse('registro_verificar'))
        # Todavía no hay cuenta: primero hay que verificar el correo.
        self.assertFalse(Usuario.objects.exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('nueva@example.com', mail.outbox[0].to)

        resp = self._verificar(self._codigo_enviado())
        self.assertRedirects(resp, reverse('encuesta'), fetch_redirect_response=False)

        usuario = Usuario.objects.get(email='nueva@example.com')
        self.assertEqual(usuario.rol, Usuario.Rol.USUARIA_COMUN)
        self.assertEqual(usuario.rut_hash, hash_rut('11111111-1'))
        self.assertTrue(usuario.check_password(self.CLAVE))
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)
        self.assertFalse(RegistroOTP.objects.exists())
        # Correo de bienvenida, sin la contraseña.
        self.assertEqual(len(mail.outbox), 2)
        self.assertNotIn(self.CLAVE, mail.outbox[1].body)

    def test_ni_el_codigo_ni_la_clave_se_guardan_en_claro(self):
        self._paso1()
        otp = RegistroOTP.objects.get()
        codigo = self._codigo_enviado()
        self.assertNotIn(codigo, otp.codigo_hash)
        self.assertNotEqual(otp.password_hash, self.CLAVE)
        self.assertTrue(check_password(self.CLAVE, otp.password_hash))

    def test_registro_rechaza_rut_invalido(self):
        resp = self._paso1(rut='11.111.111-2')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(RegistroOTP.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_registro_rechaza_rut_duplicado(self):
        Usuario.objects.create_user(rut='11.111.111-1', email='a@example.com')
        resp = self._paso1(rut='11111111-1', email='b@example.com')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(RegistroOTP.objects.exists())

    def test_registro_rechaza_claves_distintas(self):
        resp = self._paso1(password2='Otra-Clave-Distinta-9')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'no coinciden')
        self.assertFalse(RegistroOTP.objects.exists())

    def test_registro_rechaza_clave_debil(self):
        for debil in ('12345678', 'abc'):
            resp = self._paso1(password1=debil, password2=debil)
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.context['form'].errors.get('password1'), debil)
        self.assertFalse(RegistroOTP.objects.exists())

    def test_codigo_incorrecto_no_crea_cuenta_y_cuenta_intentos(self):
        self._paso1()
        codigo = self._codigo_enviado()
        malo = '000000' if codigo != '000000' else '111111'
        resp = self._verificar(malo)
        self.assertContains(resp, 'no es correcto')
        self.assertEqual(RegistroOTP.objects.get().intentos, 1)
        self.assertFalse(Usuario.objects.exists())

    def test_tras_5_intentos_fallidos_el_codigo_se_invalida(self):
        self._paso1()
        codigo = self._codigo_enviado()
        malo = '000000' if codigo != '000000' else '111111'
        for _ in range(RegistroOTP.MAX_INTENTOS):
            self._verificar(malo)
        resp = self._verificar(codigo)
        self.assertContains(resp, 'Solicita un código nuevo')
        self.assertFalse(Usuario.objects.exists())

    def test_codigo_vencido_no_sirve(self):
        self._paso1()
        codigo = self._codigo_enviado()
        RegistroOTP.objects.update(
            enviado_en=timezone.now() - RegistroOTP.VIGENCIA - timedelta(seconds=1))
        resp = self._verificar(codigo)
        self.assertContains(resp, 'venció')
        self.assertFalse(Usuario.objects.exists())

    def test_reenviar_respeta_la_espera_y_el_codigo_nuevo_reemplaza_al_anterior(self):
        self._paso1()
        viejo = self._codigo_enviado()
        # Antes de un minuto no se reenvía.
        self.client.post(reverse('registro_reenviar'))
        self.assertEqual(len(mail.outbox), 1)

        RegistroOTP.objects.update(enviado_en=timezone.now() - timedelta(minutes=2))
        self.client.post(reverse('registro_reenviar'))
        self.assertEqual(len(mail.outbox), 2)
        nuevo = self._codigo_enviado()
        if nuevo != viejo:
            self.assertContains(self._verificar(viejo), 'no es correcto')
        self.assertRedirects(self._verificar(nuevo), reverse('encuesta'),
                             fetch_redirect_response=False)

    def test_verificar_sin_registro_pendiente_vuelve_al_paso_1(self):
        resp = self.client.get(reverse('registro_verificar'))
        self.assertRedirects(resp, reverse('registro'))


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


class LoginYMenuTest(TestCase):
    """Fase 28: mensaje de login sin enumeración de RUT y menú de inicio por rol."""

    def setUp(self):
        self.usuaria = Usuario.objects.create_user(
            rut='11.111.111-1', email='a@example.com', password='clave-de-prueba-123',
        )

    def _login_fallido(self, rut):
        return self.client.post(reverse('login'), {'username': rut, 'password': 'clave-mala-999'})

    def test_login_fallido_muestra_enlace_a_registro(self):
        resp = self._login_fallido('11.111.111-1')
        self.assertContains(resp, 'RUT o contraseña incorrectos.')
        self.assertContains(resp, reverse('registro'))

    def test_mismo_mensaje_exista_o_no_el_rut(self):
        existente = self._login_fallido('11.111.111-1')
        inexistente = self._login_fallido('22.222.222-2')
        self.assertEqual(
            existente.context['form'].non_field_errors(),
            inexistente.context['form'].non_field_errors(),
        )
        # Se revisa solo el mensaje de error (el script de base.html contiene
        # "Service Worker no registrado", que no tiene que ver con el RUT).
        for resp in (existente, inexistente):
            texto = ' '.join(resp.context['form'].non_field_errors()).lower()
            self.assertNotIn('registrad', texto)
            self.assertNotIn('no existe', texto)

    def test_menu_usuaria_comun(self):
        self.client.login(username='11111111-1', password='clave-de-prueba-123')
        resp = self.client.get(reverse('home'))
        self.assertContains(resp, 'Bienvenida')
        self.assertNotContains(resp, 'Usuaria común')
        for nombre in ('encuesta', 'mi_tablero', 'mi_evaluacion', 'password_change', 'retirarse'):
            self.assertContains(resp, f'href="{reverse(nombre)}"')
        self.assertNotContains(resp, reverse('buscar_paciente'))
        self.assertNotContains(resp, reverse('admin:index'))

    def test_menu_profesional(self):
        Usuario.objects.create_user(
            rut='9.876.543-3', email='p@example.com', password='clave-prof-123',
            rol=Usuario.Rol.PROFESIONAL_SALUD,
        )
        self.client.login(username='98765433', password='clave-prof-123')
        resp = self.client.get(reverse('home'))
        for nombre in ('buscar_paciente', 'estadisticas', 'encuesta', 'password_change'):
            self.assertContains(resp, f'href="{reverse(nombre)}"')
        self.assertNotContains(resp, reverse('mi_tablero'))
        self.assertNotContains(resp, reverse('retirarse'))


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


class AdministracionSistemaTest(TestCase):
    """Fase 30: administración de cuentas dentro del sistema (solo superusuario)."""

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            rut_hash='11.111.111-1', email='admin@example.com', password='clave-admin-123',
        )
        self.usuaria = Usuario.objects.create_user(
            rut='7.654.321-6', email='u@example.com', password='clave-usuaria-123',
        )
        self.client.login(username='11111111-1', password='clave-admin-123')

    def test_solo_superusuario_entra(self):
        self.client.logout()
        self.client.login(username='76543216', password='clave-usuaria-123')
        self.assertEqual(self.client.get(reverse('admin_panel')).status_code, 403)
        resp = self.client.post(reverse('admin_cambiar_rol', args=[self.usuaria.pk]), {'rol': 'PROFESIONAL'})
        self.assertEqual(resp.status_code, 403)

    def test_buscar_por_rut_lleva_a_la_cuenta(self):
        resp = self.client.get(reverse('admin_panel'), {'rut': '7.654.321-6'})
        self.assertRedirects(resp, reverse('admin_cuenta', args=[self.usuaria.pk]))

    def test_buscar_rut_inexistente(self):
        resp = self.client.get(reverse('admin_panel'), {'rut': '22.222.222-2'})
        self.assertContains(resp, 'No hay ninguna cuenta con ese RUT.')

    def test_promover_y_revocar(self):
        url = reverse('admin_cambiar_rol', args=[self.usuaria.pk])
        self.client.post(url, {'rol': 'PROFESIONAL'})
        self.usuaria.refresh_from_db()
        self.assertEqual(self.usuaria.rol, Usuario.Rol.PROFESIONAL_SALUD)
        self.client.post(url, {'rol': 'USUARIA'})
        self.usuaria.refresh_from_db()
        self.assertEqual(self.usuaria.rol, Usuario.Rol.USUARIA_COMUN)

    def test_eliminar_borra_cuenta_y_respuestas(self):
        from apps.encuestas.models import Identificacion
        Identificacion.objects.create(
            usuario=self.usuaria, rut_hash=self.usuaria.rut_hash,
            fecha_nacimiento='1975-05-20',
            genero=Identificacion.GeneroOptions.FEMENINO,
            nivel_educacion=Identificacion.NivelEducativo.MEDIA_COM,
            comuna='Santiago',
        )
        url = reverse('admin_eliminar', args=[self.usuaria.pk])
        # Sin marcar la casilla no se elimina.
        self.client.post(url, {})
        self.assertTrue(Usuario.objects.filter(pk=self.usuaria.pk).exists())

        resp = self.client.post(url, {'entiendo': 'on'})
        self.assertRedirects(resp, reverse('admin_panel'))
        self.assertFalse(Usuario.objects.filter(pk=self.usuaria.pk).exists())
        self.assertFalse(Identificacion.objects.exists())

    def test_no_se_modifica_la_propia_cuenta_ni_otro_superusuario(self):
        otro = Usuario.objects.create_superuser(
            rut_hash='9.876.543-3', email='otro@example.com', password='clave-otro-123',
        )
        for cuenta in (self.admin, otro):
            # El superusuario se crea con rol profesional: intentar revocarlo no debe tener efecto.
            self.client.post(reverse('admin_cambiar_rol', args=[cuenta.pk]), {'rol': 'USUARIA'})
            self.client.post(reverse('admin_eliminar', args=[cuenta.pk]), {'entiendo': 'on'})
            cuenta.refresh_from_db()  # falla si se hubiera eliminado
            self.assertEqual(cuenta.rol, Usuario.Rol.PROFESIONAL_SALUD)

    def test_crear_profesional(self):
        resp = self.client.post(
            reverse('admin_crear_profesional'),
            {'rut': '12.345.678-5', 'email': 'nuevo@example.com'},
        )
        nueva = Usuario.objects.get(email='nuevo@example.com')
        self.assertRedirects(resp, reverse('admin_cuenta', args=[nueva.pk]))
        self.assertEqual(nueva.rol, Usuario.Rol.PROFESIONAL_SALUD)
        self.assertEqual(len(mail.outbox), 1)

    def test_menu_superusuario_apunta_a_administracion_propia(self):
        resp = self.client.get(reverse('home'))
        self.assertContains(resp, f'href="{reverse("admin_panel")}"')
        self.assertNotContains(resp, f'href="{reverse("admin:index")}"')


class NavegacionVolverTest(TestCase):
    """Toda página interna tiene un "Volver"; el menú de inicio no lo necesita."""

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            rut_hash='11.111.111-1', email='admin@example.com', password='clave-admin-123',
        )
        self.client.login(username='11111111-1', password='clave-admin-123')

    def test_inicio_sin_volver(self):
        self.assertNotContains(self.client.get(reverse('home')), 'class="volver"')

    def test_pagina_de_primer_nivel_vuelve_al_menu(self):
        resp = self.client.get(reverse('admin_panel'))
        self.assertContains(resp, '← Volver al menú')

    def test_pagina_de_segundo_nivel_vuelve_a_la_anterior(self):
        resp = self.client.get(reverse('admin_cuenta', args=[self.admin.pk]))
        self.assertContains(resp, '← Volver a administración')
        self.assertNotContains(resp, '← Volver al menú')
