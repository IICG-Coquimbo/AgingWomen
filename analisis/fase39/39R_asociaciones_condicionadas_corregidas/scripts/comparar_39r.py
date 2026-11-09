"""
Fase 39R: comparación con la Fase 39 histórica (solo lectura de esta) y barrido final de exclusiones. Escribe en comparacion_historica/.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/comparar_39r.py
"""
import filecmp
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

N.instalar_gancho()
sello = N.huella_sello()
pq = N.cargar()
R, H = N.BASE, N.D39
C = R / 'comparacion_historica'
AJUSTADAS = ('p_ajustado', 'q_bh', 'supera_nula', 'clase')
NO_METRICA = ('antecedente', 'consecuente', 'dimension', 'estrato', 'grupo', 'variables', 'largo')


def leer_reglas(b):
    return pd.read_csv(b / 'reglas' / 'reglas_todos_estratos.csv')


def tiene_retirada(s):
    return any(x in str(s).split(' & ') for x in N.RETIRADAS)


Th, Tr = leer_reglas(H), leer_reglas(R)
Mh, Mr = pd.read_csv(H / 'reglas' / 'resumen_estratos.csv'), pd.read_csv(R / 'reglas' / 'resumen_estratos.csv')


def resumen_reglas(T, M):
    filas = []
    for dim, e in N.ESTRATOS:
        t = T[(T['dimension'] == dim) & (T['estrato'] == e)]
        m = M[(M['dimension'] == dim) & (M['estrato'] == e)].iloc[0]
        red = t['redundante'].fillna(False).astype(bool)
        f = {'dimension': dim, 'estrato': e, 'n': int(m['n']), 'items': int(m['items']), 'antecedentes_evaluados': int(m['antecedentes_evaluados']), 'reglas': len(t), 'hacia_severo': int((t['consecuente'] == N.CONSECUENTES[0]).sum()),
             'hacia_no_severo': int((t['consecuente'] == N.CONSECUENTES[1]).sum()), 'marcadas': int(t['marcada'].sum()), 'marcadas_no_redundantes': int((t['marcada'] & ~red).sum()), 'nula_media_marcadas': float(m['nula_media_marcadas']),
             'nula_p95_marcadas': float(m['nula_p95_marcadas']), 'p_exceso_marcadas': float(m['p_exceso_marcadas']), 'nula_p95_max_z': float(m['nula_p95_max_z']), 'supera_nula_estrato': int(t['supera_nula_estrato'].sum()),
             'supera_nula_conjunta': int(t['supera_nula_conjunta'].sum()), 'estables': int(t['estable'].fillna(False).astype(bool).sum()), 'marcadas_media_submuestra': float(m['marcadas_media_sub'])}
        for k in '12345':
            f[f'clase_{k}'] = int(t['clase'].str.startswith(k).sum())
        filas.append(f)
    return pd.DataFrame(filas)


rh, rr = resumen_reglas(Th, Mh), resumen_reglas(Tr, Mr)
por = rh.merge(rr, on=['dimension', 'estrato', 'n'], suffixes=('_39', '_39R'))
N.a_csv(por, C / 'comparacion_por_estrato.csv')
tot = {}
for col in ('reglas', 'hacia_severo', 'hacia_no_severo', 'marcadas', 'marcadas_no_redundantes', 'supera_nula_estrato', 'supera_nula_conjunta', 'estables', 'clase_1', 'clase_2', 'clase_3', 'clase_4', 'clase_5'):
    tot[col] = {'fase_39': int(rh[col].sum()), 'fase_39R': int(rr[col].sum())}

