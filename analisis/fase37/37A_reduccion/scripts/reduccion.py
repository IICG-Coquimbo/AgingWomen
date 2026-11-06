"""
Fase 37A: núcleo de la reducción. Ajusta PCA sobre una matriz ya preparada, guarda el modelo en JSON y proyecta con él.

No escala: la matriz entra tal como salió de la Fase 36. FAMD es esta misma descomposición sobre F1 y F2, según la validación
matemática de la Fase 36B. Los valores propios siguen la convención n: explained_variance_ × (n − 1)/n.
"""
import json
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA

CANDIDATOS = [2, 3, 5, 8, 12, 16, 20]
UMBRALES = [50, 60, 70, 80, 90]


def ajustar(Z, columnas):
    """Z: arreglo de las filas de ajuste. Devuelve el modelo como diccionario, sin referencias a sklearn."""
    Z = np.asarray(Z, dtype=float)
    n = Z.shape[0]
    rango = int(np.linalg.matrix_rank(Z - Z.mean(axis=0)))
    pca = PCA(n_components=rango, svd_solver='full').fit(Z)
    lam = pca.explained_variance_ * (n - 1) / n
    return {'columnas': list(columnas), 'n_ajuste': n, 'rango': rango, 'media': pca.mean_.tolist(), 'componentes': pca.components_.tolist(),
            'valores_propios': lam.tolist(), 'valores_singulares': pca.singular_values_.tolist(), 'inercia_total': float(Z.var(axis=0).sum()),
            'solver': 'sklearn.decomposition.PCA(svd_solver="full")', 'convencion_valores_propios': 'n: explained_variance_ × (n − 1)/n'}


def proyectar(modelo, Z, k=None):
    """Coordenadas con parámetros congelados: (Z − media) · V. No recalcula nada con las filas recibidas."""
    V = np.asarray(modelo['componentes'])
    if k is not None:
        if k > modelo['rango']:
            raise ValueError(f'k = {k} supera el rango efectivo {modelo["rango"]}')
        V = V[:k]
    return (np.asarray(Z, dtype=float) - np.asarray(modelo['media'])) @ V.T


def guardar(modelo, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(modelo, ensure_ascii=False, indent=0) + '\n', encoding='utf-8', newline='\n')


def cargar(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


def componentes_para(lam, umbral):
    """Menor número de ejes cuyo porcentaje acumulado alcanza el umbral."""
    acum = 100 * np.cumsum(lam) / np.sum(lam)
    return int(np.searchsorted(acum, umbral - 1e-12) + 1)


def similitud_subespacio(A, B):
    """Media de cos² de los ángulos principales entre dos conjuntos de coordenadas de las mismas filas. 1 = mismo subespacio."""
    qa = np.linalg.qr(A - A.mean(axis=0))[0]
    qb = np.linalg.qr(B - B.mean(axis=0))[0]
    s = np.linalg.svd(qa.T @ qb, compute_uv=False)
    return float(np.mean(np.clip(s, 0, 1) ** 2))


def procrustes(base, variante):
    """Rotación ortogonal que lleva la variante hacia la base, calculada en las filas recibidas. No escala."""
    U, _, Vt = np.linalg.svd(variante.T @ base, full_matrices=False)
    return U @ Vt


def analisis_paralelo(Z, variable_de_columna, n_perm=200, semilla=(42, 0)):
    """Percentil 95 de cada valor propio al permutar cada variable por separado. Las indicadoras de una variable se mueven juntas."""
    Z = np.asarray(Z, dtype=float)
    n = Z.shape[0]
    grupos = {}
    for j, v in enumerate(variable_de_columna):
        grupos.setdefault(v, []).append(j)
    rng = np.random.default_rng(list(semilla))
    salida = []
    for _ in range(n_perm):
        X = np.empty_like(Z)
        for cols in grupos.values():
            X[:, cols] = Z[rng.permutation(n)][:, cols]
        salida.append(np.linalg.svd(X - X.mean(axis=0), compute_uv=False) ** 2 / n)
    return np.percentile(np.array(salida), 95, axis=0)
