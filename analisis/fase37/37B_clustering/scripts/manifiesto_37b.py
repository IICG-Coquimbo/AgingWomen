"""
Fase 37B: escribe integridad/manifiesto_final_37B.csv con la huella de todos los archivos de la subfase, salvo el propio manifiesto.

Uso, desde analisis/: python fase37/37B_clustering/scripts/manifiesto_37b.py
"""
import csv
import hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SALIDA = BASE / 'integridad' / 'manifiesto_final_37B.csv'
archivos = sorted(p for p in BASE.rglob('*') if p.is_file() and p != SALIDA and '__pycache__' not in p.parts)
with SALIDA.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['ruta', 'sha256', 'bytes'])
    for p in archivos:
        w.writerow([p.relative_to(BASE).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size])
print(len(archivos), 'archivos en el manifiesto')