# reglas conservadas por estrato
cl = ['dimension', 'estrato', 'antecedente', 'consecuente']
m = Th.merge(Tr, on=cl, how='outer', suffixes=('_39', '_39R'), indicator=True)
ret_h = m['_merge'].eq('left_only') & m['variables_39'].map(lambda s: tiene_retirada(s))
perd = m['_merge'].eq('left_only') & ~ret_h
nuevas = m['_merge'].eq('right_only')
cons = m[m['_merge'] == 'both']
metricas = [c for c in Th.columns if c in Tr.columns and c not in cl and c not in NO_METRICA and not c.startswith(AJUSTADAS) and pd.api.types.is_numeric_dtype(Th[c]) and pd.api.types.is_numeric_dtype(Tr[c])]
dif = {}
for c in metricas:
    a, b = cons[f'{c}_39'].astype(float), cons[f'{c}_39R'].astype(float)
    dif[c] = int((~(np.isclose(a, b, rtol=1e-12, atol=1e-12) | (a.isna() & b.isna()))).sum())
filas = []
for (dim, e), g in m.groupby(['dimension', 'estrato']):
    i = g.index
    filas.append({'dimension': dim, 'estrato': e, 'reglas_39': int(g['_merge'].isin(['left_only', 'both']).sum()), 'retiradas_por_variable_excluida': int(ret_h.loc[i].sum()), 'conservadas': int((g['_merge'] == 'both').sum()), 'perdidas_sin_variable_excluida': int(perd.loc[i].sum()), 'nuevas': int(nuevas.loc[i].sum())})
N.a_csv(pd.DataFrame(filas), C / 'reglas_conservadas_por_estrato.csv')
N.a_csv(pd.DataFrame([{'metrica': k, 'reglas_conservadas_con_diferencia': v} for k, v in dif.items()]), C / 'metricas_reglas_conservadas.csv')
trans = cons.groupby(['clase_39', 'clase_39R']).size().reset_index(name='reglas')
N.a_csv(trans, C / 'transiciones_clase_reglas.csv')
pa, pb = cons['p_ajustado_estrato_39'].astype(float), cons['p_ajustado_estrato_39R'].astype(float)
ca, cb = cons['p_ajustado_conjunto_39'].astype(float), cons['p_ajustado_conjunto_39R'].astype(float)
ajustes = {'conservadas': len(cons), 'p_estrato_iguales': int(np.isclose(pa, pb).sum()), 'p_estrato_bajan': int((pb < pa - 1e-12).sum()), 'p_estrato_suben': int((pb > pa + 1e-12).sum()), 'p_estrato_baja_maxima': float((pa - pb).max()),
           'p_conjunto_iguales': int(np.isclose(ca, cb).sum()), 'p_conjunto_bajan': int((cb < ca - 1e-12).sum()), 'p_conjunto_suben': int((cb > ca + 1e-12).sum()), 'p_conjunto_baja_maxima': float((ca - cb).max()),
           'min_p_estrato_39': float(Th['p_ajustado_estrato'].min()), 'min_p_estrato_39R': float(Tr['p_ajustado_estrato'].min()), 'min_p_conjunto_39': float(Th['p_ajustado_conjunto'].min()), 'min_p_conjunto_39R': float(Tr['p_ajustado_conjunto'].min())}
Ng = {'39': pd.read_csv(H / 'referencia_nula' / 'nula_conjunta_estratos.csv'), '39R': pd.read_csv(R / 'referencia_nula' / 'nula_conjunta_estratos.csv')}
ajustes.update({'nula_conjunta_p95_39': float(Ng['39']['max_z_9_estratos'].quantile(.95)), 'nula_conjunta_p95_39R': float(Ng['39R']['max_z_9_estratos'].quantile(.95)), 'nula_conjunta_nunca_sube': bool((Ng['39R']['max_z_9_estratos'].to_numpy() <= Ng['39']['max_z_9_estratos'].to_numpy() + 1e-12).all())})
top_h = Th.assign(az=Th['z'].abs()).sort_values('az', ascending=False).head(10)[['dimension', 'estrato', 'antecedente', 'consecuente', 'n_antecedente', 'confianza', 'z', 'p_ajustado_estrato', 'p_ajustado_conjunto', 'clase']]
top_r = Tr.assign(az=Tr['z'].abs()).sort_values('az', ascending=False).head(10)[['dimension', 'estrato', 'antecedente', 'consecuente', 'n_antecedente', 'confianza', 'z', 'p_ajustado_estrato', 'p_ajustado_conjunto', 'clase']]
N.a_csv(top_h.assign(fase='39'), C / 'mayor_z_fase39.csv')
N.a_csv(top_r.assign(fase='39R'), C / 'mayor_z_fase39R.csv')

