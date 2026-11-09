"""
Límite de intentos en el acceso público: ingreso, recuperación de contraseña y registro.

Regla (ventana fija desde el primer fallo, igual que intentos.py):
- por RUT: `LIMITE_INGRESO_RUT` fallos (5) bloquean ese RUT, exista o no la cuenta, para
  no revelar quién está registrada;
- por dirección IP: `LIMITE_INGRESO_IP` fallos (30), para frenar los intentos contra muchos RUT;
- mientras dura el bloqueo la contraseña NO se comprueba. Termina solo al cabo de
  `LIMITE_VENTANA` segundos (900): ninguna cuenta queda bloqueada de forma permanente.
  Quien recupera su contraseña por correo desbloquea su RUT de inmediato.

Los contadores viven en la caché de Django con claves derivadas (HMAC), sin RUT ni IP en
claro y sin tocar la base de datos. Con varios procesos debe configurarse una caché
compartida; con la caché local cada proceso cuenta por separado (ver intentos.py).
Detrás de un proxy, `LIMITE_IP_CABECERA` indica la cabecera con la IP real; sin ella,
todas las solicitudes parecerían venir de la misma dirección.
"""
from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import salted_hmac

from .rut import hash_rut

SAL = 'agingwomen.limite-ingreso'
MENSAJE_BLOQUEO = ('Demasiados intentos. Por seguridad, espera unos minutos antes de volver a '
                   'intentarlo o recupera tu contraseña.')
MENSAJE_REGISTRO = 'Demasiados intentos de registro desde esta conexión. Espera unos minutos.'


def _activos():
    return getattr(settings, 'LIMITES_ACTIVOS', True)


def _ventana():
    return int(getattr(settings, 'LIMITE_VENTANA', 900))


def _clave(tipo, valor):
    return 'aw:limite:' + salted_hmac(SAL, f'{tipo}|{valor}', algorithm='sha256').hexdigest()[:40]


def ip_de(request):
    cabecera = getattr(settings, 'LIMITE_IP_CABECERA', '')
    if cabecera and request.headers.get(cabecera):
        # El último valor es el que agregó el proxy propio; los anteriores los controla el cliente.
        return request.headers[cabecera].split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR', '')


def _alcanzado(clave, limite):
    return (cache.get(clave) or 0) >= limite


def _contar(clave):
    cache.add(clave, 0, _ventana())
    try:
        cache.incr(clave)
    except ValueError:   # venció entre add e incr
        cache.set(clave, 1, _ventana())


def _claves_ingreso(request, rut):
    pares = [(_clave('ip', ip_de(request)), int(getattr(settings, 'LIMITE_INGRESO_IP', 30)))]
    if rut:
        pares.append((_clave('rut', hash_rut(rut)), int(getattr(settings, 'LIMITE_INGRESO_RUT', 5))))
    return pares


def ingreso_bloqueado(request, rut):
    return _activos() and any(_alcanzado(k, n) for k, n in _claves_ingreso(request, rut))


def registrar_fallo_ingreso(request, rut):
    if _activos():
        for clave, _limite in _claves_ingreso(request, rut):
            _contar(clave)


def reiniciar_rut(rut):
    cache.delete(_clave('rut', hash_rut(rut)))


def reiniciar_cuenta(usuario):
    """Tras recuperar la contraseña por correo: la persona ya demostró que la cuenta es suya."""
    cache.delete(_clave('rut', usuario.rut_hash))


def _permitir(pares):
    """Cuenta una solicitud; False si alguno de sus contadores ya llegó al límite."""
    if not _activos():
        return True
    if any(_alcanzado(k, n) for k, n in pares):
        return False
    for clave, _limite in pares:
        _contar(clave)
    return True


def permitir_recuperacion(request, correo):
    return _permitir([(_clave('recuperar-ip', ip_de(request)), int(getattr(settings, 'LIMITE_RECUPERAR_IP', 10))),
                      (_clave('recuperar-correo', (correo or '').lower()),
                       int(getattr(settings, 'LIMITE_RECUPERAR_CORREO', 3)))])


def permitir_registro(request):
    return _permitir([(_clave('registro-ip', ip_de(request)), int(getattr(settings, 'LIMITE_REGISTRO_IP', 10)))])
