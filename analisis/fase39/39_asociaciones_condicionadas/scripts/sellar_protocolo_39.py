"""Fase 39: sella un archivo del protocolo con SHA-256. No sobrescribe un sello existente.

Uso: python sellar_protocolo_39.py [archivo] [nombre_sello]
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
P = Path(__file__).resolve().parents[1] / 'protocolo'
archivo = sys.argv[1] if len(sys.argv) > 1 else '01_protocolo_39.md'
nombre = sys.argv[2] if len(sys.argv) > 2 else 'sello_protocolo.json'
destino = P / nombre
if destino.exists():
    raise SystemExit(f'El sello {nombre} ya existe; no se sobrescribe.')
datos = (P / archivo).read_bytes()
s = {'archivo': archivo, 'sha256': hashlib.sha256(datos).hexdigest(), 'bytes': len(datos), 'sellado': datetime.now().isoformat(timespec='seconds')}
destino.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
print(s)
