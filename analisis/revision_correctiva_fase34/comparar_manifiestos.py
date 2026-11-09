"""
Compara las huellas de antes y después. Uso: python analisis/revision_correctiva_fase34/comparar_manifiestos.py
Termina con error si algún archivo protegido cambió, desapareció o apareció.
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent


def leer(etapa):
    with (AQUI / 'manifiestos' / f'manifiesto_{etapa}.csv').open(encoding='utf-8') as f:
        return {r['ruta']: r['sha256'] for r in csv.DictReader(f)}


antes, despues = leer('antes'), leer('despues')
cambiados = sorted(r for r in antes if r in despues and antes[r] != despues[r])
faltan, nuevos = sorted(set(antes) - set(despues)), sorted(set(despues) - set(antes))
head_a = (AQUI / 'manifiestos' / 'head_antes.txt').read_text().strip()
head_d = (AQUI / 'manifiestos' / 'head_despues.txt').read_text().strip()
versionados = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=RAIZ, capture_output=True, text=True).stdout.split()
claves = ['datos/analitico/dataset_fase35_33_variables.csv', 'datos/limpio_usuaria/dataset_usuaria_limpio.csv',
          'analisis/reunion_2026-11-03/revision_33_variables/permutaciones_50000/relevancia_33.csv',
          'analisis/reunion_2026-11-03/revision_33_variables/permutaciones_10000/relevancia_33.csv',
          'analisis/random_forest_revision_35b_33_variables/resultados/rendimiento_modelos.csv']
r = {'archivos_antes': len(antes), 'archivos_despues': len(despues), 'cambiados': cambiados, 'faltan': faltan, 'nuevos': nuevos,
     'head_antes': head_a, 'head_despues': head_d, 'versionados_modificados': versionados,
     'claves': [{'ruta': c, 'sha256': antes[c], 'igual': antes[c] == despues[c]} for c in claves]}
(AQUI / 'tablas' / 'comparacion_manifiestos.json').write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: r[k] for k in r if k != 'claves'}, ensure_ascii=False))
sys.exit(1 if cambiados or faltan or nuevos or head_a != head_d or versionados else 0)
