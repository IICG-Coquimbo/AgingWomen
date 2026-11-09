"""
Cierre de la Fase 35: contrasta las cifras de los informes con los archivos guardados.

Solo lee resultados y comprueba aritmética sobre ellos (p, q de Benjamini-Hochberg y SU a partir de componentes
ya guardados). No genera permutaciones, no calcula FCBF, no entrena modelos y no usa datos de la Fase 36.
Uso, desde analisis/: python cierre_fases_34_35/scripts/verificar_fase35.py
Escribe solo cierre_fases_34_35/tablas/verificacion_fase35.csv y datos_fase35.json.
"""
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

ANALISIS = Path(__file__).resolve().parents[2]
RAIZ = ANALISIS.parent
TABLAS = ANALISIS / 'cierre_fases_34_35' / 'tablas'
S33 = ANALISIS / 'reunion_2026-11-03' / 'revision_33_variables'
P50 = S33 / 'permutaciones_50000'
P10 = S33 / 'permutaciones_10000'
RF = ANALISIS / 'random_forest_revision_35b_33_variables' / 'resultados'
RF_REG = ANALISIS / 'random_forest_revision_35b_33_variables' / 'registro_ejecucion.txt'
LIMPIO = RAIZ / 'datos' / 'limpio_usuaria' / 'dataset_usuaria_limpio.csv'
F35 = RAIZ / 'datos' / 'analitico' / 'dataset_fase35.csv'
F35_33 = RAIZ / 'datos' / 'analitico' / 'dataset_fase35_33_variables.csv'
ORIGEN = ANALISIS / 'revision_correctiva_fase34' / 'tablas' / 'origen_respuestas_34D.csv'

FILAS = []


def rel(r):
    return Path(r).relative_to(RAIZ).as_posix()


def leer(r):
    return pd.read_csv(r, encoding='utf-8-sig')


def comprobar(grupo, que, esperado, obtenido, fuente, tol=None):
    if tol is None:
        ok = esperado == obtenido
    else:
        ok = abs(float(esperado) - float(obtenido)) <= tol
    FILAS.append({'grupo': grupo, 'comprobacion': que, 'esperado': esperado, 'obtenido': obtenido,
                  'fuente': rel(fuente), 'estado': 'OK' if ok else 'DIFERENCIA'})


def bh(p):
    p = np.asarray(p, float)
    orden = np.argsort(p)
    q = p[orden] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    salida = np.empty(len(p))
    salida[orden] = np.minimum(q, 1)
    return salida


