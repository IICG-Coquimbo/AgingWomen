"""
Indicadores de estabilidad de la Fase 35B. Son descriptivos: no modifican la selección.

Z es una matriz de remuestreos x variables, con 1 si la variable quedó seleccionada.
"""
import numpy as np
from scipy import stats


def banda(porcentaje):
    """Bandas descriptivas del protocolo."""
    return '>= 80 %' if porcentaje >= 80 else '50-79 %' if porcentaje >= 50 else '< 50 %'


def nogueira(Z, confianza=0.95):
    """
    Índice de estabilidad de Nogueira, Sechidis y Brown (2018) e intervalo de confianza.
    Devuelve NaN si la selección es vacía o completa en todos los remuestreos.
    """
    Z = np.asarray(Z, dtype=float)
    M, d = Z.shape
    p = Z.mean(axis=0)
    k = Z.sum(axis=1)
    k_medio = p.sum()
    denominador = (k_medio / d) * (1 - k_medio / d)
    if M < 2 or denominador == 0:
        return {'indice': np.nan, 'ic_inferior': np.nan, 'ic_superior': np.nan}
    indice = 1 - (M / (M - 1)) * np.mean(p * (1 - p)) / denominador
    phi = (1 / denominador) * ((Z * p).mean(axis=1) - k * k_medio / d ** 2
                               + (indice / 2) * (2 * k * k_medio / d ** 2 - k / d - k_medio / d + 1))
    varianza = (4 / M ** 2) * np.sum((phi - phi.mean()) ** 2)
    z = stats.norm.ppf(1 - (1 - confianza) / 2)
    return {'indice': float(indice), 'ic_inferior': float(indice - z * np.sqrt(varianza)),
            'ic_superior': float(indice + z * np.sqrt(varianza))}


def jaccard(a, b):
    """Jaccard de dos conjuntos; dos selecciones vacías valen 1."""
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 1.0


def jaccard_promedio(Z):
    """Promedio de Jaccard entre todos los pares de remuestreos."""
    Z = np.asarray(Z, dtype=int)
    M = len(Z)
    if M < 2:
        return np.nan
    interseccion = Z @ Z.T
    k = Z.sum(axis=1)
    union = k[:, None] + k[None, :] - interseccion
    with np.errstate(divide='ignore', invalid='ignore'):
        valores = np.where(union > 0, interseccion / union, 1.0)
    return float(valores[np.triu_indices(M, k=1)].mean())
