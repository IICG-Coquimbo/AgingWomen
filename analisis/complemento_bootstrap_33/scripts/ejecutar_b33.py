"""Ejecuta los 500 remuestreos en un solo proceso. Reanudable: cada remuestreo queda en remuestreos/cache/rem_XXXX.json.

Uso, desde analisis/complemento_bootstrap_33/scripts:
    python ejecutar_b33.py
Se detiene de forma segura si la memoria libre baja de 400 MB.
"""
import json
import sys
import time
from datetime import datetime

import psutil

import nucleo_b33 as N

MEMORIA_MINIMA_MB = 400


def main():
    _, _, esc = N.cargar()
    N.CACHE.mkdir(parents=True, exist_ok=True)
    registro = N.BASE / 'remuestreos' / 'progreso.log'
    inicio = time.perf_counter()
    minimo = psutil.virtual_memory().available / 2 ** 20
    with open(registro, 'a', encoding='utf-8') as log:
        log.write(f'{datetime.now():%Y-%m-%d %H:%M:%S} inicio; memoria libre {minimo:.0f} MB\n')
        for i in range(N.N_REMUESTREOS):
            ya = (N.CACHE / f'rem_{i:04d}.json').exists()
            t0 = time.perf_counter()
            r = N.un_remuestreo(esc, i, N.N_PERMUTACIONES, N.CACHE)
            libre = psutil.virtual_memory().available / 2 ** 20
            minimo = min(minimo, libre)
            log.write(f'{datetime.now():%H:%M:%S} rem {i:03d} {"cache" if ya else f"{time.perf_counter() - t0:.1f}s"} '
                      f'relevantes {len(r["relevantes"])} pares {r["n_pares"]} libre {libre:.0f} MB\n')
            log.flush()
            if libre < MEMORIA_MINIMA_MB:
                log.write('Detenido: memoria libre insuficiente. Se puede reanudar.\n')
                sys.exit(2)
        total = time.perf_counter() - inicio
        log.write(f'{datetime.now():%Y-%m-%d %H:%M:%S} fin; {total:.1f} s; memoria libre mínima {minimo:.0f} MB\n')
    (N.BASE / 'remuestreos' / 'ejecucion.json').write_text(json.dumps(
        {'fin': datetime.now().isoformat(timespec='seconds'), 'segundos_esta_sesion': round(total, 1),
         'memoria_libre_minima_mb': round(minimo), 'procesos': 1, 'remuestreos': N.N_REMUESTREOS,
         'permutaciones': N.N_PERMUTACIONES, 'alfa': N.ALFA, 'id_analisis': N.ID_ANALISIS}, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