def fase35a():
    g = '35A'
    d = pd.read_csv(F35, encoding='utf-8-sig', dtype=str, keep_default_na=False)
    lim = pd.read_csv(LIMPIO, encoding='utf-8-sig', dtype=str, keep_default_na=False)
    m = lim[lim['participante_id'].isin(d['participante_id'])].set_index('participante_id')
    d = d.set_index('participante_id')
    comprobar(g, 'Participantes con MRS completo', 529, len(d), F35)
    comprobar(g, 'Severas (MRS total >= 16)', 281, int((d['severo_mrs'].astype(float) == 1).sum()), F35)
    comprobar(g, 'Clasificadas como trabajadoras', 309, int((d['trabaja_actualmente'].astype(float) == 1).sum()), F35)
    comprobar(g, 'No trabajan', 220, int((d['trabaja_actualmente'].astype(float) == 0).sum()), F35)
    tr = d['trabaja_actualmente'].astype(float) == 1
    resp = m['lugar_trabajo_comprensivo'] != ''
    comprobar(g, 'Con lugar de trabajo en el conjunto limpio', 287, int(resp.sum()), LIMPIO)
    comprobar(g, 'Con estrés laboral en el conjunto limpio', 287, int((m['estres_entorno_laboral'] != '').sum()), LIMPIO)
    sin = tr & ~resp.reindex(d.index)
    comprobar(g, 'Trabajadoras sin datos laborales (situación imputada)', 22, int(sin.sum()), LIMPIO)
    o = leer(ORIGEN).set_index('variable')
    comprobar(g, 'Situación laboral imputada (tabla de origen)', 22, int(o.at['trabaja_actualmente', 'imputadas']), ORIGEN)
    for c in ('lugar_trabajo_comprensivo', 'estres_entorno_laboral'):
        comprobar(g, f'{c}: las 22 valen 3 en el conjunto de la Fase 35', 22, int((d.loc[sin, c].astype(float) == 3).sum()), F35)
        comprobar(g, f'{c}: quienes no trabajan valen 0', 220, int((d.loc[~tr, c].astype(float) == 0).sum()), F35)
    comprobar(g, 'lugar_trabajo: imputadas 34B dentro de las 287', 16, int(o.at['lugar_trabajo_comprensivo', 'imputadas']), ORIGEN)
    comprobar(g, 'estres_entorno: imputadas 34B dentro de las 287', 10, int(o.at['estres_entorno_laboral', 'imputadas']), ORIGEN)
    comprobar(g, 'Cuidadoras con sobrecarga en el limpio', 251, int((m['sobrecarga_fisica_emocional'] != '').sum()), LIMPIO)
    d33 = pd.read_csv(F35_33, encoding='utf-8-sig', nrows=1)
    comprobar(g, 'dataset_fase35_33_variables: columnas', 39, d33.shape[1], F35_33)
    comprobar(g, 'dataset_fase35_33_variables trae previsión y doble carga', True,
              {'prevision', 'doble_carga'} <= set(d33.columns), F35_33)
    comprobar(g, 'dataset_fase35_33_variables no trae sobrecarga', False, 'sobrecarga_fisica_emocional' in d33.columns, F35_33)
    return {'trabajadoras': int(tr.sum()), 'con_respuesta': int(resp.sum()), 'imputadas': int(sin.sum())}


