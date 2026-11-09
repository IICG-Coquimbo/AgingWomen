"""
Medidas de la Fase 35B: incertidumbre simétrica (SU), prueba por permutaciones,
corrección de Benjamini-Hochberg, semillas deterministas y discretización.

SU(X,Y) = 2·I(X;Y) / [H(X) + H(Y)], con log2 y frecuencias observadas, sin
corrección de sesgo. Protocolo: analisis/protocolo_fase35b.md.
"""
import numpy as np
from scipy import stats

from . import configuracion as C

LOTE_PERMUTACIONES = 1000


def codificar(x):
    """Códigos enteros 0..k-1 de cualquier arreglo de categorías."""
    return np.unique(np.asarray(x), return_inverse=True)[1]


def _entropia_filas(conteos, n):
    """Entropía en bits de cada fila de una matriz de conteos."""
    p = conteos / n
    with np.errstate(divide='ignore', invalid='ignore'):
        terminos = np.where(p > 0, p * np.log2(p), 0.0)
    return -terminos.sum(axis=1)


def entropia(x):
    x = codificar(x)
    return float(_entropia_filas(np.bincount(x)[None, :], len(x))[0]) if len(x) else 0.0


def _su_desde_entropias(hx, hy, hxy):
    return np.clip(2 * (hx + hy - hxy) / (hx + hy), 0.0, 1.0)


def su(x, y):
    """Incertidumbre simétrica de dos variables categóricas. Si no hay variación, SU = 0."""
    x, y = codificar(x), codificar(y)
    if len(x) == 0:
        return 0.0
    hx, hy = entropia(x), entropia(y)
    if hx == 0 or hy == 0:
        return 0.0
    conjunta = np.bincount(x * (y.max() + 1) + y)[None, :]
    return float(_su_desde_entropias(hx, hy, _entropia_filas(conjunta, len(x))[0]))


def prueba_permutacion(permutada, fija, n_permutaciones, rng, tolerancia=C.TOLERANCIA_SU_35B):
    """
    (SU observada, p). Baraja `permutada` entre las mismas personas y deja `fija`.
    p = (1 + nº de permutaciones con SU >= observada) / (n_permutaciones + 1).
    Una variable constante da SU = 0 y p = 1.
    """
    x, y = codificar(permutada), codificar(fija)
    if len(x) == 0:
        return 0.0, 1.0
    n, kx, ky = len(x), x.max() + 1, y.max() + 1
    hx = _entropia_filas(np.bincount(x, minlength=kx)[None, :], n)[0]
    hy = _entropia_filas(np.bincount(y, minlength=ky)[None, :], n)[0]
    if hx == 0 or hy == 0:
        return 0.0, 1.0
    conjunta = np.bincount(x * ky + y, minlength=kx * ky)[None, :]
    observada = float(_su_desde_entropias(hx, hy, _entropia_filas(conjunta, n)[0]))
    mayores, hechas = 0, 0
    while hechas < n_permutaciones:
        m = min(LOTE_PERMUTACIONES, n_permutaciones - hechas)
        barajada = rng.permuted(np.tile(x, (m, 1)), axis=1)
        indices = barajada * ky + y + np.arange(m)[:, None] * (kx * ky)
        conteos = np.bincount(indices.ravel(), minlength=m * kx * ky).reshape(m, -1)
        valores = _su_desde_entropias(hx, hy, _entropia_filas(conteos, n))
        mayores += int((valores >= observada - tolerancia).sum())
        hechas += m
    return observada, (1 + mayores) / (n_permutaciones + 1)


def benjamini_hochberg(valores_p):
    """Valores q de una familia completa. Una familia vacía devuelve un arreglo vacío."""
    valores_p = np.asarray(valores_p, dtype=float)
    return stats.false_discovery_control(valores_p, method='bh') if len(valores_p) else valores_p


def generador(analisis, remuestreo, tipo, indice=0):
    """
    Generador independiente y determinista para un cálculo. La clave usa solo enteros
    fijos: el resultado no depende del orden de cálculo ni del número de procesos.
    """
    return np.random.default_rng(np.random.SeedSequence(C.SEMILLA, spawn_key=(analisis, remuestreo, tipo, indice)))


def tramos_cerrados_derecha(x, cortes):
    """Tramos (a, b]: los valores iguales a un corte quedan en el tramo inferior. Los cortes repetidos se fusionan."""
    return np.searchsorted(np.unique(np.asarray(cortes, dtype=float)), np.asarray(x, dtype=float), side='left')


def tramos_cerrados_izquierda(x, cortes):
    """Tramos [a, b): los valores iguales a un corte quedan en el tramo superior."""
    return np.searchsorted(np.asarray(cortes, dtype=float), np.asarray(x, dtype=float), side='right')
