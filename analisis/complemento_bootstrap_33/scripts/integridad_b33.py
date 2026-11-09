"""Complemento bootstrap 33: huellas SHA-256 de todo lo protegido, antes y después de ejecutar.

Uso, desde analisis/complemento_bootstrap_33/scripts:
    python integridad_b33.py antes
    python integridad_b33.py despues

Protegido: todo `analisis/` (salvo esta carpeta y los __pycache__), todo `src/` y `datos/` salvo `datos/reales` y el
archivo de verdad del simulador, que ni siquiera se abren para calcular su huella.
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
ANALISIS = BASE.parent
RAIZ = ANALISIS.parent
SALIDA = BASE / 'integridad'
EXCLUIR_DATOS = {'reales'}
VERDAD = 'dataset_usuaria_verdad.csv'


def sha(ruta):
    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def protegidos():
    rutas = []
    for p in ANALISIS.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or BASE in p.parents:
            continue
        rutas.append(p)
    rutas += [p for p in (RAIZ / 'src').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    for p in (RAIZ / 'datos').rglob('*'):
        rel = p.relative_to(RAIZ / 'datos').parts
        if p.is_file() and rel[0] not in EXCLUIR_DATOS and p.name != VERDAD:
            rutas.append(p)
    return sorted(rutas)


def manifiesto():
    return {p.relative_to(RAIZ).as_posix(): sha(p) for p in protegidos()}


def git(*args):
    return subprocess.run(['git', *args], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8').stdout


def estado_git():
    return {'head': git('rev-parse', 'HEAD').strip(), 'rama': git('branch', '--show-current').strip(),
            'status': sorted(l for l in git('status', '--porcelain').splitlines() if 'complemento_bootstrap_33' not in l)}


def main(modo):
    SALIDA.mkdir(parents=True, exist_ok=True)
    m, g = manifiesto(), estado_git()
    if modo == 'antes':
        ruta = SALIDA / 'manifiesto_antes.json'
        if ruta.exists():
            raise SystemExit('El manifiesto inicial ya existe: no se sobrescribe.')
        ruta.write_text(json.dumps({'fecha': datetime.now().isoformat(timespec='seconds'), 'git': g, 'archivos': m},
                                   ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'{len(m)} archivos protegidos; HEAD {g["head"][:7]}; {len(g["status"])} entradas de git status')
        return
    antes = json.loads((SALIDA / 'manifiesto_antes.json').read_text(encoding='utf-8'))
    a = antes['archivos']
    cambiados = sorted(k for k in a if k in m and a[k] != m[k])
    faltan = sorted(set(a) - set(m))
    nuevos = sorted(set(m) - set(a))
    res = {'fecha': datetime.now().isoformat(timespec='seconds'), 'comparados': len(a), 'cambiados': cambiados,
           'eliminados': faltan, 'nuevos_fuera_de_la_carpeta': nuevos, 'git_antes': antes['git'], 'git_despues': g,
           'git_igual': antes['git'] == g,
           'pycache_nuevo': sorted(str(p.relative_to(RAIZ)) for p in BASE.rglob('__pycache__'))}
    (SALIDA / 'integridad_final.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{len(a)} comparados; cambiados {len(cambiados)}; eliminados {len(faltan)}; nuevos {len(nuevos)}; "
          f"git igual {res['git_igual']}; __pycache__ en la carpeta {len(res['pycache_nuevo'])}")
    for x in cambiados + faltan + nuevos:
        print('  ', x)
    sys.exit(int(bool(cambiados or faltan or nuevos or not res['git_igual'])))


if __name__ == '__main__':
    main(sys.argv[1])
