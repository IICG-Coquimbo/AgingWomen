"""Fase 39: manifiesto final con la huella SHA-256 de cada archivo de la carpeta de la fase (sin el propio manifiesto)."""
import sys

import nucleo_39 as N
import pandas as pd

sys.dont_write_bytecode = True
B = N.BASE
salida = B / 'integridad' / 'manifiesto_final.csv'
pyc = list(B.rglob('__pycache__')) + list(N.D38.rglob('__pycache__')) + list((N.ANALISIS / 'fase37' / '37D_caracterizacion').rglob('__pycache__'))
if pyc:
    raise SystemExit(f'__pycache__ presente: {pyc}')
filas = [{'archivo': p.relative_to(B).as_posix(), 'bytes': p.stat().st_size, 'sha256': N.sha(p)} for p in sorted(B.rglob('*')) if p.is_file() and p != salida]
pd.DataFrame(filas).to_csv(salida, index=False, encoding='utf-8')
print(len(filas), 'archivos en el manifiesto')
