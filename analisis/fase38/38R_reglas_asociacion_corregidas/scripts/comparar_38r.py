"""
Fase 38R: comparación automática con la Fase 38 histórica y verificación de exclusiones en todos los resultados. Solo lee resultados; escribe en comparacion/.

Uso, desde la carpeta scripts: python -B comparar_38r.py
"""
import json
import re
import sys

sys.dont_write_bytecode = True
import nucleo_38r as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

B, D, C = N.BASE, N.D38, N.BASE / 'comparacion'
N.instalar_gancho()
sello = N.huella_sello()
CLASE6 = 'bajo_impacto=no_lo_realiza_o_nunca & distension=nunca_o_casi_nunca & trabaja=SI'


def resumen_cfg(R, nula, meta=None):
    return {'reglas': len(R), 'hacia_severo': int((R['consecuente'] == 'severo_mrs=SI').sum()), 'hacia_no_severo': int((R['consecuente'] == 'severo_mrs=NO').sum()), 'marcadas': int(R['marcada'].sum()),
            'marcadas_no_redundantes': int((R['marcada'] & ~R['redundante'].fillna(False).astype(bool)).sum()), 'nula_media_marcadas': float(nula['reglas_marcadas'].mean()), 'nula_p95_marcadas': float(nula['reglas_marcadas'].quantile(.95)),
            'p_exceso_marcadas': float((1 + (nula['reglas_marcadas'] >= R['marcada'].sum()).sum()) / (1 + len(nula))), 'nula_p95_max_z': float(nula['max_z'].quantile(.95)), 'superan_nula': int(R['supera_nula'].sum()),
            'superan_nula_no_redundantes': int((R['supera_nula'] & ~R['redundante'].fillna(False).astype(bool)).sum()), 'compatibles_con_nula_marcadas_no_redundantes': int((R['marcada'] & ~R['redundante'].fillna(False).astype(bool) & ~R['supera_nula']).sum())}


Hr, Rr = pd.read_csv(D / 'reglas/reglas_principal.csv'), pd.read_csv(B / 'reglas/reglas_principal.csv')
Hn, Rn = pd.read_csv(D / 'referencia_nula/nula_principal.csv'), pd.read_csv(B / 'referencia_nula/nula_principal.csv')
Hm, Rm = N.leer_json(D / 'reglas/resumen_principal.json'), N.leer_json(B / 'reglas/resumen_principal.json')
HE, RE = pd.read_csv(D / 'estabilidad/estabilidad_reglas.csv'), pd.read_csv(B / 'estabilidad/estabilidad_reglas.csv')
HF, RF = pd.read_csv(D / 'estabilidad/estabilidad_familias.csv'), pd.read_csv(B / 'estabilidad/estabilidad_familias.csv')
HS, RS = pd.read_csv(D / 'estabilidad/submuestras.csv'), pd.read_csv(B / 'estabilidad/submuestras.csv')

# ---- principal
principal = []
h, r = resumen_cfg(Hr, Hn), resumen_cfg(Rr, Rn)
extra = {'variables': (31, 29), 'items': (Hm['items'], Rm['items']), 'conjuntos_frecuentes': (Hm['conjuntos_frecuentes'], Rm['conjuntos_frecuentes']), 'antecedentes_evaluados': (Hm['antecedentes_evaluados'], Rm['antecedentes_evaluados'])}
for k, (a, b) in extra.items():
    principal.append({'indicador': k, 'fase_38': a, 'fase_38R': b})
for k in h:
    principal.append({'indicador': k, 'fase_38': h[k], 'fase_38R': r[k]})
clases = sorted(set(Hr['clase']) | set(Rr['clase']))
for k in clases:
    principal.append({'indicador': f'clase: {k}', 'fase_38': int((Hr['clase'] == k).sum()), 'fase_38R': int((Rr['clase'] == k).sum())})