# comparaciones entre estratos
filas, top, trans_h, cons_h = [], [], [], {}
Cmeta = {}
for dim in N.DIMENSIONES:
    a, b = pd.read_csv(H / 'comparacion' / f'comparacion_{dim}.csv'), pd.read_csv(R / 'comparacion' / f'comparacion_{dim}.csv')
    na, nb = pd.read_csv(H / 'comparacion' / f'nula_comparacion_{dim}.csv'), pd.read_csv(R / 'comparacion' / f'nula_comparacion_{dim}.csv')
    x = a.merge(b, on='antecedente', how='outer', suffixes=('_39', '_39R'), indicator=True)
    ret = x['_merge'].eq('left_only') & x['variables_39'].map(lambda s: tiene_retirada(s))
    both = x[x['_merge'] == 'both']
    col_dr = [f'DR_{e}' for e in N.dims_de(dim)] + ['rango_DR', 'Q', 'p_chi2', 'reaparece_marcada', 'misma_direccion']
    difs = sum(int((~np.isclose(both[f'{c}_39'].astype(float), both[f'{c}_39R'].astype(float), rtol=1e-12, atol=1e-12)).sum()) for c in col_dr)
    trans_h.append(both.groupby(['clase_39', 'clase_39R']).size().reset_index(name='comparaciones').assign(dimension=dim))
    filas.append({'dimension': dim, 'candidatos': None, 'comparables_39': len(a), 'comparables_39R': len(b), 'retiradas_por_variable_excluida': int(ret.sum()), 'perdidas_sin_variable_excluida': int((x['_merge'].eq('left_only') & ~ret).sum()), 'nuevas': int(x['_merge'].eq('right_only').sum()),
                  'diferencias_DR_Q_estabilidad_en_conservadas': difs, 'marcadas_39': int(a['marcada'].sum()), 'marcadas_39R': int(b['marcada'].sum()), 'redundantes_39': int(a['redundante'].sum()), 'redundantes_39R': int(b['redundante'].sum()),
                  'H1_39': int(a['clase'].str.startswith('H1').sum()), 'H1_39R': int(b['clase'].str.startswith('H1').sum()), 'H2_39': int(a['clase'].str.startswith('H2').sum()), 'H2_39R': int(b['clase'].str.startswith('H2').sum()),
                  'H3_39': int(a['clase'].str.startswith('H3').sum()), 'H3_39R': int(b['clase'].str.startswith('H3').sum()), 'H4_39': int(a['clase'].str.startswith('H4').sum()), 'H4_39R': int(b['clase'].str.startswith('H4').sum()), 'H5_39': int(a['clase'].str.startswith('H5').sum()), 'H5_39R': int(b['clase'].str.startswith('H5').sum()),
                  'estables_marcadas_39': int((a['marcada'] & a['estable'].fillna(False).astype(bool)).sum()), 'estables_marcadas_39R': int((b['marcada'] & b['estable'].fillna(False).astype(bool)).sum()), 'composicion_distinta_marcadas_39': int((a['marcada'] & a['composicion_distinta']).sum()), 'composicion_distinta_marcadas_39R': int((b['marcada'] & b['composicion_distinta']).sum()),
                  'nula_media_marcadas_39': float(na['marcadas'].mean()), 'nula_media_marcadas_39R': float(nb['marcadas'].mean()), 'p_exceso_39': float(((na['marcadas'] >= a['marcada'].sum()).sum() + 1) / (len(na) + 1)), 'p_exceso_39R': float(((nb['marcadas'] >= b['marcada'].sum()).sum() + 1) / (len(nb) + 1)),
                  'nula_p95_max_Q_39': float(na['max_Q'].quantile(.95)), 'nula_p95_max_Q_39R': float(nb['max_Q'].quantile(.95)), 'mayor_Q_39': float(a['Q'].max()), 'mayor_Q_39R': float(b['Q'].max()), 'mayor_rango_39': float(a['rango_DR'].max()), 'mayor_rango_39R': float(b['rango_DR'].max()),
                  'min_p_dimension_39': float(a['p_ajustado_dimension'].min()), 'min_p_dimension_39R': float(b['p_ajustado_dimension'].min()), 'min_p_conjunto_39': float(a['p_ajustado_conjunto'].min()), 'min_p_conjunto_39R': float(b['p_ajustado_conjunto'].min()),
                  'supera_nula_dimension_39': int(a['supera_nula_dimension'].sum()), 'supera_nula_dimension_39R': int(b['supera_nula_dimension'].sum()), 'supera_nula_conjunta_39': int(a['supera_nula_conjunta'].sum()), 'supera_nula_conjunta_39R': int(b['supera_nula_conjunta'].sum()),
                  'q_bh_minimo_39': float(a['q_bh_dimension'].min()), 'q_bh_minimo_39R': float(b['q_bh_dimension'].min())})
    for fase, t in (('39', a), ('39R', b)):
        cols = ['antecedente', 'rango_DR', 'Q', 'p_chi2', 'q_bh_dimension', 'p_ajustado_dimension', 'p_ajustado_conjunto', 'redundante', 'estable', 'reaparece_marcada', 'composicion_distinta', 'clase'] + [f'DR_{e}' for e in N.dims_de(dim)] + ([] if len(N.dims_de(dim)) != 2 else ['delta', 'delta_inf', 'delta_sup', 'z_interaccion'])
        top.append(t.sort_values('Q', ascending=False).head(5)[cols].assign(dimension=dim, fase=fase))
