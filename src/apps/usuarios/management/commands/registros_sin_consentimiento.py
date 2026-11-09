"""
Fase 40: informe de SOLO LECTURA de los registros sin consentimiento verificable
(p. ej., registros presenciales anteriores a la Etapa 2 sin constancia).

No modifica, no elimina y no «regulariza» nada: esos registros se conservan, quedan
fuera de las estadísticas y no admiten respuestas nuevas hasta que haya un
consentimiento válido (registrado presencialmente con su documento, o aceptado por
ella en su cuenta) o hasta que ella pida retirarse. Muestra solo el número de ficha,
la ronda en curso y el motivo: ningún RUT (no se guarda) ni dato de salud.
"""
from django.core.management.base import BaseCommand

from apps.encuestas.estadisticas import ETIQUETAS_EXCLUSION, motivo_exclusion
from apps.encuestas.models import Identificacion


class Command(BaseCommand):
    help = 'Lista (sin modificar nada) las fichas sin consentimiento verificable.'

    def handle(self, **opciones):
        por_motivo = {}
        for ficha in Identificacion.objects.select_related('usuario').order_by('pk'):
            motivo = motivo_exclusion(ficha)
            if motivo:
                por_motivo.setdefault(motivo, []).append(ficha)
        if not por_motivo:
            self.stdout.write('No hay fichas sin consentimiento verificable.')
            return
        for motivo, fichas in por_motivo.items():
            self.stdout.write(f'{ETIQUETAS_EXCLUSION.get(motivo, motivo)}: {len(fichas)}')
            for f in fichas:
                self.stdout.write(f'  ficha N.º {f.pk} (ronda en curso {f.ronda_actual})')
        self.stdout.write('Nada se modificó. Estas fichas se conservan, no entran en las estadísticas y no '
                          'admiten respuestas nuevas hasta registrar un consentimiento válido.')
