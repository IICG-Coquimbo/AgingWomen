"""
createsuperuser con validación del RUT.

El campo de acceso del modelo es `rut_hash`, así que el comando de Django no
sabe que lo escrito es un RUT: no revisa el dígito verificador y su chequeo de
"ya existe" compara el RUT en claro contra hashes (nunca coincide). Aquí se
valida el RUT y se busca por su hash antes de crear la cuenta. Sirve tanto en
modo interactivo (vuelve a pedir el RUT) como con --noinput (falla con error).
"""
from django.contrib.auth.management.commands import createsuperuser

from apps.usuarios.models import Usuario
from apps.usuarios.rut import hash_rut, validar_rut


class Command(createsuperuser.Command):

    def _validate_username(self, username, verbose_field_name, database):
        if username:
            if not validar_rut(username):
                return 'Error: RUT inválido, revisa el dígito verificador.'
            if Usuario.objects.db_manager(database).filter(rut_hash=hash_rut(username)).exists():
                return 'Error: ya existe una cuenta con ese RUT.'
        return super()._validate_username(username, verbose_field_name, database)
