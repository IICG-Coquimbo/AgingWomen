"""
Fase 34E (OB2): análisis multivariado exploratorio (plan aprobado 2026-10-30).

1. Matriz de asociación mixta de las 38 predictoras de la Fase 35A + severidad:
   rho de Spearman (numérica/ordinal/binaria × numérica/ordinal/binaria),
   V de Cramér con corrección de sesgo (nominal × nominal) y razón de
   correlación eta sobre rangos (nominal × numérica/ordinal). Nunca Pearson:
   los códigos de una categórica no son cantidades.
2. Grupos de variables relacionadas: agrupamiento jerárquico (enlace
   promedio) con distancia 1 − |asociación|.
3. Tríadas: severidad según dos variables a la vez (tabla estratificada,
   regresión logística ordinal con interacción y Spearman parcial).
"""
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform

from . import graficos as G
from . import variables as V

ANALITICO = V.RAIZ / 'datos' / 'analitico'
RESULTADOS_35 = V.RAIZ / 'analisis' / 'resultados' / 'usuaria'

# Preguntas que no aplican a una parte (0 / 'NO_APLICA' en la Fase 35A): quedan
# fuera del par, porque "no aplica" no es un nivel de la escala.
NO_APLICA_ORDINAL = ['lugar_trabajo_comprensivo', 'estres_entorno_laboral', 'tipo_sangrado']
NO_APLICA_NOMINAL = 'NO_APLICA'
# Respuestas laborales imputadas por mediana en la 35A: se usan las originales.
IMPUTADAS_TRABAJO = ['lugar_trabajo_comprensivo', 'estres_entorno_laboral']
SEVERIDAD = 'severidad'
CORTE_GRUPO = 0.30            # asociación promedio mínima para formar un grupo (distancia 0,70)
MINIMO_CELDA = 10             # combinaciones con menos participantes se marcan como poco confiables
CORTAS = {SEVERIDAD: 'Severidad MRS (4 clases)'}


def etiqueta(v):
    return CORTAS.get(v) or V.etiqueta(v)


# --- Datos ----------------------------------------------------------------------

def cargar():
    """
    (datos para asociación, tipos {variable: 'nominal' | 'ordenada'}, predictoras).
    Parte del conjunto de la Fase 35A y deshace lo que no es una observación:
    IMC imputado por la media, "no aplica" y las 22 respuestas laborales imputadas.
    """
    f = pd.read_csv(ANALITICO / 'dataset_fase35.csv', dtype=str, encoding='utf-8-sig')
    crudo = pd.read_csv(ANALITICO / 'conjunto_eda_usuaria.csv', dtype=str, encoding='utf-8-sig',
                        usecols=['participante_id', *IMPUTADAS_TRABAJO]).set_index('participante_id')
    dicc = pd.read_csv(RESULTADOS_35 / 'diccionario_datos_fase35.csv', encoding='utf-8-sig')
    pred = dicc[dicc['rol'] == 'predictora']
    tipos = {v: 'nominal' if t == 'nominal' else 'ordenada' for v, t in zip(pred['variable'], pred['tipo_final'])}
    datos = pd.DataFrame(index=f.index)
    datos['participante_id'] = f['participante_id']
    datos[SEVERIDAD] = f['severidad_mrs_4'].map({s: i for i, s in enumerate(V.ORDEN_SEVERIDAD)})
    datos['mrs_total'] = pd.to_numeric(f['mrs_total'])
    datos['mrs_severidad'] = f['severidad_mrs_4']
    for v, tipo in tipos.items():
        if tipo == 'nominal':
            datos[v] = f[v].where(f[v] != NO_APLICA_NOMINAL)
        else:
            datos[v] = pd.to_numeric(f[v])
    for v in NO_APLICA_ORDINAL:
        datos[v] = datos[v].where(datos[v] != 0)
    originales = crudo.reindex(f['participante_id'])
    for v in IMPUTADAS_TRABAJO:
        datos.loc[originales[v].isna().to_numpy(), v] = np.nan
    datos.loc[f['imc_fue_imputado'] == '1', 'imc'] = np.nan
    return datos, {SEVERIDAD: 'ordenada', **tipos}, list(tipos)


# --- Medidas de asociación --------------------------------------------------------

def _pares(x, y):
    m = x.notna() & y.notna()
    return x[m], y[m]


