"""
Fase 40S-1: configuración por entorno.

Cada caso carga settings.py en un proceso aparte con un entorno controlado.
Los valores usados aquí son de PRUEBA, generados al momento; nunca los reales.
"""
import json
import logging
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from .rut import hash_rut

BASE = Path(settings.BASE_DIR)
SETTINGS = BASE / 'Encuesta_integral' / 'settings.py'

LEER = r'''
import json, os, sys
sys.path.insert(0, os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'Encuesta_integral.settings'
from django.conf import settings
claves = ['DEBUG', 'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'SESSION_COOKIE_HTTPONLY',
          'CSRF_COOKIE_HTTPONLY', 'SECURE_SSL_REDIRECT', 'SECURE_HSTS_SECONDS', 'SECURE_PROXY_SSL_HEADER',
          'SECURE_CONTENT_TYPE_NOSNIFF', 'X_FRAME_OPTIONS', 'ALLOWED_HOSTS', 'CSRF_TRUSTED_ORIGINS',
          'EMAIL_BACKEND']
print(json.dumps({c: getattr(settings, c, None) for c in claves}))
'''


def _secretos_prueba():
    return {
        'SECRET_KEY': secrets.token_urlsafe(50),
        'RUT_HASH_PEPPER': secrets.token_urlsafe(32),
        'DB_PASSWORD': secrets.token_urlsafe(16),
    }


