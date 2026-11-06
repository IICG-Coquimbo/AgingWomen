"""
Fase 37D: sella el protocolo con su huella SHA-256 y la hora. Se ejecuta una sola vez, antes de calcular asociaciones con el MRS. No sobrescribe un sello existente.

Uso, desde analisis/: python fase37/37D_caracterizacion/scripts/sellar_protocolo_37d.py [archivo] [nombre_sello]
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'protocolo'
archivo = sys.argv[1] if len(sys.argv) > 1 else '01_protocolo_37D.md'
sello = P / (sys.argv[2] if len(sys.argv) > 2 else 'sello_protocolo.json')
if sello.exists():
    raise SystemExit(f'{sello.name} ya existe; no se sobrescribe.')
h = hashlib.sha256((P / archivo).read_bytes()).hexdigest()
sello.write_text(json.dumps({'archivo': archivo, 'sha256': h, 'sellado': datetime.now().isoformat(timespec='seconds'),
                             'nota': 'Sellado antes de calcular asociaciones entre características o segmentos y el MRS.'}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
print(archivo, h)
