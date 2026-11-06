"""
Fase 39 (exploratorio, agregado después del sellado; ver protocolo/02_modificaciones_posteriores.md): como ninguna regla supera la nula de su estrato, la tabla
de «diferencias de significación» del protocolo queda vacía. Esta tabla ilustra el problema con la significación nominal: para cada antecedente comparable de las
dimensiones con dos estratos, p de Fisher sin ajuste en cada estrato y prueba de interacción.

Uso, desde la carpeta scripts: python significacion_39.py
"""
import sys

import nucleo_39 as N
import pandas as pd
from scipy.stats import fisher_exact

sys.dont_write_bytecode = True
N.instalar_gancho()
filas, res = [], []
for dim in ('trabajo', 'pareja', 'cuidado'):
    e1, e2 = N.dims_de(dim)
    H = pd.read_csv(N.BASE / 'comparacion' / f'comparacion_{dim}.csv')
    for _, r in H.iterrows():
        p = {}
        for e in (e1, e2):
            p[e] = fisher_exact([[r[f'nAC_{e}'], r[f'nA_{e}'] - r[f'nAC_{e}']], [r[f'nnoAC_{e}'], r[f'nnoA_{e}'] - r[f'nnoAC_{e}']]])[1]
        uno = (p[e1] < 0.05) != (p[e2] < 0.05)
        filas.append({'dimension': dim, 'antecedente': r['antecedente'], f'p_fisher_estrato_1': p[e1], f'p_fisher_estrato_2': p[e2], 'estrato_1': e1, 'estrato_2': e2,
                      'significativa_solo_en_uno': uno, 'p_interaccion_sin_ajuste': r['p_chi2'], 'p_ajustado_dimension': r['p_ajustado_dimension'], 'delta': r['delta']})
    t = pd.DataFrame([f for f in filas if f['dimension'] == dim])
    u = t[t['significativa_solo_en_uno']]
    res.append({'dimension': dim, 'comparables': len(t), 'nominal_en_ambos': int(((t['p_fisher_estrato_1'] < 0.05) & (t['p_fisher_estrato_2'] < 0.05)).sum()),
                'nominal_solo_en_uno': len(u), 'de_ellas_interaccion_p_menor_005_sin_ajuste': int((u['p_interaccion_sin_ajuste'] < 0.05).sum()),
                'de_ellas_superan_nula_dimension': int((u['p_ajustado_dimension'] < 0.05).sum())})
N.a_csv(pd.DataFrame(filas), N.BASE / 'comparacion' / 'significacion_nominal_exploratoria.csv')
N.a_csv(pd.DataFrame(res), N.BASE / 'comparacion' / 'significacion_nominal_resumen.csv')
N.registrar('significación nominal exploratoria')
print(pd.DataFrame(res).to_string(index=False))
