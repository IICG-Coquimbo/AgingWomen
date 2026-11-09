"""
Cierre de las Fases 34 y 35: huella SHA-256 del repositorio analítico, con esta carpeta excluida.

Uso, desde la raíz del proyecto:
    python analisis/cierre_fases_34_35/scripts/manifiesto_cierre.py antes
    python analisis/cierre_fases_34_35/scripts/manifiesto_cierre.py despues

Reutiliza la función de huella de la corrección controlada. A diferencia de aquel manifiesto, este también
protege la carpeta analisis/revision_correctiva_fase34/, para conservar sus entregables.
Solo lee los archivos. Escribe únicamente en analisis/cierre_fases_34_35/integridad/.
"""
import csv
import subprocess
import sys
from pathlib import Path

CIERRE = Path(__file__).resolve().parents[1]
RAIZ = CIERRE.parents[1]
sys.path.insert(0, str(RAIZ / 'analisis' / 'revision_correctiva_fase34'))

from manifiesto import huella  # noqa: E402

CARPETAS = [RAIZ / 'analisis', RAIZ / 'datos' / 'analitico', RAIZ / 'datos' / 'limpio_usuaria', RAIZ / 'datos' / 'sintetico']
SALIDA = CIERRE / 'integridad'


def archivos():
    for carpeta in CARPETAS:
        for ruta in sorted(carpeta.rglob('*')):
            if ruta.is_file() and '__pycache__' not in ruta.parts and CIERRE not in ruta.parents:
                yield ruta


def main(etapa):
    SALIDA.mkdir(parents=True, exist_ok=True)
    filas = [(r.relative_to(RAIZ).as_posix(), r.stat().st_size, huella(r)) for r in archivos()]
    with (SALIDA / f'manifiesto_{etapa}.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ruta', 'bytes', 'sha256'])
        w.writerows(filas)
    def git(*a):
        return subprocess.run(['git', *a], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8').stdout
    (SALIDA / f'git_{etapa}.txt').write_text(f'HEAD {git("rev-parse", "HEAD").strip()}\n{git("status", "--short", "--untracked-files=no")}', encoding='utf-8')
    print(f'{etapa}: {len(filas)} archivos')


if __name__ == '__main__':
    main(sys.argv[1])
