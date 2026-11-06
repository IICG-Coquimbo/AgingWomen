"""
Fase 38: sensibilidades S1-S8 (FP-Growth, 1.000 permutaciones propias por configuración) y lectura de cada regla marcada de la principal en cada una.

Uso, desde la carpeta scripts: python sensibilidades_38.py
"""
import sys

import algoritmos_38 as G
import evaluacion_38 as EV
import nucleo_38 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
N.instalar_gancho()
N.huella_sello()
B = N.BASE
S = B / 'sensibilidades'
d = N.cargar()
P = pd.read_csv(B / 'reglas' / 'reglas_principal.csv')
P['items'] = P['antecedente'].str.split(' & ')
marcadas = P[P['marcada']].reset_index(drop=True)
resumen, lectura, clases = [], [], []
for nombre in N.CONFIGS:
    if nombre == 'principal':
        continue
    c = N.construir(d, nombre)
    R, nula, _, _, _, meta, frec, det = EV.evaluar(c, S / 'lotes' / nombre, soporte_principal=53 if nombre == 'S3-bajo' else None)
    N.a_csv(R.drop(columns=['items']), S / 'reglas' / f'reglas_{nombre}.csv')
    N.a_csv(nula, S / 'nula' / f'nula_{nombre}.csv')
    resumen.append(meta)
    if len(R):
        k = R.groupby('clase').size()
        clases.append({'configuracion': nombre, **k.to_dict()})
    # lectura de las reglas marcadas de la principal
    cols = set(c.T.columns)
    evaluables = [i for i, it in enumerate(marcadas['items']) if set(it) <= cols and len(it) <= c.largo]
    A = G.matriz_antecedentes(c.T, [frozenset(marcadas.at[i, 'items']) for i in evaluables]) if evaluables else np.zeros((0, c.n), np.uint8)
    nA = A.sum(axis=1)
    k_si = A.astype(np.int64) @ c.y
    p0 = c.n_si / c.n
    en_R = dict(zip(R['antecedente'], zip(R['consecuente'], R['supera_nula'], R['clase']))) if len(R) else {}
    pos = {i: j for j, i in enumerate(evaluables)}
    for i, r in marcadas.iterrows():
        fila = {'configuracion': nombre, 'antecedente': r['antecedente'], 'consecuente_principal': r['consecuente'], 'diferencia_principal': r['diferencia_basal'],
                'n_antecedente': np.nan, 'confianza': np.nan, 'diferencia_basal': np.nan, 'supera_nula': np.nan, 'clase': ''}
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
            if n_a < c.min_ant:
                fila['lectura'] = 'desaparece por falta de casos'
            elif dif < 0:
                fila['lectura'] = 'cambia de dirección'
            elif dif >= N.DIF_MARCADA and (conf * n_a) >= c.min_conj:
                fila['lectura'] = 'se mantiene'
            else:
                fila['lectura'] = 'se debilita'
            if r['antecedente'] in en_R:
                fila['supera_nula'], fila['clase'] = en_R[r['antecedente']][1], en_R[r['antecedente']][2]
        lectura.append(fila)
    print(nombre, {k: v for k, v in meta.items() if k in ('n', 'items', 'reglas', 'marcadas', 'nula_media_marcadas', 'nula_p95_marcadas', 'supera_nula', 'segundos')}, flush=True)
L = pd.DataFrame(lectura)
N.a_csv(L, S / 'lectura_reglas_principal.csv')
tab = L.groupby(['configuracion', 'lectura']).size().unstack(fill_value=0).reset_index()
N.a_csv(tab, S / 'lectura_resumen.csv')
M = pd.DataFrame(resumen)
N.a_csv(M.drop(columns=['items_constantes_quitados']), S / 'resumen_sensibilidades.csv')
N.a_csv(pd.DataFrame(clases).fillna(0), S / 'clases_sensibilidades.csv')
# reglas que superan la nula en alguna sensibilidad
sup = []
for nombre in N.CONFIGS:
    if nombre == 'principal':
        continue
    R = pd.read_csv(S / 'reglas' / f'reglas_{nombre}.csv')
    for r in R[R['supera_nula']].itertuples():
        sup.append({'configuracion': nombre, 'antecedente': r.antecedente, 'consecuente': r.consecuente, 'n': r.n, 'n_antecedente': r.n_antecedente,
                    'confianza': r.confianza, 'frecuencia_basal': r.frecuencia_basal, 'diferencia_basal': r.diferencia_basal, 'p_ajustado_busqueda': r.p_ajustado_busqueda,
                    'redundante': r.redundante, 'clase': r.clase})
N.a_csv(pd.DataFrame(sup, columns=['configuracion', 'antecedente', 'consecuente', 'n', 'n_antecedente', 'confianza', 'frecuencia_basal', 'diferencia_basal',
                                   'p_ajustado_busqueda', 'redundante', 'clase']), S / 'superan_nula_sensibilidades.csv')
N.registrar('sensibilidades')
print(tab.to_string(index=False))
print(pd.DataFrame(sup).to_string() if sup else 'ninguna regla supera la nula en las sensibilidades')
