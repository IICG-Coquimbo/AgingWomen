"""
Pasos del preprocesamiento de la Fase 35A: codificación para el modelado,
imputación del IMC, filtros de baja variabilidad y de redundancia, y
validación contra los supuestos de la simulación.

Todos los umbrales y excepciones vienen de `configuracion.py`.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

from eda import variables as V

from . import configuracion as C

SI_NO = {'SI': 1, 'NO': 0, 'True': 1, 'False': 0, '1': 1, '0': 0}
ORDEN_SANGRADO = {c: i for i, c in enumerate(V.ORDEN_TEXTO['tipo_sangrado'], start=1)}


def menstrua(df):
    """Aún menstrúa = última menstruación hace menos de 12 meses (NaN si no hay fecha)."""
    return V.numerica(df['meses_desde_fum']) < 12


def aplica(df, v):
    """Máscara de quienes debían responder `v` (todas, si la pregunta es general)."""
    if v in ('lugar_trabajo_comprensivo', 'estres_entorno_laboral'):
        return df['trabaja_actualmente'] == 'True'
    if v in ('menstruacion_llega', 'tipo_sangrado', 'usa_metodo_anticonceptivo'):
        return menstrua(df)
    if v == 'tipo_metodo_anticonceptivo':
        return menstrua(df) & (df['usa_metodo_anticonceptivo'] == 'SI')
    return pd.Series(True, index=df.index)


# --- 2.2 IMC ----------------------------------------------------------------------

def imputar_imc(df):
    """IMC continuo imputado con la media de los valores observados + marca de auditoría."""
    imc = V.numerica(df['imc'])
    media = imc.mean()
    marca = imc.isna().astype(int)
    return imc.fillna(media), marca, media


def _describir(x):
    return {'n': int(x.notna().sum()), 'media': x.mean(), 'mediana': x.median(), 'de': x.std(),
            'minimo': x.min(), 'maximo': x.max()}


def sensibilidad_imc(df, imc_imputado, marca):
    """Antes/después de imputar y asociación con el MRS en ambos escenarios."""
    observado = V.numerica(df['imc'])
    total = V.numerica(df['mrs_total'])
    severo = df['severo_mrs']
    filas = []
    for escenario, x, mascara in (('IMC observado (solo quienes informaron)', observado, observado.notna()),
                                  ('IMC imputado por la media (todas)', imc_imputado, imc_imputado.notna())):
        d = _describir(x[mascara])
        rho, p = stats.spearmanr(x[mascara], total[mascara])
        u = stats.mannwhitneyu(x[mascara & (severo == 1)], x[mascara & (severo == 0)])
        filas.append({'escenario': escenario, **d,
                      'n_imputado': int(marca[mascara].sum()), 'pct_imputado': 100 * marca[mascara].mean(),
                      'rho_spearman_mrs_total': rho, 'p_spearman': p,
                      'media_imc_severo': x[mascara & (severo == 1)].mean(),
                      'media_imc_no_severo': x[mascara & (severo == 0)].mean(), 'p_mann_whitney_severo': u.pvalue})
    return pd.DataFrame(filas)


# --- Codificación para el modelado -------------------------------------------------

def codificar(df, v, tipo):
    """
    Columna lista para el modelado:
      - binarias → 1/0; ordinales → su código numérico (tipo de sangrado según su orden);
      - frecuencias condicionales (CERO_SI_NO) → 0 si no realiza la actividad;
      - condicionales que no aplican → NO_APLICA (0) en ordinales, 'NO_APLICA' en nominales;
      - continuas → número; nominales → texto del código.
    """
    s = df[v]
    if v in C.CERO_SI_NO:
        s = s.where(df[C.CERO_SI_NO[v]] != 'NO', '0')
    if tipo == 'binaria':
        x = s.map(SI_NO)
    elif v == 'tipo_sangrado':
        x = s.map(ORDEN_SANGRADO)
    elif tipo in ('ordinal', 'continua'):
        x = V.numerica(s)
    else:
        x = s.copy()
    if v in C.CONDICIONALES_NO_APLICA:
        fuera = ~aplica(df, v).fillna(False)
        x = x.astype(object) if tipo == 'nominal' else x
        x[fuera] = 'NO_APLICA' if tipo == 'nominal' else C.NO_APLICA
    return x


# --- 2.5 Baja variabilidad -----------------------------------------------------------

def dominancia(x):
    conteo = x.value_counts(dropna=True)
    p = conteo / conteo.sum()
    entropia = float(-(p * np.log2(p)).sum())
    return conteo.index[0], 100 * p.iloc[0], entropia


def filtro_dominancia(X, tipos):
    filas = []
    for v in X.columns:
        if tipos[v] == 'continua':
            continue
        cat, pct, h = dominancia(X[v])
        if tipos[v] == 'binaria':
            cat = {1: 'Sí', 0: 'No'}.get(cat, cat)
        if pct > C.UMBRAL_ELIMINAR_DOMINANCIA:
            if v in C.CONSERVAR_PESE_A_DOMINANCIA:
                decision, motivo = 'conservar (excepción)', C.CONSERVAR_PESE_A_DOMINANCIA[v]
            else:
                decision = 'eliminar'
                motivo = (f'La categoría dominante supera el {C.UMBRAL_ELIMINAR_DOMINANCIA} %: casi no varía y '
                          'no puede discriminar entre participantes.')
                if cat == 'NO_APLICA':
                    motivo += (' La categoría dominante es "no aplica": la pregunta solo corresponde a muy pocas '
                               'participantes, así que en el conjunto general casi no aporta información.')
        elif pct >= C.UMBRAL_REVISAR_DOMINANCIA:
            decision = 'revisar → conservar'
            motivo = (f'Entre {C.UMBRAL_REVISAR_DOMINANCIA} % y {C.UMBRAL_ELIMINAR_DOMINANCIA} %: se conserva por '
                      'relevancia (decisión de la usuaria 2026-10-28).')
            if v in C.CONSERVAR_PESE_A_DOMINANCIA:
                motivo += ' ' + C.CONSERVAR_PESE_A_DOMINANCIA[v]
        else:
            decision, motivo = 'conservar', f'Ninguna categoría llega al {C.UMBRAL_REVISAR_DOMINANCIA} %.'
        filas.append({'variable': v, 'etiqueta': V.etiqueta(v), 'categoria_dominante': cat,
                      'porcentaje_dominancia': pct, 'entropia_bits': h, 'decision': decision,
                      'justificacion': motivo})
    return pd.DataFrame(filas).sort_values('porcentaje_dominancia', ascending=False, ignore_index=True)


# --- 2.6 Redundancia ------------------------------------------------------------------

def cramer_v(a, b):
    tabla = pd.crosstab(a, b)
    if min(tabla.shape) < 2:
        return np.nan
    chi2 = stats.chi2_contingency(tabla, correction=False)[0]
    n = tabla.to_numpy().sum()
    return float(np.sqrt(chi2 / (n * (min(tabla.shape) - 1))))


def _discretizar(x):
    """Continua → quintiles, para poder cruzarla con una nominal en la V de Cramér."""
    return pd.qcut(x, 5, duplicates='drop').astype(str)


def asociacion(X, a, b, tipos):
    """
    (métrica, valor, n) del par. Si una de las dos tiene "no aplica", se mide
    solo donde ambas aplican: así la asociación no la produce la propia regla
    de la encuesta (por ejemplo, "no aplica" en trabajo ⇔ no trabaja).
    """
    mascara = X[a].notna() & X[b].notna()
    for v in (a, b):
        if v in C.CONDICIONALES_NO_APLICA:
            mascara &= ~X[v].isin([C.NO_APLICA, 'NO_APLICA'])
    xa, xb = X.loc[mascara, a], X.loc[mascara, b]
    if xa.nunique() < 2 or xb.nunique() < 2:
        return 'no calculable (una es constante donde ambas aplican)', np.nan, int(mascara.sum())
    if 'nominal' in (tipos[a], tipos[b]):
        xa = _discretizar(xa) if tipos[a] == 'continua' else xa
        xb = _discretizar(xb) if tipos[b] == 'continua' else xb
        return 'V de Cramér', cramer_v(xa, xb), int(mascara.sum())
    return 'rho de Spearman', float(stats.spearmanr(xa, xb)[0]), int(mascara.sum())


def _prioridad(v, faltantes, tipos, X):
    """Clave de orden: menor = se conserva primero."""
    pref = C.PREFERENCIA.index(v) if v in C.PREFERENCIA else len(C.PREFERENCIA)
    return (pref, v not in C.CONTROL, faltantes.get(v, 0), -X[v].nunique())


def filtro_redundancia(X, tipos, faltantes):
    """
    Todos los pares; los que superan el umbral se resuelven de mayor a menor
    asociación, conservando la variable con mayor prioridad.
    """
    variables = list(X.columns)
    pares = []
    for i, a in enumerate(variables):
        for b in variables[i + 1:]:
            metrica, valor, n = asociacion(X, a, b, tipos)
            pares.append({'variable_1': a, 'variable_2': b, 'metrica': metrica, 'valor': valor, 'n_par': n})
    pares = pd.DataFrame(pares)
    pares['abs'] = pares['valor'].abs()
    altos = pares[pares['abs'] > C.UMBRAL_REDUNDANCIA].sort_values('abs', ascending=False)
    eliminadas, filas = {}, []
    for p in altos.itertuples():
        a, b = p.variable_1, p.variable_2
        if a in eliminadas or b in eliminadas:
            ya = a if a in eliminadas else b
            filas.append({**_fila(p), 'variable_conservada': '-', 'variables_eliminadas': '-',
                          'justificacion': f'Par ya resuelto: {ya} se eliminó por su par con {eliminadas[ya]}.'})
            continue
        queda, sale = sorted((a, b), key=lambda v: _prioridad(v, faltantes, tipos, X))
        eliminadas[sale] = queda
        filas.append({**_fila(p), 'variable_conservada': queda, 'variables_eliminadas': sale,
                      'justificacion': _por_que(queda, sale, faltantes, X)})
    return pares.drop(columns='abs'), pd.DataFrame(filas), eliminadas


def _fila(p):
    return {'variable_1': p.variable_1, 'variable_2': p.variable_2, 'metrica': p.metrica, 'valor': p.valor,
            'n_par': p.n_par}


def _por_que(queda, sale, faltantes, X):
    if queda in C.PREFERENCIA:
        return f'{queda} representa mejor el constructo (lista de preferencia de configuracion.py).'
    if queda in C.CONTROL and sale not in C.CONTROL:
        return f'{queda} es variable de control.'
    if faltantes.get(queda, 0) < faltantes.get(sale, 0):
        return f'{queda} tenía menor % de faltantes antes de la limpieza.'
    return f'{queda} tiene más niveles ({X[queda].nunique()} vs {X[sale].nunique()}): conserva más información.'


# --- Variables solo descriptivas (decisión de la usuaria 2026-11-01) ----------------------

def revisar_excluidas(X_excluidas, X, tipos):
    """Criterios originales de cada excluida frente a las predictoras finales, y su relación con la etapa."""
    etapa = X_excluidas['etapa_menopausica']
    filas = []
    for v in X_excluidas.columns:
        cat, pct, _ = dominancia(X_excluidas[v])
        asociaciones = [(c, *asociacion(X.assign(**{v: X_excluidas[v]}), v, c, tipos)) for c in X.columns]
        mayor = max((a for a in asociaciones if pd.notna(a[2])), key=lambda a: abs(a[2]))
        filas.append({'variable': v, 'etiqueta': V.etiqueta(v), 'tipo': C.EXCLUIDAS_MODELADO[v][0],
                      'n_no_aplica': int(X_excluidas[v].isin([C.NO_APLICA, 'NO_APLICA']).sum()),
                      'categoria_dominante': cat, 'porcentaje_dominancia': pct,
                      'supera_dominancia': pct > C.UMBRAL_ELIMINAR_DOMINANCIA,
                      'mayor_asociacion_con': mayor[0], 'mayor_asociacion_metrica': mayor[1],
                      'mayor_asociacion_valor': mayor[2], 'n_par': mayor[3],
                      'supera_redundancia': abs(mayor[2]) > C.UMBRAL_REDUNDANCIA,
                      'v_con_etapa_todas_las_filas': np.nan if v == 'etapa_menopausica' else
                      cramer_v(etapa, X_excluidas[v].astype(str)),
                      'motivo': C.EXCLUIDAS_MODELADO[v][1]})
    return pd.DataFrame(filas)


def reconstruccion_etapa(X_excluidas, X):
    """
    ¿Cuánto de la etapa menopáusica se puede recuperar desde otras variables?
    Acierto de un bosque aleatorio (validación cruzada estratificada de 5
    particiones). Solo documenta la exclusión; no decide nada ni es un modelo final.
    """
    objetivo = X_excluidas['etapa_menopausica'].replace({'indeterminada (histerectomía)': 'indeterminada'})
    todo = pd.concat([X, X_excluidas.drop(columns='etapa_menopausica')], axis=1)
    gine = ['tipo_sangrado', 'usa_metodo_anticonceptivo']
    finales = list(X.columns)
    cv = StratifiedKFold(5, shuffle=True, random_state=C.SEMILLA)
    modelo = RandomForestClassifier(300, random_state=C.SEMILLA, n_jobs=-1)
    filas = [{'escenario': 'Línea base: siempre la categoría más frecuente', 'n_variables': 0,
              'acierto': objetivo.value_counts(normalize=True).iloc[0]}]
    for nombre, columnas in (('Solo regularidad de la menstruación', ['menstruacion_llega']),
                             ('Solo tipo de sangrado y método anticonceptivo', gine),
                             ('Solo edad', ['edad']),
                             ('Predictoras finales más sangrado y método anticonceptivo', finales + gine),
                             ('Predictoras finales', finales),
                             ('Predictoras finales sin edad', [v for v in finales if v != 'edad'])):
        entrada = pd.get_dummies(todo[columnas], dtype=float).fillna(-1)
        filas.append({'escenario': nombre, 'n_variables': len(columnas),
                      'acierto': cross_val_score(modelo, entrada, objetivo, cv=cv, scoring='accuracy').mean()})
    return pd.DataFrame(filas)


# --- Módulo 3: validación contra la simulación --------------------------------------------

def validar(df):
    """
    Asociación de cada variable con mrs_total (rho de Spearman) y comparación
    con el signo que le dio la simulación. Solo verifica; no decide nada.
    """
    subconjuntos = {None: pd.Series(True, index=df.index), 'trabaja': df['trabaja_actualmente'] == 'True',
                    'cuida': df['cuida_otras_personas'] == 'SI', 'menstrua': menstrua(df).fillna(False),
                    'pareja': df['tiene_pareja'] == 'SI'}
    total = V.numerica(df['mrs_total'])
    filas = []
    for v, signo, sub, texto in C.PATRONES_SIMULACION:
        m = subconjuntos[sub]
        s = df.loc[m, v]
        x = s.map(ORDEN_SANGRADO) if v == 'tipo_sangrado' else s.map(SI_NO) if s.dropna().isin(SI_NO).all() \
            else V.numerica(s)
        ok = s.notna() if v == 'menstruacion_llega' else x.notna()
        if v == 'menstruacion_llega':
            # Nominal: Kruskal-Wallis entre categorías; el "efecto" se informa como épsilon².
            grupos = [total[m][ok][s[ok] == c] for c in s[ok].unique()]
            h, p = stats.kruskal(*grupos)
            efecto, metrica = (h - len(grupos) + 1) / (ok.sum() - len(grupos)), 'épsilon² (Kruskal-Wallis)'
        else:
            efecto, p = stats.spearmanr(x[ok], total[m][ok])
            metrica = 'rho de Spearman con mrs_total'
        filas.append({'variable_o_relacion': v, 'etiqueta': V.etiqueta(v), 'patron_esperado': texto,
                      'signo_esperado': {1: 'positivo', -1: 'negativo', 0: 'sin asociación'}[signo],
                      'subconjunto': {None: 'todas', 'trabaja': 'quienes trabajan', 'cuida': 'quienes cuidan',
                                      'menstrua': 'quienes menstrúan', 'pareja': 'quienes tienen pareja'}[sub],
                      'n': int(ok.sum()), 'metrica': metrica, 'resultado_observado': efecto, 'p': p,
                      'signo_num': signo})
    t = pd.DataFrame(filas)
    t['p_ajustado'] = stats.false_discovery_control(t['p'], method='bh')
    t['coherencia'] = [_coherencia(f) for f in t.itertuples()]
    t['comentario'] = [_comentario(f, c) for f, c in zip(t.itertuples(), t['coherencia'])]
    return t.drop(columns='signo_num')


def _coherencia(f):
    sig = f.p_ajustado < 0.05
    if f.signo_num == 0:
        return 'esperado' if not sig else 'no esperado'
    if np.sign(f.resultado_observado) == f.signo_num:
        return 'esperado' if sig else 'parcial'
    return 'no esperado' if sig else 'parcial'


def _comentario(f, coherencia):
    valor = f'{f.resultado_observado:+.3f}'
    p = '< 0,001' if f.p_ajustado < 0.001 else f'{f.p_ajustado:.3f}'.replace('.', ',')
    if f.signo_num == 0:
        return (f'Sin asociación, como se generó ({valor}, p ajustado {p}).' if coherencia == 'esperado' else
                f'Aparece una asociación que la simulación no puso ({valor}, p ajustado {p}): se reporta como '
                'hallazgo de validación; no se modifican los datos.')
    if coherencia == 'esperado':
        return f'Signo correcto y significativo ({valor}, p ajustado {p}).'
    if coherencia == 'parcial':
        return (f'Signo {"correcto" if np.sign(f.resultado_observado) == f.signo_num else "contrario"} pero no '
                f'significativo ({valor}, p ajustado {p}): el efecto simulado es chico frente al ruido y a la '
                'suciedad agregada. No se modifican los datos.')
    return f'Signo contrario y significativo ({valor}, p ajustado {p}): revisar la simulación.'
