"""
Fase documental 38R/39R: control de integridad propio. Solo calcula huellas y lee Git; escribe únicamente en documentos_definitivos/validacion/.
No usa integridad_38r.py ni integridad_39r.py, porque esos scripts sobrescribirían sus carpetas integridad/.

Uso: python -B control_integridad_documental.py inicial | final
"""
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
DOC = AQUI.parent
R38 = DOC.parent
RAIZ = R38.parents[2]
R39 = RAIZ / 'analisis' / 'fase39' / '39R_asociaciones_condicionadas_corregidas'
VAL = DOC / 'validacion'
VAL.mkdir(parents=True, exist_ok=True)
PROHIBIDOS = ('verdad', 'bitacora', 'dataset_usuaria_sucio')
OMITIR = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env', 'documentos_definitivos'}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def huellas():
    salida, omitidos = {}, []
    for carpeta, subs, archivos in os.walk(RAIZ):
        subs[:] = [s for s in subs if s not in OMITIR]
        for a in archivos:
            p = Path(carpeta) / a
            r = p.relative_to(RAIZ).as_posix()
            if any(x in a.lower() for x in PROHIBIDOS):
                e = p.stat()
                omitidos.append(r)
                salida[r] = f'sin abrir:{e.st_size}:{e.st_mtime_ns}'
                continue
            salida[r] = sha(p)
    return salida, omitidos


def git(*a):
    return subprocess.run(['git', '--no-optional-locks', *a], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8').stdout


def estado_git():
    return {'rama': git('rev-parse', '--abbrev-ref', 'HEAD').strip(), 'head': git('rev-parse', 'HEAD').strip(), 'stash': len(git('stash', 'list').splitlines()),
            'status': git('status', '--porcelain').splitlines()}


def leer_csv(p):
    with open(p, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def sellos():
    fil = {}
    for nombre, base, arch in (('38R', R38, '01_protocolo_38R.md'), ('39R', R39, '01_protocolo_39R.md')):
        s = json.loads((base / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
        real = sha(base / 'protocolo' / arch)
        fil[nombre] = {'sellado': s.get('sha256'), 'actual': real, 'coincide': s.get('sha256') == real}
    return fil


def pendientes():
    fil = leer_csv(R38 / 'integridad' / 'manifiesto_pendientes_inicial.csv')
    distintos = [x['ruta'] for x in fil if not (RAIZ / x['ruta']).is_file() or sha(RAIZ / x['ruta']) != x['sha256']]
    return {'archivos': len(fil), 'distintos': distintos}


def contra_ultimo_control(h):
    """Compara con las huellas finales de la 39R (último control del cálculo)."""
    fil = leer_csv(R39 / 'integridad' / 'huellas_final.csv')
    cambiados = [x['ruta'] for x in fil if h.get(x['ruta']) != x['huella']]
    return {'huellas_comparadas': len(fil), 'distintas': cambiados}


modo = sys.argv[1]
h, omitidos = huellas()
est = estado_git()
res = {'modo': modo, 'fecha': datetime.now().isoformat(timespec='seconds'), 'archivos': len(h), 'omitidos_por_nombre_sin_abrir': omitidos, 'git': est, 'sellos': sellos(),
       'pendientes_fase_40': pendientes(), 'contra_huellas_finales_39R': contra_ultimo_control(h)}
with open(VAL / f'huellas_{modo}.csv', 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['ruta', 'sha256'])
    w.writerows(sorted(h.items()))
if modo == 'final':
    ini = {x['ruta']: x['sha256'] for x in leer_csv(VAL / 'huellas_inicial.csv')}
    res['comparacion_con_inicial'] = {'cambiados': sorted(k for k in ini if k in h and ini[k] != h[k]), 'desaparecidos': sorted(set(ini) - set(h)), 'nuevos': sorted(set(h) - set(ini))}
    gi = json.loads((VAL / 'control_inicial.json').read_text(encoding='utf-8'))['git']
    res['git_igual_al_inicial'] = gi == est
(VAL / f'control_{modo}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
print({k: (v if k not in ('git', 'omitidos_por_nombre_sin_abrir') else '...') for k, v in res.items()})
print('git:', est['rama'], est['head'][:7], 'status', len(est['status']), 'stash', est['stash'])
