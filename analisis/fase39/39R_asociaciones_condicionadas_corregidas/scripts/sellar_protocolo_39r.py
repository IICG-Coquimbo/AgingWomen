"""
Fase 39R: sella el protocolo, las fuentes metodológicas y el código de análisis con SHA-256. Se niega si ya hay sello o si existen resultados de reglas.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/sellar_protocolo_39r.py
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
RAIZ = BASE.parents[2]
P = BASE / 'protocolo'
SELLO = P / 'sello_protocolo.json'
CODIGO = ['barreras_39r.py', 'nucleo_39r.py', 'etapa_a_preparacion.py', 'etapa_bc_reglas_nulas.py', 'etapa_d_comparacion.py', 'etapa_e_sensibilidades.py', 'etapa_e_ab1.py', 'exploratorio_significacion.py']
A = 'analisis/'
H39 = A + 'fase39/39_asociaciones_condicionadas/'
H38 = A + 'fase38/38_reglas_asociacion_generales/'
R38 = A + 'fase38/38R_reglas_asociacion_corregidas/'
FUENTES = [H39 + 'protocolo/01_protocolo_39.md', H39 + 'protocolo/02_modificaciones_posteriores.md', H39 + 'protocolo/sello_protocolo.json', R38 + 'protocolo/01_protocolo_38R.md', R38 + 'protocolo/sello_protocolo.json',
           R38 + 'informes/informe_comparativo_38R.md', R38 + 'preparacion/matriz_transaccional_principal.csv', H39 + 'scripts/nucleo_39.py', H39 + 'scripts/busqueda_39.py', H39 + 'scripts/heterogeneidad_39.py',
           H38 + 'scripts/nucleo_38.py', H38 + 'scripts/algoritmos_38.py', H38 + 'scripts/evaluacion_38.py', R38 + 'scripts/nucleo_38r.py', R38 + 'scripts/barreras_38r.py']


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


if SELLO.exists():
    raise SystemExit('Ya existe un sello: no se reemplaza.')
for carpeta in ('reglas', 'referencia_nula', 'comparacion', 'sensibilidades', 'estabilidad', 'ab1', 'resultados'):
    if (BASE / carpeta).exists() and any((BASE / carpeta).iterdir()):
        raise SystemExit(f'Ya hay resultados en {carpeta}: no se puede sellar antes de calcular.')
archivo = P / '01_protocolo_39R.md'
s = {'archivo': archivo.name, 'sha256': sha(archivo), 'bytes': archivo.stat().st_size, 'sellado': datetime.now().isoformat(timespec='seconds'), 'protocolo_historico_39_sha256': '18f15f821635f8c3d55a31f539d84d95ef8e5a32591e465073fb181a424c9042',
     'protocolo_38R_sha256': '32a64ec8d5cdd4ceec8a13f54e44abccfbda689517cf430299eaf6a4b601e867', 'fuentes': {f: sha(RAIZ / f) for f in FUENTES}, 'codigo': {c: sha(AQUI / c) for c in CODIGO}}
if sha(RAIZ / FUENTES[0]) != s['protocolo_historico_39_sha256'] or sha(RAIZ / FUENTES[3]) != s['protocolo_38R_sha256']:
    raise SystemExit('Un protocolo de origen no coincide con su huella declarada.')
SELLO.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
print({k: v for k, v in s.items() if k not in ('fuentes', 'codigo')}, len(s['fuentes']), len(s['codigo']))
