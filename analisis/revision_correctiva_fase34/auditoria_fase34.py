"""
Revisión correctiva de la Fase 34: diagnóstico de solo lectura.

Uso, desde la raíz del proyecto:
    python analisis/revision_correctiva_fase34/auditoria_fase34.py

Qué hace:
  - Repite en memoria la limpieza 34B para saber qué celdas se imputaron, sin escribir sus salidas.
  - Calcula tablas descriptivas y de sensibilidad (Spearman, Kruskal-Wallis, chi²).
  - Escribe únicamente en analisis/revision_correctiva_fase34/tablas/.

Qué no hace: no modifica datos ni figuras, no ejecuta el EDA, no calcula SU ni permutaciones de Shannon,
no entrena Random Forest. La versión verdadera del simulador solo se usa como diagnóstico de la simulación:
nunca corrige ni selecciona respuestas del conjunto analítico.
"""
import json
import sys

sys.dont_write_bytecode = True

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(RAIZ / 'analisis'))

from eda import estadistica as E  # noqa: E402
from eda import variables as V  # noqa: E402
from limpieza import reglas  # noqa: E402
from limpieza.evaluacion import evaluar  # noqa: E402

TABLAS = AQUI / 'tablas'
TABLAS.mkdir(exist_ok=True)
SUCIO = RAIZ / 'datos' / 'sintetico' / 'dataset_usuaria_sucio.csv'
VERDAD = RAIZ / 'datos' / 'sintetico' / 'dataset_usuaria_verdad.csv'
BITACORA = RAIZ / 'datos' / 'sintetico' / 'bitacora_suciedad.csv'
LIMPIO = RAIZ / 'datos' / 'limpio_usuaria' / 'dataset_usuaria_limpio.csv'
RES = RAIZ / 'analisis' / 'resultados' / 'usuaria'
REV33 = RAIZ / 'analisis' / 'reunion_2026-11-03' / 'revision_33_variables'
REV34 = RAIZ / 'analisis' / 'reunion_2026-11-03'
RF33 = RAIZ / 'analisis' / 'random_forest_revision_35b_33_variables'
ORDEN_SEV = list(V.ORDEN_SEVERIDAD)
R = {}          # resumen para el informe


def leer(ruta):
    return pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding='utf-8-sig')


def guardar(tabla, nombre):
    tabla.to_csv(TABLAS / f'{nombre}.csv', index=False, encoding='utf-8-sig')
    return tabla


# ---------------------------------------------------------------- reconstrucción

def reconstruir():
    crudo = leer(SUCIO)
    captura = {}
    o8, o9 = reglas.p8_condicionales, reglas.p9_imputacion

    def c8(df, *a, **k):
        captura['pre8'] = df.copy()
        return o8(df, *a, **k)

    def c9(df, *a, **k):
        captura['pre9'] = df.copy()
        return o9(df, *a, **k)

    reglas.p8_condicionales, reglas.p9_imputacion = c8, c9
    try:
        limpio, excluidas, _, _ = reglas.limpiar(crudo)
    finally:
        reglas.p8_condicionales, reglas.p9_imputacion = o8, o9
    # La limpieza en memoria debe ser idéntica al archivo: si no, las marcas no valdrían.
    disco = leer(LIMPIO)
    memoria = limpio.astype(object).where(limpio.notna(), '').astype(str)
    distintas = int((memoria[disco.columns].to_numpy() != disco.to_numpy()).sum())
    R['reconstruccion'] = {'filas_memoria': len(limpio), 'filas_disco': len(disco), 'celdas_distintas': distintas}
    if distintas:
        pares = [(c, int((memoria[c].to_numpy() != disco[c].to_numpy()).sum())) for c in disco.columns
                 if (memoria[c].to_numpy() != disco[c].to_numpy()).any()]
        R['reconstruccion']['columnas_distintas'] = pares[:20]
    return limpio, excluidas, captura['pre8'], captura['pre9'], disco


LIM, EXC, PRE8, PRE9, DISCO = reconstruir()
L = DISCO.replace('', np.nan).set_index('participante_id')
P8 = PRE8.set_index('participante_id').reindex(L.index)
P9 = PRE9.set_index('participante_id').reindex(L.index)
EN_529 = L['mrs_completo'] == '1'
M = L[EN_529].copy()
ids = M.index
Y = pd.to_numeric(M['mrs_severidad'].map({s: i for i, s in enumerate(ORDEN_SEV)}))
TOTAL = pd.to_numeric(M['mrs_total'])
SEVERO = (TOTAL >= 16).astype(int)
VERD = leer(VERDAD).drop_duplicates('participante_id').set_index('participante_id').reindex(ids)


def imputada(c):
    """Vacía justo antes de imputar (paso 9) y con valor en el conjunto limpio."""
    return (P9[c].isna() & L[c].notna()).reindex(ids)


def deducida(c):
    """Vacía antes del paso de condicionales y con valor después: es lógica, no imputación."""
    return (P8[c].isna() & P9[c].notna()).reindex(ids)


