"""
Fase 37B: referencia nula. Por réplica: permuta las variables generales, transforma con parámetros congelados, recalcula la reducción y evalúa las 420 configuraciones.

Uso, desde analisis/: python fase37/37B_clustering/scripts/ejecutar_nula_37b.py [--replicas 0,1,...] [--procesos N] [--salida CARPETA]
Cada réplica se guarda aparte. Al reanudar, se omite la que ya esté completa.
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import nucleo_37b as Q
import pandas as pd


def trabajo(arg):
    r, salida, sello, subs = arg
    destino = Path(salida) / 'referencia_nula' / 'lotes' / f'replica_{r:02d}.csv'
    marca = destino.with_suffix('.json')
    if destino.exists() and marca.exists() and json.loads(marca.read_text(encoding='utf-8')).get('huella_protocolo') == sello:
        return f'replica_{r:02d}', 'omitida', 0.0, Q.leidos()
    t0 = time.time()
    try:
        espacios = Q.espacios_nulos(Q.tabla_general(), r)
        filas = []
        for cfg in Q.configuraciones():
            e, c, a, k = cfg['espacio'], cfg['componentes'], cfg['algoritmo'], cfg['k']
            X = espacios[e] if c == 0 else espacios[e][:, :c]
            l, ajuste, _ = Q.ajustar(X, a, k)
            cal, _ = Q.calidad(X, l)
            tam = Q.tamanos(l, k)
            filas.append({'replica': r, 'config': cfg['config'], **cal, **{x: tam[x] for x in ('tam_min', 'tam_max', 'equilibrio', 'grupos_pequenos')}, 'fraccion_eje1': Q.fraccion_eje1(X, l, espacios[cfg['base']][:, 0]), **Q.estabilidad(X, a, k, l, subs)})
        tmp = destino.with_suffix('.tmp')
        pd.DataFrame(filas).to_csv(tmp, index=False, encoding='utf-8', lineterminator='\n')
        tmp.replace(destino)
        marca.write_text(json.dumps({'replica': r, 'huella_protocolo': sello, 'configuraciones': len(filas)}) + '\n', encoding='utf-8', newline='\n')
        return f'replica_{r:02d}', 'completa', time.time() - t0, Q.leidos()
    except Exception as ex:  # noqa: BLE001
        return f'replica_{r:02d}', f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--replicas', default='')
    ap.add_argument('--procesos', type=int, default=10)
    ap.add_argument('--salida', default=str(Q.BASE))
    a = ap.parse_args()
    S = Path(a.salida).resolve()
    (S / 'referencia_nula' / 'lotes').mkdir(parents=True, exist_ok=True)
    (S / 'integridad').mkdir(parents=True, exist_ok=True)
    sello = Q.huella_sello()
    subs = Q.subconjuntos()
    replicas = [int(x) for x in a.replicas.split(',')] if a.replicas else list(range(Q.N_NULA))
    t0 = time.time()
    with mp.Pool(min(a.procesos, len(replicas)), initializer=Q.instalar_gancho) as pool:
        res = []
        for r in pool.imap_unordered(trabajo, [(x, str(S), sello, subs) for x in replicas]):
            res.append(r)
            print(r[0], r[1], f'{r[2]:.0f} s', f'total {time.time() - t0:.0f} s', flush=True)
    Q.registrar(S, 'nula', res)
    malos = [r for r in res if r[1] not in ('completa', 'omitida')]
    print('Réplicas con error:', len(malos))
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
