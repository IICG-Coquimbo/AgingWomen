"""
Fase 39: comparación formal de la asociación entre estratos (sección 8 del protocolo). Para cada antecedente comparable de 1 o 2 condiciones:
diferencia de riesgo DR_s = P(severo | A, s) − P(severo | no A, s) en cada estrato, IC de Newcombe, estadístico de heterogeneidad Q (para dos estratos, Δ y z),
referencia nula por permutación dentro de los estratos (máximo Q y menor p χ²), estabilidad por submuestras estratificadas y redundancia.
"""
import math
import sys
from itertools import combinations

import nucleo_39 as N
import numpy as np
import pandas as pd
from scipy.stats import chi2

sys.dont_write_bytecode = True
G = N.G


def candidatos(T, excl, largo):
    items = [c for c in T.columns if N.N38.variable_de_item(c) not in excl]
    ants = [(i,) for i in items]
    if largo >= 2:
        ants += [(a, b) for a, b in combinations(items, 2) if N.N38.variable_de_item(a) != N.N38.variable_de_item(b)]
    return ants


def recuentos(A, Y, ms):
    """Para cada estrato: n_A (k,), k_si (k, m), n (escalar), n_si (m,)."""
    out = []
    for m in ms:
        As = A[:, m]
        out.append((As.sum(axis=1).astype(float), G.contar(As, Y[m]).astype(float), float(m.sum()), Y[m].sum(axis=0).astype(float)))
    return out


def estadisticos(rec):
    """DR, var, Q y p para cada antecedente y cada columna de Y. rec: salida de recuentos."""
    DR, V = [], []
    for nA, k, n, nsi in rec:
        nA2 = nA[:, None]
        nno = n - nA2
        with np.errstate(divide='ignore', invalid='ignore'):
            c1 = k / nA2
            c0 = (nsi[None, :] - k) / nno
            p1 = (k + 0.5) / (nA2 + 1)
            p0 = (nsi[None, :] - k + 0.5) / (nno + 1)
            v = p1 * (1 - p1) / nA2 + p0 * (1 - p0) / nno
        DR.append(c1 - c0)
        V.append(v)
    DR, V = np.stack(DR), np.stack(V)
    W = 1 / V
    DRw = (W * DR).sum(axis=0) / W.sum(axis=0)
    Q = (W * (DR - DRw) ** 2).sum(axis=0)
    return DR, V, Q


def comparables(A, ms, comp, ants, Tfull):
    """Antecedentes con n_A ≥ comp y n − n_A ≥ comp en todos los estratos, y sin pares determinados en ningún estrato."""
    ok = np.ones(len(ants), bool)
    col = {c: i for i, c in enumerate(Tfull.columns)}
    V = Tfull.to_numpy()
    for m in ms:
        nA = A[:, m].sum(axis=1)
        ok &= (nA >= comp) & (m.sum() - nA >= comp)
        ns = V[m].sum(axis=0)
        for r, a in enumerate(ants):
            if len(a) == 2 and ok[r] and (nA[r] == ns[col[a[0]]] or nA[r] == ns[col[a[1]]]):
                ok[r] = False
    return ok


def orden(DR):
    """Dirección del patrón entre estratos: signo de Δ para dos estratos; (estrato máximo, estrato mínimo) para tres o más."""
    if DR.shape[0] == 2:
        return np.sign(DR[0] - DR[1])
    return np.argmax(DR, axis=0) * 10 + np.argmin(DR, axis=0)


def tabla(ants, rec, DR, V, Q, estratos):
    S = len(estratos)
    df = S - 1
    filas = []
    for r, a in enumerate(ants):
        f = {'antecedente': ' & '.join(a), 'largo': len(a), 'variables': ' & '.join(sorted(N.N38.variable_de_item(i) for i in a))}
        for s, (nA, k, n, nsi) in enumerate(rec):
            e = estratos[s]
            kk, na, ksi = k[r, 0], nA[r], nsi[0]
            lo, hi = N.N38.newcombe(kk, na, ksi - kk, n - na)
            f.update({f'n_{e}': int(n), f'nA_{e}': int(na), f'nAC_{e}': int(kk), f'nnoA_{e}': int(n - na), f'nnoAC_{e}': int(ksi - kk),
                      f'basal_{e}': ksi / n, f'confianza_{e}': kk / na, f'prevalencia_{e}': na / n, f'DR_{e}': DR[s, r, 0], f'DR_inf_{e}': float(lo), f'DR_sup_{e}': float(hi)})
        d = DR[:, r, 0]
        f['rango_DR'] = float(d.max() - d.min())
        f['Q'] = float(Q[r, 0])
        f['p_chi2'] = float(chi2.sf(Q[r, 0], df))
        if S == 2:
            e1, e2 = estratos
            f['delta'] = float(d[0] - d[1])
            f['z_interaccion'] = float((d[0] - d[1]) / math.sqrt(V[0, r, 0] + V[1, r, 0]))
            l1, u1, l2, u2 = f[f'DR_inf_{e1}'], f[f'DR_sup_{e1}'], f[f'DR_inf_{e2}'], f[f'DR_sup_{e2}']
            f['delta_inf'] = f['delta'] - math.sqrt((d[0] - l1) ** 2 + (u2 - d[1]) ** 2)
            f['delta_sup'] = f['delta'] + math.sqrt((u1 - d[0]) ** 2 + (d[1] - l2) ** 2)
        f['estrato_DR_max'] = estratos[int(np.argmax(d))]
        f['estrato_DR_min'] = estratos[int(np.argmin(d))]
        f['orden'] = float(orden(DR[:, r, :])[0])
        prev = [f[f'prevalencia_{e}'] for e in estratos]
        f['composicion_distinta'] = (max(prev) - min(prev)) >= N.COMPOSICION
        f['marcada'] = f['rango_DR'] >= N.DIF_HET
        filas.append(f)
    return pd.DataFrame(filas)