def spearman(x, mascara=None):
    x = pd.to_numeric(x, errors='coerce')
    k = x.notna() if mascara is None else x.notna() & mascara
    if x[k].nunique() < 2:
        return int(k.sum()), np.nan, np.nan
    rho, p = stats.spearmanr(x[k], Y[k])
    return int(k.sum()), float(rho), float(p)


def binaria(s):
    return s.map(V.BINARIAS)


# ---------------------------------------------------------------- familia FDR original

def familia(grupos):
    t = pd.concat([E.cruce_con_mrs(DF_EDA, list(g), rol, resultado='severidad') for g, rol in grupos])
    return E.corregir_fdr(t)


DF_EDA = L.reset_index().copy()
DF_EDA['severidad'] = E.severidad_codigo(DF_EDA)
PRINCIPAL = familia(((V.PREDICTORES, 'predictor'), (V.PREDICTORES_TRABAJO, 'predictor (trabajo)'),
                     (V.CONTROL_USUARIA, 'control'), (V.OTRAS_USUARIA, 'otra')))
SECUNDARIA = familia(((V.GINECOLOGICAS, 'ginecológica'), (V.SALUD_USUARIA, 'salud')))
GUARDADA = pd.read_csv(RES / 'asociacion_severidad.csv', encoding='utf-8-sig')
g = GUARDADA[GUARDADA['familia'] == 'principal'].set_index('variable')
f = PRINCIPAL.set_index('variable').reindex(g.index)
R['familia'] = {
    'n_principal': len(PRINCIPAL), 'n_secundaria': len(SECUNDARIA),
    'max_dif_p': float((g['p'] - f['p']).abs().max()), 'max_dif_q': float((g['p_ajustado'] - f['p_ajustado']).abs().max()),
    'max_dif_efecto': float((g['efecto'] - f['efecto']).abs().max()),
    'variables_iguales': sorted(g.index) == sorted(PRINCIPAL['variable']),
}
guardar(pd.DataFrame({'variable': g.index, 'prueba': g['prueba'].values, 'n': g['n'].values, 'efecto_guardado': g['efecto'].values,
                      'efecto_recalculado': f['efecto'].values, 'p_guardado': g['p'].values, 'p_recalculado': f['p'].values,
                      'q_guardado': g['p_ajustado'].values, 'q_recalculado': f['p_ajustado'].values}), 'verificacion_familia_fdr')


def q_con(variable, p_nuevo):
    """q de `variable` en la familia principal si solo cambia su p. Las otras 40 pruebas quedan iguales."""
    t = PRINCIPAL.set_index('variable')['p'].copy()
    t[variable] = p_nuevo
    return float(pd.Series(stats.false_discovery_control(t.to_numpy(), method='bh'), index=t.index)[variable])


def q_original(variable):
    return float(PRINCIPAL.set_index('variable').at[variable, 'p_ajustado'])


# ---------------------------------------------------------------- 1. Diabetes

def fila_grupo(nombre, k):
    n = int(k.sum())
    fila = {'grupo': nombre, 'n': n, 'severas_n': int(SEVERO[k].sum()), 'severas_pct': 100 * SEVERO[k].mean() if n else np.nan}
    for s in ORDEN_SEV:
        fila[f'{s}_n'] = int((M.loc[k, 'mrs_severidad'] == s).sum())
        fila[f'{s}_pct'] = 100 * (M.loc[k, 'mrs_severidad'] == s).mean() if n else np.nan
    fila['mrs_media'] = float(TOTAL[k].mean()) if n else np.nan
    fila['mrs_mediana'] = float(TOTAL[k].median()) if n else np.nan
    return fila


