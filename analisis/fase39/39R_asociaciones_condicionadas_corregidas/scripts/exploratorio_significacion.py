"""
Fase 39R, EXPLORATORIO. Reproduce la tabla agregada a la Fase 39 después de su sello (02_modificaciones_posteriores.md, punto 3): p de Fisher sin ajuste en cada estrato y prueba de interacción,
para cada antecedente comparable de las dimensiones con dos estratos. No interviene en ninguna clase ni en la conclusión. Escribe en una carpeta aparte, rotulada como exploratoria.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/exploratorio_significacion.py
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import fisher_exact  # noqa: E402

N.instalar_gancho()
N.huella_sello()
filas, res = [], []
for dim in ('trabajo', 'pareja', 'cuidado'):
    e1, e2 = N.dims_de(dim)
    H = pd.read_csv(N.BASE / 'comparacion' / f'comparacion_{dim}.csv')
    for _, r in H.iterrows():
        p = {}
        for e in (e1, e2):
            p[e] = fisher_exact([[r[f'nAC_{e}'], r[f'nA_{e}'] - r[f'nAC_{e}']], [r[f'nnoAC_{e}'], r[f'nnoA_{e}'] - r[f'nnoAC_{e}']]])[1]
        uno = (p[e1] < 0.05) != (p[e2] < 0.05)
        filas.append({'dimension': dim, 'antecedente': r['antecedente'], 'p_fisher_estrato_1': p[e1], 'p_fisher_estrato_2': p[e2], 'estrato_1': e1, 'estrato_2': e2,
                      'significativa_solo_en_uno': uno, 'p_interaccion_sin_ajuste': r['p_chi2'], 'p_ajustado_dimension': r['p_ajustado_dimension'], 'delta': r['delta']})
    t = pd.DataFrame([f for f in filas if f['dimension'] == dim])
    u = t[t['significativa_solo_en_uno']]
    res.append({'dimension': dim, 'comparables': len(t), 'nominal_en_ambos': int(((t['p_fisher_estrato_1'] < 0.05) & (t['p_fisher_estrato_2'] < 0.05)).sum()),
                'nominal_solo_en_uno': len(u), 'de_ellas_interaccion_p_menor_005_sin_ajuste': int((u['p_interaccion_sin_ajuste'] < 0.05).sum()),
                'de_ellas_superan_nula_dimension': int((u['p_ajustado_dimension'] < 0.05).sum())})
X = N.BASE / 'exploratorio_posterior_al_sello'
N.a_csv(pd.DataFrame(filas), X / 'significacion_nominal_exploratoria.csv')
N.a_csv(pd.DataFrame(res), X / 'significacion_nominal_resumen.csv')
N.registrar('exploratorio: significación nominal')
print(pd.DataFrame(res).to_string(index=False))