def _cargar(entorno):
    """Carga settings.py con SOLO las variables dadas (más PATH). Devuelve (código, salida, error)."""
    base = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'HOME') if k in os.environ}
    base.update(entorno)
    r = subprocess.run([sys.executable, '-c', LEER], cwd=BASE, env=base, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


class SinSecretosEnElCodigoTest(SimpleTestCase):
    def test_settings_no_tiene_valores_por_defecto_para_secretos(self):
        texto = SETTINGS.read_text(encoding='utf-8')
        # Ninguna clave escrita (la palabra sí aparece en la validación que rechaza claves de desarrollo).
        self.assertIsNone(re.search(r'django-insecure-\S', texto))
        self.assertIsNone(re.search(r"^SECRET_KEY = ['\"]", texto, re.M))
        self.assertNotIn("os.environ.get('DB_PASSWORD',", texto)
        self.assertNotIn("os.environ.get('RUT_HASH_PEPPER',", texto)
        self.assertIn("SECRET_KEY = _obligatoria('SECRET_KEY')", texto)
        self.assertIn("RUT_HASH_PEPPER = _obligatoria('RUT_HASH_PEPPER')", texto)
        self.assertIn("'PASSWORD': _obligatoria('DB_PASSWORD')", texto)
        self.assertIn("DEBUG = _bool_entorno('DEBUG', False)", texto)


class VariablesObligatoriasTest(SimpleTestCase):
    def test_falta_cada_secreto_no_arranca(self):
        for falta in ('SECRET_KEY', 'RUT_HASH_PEPPER', 'DB_PASSWORD'):
            for debug in ('1', '0'):
                with self.subTest(falta=falta, debug=debug):
                    entorno = dict(_secretos_prueba(), DEBUG=debug,
                                   EMAIL_HOST_USER='x@ejemplo.cl', EMAIL_HOST_PASSWORD='prueba')
                    del entorno[falta]
                    codigo, _, error = _cargar(entorno)
                    self.assertNotEqual(codigo, 0)
                    self.assertIn('ImproperlyConfigured', error)
                    self.assertIn(f'Falta la variable de entorno {falta}', error)

    def test_secreto_vacio_no_arranca(self):
        entorno = dict(_secretos_prueba(), DEBUG='1', SECRET_KEY='   ')
        codigo, _, error = _cargar(entorno)
        self.assertNotEqual(codigo, 0)
        self.assertIn('Falta la variable de entorno SECRET_KEY', error)

    def test_debug_invalido_no_arranca(self):
        codigo, _, error = _cargar(dict(_secretos_prueba(), DEBUG='quizas'))
        self.assertNotEqual(codigo, 0)
        self.assertIn('DEBUG debe ser 1 o 0', error)


class PerfilDesarrolloTest(SimpleTestCase):
    def test_debug_1_arranca_sin_cookies_seguras_y_con_correo_de_consola(self):
        codigo, salida, error = _cargar(dict(_secretos_prueba(), DEBUG='1'))
        self.assertEqual(codigo, 0, error)
        conf = json.loads(salida)
        self.assertTrue(conf['DEBUG'])
        self.assertFalse(conf['SESSION_COOKIE_SECURE'])
        self.assertFalse(conf['CSRF_COOKIE_SECURE'])
        self.assertEqual(conf['EMAIL_BACKEND'], 'django.core.mail.backends.console.EmailBackend')
        self.assertEqual(conf['ALLOWED_HOSTS'], ['localhost', '127.0.0.1'])


class PerfilProduccionTest(SimpleTestCase):
    def _completo(self, **cambios):
        entorno = dict(_secretos_prueba(), ALLOWED_HOSTS='ejemplo.cl',
                       CSRF_TRUSTED_ORIGINS='https://ejemplo.cl',
                       EMAIL_HOST_USER='x@ejemplo.cl', EMAIL_HOST_PASSWORD='prueba')
        entorno.update(cambios)
        return {k: v for k, v in entorno.items() if v is not None}

    def test_debug_desactivado_por_defecto(self):
        codigo, salida, error = _cargar(self._completo())
        self.assertEqual(codigo, 0, error)
        self.assertFalse(json.loads(salida)['DEBUG'])

    def test_produccion_completa_arranca_con_cookies_seguras(self):
        codigo, salida, error = _cargar(self._completo(DEBUG='0'))
        self.assertEqual(codigo, 0, error)
        conf = json.loads(salida)
        self.assertTrue(conf['SESSION_COOKIE_SECURE'])
        self.assertTrue(conf['CSRF_COOKIE_SECURE'])
        self.assertTrue(conf['SESSION_COOKIE_HTTPONLY'])
        self.assertFalse(conf['CSRF_COOKIE_HTTPONLY'])  # encuesta.js lee el token
        self.assertTrue(conf['SECURE_CONTENT_TYPE_NOSNIFF'])
        self.assertEqual(conf['X_FRAME_OPTIONS'], 'DENY')
        self.assertEqual(conf['CSRF_TRUSTED_ORIGINS'], ['https://ejemplo.cl'])
        self.assertEqual(conf['EMAIL_BACKEND'], 'django.core.mail.backends.smtp.EmailBackend')
        # HSTS, redirección y proxy: apagados hasta confirmar el despliegue.
        self.assertEqual(conf['SECURE_HSTS_SECONDS'], 0)
        self.assertFalse(conf['SECURE_SSL_REDIRECT'])
        self.assertIsNone(conf['SECURE_PROXY_SSL_HEADER'])

    def test_https_proxy_y_hsts_solo_si_se_piden(self):
        codigo, salida, error = _cargar(self._completo(
            SECURE_SSL_REDIRECT='1', DETRAS_DE_PROXY_HTTPS='1', SECURE_HSTS_SECONDS='3600'))
        self.assertEqual(codigo, 0, error)
        conf = json.loads(salida)
        self.assertTrue(conf['SECURE_SSL_REDIRECT'])
        self.assertEqual(conf['SECURE_PROXY_SSL_HEADER'], ['HTTP_X_FORWARDED_PROTO', 'https'])
        self.assertEqual(conf['SECURE_HSTS_SECONDS'], 3600)

    def test_rechaza_configuraciones_inseguras(self):
        casos = {
            'clave de desarrollo': dict(SECRET_KEY='django-insecure-' + secrets.token_urlsafe(50)),
            'clave corta': dict(SECRET_KEY=secrets.token_urlsafe(20)),
            'pepper corto': dict(RUT_HASH_PEPPER=secrets.token_urlsafe(8)),
            'hosts comodín': dict(ALLOWED_HOSTS='*'),
            'sin correo real': dict(EMAIL_HOST_USER=None, EMAIL_HOST_PASSWORD=None),
        }
        for nombre, cambios in casos.items():
            with self.subTest(nombre):
                entorno = self._completo(**cambios)
                codigo, _, error = _cargar(entorno)
                self.assertNotEqual(codigo, 0)
                self.assertIn('Configuración de producción', error)
                # El mensaje nunca incluye los valores.
                for clave in ('SECRET_KEY', 'RUT_HASH_PEPPER', 'DB_PASSWORD'):
                    self.assertNotIn(entorno[clave], error)


class ValoresActivosTest(SimpleTestCase):
    """En el entorno en que corren las pruebas, los valores se leen tal cual (sin comillas ni espacios añadidos)."""

    def test_se_leen_sin_transformar(self):
        self.assertEqual(settings.SECRET_KEY, os.environ['SECRET_KEY'])
        self.assertEqual(settings.RUT_HASH_PEPPER, os.environ['RUT_HASH_PEPPER'])
        self.assertEqual(settings.DATABASES['default']['PASSWORD'], os.environ['DB_PASSWORD'])
        for valor in (settings.SECRET_KEY, settings.RUT_HASH_PEPPER):
            self.assertNotIn(valor[:1], ('"', "'", ' '))
            self.assertNotIn(valor[-1:], ('"', "'", ' '))

    def test_postgresql(self):
        self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.postgresql')

    def test_hash_rut_depende_solo_del_pepper(self):
        with self.settings(RUT_HASH_PEPPER='pepper-de-prueba-a'):
            a = hash_rut('11.111.111-1')
        with self.settings(RUT_HASH_PEPPER='pepper-de-prueba-b'):
            b = hash_rut('11.111.111-1')
        self.assertNotEqual(a, b)  # por eso el pepper NO puede cambiar sin migración (40S-2)
        self.assertEqual(hash_rut('11.111.111-1'), hash_rut('11111111-1'))


class RegistrosTest(SimpleTestCase):
    def test_consola_de_django_solo_con_debug(self):
        # Configuración por defecto de Django: el manejador de consola filtra con RequireDebugTrue,
        # así que sin DEBUG los errores no se imprimen con su traza; no hay ADMINS a quien enviarlos.
        consola = [h for h in logging.getLogger('django').handlers if h.get_name() == 'console']
        self.assertTrue(consola)
        self.assertTrue(any(type(f).__name__ == 'RequireDebugTrue' for f in consola[0].filters))
        self.assertEqual(settings.ADMINS, [])
        self.assertFalse(hasattr(settings, 'LOGGING') and settings.LOGGING)
