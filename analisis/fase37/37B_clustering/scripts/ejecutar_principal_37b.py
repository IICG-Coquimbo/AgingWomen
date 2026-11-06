"""
Fase 37B: ajusta las 420 configuraciones principales, con estabilidad. Cada configuración se guarda aparte, y al reanudar se omite la que ya esté completa y coincida con sus entradas.

Uso, desde analisis/: python fase37/37B_clustering/scripts/ejecutar_principal_37b.py [--solo TEXTO] [--procesos N] [--salida CARPETA]
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from functools import lru_cache
from pathlib import Path

import nucleo_37b as Q
import numpy as np
from sklearn.metrics import adjusted_rand_score


@lru_cache(maxsize=None)
def _entrada(e, c):
    x = Q.coordenadas(e, c)
    Q.verificar_columnas(x.columns)
    base = e[2:] if e.startswith('R0') else e
    ruta = Q.F36 / 'matrices' / f'{Q.MATRIZ[base]}.csv' if c == 0 else Q.A37 / 'coordenadas' / e / f'coordenadas_k{c:02d}.csv'
    return x.to_numpy(), Q.eje1(base).to_numpy(), Q.sha(ruta)


def trabajo(arg):
    cfg, salida, sello, subs = arg
    destino = Path(salida) / 'resultados' / 'lotes' / f'{cfg["config"]}.json'
    X, c1, huella = _entrada(cfg['espacio'], cfg['componentes'])
    if destino.exists():
        previo = json.loads(destino.read_text(encoding='utf-8'))
        if previo.get('huella_entrada') == huella and previo.get('huella_protocolo') == sello and previo.get('completa'):
            return cfg['config'], 'omitida', 0.0, Q.leidos()
    t0 = time.time()
    try:
        a, k = cfg['algoritmo'], cfg['k']
        l, ajuste, centros = Q.ajustar(X, a, k)
        protos = centros if centros is not None else Q.prototipos(X, l, k)
        cal, s = Q.calidad(X, l)
        por_grupo = [{'grupo': g, 'n': int((l == g).sum()), 'media': float(s[l == g].mean()), 'q1': float(np.percentile(s[l == g], 25)), 'mediana': float(np.median(s[l == g])), 'q3': float(np.percentile(s[l == g], 75)), 'min': float(s[l == g].min()), 'max': float(s[l == g].max()), 'negativos': float((s[l == g] < 0).mean())} for g in range(k)]
        et, d1, _, margen = Q.asignar(protos, X)
        p95 = [float(np.percentile(d1[l == g], 95)) for g in range(k)]
        est, frente, fuera = Q.estabilidad(X, a, k, l, subs, detalle=True)
        res = {**cfg, 'huella_entrada': huella, 'huella_protocolo': sello, 'completa': True, 'etiquetas': l.tolist(), **ajuste, **cal, **Q.tamanos(l, k), 'fraccion_eje1': Q.fraccion_eje1(X, l, c1),
               'silueta_por_grupo': por_grupo, 'centroides': protos.tolist(), 'acuerdo_prototipo_pct': float(100 * (et == l).mean()), 'acuerdo_prototipo_ari': float(adjusted_rand_score(l, et)),
               'margen_mediano': float(np.median(margen)), 'distancia_p95_grupo': p95, **est, 'ari_completo_rep': frente, 'ari_fuera_rep': fuera}
        if a == 'km':
            alt, aj2, _ = Q.ajustar_km(X, k, 43)
            res['ari_semilla_alterna'] = float(adjusted_rand_score(l, alt))
            res['inercia_semilla_alterna'] = aj2['inercia']
        tmp = destino.with_suffix('.tmp')
        tmp.write_text(json.dumps(res, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        tmp.replace(destino)
        return cfg['config'], 'completa', time.time() - t0, Q.leidos()
    except Exception as ex:  # noqa: BLE001
        return cfg['config'], f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--solo', default='')
    ap.add_argument('--procesos', type=int, default=10)
    ap.add_argument('--salida', default=str(Q.BASE))
    a = ap.parse_args()
    S = Path(a.salida).resolve()
    (S / 'resultados' / 'lotes').mkdir(parents=True, exist_ok=True)
    (S / 'integridad').mkdir(parents=True, exist_ok=True)
    sello = Q.huella_sello()
    subs = Q.subconjuntos()
    cfgs = [c for c in Q.configuraciones() if a.solo in c['config']]
    t0 = time.time()
    with mp.Pool(a.procesos, initializer=Q.instalar_gancho) as pool:
        res = []
        for i, r in enumerate(pool.imap_unordered(trabajo, [(c, str(S), sello, subs) for c in cfgs], chunksize=2)):
            res.append(r)
            if (i + 1) % 40 == 0:
                print(i + 1, 'de', len(cfgs), f'{time.time() - t0:.0f} s', flush=True)
    Q.registrar(S, 'principal', res)
    malos = [r for r in res if r[1] not in ('completa', 'omitida')]
    print('Completas nuevas:', sum(r[1] == 'completa' for r in res), '| omitidas:', sum(r[1] == 'omitida' for r in res), '| con error:', len(malos), f'| {time.time() - t0:.0f} s')
    for r in malos[:5]:
        print(r[:2])
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
