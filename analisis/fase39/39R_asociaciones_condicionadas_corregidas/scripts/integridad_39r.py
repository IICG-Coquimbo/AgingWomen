"""
Fase 39R: control correctivo de integridad, independiente de HEAD (los controles históricos de la Fase 39 exigen HEAD 745d689 y src/ sin cambios; ya no pueden cumplirse: se documenta y no se modifican).

Inicial: huella SHA-256 de todo analisis/ (incluida la 38R, salvo la propia 39R), datos/analitico, datos/limpio_usuaria, datos/sintetico y src/; estado de Git y comprobación del respaldo.
Final: repite y compara, comprueba los manifiestos de las Fases 34 a 39, el sello de la 38R, los pendientes de la Fase 40 y el estado de Git.
Los archivos cuyo nombre contiene verdad, bitacora o dataset_usuaria_sucio no se abren: se registra solo tamaño y fecha.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/integridad_39r.py inicial|final
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
D38R = A / 'fase38' / '38R_reglas_asociacion_corregidas'
RESPALDO = RAIZ / 'datos' / 'respaldos' / '2026-11-08_antes_38R'
EXCEPCIONES_DOCUMENTADAS = {'analisis/limpieza/catalogo.py', 'analisis/eda/univariado.py', 'analisis/eda_usuaria.py'}
PRUEBA_40B1 = 'analisis/fase40/40B_implementacion/pruebas/test_40b1_proteccion_historica.py'
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


def sello_38r():
    """Sello de la 38R: protocolo y código sellados, sin ejecutar nada de esa fase."""
    s = json.loads((D38R / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    malos = [] if sha(D38R / 'protocolo' / s['archivo']) == s['sha256'] else [s['archivo']]
    malos += [c for c, h in s['codigo'].items() if sha(D38R / 'scripts' / c) != h]
    final = json.loads((D38R / 'integridad' / 'integridad_final.json').read_text(encoding='utf-8'))
    return {'sha256': s['sha256'], 'distintos': malos, 'integridad_final_38R': {k: final.get(k) for k in ('fecha', 'huellas_cambiadas', 'pendientes_distintos', 'manifiestos_diferencias_no_documentadas')}}


def comprobar_respaldo():
    """Copias del respaldo previo a la 38R frente a su manifiesto, y archivos pendientes actuales frente a ese mismo manifiesto."""
    with open(RESPALDO / 'manifiesto_pendientes.csv', encoding='utf-8-sig', newline='') as f:
        t = list(csv.DictReader(f))
    col = next(c for c in ('ruta', 'archivo') if c in t[0])
    copia = [r[col] for r in t if not (RESPALDO / 'archivos' / r[col]).is_file() or sha(RESPALDO / 'archivos' / r[col]) != r['sha256']]
    actual = [r[col] for r in t if not (RAIZ / r[col]).is_file() or sha(RAIZ / r[col]) != r['sha256']]
    return {'archivos': len(t), 'copias_distintas': copia, 'pendientes_actuales_distintos': actual}


def lineas_status():
    return [l for l in git('status', '--porcelain=v1').splitlines() if PROPIA not in l]


def main(momento):
    D.mkdir(parents=True, exist_ok=True)
    if momento == 'inicial':
        for x in ('huellas_inicial.csv', 'integridad_inicial.json', 'estado_git_inicial.json'):
            if (D / x).exists():
                raise SystemExit(f'Ya existe {x}: la medición inicial no se reemplaza.')
        (D / 'estado_git_inicial.json').write_text(json.dumps({'fecha': datetime.now().isoformat(timespec='seconds'), 'rama': git('rev-parse', '--abbrev-ref', 'HEAD').strip(), 'head': git('rev-parse', 'HEAD').strip(), 'git_status': lineas_status()}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    h = huellas()
    guardar(h, D / f'huellas_{momento}.csv')
    M = manifiestos()
    with open(D / f'manifiestos_{momento}.csv', 'w', encoding='utf-8', newline='\n') as f:
        w = csv.DictWriter(f, list(M[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(M)
    t = prueba_40b1()
    ini = json.loads((D / 'estado_git_inicial.json').read_text(encoding='utf-8'))
    actual = lineas_status()
    res = {'momento': momento, 'fecha': datetime.now().isoformat(timespec='seconds'), 'archivos_con_huella': len(h), 'manifiestos_archivos': sum(x['archivos'] for x in M), 'manifiestos_distintos': sum(x['distintos'] for x in M),
           'manifiestos_diferencias_no_documentadas': sorted({e for x in M for e in x['ejemplos'].split('; ') if e} - EXCEPCIONES_DOCUMENTADAS), 'prueba_40b1': t, 'rama': git('rev-parse', '--abbrev-ref', 'HEAD').strip(), 'head': git('rev-parse', 'HEAD').strip(),
           'head_igual_al_inicial': git('rev-parse', 'HEAD').strip() == ini['head'], 'rama_igual_a_la_inicial': git('rev-parse', '--abbrev-ref', 'HEAD').strip() == ini['rama'], 'lineas_git_status_sin_39R': len(actual), 'git_status_igual_al_inicial': actual == ini['git_status'],
           'pycache_fases_36_a_39': pycache(), 'sello_38R': sello_38r(), 'respaldo_antes_38R': comprobar_respaldo()}
    ok = not res['manifiestos_diferencias_no_documentadas'] and t['codigo'] == 0 and res['git_status_igual_al_inicial'] and res['head_igual_al_inicial'] and res['rama_igual_a_la_inicial'] and not res['pycache_fases_36_a_39'] \
        and not res['sello_38R']['distintos'] and not res['respaldo_antes_38R']['copias_distintas'] and not res['respaldo_antes_38R']['pendientes_actuales_distintos']
    if momento == 'final':
        inicial = leer(D / 'huellas_inicial.csv')
        res['huellas_cambiadas'] = sorted(r for r in inicial if h.get(r) != inicial[r])
        res['huellas_nuevas'] = sorted(r for r in h if r not in inicial)
        ok = ok and not res['huellas_cambiadas'] and not res['huellas_nuevas']
    res['correcto'] = bool(ok)
    (D / f'integridad_{momento}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    for x in M:
        print(x)
    print(res)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'inicial')
