"""
Revisión correctiva de la Fase 34: huella SHA-256 de todo lo protegido.

Uso, desde la raíz del proyecto:
    python analisis/revision_correctiva_fase34/manifiesto.py antes
    python analisis/revision_correctiva_fase34/manifiesto.py despues

Solo lee los archivos protegidos. Escribe únicamente dentro de esta carpeta.
"""
import csv
import hashlib
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
CARPETAS = [RAIZ / 'analisis', RAIZ / 'datos' / 'analitico', RAIZ / 'datos' / 'limpio_usuaria',
            RAIZ / 'datos' / 'sintetico']


def huella(ruta):
    h = hashlib.sha256()
    with ruta.open('rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def archivos():
    for carpeta in CARPETAS:
        for ruta in sorted(carpeta.rglob('*')):
            if not ruta.is_file() or '__pycache__' in ruta.parts or AQUI in ruta.parents:
                continue
            yield ruta


def main(etapa):
    salida = AQUI / 'manifiestos' / f'manifiesto_{etapa}.csv'
    salida.parent.mkdir(exist_ok=True)
    filas = [(r.relative_to(RAIZ).as_posix(), r.stat().st_size, huella(r)) for r in archivos()]
    with salida.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ruta', 'bytes', 'sha256'])
        w.writerows(filas)
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    (salida.parent / f'head_{etapa}.txt').write_text(head + '\n', encoding='utf-8')
    print(f'{etapa}: {len(filas)} archivos; HEAD {head}')


if __name__ == '__main__':
    main(sys.argv[1])
