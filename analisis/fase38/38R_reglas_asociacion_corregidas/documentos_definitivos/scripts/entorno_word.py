"""Ubicación explícita del paquete docx para los generadores de Word de la 38R y la 39R."""
import os
from pathlib import Path

HERRAMIENTAS = Path(__file__).resolve().parent.parent / 'herramientas_word'
NODE_MODULES = HERRAMIENTAS / 'node_modules'


def entorno_node():
    """Entorno para llamar a node. Se detiene si el paquete no está instalado en herramientas_word."""
    if not (NODE_MODULES / 'docx' / 'package.json').exists():
        raise SystemExit(f'Falta el paquete docx. Ejecuta «npm ci» en {HERRAMIENTAS} (ver LEEME.md).')
    return {**os.environ, 'NODE_PATH': str(NODE_MODULES)}
