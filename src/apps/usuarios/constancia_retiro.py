"""
Fase 40, Etapa 2: constancia mínima del retiro, SIN guardarla en el servidor.

No hay plazo de conservación ni base legal definidos para guardar constancias con
identificadores (decisión pendiente; ver el informe de la Etapa 2). Por eso no se crea
tabla ni migración: al retirarse, la participante recibe un comprobante firmado por el
servidor que ella conserva. Contiene solo:
- un código aleatorio, la fecha y hora del retiro y la versión del consentimiento;
- una huella con clave del RUT pseudonimizado (no revela el RUT; permite confirmar que
  el comprobante corresponde a la persona que lo presenta, si ella entrega su RUT).
Ningún dato de salud. La verificación usa `django.core.signing` (SECRET_KEY): al rotar
la clave (Etapa 4) hay que dejar la anterior en SECRET_KEY_FALLBACKS para seguir
verificando comprobantes emitidos antes.
"""
import secrets

from django.core import signing
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from .privacidad import version_consentimiento
from .rut import hash_rut

SAL = 'agingwomen.fase40.constancia-retiro'


def _huella(rut_hash):
    return salted_hmac(SAL + '.huella', rut_hash, algorithm='sha256').hexdigest()[:20]


def emitir(rut_hash, momento=None, presencial=None):
    """
    `presencial` (retiro registrado por una profesional): {'folio': folio del documento de
    revocación firmado, 'custodia': dónde se guarda, 'profesional': id de la cuenta que lo registró}. Quedan dentro del
    comprobante firmado, así el papel y el comprobante se pueden cotejar.
    """
    momento = momento or timezone.now()
    datos = {'tipo': 'retiro', 'codigo': secrets.token_hex(6).upper(),
             'fecha': timezone.localtime(momento).isoformat(timespec='seconds'),
             'version': version_consentimiento(), 'huella': _huella(rut_hash)}
    if presencial:
        datos.update({'modalidad': 'presencial', 'folio_revocacion': presencial['folio'],
                      'custodia': presencial['custodia'], 'profesional': presencial['profesional']})
    return datos, signing.dumps(datos, salt=SAL, compress=True)


def verificar(comprobante, rut=None):
    """Datos del comprobante si la firma es válida (y, si se da el RUT, si corresponde a él); si no, None."""
    try:
        datos = signing.loads(comprobante.strip(), salt=SAL)
    except signing.BadSignature:
        return None
    if datos.get('tipo') != 'retiro':
        return None
    if rut is not None and not constant_time_compare(_huella(hash_rut(rut)), datos.get('huella', '')):
        return None
    return datos
