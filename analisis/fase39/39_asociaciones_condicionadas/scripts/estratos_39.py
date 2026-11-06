"""
Fase 39: análisis principal. (1) Reglas dentro de cada uno de los 9 estratos, con referencia nula propia, estabilidad y ajuste conjunto. (2) Comparación formal
entre estratos en cada dimensión, con referencia nula, estabilidad, redundancia y ajuste conjunto. (3) Diferencias de significación.

Uso, desde la carpeta scripts: python estratos_39.py
"""
import sys

import busqueda_39 as B
import heterogeneidad_39 as H
import nucleo_39 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
N.instalar_gancho()
N.huella_sello()
BASE = N.BASE
d = N.cargar()
y = d.M['severo_mrs'].to_numpy().astype(int)
T529, _ = N.base_items(d)
masc = N.mascaras(d)

# ---- 1. reglas dentro de cada estrato
Rs, nulas, metas, Es = {}, {}, [], {}
for dim, e in N.ESTRATOS:
    c = N.construir(d, dim, e, T529=T529, masc=masc)
    k = N.NUM_ESTRATO[(dim, e)]
    R, nl, meta, frec, det = B.buscar(c, BASE / 'referencia_nula' / 'lotes' / f'{dim}_{e}', [N.SEMILLA, 39, k])
    if len(R):
        E, me = B.estabilidad(c, frec, det, R, BASE / 'estabilidad' / 'lotes' / f'{dim}_{e}', [N.SEMILLA, 39, 2, k])
        meta.update(me)
        R = B.clasificar(R, E)
        Es[(dim, e)] = E
    Rs[(dim, e)], nulas[(dim, e)] = R, nl
    N.a_csv(nl, BASE / 'referencia_nula' / f'nula_{dim}_{e}.csv')
    metas.append({'dimension': dim, 'estrato': e, **meta})
    print(dim, e, {k_: meta[k_] for k_ in ('n', 'reglas', 'marcadas', 'nula_media_marcadas', 'supera_nula_estrato', 'segundos')}, flush=True)
Rs, mx = B.ajuste_conjunto(Rs, nulas)
N.a_csv(pd.DataFrame({'permutacion': np.arange(len(mx)), 'max_z_9_estratos': mx}), BASE / 'referencia_nula' / 'nula_conjunta_estratos.csv')
todas = []
for (dim, e), R in Rs.items():
    N.a_csv(R.drop(columns=['items']), BASE / 'reglas' / dim / f'reglas_{e}.csv')
    if (dim, e) in Es:
        N.a_csv(Es[(dim, e)], BASE / 'estabilidad' / f'estabilidad_{dim}_{e}.csv')
    t = R.drop(columns=['items']).copy()
    t.insert(0, 'estrato', e)
    t.insert(0, 'dimension', dim)
    todas.append(t)
TODAS = pd.concat(todas, ignore_index=True)
N.a_csv(TODAS, BASE / 'reglas' / 'reglas_todos_estratos.csv')
M = pd.DataFrame(metas)
cls = TODAS.groupby(['dimension', 'estrato', 'clase']).size().unstack(fill_value=0).reset_index()
M = M.merge(cls, on=['dimension', 'estrato'], how='left')
M['supera_nula_conjunta'] = M.apply(lambda r: int(TODAS[(TODAS['dimension'] == r['dimension']) & (TODAS['estrato'] == r['estrato'])]['supera_nula_conjunta'].sum()), axis=1)
N.a_csv(M, BASE / 'reglas' / 'resumen_estratos.csv')
DEST = TODAS[TODAS['supera_nula_estrato']].sort_values('p_ajustado_estrato')
N.a_csv(DEST, BASE / 'reglas' / 'reglas_superan_nula_estrato.csv')
top = (TODAS[~TODAS['redundante'].fillna(False).astype(bool)].assign(az=lambda t: t['z'].abs()).sort_values('az', ascending=False)
       .groupby(['dimension', 'estrato', 'consecuente']).head(5).drop(columns='az'))
N.a_csv(top, BASE / 'reglas' / 'reglas_mayor_z_por_estrato.csv')
N.a_csv(TODAS[TODAS['marcada'] & TODAS['redundante'].fillna(False).astype(bool)], BASE / 'redundancia' / 'reglas_redundantes_estratos.csv')

