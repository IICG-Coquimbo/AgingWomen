from django.core.management.base import BaseCommand, CommandError

from apps.usuarios.models import Usuario
from apps.usuarios.rut import validar_rut


class Command(BaseCommand):
    help = (
        'Crea una cuenta de personal del servicio de salud (rol PROFESIONAL). '
        'El personal de salud recibe sus credenciales del servicio, no se auto-registra.'
    )

    def add_arguments(self, parser):
        parser.add_argument('rut', help='RUT del profesional (con o sin puntos/guión)')
        parser.add_argument('email', help='Correo del profesional')
        parser.add_argument(
            '--password',
            help='Contraseña. Si se omite, la persona define la suya con «Olvidé mi contraseña».',
        )

    def handle(self, *args, **options):
        rut = options['rut']
        if not validar_rut(rut):
            raise CommandError(f'RUT inválido: {rut}')

        usuario = Usuario.objects.create_user(
            rut=rut,
            email=options['email'],
            password=options.get('password'),
            rol=Usuario.Rol.PROFESIONAL_SALUD,
        )

        self.stdout.write(self.style.SUCCESS(f'Profesional creado: {usuario.email}'))
        if not options.get('password'):
            self.stdout.write('Para definir su contraseña debe usar «Olvidé mi contraseña» con ese correo.')