def permutaciones(n, ms, semilla, n_perm=N.N_PERM):
    """Índices permutados solo dentro de cada estrato (los participantes fuera de los estratos quedan fijos)."""
    rng = np.random.default_rng(semilla)
    idx = [np.flatnonzero(m) for m in ms]
    perms = []
    for _ in range(n_perm):
        p = np.arange(n)
        for ii in idx:
            p[ii] = ii[rng.permutation(len(ii))]
        perms.append(p)
    return perms


def nula(A, y, ms, carpeta, semilla, n_perm=N.N_PERM, lote=100):
    """Permutación de la severidad dentro de cada estrato a la vez; máximo Q y menor p χ² por permutación. Lotes reanudables."""
    carpeta.mkdir(parents=True, exist_ok=True)
    perms = permutaciones(len(y), ms, semilla, n_perm)
    df = len(ms) - 1
    filas = []
    for i0 in range(0, n_perm, lote):
        archivo = carpeta / f'lote_{i0:04d}.npz'
        if archivo.exists():
            z = np.load(archivo)
            filas.append(pd.DataFrame({k: z[k] for k in z.files}))
            continue
        Y = np.stack([y[p] for p in perms[i0:i0 + lote]], axis=1)
        DR, V, Q = estadisticos(recuentos(A, Y, ms))
        rango = DR.max(axis=0) - DR.min(axis=0)
        t = {'permutacion': np.arange(i0, i0 + Y.shape[1]), 'max_Q': Q.max(axis=0), 'min_p': chi2.sf(Q.max(axis=0), df),
             'marcadas': (rango >= N.DIF_HET).sum(axis=0), 'max_rango': rango.max(axis=0)}
        np.savez(archivo, **t)
        filas.append(pd.DataFrame(t))
    return pd.concat(filas, ignore_index=True)


def estabilidad(A, y, ms, ord_obs, comp, semilla, n_sub=N.N_SUB, frac=N.FRAC_SUB):
    """Submuestras estratificadas del 80 % de cada estrato. Devuelve reaparición (marcada, mismo orden, comparable) y misma dirección."""
    rng = np.random.default_rng(semilla)
    n = len(y)
    S = np.zeros((n, n_sub), np.uint8)
    for m in ms:
        ii = np.flatnonzero(m)
        k = int(round(frac * len(ii)))
        for j in range(n_sub):
            S[rng.choice(ii, k, replace=False), j] = 1
    c_sub = math.ceil(round(frac * comp, 9))
    DRs, ev = [], np.ones((A.shape[0], n_sub), bool)
    for m in ms:
        As = A[:, m]
        Sm = S[m]
        nA = G.contar(As, Sm).astype(float)
        k = G.contar(As, Sm * y[m][:, None]).astype(float)
        nn = Sm.sum(axis=0)[None, :].astype(float)
        nsi = (Sm * y[m][:, None]).sum(axis=0)[None, :].astype(float)
        with np.errstate(divide='ignore', invalid='ignore'):
            DRs.append(k / nA - (nsi - k) / (nn - nA))
        ev &= (nA >= c_sub) & (nn - nA >= c_sub)
    DR = np.stack(DRs)
    rango = DR.max(axis=0) - DR.min(axis=0)
    o = orden(np.nan_to_num(DR))
    mismo = o == ord_obs[:, None]
    return pd.DataFrame({'reaparece_marcada': ((rango >= N.DIF_HET) & mismo & ev).mean(axis=1), 'misma_direccion': (mismo & ev).sum(axis=1) / np.maximum(ev.sum(axis=1), 1),
                         'submuestras_evaluables': ev.sum(axis=1)})


def redundancia(H):
    """Un par es redundante si alguna de sus condiciones, sola y comparable, tiene un rango ≥ rango del par − 0,05."""
    r1 = dict(zip(H.loc[H['largo'] == 1, 'antecedente'], H.loc[H['largo'] == 1, 'rango_DR']))
    red, sub = [], []
    for a, l, r in zip(H['antecedente'], H['largo'], H['rango_DR']):
        if l == 1:
            red.append(False)
            sub.append('')
            continue
        partes = [p for p in a.split(' & ') if p in r1]
        mejor = max(partes, key=lambda p: r1[p]) if partes else ''
        red.append(bool(partes) and r1[mejor] >= r - N.MEJORA_MIN)
        sub.append(mejor)
    H = H.copy()
    H['redundante'] = red
    H['condicion_sola_mas_cercana'] = sub
    return H


