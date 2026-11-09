"""
Fase 37B: sensibilidades. Ajusta las 34 variantes de la Fase 37A con cada combinación de componentes, algoritmo y k, y las compara con la configuración base por ARI.

Ajuste y proyección se mantienen separados. Solo se comparan participantes presentes en ambas.
Requiere las etiquetas principales. Uso, desde analisis/: python fase37/37B_clustering/scripts/ejecutar_sensibilidades_37b.py [--procesos N] [--salida CARPETA]
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import nucleo_37b as Q
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score


def trabajo(arg):
    carpeta, salida, sello = arg
    sid, e = Path(carpeta).parent.name, Path(carpeta).name
    destino = Path(salida) / 'sensibilidades' / 'lotes' / f'{sid}_{e}.csv'
    marca = destino.with_suffix('.json')
    nombre = f'{sid}_{e}'
    if destino.exists() and marca.exists() and json.loads(marca.read_text(encoding='utf-8')).get('huella_protocolo') == sello:
        return nombre, 'omitida', 0.0, Q.leidos()
    t0 = time.time()
    try:
        aj = pd.read_csv(Path(carpeta) / 'coordenadas_ajuste.csv', dtype={'participante_id': str}).set_index('participante_id')
        ruta_pr = Path(carpeta) / 'coordenadas_proyeccion.csv'
        pr = pd.read_csv(ruta_pr, dtype={'participante_id': str}).set_index('participante_id') if ruta_pr.exists() else None
        if pr is not None and set(aj.index) & set(pr.index):
            raise ValueError('Una participante aparece en ajuste y en proyección')
        umbral = int(np.ceil(0.05 * len(aj)))
        filas, etiquetas = [], {'participante_id': list(aj.index) + (list(pr.index) if pr is not None else []), 'rol': ['ajuste'] * len(aj) + (['proyeccion'] * len(pr) if pr is not None else [])}
        for c in Q.COMPONENTES:
            cols = [f'C{i + 1}' for i in range(c)]
            X = aj[cols].to_numpy()
            for a in Q.ALGORITMOS:
                for k in Q.CLUSTERES:
                    cfg = f'{e}_c{c:02d}_{a}_k{k}'
                    base = json.loads((Path(salida) / 'resultados' / 'lotes' / f'{cfg}.json').read_text(encoding='utf-8'))
                    lb = pd.Series(base['etiquetas'], index=Q.identificadores())
                    l, ajuste, centros = Q.ajustar(X, a, k)
                    protos = centros if centros is not None else Q.prototipos(X, l, k)
                    cal, _ = Q.calidad(X, l)
                    tam = Q.tamanos(l, k, umbral)
                    fila = {'sensibilidad': sid, 'familia': Q.FAMILIA[sid], 'base': e, 'componentes': c, 'algoritmo': a, 'k': k, 'config_base': cfg, 'filas_ajuste': len(aj), 'filas_proyeccion': 0 if pr is None else len(pr),
                            'ari_ajuste': float(adjusted_rand_score(lb.loc[aj.index].to_numpy(), l)), 'ari_proyeccion': np.nan, 'silueta': cal['silueta'], 'tam_min': tam['tam_min'], 'tam_max': tam['tam_max'], 'grupos_pequenos': tam['grupos_pequenos'], 'equilibrio': tam['equilibrio'],
                            'tam_min_base': base['tam_min'], 'grupos_pequenos_base': base['grupos_pequenos'], 'tamanos': ' '.join(map(str, tam['tamanos']))}
                    lp = []
                    if pr is not None:
                        lp = Q.asignar(protos, pr[cols].to_numpy())[0]
                        fila['ari_proyeccion'] = float(adjusted_rand_score(lb.loc[pr.index].to_numpy(), lp))
                        lp = lp.tolist()
                    filas.append(fila)
                    etiquetas[cfg] = l.tolist() + lp
        (Path(salida) / 'sensibilidades' / 'etiquetas').mkdir(parents=True, exist_ok=True)
        pd.DataFrame(etiquetas).to_csv(Path(salida) / 'sensibilidades' / 'etiquetas' / f'{nombre}.csv', index=False, encoding='utf-8', lineterminator='\n')
        tmp = destino.with_suffix('.tmp')
        pd.DataFrame(filas).to_csv(tmp, index=False, encoding='utf-8', lineterminator='\n')
        tmp.replace(destino)
        marca.write_text(json.dumps({'variante': nombre, 'huella_protocolo': sello, 'ajustes': len(filas)}) + '\n', encoding='utf-8', newline='\n')
        return nombre, 'completa', time.time() - t0, Q.leidos()
    except Exception as ex:  # noqa: BLE001
        return nombre, f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procesos', type=int, default=10)
    ap.add_argument('--salida', default=str(Q.BASE))
    a = ap.parse_args()
    S = Path(a.salida).resolve()
    (S / 'sensibilidades' / 'lotes').mkdir(parents=True, exist_ok=True)
    sello = Q.huella_sello()
    variantes = sorted(str(p.parent) for p in (Q.A37 / 'sensibilidades').glob('*/*/modelo.json'))
    t0 = time.time()
    with mp.Pool(a.procesos, initializer=Q.instalar_gancho) as pool:
        res = list(pool.imap_unordered(trabajo, [(v, str(S), sello) for v in variantes]))
    Q.registrar(S, 'sensibilidades', res)
    malos = [r for r in res if r[1] not in ('completa', 'omitida')]
    print('Variantes:', len(res), '| completas nuevas:', sum(r[1] == 'completa' for r in res), '| con error:', len(malos), f'| {time.time() - t0:.0f} s')
    for r in malos[:5]:
        print(r[:2])
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