def spearman(x, y):
    x, y = _pares(x, y)
    if x.nunique() < 2 or y.nunique() < 2:
        return np.nan, np.nan, len(x)
    r, p = stats.spearmanr(x, y)
    return r, p, len(x)


def cramer_v(a, b):
    """V de Cramér con corrección de sesgo de Bergsma (2013)."""
    a, b = _pares(a, b)
    t = pd.crosstab(a, b)
    if min(t.shape) < 2:
        return np.nan, np.nan, len(a)
    chi2, p, _, _ = stats.chi2_contingency(t, correction=False)
    n = t.to_numpy().sum()
    r, k = t.shape
    phi2 = max(0.0, chi2 / n - (k - 1) * (r - 1) / (n - 1))
    rc, kc = r - (r - 1) ** 2 / (n - 1), k - (k - 1) ** 2 / (n - 1)
    d = min(kc - 1, rc - 1)
    return (np.sqrt(phi2 / d) if d > 0 else np.nan), p, n


def eta_rangos(grupo, x):
    """Razón de correlación eta sobre rangos; su prueba es Kruskal-Wallis."""
    grupo, x = _pares(grupo, x)
    if grupo.nunique() < 2 or x.nunique() < 2:
        return np.nan, np.nan, len(x)
    rangos = x.rank()
    media = rangos.mean()
    entre = sum(len(r) * (r.mean() - media) ** 2 for _, r in rangos.groupby(grupo))
    total = ((rangos - media) ** 2).sum()
    p = stats.kruskal(*[r for _, r in rangos.groupby(grupo)]).pvalue
    return np.sqrt(entre / total), p, len(x)


MEDIDAS = {('ordenada', 'ordenada'): ('rho de Spearman', spearman),
           ('nominal', 'nominal'): ('V de Cramér corregida', cramer_v)}


def asociar(datos, a, b, tipos):
    ta, tb = tipos[a], tipos[b]
    if ta == tb:
        nombre, funcion = MEDIDAS[(ta, tb)]
        return (nombre, *funcion(datos[a], datos[b]))
    nominal, otra = (a, b) if ta == 'nominal' else (b, a)
    return ('eta (rangos)', *eta_rangos(datos[nominal], datos[otra]))


def matriz_mixta(datos, variables, tipos):
    """(tabla larga de pares, matriz cuadrada de valores con signo solo en Spearman)."""
    filas = []
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for i, a in enumerate(variables):
            for b in variables[i + 1:]:
                medida, valor, p, n = asociar(datos, a, b, tipos)
                filas.append({'variable_1': a, 'variable_2': b, 'medida': medida, 'valor': valor,
                              'abs_valor': abs(valor), 'p': p, 'n_par': int(n)})
    largo = pd.DataFrame(filas)
    from statsmodels.stats.multitest import multipletests
    validos = largo['p'].notna()
    largo['p_ajustado'] = np.nan
    largo.loc[validos, 'p_ajustado'] = multipletests(largo.loc[validos, 'p'], method='fdr_bh')[1]
    m = pd.DataFrame(np.eye(len(variables)), index=variables, columns=variables)
    for t in largo.itertuples():
        m.at[t.variable_1, t.variable_2] = m.at[t.variable_2, t.variable_1] = t.valor
    largo['etiqueta_1'] = largo['variable_1'].map(etiqueta)
    largo['etiqueta_2'] = largo['variable_2'].map(etiqueta)
    return largo, m


# --- Grupos de variables ----------------------------------------------------------

def agrupar(matriz, corte=CORTE_GRUPO):
    """
    Agrupamiento jerárquico de variables: distancia = 1 − |asociación| (un par
    sin valor cuenta como sin relación, distancia 1), enlace promedio. Corte a
    distancia 1 − corte. Devuelve (enlace, grupo por variable, orden de hojas).
    """
    d = 1 - matriz.abs().fillna(0).to_numpy()
    np.fill_diagonal(d, 0)
    enlace = hierarchy.linkage(squareform(d, checks=False), method='average')
    grupo = pd.Series(hierarchy.fcluster(enlace, t=1 - corte, criterion='distance'), index=matriz.index)
    orden = hierarchy.leaves_list(enlace)
    return enlace, grupo, [matriz.index[i] for i in orden]


