"""
Fase 39R, etapas B y C: reglas dentro de los 9 estratos con referencia nula propia (1.000 permutaciones, semillas históricas), estabilidad, referencia conjunta de los 9 estratos y clasificación.
Usa sin modificar busqueda_39.py. La búsqueda y la nula van juntas porque comparten los antecedentes frecuentes.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/etapa_bc_reglas_nulas.py
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import busqueda_39 as B  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

N.instalar_gancho()
N.huella_sello()
BASE = N.BASE
pq = N.cargar()
T529, _ = N.base_items(pq)
masc = N.mascaras(pq)

Rs, nulas, metas, Es = {}, {}, [], {}
for dim, e in N.ESTRATOS:
    c = N.construir(pq, dim, e, T529=T529, masc=masc)
    k = N.NUM_ESTRATO[(dim, e)]
    R, nl, meta, frec, det = B.buscar(c, BASE / 'referencia_nula' / 'lotes' / f'{dim}_{e}', [N.SEMILLA, 39, k], n_perm=N.N_PERM)
    if len(R):
        E, me = B.estabilidad(c, frec, det, R, BASE / 'estabilidad' / 'lotes' / f'{dim}_{e}', [N.SEMILLA, 39, 2, k], n_sub=N.N_SUB)
        meta.update(me)
        R = B.clasificar(R, E)
        Es[(dim, e)] = E
    N.BAR.verificar_tabla_reglas(R, 'principal', dim, pq.dec, N.variable_de_item, N.CONSECUENTES)
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
N.registrar('etapas B y C: reglas y referencias nulas')
print(M[['dimension', 'estrato', 'n', 'items', 'reglas', 'marcadas', 'nula_media_marcadas', 'p_exceso_marcadas', 'supera_nula_estrato', 'supera_nula_conjunta']].to_string(index=False))
print('Clases:', TODAS['clase'].value_counts().to_dict())