principal += [{'indicador': 'estables (regla)', 'fase_38': int(HE['estable'].sum()), 'fase_38R': int(RE['estable'].sum())},
              {'indicador': 'familias evaluadas', 'fase_38': len(HF), 'fase_38R': len(RF)},
              {'indicador': 'media de reaparición de familias', 'fase_38': float(HF['familia_reaparece'].mean()), 'fase_38R': float(RF['familia_reaparece'].mean())},
              {'indicador': 'media de reglas marcadas por submuestra', 'fase_38': float(HS['reglas_marcadas'].mean()), 'fase_38R': float(RS['reglas_marcadas'].mean())}]
N.a_csv(pd.DataFrame(principal), C / 'comparacion_principal.csv')

# ---- reglas conservadas tras la referencia nula
vet = Hr['antecedente'].str.contains('med_diabetes=|prevision=')
m = Hr[~vet].merge(Rr, on='antecedente', suffixes=('_h', '_r'))
N.a_csv(m.groupby(['clase_h', 'clase_r']).size().reset_index(name='reglas'), C / 'transiciones_de_clase.csv')
camb = m[m['clase_h'] != m['clase_r']][['antecedente', 'consecuente_r', 'clase_h', 'clase_r', 'p_ajustado_busqueda_h', 'p_ajustado_busqueda_r', 'q_bh_todas_h', 'q_bh_todas_r', 'reaparece_marcada_r', 'misma_direccion_r']]
N.a_csv(camb, C / 'reglas_que_cambian_de_clase.csv')
Em = HE[HE['antecedente'].isin(m['antecedente'])].merge(RE, on='antecedente', suffixes=('_h', '_r'))
conservadas = {'reglas_conservadas': len(m), 'p_ajustado_baja_o_igual': int((m['p_ajustado_busqueda_r'] <= m['p_ajustado_busqueda_h'] + 1e-12).sum()), 'p_ajustado_igual': int(np.isclose(m['p_ajustado_busqueda_r'], m['p_ajustado_busqueda_h']).sum()),
               'p_ajustado_baja_max': float((m['p_ajustado_busqueda_h'] - m['p_ajustado_busqueda_r']).max()), 'q_baja_o_igual': int((m['q_bh_todas_r'] <= m['q_bh_todas_h'] + 1e-12).sum()), 'q_iguales': int(np.isclose(m['q_bh_todas_r'], m['q_bh_todas_h']).sum()),
               'q_sube': int((m['q_bh_todas_r'] > m['q_bh_todas_h'] + 1e-12).sum()), 'cambian_de_clase': len(camb),
               'estabilidad_identica': {k: int(np.isclose(Em[f'{k}_h'], Em[f'{k}_r']).sum()) for k in ('reaparece_marcada', 'misma_direccion')}, 'estable_identica': int((Em['estable_h'] == Em['estable_r']).sum()), 'filas_estabilidad_comparadas': len(Em),
               'nula_max_z_nunca_sube': bool((Rn['max_z'].to_numpy() <= Hn['max_z'].to_numpy() + 1e-12).all()), 'nula_marcadas_nunca_sube': bool((Rn['reglas_marcadas'].to_numpy() <= Hn['reglas_marcadas'].to_numpy()).all()),
               'permutaciones_con_max_z_menor': int((Rn['max_z'].to_numpy() < Hn['max_z'].to_numpy() - 1e-12).sum()), 'permutaciones': len(Rn)}

# ---- regla de clase 6
filas = []
fh, fr = Hr[Hr['antecedente'] == CLASE6].iloc[0], Rr[Rr['antecedente'] == CLASE6].iloc[0]
for k in ('consecuente', 'n_antecedente', 'n_conjunto', 'soporte', 'confianza', 'ic_confianza_inf', 'ic_confianza_sup', 'frecuencia_basal', 'lift', 'diferencia_basal', 'leverage', 'diferencia_riesgo', 'razon_riesgos', 'z', 'p_fisher', 'q_bh_todas', 'p_ajustado_busqueda', 'supera_nula', 'marcada',
          'redundante', 'mejora_sobre_subreglas', 'reaparece_marcada', 'misma_direccion', 'estable', 'clase'):
    filas.append({'medida': k, 'fase_38': fh[k], 'fase_38R': fr[k]})
