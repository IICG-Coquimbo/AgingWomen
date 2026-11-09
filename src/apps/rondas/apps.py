from django.apps import AppConfig


class RondasConfig(AppConfig):
    """
    Fase 40B-1: registro de las rondas de encuesta de cada participante.

    Va en una app propia, y no en apps/encuestas/models.py, para no tocar ese
    archivo: la limpieza histórica (40B-0) y las pruebas de las Fases 35 a 39
    lo leen o comprueban su huella.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rondas'
    verbose_name = 'Registro de rondas'

    def ready(self):
        from . import senales  # noqa: F401  (conecta post_save de Identificacion)
        from .proteccion import conectar
        conectar()  # Fase 40B-2: las rondas cerradas no se modifican