def diabetes():
    c = 'usa_medicamentos_diabetes'
    imp = imputada(c)
    si, no = M[c] == 'SI', M[c] == 'NO'
    filas = []
    for base, mascara in (('Todas (529)', pd.Series(True, index=ids)), ('Solo observadas', ~imp)):
        for nombre, k in (('Sí', si), ('No', no)):
            d = fila_grupo(nombre, k & mascara)
            d['base'] = base
            d['observadas'] = int((k & mascara & ~imp).sum())
            d['imputadas'] = int((k & mascara & imp).sum())
            d['edad_media'] = float(pd.to_numeric(M.loc[k & mascara, 'edad']).mean())
            d['imc_observado_media'] = float(pd.to_numeric(M.loc[k & mascara, 'imc'], errors='coerce').mean())
            filas.append(d)
    tabla = guardar(pd.DataFrame(filas), 'diabetes_tabla_cruzada')

    x = binaria(M[c])
    pruebas = []
    for base, mascara in (('Todas (529)', pd.Series(True, index=ids)), ('Solo observadas', ~imp)):
        n, rho, p = spearman(x, mascara)
        rho_total, p_total = stats.spearmanr(x[mascara], TOTAL[mascara])
        cruz = pd.crosstab(x[mascara], SEVERO[mascara]).reindex(index=[1, 0], columns=[1, 0])
        odds, p_fisher = stats.fisher_exact(cruz.to_numpy())
        mw = stats.mannwhitneyu(Y[mascara & si], Y[mascara & no])
        pruebas.append({'base': base, 'n': n, 'rho_severidad_4': rho, 'p_sin_ajustar': p,
                        'q_familia_41': q_con(c, p), 'rho_mrs_total': float(rho_total), 'p_mrs_total': float(p_total),
                        'odds_ratio_severo': float(odds), 'p_fisher_severo': float(p_fisher), 'p_mann_whitney': float(mw.pvalue)})
    guardar(pd.DataFrame(pruebas), 'diabetes_pruebas')

    conjunta = pd.concat([PRINCIPAL.drop(columns='p_ajustado'), SECUNDARIA.drop(columns='p_ajustado')])
    q51 = E.corregir_fdr(conjunta).set_index('variable').at[c, 'p_ajustado']
    orden = PRINCIPAL.sort_values('p').reset_index(drop=True)
    rango = int(orden.index[orden['variable'] == c][0]) + 1
    p_orig = float(orden.at[rango - 1, 'p'])

    # Codificación: del texto sucio al limpio y de ahí a 1/0.
    sucio = leer(SUCIO).drop_duplicates('participante_id').set_index('participante_id').reindex(ids)
    crudo = sucio[c].str.strip().replace('', '(vacío)')
    cod = pd.crosstab(crudo, M[c]).reset_index().rename(columns={c: 'valor_en_sucio'})
    guardar(cod, 'diabetes_codificacion')
    verdad = pd.crosstab([imp.map({True: 'Imputada', False: 'Observada'}).rename('situacion'), M[c].rename('limpio')],
                         VERD[c].rename('simulador')).reset_index()
    guardar(verdad, 'diabetes_diagnostico_verdad')

    rel = pd.read_csv(REV34 / 'permutaciones_50000' / 'relevancia_34.csv', encoding='utf-8-sig').set_index('variable').loc[c]
    obs = M.loc[~imp, c]
    R['diabetes'] = {
        'imputadas_529': int(imp.sum()), 'imputadas_a': M.loc[imp, c].value_counts().to_dict(),
        'imputados_resumen_34D': 24, 'rango_bh': rango, 'p_original': p_orig,
        'q_verificado_a_mano': p_orig * len(PRINCIPAL) / rango, 'q_familia_principal': q_original(c),
        'q_familia_conjunta_51': float(q51), 'familias_rol': 'control / principal',
        'codigo_si': int(V.BINARIAS['SI']), 'codigo_no': int(V.BINARIAS['NO']),
        'x_igual_codigo': bool((x == (M[c] == 'SI').astype(int)).all()),
        'dominancia_todas': 100 * (M[c] == 'NO').mean(), 'dominancia_observadas': 100 * (obs == 'NO').mean(),
        'su_34': float(rel['su']), 'p_shannon_50000': float(rel['p']), 'q_shannon_34': float(rel['q']),
        'imputadas_erroneas_segun_verdad': int((M.loc[imp, c] != VERD.loc[imp, c]).sum()),
    }
    return tabla


# ---------------------------------------------------------------- 2. Trabajo y cuidados

def situacion(c):
    imp, ded = imputada(c), deducida(c)
    return pd.Series(np.select([imp, ded], ['Imputada', 'Deducida'], 'Respondida'), index=ids)


def sens(variable, escenario, x, mascara=None, q=True, nota=''):
    n, rho, p = spearman(x, mascara)
    return {'variable': variable, 'escenario': escenario, 'n': n, 'rho': rho, 'p_sin_ajustar': p,
            'q_familia_41': q_con(variable, p) if q and variable in set(PRINCIPAL['variable']) else np.nan, 'nota': nota}


