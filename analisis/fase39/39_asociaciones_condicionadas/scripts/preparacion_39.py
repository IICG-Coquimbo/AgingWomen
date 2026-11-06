"""
Fase 39: preparación de las matrices condicionadas. Verifica que la codificación sea idéntica a la Fase 38, define la pertenencia a los estratos y a A/B1, y
escribe tamaños, frecuencias basales, umbrales y matrices por estrato.

Uso, desde la carpeta scripts: python preparacion_39.py
"""
import sys

import nucleo_39 as N
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

sys.dont_write_bytecode = True
N.instalar_gancho()
N.huella_sello()
P = N.BASE / 'preparacion'
d = N.cargar()
y = d.M['severo_mrs'].to_numpy().astype(int)
T529, traza = N.base_items(d)
# 1. codificación idéntica a la Fase 38
M38 = pd.read_csv(N.D38 / 'preparacion' / 'matriz_transaccional_principal.csv', dtype={'participante_id': str})
cols38 = [c for c in M38.columns if c not in ('participante_id',) + N.CONSECUENTES]
verif = {'ids_iguales_y_en_orden': M38['participante_id'].tolist() == list(d.ids), 'mismos_items': cols38 == list(T529.columns),
         'misma_matriz': bool((M38[cols38].to_numpy().astype(bool) == T529.to_numpy()).all()), 'items': len(cols38),
         'consecuente_igual': bool((M38['severo_mrs=SI'].to_numpy() == y).all()), 'severos': int(y.sum()), 'no_severos': int(len(y) - y.sum()),
         'participantes': len(d.ids), 'ids_unicos': len(set(d.ids)), 'B1_igual_a_regla': bool((d.E['B1'] == d.E['B1_regla']).all())}
if not all(v for k, v in verif.items() if isinstance(v, bool)) or verif['severos'] != 281 or verif['participantes'] != 529:
    raise SystemExit(f'Verificación fallida: {verif}')
N.a_json(verif, P / 'verificacion_codificacion.json')
masc = N.mascaras(d)
# 2. pertenencia
pert = pd.DataFrame({'participante_id': d.ids, 'severo_mrs': y})
for dim in N.DIMENSIONES:
    lab = np.full(len(y), '', object)
    for e in N.dims_de(dim):
        lab[masc[(dim, e)]] = e
    if (lab == '').any():
        raise SystemExit(f'Participantes sin estrato en {dim}')
    pert[dim] = lab
pert['A'] = d.E['A'].to_numpy()
pert['B1'] = d.E['B1'].to_numpy()
N.a_csv(pert, P / 'pertenencia_estratos.csv')
# 3. diccionario de estratos, tamaños y basales
defin = {('trabajo', 'trabaja'): 'trabaja_actualmente = 1', ('trabajo', 'no_trabaja'): 'trabaja_actualmente = 0', ('pareja', 'con_pareja'): 'tiene_pareja = 1',
         ('pareja', 'sin_pareja'): 'tiene_pareja = 0', ('ejercicio', '0_dias'): 'dias_ejercicio_semana = 1 (0 días)', ('ejercicio', '1-2_dias'): 'dias_ejercicio_semana = 2 (1-2 días)',
         ('ejercicio', '3_o_mas_dias'): 'dias_ejercicio_semana ≥ 3 (3-4, 5-6 o todos los días)', ('cuidado', 'cuida'): 'cantidad_personas_cuida ≥ 1',
         ('cuidado', 'no_cuida'): 'cantidad_personas_cuida = 0'}
filas, items_estr = [], []
for (g, e), m in masc.items():
    c = N.construir(d, g, e, T529=T529, masc=masc)
    lo, hi = N.N38.wilson(c.n_si, c.n)
    filas.append({'grupo': g, 'estrato': e, 'nombre': N.NOMBRE.get(e, e), 'definicion': defin.get((g, e), f'etiqueta histórica {g} = {e.split("_")[-1]}'),
                  'participantes': c.n, 'severas': c.n_si, 'no_severas': c.n - c.n_si, 'frecuencia_basal_si': c.n_si / c.n, 'ic_basal_inf': float(lo), 'ic_basal_sup': float(hi),
                  'largo_maximo': c.largo, 'umbral_antecedente': c.min_ant, 'umbral_conjunto': c.min_conj, 'comparabilidad_minima': c.comp,
                  'variables_excluidas': ', '.join(c.excluidas), 'items': c.T.shape[1], 'items_constantes_quitados': len(c.constantes),
                  'busqueda': 'búsqueda de reglas' if c.largo > 0 else 'solo descripción', 'uso': 'principal' if g in N.DIMENSIONES else 'exploratorio secundario'})
    pre = c.T.mean()
    for it in T529.columns:
        if N.N38.variable_de_item(it) in c.excluidas:
            continue
        items_estr.append({'grupo': g, 'estrato': e, 'item': it, 'participantes': int(T529.loc[m, it].sum()), 'prevalencia': float(T529.loc[m, it].mean()),
                           'en_estrato': it in c.T.columns})
    Mx = c.T.astype(int)
    Mx.insert(0, 'participante_id', c.ids)
    Mx['severo_mrs=SI'] = c.y
    Mx['severo_mrs=NO'] = 1 - c.y
    N.a_csv(Mx, P / 'matrices' / f'matriz_{g}_{e}.csv')
D = pd.DataFrame(filas)
N.a_csv(D, P / 'diccionario_estratos.csv')
N.a_csv(pd.DataFrame(items_estr), P / 'items_por_estrato.csv')
# 4. diferencias de frecuencia basal entre estratos (descriptivo, asociación del contexto con la severidad)
dif = []
for g in list(N.DIMENSIONES) + ['A', 'B1']:
    t = D[D['grupo'] == g].reset_index(drop=True)
    for i in range(len(t)):
        for j in range(i + 1, len(t)):
            a, b = t.loc[i], t.loc[j]
            lo, hi = N.N38.newcombe(a['severas'], a['participantes'], b['severas'], b['participantes'])
            p = fisher_exact([[a['severas'], a['no_severas']], [b['severas'], b['no_severas']]])[1]
            dif.append({'grupo': g, 'estrato_1': a['estrato'], 'estrato_2': b['estrato'], 'basal_1': a['frecuencia_basal_si'], 'basal_2': b['frecuencia_basal_si'],
                        'diferencia': a['frecuencia_basal_si'] - b['frecuencia_basal_si'], 'ic_inf': float(lo), 'ic_sup': float(hi), 'p_fisher': p})
N.a_csv(pd.DataFrame(dif), P / 'diferencias_basales.csv')
# 5. superposición entre dimensiones
cr = []
for a in N.DIMENSIONES:
    for b in N.DIMENSIONES:
        if a < b:
            t = pd.crosstab(pert[a], pert[b])
            for i in t.index:
                for j in t.columns:
                    cr.append({'dimension_1': a, 'estrato_1': i, 'dimension_2': b, 'estrato_2': j, 'participantes': int(t.loc[i, j])})
N.a_csv(pd.DataFrame(cr), P / 'superposicion_dimensiones.csv')
N.a_csv(traza, P / 'trazabilidad_items_fase38.csv')
N.registrar('preparacion')
print(verif)
print(D[['grupo', 'estrato', 'participantes', 'severas', 'frecuencia_basal_si', 'largo_maximo', 'umbral_antecedente', 'umbral_conjunto', 'items']].to_string(index=False))
