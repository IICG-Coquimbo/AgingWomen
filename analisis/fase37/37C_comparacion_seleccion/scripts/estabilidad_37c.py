"""
Fase 37C: estabilidad con reducción reajustada (E1), con escalado recalibrado (E2) y con imputación reestimada (E3).

Cada trabajo es (escenario, nivel, repetición). Solo las filas de la submuestra ajustan parámetros, reducción y agrupamiento; las demás pasan por esa cadena.
Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/estabilidad_37c.py [--procesos N] [--salida CARPETA] [--configs A,B] [--reps N]
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import nucleo_37c as N
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

Q = N.Q
CAD = None


def iniciar():
    global CAD
    Q.instalar_gancho()
    CAD = N.Cadena()


def ajustar_config(coords, Z, idx, cfg, r):
    """Agrupa con las filas de la submuestra y asigna a las 529. Las de la submuestra conservan la etiqueta del algoritmo."""
    X = Z if cfg['componentes'] == 0 else coords[:, :cfg['componentes']]
    l, _, centros = Q.ajustar(X[idx], cfg['algoritmo'], cfg['k'], Q.semilla_rep(r))
    grupos = np.unique(l)
    protos = np.vstack([X[idx][l == g].mean(axis=0) for g in grupos]) if centros is None else centros[grupos]
    et, d1, d2, margen = Q.asignar(protos, X)
    salida = grupos[et]
    salida[idx] = l
    return salida.astype(np.int8), margen, d1


def trabajo(arg):
    base, nivel, r, idx, cfgs, salida, sello = arg
    nombre = f'{base}_{nivel}_r{r:02d}'
    destino = Path(salida) / 'estabilidad' / 'lotes' / f'{nombre}.npz'
    marca = destino.with_suffix('.json')
    if destino.exists() and marca.exists() and N.leer_json(marca).get('huella_protocolo') == sello:
        return nombre, 'omitida', 0.0, Q.leidos()
    t0 = time.time()
    try:
        Z = CAD.matriz_nivel(base, nivel, idx).to_numpy()
        coords, modelo = N.coordenadas_cadena(Z, idx)
        etiquetas = {}
        for c in cfgs:
            etiquetas[c['config']] = ajustar_config(coords, Z, idx, c, r)[0]
        sim = []
        hist = Q.coordenadas(base, 20).to_numpy()
        for c in Q.COMPONENTES:
            sim.append(N.R.similitud_subespacio(hist[idx][:, :c], coords[idx][:, :c]))
        lam = np.array(modelo['valores_propios'])
        info = {'huella_protocolo': sello, 'trabajo': nombre, 'similitud': sim, 'pct_eje1': float(100 * lam[0] / lam.sum()), 'pct_eje2': float(100 * lam[1] / lam.sum())}
        if nivel == 'E3':
            info['imputaciones'] = CAD.tabla_imputada(idx)[1]
        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_name(destino.stem + '_tmp.npz')
        np.savez_compressed(tmp, **etiquetas)
        tmp.replace(destino)
        marca.write_text(json.dumps(info, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        return nombre, 'completa', time.time() - t0, Q.leidos()
    except Exception as ex:  # noqa: BLE001
        return nombre, f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos()


def consolidar(S, configs, subs):
    """Calcula los ARI por configuración y nivel desde las etiquetas guardadas."""
    et37 = N.etiquetas_37b()
    filas, por_rep, tam = [], [], []
    usadas = np.zeros((len(subs), N.Q.N), bool)
    for r, idx in enumerate(subs):
        usadas[r, idx] = True
    for nivel in N.NIVELES:
        cargas = {}
        for c in configs:
            base = N.info_config(c)['base']
            if base not in cargas:
                cargas[base] = [np.load(S / 'estabilidad' / 'lotes' / f'{base}_{nivel}_r{r:02d}.npz') for r in range(len(subs))]
            todas = np.vstack([cargas[base][r][c] for r in range(len(subs))])
            ref = et37[c].to_numpy()
            frente = [adjusted_rand_score(ref[usadas[r]], todas[r][usadas[r]]) for r in range(len(subs))]
            fuera = [adjusted_rand_score(ref[~usadas[r]], todas[r][~usadas[r]]) for r in range(len(subs))]
            entre = N.ari_pares_compartidos(todas, usadas)
            fp = N.ari_pares_fuera(todas, usadas)
            k = N.info_config(c)['k']
            minimos = [np.bincount(todas[r][usadas[r]], minlength=k).min() for r in range(len(subs))]
            filas.append({'config': c, 'nivel': nivel, **Q.resumir(frente, 'ari_completo'), **Q.resumir(entre, 'ari_entre'), **Q.resumir(fuera, 'ari_fuera'), **Q.resumir(fp, 'ari_fuera_pares'),
                          'tam_min_rep_min': int(min(minimos)), 'tam_min_rep_mediana': float(np.median(minimos)), 'rep_grupo_bajo_5pct': int(sum(m < np.ceil(0.05 * Q.N_SUB) for m in minimos))})
            for r in range(len(subs)):
                por_rep.append({'config': c, 'nivel': nivel, 'repeticion': r, 'ari_completo': frente[r], 'ari_fuera': fuera[r]})
                tam.append({'config': c, 'nivel': nivel, 'repeticion': r, 'tamanos_submuestra': ' '.join(map(str, np.bincount(todas[r][usadas[r]], minlength=k)))})
    res = pd.DataFrame(filas)
    N.a_csv(res, S / 'estabilidad' / 'estabilidad_por_nivel.csv')
    N.a_csv(pd.DataFrame(por_rep), S / 'estabilidad' / 'ari_por_repeticion.csv')
    N.a_csv(pd.DataFrame(tam), S / 'estabilidad' / 'tamanos_por_repeticion.csv')
    # Metadatos de cada repetición
    sim, imp = [], []
    for base in Q.ESPACIOS:
        for nivel in N.NIVELES:
            for r in range(len(subs)):
                m = N.leer_json(S / 'estabilidad' / 'lotes' / f'{base}_{nivel}_r{r:02d}.json')
                for c, s in zip(Q.COMPONENTES, m['similitud']):
                    sim.append({'base': base, 'nivel': nivel, 'repeticion': r, 'componentes': c, 'similitud_subespacio': s, 'pct_eje1': m['pct_eje1'], 'pct_eje2': m['pct_eje2']})
                if nivel == 'E3' and base == 'P1':
                    for v, x in m['imputaciones'].items():
                        imp.append({'repeticion': r, 'variable': v, 'valor_reestimado': x})
    N.a_csv(pd.DataFrame(sim), S / 'estabilidad' / 'similitud_reduccion.csv')
    imp = pd.DataFrame(imp)
    N.a_csv(imp, S / 'estabilidad' / 'imputaciones_reestimadas.csv')
    # Comparación con E0 (tabla de la Fase 37B)
    t = N.tabla_37b()
    comp = []
    for c in configs:
        fila = {'config': c, **N.info_config(c), 'en_lista_a': bool(t.loc[c, 'lista_37C'])}
        fila.update({'E0_entre_media': t.loc[c, 'ari_entre_media'], 'E0_entre_p05': t.loc[c, 'ari_entre_p05'], 'E0_entre_min': t.loc[c, 'ari_entre_min'], 'E0_completo_media': t.loc[c, 'ari_completo_media'], 'E0_fuera_media': t.loc[c, 'ari_fuera_media'], 'E0_fuera_p05': t.loc[c, 'ari_fuera_p05']})
        for nivel in N.NIVELES:
            x = res[(res['config'] == c) & (res['nivel'] == nivel)].iloc[0]
            for m in ('ari_entre_media', 'ari_entre_mediana', 'ari_entre_p05', 'ari_entre_min', 'ari_completo_media', 'ari_fuera_media', 'ari_fuera_p05', 'ari_fuera_pares_media'):
                fila[f'{nivel}_{m[4:]}'] = x[m]
        comp.append(fila)
    N.a_csv(pd.DataFrame(comp), S / 'estabilidad' / 'comparacion_niveles.csv')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procesos', type=int, default=10)
    ap.add_argument('--salida', default=str(N.BASE))
    ap.add_argument('--configs', default='')
    ap.add_argument('--reps', type=int, default=Q.N_REP)
    a = ap.parse_args()
    S = Path(a.salida).resolve()
    sello = N.huella_sello()
    configs = a.configs.split(',') if a.configs else pd.read_csv(N.BASE / 'candidatos' / 'conjunto_estabilidad.csv')['config'].tolist()
    subs = Q.subconjuntos()[:a.reps]
    por_base = {e: [N.info_config(c) for c in configs if N.info_config(c)['base'] == e] for e in Q.ESPACIOS}
    trabajos = [(e, nivel, r, subs[r], por_base[e], str(S), sello) for e in Q.ESPACIOS for nivel in N.NIVELES for r in range(len(subs))]
    t0 = time.time()
    with mp.Pool(a.procesos, initializer=iniciar) as pool:
        res = list(pool.imap_unordered(trabajo, trabajos, chunksize=1))
    if S == N.BASE:
        N.registrar('estabilidad', res)
    malos = [r for r in res if r[1] not in ('completa', 'omitida')]
    print('Trabajos:', len(res), '| nuevos:', sum(r[1] == 'completa' for r in res), '| con error:', len(malos), f'| {time.time() - t0:.0f} s')
    for r in malos[:5]:
        print(r[:2])
    if malos:
        return 1
    consolidar(S, configs, subs)
    return 0


if __name__ == '__main__':
    sys.exit(main())
