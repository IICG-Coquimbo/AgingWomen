"""
Fase 38R: copia de seguridad verificable de los archivos locales pendientes, con sus rutas relativas, antes de crear resultados.

Solo lee Git (sin bloqueos opcionales) y solo escribe en datos/respaldos/ (ignorada por Git) y en la carpeta de la Fase 38R.
Se detiene si el destino ya existe o si alguna copia no coincide con su original.

Uso, desde la raíz: python -B analisis/fase38/38R_reglas_asociacion_corregidas/scripts/respaldo_pendientes.py
"""
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parents[1]
PROPIA = BASE.relative_to(RAIZ).as_posix() + '/'
DEST = RAIZ / 'datos' / 'respaldos' / '2026-11-08_antes_38R'


def git(*a):
    return subprocess.run(['git', '--no-optional-locks', *a], cwd=RAIZ, capture_output=True, check=True).stdout


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    if DEST.exists():
        raise SystemExit(f'El destino ya existe, no se sobrescribe: {DEST}')
    rutas = sorted({x.decode('utf-8') for x in git('ls-files', '-m', '-o', '--exclude-standard', '-z').split(b'\0') if x and not x.decode('utf-8').startswith(PROPIA)})
    estado = git('status', '--porcelain=v1').decode('utf-8').splitlines()
    estado = [l for l in estado if PROPIA.rstrip('/') not in l and 'analisis/fase38/' != l[3:].strip()]
    filas = []
    for r in rutas:
        o = RAIZ / r
        if not o.is_file():
            raise SystemExit(f'Pendiente que no es un archivo legible: {r}')
        d = DEST / 'archivos' / r
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(o, d)
        so, sd = sha(o), sha(d)
        if so != sd:
            raise SystemExit(f'La copia no coincide con el original: {r}')
        filas.append({'ruta': r, 'bytes': o.stat().st_size, 'sha256': so})
    for nombre in (DEST / 'manifiesto_pendientes.csv', BASE / 'integridad' / 'manifiesto_pendientes_inicial.csv'):
        nombre.parent.mkdir(parents=True, exist_ok=True)
        with open(nombre, 'w', encoding='utf-8', newline='\n') as f:
            w = csv.DictWriter(f, ['ruta', 'bytes', 'sha256'], lineterminator='\n')
            w.writeheader()
            w.writerows(filas)
    info = {'fecha': datetime.now().isoformat(timespec='seconds'), 'rama': git('rev-parse', '--abbrev-ref', 'HEAD').decode().strip(), 'head': git('rev-parse', 'HEAD').decode().strip(),
            'lineas_git_status': len(estado), 'archivos_pendientes': len(filas), 'modificados': sum(l[:2] == ' M' for l in estado), 'entradas_sin_seguimiento': sum(l[:2] == '??' for l in estado),
            'bytes_totales': sum(f['bytes'] for f in filas), 'destino': DEST.relative_to(RAIZ).as_posix(), 'copias_verificadas_sha256': len(filas), 'git_status': estado}
    for nombre in (DEST / 'estado_git.json', BASE / 'integridad' / 'estado_git_inicial.json'):
        nombre.write_text(json.dumps(info, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print({k: v for k, v in info.items() if k != 'git_status'})


if __name__ == '__main__':
    main()
