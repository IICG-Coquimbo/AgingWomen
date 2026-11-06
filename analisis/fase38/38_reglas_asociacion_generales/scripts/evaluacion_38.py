"""
Fase 38: evaluación completa de una configuración: reglas, redundancia, q de BH sobre todas las reglas evaluadas, referencia nula por permutaciones
(máximo |z|, Westfall-Young de un paso) y, si se pide, estabilidad por submuestras. Los lotes se guardan para poder reanudar.
"""
import math
import sys
import time

import algoritmos_38 as G
import nucleo_38 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True


def mapa_consecuente(frec):
    """antecedente → (n_A, n_SI) para todos los antecedentes frecuentes."""
    out = {}
    for s, c in frec.items():
        if s & G.CONS:
            continue
        si = frec.get(s | {N.CONSECUENTES[0]})
        no = frec.get(s | {N.CONSECUENTES[1]})
        if si is None and no is None:
            si = None
        elif si is None:
            si = c - no
        out[s] = (c, si)
    return out


def descubrir(c, minsup=None, algoritmo='fpgrowth'):
    minsup = minsup or c.min_conj
    f = {'fpgrowth': G.fpgrowth, 'apriori': G.apriori, 'exhaustiva': G.exhaustiva}[algoritmo]
    return f(c.T, c.y, minsup, c.largo)


def reglas_de(c, frec, determinados):
    R = G.reglas(frec, c.n, c.n_si, c.min_ant, c.min_conj, determinados)
    if not len(R):
        return R
    R = G.redundancia(R, mapa_consecuente(frec))
    R['q_bh_todas'] = N.bh(R['p_fisher'].to_numpy())
    R['familia'] = R['variables'] + ' → ' + R['consecuente']
    return R


def referencia_nula(c, frec, determinados, carpeta, n_perm=N.N_PERM, lote=100, semilla=N.SEMILLA):
    """Permuta el consecuente dentro de la población de la configuración y repite la búsqueda completa sobre los mismos antecedentes (que no dependen del
    consecuente). Guarda por permutación: máximo |z| entre reglas válidas, número de reglas marcadas y mayor |c − p0|."""
    carpeta.mkdir(parents=True, exist_ok=True)
    ants = list(G.antecedentes(frec, c.min_ant, determinados))
    nA = np.array([frec[s] for s in ants], float)
    A = G.matriz_antecedentes(c.T, ants)
    rng = np.random.default_rng(semilla)
    perms = [rng.permutation(c.n) for _ in range(n_perm)]
    filas = []
    for i0 in range(0, n_perm, lote):
        archivo = carpeta / f'lote_{i0:04d}.npz'
        if archivo.exists():
            z = np.load(archivo)
            filas.append(pd.DataFrame({k: z[k] for k in z.files}))
            continue
        Y = np.stack([c.y[p] for p in perms[i0:i0 + lote]], axis=1)
        k = G.contar(A, Y)
        zz, val, dif = G.z_y_validez(nA, k, c.n, c.n_si, c.min_conj)
        zz = np.where(val, zz, 0)
        marc = (val & (dif >= N.DIF_MARCADA)).sum(axis=0)
        t = {'permutacion': np.arange(i0, i0 + Y.shape[1]), 'max_z': zz.max(axis=0), 'reglas_marcadas': marc,
             'max_dif': np.where(val, dif, 0).max(axis=0), 'reglas_validas': val.sum(axis=0)}
        np.savez(archivo, **t)
        filas.append(pd.DataFrame(t))
    return pd.concat(filas, ignore_index=True), len(ants)


def ajustar(R, nula):
    m = nula['max_z'].to_numpy()
    R = R.copy()
    R['p_ajustado_busqueda'] = [(1 + (m >= z).sum()) / (1 + len(m)) for z in R['z'].abs()]
    R['supera_nula'] = R['p_ajustado_busqueda'] < N.ALFA
    return R


