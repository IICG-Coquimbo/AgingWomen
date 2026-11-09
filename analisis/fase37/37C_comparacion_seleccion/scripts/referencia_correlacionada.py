"""
Fase 37C: referencia nula correlacionada. Cópula gaussiana con marginales empíricas exactas (alternativa A del protocolo).

Hipótesis: las variables conservan sus marginales y sus asociaciones monótonas por pares, y provienen de una sola nube latente, unimodal y sin grupos.
Módulo aislado: no lee archivos y no conoce el MRS. Recibe la tabla general de la Fase 36 y las definiciones de sus variables.
Conserva exactamente: conteos de cada variable (incluida la ausencia del IMC) y lógica madre-hija. Conserva de forma aproximada: Spearman por pares.
No conserva: relaciones no monótonas, dependencias de orden superior ni combinaciones lógicas entre variables distintas.
"""
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from sklearn.linear_model import LogisticRegression

N_SIM = 40000
ITERACIONES = 25


def _clave_nivel(d):
    """Función de orden de los niveles: código del instrumento y, a igual código, el nivel."""
    if d['tipo'] == 'cuantitativa':
        return float
    niv = d['niveles']
    return lambda x: (float(niv[x]['codigo']), float(x)) if niv[x]['codigo'] is not None else (0.0, 0.0)


def _orden_binaria(valores):
    return sorted(set(valores))


