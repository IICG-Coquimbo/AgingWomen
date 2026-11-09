"""
Fase 38R, etapa C: pruebas, comparaciones múltiples, referencia nula (1.000 permutaciones, semilla 42), estabilidad, reclasificación y las 15 sensibilidades.
Reutiliza sin modificar la evaluación histórica. Las barreras se aplican a cada tabla de reglas antes de guardarla.

Uso, desde la carpeta scripts: python -B etapa_c_robustez.py
"""
import sys

sys.dont_write_bytecode = True
import nucleo_38r as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

G, EV, H = N.G, N.EV, N.H
N.instalar_gancho()
sello = N.huella_sello()
B = N.BASE
S = B / 'sensibilidades'
pq = N.cargar()
c = N.construir(pq, 'principal')

# ---- principal
R, nula, E, F, Sb, meta, frec, det = EV.evaluar(c, B / 'referencia_nula' / 'principal', con_estabilidad=True)
N.B.verificar_reglas(R, N.variable_de_item, c.autorizadas, N.CONSECUENTES)
N.a_csv(R.drop(columns=['items']), B / 'reglas' / 'reglas_principal.csv')
N.a_csv(nula, B / 'referencia_nula' / 'nula_principal.csv')
N.a_csv(E, B / 'estabilidad' / 'estabilidad_reglas.csv')
N.a_csv(F, B / 'estabilidad' / 'estabilidad_familias.csv')
N.a_csv(Sb, B / 'estabilidad' / 'submuestras.csv')
sol = R[R['clase'].str.startswith('6')].sort_values('z', key=abs, ascending=False)
cols = ['antecedente', 'consecuente', 'largo', 'n_antecedente', 'n_conjunto', 'soporte', 'confianza', 'ic_confianza_inf', 'ic_confianza_sup', 'frecuencia_basal', 'lift', 'diferencia_basal', 'diferencia_riesgo', 'ic_dr_inf', 'ic_dr_sup',
        'razon_riesgos', 'leverage', 'p_fisher', 'q_bh_todas', 'p_ajustado_busqueda', 'reaparece_marcada', 'misma_direccion', 'mejora_sobre_subreglas', 'subregla_mas_cercana', 'clase']
N.a_csv(sol[cols], B / 'reglas' / 'reglas_destacadas.csv')
no_red = R[~R['redundante'].fillna(False).astype(bool)]
top = pd.concat([no_red[no_red['consecuente'] == cc].sort_values('z', key=abs, ascending=False).head(10) for cc in N.CONSECUENTES])
N.a_csv(top[cols], B / 'reglas' / 'reglas_no_destacadas_mayor_z.csv')
cob = []
for nombre_conj, mask in (('todas las reglas', np.ones(len(R), bool)), ('marcadas', R['marcada'].to_numpy()), ('marcadas no redundantes', (R['marcada'] & ~R['redundante'].fillna(False).astype(bool)).to_numpy()),
                          ('superan la referencia nula', R['supera_nula'].to_numpy()), ('sólidas (clase 6)', R['clase'].str.startswith('6').to_numpy())):
    for cc in N.CONSECUENTES:
        sub = R[mask & (R['consecuente'] == cc).to_numpy()]
        if len(sub):
            A = G.matriz_antecedentes(c.T, [frozenset(i) for i in sub['items']])
            cubre = A.any(axis=0)
            cob.append({'conjunto': nombre_conj, 'consecuente': cc, 'reglas': len(sub), 'participantes_cubiertas': int(cubre.sum()), 'cobertura': float(cubre.mean()), 'confianza_media': float(sub['confianza'].mean()),
                        'confianza_maxima': float(sub['confianza'].max()), 'lift_maximo': float(sub['lift'].max())})
        else:
            cob.append({'conjunto': nombre_conj, 'consecuente': cc, 'reglas': 0, 'participantes_cubiertas': 0, 'cobertura': 0.0, 'confianza_media': np.nan, 'confianza_maxima': np.nan, 'lift_maximo': np.nan})
N.a_csv(pd.DataFrame(cob), B / 'reglas' / 'cobertura.csv')
N.a_csv(R.groupby(['clase', 'consecuente']).size().unstack(fill_value=0).reset_index(), B / 'reglas' / 'clases_principal.csv')
red = R[R['redundante'].fillna(False).astype(bool) & R['marcada']]
N.a_csv(red[['antecedente', 'consecuente', 'confianza', 'subregla_mas_cercana', 'mejora_sobre_subreglas', 'familia']], B / 'reglas' / 'redundantes_marcadas.csv')
fam = R[R['marcada']].groupby('familia').agg(reglas=('antecedente', 'size'), redundantes=('redundante', 'sum'), confianza_max=('confianza', 'max'), supera_nula=('supera_nula', 'sum')).reset_index().sort_values('reglas', ascending=False)
N.a_csv(fam, B / 'reglas' / 'familias_marcadas.csv')
# Convicción: no es una métrica del protocolo histórico. Anexo descriptivo pedido en la instrucción de la 38R; no interviene en ninguna clasificación.
conv = R[['antecedente', 'consecuente', 'confianza', 'frecuencia_basal']].copy()
conv['conviccion'] = np.where(conv['confianza'] >= 1, np.inf, (1 - conv['frecuencia_basal']) / (1 - conv['confianza']))
N.a_csv(conv, B / 'reglas' / 'conviccion_descriptiva_anexo.csv')
meta['sello_protocolo'] = sello['sha256']
meta['clases'] = R['clase'].value_counts().to_dict()
meta['destacadas'] = len(sol)
N.a_json(meta, B / 'reglas' / 'resumen_principal.json')
N.registrar('etapa C principal')
print({k: v for k, v in meta.items() if k != 'items_constantes_quitados'}, flush=True)

