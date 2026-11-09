"""
Fase 37C: asignación de nuevas participantes por la cadena E3. Los umbrales del mecanismo de incertidumbre se fijan en la submuestra y se evalúan en las no usadas. No modifica la plataforma.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/asignacion_37c.py [--procesos N]
"""
import argparse
import multiprocessing as mp
import sys
import time

import nucleo_37c as N
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

Q = N.Q
S = N.BASE / 'asignacion'
MARGENES = [0.05, 0.10, 0.15, 0.20, 0.30]
PERCENTILES = [90, 95, 99]
CAD = None


def iniciar():
    global CAD
    Q.instalar_gancho()
    CAD = N.Cadena()


def trabajo(arg):
    base, r, idx, cfgs = arg
    nombre = f'{base}_r{r:02d}'
    t0 = time.time()
    try:
        Z = CAD.matriz_nivel(base, 'E3', idx).to_numpy()
        F, _ = N.coordenadas_cadena(Z, idx)
        et = N.etiquetas_37b()
        resto = np.setdiff1d(np.arange(Q.N), idx)
        filas, grilla = [], []
        for c in cfgs:
            X = Z if c['componentes'] == 0 else F[:, :c['componentes']]
            l, _, centros = Q.ajustar(X[idx], c['algoritmo'], c['k'], Q.semilla_rep(r))
            grupos = np.unique(l)
            protos = np.vstack([X[idx][l == g].mean(axis=0) for g in grupos]) if centros is None else centros[grupos]
            as_sub, d_sub, _, m_sub = Q.asignar(protos, X[idx])
            as_res, d_res, _, m_res = Q.asignar(protos, X[resto])
            ref = et[c['config']].to_numpy()
            # La alineación solo usa la submuestra, para no contaminar la evaluación.
            mapa = N.alinear(ref[idx], grupos[as_sub])
            traduccion = {}
            for a_, b_ in zip(grupos[as_sub], mapa):
                traduccion[a_] = b_
            pred = np.array([traduccion.get(x, -1) for x in grupos[as_res]])
            error = pred != ref[resto]
            umbral_d = {p: np.array([np.percentile(d_sub[as_sub == g], p) if (as_sub == g).any() else np.inf for g in range(len(grupos))]) for p in PERCENTILES}
            filas.append({'config': c['config'], 'repeticion': r, 'ari_fuera': adjusted_rand_score(ref[resto], pred), 'desacuerdo_pct': float(100 * error.mean()), 'margen_mediano_fuera': float(np.median(m_res)), 'distancia_mediana_fuera': float(np.median(d_res)), 'distancia_mediana_sub': float(np.median(d_sub)),
                          'acuerdo_prototipo_sub_ari': adjusted_rand_score(l, as_sub)})
            for u in MARGENES:
                sen = m_res < u
                grilla.append({'config': c['config'], 'repeticion': r, 'tipo': 'margen', 'umbral': u, 'senaladas_pct': float(100 * sen.mean()), 'desacuerdo_senaladas_pct': float(100 * error[sen].mean()) if sen.any() else np.nan, 'desacuerdo_resto_pct': float(100 * error[~sen].mean()) if (~sen).any() else np.nan, 'n_senaladas': int(sen.sum())})
            for p in PERCENTILES:
                sen = d_res > umbral_d[p][as_res]
                grilla.append({'config': c['config'], 'repeticion': r, 'tipo': 'distancia_percentil', 'umbral': p, 'senaladas_pct': float(100 * sen.mean()), 'desacuerdo_senaladas_pct': float(100 * error[sen].mean()) if sen.any() else np.nan, 'desacuerdo_resto_pct': float(100 * error[~sen].mean()) if (~sen).any() else np.nan, 'n_senaladas': int(sen.sum())})
        return nombre, 'completa', time.time() - t0, Q.leidos(), filas, grilla
    except Exception as ex:  # noqa: BLE001
        return nombre, f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos(), [], []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procesos', type=int, default=10)
    a = ap.parse_args()
    N.huella_sello()
    pri = list(N.priorizadas())
    subs = Q.subconjuntos()
    trabajos = []
    for e in Q.ESPACIOS:
        cfgs = [N.info_config(c) for c in pri if N.info_config(c)['base'] == e]
        trabajos.extend((e, r, subs[r], cfgs) for r in range(len(subs)))
    t0 = time.time()
    with mp.Pool(a.procesos, initializer=iniciar) as pool:
        res = pool.map(trabajo, trabajos, chunksize=1)
    N.registrar('asignacion', [r[:4] for r in res])
    malos = [r for r in res if r[1] != 'completa']
    if malos:
        print([m[:2] for m in malos[:3]])
        return 1
    d = pd.DataFrame([x for r in res for x in r[4]])
    g = pd.DataFrame([x for r in res for x in r[5]])
    N.a_csv(d, S / 'fuera_de_muestra_por_repeticion.csv')
    N.a_csv(g, S / 'grilla_incertidumbre_por_repeticion.csv')
    res1 = d.groupby('config').agg(ari_fuera_media=('ari_fuera', 'mean'), ari_fuera_p05=('ari_fuera', lambda s: np.percentile(s, 5)), ari_fuera_min=('ari_fuera', 'min'), desacuerdo_pct_medio=('desacuerdo_pct', 'mean'), margen_mediano_fuera=('margen_mediano_fuera', 'median'), distancia_fuera=('distancia_mediana_fuera', 'median'), distancia_sub=('distancia_mediana_sub', 'median'), acuerdo_prototipo_sub=('acuerdo_prototipo_sub_ari', 'mean')).reset_index()
    t = N.tabla_37b()
    h = pd.read_csv(N.B37 / 'prototipos' / 'evaluacion_asignacion.csv').set_index('config')
    res1['acuerdo_prototipo_ari_529'] = res1['config'].map(h['acuerdo_prototipo_ari'])
    res1['acuerdo_prototipo_pct_529'] = res1['config'].map(h['acuerdo_prototipo_pct'])
    res1['margen_mediano_529'] = res1['config'].map(t['margen_mediano'])
    res1['regla'] = res1['config'].map(lambda c: 'Centroides de K-means' if '_km_' in c else 'Prototipos: aproximación, no equivale al jerárquico original')
    N.a_csv(res1, S / 'evaluacion_asignacion.csv')
    g2 = g.groupby(['config', 'tipo', 'umbral']).agg(senaladas_pct=('senaladas_pct', 'mean'), desacuerdo_senaladas_pct=('desacuerdo_senaladas_pct', 'mean'), desacuerdo_resto_pct=('desacuerdo_resto_pct', 'mean'), repeticiones_sin_senaladas=('n_senaladas', lambda s: int((s == 0).sum()))).reset_index()
    N.a_csv(g2, S / 'grilla_incertidumbre.csv')
    print('Asignación lista', round(time.time() - t0), 's')
    print(res1.sort_values('ari_fuera_media', ascending=False).head(12)[['config', 'ari_fuera_media', 'ari_fuera_p05', 'desacuerdo_pct_medio', 'margen_mediano_fuera']].round(2).to_string())
    return 0


if __name__ == '__main__':
    sys.exit(main())
