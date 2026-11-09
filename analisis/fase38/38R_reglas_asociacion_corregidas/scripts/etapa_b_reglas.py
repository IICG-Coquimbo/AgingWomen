"""
Fase 38R, etapa B: Apriori, FP-Growth y enumeración exhaustiva sobre la matriz corregida, identificación de reglas conservadas y comparación automática de sus métricas con la Fase 38.
No calcula referencia nula ni clasifica: eso es la etapa C.

Uso, desde la carpeta scripts: python -B etapa_b_reglas.py
"""
import platform
import sys
import time
import tracemalloc

sys.dont_write_bytecode = True
import nucleo_38r as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy  # noqa: E402

G, EV, H = N.G, N.EV, N.H
N.instalar_gancho()
sello = N.huella_sello()
B = N.BASE
pq = N.cargar()
c = N.construir(pq, 'principal')
if (c.min_ant, c.min_conj, c.largo) != (53, 27, 3):
    raise N.B.Incumplimiento(f'Umbrales distintos del protocolo: {c.min_ant}, {c.min_conj}, {c.largo}')

eq, res = [], {}
det = H.pares_determinados(c.T)
for nombre in ('apriori', 'fpgrowth', 'exhaustiva'):
    t = time.perf_counter()
    f = EV.descubrir(c, algoritmo=nombre)
    seg = time.perf_counter() - t
    tracemalloc.start()
    EV.descubrir(c, algoritmo=nombre)
    pico = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    res[nombre] = f
    R_ = G.reglas(f, c.n, c.n_si, c.min_ant, c.min_conj, det)
    res[nombre + '_reglas'] = R_
    N.B.verificar_reglas(R_, N.variable_de_item, c.autorizadas, N.CONSECUENTES)
    eq.append({'algoritmo': nombre, 'conjuntos_frecuentes': len(f), 'reglas': len(R_), 'segundos': round(seg, 2), 'memoria_pico_mb': round(pico / 2 ** 20, 1), 'minsup_absoluto': c.min_conj, 'largo_maximo_antecedente': c.largo})
EQ = pd.DataFrame(eq)
comp = []
for a, b in (('apriori', 'fpgrowth'), ('apriori', 'exhaustiva'), ('fpgrowth', 'exhaustiva')):
    igual, dif = G.iguales(res[a], res[b])
    ra, rb = res[a + '_reglas'], res[b + '_reglas']
    comp.append({'comparacion': f'{a} frente a {b}', 'mismos_conjuntos_y_recuentos': igual, 'diferencias': dif,
                 'mismas_reglas': ra[['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']].equals(rb[['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']])})
CMP = pd.DataFrame(comp)
N.a_csv(EQ, B / 'reglas' / 'equivalencia_algoritmos.csv')
N.a_csv(CMP, B / 'reglas' / 'equivalencia_comparaciones.csv')
N.a_json({'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__, 'sistema': platform.platform(),
          'implementacion': 'Apriori, FP-Growth y enumeración exhaustiva históricos (fase38/.../scripts/algoritmos_38.py), importados sin modificar', 'semilla': N.SEMILLA, 'hilos_numericos': 1}, B / 'reglas' / 'entorno.json')
if not CMP['mismos_conjuntos_y_recuentos'].all() or not CMP['mismas_reglas'].all():
    raise SystemExit('Los algoritmos no coinciden')

frec = res['fpgrowth']
R = EV.reglas_de(c, frec, det)
N.B.verificar_reglas(R, N.variable_de_item, c.autorizadas, N.CONSECUENTES)

# Reglas conservadas frente a la Fase 38
Hr = pd.read_csv(N.D38 / 'reglas' / 'reglas_principal.csv')
vetada = Hr['antecedente'].str.contains('med_diabetes=|prevision=')
ant_h, ant_r = set(Hr.loc[~vetada, 'antecedente']), set(R['antecedente'])
identif = Hr[['antecedente', 'consecuente', 'largo', 'marcada', 'clase']].copy()
identif['estado_38R'] = np.where(vetada, 'retirada: contiene una variable excluida', np.where(Hr['antecedente'].isin(ant_r), 'conservada', 'perdida sin motivo'))
N.a_csv(identif, B / 'comparacion' / 'identificacion_reglas.csv')
faltan, nuevas = ant_h - ant_r, ant_r - ant_h
m = Hr.loc[~vetada].merge(R.drop(columns=['items']), on='antecedente', suffixes=('_h', '_r'))
exactas = ['consecuente', 'largo', 'variables', 'n_antecedente', 'n_conjunto', 'n', 'marcada', 'subregla_mas_cercana', 'redundante', 'familia']
numericas = ['frecuencia_basal', 'soporte_antecedente', 'soporte', 'confianza', 'ic_confianza_inf', 'ic_confianza_sup', 'lift', 'diferencia_basal', 'leverage', 'confianza_sin_antecedente', 'diferencia_riesgo', 'ic_dr_inf', 'ic_dr_sup', 'razon_riesgos', 'ic_rr_inf', 'ic_rr_sup', 'z', 'p_fisher', 'mejora_sobre_subreglas']
filas = []
for k in exactas:
    a, b = m[f'{k}_h'], m[f'{k}_r']
    if k == 'subregla_mas_cercana':
        a, b = a.fillna(''), b.fillna('')
    filas.append({'metrica': k, 'tipo': 'exacta', 'reglas_comparadas': len(m), 'diferencias': int((a.astype(str) != b.astype(str)).sum()), 'dif_max_absoluta': np.nan})
for k in numericas:
    a, b = m[f'{k}_h'].to_numpy(float), m[f'{k}_r'].to_numpy(float)
    dif = np.abs(a - b)
    filas.append({'metrica': k, 'tipo': 'numérica (tolerancia 1e-9)', 'reglas_comparadas': len(m), 'diferencias': int(np.nansum(dif > 1e-9) + (np.isnan(a) != np.isnan(b)).sum()), 'dif_max_absoluta': float(np.nanmax(dif)) if len(dif) else np.nan})
Cm = pd.DataFrame(filas)
N.a_csv(Cm, B / 'comparacion' / 'metricas_reglas_conservadas.csv')
info = {'reglas_historicas': len(Hr), 'reglas_historicas_retiradas': int(vetada.sum()), 'reglas_historicas_elegibles': int((~vetada).sum()), 'reglas_38R': len(R), 'perdidas_sin_motivo': len(faltan), 'nuevas_no_historicas': len(nuevas),
        'metricas_con_diferencias': Cm.loc[Cm['diferencias'] > 0, 'metrica'].tolist(), 'conjuntos_frecuentes': len(frec), 'por_consecuente': R['consecuente'].value_counts().to_dict(), 'reglas_con_variable_prohibida': 0, 'marcadas_descriptivas': int(R['marcada'].sum()), 'sello_protocolo': sello['sha256']}
N.a_json(info, B / 'comparacion' / 'resumen_etapa_b.json')
if faltan or nuevas or Cm['diferencias'].sum():
    N.registrar('etapa B con diferencias')
    raise SystemExit(f'Las reglas conservadas difieren: {info}')
N.registrar('etapa B reglas')
print(EQ.to_string(index=False))
print(CMP.to_string(index=False))
print(info)