def estabilidad(c, frec, determinados, R, carpeta, n_sub=N.N_SUB, frac=N.FRAC_SUB, lote=50, semilla=N.SEMILLA):
    """Submuestras sin reemplazo: redescubre las reglas con los mismos ítems y umbrales proporcionales. Usa todos los antecedentes que podrían alcanzar el
    umbral en una submuestra (n_A completo ≥ umbral de la submuestra)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    m = int(round(frac * c.n))
    a_sub = math.ceil(round(0.10 * m, 9))
    b_sub = math.ceil(round(0.05 * m, 9))
    ants = list(G.antecedentes(frec, a_sub, determinados))
    idx = {s: i for i, s in enumerate(ants)}
    A = G.matriz_antecedentes(c.T, ants)
    rng = np.random.default_rng([semilla, 2])
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
    dif = np.abs(cs - p0)
    marc = (nA >= a_sub) & (kk >= b_sub) & (dif >= N.DIF_MARCADA)
    filas_r = []
    marc_full = set(R.loc[R['marcada'], 'items'].map(frozenset))
    for items, cons in zip(R['items'], R['consecuente']):
        i = idx[frozenset(items)]
        dir_ok = si[i] if cons == N.CONSECUENTES[0] else ~si[i]
        evaluable = nA[i] >= a_sub
        conf = np.where(cons == N.CONSECUENTES[0], cs[i], 1 - cs[i])
        base = np.where(cons == N.CONSECUENTES[0], p0, 1 - p0)
        sup = np.where(cons == N.CONSECUENTES[0], k[i], nA[i] - k[i]) / m
        ev = evaluable
        q = (lambda x: np.percentile(x[ev], [2.5, 97.5]) if ev.any() else [np.nan, np.nan])
        filas_r.append({'reaparece_marcada': float((marc[i] & dir_ok).mean()), 'misma_direccion': float((dir_ok & ev).sum() / max(ev.sum(), 1)),
                        'submuestras_evaluables': int(ev.sum()), 'confianza_p2_5': q(conf)[0], 'confianza_p97_5': q(conf)[1],
                        'soporte_p2_5': q(sup)[0], 'soporte_p97_5': q(sup)[1], 'lift_p2_5': q(conf / base)[0], 'lift_p97_5': q(conf / base)[1]})
    E = pd.concat([R[['antecedente', 'consecuente', 'familia']].reset_index(drop=True), pd.DataFrame(filas_r)], axis=1)
    E['estable'] = (E['reaparece_marcada'] >= N.ESTABLE_REAP) & (E['misma_direccion'] >= N.ESTABLE_DIR)
    # familias
    fam_de = {}
    for s, i in idx.items():
        vs = ' & '.join(sorted(N.variable_de_item(x) for x in s))
        fam_de.setdefault(vs, []).append(i)
    fam = []
    for f in sorted(set(R.loc[R['marcada'], 'familia'])):
        vs, cons = f.split(' → ')
        filas = fam_de[vs]
        d = si[filas] if cons == N.CONSECUENTES[0] else ~si[filas]
        aparece = (marc[filas] & d).any(axis=0)
        fam.append({'familia': f, 'reglas_en_familia_completa': int(((R['familia'] == f) & R['marcada']).sum()), 'familia_reaparece': float(aparece.mean())})
    F = pd.DataFrame(fam)
    # reglas nuevas y desaparecidas por submuestra
    idx_full = np.array([idx[s] for s in marc_full]) if marc_full else np.array([], int)
    total_sub = marc.sum(axis=0)
    full_en_sub = marc[idx_full].sum(axis=0) if len(idx_full) else np.zeros(n_sub)
    Sb = pd.DataFrame({'submuestra': np.arange(n_sub), 'n': m, 'frecuencia_basal_si': p0, 'reglas_marcadas': total_sub, 'marcadas_tambien_en_completa': full_en_sub,
                       'nuevas': total_sub - full_en_sub, 'desaparecidas': len(idx_full) - full_en_sub})
    return E, F, Sb, {'n_submuestra': m, 'umbral_antecedente': a_sub, 'umbral_conjunto': b_sub, 'antecedentes_evaluados': len(ants)}


def clasificar(R, E=None, soporte_principal=None):
    """Clasificación excluyente del protocolo (sección 9)."""
    R = R.copy()
    if E is not None:
        R = R.merge(E[['antecedente', 'reaparece_marcada', 'misma_direccion', 'estable']], on='antecedente', how='left')
    clase = []
    for r in R.itertuples():
        if soporte_principal is not None and r.n_antecedente < soporte_principal:
            clase.append('1 soporte insuficiente')
        elif not r.marcada:
            clase.append('2 asociación débil')
        elif r.redundante is True:
            clase.append('3 redundante')
        elif not r.supera_nula:
            clase.append('4 compatible con la referencia nula')
        elif E is None:
            clase.append('5-6 supera la nula (estabilidad no evaluada)')
        elif not r.estable:
            clase.append('5 inestable')
        else:
            clase.append('6 asociación relativamente más marcada')
    R['clase'] = clase
    return R


def evaluar(c, carpeta, con_estabilidad=False, soporte_principal=None, algoritmo='fpgrowth'):
    t0 = time.time()
    frec = descubrir(c, algoritmo=algoritmo)
    det = N.pares_determinados(c.T)
    R = reglas_de(c, frec, det)
    nula, n_ants = referencia_nula(c, frec, det, carpeta / 'lotes_nula')
    R = ajustar(R, nula)
    E = F = Sb = meta_e = None
    if con_estabilidad:
        E, F, Sb, meta_e = estabilidad(c, frec, det, R, carpeta / 'lotes_estabilidad')
    R = clasificar(R, E, soporte_principal)
    meta = {'configuracion': c.nombre, 'descripcion': c.descripcion, 'n': c.n, 'n_si': c.n_si, 'frecuencia_basal_si': c.n_si / c.n, 'items': c.T.shape[1],
            'items_constantes_quitados': c.constantes, 'umbral_antecedente': c.min_ant, 'umbral_conjunto': c.min_conj, 'largo_maximo': c.largo,
            'conjuntos_frecuentes': len(frec), 'antecedentes_evaluados': n_ants, 'pares_determinados': len(det), 'reglas': len(R),
            'marcadas': int(R['marcada'].sum()) if len(R) else 0, 'nula_media_marcadas': float(nula['reglas_marcadas'].mean()),
            'nula_p95_marcadas': float(nula['reglas_marcadas'].quantile(0.95)), 'nula_p95_max_z': float(nula['max_z'].quantile(0.95)),
            'nula_p95_max_dif': float(nula['max_dif'].quantile(0.95)), 'supera_nula': int(R['supera_nula'].sum()) if len(R) else 0,
            'segundos': round(time.time() - t0, 1)}
    if meta_e:
        meta['estabilidad'] = meta_e
    return R, nula, E, F, Sb, meta, frec, det