def shannon():
    g = 'Shannon'
    r50 = leer(P50 / 'relevancia_33.csv')
    r10 = leer(P10 / 'relevancia_33.csv')
    comprobar(g, 'Variables evaluadas', 33, len(r50), P50 / 'relevancia_33.csv')
    comprobar(g, 'Sin duplicados', 33, r50['variable'].nunique(), P50 / 'relevancia_33.csv')
    for v in ('usa_medicamentos_diabetes', 'doble_carga', 'prevision', 'etapa_menopausica', 'menstruacion_llega',
              'tipo_sangrado', 'usa_metodo_anticonceptivo'):
        comprobar(g, f'{v} fuera de la lista', False, v in set(r50['variable']), P50 / 'relevancia_33.csv')
    pob = r50['poblacion'].value_counts().to_dict()
    n_por = r50.groupby('poblacion')['n'].unique().apply(lambda x: x.tolist()).to_dict()
    comprobar(g, 'Variables por población', {'general': 30, 'laboral': 2, 'cuidadoras': 1}, pob, P50 / 'relevancia_33.csv')
    comprobar(g, 'n por población', {'cuidadoras': [239], 'general': [529], 'laboral': [287]}, dict(sorted(n_por.items())), P50 / 'relevancia_33.csv')
    for B, t, ruta in ((50000, r50, P50), (10000, r10, P10)):
        comprobar(g, f'p = (k+1)/(B+1), B = {B}: desviación máxima', 0.0,
                  float(((t['k'] + 1) / (B + 1) - t['p']).abs().max()), ruta / 'relevancia_33.csv', tol=6e-7)
        comprobar(g, f'q = BH sobre las 33 (B = {B}): desviación máxima', 0.0,
                  float(np.abs(bh(t['p']) - t['q']).max()), ruta / 'relevancia_33.csv', tol=6e-6)
    seis = {'dias_ejercicio_semana', 'frecuencia_bajo_impacto', 'imc', 'frecuencia_fuerza', 'lugar_trabajo_comprensivo',
            'trabaja_actualmente'}
    comprobar(g, 'q < 0,10 con 50.000', seis, set(r50.loc[r50['q'] < 0.10, 'variable']), P50 / 'relevancia_33.csv')
    comprobar(g, 'q < 0,10 con 10.000', seis, set(r10.loc[r10['q'] < 0.10, 'variable']), P10 / 'relevancia_33.csv')
    comprobar(g, 'q < 0,05 con 10.000', 0, int((r10['q'] < 0.05).sum()), P10 / 'relevancia_33.csv')
    comprobar(g, 'q < 0,05 con 50.000', {'dias_ejercicio_semana', 'frecuencia_bajo_impacto'},
              set(r50.loc[r50['q'] < 0.05, 'variable']), P50 / 'relevancia_33.csv')
    esperado = {'dias_ejercicio_semana': (0.018255, 0.045869), 'frecuencia_bajo_impacto': (0.016664, 0.045869),
                'imc': (0.017585, 0.080958), 'frecuencia_fuerza': (0.019287, 0.089428),
                'lugar_trabajo_comprensivo': (0.020521, 0.089428), 'trabaja_actualmente': (0.008290, 0.089428)}
    i = r50.set_index('variable')
    for v, (su, q) in esperado.items():
        comprobar(g, f'{v}: SU', su, float(i.at[v, 'su']), P50 / 'relevancia_33.csv', tol=1e-6)
        comprobar(g, f'{v}: q (50.000)', q, float(i.at[v, 'q']), P50 / 'relevancia_33.csv', tol=1e-6)
    mc = leer(P50 / 'incertidumbre_monte_carlo.csv').set_index('variable')
    comprobar(g, 'Intervalo Monte Carlo de q de días de ejercicio incluye 0,05', True,
              bool(mc.at['dias_ejercicio_semana', 'q_mc_inferior'] < 0.05 < mc.at['dias_ejercicio_semana', 'q_mc_superior']),
              P50 / 'incertidumbre_monte_carlo.csv')
    comp = leer(P50 / 'shannon_componentes.csv')
    su = 2 * comp['informacion_mutua'] / (comp['h_x'] + comp['h_severidad'])
    comprobar(g, 'SU = 2·I/(H(X)+H(Y)): desviación máxima', 0.0, float((su - comp['su']).abs().max()),
              P50 / 'shannon_componentes.csv', tol=2e-6)
    comprobar(g, 'I = H(X)+H(Y)-H(X,Y): desviación máxima', 0.0,
              float((comp['h_x'] + comp['h_severidad'] - comp['h_conjunta'] - comp['informacion_mutua']).abs().max()),
              P50 / 'shannon_componentes.csv', tol=2e-6)
    comprobar(g, 'SU de componentes igual a relevancia_33', 0.0,
              float((comp.set_index('variable')['su'] - r50.set_index('variable')['su']).abs().max()),
              P50 / 'shannon_componentes.csv', tol=2e-6)
    sens = leer(P50 / 'sensibilidades.csv')
    r10i = r10.set_index('variable')
    orden = r50.sort_values(['q', 'p'])
    filas = [{'variable': f.variable, 'poblacion': f.poblacion, 'n': int(f.n), 'su': float(f.su), 'k': int(f.k), 'p': float(f.p),
              'q': float(f.q), 'q_10000': float(r10i.at[f.variable, 'q']), 'mc_inf': float(mc.at[f.variable, 'q_mc_inferior']),
              'mc_sup': float(mc.at[f.variable, 'q_mc_superior'])} for f in orden.head(11).itertuples()]
    return {'sensibilidades': sens.to_dict('records'), 'primeras': filas,
            'componentes': comp[['variable', 'h_x', 'h_severidad', 'informacion_mutua']].to_dict('records')}


