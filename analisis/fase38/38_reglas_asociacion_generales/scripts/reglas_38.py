"""
Fase 38: análisis principal. Equivalencia Apriori / FP-Growth / exhaustiva (tiempo y memoria), reglas, redundancia, referencia nula, estabilidad y clasificación.

Uso, desde la carpeta scripts: python reglas_38.py
"""
import platform
import sys
import time
import tracemalloc

import algoritmos_38 as G
import evaluacion_38 as EV
import nucleo_38 as N
import numpy as np
import pandas as pd
import scipy

sys.dont_write_bytecode = True
N.instalar_gancho()
sello = N.huella_sello()
B = N.BASE
d = N.cargar()
c = N.construir(d, 'principal')

# ---- equivalencia
eq, resultados = [], {}
for nombre in ('apriori', 'fpgrowth', 'exhaustiva'):
    t = time.perf_counter()
    f = EV.descubrir(c, algoritmo=nombre)
    seg = time.perf_counter() - t
    tracemalloc.start()
    EV.descubrir(c, algoritmo=nombre)
    pico = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    resultados[nombre] = f
    det = N.pares_determinados(c.T)
    R_ = G.reglas(f, c.n, c.n_si, c.min_ant, c.min_conj, det)
    eq.append({'algoritmo': nombre, 'conjuntos_frecuentes': len(f), 'reglas': len(R_), 'segundos': round(seg, 2), 'memoria_pico_mb': round(pico / 2 ** 20, 1),
               'minsup_absoluto': c.min_conj, 'largo_maximo_antecedente': c.largo})
    resultados[nombre + '_reglas'] = R_
EQ = pd.DataFrame(eq)
comp = []
for a, b in (('apriori', 'fpgrowth'), ('apriori', 'exhaustiva'), ('fpgrowth', 'exhaustiva')):
    igual, dif = G.iguales(resultados[a], resultados[b])
    ra, rb = resultados[a + '_reglas'], resultados[b + '_reglas']
    reglas_iguales = ra[['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']].equals(rb[['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']])
    comp.append({'comparacion': f'{a} frente a {b}', 'mismos_conjuntos_y_recuentos': igual, 'diferencias': dif, 'mismas_reglas': reglas_iguales})
CMP = pd.DataFrame(comp)
N.a_csv(EQ, B / 'reglas' / 'equivalencia_algoritmos.csv')
N.a_csv(CMP, B / 'reglas' / 'equivalencia_comparaciones.csv')
N.a_json({'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__, 'sistema': platform.platform(),
          'implementacion': 'Apriori, FP-Growth y enumeración exhaustiva propios (scripts/algoritmos_38.py); mlxtend no instalado y no se instala',
          'semilla': N.SEMILLA, 'hilos_numericos': 1}, B / 'reglas' / 'entorno.json')
if not CMP['mismos_conjuntos_y_recuentos'].all() or not CMP['mismas_reglas'].all():
    raise SystemExit('Los algoritmos no coinciden')
print(EQ.to_string(index=False))

# ---- evaluación completa (FP-Growth)
R, nula, E, F, Sb, meta, frec, det = EV.evaluar(c, B / 'referencia_nula' / 'principal', con_estabilidad=True)
for archivo in (B / 'referencia_nula' / 'principal' / 'lotes_estabilidad').glob('*'):
    pass
(B / 'estabilidad').mkdir(exist_ok=True)
R_out = R.drop(columns=['items'])
N.a_csv(R_out, B / 'reglas' / 'reglas_principal.csv')
N.a_csv(nula, B / 'referencia_nula' / 'nula_principal.csv')
N.a_csv(E, B / 'estabilidad' / 'estabilidad_reglas.csv')
N.a_csv(F, B / 'estabilidad' / 'estabilidad_familias.csv')
N.a_csv(Sb, B / 'estabilidad' / 'submuestras.csv')