# ---- 2. comparación entre estratos
Hs, nulas_h, metas_h = {}, {}, []
for dim in N.DIMENSIONES:
    est = N.dims_de(dim)
    Hd, nl, meta = H.comparar(T529, y, masc, dim, est, N.UMBRALES['principal'][4], 2, BASE / 'comparacion' / 'lotes' / dim,
                              [N.SEMILLA, 39, 100 + N.NUM_DIM[dim]], [N.SEMILLA, 39, 3, N.NUM_DIM[dim]])
    Hs[dim], nulas_h[dim] = Hd, nl
    N.a_csv(nl, BASE / 'comparacion' / f'nula_comparacion_{dim}.csv')
    metas_h.append(meta)
    print('comparación', dim, meta, flush=True)
Hs, mp = H.ajuste_conjunto(Hs, nulas_h)
N.a_csv(pd.DataFrame({'permutacion': np.arange(len(mp)), 'min_p_4_dimensiones': mp}), BASE / 'comparacion' / 'nula_conjunta_dimensiones.csv')
for dim, Hd in Hs.items():
    N.a_csv(Hd, BASE / 'comparacion' / f'comparacion_{dim}.csv')
MH = pd.DataFrame(metas_h)
MH['clases'] = [Hs[g]['clase'].value_counts().to_dict() for g in MH['grupo']]
MH['supera_nula_conjunta'] = [int(Hs[g]['supera_nula_conjunta'].sum()) for g in MH['grupo']]
N.a_csv(MH, BASE / 'comparacion' / 'resumen_comparacion.csv')
N.a_csv(pd.concat([Hd[Hd['redundante']].assign(dimension=g) for g, Hd in Hs.items()], ignore_index=True), BASE / 'redundancia' / 'comparaciones_redundantes.csv')

# ---- 3. diferencias de significación: reglas que superan la nula de un estrato, comparadas con la prueba de interacción
sig = []
for _, r in DEST.iterrows():
    dim = r['dimension']
    est = N.dims_de(dim)
    Hd = Hs[dim]
    fila = Hd[Hd['antecedente'] == r['antecedente']]
    ms = [masc[(dim, e)] for e in est]
    otros = {e: bool(((TODAS['dimension'] == dim) & (TODAS['estrato'] == e) & (TODAS['antecedente'] == r['antecedente']) & TODAS['supera_nula_estrato']).any()) for e in est}
    base = {'dimension': dim, 'estrato_donde_supera': r['estrato'], 'antecedente': r['antecedente'], 'consecuente': r['consecuente'],
            'supera_en_otros_estratos': ', '.join(e for e, v in otros.items() if v and e != r['estrato']) or 'ninguno'}
    if len(fila):
        f = fila.iloc[0]
        base.update({'en_busqueda_de_heterogeneidad': True, 'nA_por_estrato': ' / '.join(str(int(f[f'nA_{e}'])) for e in est), 'rango_DR': f['rango_DR'],
                     'delta': f.get('delta', np.nan), 'z_interaccion': f.get('z_interaccion', np.nan), 'p_chi2_sin_ajuste': f['p_chi2'],
                     'p_ajustado_dimension': f['p_ajustado_dimension'], 'clase_comparacion': f['clase']})
    else:
        x = H.interaccion_ad_hoc(T529, y, ms, r['antecedente'])
        base.update({'en_busqueda_de_heterogeneidad': False, 'nA_por_estrato': x['nA_por_estrato'], 'rango_DR': x['rango_DR'], 'delta': x.get('delta', np.nan),
                     'z_interaccion': x.get('z_interaccion', np.nan), 'p_chi2_sin_ajuste': x['p_chi2_sin_ajuste'], 'p_ajustado_dimension': np.nan,
                     'clase_comparacion': 'fuera de la búsqueda (3 condiciones o no comparable): prueba sin ajuste, solo descriptiva'})
    sig.append(base)
N.a_csv(pd.DataFrame(sig), BASE / 'comparacion' / 'diferencias_de_significacion.csv')
N.registrar('estratos y comparación principal')
print(M[['dimension', 'estrato', 'n', 'reglas', 'marcadas', 'nula_media_marcadas', 'p_exceso_marcadas', 'supera_nula_estrato', 'supera_nula_conjunta']].to_string(index=False))
print(MH.to_string(index=False))
print(pd.DataFrame(sig).to_string() if sig else 'ninguna regla supera la nula de su estrato')
