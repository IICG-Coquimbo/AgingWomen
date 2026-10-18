"""Estadística descriptiva, perfil sintomático, cruces con el MRS y atípicos (Fase 33)."""
import numpy as np
import pandas as pd
from scipy import stats

from . import variables as V


def descriptivos_continuos(df, columnas):
    filas = []
    for c in columnas:
        x = V.numerica(df[c]).dropna()
        q1, q3 = x.quantile([.25, .75])
        filas.append({'variable': c, 'n': len(x), 'media': x.mean(), 'de': x.std(),
                      'mediana': x.median(), 'q1': q1, 'q3': q3, 'min': x.min(), 'max': x.max()})
    return pd.DataFrame(filas)


def frecuencias(df, columnas):
    """Tabla larga: variable, valor, n, % (sobre las filas con dato)."""
    filas = []
    for c in columnas:
        conteo = df[c].value_counts(dropna=True)
        total = conteo.sum()
        for valor, n in conteo.sort_index().items():
            filas.append({'variable': c, 'valor': valor, 'n': int(n), 'pct': 100 * n / total})
    return pd.DataFrame(filas)


def perfil_mrs(df):
    """% con cada síntoma en grado moderado o más (≥ 2), ordenado de mayor a menor."""
    mrs = df[df['mrs_completo'] == '1']
    filas = [{'item': i, 'sintoma': nombre,
              'pct_moderado_o_mas': 100 * (V.numerica(mrs[i]) >= 2).mean(),
              'media': V.numerica(mrs[i]).mean()}
             for i, nombre in V.MRS_ITEMS.items()]
    return pd.DataFrame(filas).sort_values('pct_moderado_o_mas', ascending=False)


def severidad_por(df, grupo, orden=None):
    """Tabla % de severidad del MRS por categoría de `grupo` (filas suman 100)."""
    mrs = df[df['mrs_completo'] == '1']
    tabla = pd.crosstab(mrs[grupo], mrs['mrs_severidad'], normalize='index') * 100
    tabla = tabla.reindex(columns=V.ORDEN_SEVERIDAD, fill_value=0)
    if orden:
        tabla = tabla.reindex([o for o in orden if o in tabla.index])
    tabla['n'] = mrs[grupo].value_counts()
    tabla['mrs_medio'] = V.numerica(mrs['mrs_total']).groupby(mrs[grupo]).mean()
    return tabla


def _es_ordenable(s):
    return s.isin(V.BINARIAS).all() or V.numerica(s).notna().all() or s.name == 'nivel_educacion'


def cruce_con_mrs(df, variables, rol, resultado='mrs_total'):
    """
    Relación de cada variable con el MRS:
      - ordinal / continua / binaria → correlación de Spearman (rho);
      - categórica de más de dos valores → Kruskal-Wallis con épsilon² como tamaño de efecto.
    Las preguntas condicionales se codifican como en el modelo (0 si la madre es "No").
    """
    mrs = df[df['mrs_completo'] == '1']
    y_total = V.numerica(mrs[resultado])
    filas = []
    for v in variables:
        s = mrs[v].where(mrs[V.CERO_SI_NO[v]] != 'NO', '0') if v in V.CERO_SI_NO else mrs[v]
        ok = s.notna()
        if ok.sum() < 20:
            continue
        s, y = s[ok], y_total[ok]
        if _es_ordenable(s):
            x = V.codificar(pd.DataFrame({v: s}), [v])[v]
            rho, p = stats.spearmanr(x, y)
            filas.append({'variable': v, 'rol': rol, 'n': len(s), 'prueba': 'Spearman',
                          'efecto': rho, 'medida': 'rho', 'p': p})
        else:
            grupos = [y[s == g] for g in s.unique() if (s == g).sum() >= 5]
            if len(grupos) < 2:
                continue
            h, p = stats.kruskal(*grupos)
            n = sum(len(g) for g in grupos)
            eps2 = (h - len(grupos) + 1) / (n - len(grupos))
            filas.append({'variable': v, 'rol': rol, 'n': n, 'prueba': 'Kruskal-Wallis',
                          'efecto': eps2, 'medida': 'ε²', 'p': p})
    return pd.DataFrame(filas)


def corregir_fdr(tabla):
    """Benjamini-Hochberg sobre todas las pruebas de la tabla."""
    tabla = tabla.copy()
    tabla['p_ajustado'] = stats.false_discovery_control(tabla['p'], method='bh')
    return tabla.sort_values('p_ajustado').reset_index(drop=True)


def atipicos(df, columnas):
    """Regla de Tukey (1,5 × RIC). Se informan; no se eliminan."""
    filas = []
    for c in columnas:
        x = V.numerica(df[c]).dropna()
        q1, q3 = x.quantile([.25, .75])
        ric = q3 - q1
        bajo, alto = q1 - 1.5 * ric, q3 + 1.5 * ric
        fuera = x[(x < bajo) | (x > alto)]
        filas.append({'variable': c, 'n': len(x), 'limite_inferior': bajo, 'limite_superior': alto,
                      'atipicos': len(fuera), 'pct': 100 * len(fuera) / len(x) if len(x) else 0,
                      'valores': ', '.join(f'{v:g}' for v in sorted(fuera.unique())[:8])})
    return pd.DataFrame(filas)


def redundantes(X, importancia, umbral=0.8):
    """
    Pares de predictores con |rho de Spearman| ≥ umbral. De cada par se descarta
    el de menor importancia. Devuelve (pares, descartadas).
    """
    rho = X.corr(method='spearman').abs()
    pares, descartadas = [], set()
    cols = list(X.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            if rho.at[a, b] >= umbral:
                menos = a if importancia.get(a, 0) < importancia.get(b, 0) else b
                pares.append({'a': a, 'b': b, 'rho': rho.at[a, b], 'descartada': menos})
                descartadas.add(menos)
    return pd.DataFrame(pares), descartadas


def severidad_codigo(df):
    """Severidad del MRS como ordinal 0-3 (0 = sin síntomas o muy leves … 3 = severa)."""
    return df['mrs_severidad'].map({s: str(i) for i, s in enumerate(V.ORDEN_SEVERIDAD)})


def matriz_spearman(df, variables):
    """
    Matriz de Spearman (pares completos) entre `variables` ordinales/continuas/
    binarias y la severidad, sobre quienes tienen MRS completo. Las preguntas
    condicionales se codifican como en el modelo (0 si la madre es "No").
    """
    mrs = df[df['mrs_completo'] == '1']
    X = V.codificar(mrs, variables)
    X.insert(0, 'severidad', V.numerica(severidad_codigo(mrs)))
    return X.corr(method='spearman')