CH = pd.DataFrame(filas).drop(columns=['candidatos'])
N.a_csv(CH, C / 'comparacion_entre_estratos.csv')
N.a_csv(pd.concat(trans_h, ignore_index=True), C / 'transiciones_clase_comparaciones.csv')
N.a_csv(pd.concat(top, ignore_index=True), C / 'mayores_Q_por_dimension.csv')

# sensibilidades
Sh, Sr = pd.read_csv(H / 'sensibilidades' / 'resumen_sensibilidades_estratos.csv'), pd.read_csv(R / 'sensibilidades' / 'resumen_sensibilidades_estratos.csv')
col = ['sensibilidad', 'dimension', 'estrato']
sm = Sh.merge(Sr, on=col, suffixes=('_39', '_39R'))
N.a_csv(sm, C / 'sensibilidades_por_estrato.csv')
ag = sm.groupby('sensibilidad', sort=False)[['items_39', 'items_39R', 'reglas_39', 'reglas_39R', 'marcadas_39', 'marcadas_39R', 'nula_media_marcadas_39', 'nula_media_marcadas_39R', 'supera_nula_estrato_39', 'supera_nula_estrato_39R']].sum().reset_index()
N.a_csv(ag, C / 'sensibilidades_agregadas.csv')
Hc, Rc = pd.read_csv(H / 'sensibilidades' / 'resumen_sensibilidades_comparacion.csv'), pd.read_csv(R / 'sensibilidades' / 'resumen_sensibilidades_comparacion.csv')
sc = Hc.merge(Rc, on=['sensibilidad', 'grupo'], how='outer', suffixes=('_39', '_39R'))
N.a_csv(sc, C / 'sensibilidades_comparacion.csv')
Sup_h, Sup_r = pd.read_csv(H / 'sensibilidades' / 'reglas_superan_nula_sensibilidades.csv'), pd.read_csv(R / 'sensibilidades' / 'reglas_superan_nula_sensibilidades.csv')
N.a_csv(Sup_h.assign(fase='39'), C / 'superan_nula_sensibilidades_39.csv')
N.a_csv(Sup_r.assign(fase='39R'), C / 'superan_nula_sensibilidades_39R.csv')
Lh, Lr = pd.read_csv(H / 'sensibilidades' / 'lectura_comparaciones_resumen.csv'), pd.read_csv(R / 'sensibilidades' / 'lectura_comparaciones_resumen.csv')
N.a_csv(Lh.assign(fase='39'), C / 'lectura_sensibilidades_39.csv')
N.a_csv(Lr.assign(fase='39R'), C / 'lectura_sensibilidades_39R.csv')
s1 = []
for dim, e in N.ESTRATOS:
    a, b = H / 'sensibilidades' / 'reglas' / 'S1' / f'reglas_{dim}_{e}.csv', R / 'sensibilidades' / 'reglas' / 'S1' / f'reglas_{dim}_{e}.csv'
    s1.append({'dimension': dim, 'estrato': e, 'identico_byte_a_byte': a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False)})