# destacadas y no destacadas
sol = R[R['clase'].str.startswith('6')].sort_values('z', key=abs, ascending=False)
cols = ['antecedente', 'consecuente', 'largo', 'n_antecedente', 'n_conjunto', 'soporte', 'confianza', 'ic_confianza_inf', 'ic_confianza_sup', 'frecuencia_basal', 'lift',
        'diferencia_basal', 'diferencia_riesgo', 'ic_dr_inf', 'ic_dr_sup', 'razon_riesgos', 'leverage', 'p_fisher', 'q_bh_todas', 'p_ajustado_busqueda',
        'reaparece_marcada', 'misma_direccion', 'mejora_sobre_subreglas', 'subregla_mas_cercana', 'clase']
N.a_csv(sol[cols], B / 'reglas' / 'reglas_destacadas.csv')
no_red = R[~R['redundante'].fillna(False).astype(bool)]
top = pd.concat([no_red[no_red['consecuente'] == cc].sort_values('z', key=abs, ascending=False).head(10) for cc in N.CONSECUENTES])
N.a_csv(top[cols], B / 'reglas' / 'reglas_no_destacadas_mayor_z.csv')

# cobertura
cob = []
Tm = c.T
for nombre_conj, mask in (('todas las reglas', np.ones(len(R), bool)), ('marcadas', R['marcada'].to_numpy()),
                          ('marcadas no redundantes', (R['marcada'] & ~R['redundante'].fillna(False).astype(bool)).to_numpy()),
                          ('superan la referencia nula', R['supera_nula'].to_numpy()), ('sólidas (clase 6)', R['clase'].str.startswith('6').to_numpy())):
    for cc in N.CONSECUENTES:
        sub = R[mask & (R['consecuente'] == cc).to_numpy()]
        if len(sub):
            A = G.matriz_antecedentes(Tm, [frozenset(i) for i in sub['items']])
            cubre = A.any(axis=0)
            cob.append({'conjunto': nombre_conj, 'consecuente': cc, 'reglas': len(sub), 'participantes_cubiertas': int(cubre.sum()), 'cobertura': float(cubre.mean()),
                        'confianza_media': float(sub['confianza'].mean()), 'confianza_maxima': float(sub['confianza'].max()), 'lift_maximo': float(sub['lift'].max())})
        else:
            cob.append({'conjunto': nombre_conj, 'consecuente': cc, 'reglas': 0, 'participantes_cubiertas': 0, 'cobertura': 0.0,
                        'confianza_media': np.nan, 'confianza_maxima': np.nan, 'lift_maximo': np.nan})
N.a_csv(pd.DataFrame(cob), B / 'reglas' / 'cobertura.csv')
clases = R.groupby(['clase', 'consecuente']).size().unstack(fill_value=0).reset_index()
N.a_csv(clases, B / 'reglas' / 'clases_principal.csv')
red = R[R['redundante'].fillna(False).astype(bool) & R['marcada']]
N.a_csv(red[['antecedente', 'consecuente', 'confianza', 'subregla_mas_cercana', 'mejora_sobre_subreglas', 'familia']], B / 'reglas' / 'redundantes_marcadas.csv')
fam = R[R['marcada']].groupby('familia').agg(reglas=('antecedente', 'size'), redundantes=('redundante', 'sum'), confianza_max=('confianza', 'max'),
                                            supera_nula=('supera_nula', 'sum')).reset_index().sort_values('reglas', ascending=False)
N.a_csv(fam, B / 'reglas' / 'familias_marcadas.csv')
meta['sello_protocolo'] = sello['sha256']
meta['clases'] = R['clase'].value_counts().to_dict()
meta['destacadas'] = len(sol)
N.a_json(meta, B / 'reglas' / 'resumen_principal.json')
N.registrar('reglas principal')
print(CMP.to_string(index=False))
print({k: v for k, v in meta.items() if k != 'items_constantes_quitados'})
print(R['clase'].value_counts())
print(top[['antecedente', 'consecuente', 'n_antecedente', 'confianza', 'diferencia_basal', 'p_ajustado_busqueda', 'clase']].to_string())
