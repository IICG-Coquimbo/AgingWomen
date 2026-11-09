"""
Fase 39: búsqueda de reglas dentro de un estrato con el procedimiento verificado de la Fase 38 (FP-Growth, redundancia, Westfall-Young), estabilidad con
umbrales proporcionales al estrato, clasificación de la sección 13 y ajuste conjunto entre estratos.
"""
import math
import sys
import time

import nucleo_39 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
G, EV = N.G, N.EV38


def buscar(c, carpeta, semilla, n_perm=N.N_PERM):
    """Reglas del estrato con su referencia nula propia (permutación de la severidad solo dentro del estrato)."""
    t0 = time.time()
    if c.largo == 0:
        return pd.DataFrame(), None, {'reglas': 0, 'busqueda': 'solo descripción'}, None, None
    frec = EV.descubrir(c)
    det = N.N38.pares_determinados(c.T)
    R = EV.reglas_de(c, frec, det)
    nula, n_ants = EV.referencia_nula(c, frec, det, carpeta, n_perm=n_perm, semilla=semilla)
    if len(R):
        R = EV.ajustar(R, nula).rename(columns={'p_ajustado_busqueda': 'p_ajustado_estrato', 'supera_nula': 'supera_nula_estrato'})
        R['q_bh_estrato'] = R.pop('q_bh_todas')
        R['proxima_a_sintomas'] = R['variables'].apply(lambda v: any(x in v.split(' & ') for x in N.N38.PROXIMAS))
        R['incluye_modulo'] = R['variables'].apply(lambda v: any(x in v for x in ('lugar_trabajo_comprensivo', 'estres_entorno_laboral', 'sobrecarga_fisica_emocional')))
    marc = int(R['marcada'].sum()) if len(R) else 0
    meta = {'n': c.n, 'n_si': c.n_si, 'frecuencia_basal_si': c.n_si / c.n, 'items': c.T.shape[1], 'largo_maximo': c.largo, 'umbral_antecedente': c.min_ant,
            'umbral_conjunto': c.min_conj, 'pares_determinados': len(det), 'antecedentes_evaluados': n_ants, 'reglas': len(R), 'marcadas': marc,
            'nula_media_marcadas': float(nula['reglas_marcadas'].mean()), 'nula_p95_marcadas': float(nula['reglas_marcadas'].quantile(0.95)),
            'p_exceso_marcadas': float(((nula['reglas_marcadas'] >= marc).sum() + 1) / (len(nula) + 1)), 'nula_p95_max_z': float(nula['max_z'].quantile(0.95)),
            'supera_nula_estrato': int(R['supera_nula_estrato'].sum()) if len(R) else 0, 'segundos': round(time.time() - t0, 1)}
    return R, nula, meta, frec, det


def estabilidad(c, frec, det, R, carpeta, semilla, n_sub=N.N_SUB, frac=N.FRAC_SUB):
    """Submuestras del 80 % del estrato con umbrales ⌈0,8·mínimos⌉; reaparición marcada y dirección de cada regla."""
    m = int(round(frac * c.n))
    a_sub, b_sub = math.ceil(round(frac * c.min_ant, 9)), math.ceil(round(frac * c.min_conj, 9))
    ants = list(G.antecedentes(frec, a_sub, det))
    idx = {s: i for i, s in enumerate(ants)}
    A = G.matriz_antecedentes(c.T, ants)
    archivo = carpeta / 'submuestras.npz'
    rng = np.random.default_rng(semilla)
    S = np.zeros((c.n, n_sub), np.uint8)
    for j in range(n_sub):
        S[rng.choice(c.n, m, replace=False), j] = 1
    nA = G.contar(A, S)
    k = G.contar(A, S * c.y[:, None])
    n_si = (S * c.y[:, None]).sum(axis=0)
    p0 = n_si / m
    with np.errstate(divide='ignore', invalid='ignore'):
        cs = k / nA
    si = cs >= p0
    kk = np.where(si, k, nA - k)
    marc = (nA >= a_sub) & (kk >= b_sub) & (np.abs(cs - p0) >= N.DIF_MARCADA)
    carpeta.mkdir(parents=True, exist_ok=True)
    np.savez(archivo, marcadas_por_submuestra=marc.sum(axis=0), n_si=n_si)
    filas = []
    for items, cons in zip(R['items'], R['consecuente']):
        i = idx[frozenset(items)]
        d = si[i] if cons == N.CONSECUENTES[0] else ~si[i]
        ev = nA[i] >= a_sub
        conf = np.where(cons == N.CONSECUENTES[0], cs[i], 1 - cs[i])
        q = np.percentile(conf[ev], [2.5, 97.5]) if ev.any() else [np.nan, np.nan]
        filas.append({'reaparece_marcada': float((marc[i] & d).mean()), 'misma_direccion': float((d & ev).sum() / max(ev.sum(), 1)), 'submuestras_evaluables': int(ev.sum()),
                      'confianza_p2_5': q[0], 'confianza_p97_5': q[1]})
    E = pd.concat([R[['antecedente', 'consecuente']].reset_index(drop=True), pd.DataFrame(filas)], axis=1)
    E['estable'] = (E['reaparece_marcada'] >= N.ESTABLE_REAP) & (E['misma_direccion'] >= N.ESTABLE_DIR)
    return E, {'n_submuestra': m, 'umbral_antecedente_sub': a_sub, 'umbral_conjunto_sub': b_sub, 'marcadas_media_sub': float(marc.sum(axis=0).mean())}


def clasificar(R, E=None):
    R = R.copy()
    if E is not None:
        R = R.merge(E[['antecedente', 'reaparece_marcada', 'misma_direccion', 'estable']], on='antecedente', how='left')
    clase = []
    for r in R.itertuples():
        if not r.marcada:
            clase.append('1 asociación débil')
        elif r.redundante is True:
            clase.append('2 redundante')
        elif not r.supera_nula_estrato:
            clase.append('3 compatible con la nula del estrato')
        elif E is None:
            clase.append('4-5 supera la nula del estrato (estabilidad no evaluada)')
        elif not r.estable:
            clase.append('4 inestable')
        else:
            clase.append('5 asociación relativamente más marcada')
    R['clase'] = clase
    return R


def ajuste_conjunto(Rs, nulas):
    """p ajustado conjunto: máximo |z| entre todos los estratos en cada índice de permutación (permutaciones independientes por estrato)."""
    if not nulas:
        return Rs
    mx = np.max(np.stack([n['max_z'].to_numpy() for n in nulas.values()]), axis=0)
    out = {}
    for k, R in Rs.items():
        R = R.copy()
        if len(R):
            R['p_ajustado_conjunto'] = [(1 + (mx >= z).sum()) / (1 + len(mx)) for z in R['z'].abs()]
            R['supera_nula_conjunta'] = R['p_ajustado_conjunto'] < N.ALFA
        out[k] = R
    return out, mx
