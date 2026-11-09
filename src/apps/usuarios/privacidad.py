"""
Fase 40 — privacidad (P1, P3, P6, P7). Sin migraciones ni datos nuevos guardados.

- Participación: se identifica por el momento en que se aceptó el consentimiento
  (`Usuario.consentimiento_aceptado_en`). El retiro lo borra y un consentimiento
  nuevo crea otro valor, así que un envío preparado en una participación anterior
  (pestaña antigua, dispositivo desactualizado, cola offline) se distingue sin
  conservar nada de lo eliminado.
- Clave local: cada cuenta recibe del servidor, solo con sesión iniciada, una clave
  AES-256 derivada de SECRET_KEY, de la cuenta y de su participación. El navegador
  cifra con ella todo lo que guarda en IndexedDB y la borra al cerrar sesión. Al
  cambiar la participación cambia la clave: lo cifrado con la anterior queda ilegible.
- Consentimiento de una paciente atendida por una profesional: sin consentimiento
  vigente no se registran respuestas. Etapa 2: sin cuenta, hace falta el consentimiento
  presencial registrado (`sin_consentimiento_vigente`).
"""
import base64

from django.utils.crypto import salted_hmac

from .models import Usuario

SAL_CLAVE = 'agingwomen.fase40.clave-local'
SAL_CUENTA = 'agingwomen.fase40.cuenta-local'
PARTICIPACION_PROFESIONAL = 'profesional'


def participacion_de(usuario):
    """Identificador de la participación vigente; None si una usuaria no tiene consentimiento."""
    if usuario.es_profesional:
        return PARTICIPACION_PROFESIONAL
    aceptado = usuario.consentimiento_aceptado_en
    return str(int(aceptado.timestamp() * 1_000_000)) if aceptado else None


def cuenta_local(usuario):
    """Nombre del espacio de la cuenta en IndexedDB (no revela el RUT ni el id)."""
    return salted_hmac(SAL_CUENTA, str(usuario.pk), algorithm='sha256').hexdigest()[:32]


def clave_local(usuario):
    """Clave AES-256 en base64 para cifrar el almacenamiento local de esta cuenta y participación."""
    participacion = participacion_de(usuario)
    if participacion is None:
        return None
    digest = salted_hmac(SAL_CLAVE, f'{usuario.pk}|{participacion}', algorithm='sha256').digest()
    return base64.b64encode(digest).decode('ascii')


def cuenta_sin_consentimiento(rut_hash=None, usuario_id=None):
    """
    La cuenta de usuaria común asociada (por RUT o por la ficha) si existe y NO tiene
    consentimiento vigente. None si no hay cuenta o si tiene consentimiento.
    """
    filtro = {}
    if usuario_id:
        filtro['pk'] = usuario_id
    elif rut_hash:
        filtro['rut_hash'] = rut_hash
    else:
        return None
    cuenta = Usuario.objects.filter(**filtro).first()
    if cuenta is None or cuenta.es_profesional or cuenta.consentimiento_aceptado_en:
        return None
    return cuenta


def ficha_sin_consentimiento(ficha):
    """True si la ficha no tiene consentimiento vigente (ver `sin_consentimiento_vigente`)."""
    return sin_consentimiento_vigente(ficha.rut_hash, usuario_id=ficha.usuario_id)


def sin_consentimiento_vigente(rut_hash, usuario_id=None):
    """
    Fase 40, Etapa 2: única regla de consentimiento para registrar datos de una persona.
    - Con cuenta de usuaria (por la ficha o por el RUT): vale su consentimiento vigente,
      dado en línea o presencialmente con su contraseña (ambos fijan `consentimiento_aceptado_en`).
    - Sin cuenta: hace falta un consentimiento presencial registrado con su constancia.
    True si NO hay consentimiento vigente.
    """
    return participacion_paciente(rut_hash, usuario_id) is None


def participacion_paciente(rut_hash, usuario_id=None):
    """
    Identificador de la participación vigente de una persona atendida por una profesional;
    None si no tiene consentimiento vigente (misma regla que `sin_consentimiento_vigente`).
    - Con cuenta: el de su cuenta (`participacion_de`).
    - Sin cuenta: el momento en que se registró su consentimiento presencial.
    Cambia con cada retiro y consentimiento nuevo, así que un envío preparado para una
    participación anterior (cola sin conexión de la profesional, pestaña antigua) se
    reconoce sin conservar nada de lo eliminado.
    """
    from .models import ConsentimientoPresencial
    cuenta = None
    if usuario_id:
        cuenta = Usuario.objects.filter(pk=usuario_id).first()
    if cuenta is None and rut_hash:
        cuenta = Usuario.objects.filter(rut_hash=rut_hash).first()
    if cuenta is not None and not cuenta.es_profesional:
        return participacion_de(cuenta)
    if not rut_hash:
        return None
    registro = ConsentimientoPresencial.objects.filter(rut_hash=rut_hash).only('registrado_en').first()
    return f'p{int(registro.registrado_en.timestamp() * 1_000_000)}' if registro else None


def version_consentimiento():
    """Versión del documento de consentimiento: huella SHA-256 (12) del texto que se muestra."""
    import hashlib
    from pathlib import Path

    from django.conf import settings
    texto = (Path(settings.BASE_DIR) / 'templates' / 'usuarios' / 'consentimiento.html').read_bytes()
    return 'sha256:' + hashlib.sha256(texto).hexdigest()[:12]


MENSAJE_SIN_CONSENTIMIENTO_PACIENTE = (
    'Esta persona no tiene un consentimiento vigente (nunca lo aceptó o se retiró del estudio). '
    'No se pueden registrar respuestas hasta que lo acepte en línea o se registre su consentimiento '
    'presencial con la constancia correspondiente.'
)


def contexto(request):
    """Context processor: nombre del espacio local de la cuenta con sesión (base.html, encuesta.html)."""
    usuario = getattr(request, 'user', None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    return {'cuenta_local': cuenta_local(usuario)}