class Copula:
    """Parámetros calibrados una sola vez. `muestrear(rng)` devuelve una tabla con el mismo formato que la de entrada."""

    def __init__(self, tabla, definiciones, madres, semilla=(42, 37), contraccion=0.0):
        self.indice, self.columnas = tabla.index, list(tabla.columns)
        self.madres = dict(madres)
        self.defs = {d['variable']: d for d in definiciones}
        self.nominal = [v for v, d in self.defs.items() if d['tipo'] == 'nominal']
        self.latentes = [v for v, d in self.defs.items() if d['tipo'] != 'nominal' and v != 'imc']
        self.tiene_imc = 'imc' in self.defs
        self.nombres = list(self.latentes) + (['imc', '__imc_ausente'] if self.tiene_imc else [])
        self.valores = {}     # variable -> valores observados ordenados (multiconjunto)
        self.numericos = {}   # variable -> serie numérica con la que se mide Spearman
        for v in self.latentes:
            d = self.defs[v]
            s = tabla[v].astype(str).where(tabla[v].astype(str) != '', d['madre']['estructural'] if d.get('madre') else '')
            if (s == '').any():
                raise ValueError(f'{v}: celdas vacías no estructurales')
            if d['tipo'] == 'cuantitativa':
                orden = sorted(s, key=float)
                num = s.astype(float)
            elif d['tipo'] == 'binaria':
                niveles = sorted(set(s))
                cod = {n: float(d['niveles'][n]['codigo']) for n in niveles}
                orden = sorted(s, key=lambda x: cod[x])
                num = s.map(cod)
            else:
                clave = _clave_nivel(d)
                orden = sorted(s, key=clave)
                num = s.map(lambda x: clave(x)[0])
            self.valores[v] = np.array(orden, dtype=object)
            self.numericos[v] = num.astype(float).to_numpy()
        if self.tiene_imc:
            imc = tabla['imc'].astype(str)
            aus = (imc == '').to_numpy()
            self.imc_ausente = aus
            self.valores['imc'] = np.array(sorted(imc[~aus], key=float), dtype=object)
            self.numericos['imc'] = np.where(aus, np.nan, pd.to_numeric(imc, errors='coerce'))
            self.numericos['__imc_ausente'] = aus.astype(float)
        self.objetivo = self._spearman_observado()
        self.R_calibrada, self.historial = self._calibrar(semilla)
        self.contraccion = contraccion
        self.R = (1 - contraccion) * self.R_calibrada + contraccion * np.eye(len(self.nombres))
        self.nominal_modelo = {}
        for v in self.nominal:
            self.nominal_modelo[v] = self._ajustar_nominal(tabla, v)

    # ---- objetivo
    def _spearman_observado(self):
        p = len(self.nombres)
        S = np.eye(p)
        for i in range(p):
            for j in range(i + 1, p):
                a, b = self.numericos[self.nombres[i]], self.numericos[self.nombres[j]]
                if {self.nombres[i], self.nombres[j]} == {'imc', '__imc_ausente'}:
                    r = 0.0
                else:
                    m = ~(np.isnan(a) | np.isnan(b))
                    r = spearmanr(a[m], b[m]).statistic
                S[i, j] = S[j, i] = 0.0 if np.isnan(r) else r
        return S

    # ---- calibración
    @staticmethod
    def _correlacion_valida(R):
        v, w = np.linalg.eigh((R + R.T) / 2)
        A = (w * np.clip(v, 1e-4, None)) @ w.T
        d = np.sqrt(np.diag(A))
        return A / np.outer(d, d)

    def _discretizar_sim(self, L):
        """Lleva cada columna latente a los valores numéricos observados, con las mismas proporciones."""
        S = np.empty_like(L)
        for j, v in enumerate(self.nombres):
            base = self.numericos[v]
            base = np.sort(base[~np.isnan(base)])
            pos = (rankdata(L[:, j], method='ordinal') - 0.5) / len(L)
            S[:, j] = base[np.minimum((pos * len(base)).astype(int), len(base) - 1)]
        return S

    def _spearman_sim(self, S):
        i = self.nombres.index('imc') if self.tiene_imc else None
        ranks = np.apply_along_axis(rankdata, 0, S)
        C = np.corrcoef(ranks, rowvar=False)
        if i is not None:
            C[i, self.nombres.index('__imc_ausente')] = C[self.nombres.index('__imc_ausente'), i] = 0.0
        return np.nan_to_num(C)

    def _calibrar(self, semilla):
        rng = np.random.default_rng(list(semilla))
        R = self._correlacion_valida(self.objetivo)
        Z0 = rng.standard_normal((N_SIM, len(self.nombres)))
        hist = []
        for _ in range(ITERACIONES):
            L = Z0 @ np.linalg.cholesky(R).T
            S = self._spearman_sim(self._discretizar_sim(L))
            error = self.objetivo - S
            hist.append(float(np.abs(error).max()))
            R = self._correlacion_valida(R + error)
        return R, hist

    # ---- nominal
    def _x_nominal(self, numericos):
        """Variables explicativas estandarizadas, con las medias y DE de los datos de calibración."""
        cols = [v for v in self.nombres if v != 'imc']
        X = np.column_stack([numericos[c] for c in cols])
        if not hasattr(self, '_escala'):
            self._escala = (X.mean(axis=0), X.std(axis=0))
        media, de = self._escala
        return (X - media) / np.where(de > 0, de, 1)

    def _ajustar_nominal(self, tabla, v):
        y = tabla[v].astype(str).to_numpy()
        X = self._x_nominal(self.numericos)
        m = LogisticRegression(C=0.1, max_iter=2000).fit(X, y)
        conteos = pd.Series(y).value_counts()
        return {'modelo': m, 'conteos': conteos}

    def _muestrear_nominal(self, numericos, v, rng):
        info = self.nominal_modelo[v]
        P = info['modelo'].predict_proba(self._x_nominal(numericos))
        clases = list(info['modelo'].classes_)
        salida = np.empty(len(P), dtype=object)
        libre = np.ones(len(P), bool)
        for c in sorted(clases, key=lambda x: info['conteos'][x]):   # de la más rara a la más común
            n = int(info['conteos'][c])
            clave = np.log(np.clip(P[:, clases.index(c)], 1e-12, None)) + rng.gumbel(size=len(P))
            clave[~libre] = -np.inf
            elegidas = np.argsort(-clave)[:n]
            salida[elegidas] = c
            libre[elegidas] = False
        return salida

    # ---- réplica
    def muestrear(self, rng):
        n = len(self.indice)
        L = rng.standard_normal((n, len(self.nombres))) @ np.linalg.cholesky(self.R).T
        t = pd.DataFrame(index=self.indice)
        numericos = {}
        for j, v in enumerate(self.nombres):
            if v in ('imc', '__imc_ausente'):
                continue
            o = np.argsort(np.argsort(L[:, j]))
            t[v] = self.valores[v][o]
            numericos[v] = self.numericos[v].copy()
            numericos[v] = np.sort(self.numericos[v])[o]
        if self.tiene_imc:
            ja, ji = self.nombres.index('__imc_ausente'), self.nombres.index('imc')
            m = int(self.imc_ausente.sum())
            aus = np.zeros(n, bool)
            aus[np.argsort(-L[:, ja])[:m]] = True
            imc = np.full(n, '', dtype=object)
            orden_obs = np.argsort(np.argsort(L[~aus, ji]))
            imc[~aus] = self.valores['imc'][orden_obs]
            t['imc'] = imc
            numericos['__imc_ausente'] = aus.astype(float)
        for v in self.nominal:
            t[v] = self._muestrear_nominal(numericos, v, rng)
        for hija, madre in self.madres.items():
            estructural = self.defs[hija]['madre']['estructural']
            sin = t[hija].astype(str) == estructural
            t[madre] = np.where(sin, 'NO', 'SI')
            t.loc[sin, hija] = ''
        return t[self.columnas]

    # ---- propiedades declaradas
    def spearman_tabla(self, t):
        """Matriz de Spearman de una tabla con este formato, comparable con self.objetivo."""
        nums = {}
        for v in self.latentes:
            d = self.defs[v]
            s = t[v].astype(str).where(t[v].astype(str) != '', d['madre']['estructural'] if d.get('madre') else '')
            if d['tipo'] == 'cuantitativa':
                nums[v] = s.astype(float).to_numpy()
            elif d['tipo'] == 'binaria':
                nums[v] = s.map({n: float(x['codigo']) for n, x in d['niveles'].items()}).astype(float).to_numpy()
            else:
                clave = _clave_nivel(d)
                nums[v] = s.map(lambda x: clave(x)[0]).astype(float).to_numpy()
        if self.tiene_imc:
            imc = t['imc'].astype(str)
            aus = (imc == '').to_numpy()
            nums['imc'] = np.where(aus, np.nan, pd.to_numeric(imc, errors='coerce'))
            nums['__imc_ausente'] = aus.astype(float)
        p = len(self.nombres)
        S = np.eye(p)
        for i in range(p):
            for j in range(i + 1, p):
                if {self.nombres[i], self.nombres[j]} == {'imc', '__imc_ausente'}:
                    continue
                a, b = nums[self.nombres[i]], nums[self.nombres[j]]
                m = ~(np.isnan(a) | np.isnan(b))
                r = spearmanr(a[m], b[m]).statistic
                S[i, j] = S[j, i] = 0.0 if np.isnan(r) else r
        return S


def v_cramer(a, b):
    t = pd.crosstab(pd.Series(a), pd.Series(b)).to_numpy().astype(float)
    if min(t.shape) < 2:
        return 0.0
    e = t.sum(axis=1, keepdims=True) * t.sum(axis=0, keepdims=True) / t.sum()
    chi = ((t - e) ** 2 / e).sum()
    return float(np.sqrt(chi / (t.sum() * (min(t.shape) - 1))))
