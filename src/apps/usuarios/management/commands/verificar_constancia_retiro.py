"""Fase 40, Etapa 2: verifica un comprobante de retiro (no consulta ni guarda datos)."""
from django.core.management.base import BaseCommand

from apps.usuarios.constancia_retiro import verificar


class Command(BaseCommand):
    help = 'Verifica la firma de un comprobante de retiro y, opcionalmente, que corresponda a un RUT.'

    def add_arguments(self, parser):
        parser.add_argument('comprobante')
        parser.add_argument('--rut', default=None)

    def handle(self, comprobante, rut=None, **opciones):
        datos = verificar(comprobante, rut=rut)
        if datos is None:
            self.stdout.write('NO VÁLIDO: firma incorrecta o no corresponde a ese RUT.')
            return
        presencial = (f"; presencial, documento de revocación {datos['folio_revocacion']}, "
                      f"registrado por la cuenta profesional {datos['profesional']}"
                      if datos.get('modalidad') == 'presencial' else '')
        self.stdout.write(f"VÁLIDO: retiro {datos['codigo']} del {datos['fecha']} "
                          f"(consentimiento {datos['version']}{presencial})"
                          f"{' y corresponde al RUT indicado' if rut else ''}.")