def fcbf():
    g = 'FCBF'
    t = leer(S33 / 'informe' / 'fcbf_10000_50000.csv')
    r = S33 / 'informe' / 'fcbf_10000_50000.csv'
    def sel(var, B):
        return set(t.loc[(t['variante'] == var) & (t[f'decision_{B}'] == 'seleccionada'), 'variable'])
    for B in (10000, 50000):
        comprobar(g, f'Adaptado seleccionadas, B = {B}',
                  {'frecuencia_fuerza', 'imc', 'lugar_trabajo_comprensivo', 'trabaja_actualmente'}, sel('adaptado', B), r)
        comprobar(g, f'Estándar seleccionadas, B = {B}', {'frecuencia_fuerza', 'lugar_trabajo_comprensivo'}, sel('estandar', B), r)
    comprobar(g, 'Decisión idéntica entre 10.000 y 50.000', True, bool((t['decision_10000'] == t['decision_50000']).all()), r)
    a = t[t['variante'] == 'estandar'].set_index('variable')
    b = t[t['variante'] == 'adaptado'].set_index('variable')
    for v in ('dias_ejercicio_semana', 'frecuencia_bajo_impacto'):
        comprobar(g, f'{v} redundante respecto a fuerza en ambas variantes', ('frecuencia_fuerza', 'frecuencia_fuerza'),
                  (a.at[v, 'eliminada_por_50000'], b.at[v, 'eliminada_por_50000']), r)
    for v in ('imc', 'trabaja_actualmente'):
        comprobar(g, f'{v}: redundante solo en el estándar', ('redundante', 'seleccionada'),
                  (a.at[v, 'decision_50000'], b.at[v, 'decision_50000']), r)
    return {'q_par_estandar': {v: float(a.at[v, 'q_par_50000']) for v in ('imc', 'trabaja_actualmente')}}


