"""
Fase 39R, etapa E (2): comparación secundaria y exploratoria con A y B1, con las etiquetas históricas sin reajustar. Sin trabajo, pareja ni días de ejercicio. No se calcula PCA, K-means ni FAMD.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/etapa_e_ab1.py
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import busqueda_39 as B  # noqa: E402
import heterogeneidad_39 as H  # noqa: E402
import pandas as pd  # noqa: E402

N.instalar_gancho()
N.huella_sello()
S = N.BASE / 'ab1'
pq = N.cargar()
d = pq.d
y = d.M['severo_mrs'].to_numpy().astype(int)
T529, _ = N.base_items(pq)
masc = N.mascaras(pq)
metas, todas, comp = [], [], []
for gi, g in enumerate(('A', 'B1')):
    Rs, nulas = {}, {}
    for k, e in enumerate(N.dims_de(g)):
        c = N.construir(pq, g, e, T529=T529, masc=masc)
        R, nl, meta, frec, det = B.buscar(c, S / 'lotes' / e, [N.SEMILLA, 39, 200 + 10 * gi + k], n_perm=N.N_PERM)
        if len(R):
            E, me = B.estabilidad(c, frec, det, R, S / 'lotes_estabilidad' / e, [N.SEMILLA, 39, 2, 200 + 10 * gi + k], n_sub=N.N_SUB)
            meta.update(me)
            R = B.clasificar(R, E)
            N.BAR.verificar_tabla_reglas(R, 'principal', g, pq.dec, N.variable_de_item, N.CONSECUENTES)
        Rs[e], nulas[e] = R, nl
        lo, hi = N.N38.wilson(c.n_si, c.n)
        metas.append({'grupo': g, 'estrato': e, 'ic_basal_inf': float(lo), 'ic_basal_sup': float(hi), **meta})
        print(g, e, {x: meta[x] for x in ('n', 'reglas', 'marcadas', 'nula_media_marcadas', 'supera_nula_estrato')}, flush=True)
    Rs, _ = B.ajuste_conjunto(Rs, nulas)
    for e, R in Rs.items():
        if len(R):
            t = R.drop(columns=['items']).copy()
            t.insert(0, 'estrato', e)
            t.insert(0, 'grupo', g)
            todas.append(t)
    Hg, nl, meta = H.comparar(T529, y, masc, g, N.dims_de(g), N.UMBRALES['principal'][4], 2, S / 'lotes_comparacion' / g, [N.SEMILLA, 39, 110 + gi], [N.SEMILLA, 39, 3, 10 + gi], n_perm=N.N_PERM)
    N.BAR.verificar_tabla_comparacion(Hg, 'principal', g, pq.dec, N.variable_de_item)
    N.a_csv(Hg, S / f'comparacion_{g}.csv')
    N.a_csv(nl, S / f'nula_comparacion_{g}.csv')
    meta['clases'] = Hg['clase'].value_counts().to_dict() if len(Hg) else {}
    comp.append(meta)
    print('comparación', g, meta, flush=True)
N.a_csv(pd.concat(todas, ignore_index=True), S / 'reglas_grupos_A_B1.csv')
N.a_csv(pd.DataFrame(metas), S / 'resumen_grupos_A_B1.csv')
N.a_csv(pd.DataFrame(comp), S / 'resumen_comparacion_A_B1.csv')
pert = pd.read_csv(N.BASE / 'preparacion' / 'pertenencia_estratos.csv', dtype={'participante_id': str})
filas = []
for g in ('A', 'B1'):
    for dim in N.DIMENSIONES:
        t = pd.crosstab(pert[g], pert[dim])
        for i in t.index:
            for j in t.columns:
                filas.append({'grupo': g, 'etiqueta': int(i), 'dimension': dim, 'estrato': j, 'participantes': int(t.loc[i, j]), 'proporcion_del_grupo': float(t.loc[i, j] / t.loc[i].sum())})
t = pd.crosstab(pert['A'], pert['B1'])
N.a_csv(pd.DataFrame(filas), S / 'composicion_A_B1_por_dimension.csv')
N.a_csv(t.reset_index().rename(columns={'A': 'A \\ B1'}), S / 'cruce_A_B1.csv')
N.registrar('etapa E: A y B1')
print(pd.DataFrame(metas)[['grupo', 'estrato', 'n', 'frecuencia_basal_si', 'largo_maximo', 'reglas', 'marcadas', 'nula_media_marcadas', 'p_exceso_marcadas', 'supera_nula_estrato']].to_string(index=False))
