"""
Fase 39R, etapa D: comparación formal entre estratos en cada dimensión (DR, Newcombe, Q, Δ, nula de heterogeneidad, ajustes, redundancia, composición y estabilidad) y diferencias de significación.
Usa sin modificar heterogeneidad_39.py.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/etapa_d_comparacion.py
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import heterogeneidad_39 as H  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

N.instalar_gancho()
N.huella_sello()
BASE = N.BASE
pq = N.cargar()
y = pq.d.M['severo_mrs'].to_numpy().astype(int)
T529, _ = N.base_items(pq)
masc = N.mascaras(pq)
TODAS = pd.read_csv(BASE / 'reglas' / 'reglas_todos_estratos.csv')
DEST = pd.read_csv(BASE / 'reglas' / 'reglas_superan_nula_estrato.csv')

Hs, nulas_h, metas_h = {}, {}, []
for dim in N.DIMENSIONES:
    est = N.dims_de(dim)
    Hd, nl, meta = H.comparar(T529, y, masc, dim, est, N.UMBRALES['principal'][4], 2, BASE / 'comparacion' / 'lotes' / dim,
                              [N.SEMILLA, 39, 100 + N.NUM_DIM[dim]], [N.SEMILLA, 39, 3, N.NUM_DIM[dim]], n_perm=N.N_PERM)
    N.BAR.verificar_tabla_comparacion(Hd, 'principal', dim, pq.dec, N.variable_de_item)
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

# diferencias de significación: reglas que superan la nula de un estrato, con su prueba de interacción (no se interpretan como interacción por sí solas)
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
N.a_csv(pd.DataFrame(sig, columns=['dimension', 'estrato_donde_supera', 'antecedente', 'consecuente', 'supera_en_otros_estratos', 'en_busqueda_de_heterogeneidad', 'nA_por_estrato', 'rango_DR', 'delta', 'z_interaccion', 'p_chi2_sin_ajuste', 'p_ajustado_dimension', 'clase_comparacion']),
        BASE / 'comparacion' / 'diferencias_de_significacion.csv')
N.registrar('etapa D: comparación entre estratos')
print(MH.to_string(index=False))
print(pd.DataFrame(sig).to_string() if sig else 'ninguna regla supera la nula de su estrato')