def trabajo_cuidados():
    tr, cu = M['trabaja_actualmente'], M['cuida_otras_personas']
    st, sc = situacion('trabaja_actualmente'), situacion('cuida_otras_personas')
    ti, ci = st == 'Imputada', sc == 'Imputada'
    verdad_tr = VERD['trabaja_actualmente'].str.strip()
    verdad_cu = VERD['cuida_otras_personas'].str.strip()

    # Grupos por condición de la respuesta
    filas = []
    for var, sit, vals, verdad, si in (('trabaja_actualmente', st, tr, verdad_tr, 'True'), ('cuida_otras_personas', sc, cu, verdad_cu, 'SI')):
        for (s, v), idx in vals.groupby([sit, vals]).groups.items():
            k = pd.Series(ids.isin(idx), index=ids)
            d = fila_grupo(f'{s} · {v}', k)
            d['variable'] = var
            d['coincide_con_verdad'] = int((verdad[k] == v).sum())
            d['distinta_de_verdad'] = int((verdad[k] != v).sum())
            filas.append(d)
    guardar(pd.DataFrame(filas), 'imputacion_grupos')

    # Indicadores de auditoría: solo en esta carpeta, sin tocar el conjunto.
    indicador = pd.DataFrame({'trabaja_situacion': st, 'cuida_situacion': sc,
                              'doble_carga_depende_de_imputada': (ti | ci).astype(int),
                              'cantidad_imputada': imputada('cantidad_personas_cuida').astype(int),
                              'sobrecarga_imputada': imputada('sobrecarga_fisica_emocional').astype(int),
                              'lugar_imputada': imputada('lugar_trabajo_comprensivo').astype(int),
                              'estres_imputada': imputada('estres_entorno_laboral').astype(int)})
    guardar(indicador.reset_index(), 'indicadores_auditoria')

    x_tr = binaria(tr)
    x_tr_no = x_tr.where(~ti, 0)
    x_tr_v = binaria(verdad_tr)
    x_cu = binaria(cu)
    x_cu_v = binaria(verdad_cu)
    doble = pd.to_numeric(M['doble_carga'])
    cant = pd.to_numeric(M['cantidad_personas_cuida'].where(cu != 'NO', '0'), errors='coerce')
    cant_imp = imputada('cantidad_personas_cuida')
    sob = pd.to_numeric(M['sobrecarga_fisica_emocional'].where(cu != 'NO', '0'), errors='coerce')
    sob_imp = imputada('sobrecarga_fisica_emocional')
    lug, est = pd.to_numeric(M['lugar_trabajo_comprensivo'], errors='coerce'), pd.to_numeric(M['estres_entorno_laboral'], errors='coerce')
    lug_imp, est_imp = imputada('lugar_trabajo_comprensivo'), imputada('estres_entorno_laboral')
    cuid = cu == 'SI'

    filas = [
        sens('trabaja_actualmente', 'Actual', x_tr),
        sens('trabaja_actualmente', 'Solo respondidas (sin las imputadas)', x_tr, ~ti),
        sens('trabaja_actualmente', 'Hipótesis: las imputadas valen «No»', x_tr_no, nota='cota; no es una corrección'),
        sens('trabaja_actualmente', 'Diagnóstico: valor del simulador', x_tr_v, nota='solo diagnóstico de la simulación'),
        sens('cuida_otras_personas', 'Actual', x_cu, q=False),
        sens('cuida_otras_personas', 'Solo respondidas o deducidas', x_cu, ~ci, q=False),
        sens('cuida_otras_personas', 'Diagnóstico: valor del simulador', x_cu_v, q=False, nota='solo diagnóstico de la simulación'),
        sens('doble_carga', 'Actual', doble),
        sens('doble_carga', 'Sin filas que dependen de una imputada', doble, ~(ti | ci)),
        sens('doble_carga', 'Diagnóstico: valor del simulador', (x_tr_v * x_cu_v), nota='solo diagnóstico de la simulación'),
        sens('cantidad_personas_cuida', 'Actual (0 si no cuida)', cant),
        sens('cantidad_personas_cuida', 'Sin las 21 «No» imputadas', cant, ~ci),
        sens('cantidad_personas_cuida', 'Sin «No» imputadas ni cantidades imputadas', cant, ~ci & ~cant_imp),
        sens('cantidad_personas_cuida', 'Solo cuidadoras (251)', cant, cuid, q=False),
        sens('cantidad_personas_cuida', 'Solo cuidadoras con cantidad observada', cant, cuid & ~cant_imp, q=False),
        sens('sobrecarga_fisica_emocional', 'Actual (0 si no cuida)', sob),
        sens('sobrecarga_fisica_emocional', 'Sin «No» imputadas ni sobrecarga imputada', sob, ~ci & ~sob_imp),
        sens('sobrecarga_fisica_emocional', 'Solo cuidadoras (251)', sob, cuid, q=False),
        sens('sobrecarga_fisica_emocional', 'Solo cuidadoras con respuesta observada', sob, cuid & ~sob_imp, q=False),
        sens('lugar_trabajo_comprensivo', 'Actual (287)', lug),
        sens('lugar_trabajo_comprensivo', 'Solo observadas', lug, ~lug_imp),
        sens('estres_entorno_laboral', 'Actual (287)', est),
        sens('estres_entorno_laboral', 'Solo observadas', est, ~est_imp),
    ]
    guardar(pd.DataFrame(filas), 'sensibilidad_asociaciones')

    # Comparación trabaja vs. no trabaja en severo (chi²), con y sin imputadas
    comp = []
    for nombre, x, k in (('Actual', x_tr, pd.Series(True, index=ids)), ('Solo respondidas', x_tr, ~ti),
                         ('Hipótesis: imputadas = No', x_tr_no, pd.Series(True, index=ids)),
                         ('Diagnóstico: simulador', x_tr_v, pd.Series(True, index=ids))):
        t = pd.crosstab(x[k], SEVERO[k]).reindex(index=[1, 0], columns=[1, 0]).fillna(0)
        chi = stats.chi2_contingency(t.to_numpy(), correction=False)
        s1, s0 = x[k] == 1, x[k] == 0
        comp.append({'escenario': nombre, 'n_trabaja': int(s1.sum()), 'n_no_trabaja': int(s0.sum()),
                     'severas_trabaja_pct': 100 * SEVERO[k][s1].mean(), 'severas_no_trabaja_pct': 100 * SEVERO[k][s0].mean(),
                     'mrs_media_trabaja': float(TOTAL[k][s1].mean()), 'mrs_media_no_trabaja': float(TOTAL[k][s0].mean()),
                     'chi2_p_sin_ajustar': float(chi[1])})
    guardar(pd.DataFrame(comp), 'sensibilidad_trabaja_grupos')

    # Poblaciones
    d35 = pd.read_csv(RAIZ / 'datos' / 'analitico' / 'dataset_fase35_33_variables.csv', dtype=str, encoding='utf-8-sig').set_index('participante_id').reindex(ids)
    lab = M['lugar_trabajo_comprensivo'].notna() | M['estres_entorno_laboral'].notna()
    v_tr, v_cu = verdad_tr == 'True', verdad_cu == 'SI'
    poblaciones = []

    def pob(nombre, k, verdad=None, etiqueta=''):
        poblaciones.append({'poblacion': nombre, 'n': int(k.sum()), 'segun_simulador_si': int(verdad[k].sum()) if verdad is not None else np.nan,
                            'segun_simulador_no': int((~verdad[k]).sum()) if verdad is not None else np.nan, 'nota': etiqueta})

    es_tr, es_cu = tr == 'True', cu == 'SI'
    pob('Trabaja = Sí en el conjunto limpio', es_tr, v_tr, 'denominador de 34C y 34D')
    pob('  Respondida o deducida', es_tr & ~ti, v_tr, 'población laboral de la Fase 35B')
    pob('  Imputada', ti, v_tr, 'sin ninguna respuesta laboral')
    pob('Trabaja = No', tr == 'False', v_tr, '')
    pob('Con respuesta laboral (lugar o estrés)', lab, v_tr, '')
    pob('Laboral con ambas observadas', es_tr & ~ti & ~lug_imp & ~est_imp, v_tr, '')
    pob('Cuida = Sí en el conjunto limpio', es_cu, v_cu, 'denominador de 34D')
    pob('  Con sobrecarga observada', es_cu & ~sob_imp, v_cu, 'población de cuidadoras de la Fase 35B')
    pob('  Con sobrecarga imputada', es_cu & sob_imp, v_cu, '')
    pob('Cuida = No respondida', (cu == 'NO') & ~ci, v_cu, '')
    pob('Cuida = No imputada', ci, v_cu, 'cantidad 0 y doble carga 0')
    guardar(pd.DataFrame(poblaciones), 'poblaciones')

    pob35 = pd.read_csv(REV33 / 'permutaciones_50000' / 'poblaciones.csv', encoding='utf-8-sig')
    d1, d0 = doble == 1, doble == 0
    R['imputacion'] = {
        'trabaja_situacion': st.value_counts().to_dict(), 'cuida_situacion': sc.value_counts().to_dict(),
        'trabaja_imputadas_erroneas': int((tr[ti] != verdad_tr[ti]).sum()), 'cuida_imputadas_erroneas': int((cu[ci] != verdad_cu[ci]).sum()),
        'doble1_con_trabaja_imputada': int((d1 & ti).sum()), 'doble0_con_cuida_imputada': int((d0 & ci).sum()),
        'doble_con_alguna_imputada': int((ti | ci).sum()), 'doble_ambas_imputadas': int((ti & ci).sum()),
        'doble_distinta_de_verdad': int((doble != (x_tr_v * x_cu_v)).sum()), 'doble1_mal': int((d1 & ((x_tr_v * x_cu_v) == 0)).sum()),
        'doble0_mal': int((d0 & ((x_tr_v * x_cu_v) == 1)).sum()),
        'cantidad_imputadas': int(cant_imp.sum()), 'cantidad_ceros_por_cuida_imputada': int((ci & (cant == 0)).sum()),
        'sobrecarga_imputadas': int(sob_imp.sum()), 'lugar_imputadas': int(lug_imp.sum()), 'estres_imputadas': int(est_imp.sum()),
        'imputadas_trabaja_en_lugar_35': d35.loc[ti, 'lugar_trabajo_comprensivo'].value_counts(dropna=False).to_dict(),
        'imputadas_trabaja_en_estres_35': d35.loc[ti, 'estres_entorno_laboral'].value_counts(dropna=False).to_dict(),
        'no_trabaja_en_lugar_35': d35.loc[tr == 'False', 'lugar_trabajo_comprensivo'].value_counts(dropna=False).to_dict(),
        'poblaciones_35b': pob35.to_dict('records'),
        'laboral_coincide': bool((es_tr & ~ti).sum() == 287 and lab.sum() == 287 and (lab == (es_tr & ~ti)).all()),
        'cuida_columna_en_35': 'cuida_otras_personas' in d35.columns, 'doble_columna_en_35': 'doble_carga' in d35.columns,
    }


