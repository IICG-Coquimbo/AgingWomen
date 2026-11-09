"""
Complemento de la Fase 37C: comprobación posterior al sellado. A sin la variable evaluada (A−v), en las mismas 30 repeticiones. Ver protocolo/02_nota_posterior_sin_variable.md.

Uso, desde analisis/: python fase37/37C_complemento_tres_preguntas/scripts/posterior_sin_variable.py [--procesos 2]
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import sys
import time

import nucleo_complemento as C
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

N, Q = C.N, C.Q
B = C.BASE
CAD, OBJ = None, None


def iniciar():
    global CAD, OBJ
    Q.instalar_gancho()
    CAD = N.Cadena()
    OBJ = C.objetivos(CAD)


def sin_variable(Z, columnas, v, idx, semilla):
    quitar = set(C.columnas_de([v], columnas))
    if not quitar:
        raise ValueError(f'{v} no tiene columnas en P2')
    usar = [i for i in range(Z.shape[1]) if i not in quitar]
    F, _ = N.coordenadas_cadena(Z[:, usar], idx)
    X = F[:, :12]
    l, _, centros = Q.ajustar_km(X[idx], C.K, semilla)
    et = Q.asignar(centros, X)[0]
    et[idx] = l
    return et.astype(int)


def trabajo(arg):
    r, idx = arg
    t0 = time.time()
    try:
        resto = np.setdiff1d(np.arange(Q.N), idx)
        semilla = Q.semilla_rep(r)
        tabla, _ = CAD.tabla_imputada(idx)
        Zd = CAD.calibrada(C.ESPACIO, tabla, idx)
        columnas, Z = list(Zd.columns), Zd.to_numpy()
        lote = np.load(B / 'fuera_de_muestra' / 'lotes' / f'r{r:02d}.npz')
        Ar, cod = lote['A'].astype(int), lote['celdas'].astype(int)
        Dc = C.indicadores(cod)
        filas = []
        for v, b in C.BLOQUE_DE.items():
            lv = sin_variable(Z, columnas, v, idx, semilla)
            Da = C.indicadores(lv)
            o = OBJ[v]
            r_c = C.r2_fuera(Dc, o['Y'], o['marca'], idx, resto)
            filas.append({'repeticion': r, 'variable': v, 'bloque': b, 'ari_A_v_con_A_r': adjusted_rand_score(Ar, lv), 'r2_A_v': C.r2_fuera(Da, o['Y'], o['marca'], idx, resto), 'r2_celdas': r_c, 'r2_celdas_A_v': C.r2_fuera(np.hstack([Dc, Da]), o['Y'], o['marca'], idx, resto)})
        return f'r{r:02d}', 'completa', time.time() - t0, Q.leidos(), filas
    except Exception as ex:  # noqa: BLE001
        return f'r{r:02d}', f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos(), []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procesos', type=int, default=2)
    a = ap.parse_args()
    if a.procesos > 2:
        raise SystemExit('El protocolo limita a 2 procesos.')
    C.huella()
    nota = B / 'protocolo' / '02_nota_posterior_sin_variable.md'
    sello = B / 'protocolo' / 'sello_nota_posterior.json'
    h = hashlib.sha256(nota.read_bytes()).hexdigest()
    if sello.exists():
        if json.loads(sello.read_text(encoding='utf-8'))['sha256'] != h:
            raise SystemExit('La nota posterior no coincide con su sello.')
    else:
        sello.write_text(json.dumps({'archivo': nota.name, 'sha256': h, 'nota': 'Sellada después de ver los primeros resultados por bloque y antes de calcular A sin la variable.'}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    subs = Q.subconjuntos()
    with mp.Pool(a.procesos, initializer=iniciar) as pool:
        res = pool.map(trabajo, list(enumerate(subs)), chunksize=1)
    C.registrar('posterior_sin_variable', [x[:4] for x in res])
    malos = [x for x in res if x[1] != 'completa']
    if malos:
        print([m[:2] for m in malos[:3]])
        return 1
    d = pd.DataFrame([f for x in res for f in x[4]])
    d['dr2_A_v_sobre_celdas'] = d['r2_celdas_A_v'] - d['r2_celdas']
    N.a_csv(d, B / 'informacion' / 'posterior_A_sin_variable_por_repeticion.csv')
    v = d.groupby(['bloque', 'variable'])[['ari_A_v_con_A_r', 'r2_A_v', 'r2_celdas', 'dr2_A_v_sobre_celdas']].mean().reset_index()
    v['dr2_p05'] = v.apply(lambda f: float(np.percentile(d[d['variable'] == f['variable']]['dr2_A_v_sobre_celdas'], 5)), axis=1)
    N.a_csv(v, B / 'informacion' / 'posterior_A_sin_variable.csv')
    br = d.groupby(['repeticion', 'bloque'])[['ari_A_v_con_A_r', 'r2_A_v', 'r2_celdas', 'dr2_A_v_sobre_celdas']].mean().reset_index()
    bb = br.groupby('bloque').agg(ari_media=('ari_A_v_con_A_r', 'mean'), r2_A_v=('r2_A_v', 'mean'), r2_celdas=('r2_celdas', 'mean'), dr2_media=('dr2_A_v_sobre_celdas', 'mean'), dr2_p05=('dr2_A_v_sobre_celdas', lambda s: float(np.percentile(s, 5)))).reset_index()
    N.a_csv(bb, B / 'informacion' / 'posterior_A_sin_variable_bloque.csv')
    pd.set_option('display.width', 200, 'display.max_rows', 60)
    print(bb.round(3).to_string())
    print(v.round(3).to_string())
    return 0


if __name__ == '__main__':
    sys.exit(main())