def tabla_grupos(matriz, grupo, orden, asociacion_severidad):
    """Grupos de 2 o más variables, en el orden del dendrograma."""
    filas, numero = [], 0
    vistos = []
    for v in orden:
        if grupo[v] not in vistos:
            vistos.append(grupo[v])
    for g in vistos:
        miembros = [v for v in orden if grupo[v] == g]
        if len(miembros) < 2:
            continue
        numero += 1
        sub = matriz.loc[miembros, miembros].abs().to_numpy()
        pares = sub[np.triu_indices(len(miembros), 1)]
        pares = pares[~np.isnan(pares)]
        filas.append({'grupo': numero, 'n_variables': len(miembros), 'variables': ', '.join(miembros),
                      'etiquetas': ', '.join(etiqueta(v) for v in miembros),
                      'asociacion_promedio': pares.mean(), 'asociacion_minima': pares.min(),
                      'asociacion_maxima': pares.max(),
                      'max_asociacion_con_severidad': max(asociacion_severidad.get(v, 0) for v in miembros)})
    return pd.DataFrame(filas)


# --- Tríadas ----------------------------------------------------------------------

def _tramos(cortes, nombres):
    return lambda x: pd.cut(x, cortes, labels=nombres, right=False).astype(object)


def _mapa(m):
    return lambda x: x.map(m)


IMC_TRAMOS = _tramos([0, 25, 30, np.inf], ['Normal (< 25)', 'Sobrepeso (25-29,9)', 'Obesidad (≥ 30)'])
TRIADAS = [
    {'clave': 'imc_ejercicio', 'titulo': 'IMC y días de ejercicio', 'frase': 'el IMC y los días de ejercicio',
     'a': ('imc', 'IMC', IMC_TRAMOS),
     'b': ('dias_ejercicio_semana', 'Ejercicio',
           _mapa({1: '0 días', 2: '1-2 días', 3: '3 o más días', 4: '3 o más días', 5: '3 o más días'})),
     'quienes': 'participantes que informaron peso y talla'},
    {'clave': 'doble_carga_estres', 'titulo': 'Doble carga y estrés laboral', 'frase': 'la doble carga y el estrés laboral',
     'a': ('doble_carga', 'Doble carga', _mapa({0: 'Sin doble carga', 1: 'Con doble carga'})),
     'b': ('estres_entorno_laboral', 'Estrés laboral',
           _mapa({1: 'Bajo (nada o leve)', 2: 'Bajo (nada o leve)', 3: 'Moderado',
                  4: 'Alto (alto o extremo)', 5: 'Alto (alto o extremo)'})),
     'quienes': 'trabajadoras con la sección Trabajo respondida', 'filtro': ('trabaja_actualmente', 1)},
    {'clave': 'diabetes_imc', 'titulo': 'Diabetes e IMC', 'frase': 'la diabetes y el IMC',
     'a': ('usa_medicamentos_diabetes', 'Diabetes', _mapa({0: 'Sin medicamentos', 1: 'Con medicamentos'})),
     'b': ('imc', 'IMC', IMC_TRAMOS),
     'quienes': 'participantes que informaron peso y talla'},
    {'clave': 'tabaco_agua', 'titulo': 'Tabaco y consumo de agua', 'frase': 'el tabaco y el consumo de agua',
     'a': ('tabaco_frecuencia', 'Tabaco', _mapa({1: 'Nunca', 2: 'Fuma', 3: 'Fuma', 4: 'Fuma', 5: 'Fuma'})),
     'b': ('vasos_agua_dia', 'Agua',
           _mapa({1: '≤ 2 vasos', 2: '≤ 2 vasos', 3: '3-4 vasos', 4: '5 o más vasos', 5: '5 o más vasos'})),
     'quienes': 'todas las participantes'},
]


def _orden(categorias):
    return list(dict.fromkeys(c for c in categorias if pd.notna(c)))


def preparar_triada(datos, t):
    """Participantes con A, B y severidad; columnas A y B ya agrupadas en categorías ordenadas."""
    d = datos
    if 'filtro' in t:
        col, val = t['filtro']
        d = d[d[col] == val]
    (va, _, fa), (vb, _, fb) = t['a'], t['b']
    d = d[d[va].notna() & d[vb].notna() & d[SEVERIDAD].notna()].copy()
    d['A'], d['B'] = fa(d[va]), fb(d[vb])
    orden_a = [c for c in _orden(fa(pd.Series(sorted(d[va].unique())))) if c in set(d['A'])]
    orden_b = [c for c in _orden(fb(pd.Series(sorted(d[vb].unique())))) if c in set(d['B'])]
    return d, orden_a, orden_b


