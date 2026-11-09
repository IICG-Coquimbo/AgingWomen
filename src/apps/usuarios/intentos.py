"""
Fase 40 (pendientes de consentimiento): límite de intentos de contraseña en los
formularios presenciales, aplicado en el servidor.

Se usa en dos lugares:
- consentimiento presencial de una mujer con cuenta (ella escribe su contraseña);
- retiro presencial (la profesional confirma con su propia contraseña).

Regla (ventana fija desde el primer fallo):
- por cuenta verificada: `INTENTOS_CLAVE_MAX` fallos (5 por defecto) bloquean la
  verificación de esa cuenta para TODAS las profesionales;
- por profesional: `INTENTOS_CLAVE_MAX_PROFESIONAL` fallos (10 por defecto) en
  cualquier cuenta la bloquean a ella, para que no pueda probar contra muchas cuentas;
- el bloqueo dura `INTENTOS_CLAVE_VENTANA` segundos (900 por defecto).
Mientras hay bloqueo la contraseña NO se comprueba: no se puede seguir probando ni
saber si la siguiente era correcta. Un acierto reinicia el contador de esa cuenta.

Los contadores viven en la caché de Django con claves derivadas (HMAC), sin RUT ni
identificadores en claro. Con un solo proceso (runserver) basta la caché local; en un
despliegue con varios procesos debe configurarse una caché compartida (decisión del
despliegue, Fase 18), o cada proceso contará por separado.
"""
from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import salted_hmac

SAL = 'agingwomen.fase40.intentos-clave'

MENSAJE_CLAVE_INCORRECTA = 'No se pudo verificar la contraseña. Pide que la escriban otra vez con cuidado.'
MENSAJE_BLOQUEO = ('Se alcanzó el máximo de intentos de verificación con contraseña. Por seguridad, '
                   'espera unos minutos antes de intentarlo de nuevo.')


def _ventana():
    return int(getattr(settings, 'INTENTOS_CLAVE_VENTANA', 900))


def _clave(tipo, ident):
    return 'aw:intentos:' + salted_hmac(SAL, f'{tipo}|{ident}', algorithm='sha256').hexdigest()[:40]


def _contadores(cuenta=None, profesional=None):
    """[(clave de caché, límite)] que aplican a esta verificación."""
    pares = []
    if cuenta is not None:
        pares.append((_clave('cuenta', cuenta.pk), int(getattr(settings, 'INTENTOS_CLAVE_MAX', 5))))
    if profesional is not None:
        pares.append((_clave('profesional', profesional.pk),
                      int(getattr(settings, 'INTENTOS_CLAVE_MAX_PROFESIONAL', 10))))
    return pares


def bloqueado(cuenta=None, profesional=None):
    return any((cache.get(k) or 0) >= limite for k, limite in _contadores(cuenta, profesional))


def registrar_fallo(cuenta=None, profesional=None):
    for k, _limite in _contadores(cuenta, profesional):
        cache.add(k, 0, _ventana())
        try:
            cache.incr(k)
        except ValueError:   # venció entre add e incr
            cache.set(k, 1, _ventana())


def reiniciar(cuenta):
    cache.delete(_clave('cuenta', cuenta.pk))


def verificar_clave(usuario, clave, profesional):
    """
    Comprueba la contraseña de `usuario` con el límite de intentos.
    Devuelve None si es correcta; si no, el mensaje (genérico) que se debe mostrar.
    """
    if bloqueado(usuario, profesional):
        return MENSAJE_BLOQUEO
    if usuario.check_password(clave or ''):
        reiniciar(usuario)
        return None
    registrar_fallo(usuario, profesional)
    return MENSAJE_BLOQUEO if bloqueado(usuario, profesional) else MENSAJE_CLAVE_INCORRECTA