# ---------------------------------------------------------------- 3. IMC

def imc():
    cat = M['imc_categoria']
    filas = [fila_grupo(c, cat == c) for c in V.ORDEN_IMC]
    guardar(pd.DataFrame(filas), 'imc_categorias')

    info = cat != 'no informado'
    t = [fila_grupo('IMC informado', info), fila_grupo('IMC no informado', ~info)]
    guardar(pd.DataFrame(t), 'imc_faltante_descriptivo')
    cruz = pd.crosstab(info, M['mrs_severidad'])
    chi_falt = stats.chi2_contingency(cruz.to_numpy())
    mw_falt = stats.mannwhitneyu(Y[info], Y[~info])

    def kw(nombre, grupos, q=True):
        grupos = {k: Y[v] for k, v in grupos.items()}
        h, p = stats.kruskal(*grupos.values())
        n = sum(len(v) for v in grupos.values())
        return {'analisis': nombre, 'prueba': 'Kruskal-Wallis', 'n': n, 'grupos': len(grupos), 'efecto': (h - len(grupos) + 1) / (n - len(grupos)), 'medida': 'ε²',
                'p_sin_ajustar': float(p), 'q_familia_41': q_con('imc_categoria', float(p)) if q else np.nan}

    k = {c: cat == c for c in V.ORDEN_IMC}
    ord_cat = cat.map({'bajo peso': 0, 'normal': 1, 'sobrepeso': 2, 'obesidad': 3})
    n_o, rho_o, p_o = spearman(ord_cat)
    n_n, rho_n, p_n = spearman(pd.to_numeric(M['imc'], errors='coerce'))
    tabla = [
        kw('Original 34C: con «no informado», sin bajo peso', {c: k[c] for c in ('normal', 'sobrepeso', 'obesidad', 'no informado')}),
        kw('Solo observado: 3 categorías, sin bajo peso', {c: k[c] for c in ('normal', 'sobrepeso', 'obesidad')}),
        kw('Solo observado: 4 categorías, con bajo peso (n = 2)', {c: k[c] for c in ('bajo peso', 'normal', 'sobrepeso', 'obesidad')}),
        kw('Solo observado: bajo peso unido a normal', {'bajo o normal': k['bajo peso'] | k['normal'], 'sobrepeso': k['sobrepeso'], 'obesidad': k['obesidad']}),
        {'analisis': 'Solo observado: categorías ordenadas', 'prueba': 'Spearman', 'n': n_o, 'grupos': 4, 'efecto': rho_o, 'medida': 'rho', 'p_sin_ajustar': p_o, 'q_familia_41': q_con('imc_categoria', p_o)},
        {'analisis': 'IMC numérico observado (ya en 34C)', 'prueba': 'Spearman', 'n': n_n, 'grupos': np.nan, 'efecto': rho_n, 'medida': 'rho', 'p_sin_ajustar': p_n, 'q_familia_41': q_original('imc')},
    ]
    guardar(pd.DataFrame(tabla), 'imc_pruebas')

    pares = []
    for a, b in (('normal', 'sobrepeso'), ('normal', 'obesidad'), ('sobrepeso', 'obesidad')):
        m = stats.mannwhitneyu(Y[k[a]], Y[k[b]])
        pares.append({'comparacion': f'{a} vs {b}', 'n_a': int(k[a].sum()), 'n_b': int(k[b].sum()), 'p_sin_ajustar': float(m.pvalue)})
    pares = pd.DataFrame(pares)
    pares['q_entre_3_pares'] = stats.false_discovery_control(pares['p_sin_ajustar'], method='bh')
    guardar(pares, 'imc_pares')

    # ¿Cambia alguna otra conclusión de la familia si solo se reemplaza la p de imc_categoria?
    base = PRINCIPAL.set_index('variable')['p'].copy()
    nueva = base.copy()
    nueva['imc_categoria'] = tabla[1]['p_sin_ajustar']
    q0 = pd.Series(stats.false_discovery_control(base.to_numpy(), method='bh'), index=base.index)
    q1 = pd.Series(stats.false_discovery_control(nueva.to_numpy(), method='bh'), index=base.index)
    R['imc_familia'] = {'q05_antes': sorted(q0[q0 < 0.05].index), 'q05_despues': sorted(q1[q1 < 0.05].index),
                        'cambian_de_lado': sorted(q0.index[(q0 < 0.05) != (q1 < 0.05)])}

    bp = M.loc[k['bajo peso'], ['imc', 'mrs_total', 'mrs_severidad']]
    R['imc'] = {
        'bajo_peso': bp.to_dict('records'), 'chi_faltante_p': float(chi_falt[1]), 'mw_faltante_p': float(mw_falt.pvalue),
        'original_n_guardado': int(g.at['imc_categoria', 'n']), 'original_p_guardado': float(g.at['imc_categoria', 'p']),
        'original_q_guardado': float(g.at['imc_categoria', 'p_ajustado']), 'original_efecto_guardado': float(g.at['imc_categoria', 'efecto']),
    }


