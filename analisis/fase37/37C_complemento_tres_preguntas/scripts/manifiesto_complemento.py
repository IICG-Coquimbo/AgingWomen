"""
Complemento de la Fase 37C: escribe integridad/manifiesto_final.csv con la huella de todos los archivos de la carpeta, salvo el propio manifiesto.

Uso, desde analisis/: python fase37/37C_complemento_tres_preguntas/scripts/manifiesto_complemento.py
"""
import csv
import hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SALIDA = BASE / 'integridad' / 'manifiesto_final.csv'
archivos = sorted(p for p in BASE.rglob('*') if p.is_file() and p != SALIDA and '__pycache__' not in p.parts)
with SALIDA.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['ruta', 'sha256', 'bytes'])
    for p in archivos:
        w.writerow([p.relative_to(BASE).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size])
print(len(archivos), 'archivos en el manifiesto')
