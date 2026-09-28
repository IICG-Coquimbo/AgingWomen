"""
Utilidades para el RUT chileno.

El RUT NO se almacena en claro en ninguna parte del sistema (regla 1.2 del spec):
solo se guarda su hash unidireccional (`hash_rut`), que además sirve como
identificador de acceso.
"""
import hashlib
import hmac

from django.conf import settings


def normalizar_rut(rut):
    """
    Deja el RUT sin puntos, guión ni espacios y con la K en mayúscula.
    Ej: ' 12.345.678-k ' -> '12345678K'
    """
    if not rut:
        return ''
    return (
        str(rut)
        .replace('.', '')
        .replace('-', '')
        .replace(' ', '')
        .strip()
        .upper()
    )


def _digito_verificador(cuerpo):
    """Calcula el dígito verificador (módulo 11) para el cuerpo numérico del RUT."""
    suma = 0
    multiplo = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return '0'
    if resto == 10:
        return 'K'
    return str(resto)


def validar_rut(rut):
    """True si el RUT tiene un dígito verificador válido."""
    rut_norm = normalizar_rut(rut)
    if len(rut_norm) < 2 or not rut_norm[:-1].isdigit():
        return False
    cuerpo, dv = rut_norm[:-1], rut_norm[-1]
    return _digito_verificador(cuerpo) == dv


def hash_rut(rut):
    """
    HMAC-SHA256 del RUT normalizado usando el pepper del proyecto.
    Es unidireccional: no se puede recuperar el RUT a partir de este valor.
    """
    rut_norm = normalizar_rut(rut)
    pepper = settings.RUT_HASH_PEPPER.encode('utf-8')
    return hmac.new(pepper, rut_norm.encode('utf-8'), hashlib.sha256).hexdigest()
