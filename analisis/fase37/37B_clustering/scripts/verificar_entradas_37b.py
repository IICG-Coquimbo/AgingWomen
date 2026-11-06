"""
Fase 37B, Parte 1: verifica las entradas antes de ejecutar cualquier algoritmo. Escribe integridad/verificacion_entradas.csv.

Uso, desde analisis/: python fase37/37B_clustering/scripts/verificar_entradas_37b.py
"""
import json
import subprocess

import nucleo_37b as Q
import numpy as np
import pandas as pd

filas = []


def ver(nombre, ok, detalle=''):
    filas.append({'comprobacion': nombre, 'resultado': 'OK' if ok else 'FALLA', 'detalle': detalle})
    print('OK   ' if ok else 'FALLA', nombre, detalle, flush=True)


ids = Q.identificadores()
ver('529 identificadores únicos', len(ids) == 529 and len(set(ids)) == 529)
m = pd.read_csv(Q.A37 / 'integridad' / 'manifiesto_final_37A.csv')
d = [r for r, h in zip(m['ruta'], m['sha256']) if not (Q.A37 / r).exists() or Q.sha(Q.A37 / r) != h]
ver('Manifiesto final de la Fase 37A', not d, f'{len(m)} archivos; distintos: {d[:3]}')
m = pd.read_csv(Q.F36 / 'integridad' / 'manifiesto_final_36B.csv', encoding='utf-8')
sys_path_ok = True
Q.sys.path.insert(0, str(Q.ANALISIS / 'revision_correctiva_fase34'))
from manifiesto import huella  # noqa: E402

d = [r for r, h in zip(m['ruta'], m['sha256']) if not (Q.F36 / r).exists() or huella(Q.F36 / r) != h]
ver('Manifiesto final de la Fase 36', not d, f'{len(m)} archivos; distintos: {d[:3]}')
s = json.loads((Q.A37 / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
ver('Sello del protocolo D-13', Q.sha(Q.A37 / 'protocolo' / s['archivo']) == s['sha256'])
for e in Q.ESPACIOS:
    h = json.loads((Q.F36 / 'artefactos' / e / 'huellas.json').read_text(encoding='utf-8'))
    ver(f'Huella de la matriz {e}', Q.sha(Q.F36 / 'matrices' / f'{Q.MATRIZ[e]}.csv') == h['matriz'])
    orden = json.loads((Q.F36 / 'artefactos' / e / 'orden_columnas.json').read_text(encoding='utf-8'))
    Z = Q.matriz(e)
    ver(f'Columnas de {e} en el orden de la Fase 36', list(Z.columns) == orden, f'{Z.shape}')
    Q.verificar_columnas(Z.columns)
    ver(f'Sin variables del MRS en {e}', True)
    modelo = Q.R.cargar(Q.A37 / 'artefactos' / e / 'modelo.json')
    for c in Q.COMPONENTES:
        x = Q.coordenadas(e, c)
        bien = x.shape == (529, c) and list(x.index) == ids and list(x.columns) == [f'C{i + 1}' for i in range(c)] and np.isfinite(x.to_numpy()).all()
        ver(f'Coordenadas {e}, k = {c}', bien and c <= modelo['rango'])
    ver(f'Sin valores faltantes o infinitos en la matriz {e}', np.isfinite(Z.to_numpy()).all())
p = Q.tabla_general()
Q.verificar_columnas(p.columns)
for e in Q.ESPACIOS:
    Z = Q.TF.Transformador.cargar(Q.F36 / 'artefactos' / e).transformar(p)[0]
    ver(f'La tabla general reproduce la matriz {e}', np.abs(Z.to_numpy() - Q.matriz(e).to_numpy()).max() < 1e-12, f'{np.abs(Z.to_numpy() - Q.matriz(e).to_numpy()).max():.1e}')
cab = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=Q.RAIZ, capture_output=True, text=True).stdout.strip()
ver('HEAD sin cambios', cab == '745d689', cab)
t = pd.DataFrame(filas)
(Q.BASE / 'integridad').mkdir(parents=True, exist_ok=True)
t.to_csv(Q.BASE / 'integridad' / 'verificacion_entradas.csv', index=False, encoding='utf-8', lineterminator='\n')
print((t['resultado'] == 'OK').sum(), 'de', len(t))
raise SystemExit(0 if (t['resultado'] == 'OK').all() else 1)
