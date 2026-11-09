"""
Fase 38R: control correctivo de integridad, independiente de HEAD (los controles históricos exigen HEAD 745d689 y ya no pueden cumplirse; se documenta y no se modifican).

Inicial: huella SHA-256 de todo analisis/ (salvo la propia 38R), datos/analitico, datos/limpio_usuaria, datos/sintetico y src/.
Final: repite y compara, comprueba los manifiestos de las Fases 34 a 39, los pendientes de la Fase 40 y el estado de Git.
Los archivos cuyo nombre contiene verdad, bitacora o dataset_usuaria_sucio no se abren: se registra solo tamaño y fecha.

Uso, desde la raíz: python -B analisis/fase38/38R_reglas_asociacion_corregidas/scripts/integridad_38r.py inicial|final
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
RAIZ = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parents[1]
D = BASE / 'integridad'
PROPIA = BASE.relative_to(RAIZ).as_posix()
PROHIBIDOS = ('verdad', 'bitacora', 'dataset_usuaria_sucio')
ALCANCE = ['analisis', 'datos/analitico', 'datos/limpio_usuaria', 'datos/sintetico', 'src']
A = RAIZ / 'analisis'
EXCEPCIONES_DOCUMENTADAS = {'analisis/limpieza/catalogo.py', 'analisis/eda/univariado.py', 'analisis/eda_usuaria.py'}
PRUEBA_40B1 ='analisis/fase40/40B_implementacion/pruebas/test_40b1_proteccion_historica.py'
MANIFIESTOS = [
    ('Fases 34-35 (cierre)', A / 'cierre_fases_34_35/integridad/manifiesto_despues.csv', RAIZ),
    ('Revisión correctiva 34', A / 'revision_correctiva_fase34/manifiestos/manifiesto_correccion_despues.csv', RAIZ),
    ('Fase 36', A / 'fase36/integridad/manifiesto_final_36B.csv', A / 'fase36'),
    ('Fase 37A', A / 'fase37/37A_reduccion/integridad/manifiesto_final_37A.csv', A / 'fase37/37A_reduccion'),
    ('Fase 37B', A / 'fase37/37B_clustering/integridad/manifiesto_final_37B.csv', A / 'fase37/37B_clustering'),
    ('Fase 37C', A / 'fase37/37C_comparacion_seleccion/integridad/manifiesto_final_37C.csv', A / 'fase37/37C_comparacion_seleccion'),
    ('Complemento 37C', A / 'fase37/37C_complemento_tres_preguntas/integridad/manifiesto_final.csv', A / 'fase37/37C_complemento_tres_preguntas'),
    ('Fase 37D', A / 'fase37/37D_caracterizacion/integridad/manifiesto_final.csv', A / 'fase37/37D_caracterizacion'),
    ('Fase 38', A / 'fase38/38_reglas_asociacion_generales/integridad/manifiesto_final.csv', A / 'fase38/38_reglas_asociacion_generales'),
    ('Fase 39', A / 'fase39/39_asociaciones_condicionadas/integridad/manifiesto_final.csv', A / 'fase39/39_asociaciones_condicionadas'),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def git(*a):
    return subprocess.run(['git', '--no-optional-locks', *a], cwd=RAIZ, capture_output=True, check=True).stdout.decode('utf-8', 'replace')


def huellas():
    out = {}
    for raiz in ALCANCE:
        for carpeta, subs, archivos in os.walk(RAIZ / raiz):
            rel = Path(carpeta).relative_to(RAIZ).as_posix()
            subs[:] = [s for s in subs if s != '__pycache__' and not f'{rel}/{s}'.startswith(PROPIA)]
            for a in archivos:
                p = Path(carpeta) / a
                r = f'{rel}/{a}'
                if any(x in a.lower() for x in PROHIBIDOS):
                    e = p.stat()
                    out[r] = f'sin abrir:{e.st_size}:{e.st_mtime_ns}'
                else:
                    out[r] = sha(p)
    return out


def guardar(h, ruta):
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['ruta', 'huella'])
        w.writerows(sorted(h.items()))


def leer(ruta):
    with open(ruta, encoding='utf-8', newline='') as f:
        return {r['ruta']: r['huella'] for r in csv.DictReader(f)}


def pycache():
    return sorted(p.relative_to(RAIZ).as_posix() for b in ('analisis/fase38', 'analisis/fase39', 'analisis/fase37', 'analisis/fase36') for p in (RAIZ / b).rglob('__pycache__'))


def manifiestos():
    filas = []
    for nombre, m, base in MANIFIESTOS:
        with open(m, encoding='utf-8-sig', newline='') as f:
            t = list(csv.DictReader(f))
        col = next(c for c in ('ruta', 'archivo') if c in t[0])
        dist, omit = [], 0
        for r in t:
            p = Path(base) / r[col]
            if any(x in p.name.lower() for x in PROHIBIDOS):
                omit += 1
                continue
            if not p.is_file() or sha(p) != r['sha256']:
                dist.append(r[col])
        filas.append({'fase': nombre, 'archivos': len(t), 'omitidos_por_nombre': omit, 'distintos': len(dist), 'ejemplos': '; '.join(dist[:4])})
    return filas


def prueba_40b1():
    r = subprocess.run([sys.executable, '-B', '-m', 'unittest', PRUEBA_40B1], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8', errors='replace', env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONIOENCODING': 'utf-8'})
    return {'codigo': r.returncode, 'cola': r.stderr.strip().splitlines()[-3:]}


def main(momento):
    D.mkdir(parents=True, exist_ok=True)
    h = huellas()
    guardar(h, D / f'huellas_{momento}.csv')
    M = manifiestos()
    with open(D / f'manifiestos_{momento}.csv', 'w', encoding='utf-8', newline='\n') as f:
        w = csv.DictWriter(f, list(M[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(M)
    t = prueba_40b1()
    inicial_git = json.loads((D / 'estado_git_inicial.json').read_text(encoding='utf-8'))
    actual = [l for l in git('status', '--porcelain=v1').splitlines() if PROPIA not in l and l[3:].strip() != 'analisis/fase38/']
    res = {'momento': momento, 'fecha': datetime.now().isoformat(timespec='seconds'), 'archivos_con_huella': len(h), 'manifiestos_archivos': sum(x['archivos'] for x in M), 'manifiestos_distintos': sum(x['distintos'] for x in M),
           'prueba_40b1': t, 'rama': git('rev-parse', '--abbrev-ref', 'HEAD').strip(), 'head': git('rev-parse', 'HEAD').strip(), 'lineas_git_status_sin_38R': len(actual),
           'git_status_igual_al_inicial': actual == inicial_git['git_status'], 'pycache_fases_36_a_39': pycache()}
    # los pendientes de la Fase 40 deben seguir iguales a la copia de seguridad
    with open(D / 'manifiesto_pendientes_inicial.csv', encoding='utf-8', newline='') as f:
        p = list(csv.DictReader(f))
    res['pendientes'] = len(p)
    res['pendientes_distintos'] = [x['ruta'] for x in p if not (RAIZ / x['ruta']).is_file() or sha(RAIZ / x['ruta']) != x['sha256']]
    if momento == 'final':
        ini = leer(D / 'huellas_inicial.csv')
        res['huellas_cambiadas'] = sorted(r for r in ini if h.get(r) != ini[r])
        res['huellas_nuevas'] = sorted(r for r in h if r not in ini)
    (D / f'integridad_{momento}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    for x in M:
        print(x)
    print({k: v for k, v in res.items()})
    # Las únicas diferencias admitidas frente a los manifiestos son las tres excepciones ya documentadas en test_40b1 (commit 573d3a3, anteriores a la 38R).
    res['manifiestos_diferencias_no_documentadas'] = sorted({e for x in M for e in x['ejemplos'].split('; ') if e} - EXCEPCIONES_DOCUMENTADAS)
    (D / f'integridad_{momento}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    ok = not res['manifiestos_diferencias_no_documentadas'] and t['codigo'] == 0 and res['git_status_igual_al_inicial'] and not res['pendientes_distintos'] and not res['pycache_fases_36_a_39']
    if momento == 'final':
        ok = ok and not res['huellas_cambiadas'] and not res['huellas_nuevas']
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'inicial')
