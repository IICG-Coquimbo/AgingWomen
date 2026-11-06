"""Fase 37B: sella el protocolo con SHA-256. Se niega a sellar si ya existen resultados de agrupamiento o si el sello ya existe."""
import hashlib
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RAIZ = BASE.parents[2]
protocolo = BASE / 'protocolo' / '01_protocolo_37B.md'
sello = BASE / 'protocolo' / 'sello_protocolo.json'
if sello.exists():
    raise SystemExit('El protocolo ya está sellado.')
previos = [p for d in ('resultados', 'etiquetas', 'estabilidad', 'referencia_nula', 'sensibilidades', 'prototipos') for p in (BASE / d).rglob('*') if p.is_file()]
if previos:
    raise SystemExit(f'Ya hay resultados: {previos[:3]}')
commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
sello.write_text(json.dumps({'archivo': protocolo.name, 'sha256': hashlib.sha256(protocolo.read_bytes()).hexdigest(), 'commit': commit,
                             'nota': 'Sellado antes de ajustar K-means o el método aglomerativo. La ejecución se detiene si la huella no coincide.'}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
print(sello.read_text(encoding='utf-8'))
