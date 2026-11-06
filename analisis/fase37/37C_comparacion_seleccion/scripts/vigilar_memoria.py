"""
Fase 37C: ejecuta una etapa vigilando la memoria libre. Fija un hilo por biblioteca numérica. Si la memoria libre baja del límite en dos lecturas seguidas, detiene
la etapa con su árbol de procesos y termina con código 75. Los lotes ya guardados se conservan y se omiten al reanudar.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/vigilar_memoria.py ETIQUETA [--limite-gb 0.7] -- comando...
"""
import csv
import ctypes
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REGISTRO = Path(__file__).resolve().parents[1] / 'integridad' / 'registro_memoria.csv'
HILOS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')


class Estado(ctypes.Structure):
    _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong), ('total', ctypes.c_ulonglong), ('libre', ctypes.c_ulonglong), ('pt', ctypes.c_ulonglong), ('pl', ctypes.c_ulonglong), ('vt', ctypes.c_ulonglong), ('vl', ctypes.c_ulonglong), ('ve', ctypes.c_ulonglong)]


def libre_gb():
    e = Estado()
    e.dwLength = ctypes.sizeof(Estado)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(e))
    return e.libre / 2 ** 30


def anotar(etiqueta, evento, libre):
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not REGISTRO.exists()
    with REGISTRO.open('a', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        if nuevo:
            w.writerow(['momento', 'etapa', 'evento', 'libre_gb'])
        w.writerow([datetime.now().isoformat(timespec='seconds'), etiqueta, evento, f'{libre:.2f}'])


def main():
    args = sys.argv[1:]
    corte = args.index('--')
    previo, comando = args[:corte], args[corte + 1:]
    etiqueta = previo[0]
    limite = float(previo[previo.index('--limite-gb') + 1]) if '--limite-gb' in previo else 0.7
    entorno = {**os.environ, **{h: '1' for h in HILOS}, 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'}
    inicio = libre_gb()
    anotar(etiqueta, 'inicio', inicio)
    if inicio < limite:
        anotar(etiqueta, 'no iniciada: memoria insuficiente', inicio)
        print(f'No se inicia {etiqueta}: {inicio:.2f} GB libres, límite {limite} GB')
        return 75
    p = subprocess.Popen(comando, env=entorno)
    minimo, bajas, t0, ultimo = inicio, 0, time.time(), time.time()
    while p.poll() is None:
        time.sleep(5)
        x = libre_gb()
        minimo = min(minimo, x)
        bajas = bajas + 1 if x < limite else 0
        if time.time() - ultimo >= 120:
            anotar(etiqueta, 'lectura', x)
            ultimo = time.time()
        if bajas >= 2:
            subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True)
            p.wait()
            anotar(etiqueta, 'detenida por memoria', x)
            print(f'Detenida {etiqueta}: {x:.2f} GB libres. Los lotes guardados se conservan.')
            return 75
    anotar(etiqueta, f'fin, código {p.returncode}, mínimo libre', minimo)
    print(f'{etiqueta}: código {p.returncode}, {time.time() - t0:.0f} s, mínimo libre {minimo:.2f} GB')
    return p.returncode


if __name__ == '__main__':
    sys.exit(main())
