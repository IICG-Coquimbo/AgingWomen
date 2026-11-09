"""
Fase 39R, etapa E (1): sensibilidades de la sección 11 del protocolo histórico, cada una con referencias nulas propias, lectura de cada diferencia marcada de la principal,
dependencia entre antecedentes, grupos pequeños y conclusión mecánica (sección 13).

La condición de ejercicio se evalúa con el texto sellado («mantenerse en S9 o ser evaluable allí»). La lectura estricta, documentada después del sello de la Fase 39, se calcula aparte.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/etapa_e_sensibilidades.py
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import busqueda_39 as B  # noqa: E402
import heterogeneidad_39 as H  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

N.instalar_gancho()
N.huella_sello()
BASE = N.BASE
S = BASE / 'sensibilidades'
pq = N.cargar()
y = pq.d.M['severo_mrs'].to_numpy().astype(int)
masc = N.mascaras(pq)
resumen_r, resumen_h, sup_r, tablas_h = [], [], [], {}
for sens in N.SENSIBILIDADES:
    T, _ = N.base_items(pq, sens)
    estratos = [('trabajo', 'trabaja')] if sens == 'S7a' else [('cuidado', 'cuida')] if sens == 'S7b' else [] if sens == 'S9' else N.ESTRATOS
    Rs, nulas = {}, {}
    for dim, e in estratos:
        c = N.construir(pq, dim, e, sens, T529=T, masc=masc)
        R, nl, meta, _, _ = B.buscar(c, S / 'lotes' / sens / f'{dim}_{e}', [N.SEMILLA, 39, 1000 + 20 * list(N.SENSIBILIDADES).index(sens) + N.NUM_ESTRATO[(dim, e)]], n_perm=N.N_PERM)
        if len(R):
            R = B.clasificar(R)
            N.BAR.verificar_tabla_reglas(R, sens, dim, pq.dec, N.variable_de_item, N.CONSECUENTES)
        Rs[(dim, e)], nulas[(dim, e)] = R, nl
        resumen_r.append({'sensibilidad': sens, 'dimension': dim, 'estrato': e, **{k: v for k, v in meta.items() if k != 'segundos'}})
    if Rs:
        Rs, _ = B.ajuste_conjunto(Rs, nulas)
        for (dim, e), R in Rs.items():
            if len(R):
                N.a_csv(R.drop(columns=['items']), S / 'reglas' / sens / f'reglas_{dim}_{e}.csv')
                for r in R[R['supera_nula_estrato']].itertuples():
                    sup_r.append({'sensibilidad': sens, 'dimension': dim, 'estrato': e, 'antecedente': r.antecedente, 'consecuente': r.consecuente, 'n': r.n,
                                  'n_antecedente': r.n_antecedente, 'n_conjunto': r.n_conjunto, 'confianza': r.confianza, 'frecuencia_basal': r.frecuencia_basal,
                                  'p_ajustado_estrato': r.p_ajustado_estrato, 'p_ajustado_conjunto': r.p_ajustado_conjunto, 'redundante': r.redundante,
                                  'proxima_a_sintomas': r.proxima_a_sintomas, 'incluye_modulo': r.incluye_modulo})
    if sens in ('S7a', 'S7b', 'S4-2'):
        resumen_h.append({'sensibilidad': sens, 'grupo': 'todas', 'nota': 'no aplica' if sens != 'S4-2' else 'igual a la principal (comparación ya limitada a 2 condiciones)'})
    else:
        dims = ['ejercicio'] if sens == 'S9' else list(N.DIMENSIONES)
        Hs, nulas_h = {}, {}
        for dim in dims:
            est = ['0_dias', '1-2_dias'] if sens == 'S9' else N.dims_de(dim)
            comp = N.UMBRALES.get(sens, N.UMBRALES['principal'])[4]
            Hd, nl, meta = H.comparar(T, y, masc, dim, est, comp, 1 if sens == 'S4-1' else 2, S / 'lotes_comparacion' / sens / dim,
                                      [N.SEMILLA, 39, 2000 + 10 * list(N.SENSIBILIDADES).index(sens) + N.NUM_DIM[dim]], [N.SEMILLA, 39, 3, N.NUM_DIM[dim]], n_perm=N.N_PERM, con_estabilidad=False)
            N.BAR.verificar_tabla_comparacion(Hd, sens, dim, pq.dec, N.variable_de_item)
            Hs[dim], nulas_h[dim] = Hd, nl
            resumen_h.append({'sensibilidad': sens, **meta})
        if sens != 'S9':
            Hs, _ = H.ajuste_conjunto(Hs, nulas_h)
        for dim, Hd in Hs.items():
            N.a_csv(Hd, S / 'comparacion' / sens / f'comparacion_{dim}.csv')
            tablas_h[(sens, dim)] = Hd
    print(sens, 'listo', flush=True)
RR = pd.DataFrame(resumen_r)
N.a_csv(RR, S / 'resumen_sensibilidades_estratos.csv')
N.a_csv(pd.DataFrame(resumen_h), S / 'resumen_sensibilidades_comparacion.csv')
N.a_csv(pd.DataFrame(sup_r, columns=['sensibilidad', 'dimension', 'estrato', 'antecedente', 'consecuente', 'n', 'n_antecedente', 'n_conjunto', 'confianza',
                                     'frecuencia_basal', 'p_ajustado_estrato', 'p_ajustado_conjunto', 'redundante', 'proxima_a_sintomas', 'incluye_modulo']),
        S / 'reglas_superan_nula_sensibilidades.csv')

# lectura de las diferencias marcadas de la principal
lect = []
for dim in N.DIMENSIONES:
    P = pd.read_csv(BASE / 'comparacion' / f'comparacion_{dim}.csv')
    P = P[P['marcada']]
    for sens in N.SENSIBILIDADES:
        if (sens, dim) not in tablas_h:
            continue
        Sx = tablas_h[(sens, dim)].set_index('antecedente')
        est = ['0_dias', '1-2_dias'] if sens == 'S9' else N.dims_de(dim)
        for _, r in P.iterrows():
            f = {'sensibilidad': sens, 'dimension': dim, 'antecedente': r['antecedente'], 'clase_principal': r['clase'], 'rango_principal': r['rango_DR']}
            if r['antecedente'] not in Sx.index:
                f['lectura'] = 'no evaluable'
            else:
                s = Sx.loc[r['antecedente']]
                dp = np.array([r[f'DR_{e}'] for e in est])
                ds = np.array([s[f'DR_{e}'] for e in est])
                o = (lambda x: np.sign(x[0] - x[1]) if len(x) == 2 else (np.argmax(x), np.argmin(x)))
                rs = ds.max() - ds.min()
                f.update({'rango_sensibilidad': rs, 'supera_nula_sensibilidad': bool(s['supera_nula_dimension'])})
                f['lectura'] = ('se mantiene' if rs >= N.DIF_HET else 'se debilita') if o(dp) == o(ds) else 'cambia de dirección'
            lect.append(f)
L = pd.DataFrame(lect)
N.a_csv(L, S / 'lectura_comparaciones_principal.csv')
N.a_csv(L.groupby(['dimension', 'sensibilidad', 'lectura']).size().unstack(fill_value=0).reset_index(), S / 'lectura_comparaciones_resumen.csv')

# dependencia entre antecedentes y grupos pequeños
IE = pd.read_csv(BASE / 'preparacion' / 'items_por_estrato.csv')
dep = []
for dim in N.DIMENSIONES:
    t = IE[IE['grupo'] == dim].pivot(index='item', columns='estrato', values='prevalencia')
    for it, r in t.iterrows():
        dep.append({'dimension': dim, 'item': it, **{f'prevalencia_{e}': r[e] for e in t.columns}, 'diferencia_max': float(r.max() - r.min()),
                    'composicion_distinta': float(r.max() - r.min()) >= N.COMPOSICION})
N.a_csv(pd.DataFrame(dep), S / 'dependencia_items_estratos.csv')
peq = []
for dim in N.DIMENSIONES:
    P = pd.read_csv(BASE / 'comparacion' / f'comparacion_{dim}.csv')
    nmin = P[[f'nA_{e}' for e in N.dims_de(dim)]].min(axis=1)
    for nombre, sub in (('todas las comparables', P), ('marcadas', P[P['marcada']]), ('marcadas no redundantes', P[P['marcada'] & ~P['redundante']])):
        nm = nmin.loc[sub.index]
        peq.append({'dimension': dim, 'conjunto': nombre, 'comparaciones': len(sub), 'con_menos_de_30_en_algun_estrato': int((nm < 30).sum()),
                    'composicion_distinta': int(sub['composicion_distinta'].sum()), 'mayor_Q': float(sub['Q'].max()) if len(sub) else np.nan,
                    'mayor_Q_con_menos_de_30': float(sub.loc[nm < 30, 'Q'].max()) if (nm < 30).any() else np.nan})
N.a_csv(pd.DataFrame(peq), S / 'grupos_pequenos_comparaciones.csv')

# conclusión mecánica (sección 13)
Hp = {dim: pd.read_csv(BASE / 'comparacion' / f'comparacion_{dim}.csv') for dim in N.DIMENSIONES}
detalle = []
for dim, Hd in Hp.items():
    for _, r in Hd[Hd['clase'].str.startswith('H5')].iterrows():
        lx = L[(L['dimension'] == dim) & (L['antecedente'] == r['antecedente'])].set_index('sensibilidad')['lectura']
        nuc = [lx.get(s, 'no evaluable') for s in N.NUCLEO_SENS]
        evaluables = [x for x in nuc if x != 'no evaluable']
        s9 = lx.get('S9', 'no evaluable')
        cond1 = bool(r['supera_nula_conjunta'])
        cond2 = len(evaluables) >= 3 and all(x == 'se mantiene' for x in evaluables)
        cond3_sellada = dim != 'ejercicio' or s9 != 'no evaluable'
        cond3_estricta = dim != 'ejercicio' or s9 == 'se mantiene'
        detalle.append({'dimension': dim, 'antecedente': r['antecedente'], 'supera_nula_conjunta': cond1, 'lecturas_nucleo': dict(zip(N.NUCLEO_SENS, nuc)), 'evaluables_nucleo': len(evaluables),
                        'mantiene_en_nucleo': cond2, 'lectura_S9': s9, 'consistente': bool(cond1 and cond2 and cond3_sellada), 'consistente_lectura_estricta_S9': bool(cond1 and cond2 and cond3_estricta)})
TODAS = pd.read_csv(BASE / 'reglas' / 'reglas_todos_estratos.csv')
clase5_conj = TODAS[TODAS['clase'].str.startswith('5') & TODAS['supera_nula_conjunta']]
n_cons = sum(c['consistente'] for c in detalle)
n_estr = sum(c['consistente_lectura_estricta_S9'] for c in detalle)
resultado = 'A' if n_cons else ('B' if len(clase5_conj) else 'C')
resultado_estricto = 'A' if n_estr else ('B' if len(clase5_conj) else 'C')
conc = {'diferencias_H5': len(detalle), 'diferencias_consistentes': n_cons, 'diferencias_consistentes_lectura_estricta_S9': n_estr, 'reglas_clase5': int(TODAS['clase'].str.startswith('5').sum()),
        'reglas_clase5_que_superan_nula_conjunta': len(clase5_conj), 'reglas_superan_nula_estrato': int(TODAS['supera_nula_estrato'].sum()), 'reglas_superan_nula_conjunta': int(TODAS['supera_nula_conjunta'].sum()),
        'comparaciones_superan_nula_dimension': int(sum(Hd['supera_nula_dimension'].sum() for Hd in Hp.values())), 'comparaciones_superan_nula_conjunta': int(sum(Hd['supera_nula_conjunta'].sum() for Hd in Hp.values())),
        'resultado': resultado, 'resultado_lectura_estricta_S9': resultado_estricto, 'la_lectura_de_S9_cambia_el_resultado': resultado != resultado_estricto,
        'texto': {'A': 'Existen diferencias entre subpoblaciones que se mantienen bajo los controles definidos.',
                  'B': 'Existen asociaciones dentro de determinados estratos, pero no evidencia suficiente de que difieran entre estratos.',
                  'C': 'Las asociaciones son débiles o compatibles con el azar y no se identifican diferencias suficientemente consistentes.'}[resultado],
        'detalle_H5': detalle}
N.a_json(conc, BASE / 'resultados' / 'conclusion_39R.json')
N.registrar('etapa E: sensibilidades y conclusión')
print(RR.groupby('sensibilidad')[['reglas', 'marcadas', 'supera_nula_estrato']].sum().to_string())
print(pd.DataFrame(resumen_h).to_string())
print(conc)