# ---- sensibilidades
P = R.drop(columns=['items']).copy()
P['items'] = P['antecedente'].str.split(' & ')
marcadas = P[P['marcada']].reset_index(drop=True)
resumen, lectura, clases, sup = [], [], [], []
for nombre in N.CONFIGS:
    if nombre == 'principal':
        continue
    x = N.construir(pq, nombre)
    Rs, nu, _, _, _, m_, fr, de = EV.evaluar(x, S / 'lotes' / nombre, soporte_principal=53 if nombre == 'S3-bajo' else None)
    N.B.verificar_reglas(Rs, N.variable_de_item, x.autorizadas, N.CONSECUENTES)
    N.a_csv(Rs.drop(columns=['items']), S / 'reglas' / f'reglas_{nombre}.csv')
    N.a_csv(nu, S / 'nula' / f'nula_{nombre}.csv')
    m_['historica_equivalente'] = N.HISTORICA[nombre] or ''
    resumen.append(m_)
    if len(Rs):
        clases.append({'configuracion': nombre, **Rs.groupby('clase').size().to_dict()})
        for r in Rs[Rs['supera_nula']].itertuples():
            sup.append({'configuracion': nombre, 'antecedente': r.antecedente, 'consecuente': r.consecuente, 'n': r.n, 'n_antecedente': r.n_antecedente, 'confianza': r.confianza, 'frecuencia_basal': r.frecuencia_basal,
                        'diferencia_basal': r.diferencia_basal, 'p_ajustado_busqueda': r.p_ajustado_busqueda, 'redundante': r.redundante, 'clase': r.clase})
    cols_x = set(x.T.columns)
    evaluables = [i for i, it in enumerate(marcadas['items']) if set(it) <= cols_x and len(it) <= x.largo]
    A = G.matriz_antecedentes(x.T, [frozenset(marcadas.at[i, 'items']) for i in evaluables]) if evaluables else np.zeros((0, x.n), np.uint8)
    nA, k_si = A.sum(axis=1), A.astype(np.int64) @ x.y
    p0 = x.n_si / x.n
    en_R = dict(zip(Rs['antecedente'], zip(Rs['consecuente'], Rs['supera_nula'], Rs['clase']))) if len(Rs) else {}
    pos = {i: j for j, i in enumerate(evaluables)}
    for i, r in marcadas.iterrows():
        fila = {'configuracion': nombre, 'antecedente': r['antecedente'], 'consecuente_principal': r['consecuente'], 'diferencia_principal': r['diferencia_basal'], 'n_antecedente': np.nan, 'confianza': np.nan, 'diferencia_basal': np.nan, 'supera_nula': np.nan, 'clase': ''}
        if i not in pos:
            fila['lectura'] = 'no evaluable'
        else:
            j = pos[i]
            n_a, ks = int(nA[j]), int(k_si[j])
            conf_si = ks / n_a if n_a else np.nan
            si = r['consecuente'] == N.CONSECUENTES[0]
            conf = conf_si if si else 1 - conf_si
            base = p0 if si else 1 - p0
            dif = conf - base
            fila.update({'n_antecedente': n_a, 'confianza': conf, 'diferencia_basal': dif})
            if n_a < x.min_ant:
                fila['lectura'] = 'desaparece por falta de casos'
            elif dif < 0:
                fila['lectura'] = 'cambia de dirección'
            elif dif >= H.DIF_MARCADA and (conf * n_a) >= x.min_conj:
                fila['lectura'] = 'se mantiene'
            else:
                fila['lectura'] = 'se debilita'
            if r['antecedente'] in en_R:
                fila['supera_nula'], fila['clase'] = en_R[r['antecedente']][1], en_R[r['antecedente']][2]
        lectura.append(fila)
    print(nombre, {k: v for k, v in m_.items() if k in ('n', 'items', 'reglas', 'marcadas', 'nula_media_marcadas', 'nula_p95_marcadas', 'supera_nula', 'segundos')}, flush=True)
L = pd.DataFrame(lectura)
N.a_csv(L, S / 'lectura_reglas_principal.csv')
N.a_csv(L.groupby(['configuracion', 'lectura']).size().unstack(fill_value=0).reset_index(), S / 'lectura_resumen.csv')
N.a_csv(pd.DataFrame(resumen).drop(columns=['items_constantes_quitados']), S / 'resumen_sensibilidades.csv')
N.a_csv(pd.DataFrame(clases).fillna(0), S / 'clases_sensibilidades.csv')
N.a_csv(pd.DataFrame(sup, columns=['configuracion', 'antecedente', 'consecuente', 'n', 'n_antecedente', 'confianza', 'frecuencia_basal', 'diferencia_basal', 'p_ajustado_busqueda', 'redundante', 'clase']), S / 'superan_nula_sensibilidades.csv')
N.registrar('etapa C sensibilidades')
print(pd.DataFrame(sup)[['configuracion', 'antecedente', 'consecuente', 'n_antecedente', 'confianza', 'p_ajustado_busqueda', 'redundante', 'clase']].to_string() if sup else 'ninguna regla supera la nula en las sensibilidades')