def estratificar(d, orden_a, orden_b):
    """Una fila por combinación A × B: n, % de cada clase, % severa y mediana MRS."""
    filas = []
    for a in orden_a:
        for b in orden_b:
            c = d[(d['A'] == a) & (d['B'] == b)]
            pct = c['mrs_severidad'].value_counts(normalize=True).reindex(V.ORDEN_SEVERIDAD, fill_value=0) * 100
            filas.append({'A': a, 'B': b, 'n': len(c), **pct.to_dict(), 'pct_severa': pct['Severa'],
                          'mediana_mrs': c['mrs_total'].median() if len(c) else np.nan,
                          'poco_confiable': len(c) < MINIMO_CELDA})
    return pd.DataFrame(filas)


def _diseno(d, orden_a, orden_b, interaccion):
    """Variables indicadoras (categoría de referencia = la primera) y, si se pide, sus productos."""
    xa = pd.get_dummies(pd.Categorical(d['A'], orden_a), prefix='A', drop_first=True, dtype=float)
    xb = pd.get_dummies(pd.Categorical(d['B'], orden_b), prefix='B', drop_first=True, dtype=float)
    X = pd.concat([xa, xb], axis=1)
    if interaccion:
        for ca in xa:
            for cb in xb:
                X[f'{ca}×{cb}'] = xa[ca] * xb[cb]
    X.index = d.index
    return X


def _ordinal(y, X):
    from statsmodels.miscmodels.ordinal_model import OrderedModel
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return OrderedModel(y, X, distr='logit').fit(method='bfgs', maxiter=5000, disp=False)


def _nombre_termino(t):
    return t.replace('A_', '').replace('B_', '')


def modelar(d, orden_a, orden_b):
    """
    Regresión logística ordinal (odds proporcionales) de la severidad 0-3:
    modelo aditivo (A + B) para los OR y modelo con interacción para la prueba
    de razón de verosimilitud. Además, logísticas binarias por corte para
    revisar el supuesto de odds proporcionales.
    """
    import statsmodels.api as sm
    y = d[SEVERIDAD].astype(int)
    X0, X1 = _diseno(d, orden_a, orden_b, False), _diseno(d, orden_a, orden_b, True)
    m0, m1 = _ordinal(y, X0), _ordinal(y, X1)
    lr = max(0.0, 2 * (m1.llf - m0.llf))
    gl = X1.shape[1] - X0.shape[1]
    efectos = []
    for c in X0.columns:
        b, ee = m0.params[c], m0.bse[c]
        fila = {'termino': _nombre_termino(c), 'variable': 'A' if c.startswith('A_') else 'B',
                'OR': np.exp(b), 'IC95_inf': np.exp(b - 1.96 * ee), 'IC95_sup': np.exp(b + 1.96 * ee),
                'p': m0.pvalues[c]}
        for corte, nombre in ((1, 'OR_corte_leve_o_mas'), (2, 'OR_corte_moderada_o_mas'), (3, 'OR_corte_severa')):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    lg = sm.Logit((y >= corte).astype(int), sm.add_constant(X0)).fit(disp=False, maxiter=200)
                fila[nombre] = np.exp(lg.params[c])
            except Exception:       # separación perfecta en un corte con pocas participantes
                fila[nombre] = np.nan
        efectos.append(fila)
    efectos = pd.DataFrame(efectos)
    estable = bool(np.isfinite(m1.bse).all() and (m1.bse < 10).all())
    return efectos, {'n': len(d), 'lr': lr, 'gl': gl, 'p_interaccion': stats.chi2.sf(lr, gl),
                     'interaccion_estable': estable, 'convergio': bool(m0.mle_retvals.get('converged', True))}


def spearman_parcial(d, x, z, y=SEVERIDAD):
    """rho de Spearman entre x y la severidad descontando z (correlación parcial sobre rangos)."""
    r = d[[x, y, z]].rank()
    rxy, rxz, ryz = r[x].corr(r[y]), r[x].corr(r[z]), r[y].corr(r[z])
    parcial = (rxy - rxz * ryz) / np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    n = len(r)
    t = parcial * np.sqrt((n - 3) / (1 - parcial ** 2))
    return rxy, parcial, 2 * stats.t.sf(abs(t), n - 3)


