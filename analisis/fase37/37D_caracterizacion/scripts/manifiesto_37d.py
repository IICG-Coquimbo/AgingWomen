"""Fase 37D: manifiesto final con la huella de todos los archivos de la carpeta, salvo el propio manifiesto."""
import sys

import nucleo_37d as N
import pandas as pd

sys.dont_write_bytecode = True
salida = N.BASE / 'integridad' / 'manifiesto_final.csv'
filas = [{'archivo': p.relative_to(N.BASE).as_posix(), 'bytes': p.stat().st_size, 'sha256': N.sha(p)}
         for p in sorted(N.BASE.rglob('*')) if p.is_file() and p != salida and '__pycache__' not in p.parts]
pd.DataFrame(filas).to_csv(salida, index=False, encoding='utf-8')
print(len(filas), 'archivos en el manifiesto;', 'pycache:', len(list(N.BASE.rglob('__pycache__'))))
