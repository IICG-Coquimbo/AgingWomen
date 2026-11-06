"""
Fase 40B-0: genera analisis/limpieza/definiciones_fase34.py (una sola vez).

Extrae los cuatro archivos de src/apps/encuestas tal como estaban en el commit
de referencia (git show, no el árbol de trabajo), los lee con las funciones
*_plataforma de catalogo.py en un directorio temporal y escribe las seis
definiciones como literales de Python, con las huellas de origen y del contenido.

Uso:
    python analisis/fase40/40B_implementacion/scripts/congelar_definiciones_fase34.py
        → crea el archivo; se niega si ya existe (nunca lo sobrescribe).
    ... --verificar
        → solo comprueba que el archivo existente coincide con lo que se generaría.
"""
import hashlib
import pprint
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / 'analisis'))
from limpieza import catalogo  # noqa: E402

COMMIT = '44bfe0b6617150d56ac3ddb73b26bdbdacafbb57'
FUENTES = ['models.py', 'condicionales.py', 'campos_por_rol.py', 'datos_geograficos.py']
DESTINO = RAIZ / 'analisis' / 'limpieza' / 'definiciones_fase34.py'


def git(*args):
    return subprocess.run(['git', *args], cwd=RAIZ, check=True, capture_output=True).stdout


def ultimo_cambio(archivo):
    return git('log', '-1', '--format=%h %ad', '--date=short', COMMIT, '--',
               f'src/apps/encuestas/{archivo}').decode().strip()


def generar():
    with tempfile.TemporaryDirectory() as tmp:
        origen = {}
        for f in FUENTES:
            contenido = git('show', f'{COMMIT}:src/apps/encuestas/{f}')
            (Path(tmp) / f).write_bytes(contenido)
            origen[f] = (hashlib.sha256(contenido).hexdigest(), ultimo_cambio(f))
        defs = catalogo.leer_plataforma(tmp)
    campos, severidad, condicionales, secciones, solo_prof, comunas = defs

    def literal(nombre, valor):
        return f'{nombre} = {pprint.pformat(valor, sort_dicts=False, width=110)}\n'

    lineas = [
        '"""',
        'Definiciones congeladas de la encuesta usadas por la limpieza histórica (Fases 32-34).',
        '',
        'GENERADO por analisis/fase40/40B_implementacion/scripts/congelar_definiciones_fase34.py',
        '(Fase 40B-0). NO EDITAR A MANO: catalogo.py comprueba HUELLA_CONTENIDO al leerlo y se',
        'detiene si el contenido cambió. Si la plataforma cambia, este archivo NO debe seguirla:',
        'reproduce la limpieza de la Fase 34. Una limpieza nueva requiere un archivo nuevo y versionado.',
        '',
        f'Origen: src/apps/encuestas en el commit {COMMIT}.',
        'SHA-256 de cada archivo de origen (contenido en git) y su último cambio:',
    ]
    lineas += [f'  {f:<22} {h}  (último cambio {c})' for f, (h, c) in origen.items()]
    lineas += ['"""', '', "VERSION = 'fase34-v1'", f"COMMIT_ORIGEN = '{COMMIT}'",
               'SHA256_ORIGEN = {', *[f"    '{f}': '{h}'," for f, (h, _) in origen.items()], '}',
               f"HUELLA_CONTENIDO = '{catalogo.huella(*defs)}'", '',
               '# MRS.SEVERIDAD_TOTAL: (máximo inclusive del puntaje total, categoría).',
               literal('SEVERIDAD_TOTAL', severidad),
               '# condicionales.SECCIONES_CONDICIONALES',
               literal('SECCIONES_CONDICIONALES', secciones),
               '# condicionales.PREGUNTAS_CONDICIONALES',
               literal('PREGUNTAS_CONDICIONALES', condicionales),
               '# campos_por_rol.SOLO_PROFESIONAL (unión de todas las secciones)',
               literal('SOLO_PROFESIONAL', tuple(sorted(solo_prof))),
               '# datos_geograficos.COMUNAS_POR_REGION',
               literal('COMUNAS_POR_REGION', comunas),
               '# models.py: {campo: {modelo, tipo, opciones {código: etiqueta} o None}}, en el orden del archivo',
               literal('CAMPOS', campos)]
    return '\n'.join(lineas)


if __name__ == '__main__':
    texto = generar()
    if '--verificar' in sys.argv:
        igual = DESTINO.read_text(encoding='utf-8') == texto
        print('Coincide con lo generado desde el commit de referencia.' if igual else 'NO COINCIDE')
        sys.exit(0 if igual else 1)
    if DESTINO.exists():
        sys.exit(f'{DESTINO} ya existe; no se sobrescribe. Use --verificar.')
    DESTINO.write_text(texto, encoding='utf-8', newline='\n')
    print(f'Creado {DESTINO.relative_to(RAIZ).as_posix()}')