N.a_csv(pd.DataFrame(filas), C / 'regla_clase6.csv')
Lh, Lr = pd.read_csv(D / 'sensibilidades/lectura_reglas_principal.csv'), pd.read_csv(B / 'sensibilidades/lectura_reglas_principal.csv')
c6 = Lr[Lr['antecedente'] == CLASE6].merge(Lh[Lh['antecedente'] == CLASE6][['configuracion', 'lectura', 'n_antecedente', 'confianza', 'supera_nula', 'clase']].rename(columns=lambda x: x if x == 'configuracion' else x + '_h'), on='configuracion', how='left')
N.a_csv(c6, C / 'regla_clase6_sensibilidades.csv')

# ---- sensibilidades
SrH, SrR = pd.read_csv(D / 'sensibilidades/resumen_sensibilidades.csv').set_index('configuracion'), pd.read_csv(B / 'sensibilidades/resumen_sensibilidades.csv').set_index('configuracion')
tabla = []
for nom in SrR.index:
    eq = N.HISTORICA[nom]
    Rs = pd.read_csv(B / f'sensibilidades/reglas/reglas_{nom}.csv')
    nr = int((Rs['supera_nula'] & ~Rs['redundante'].fillna(False).astype(bool)).sum())
    fila = {'configuracion': nom, 'equivale_a_historica': eq or 'sin equivalente', 'n': int(SrR.at[nom, 'n']), 'items': int(SrR.at[nom, 'items']), 'reglas': int(SrR.at[nom, 'reglas']), 'marcadas': int(SrR.at[nom, 'marcadas']), 'nula_media_marcadas': float(SrR.at[nom, 'nula_media_marcadas']),
            'nula_p95_marcadas': float(SrR.at[nom, 'nula_p95_marcadas']), 'superan_nula': int(SrR.at[nom, 'supera_nula']), 'superan_nula_no_redundantes': nr}
    if eq:
        Rh = pd.read_csv(D / f'sensibilidades/reglas/reglas_{eq}.csv')
        fila.update({'h_n': int(SrH.at[eq, 'n']), 'h_items': int(SrH.at[eq, 'items']), 'h_reglas': int(SrH.at[eq, 'reglas']), 'h_marcadas': int(SrH.at[eq, 'marcadas']), 'h_nula_media_marcadas': float(SrH.at[eq, 'nula_media_marcadas']), 'h_superan_nula': int(SrH.at[eq, 'supera_nula']),
                     'h_superan_nula_no_redundantes': int((Rh['supera_nula'] & ~Rh['redundante'].fillna(False).astype(bool)).sum())})
    tabla.append(fila)
N.a_csv(pd.DataFrame(tabla), C / 'comparacion_sensibilidades.csv')
# lectura de la principal
LrT = pd.read_csv(B / 'sensibilidades/lectura_resumen.csv')
N.a_csv(LrT, C / 'lectura_principal_en_sensibilidades.csv')
# observadas frente a ampliadas
obs = []
for a, b in (('S7a', 'S7a-309'), ('S7b', 'S7b-251')):
    Ra, Rb = pd.read_csv(B / f'sensibilidades/reglas/reglas_{a}.csv'), pd.read_csv(B / f'sensibilidades/reglas/reglas_{b}.csv')
    ma, mb = set(Ra.loc[Ra['marcada'], 'antecedente']), set(Rb.loc[Rb['marcada'], 'antecedente'])
    obs.append({'comparacion': f'{a} frente a {b}', 'reglas_a': len(Ra), 'reglas_b': len(Rb), 'marcadas_a': len(ma), 'marcadas_b': len(mb), 'marcadas_en_ambas': len(ma & mb), 'superan_nula_a': int(Ra['supera_nula'].sum()), 'superan_nula_b': int(Rb['supera_nula'].sum()),
                'superan_nula_no_redundantes_a': int((Ra['supera_nula'] & ~Ra['redundante'].fillna(False).astype(bool)).sum()), 'superan_nula_no_redundantes_b': int((Rb['supera_nula'] & ~Rb['redundante'].fillna(False).astype(bool)).sum())})
N.a_csv(pd.DataFrame(obs), C / 'observadas_frente_a_ampliadas.csv')

