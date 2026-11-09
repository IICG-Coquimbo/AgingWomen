"""Fase 38: manifiesto final con la huella SHA-256 de cada archivo de la carpeta de la fase (sin los lotes reanudables ni el propio manifiesto)."""
import sys

import nucleo_38 as N
import pandas as pd

sys.dont_write_bytecode = True
B = N.BASE
salida = B / 'integridad' / 'manifiesto_final.csv'
filas = [{'archivo': p.relative_to(B).as_posix(), 'bytes': p.stat().st_size, 'sha256': N.sha(p)}
         for p in sorted(B.rglob('*')) if p.is_file() and p != salida and '__pycache__' not in p.parts]
pyc = [p for p in B.rglob('__pycache__')]
if pyc:
    raise SystemExit(f'__pycache__ presente: {pyc}')
pd.DataFrame(filas).to_csv(salida, index=False, encoding='utf-8')
print(len(filas), 'archivos en el manifiesto')