for dim in N.DIMENSIONES:
    a, b = H / 'sensibilidades' / 'comparacion' / 'S1' / f'comparacion_{dim}.csv', R / 'sensibilidades' / 'comparacion' / 'S1' / f'comparacion_{dim}.csv'
    s1.append({'dimension': dim, 'estrato': '(comparación)', 'identico_byte_a_byte': a.exists() and b.exists() and filecmp.cmp(a, b, shallow=False)})
N.a_csv(pd.DataFrame(s1), C / 'S1_identidad_con_historica.csv')

# A y B1
Ah, Ar = pd.read_csv(H / 'ab1' / 'resumen_grupos_A_B1.csv'), pd.read_csv(R / 'ab1' / 'resumen_grupos_A_B1.csv')
N.a_csv(Ah.merge(Ar, on=['grupo', 'estrato', 'n'], suffixes=('_39', '_39R')), C / 'A_B1_grupos.csv')
Bh, Br = pd.read_csv(H / 'ab1' / 'resumen_comparacion_A_B1.csv'), pd.read_csv(R / 'ab1' / 'resumen_comparacion_A_B1.csv')
N.a_csv(Bh.merge(Br, on=['grupo', 'estratos'], suffixes=('_39', '_39R')), C / 'A_B1_comparacion.csv')
ABr = pd.read_csv(R / 'ab1' / 'reglas_grupos_A_B1.csv')
cab = {g: {'supera_nula_grupo': int(ABr[ABr['grupo'] == g]['supera_nula_estrato'].sum()), 'clases': ABr[ABr['grupo'] == g]['clase'].value_counts().to_dict()} for g in ('A', 'B1')}
ABh = pd.read_csv(H / 'ab1' / 'reglas_grupos_A_B1.csv')
pa = {g: {'supera_nula_grupo': int(ABh[ABh['grupo'] == g]['supera_nula_estrato'].sum()), 'clases': ABh[ABh['grupo'] == g]['clase'].value_counts().to_dict()} for g in ('A', 'B1')}

# verificación final de todas las tablas de modelado
dec = pq.dec
v, reglas_verificadas, comp_verificadas = N.variable_de_item, 0, 0
for dim, e in N.ESTRATOS:
    t = pd.read_csv(R / 'reglas' / dim / f'reglas_{e}.csv')
    N.BAR.verificar_tabla_reglas(t, 'principal', dim, dec, v, N.CONSECUENTES)
    reglas_verificadas += 1
for dim in N.DIMENSIONES:
    N.BAR.verificar_tabla_comparacion(pd.read_csv(R / 'comparacion' / f'comparacion_{dim}.csv'), 'principal', dim, dec, v)
    comp_verificadas += 1
for sens in N.SENSIBILIDADES:
    for p in sorted((R / 'sensibilidades' / 'reglas' / sens).glob('reglas_*.csv')) if (R / 'sensibilidades' / 'reglas' / sens).exists() else []:
        dim = next(d for d in N.DIMENSIONES if p.stem.startswith(f'reglas_{d}_'))
        N.BAR.verificar_tabla_reglas(pd.read_csv(p), sens, dim, dec, v, N.CONSECUENTES)
        reglas_verificadas += 1
    for p in sorted((R / 'sensibilidades' / 'comparacion' / sens).glob('comparacion_*.csv')) if (R / 'sensibilidades' / 'comparacion' / sens).exists() else []:
        N.BAR.verificar_tabla_comparacion(pd.read_csv(p), sens, p.stem.replace('comparacion_', ''), dec, v)
        comp_verificadas += 1