# --- Figuras ----------------------------------------------------------------------

def _mapa_secuencial():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list('secuencial', ['#ffffff', *G.RAMPA_SEVERIDAD])


def figura_matriz(matriz, ruta, titulo):
    """Mapa de calor de |asociación| (0-1); se anotan los valores ≥ 0,30 (con signo si es Spearman)."""
    import matplotlib.pyplot as plt
    n = len(matriz)
    fig, ax = plt.subplots(figsize=(13, 11.5))
    im = ax.imshow(matriz.abs().to_numpy(dtype=float), cmap=_mapa_secuencial(), vmin=0, vmax=1)
    nombres = [etiqueta(v) for v in matriz.columns]
    ax.set_xticks(range(n), nombres, rotation=90, fontsize=7)
    ax.set_yticks(range(n), nombres, fontsize=7)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    for i in range(n):
        for j in range(n):
            v = matriz.iat[i, j]
            if i != j and pd.notna(v) and abs(v) >= CORTE_GRUPO:
                ax.text(j, i, f'{v:.2f}'.replace('0.', '.'), ha='center', va='center', fontsize=5,
                        color='white' if abs(v) > 0.55 else G.TINTA)
    barra = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    barra.set_label('|asociación| (0 = ninguna, 1 = total)', fontsize=8)
    barra.ax.tick_params(labelsize=7)
    ax.set_title(titulo, loc='left', fontsize=12, pad=22)
    ax.text(0, 1.008, 'Spearman, V de Cramér corregida o eta según el tipo de par · se anotan los valores ≥ 0,30 '
            '(con signo en Spearman) · celdas vacías: par sin participantes en común o constante',
            transform=ax.transAxes, fontsize=7.5, color=G.TENUE, va='bottom')
    G._guardar(fig, ruta)