def random_forest():
    g = 'Random Forest'
    r = leer(RF / 'rendimiento_modelos.csv').set_index('modelo')
    esperado = {'A': (529, 3, 0.538), 'B': (529, 30, 0.622), 'C0': (287, 29, 0.628), 'C1': (287, 31, 0.659),
                'D0': (239, 30, 0.645), 'D1': (239, 31, 0.654)}
    for m, (n, nv, auc) in esperado.items():
        comprobar(g, f'{m}: n', n, int(r.at[m, 'n']), RF / 'rendimiento_modelos.csv')
        comprobar(g, f'{m}: variables', nv, int(r.at[m, 'n_variables']), RF / 'rendimiento_modelos.csv')
        comprobar(g, f'{m}: ROC-AUC de evaluación', auc, round(float(r.at[m, 'roc_auc_evaluacion']), 3), RF / 'rendimiento_modelos.csv', tol=5e-4)
        comprobar(g, f'{m}: ROC-AUC de entrenamiento supera al de evaluación en más de 0,25', True,
                  bool(r.at[m, 'roc_auc_diferencia_ent_eval'] > 0.25), RF / 'rendimiento_modelos.csv')
    c = leer(RF / 'comparacion_modelos.csv')
    roc = c[c['metrica'] == 'roc_auc'].set_index(['modelo', 'referencia'])
    for par, lectura, positiva in ((('B', 'A'), 'Mejora respaldada', True), (('C1', 'C0'), 'Sin diferencia clara', False),
                                   (('D1', 'D0'), 'Sin diferencia clara', False)):
        f = roc.loc[par]
        comprobar(g, f'{par[0]} frente a {par[1]}: lectura', lectura, f['lectura'], RF / 'comparacion_modelos.csv')
        comprobar(g, f'{par[0]} frente a {par[1]}: IC 95 % excluye 0', positiva, bool(f['ic95_inferior'] > 0), RF / 'comparacion_modelos.csv')
    azar = leer(RF / 'pruebas_azar.csv')
    a = azar[azar['metrica'] == 'roc_auc'].set_index('modelo')
    comprobar(g, 'A no se separa del azar (k de 200)', 23, int(a.at['A', 'k_mayores_o_iguales']), RF / 'pruebas_azar.csv')
    for m in ('B', 'C0', 'C1', 'D0', 'D1'):
        comprobar(g, f'{m}: ninguna permutación de 200 lo iguala', 0, int(a.at[m, 'k_mayores_o_iguales']), RF / 'pruebas_azar.csv')
    s = leer(RF / 'shannon_vs_rf.csv')
    comprobar(g, 'Variables en la comparación con Shannon', 33, len(s), RF / 'shannon_vs_rf.csv')
    comprobar(g, 'Clasificación de consistencia',
              {'Sin respaldo en ninguno': 21, 'Solo Random Forest': 6, 'Coinciden ambos métodos': 5, 'Solo Shannon': 1},
              s['consistencia'].value_counts().to_dict(), RF / 'shannon_vs_rf.csv')
    comprobar(g, 'Coinciden ambos métodos',
              {'imc', 'trabaja_actualmente', 'dias_ejercicio_semana', 'frecuencia_bajo_impacto', 'lugar_trabajo_comprensivo'},
              set(s.loc[s['consistencia'] == 'Coinciden ambos métodos', 'variable']), RF / 'shannon_vs_rf.csv')
    comprobar(g, 'Solo Shannon', {'frecuencia_fuerza'}, set(s.loc[s['consistencia'] == 'Solo Shannon', 'variable']), RF / 'shannon_vs_rf.csv')
    texto = RF_REG.read_text(encoding='utf-8')
    comprobar(g, 'Registro: 26 modelos', True, 'Modelos: 26' in texto, RF_REG)
    comprobar(g, 'Registro: scikit-learn 1.6.1', True, 'scikit-learn 1.6.1' in texto, RF_REG)
    pp = leer(RF / 'crudos' / 'rendimiento_particiones.csv')
    for m in esperado:
        comprobar(g, f'{m}: particiones de evaluación', 15, int(((pp['modelo'] == m) & (pp['conjunto'] == 'evaluacion')).sum()),
                  RF / 'crudos' / 'rendimiento_particiones.csv')
    comparar = [{'modelo': a_, 'referencia': b_, 'diferencia': float(roc.loc[(a_, b_), 'diferencia']), 'ic_inf': float(roc.loc[(a_, b_), 'ic95_inferior']),
                 'ic_sup': float(roc.loc[(a_, b_), 'ic95_superior']), 'lectura': roc.loc[(a_, b_), 'lectura']} for a_, b_ in (('B', 'A'), ('C1', 'C0'), ('D1', 'D0'))]
    azar_p = {m: (int(a.at[m, 'k_mayores_o_iguales']) + 1) / 201 for m in esperado}
    lista = s[['variable', 'etiqueta', 'poblacion', 'n', 'consistencia']].to_dict('records')
    return {'lista33': lista, 'comparar': comparar, 'azar_p': azar_p, 'rendimiento': r.loc[list(esperado), ['n', 'n_variables', 'roc_auc_evaluacion', 'roc_auc_de', 'roc_auc_entrenamiento',
                                                  'roc_auc_diferencia_ent_eval', 'balanced_accuracy_evaluacion']].reset_index().to_dict('records'),
            'consistencia': s[s['consistencia'] != 'Sin respaldo en ninguno'][['variable', 'consistencia', 'modelo_rf', 'auc_media', 'orden_en_modelo', 'q_50000', 'su', 'direccion']].to_dict('records')}


def main():
    TABLAS.mkdir(parents=True, exist_ok=True)
    datos = {'35A': fase35a(), 'shannon': shannon(), 'fcbf': fcbf(), 'rf': random_forest()}
    with (TABLAS / 'verificacion_fase35.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(FILAS[0]))
        w.writeheader()
        w.writerows(FILAS)
    datos['n_comprobaciones'] = len(FILAS)
    datos['n_ok'] = sum(x['estado'] == 'OK' for x in FILAS)
    (TABLAS / 'datos_fase35.json').write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(f"{datos['n_ok']} de {len(FILAS)} comprobaciones OK")
    for x in FILAS:
        if x['estado'] != 'OK':
            print('DIFERENCIA', x['grupo'], '|', x['comprobacion'], '| esperado', x['esperado'], '| obtenido', x['obtenido'])


if __name__ == '__main__':
    main()