# ---------------------------------------------------------------- 4. Figuras

def figuras():
    res = pd.read_csv(RES / 'eda_univariado_resumen.csv', encoding='utf-8-sig')
    filas = []
    for _, f in res.iterrows():
        v = f['variable']
        if v not in L.columns or v not in P9.columns:
            continue
        imp = imputada(v)
        n_imp = int(imp.sum())
        # Base de la figura: quienes tienen valor en el limpio entre las 529.
        s = M[v].dropna()
        anotado = f['imputados_34B'] if pd.notna(f['imputados_34B']) else 0
        tiene_marca = f'{v}_imputado' in L.columns
        dom_cod = s.value_counts(normalize=True).max() * 100 if len(s) else np.nan
        s_obs = s[~imp.reindex(s.index)]
        dom_obs = s_obs.value_counts(normalize=True).max() * 100 if len(s_obs) else np.nan
        tipo = str(f['tipo'])
        # Solo se compara si la figura usa las mismas categorías que el código crudo (sin tramos ni agrupaciones).
        comparable = tipo != 'selección múltiple' and pd.notna(dom_cod) and abs(f['porcentaje_dominante'] - dom_cod) < 0.01
        cambia = comparable and pd.notna(dom_obs) and (
            (f['porcentaje_dominante'] >= 80) != (dom_obs >= 80) or (f['porcentaje_dominante'] > 85) != (dom_obs > 85))
        filas.append({
            'variable': v, 'etiqueta': f['etiqueta'], 'figura': f'univariado_{v}.png', 'tipo': tipo, 'n_valido_figura': int(f['n_valido']),
            'faltante_figura': int(f['n_faltante']), 'imputadas_exactas_529': n_imp, 'imputados_34B_resumen': int(anotado), 'marca_en_limpio': tiene_marca,
            'observadas': int(f['n_valido']) - n_imp, 'pct_imputado': 100 * n_imp / f['n_valido'] if f['n_valido'] else 0,
            'dominante_figura_pct': f['porcentaje_dominante'], 'dominante_solo_observadas_pct': dom_obs if comparable else np.nan,
            'diferencia_puntos': (f['porcentaje_dominante'] - dom_obs) if comparable else np.nan, 'cambia_tramo_80_85': bool(cambia),
            'denominador': f['denominador'],
        })
    t = guardar(pd.DataFrame(filas), 'auditoria_figuras_34D')
    con = t[t['imputadas_exactas_529'] > 0]

    # Sobrecarga: categoría a categoría
    v = 'sobrecarga_fisica_emocional'
    sob = M.loc[M['cuida_otras_personas'] == 'SI', v]
    imp = imputada(v).reindex(sob.index)
    et = {'1': 'Nunca o casi nunca', '2': 'Rara vez', '3': 'A veces', '4': 'Frecuentemente', '5': 'Siempre'}
    frec = pd.DataFrame({'categoria': [et[k] for k in et], 'n_251': [int((sob == k).sum()) for k in et],
                         'observadas': [int(((sob == k) & ~imp).sum()) for k in et], 'imputadas': [int(((sob == k) & imp).sum()) for k in et]})
    frec['pct_sobre_251'] = 100 * frec['n_251'] / 251
    frec['pct_sobre_239'] = 100 * frec['observadas'] / 239
    guardar(frec, 'sobrecarga_251_239')

    lug = M.loc[M['lugar_trabajo_comprensivo'].notna(), 'lugar_trabajo_comprensivo']
    R['figuras'] = {
        'evaluadas': len(t), 'con_imputadas': len(con),
        'faltante_cero_con_imputadas': int(((con['faltante_figura'] == 0)).sum()),
        'resumen_distinto_de_exacto': int((t['imputados_34B_resumen'] != t['imputadas_exactas_529']).sum()),
        'resumen_sobreestima_sin_marca': t[(t['imputados_34B_resumen'] != t['imputadas_exactas_529'])][['variable', 'imputados_34B_resumen', 'imputadas_exactas_529', 'marca_en_limpio']].to_dict('records'),
        'cambian_tramo': t[t['cambia_tramo_80_85']][['variable', 'dominante_figura_pct', 'dominante_solo_observadas_pct']].to_dict('records'),
        'max_dif_puntos': float(t['diferencia_puntos'].abs().max()),
        'variable_max_dif': t.loc[t['diferencia_puntos'].abs().idxmax(), 'variable'],
        'lugar_neutral_total': int((lug == '3').sum()), 'lugar_neutral_imputadas': int(((lug == '3') & imputada('lugar_trabajo_comprensivo').reindex(lug.index)).sum()),
    }