def clasificar(H):
    c = []
    for r in H.itertuples():
        if not r.marcada:
            c.append('H1 sin diferencia apreciable')
        elif r.redundante:
            c.append('H2 redundante')
        elif not r.supera_nula_dimension:
            c.append('H3 diferencia compatible con la nula')
        elif not r.estable:
            c.append('H4 diferencia inestable')
        else:
            c.append('H5 diferencia que supera los controles de la dimensión')
    H = H.copy()
    H['clase'] = c
    return H


def comparar(T529, y, masc, grupo, estratos, comp, largo, carpeta, semilla_nula, semilla_sub, n_perm=N.N_PERM, con_estabilidad=True):
    """Comparación completa de una dimensión (o de A/B1). Devuelve tabla H, nula y meta."""
    ms = [masc[(grupo, e)] for e in estratos]
    ants = candidatos(T529, set(N.excluidas(grupo)), largo)
    A = G.matriz_antecedentes(T529, [frozenset(a) for a in ants])
    ok = comparables(A, ms, comp, ants, T529)
    ants = [a for a, k in zip(ants, ok) if k]
    A = A[ok]
    rec = recuentos(A, y[:, None], ms)
    DR, V, Q = estadisticos(rec)
    H = tabla(ants, rec, DR, V, Q, estratos)
    nl = nula(A, y, ms, carpeta / 'lotes_nula', semilla_nula, n_perm=n_perm)
    mq = nl['max_Q'].to_numpy()
    H['p_ajustado_dimension'] = [(1 + (mq >= q).sum()) / (1 + len(mq)) for q in H['Q']]
    H['supera_nula_dimension'] = H['p_ajustado_dimension'] < N.ALFA
    H['q_bh_dimension'] = N.N38.bh(H['p_chi2'].to_numpy()) if len(H) else []
    H = redundancia(H)
    if con_estabilidad and len(H):
        E = estabilidad(A, y, ms, H['orden'].to_numpy(), comp, semilla_sub)
        H = pd.concat([H, E], axis=1)
        H['estable'] = (H['reaparece_marcada'] >= N.ESTABLE_REAP) & (H['misma_direccion'] >= N.ESTABLE_DIR)
    else:
        H['estable'] = np.nan
    H['ligada_a_estrato'] = H['variables'].apply(lambda v: grupo == 'ejercicio' and any(x in v.split(' & ') for x in N.N38.FRECUENCIAS_EJERCICIO))
    H['proxima_a_sintomas'] = H['variables'].apply(lambda v: any(x in v.split(' & ') for x in N.N38.PROXIMAS))
    H = clasificar(H) if con_estabilidad else H
    meta = {'grupo': grupo, 'estratos': ' / '.join(estratos), 'comparabilidad_minima': comp, 'largo_maximo': largo, 'candidatos': len(ok), 'comparables': int(ok.sum()),
            'marcadas': int(H['marcada'].sum()) if len(H) else 0, 'nula_media_marcadas': float(nl['marcadas'].mean()),
            'p_exceso_marcadas': float(((nl['marcadas'] >= (H['marcada'].sum() if len(H) else 0)).sum() + 1) / (len(nl) + 1)),
            'nula_p95_max_Q': float(nl['max_Q'].quantile(0.95)), 'supera_nula_dimension': int(H['supera_nula_dimension'].sum()) if len(H) else 0}
    return H, nl, meta


def ajuste_conjunto(Hs, nulas):
    """p ajustado conjunto entre dimensiones: menor p χ² entre todas las dimensiones en cada índice de permutación."""
    mp = np.min(np.stack([n['min_p'].to_numpy() for n in nulas.values()]), axis=0)
    out = {}
    for k, H in Hs.items():
        H = H.copy()
        H['p_ajustado_conjunto'] = [(1 + (mp <= p).sum()) / (1 + len(mp)) for p in H['p_chi2']]
        H['supera_nula_conjunta'] = H['p_ajustado_conjunto'] < N.ALFA
        out[k] = H
    return out, mp


def interaccion_ad_hoc(T, y, ms, antecedente):
    """Estadísticos de heterogeneidad para un antecedente cualquiera (también de 3 condiciones), sin ajuste por búsqueda."""
    A = G.matriz_antecedentes(T, [frozenset(antecedente.split(' & '))])
    rec = recuentos(A, y[:, None], ms)
    DR, V, Q = estadisticos(rec)
    out = {'Q': float(Q[0, 0]), 'p_chi2_sin_ajuste': float(chi2.sf(Q[0, 0], len(ms) - 1)), 'rango_DR': float(DR[:, 0, 0].max() - DR[:, 0, 0].min())}
    if len(ms) == 2:
        out['delta'] = float(DR[0, 0, 0] - DR[1, 0, 0])
        out['z_interaccion'] = out['delta'] / math.sqrt(V[0, 0, 0] + V[1, 0, 0])
    out['nA_por_estrato'] = ' / '.join(str(int(r[0][0])) for r in rec)
    return out