def figura_grupos(matriz, enlace, orden, grupo, ruta, corte=CORTE_GRUPO):
    """Dendrograma (izquierda) alineado con la matriz reordenada (derecha); recuadros = grupos."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    n = len(orden)
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(14, 11.5), gridspec_kw={'width_ratios': [1, 3.2], 'wspace': 0.02})
    with plt.rc_context({'lines.linewidth': 0.9}):
        hierarchy.dendrogram(enlace, orientation='left', ax=ax0, no_labels=True, color_threshold=1 - corte,
                             above_threshold_color=G.EJE)
    ax0.set_ylim(10 * n, 0)
    ax0.axvline(1 - corte, color=G.ROJO, linewidth=1, linestyle=(0, (3, 3)))
    ax0.text(1 - corte, -4, f'corte: asociación promedio ≥ {corte:.2f}'.replace('.', ','), color=G.ROJO,
             fontsize=7, ha='center', va='top')
    ax0.set_xlabel('distancia = 1 − |asociación|', fontsize=8)
    for lado in ('left', 'top', 'right'):
        ax0.spines[lado].set_visible(False)
    ax0.set_yticks([])
    ax0.tick_params(axis='x', labelsize=7)
    m = matriz.loc[orden, orden]
    ax1.imshow(m.abs().to_numpy(dtype=float), cmap=_mapa_secuencial(), vmin=0, vmax=1, aspect='auto')
    ax1.set_xticks(range(n), [etiqueta(v) for v in orden], rotation=90, fontsize=7)
    ax1.yaxis.tick_right()
    ax1.set_yticks(range(n), [etiqueta(v) for v in orden], fontsize=7)
    ax1.tick_params(length=0)
    for s in ax1.spines.values():
        s.set_visible(False)
    inicio = 0
    while inicio < n:
        fin = inicio
        while fin + 1 < n and grupo[orden[fin + 1]] == grupo[orden[inicio]]:
            fin += 1
        if fin > inicio:
            ax1.add_patch(Rectangle((inicio - 0.5, inicio - 0.5), fin - inicio + 1, fin - inicio + 1,
                                    fill=False, edgecolor=G.ROJO, linewidth=1.3))
        inicio = fin + 1
    fig.suptitle('Grupos de variables relacionadas: dendrograma y matriz reordenada', x=0.01, ha='left',
                 fontweight='bold', fontsize=12)
    fig.text(0.01, 0.955, 'Recuadros rojos: grupos de 2 o más variables al cortar el árbol · color: |asociación|',
             fontsize=8, color=G.TENUE)
    fig.subplots_adjust(left=0.02, right=0.8, top=0.93, bottom=0.21)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def figura_triada(t, tabla, orden_a, orden_b, ruta):
    """Izquierda: % de severas en cada combinación (mapa de calor). Derecha: las 4 clases (barras 100 %)."""
    import matplotlib.pyplot as plt
    nombre_a, nombre_b = t['a'][1], t['b'][1]
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 0.42 * len(tabla) + 2.4),
                                   gridspec_kw={'width_ratios': [1, 1.5]})
    pct = tabla.pivot(index='A', columns='B', values='pct_severa').reindex(index=orden_a, columns=orden_b)
    n = tabla.pivot(index='A', columns='B', values='n').reindex(index=orden_a, columns=orden_b)
    ax0.imshow(pct.to_numpy(dtype=float), cmap=_mapa_secuencial(), vmin=0, vmax=100, aspect='auto')
    for i in range(len(orden_a)):
        for j in range(len(orden_b)):
            k = int(n.iat[i, j])
            p = pct.iat[i, j]
            texto = f'{p:.0f} %\nn = {k}' if k else 'n = 0'
            poco = k < MINIMO_CELDA
            ax0.text(j, i, texto + (' *' if poco and k else ''), ha='center', va='center', fontsize=8,
                     color='white' if p > 55 else G.TINTA,
                     style='italic' if poco else 'normal')
    ax0.set_xticks(range(len(orden_b)), orden_b, fontsize=7.5)
    ax0.set_yticks(range(len(orden_a)), orden_a, fontsize=7.5)
    ax0.set_xlabel(nombre_b, fontsize=8)
    ax0.set_ylabel(nombre_a, fontsize=8)
    ax0.tick_params(length=0)
    for s in ax0.spines.values():
        s.set_visible(False)
    ax0.set_title('% en la clase severa', fontsize=9.5, loc='left')
    filas = tabla.iloc[::-1]
    etiquetas = [f'{a} · {b} (n={k})' for a, b, k in zip(filas['A'], filas['B'], filas['n'])]
    izquierda = np.zeros(len(filas))
    for sev, color in zip(V.ORDEN_SEVERIDAD, G.RAMPA_SEVERIDAD):
        valores = filas[sev].to_numpy(dtype=float)
        ax1.barh(etiquetas, valores, left=izquierda, color=color, edgecolor=G.SUPERFICIE, linewidth=1.2,
                 height=0.7, label=sev)
        for k, (x0, v) in enumerate(zip(izquierda, valores)):
            if v >= 12:
                ax1.text(x0 + v / 2, k, f'{v:.0f}', ha='center', va='center', fontsize=6.5,
                         color=G.TINTA if color == G.RAMPA_SEVERIDAD[0] else 'white')
        izquierda += valores
    alto_ejes = 0.42 * len(filas) + 0.6
    for etiqueta_y, k in zip(ax1.get_yticklabels(), filas['n']):
        if k < MINIMO_CELDA:
            etiqueta_y.set_color(G.TENUE)
    ax1.set_xlim(0, 100)
    ax1.tick_params(axis='y', labelsize=7)
    ax1.tick_params(axis='x', labelsize=7)
    ax1.set_xlabel('% de participantes', fontsize=8)
    ax1.set_title('Las 4 clases de severidad en cada combinación', fontsize=9.5, loc='left')
    ax1.legend(ncol=4, loc='upper left', bbox_to_anchor=(0, -0.6 / alto_ejes), frameon=False, fontsize=7.5)
    G._grilla_x(ax1)
    alto = fig.get_size_inches()[1]
    fig.suptitle(f'Severidad según {t["frase"]} a la vez', x=0.01, y=1 - 0.12 / alto, ha='left', va='top',
                 fontweight='bold', fontsize=11)
    fig.text(0.01, 1 - 0.42 / alto,
             f'n = {int(tabla["n"].sum())} ({t["quienes"]}) · * y gris: menos de {MINIMO_CELDA} participantes',
             fontsize=7.5, color=G.TENUE, va='top')
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.6 / alto))
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
