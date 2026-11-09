"""
Fase 37A: sella el protocolo D-13 antes de cualquier ajuste. Se ejecuta una sola vez.

Uso, desde analisis/: python fase37/37A_reduccion/protocolo/sellar_protocolo.py
Se detiene si el sello ya existe o si ya hay resultados, para no sellar a posteriori.
"""
import hashlib
import json
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SELLO = AQUI / 'sello_protocolo.json'
BASE = AQUI.parent

if SELLO.exists():
    raise SystemExit('El protocolo ya está sellado.')
if any((BASE / d).exists() for d in ('tablas', 'coordenadas', 'artefactos', 'sensibilidades', 'figuras')):
    raise SystemExit('Ya existen resultados: no se puede sellar a posteriori.')
PROTOCOLO = AQUI / '01_protocolo_D13.md'
commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, cwd=AQUI).stdout.strip()
SELLO.write_text(json.dumps({'archivo': PROTOCOLO.name, 'sha256': hashlib.sha256(PROTOCOLO.read_bytes()).hexdigest(), 'mtime_protocolo': PROTOCOLO.stat().st_mtime,
                             'commit': commit, 'nota': 'Sellado antes de ajustar PCA o FAMD. El pipeline se detiene si la huella no coincide.'}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
print('Protocolo sellado:', json.loads(SELLO.read_text(encoding='utf-8'))['sha256'])