# ---------------------------------------------------------------- celda correcta y regla de pareja

def celdas_correctas():
    ev = evaluar(LIM, EXC, leer(VERDAD), leer(BITACORA))
    R['evaluacion_claves'] = sorted(ev.keys())
    R['cambios_error'] = int(ev['cambios_error'])
    for clave in ev:
        if isinstance(ev[clave], pd.DataFrame) and 'cambio_relacion_pareja_menopausia' in ev[clave].astype(str).to_string():
            guardar(ev[clave], 'celdas_correctas_cambiadas')
            R['tabla_celdas'] = ev[clave].to_dict('records')


# ---------------------------------------------------------------- integridad de la Fase 35

def integridad():
    filas = []

    def control(nombre, ok, detalle=''):
        filas.append({'comprobacion': nombre, 'resultado': 'OK' if ok else 'FALLA', 'detalle': str(detalle)})

    for B, carpeta in ((10000, 'permutaciones_10000'), (50000, 'permutaciones_50000')):
        t = pd.read_csv(REV33 / carpeta / 'relevancia_33.csv', encoding='utf-8-sig')
        control(f'Shannon {B}: 33 variables', len(t) == 33, len(t))
        # Los CSV guardan valores redondeados: la tolerancia corresponde a ese redondeo, no a una diferencia real.
        dif_p = np.abs(t['p'] - (t['k'] + 1) / (B + 1)).max()
        control(f'Shannon {B}: p = (k + 1) / (B + 1), salvo redondeo del CSV', dif_p < 1e-5, f'dif. máx. {dif_p:.2e}')
        q = stats.false_discovery_control((t['k'] + 1) / (B + 1), method='bh')
        dif_q = np.abs(t['q'] - q).max()
        control(f'Shannon {B}: q = BH de 33, salvo redondeo del CSV', dif_q < 1e-5, f'dif. máx. {dif_q:.2e}')
        sel = sorted(t.loc[t['q'] < 0.10, 'variable'])
        esperadas = sorted(['dias_ejercicio_semana', 'frecuencia_bajo_impacto', 'imc', 'frecuencia_fuerza', 'lugar_trabajo_comprensivo', 'trabaja_actualmente'])
        control(f'Shannon {B}: mismas 6 con q < 0,10', sel == esperadas, ', '.join(sel))
        control(f'Shannon {B}: sin diabetes ni doble carga', not {'usa_medicamentos_diabetes', 'doble_carga'} & set(t['variable']))
    d = pd.read_csv(RAIZ / 'datos' / 'analitico' / 'dataset_fase35_33_variables.csv', dtype=str, encoding='utf-8-sig')
    control('Conjunto de 33: 529 filas', len(d) == 529, len(d))
    control('Conjunto de 33: mismo MRS que el conjunto limpio', (d.set_index('participante_id')['mrs_total'].astype(float).reindex(ids).to_numpy() == TOTAL.to_numpy()).all())
    control('Conjunto de 33: mismo trabaja_actualmente que el limpio', (d.set_index('participante_id')['trabaja_actualmente'].reindex(ids).map({'True': 1, '1': 1, '1.0': 1, 'False': 0, '0': 0, '0.0': 0}).to_numpy() == binaria(M['trabaja_actualmente']).to_numpy()).all())
    rf = pd.read_csv(RF33 / 'resultados' / 'poblaciones.csv', encoding='utf-8-sig').set_index('elemento')['n']
    control('Random Forest: poblaciones 529, 287 y 239', (rf['todas'], rf['trabajadoras'], rf['cuidadoras']) == (529, 287, 239), rf.to_dict())
    reg = (RF33 / 'registro_ejecucion.txt').read_text(encoding='utf-8')
    control('Random Forest: registro con HEAD 745d689', '745d689937a18c35b62fd25eccc401b169b20e11' in reg)
    control('Reconstrucción: limpieza en memoria igual al archivo', R['reconstruccion']['celdas_distintas'] == 0, R['reconstruccion'])
    control('EDA: familia de 41 pruebas igual a la guardada', R['familia']['variables_iguales'] and R['familia']['max_dif_q'] < 1e-4, R['familia'])
    return guardar(pd.DataFrame(filas), 'integridad_fase35')


if __name__ == '__main__':
    diabetes()
    trabajo_cuidados()
    imc()
    figuras()
    celdas_correctas()
    t = integridad()
    fig = pd.read_csv(TABLAS / 'auditoria_figuras_34D.csv', encoding='utf-8-sig').set_index('variable')
    rf = pd.read_csv(RF33 / 'resultados' / 'revision_imputaciones_34B.csv', encoding='utf-8-sig')
    rf['exactas_529'] = rf['variable'].map(fig['imputadas_exactas_529'])
    guardar(rf[rf['identificadas'] != rf['exactas_529']][['variable', 'imputadas_34B', 'identificadas', 'exactas_529', 'tratamiento']], 'rf_identificacion_imputadas')
    (TABLAS / 'resumen.json').write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
    print(t.to_string())