for g in ('A', 'B1'):
    N.BAR.verificar_tabla_reglas(ABr[ABr['grupo'] == g], 'principal', g, dec, v, N.CONSECUENTES)
    N.BAR.verificar_tabla_comparacion(pd.read_csv(R / 'ab1' / f'comparacion_{g}.csv'), 'principal', g, dec, v)
    reglas_verificadas += 1
    comp_verificadas += 1

# barrido de texto en todo lo generado
patron = re.compile(r'med_diabetes|prevision|usa_medicamentos_diabetes|doble_carga|fonasa|isapre|ffaa', re.I)
REGISTROS = {'preparacion/verificacion_configuraciones.csv'}
barrido = []
for carpeta in ('preparacion', 'reglas', 'referencia_nula', 'estabilidad', 'comparacion', 'sensibilidades', 'ab1', 'redundancia', 'resultados', 'exploratorio_posterior_al_sello'):
    for p in (R / carpeta).rglob('*'):
        if p.suffix not in ('.csv', '.txt', '.json') or not p.is_file():
            continue
        n = len(patron.findall(p.read_text(encoding='utf-8', errors='replace')))
        barrido.append({'archivo': p.relative_to(R).as_posix(), 'bytes': p.stat().st_size, 'apariciones': n})
BR = pd.DataFrame(barrido)
BR['es_registro_de_retirada'] = BR['archivo'].isin(REGISTROS)
N.a_csv(BR, C / 'barrido_exclusiones.csv')
conc_r = N.leer_json(R / 'resultados' / 'conclusion_39R.json')
conc_h = N.leer_json(H / 'resultados' / 'conclusion_39.json')
info = {'sello_protocolo': sello['sha256'], 'totales_reglas': tot, 'filas_conservadas': len(cons), 'reglas_retiradas': int(ret_h.sum()), 'reglas_perdidas_sin_variable_excluida': int(perd.sum()), 'reglas_nuevas': int(nuevas.sum()), 'metricas_comparadas': len(dif), 'filas_con_diferencia_en_metricas': int(sum(dif.values())),
        'reglas_cambian_de_clase': int(trans.loc[trans['clase_39'] != trans['clase_39R'], 'reglas'].sum()), 'ajustes': ajustes, 'A_B1': {'fase_39': pa, 'fase_39R': cab}, 'tablas_reglas_verificadas': reglas_verificadas, 'tablas_comparacion_verificadas': comp_verificadas,
        'archivos_barridos': len(BR), 'apariciones_en_resultados': int(BR.loc[~BR['es_registro_de_retirada'], 'apariciones'].sum()), 'S1_identica_a_historica': bool(pd.DataFrame(s1)['identico_byte_a_byte'].all()),
        'conclusion_39': {k: conc_h[k] for k in ('resultado', 'diferencias_H5', 'diferencias_consistentes', 'reglas_clase5', 'reglas_superan_nula_estrato', 'comparaciones_superan_nula_dimension')}, 'conclusion_39R': {k: conc_r[k] for k in ('resultado', 'resultado_lectura_estricta_S9', 'la_lectura_de_S9_cambia_el_resultado', 'diferencias_H5', 'diferencias_consistentes', 'reglas_clase5', 'reglas_clase5_que_superan_nula_conjunta', 'reglas_superan_nula_estrato', 'reglas_superan_nula_conjunta', 'comparaciones_superan_nula_dimension', 'comparaciones_superan_nula_conjunta')}}
N.a_json(info, C / 'resumen_comparacion.json')
N.registrar('comparación con la Fase 39')
print(info)
print(CH.T.to_string())