# ---- robustez: clase 6 y se mantiene en toda sensibilidad en que es evaluable con su definición
rob = []
for a in Rr.loc[Rr['clase'].str.startswith('6'), 'antecedente']:
    x = Lr[Lr['antecedente'] == a]
    evaluable = x[x['lectura'] != 'no evaluable']
    rob.append({'antecedente': a, 'sensibilidades': len(x), 'evaluables': len(evaluable), 'se_mantiene': int((evaluable['lectura'] == 'se mantiene').sum()), 'se_debilita': int((evaluable['lectura'] == 'se debilita').sum()), 'desaparece': int((evaluable['lectura'] == 'desaparece por falta de casos').sum()),
                'cambia': int((evaluable['lectura'] == 'cambia de dirección').sum()), 'supera_nula_en': int((evaluable['supera_nula'] == True).sum()), 'detalle': '; '.join(f"{r.configuracion}: {r.lectura}" for r in x.itertuples()), 'robusta': bool(len(evaluable) and (evaluable['lectura'] == 'se mantiene').all())})  # noqa: E712
N.a_csv(pd.DataFrame(rob, columns=['antecedente', 'sensibilidades', 'evaluables', 'se_mantiene', 'se_debilita', 'desaparece', 'cambia', 'supera_nula_en', 'detalle', 'robusta']), C / 'evaluacion_robustez.csv')

# ---- barrido de exclusiones en todo lo generado por la 38R
patron = re.compile(r'med_diabetes|prevision|usa_medicamentos_diabetes|doble_carga|fonasa|isapre|ffaa', re.I)
barrido = []
for carpeta in ('preparacion', 'reglas', 'referencia_nula', 'estabilidad', 'sensibilidades'):
    for p in (B / carpeta).rglob('*'):
        if p.suffix not in ('.csv', '.txt', '.json') or not p.is_file():
            continue
        t = p.read_text(encoding='utf-8')
        n = len(patron.findall(t))
        barrido.append({'archivo': p.relative_to(B).as_posix(), 'bytes': p.stat().st_size, 'apariciones': n})
BR = pd.DataFrame(barrido)
# verificación_preparacion.json nombra los ítems históricos retirados: es un registro, no un antecedente.
BR['es_registro_de_retirada'] = BR['archivo'].eq('preparacion/verificacion_preparacion.json')
N.a_csv(BR, C / 'barrido_exclusiones.csv')
for nom in N.CONFIGS:
    Rs = Rr if nom == 'principal' else pd.read_csv(B / f'sensibilidades/reglas/reglas_{nom}.csv')
    N.B.verificar_reglas(Rs, N.variable_de_item, N.B.permitidas(nom, N.B.decisiones()), N.CONSECUENTES)
Cv = pd.read_csv(B / 'reglas/conviccion_descriptiva_anexo.csv')
info = {'conservadas': conservadas, 'configuraciones_verificadas': len(N.CONFIGS), 'archivos_barridos': len(BR), 'apariciones_en_resultados': int(BR.loc[~BR['es_registro_de_retirada'], 'apariciones'].sum()), 'robustas': int(sum(x['robusta'] for x in rob)), 'clase6': int(Rr['clase'].str.startswith('6').sum()),
        'conviccion': {'filas': len(Cv), 'mediana': float(Cv['conviccion'].replace(np.inf, np.nan).median()), 'maxima_finita': float(Cv['conviccion'].replace(np.inf, np.nan).max()), 'infinitas': int(np.isinf(Cv['conviccion']).sum())}, 'sello_protocolo': sello['sha256']}
N.a_json(info, C / 'resumen_comparacion.json')
N.registrar('comparacion')
print(pd.DataFrame(principal).to_string(index=False))
print(json.dumps(info, ensure_ascii=False, indent=1))
print(pd.DataFrame(filas).to_string(index=False))
print(c6[['configuracion', 'lectura', 'n_antecedente', 'confianza', 'supera_nula', 'clase', 'lectura_h']].to_string(index=False))
print(pd.DataFrame(tabla).to_string(index=False))
print(pd.DataFrame(obs).T.to_string())
print(LrT.to_string(index=False))
print(m.groupby(['clase_h', 'clase_r']).size())
print(camb.to_string(index=False))
print(pd.DataFrame(rob).drop(columns='detalle').to_string(index=False))
