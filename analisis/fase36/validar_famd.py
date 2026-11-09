"""
Fase 36B: validación matemática de la transformación FAMD, solo con datos de prueba sintéticos.

Uso, desde analisis/: python fase36/validar_famd.py [--referencia CARPETA_CON_PRINCE] [--salida CARPETA]

Comprueba que las columnas `(I − p)/√p` y z, seguidas de una descomposición en valores singulares, son FAMD. Compara con cuatro
derivaciones independientes de esa transformación: el criterio de Pagès (suma de r² y η²), la descomposición con métrica de columnas
1/p, el análisis de correspondencias cuando todo es categórico y las correlaciones cuando todo es cuantitativo. Si se indica la
carpeta, compara además con la biblioteca `prince`, que no es dependencia del proyecto.

No lee datos del estudio y no ajusta nada sobre las matrices reales: eso corresponde a la Fase 37.
"""
import argparse
import json
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import configuracion_fase36 as C  # noqa: E402
import transformador as T  # noqa: E402

TOL = 1e-8


def datos_prueba(n=400, semilla=C.SEMILLA):
    r = np.random.default_rng(semilla)
    latente = r.normal(size=n)
    q = pd.DataFrame({f'q{i}': np.round(40 + 10 * (0.6 * latente + r.normal(size=n)) * (i + 1), 3) for i in range(4)})

    def categoria(niveles, peso):
        s = peso * latente + r.normal(size=n)
        cortes = np.quantile(s, np.cumsum([1 / len(niveles)] * (len(niveles) - 1)))
        return pd.Series(np.array(niveles)[np.searchsorted(cortes, s)])

    q['c2'] = categoria(['A', 'B'], 0.8)
    q['c3'] = categoria(['X', 'Y', 'Z'], 0.5)
    q['c4'] = categoria(['p', 'q', 'r', 's'], 0.3)
    q.index = [f'f{i}' for i in range(n)]
    return q


def definiciones(datos, cuant, cat):
    defs = []
    for v in cuant:
        defs.append({'variable': v, 'tipo': 'cuantitativa', 'rol_famd': 'cuantitativa', 'limites': [-1e6, 1e6], 'niveles': None})
    for v in cat:
        niveles = {x: {'codigo': None, 'significado': x} for x in sorted(datos[v].unique())}
        defs.append({'variable': v, 'tipo': 'nominal', 'rol_famd': 'categorica', 'niveles': niveles})
    return defs


def descomponer(Z):
    U, s, Vt = np.linalg.svd(Z, full_matrices=False)
    return U, s, Vt, s ** 2 / len(Z)


def alinear(a, b):
    """Diferencia máxima entre coordenadas, sin importar el signo arbitrario de cada eje."""
    return max(min(np.abs(a[:, k] - b[:, k]).max(), np.abs(a[:, k] + b[:, k]).max()) for k in range(a.shape[1]))


def eta2(categoria, f):
    media = f.mean()
    entre = sum((f[categoria == c].mean() - media) ** 2 * (categoria == c).sum() for c in np.unique(categoria))
    return entre / ((f - media) ** 2).sum()


def importar_prince(carpeta):
    """Carga prince desde una carpeta externa, sin instalarlo. altair solo se usa para gráficos: se sustituye por un módulo vacío."""
    if 'altair' not in sys.modules:
        try:
            import altair  # noqa: F401
        except ImportError:
            sys.modules['altair'] = types.ModuleType('altair')
    sys.path.insert(0, carpeta)
    import prince
    return prince


def validar(carpeta_prince=None):
    filas = []

    def anotar(comprobacion, obtenido, esperado, ok=None, tol=TOL, seccion='general'):
        dif = abs(float(obtenido) - float(esperado)) if ok is None else float('nan')
        filas.append({'seccion': seccion, 'comprobacion': comprobacion, 'obtenido': obtenido, 'esperado': esperado, 'tolerancia': tol if ok is None else '',
                      'resultado': 'OK' if (dif <= tol if ok is None else ok) else 'NO CUMPLE'})

    d = datos_prueba()
    cuant, cat = ['q0', 'q1', 'q2', 'q3'], ['c2', 'c3', 'c4']
    defs = definiciones(d, cuant, cat)
    params = T.calibrar(d, defs, 'famd')
    tr = T.Transformador(params)
    Z, _ = tr.transformar(d)
    z = Z.to_numpy()
    n = len(z)
    U, s, Vt, lam = descomponer(z)
    F = U * s

    # 1. Estructura de columnas e inercia, calculadas con los datos crudos y no con la matriz.
    anotar('Todas las columnas tienen media cero', np.abs(z.mean(axis=0)).max(), 0, seccion='Ponderación')
    anotar('Cada cuantitativa tiene varianza 1', np.abs(Z[cuant].var(ddof=0) - 1).max(), 0, seccion='Ponderación')
    dif = []
    for v in cat:
        for nivel, frecuencia in d[v].value_counts(normalize=True).items():
            dif.append(abs(Z[f'{v}__{nivel}'].var(ddof=0) - (1 - frecuencia)))
    anotar('Varianza de cada indicadora = 1 − p', max(dif), 0, seccion='Ponderación')
    esperada = len(cuant) + sum(d[v].nunique() - 1 for v in cat)
    anotar('Inercia total = cuantitativas + Σ(K − 1)', z.var(axis=0).sum(), esperada, seccion='Inercia')
    anotar('La suma de valores propios iguala la inercia', lam.sum(), esperada, seccion='Inercia')
    anotar('Rango = columnas − una por categórica', (s > 1e-9).sum(), z.shape[1] - len(cat), seccion='Inercia')

    # 2. Métrica de columnas 1/p: la formulación clásica, sin dividir las indicadoras.
    Xq = ((d[cuant] - d[cuant].mean()) / d[cuant].std(ddof=0)).to_numpy()
    nucleo = Xq @ Xq.T
    for v in cat:
        I = pd.get_dummies(d[v], dtype=float).to_numpy()
        p = I.mean(axis=0)
        X = I - p
        nucleo += X @ np.diag(1 / p) @ X.T
    val, vec = np.linalg.eigh(nucleo / n)
    orden = np.argsort(val)[::-1]
    val, vec = val[orden], vec[:, orden]
    r = (s > 1e-9).sum()
    anotar('Valores propios iguales a la métrica 1/p', np.abs(val[:r] - lam[:r]).max(), 0, seccion='Equivalencia: métrica 1/p')
    F_nucleo = vec[:, :8] * np.sqrt(n * val[:8])
    anotar('Coordenadas iguales a la métrica 1/p (8 ejes)', alinear(F[:, :8], F_nucleo), 0, tol=1e-7, seccion='Equivalencia: métrica 1/p')

    # 3. Criterio de Pagès: en cada eje, valor propio = Σ r²(cuantitativa, eje) + Σ η²(categórica, eje).
    max_dif = 0
    for k in range(10):
        suma = sum(np.corrcoef(d[v].to_numpy(), F[:, k])[0, 1] ** 2 for v in cuant) + sum(eta2(d[v].to_numpy(), F[:, k]) for v in cat)
        max_dif = max(max_dif, abs(suma - lam[k]))
    anotar('λ = Σ r² + Σ η² en los 10 primeros ejes', max_dif, 0, seccion='Equivalencia: criterio de Pagès')

    # Control negativo: si las indicadoras se dividen por p en vez de √p, el criterio debe romperse.
    mala = Z.copy()
    for col, e in params['escaladores'].items():
        if e['clase'] == 'indicadora_famd':
            mala[col] = Z[col] / np.sqrt(e['p'])
    Ub, sb, _, lam_b = descomponer(mala.to_numpy())
    Fb = Ub * sb
    error_malo = max(abs(sum(np.corrcoef(d[v].to_numpy(), Fb[:, k])[0, 1] ** 2 for v in cuant) + sum(eta2(d[v].to_numpy(), Fb[:, k]) for v in cat) - lam_b[k]) for k in range(10))
    anotar('Control negativo: con la ponderación equivocada el criterio se rompe', round(error_malo, 4), '> 0,01', ok=error_malo > 0.01, seccion='Equivalencia: criterio de Pagès')

    # 4. Casos límite: todo categórico equivale a MCA y todo cuantitativo a PCA de correlaciones.
    defs_cat = definiciones(d, [], cat)
    z_cat = T.Transformador(T.calibrar(d, defs_cat, 'famd')).transformar(d)[0].to_numpy()
    lam_cat = descomponer(z_cat)[3]
    I = pd.concat([pd.get_dummies(d[v], dtype=float) for v in cat], axis=1).to_numpy()
    P = I / I.sum()
    fila, columna = P.sum(axis=1), P.sum(axis=0)
    residuos = (P - np.outer(fila, columna)) / np.sqrt(np.outer(fila, columna))
    lam_mca = np.linalg.svd(residuos, compute_uv=False) ** 2
    m = sum(d[v].nunique() for v in cat) - len(cat)
    anotar('Solo categóricas: λ = Q × λ(MCA)', np.abs(lam_cat[:m] - len(cat) * lam_mca[:m]).max(), 0, seccion='Equivalencia: casos límite')
    defs_q = definiciones(d, cuant, [])
    z_q = T.Transformador(T.calibrar(d, defs_q, 'famd')).transformar(d)[0].to_numpy()
    lam_cor = np.sort(np.linalg.eigvalsh(np.corrcoef(d[cuant].to_numpy().T)))[::-1]
    anotar('Solo cuantitativas: λ = correlaciones', np.abs(descomponer(z_q)[3] - lam_cor).max(), 0, seccion='Equivalencia: casos límite')

    # 5. PCA de scikit-learn: no reescala. Su varianza usa n − 1, por lo que λ de FAMD = varianza × (n − 1) / n.
    pca = PCA(svd_solver='full').fit(z)
    anotar('scikit-learn: varianza × (n − 1)/n = λ', np.abs(pca.explained_variance_[:r] * (n - 1) / n - lam[:r]).max(), 0, seccion='Equivalencia: scikit-learn')
    anotar('scikit-learn: mismas coordenadas (8 ejes)', alinear(pca.transform(z)[:, :8], F[:, :8]), 0, tol=1e-7, seccion='Equivalencia: scikit-learn')

    # 6. Sin doble estandarización: el peso reducido de una variable con la mitad de valores en la media sobrevive y el criterio lo refleja.
    dm = d.copy()
    faltan = np.arange(n) % 2 == 0
    dm['q0'] = dm['q0'].where(~faltan, np.nan)
    defs_m = definiciones(dm.assign(c2=d['c2']), cuant, cat)
    for x in defs_m:
        if x['variable'] == 'q0':
            x['ausente_es_media'] = True
    tr_m = T.Transformador(T.calibrar(dm, defs_m, 'famd'))
    Zm, av = tr_m.transformar(dm)
    observada = dm['q0'].dropna().to_numpy()
    var_esperada = ((observada - observada.mean()) ** 2).sum() / observada.std() ** 2 / n
    anotar('Variable con media asignada: varianza = fracción observada', Zm['q0'].var(ddof=0), var_esperada, seccion='Doble estandarización')
    anotar('Valores asignados con z = 0 exacto', np.abs(Zm.loc[faltan, 'q0']).max(), 0, tol=0, seccion='Doble estandarización')
    anotar('Filas con marca de ausencia', (av['marca'] == 'imc_ausente').sum(), faltan.sum(), tol=0, seccion='Doble estandarización')
    Um, sm, _, lam_m = descomponer(Zm.to_numpy())
    Fm = Um * sm
    max_dif = 0
    for k in range(8):
        f = Fm[:, k]
        # Con peso reducido, el aporte de la variable es su varianza por r².
        aporte_q0 = Zm['q0'].var(ddof=0) * np.corrcoef(Zm['q0'], f)[0, 1] ** 2
        suma = aporte_q0 + sum(np.corrcoef(d[v].to_numpy(), f)[0, 1] ** 2 for v in cuant[1:]) + sum(eta2(d[v].to_numpy(), f) for v in cat)
        max_dif = max(max_dif, abs(suma - lam_m[k]))
    anotar('Con peso reducido, λ = v·r² + Σ r² + Σ η²', max_dif, 0, seccion='Doble estandarización')
    reescalada = Zm['q0'] / Zm['q0'].std(ddof=0)
    anotar('Una segunda estandarización sí cambiaría el peso (se detecta)', reescalada.var(ddof=0), 1, seccion='Doble estandarización')
    anotar('La inercia lleva el peso reducido, no el reescalado', Zm.var(ddof=0).sum(), esperada - 1 + var_esperada, seccion='Doble estandarización')

    # 7. Categorías sin observaciones.
    dv = d.copy()
    defs_v = definiciones(d, cuant, cat)
    next(x for x in defs_v if x['variable'] == 'c2')['niveles']['SIN_DATOS'] = {'codigo': None, 'significado': 'sin datos'}
    try:
        T.calibrar(dv, defs_v, 'famd')
        rechazada = False
    except ValueError:
        rechazada = True
    anotar('Categoría propia con frecuencia cero: se rechaza (evita dividir por 0)', int(rechazada), 1, ok=rechazada, seccion='Categorías vacías')
    grupos = {'c2': {'A': ['A'], 'B': ['B', 'SIN_DATOS']}}
    tr_v = T.Transformador(T.calibrar(dv, defs_v, 'famd', grupos=grupos))
    Zv, _ = tr_v.transformar(dv)
    nueva = dv.iloc[[0]].copy()
    nueva['c2'] = 'SIN_DATOS'
    Zn, _ = tr_v.transformar(nueva)
    b = dv.iloc[[0]].copy()
    b['c2'] = 'B'
    anotar('Nivel sin observaciones unido a un grupo: finito e igual a su grupo', np.abs(Zn.to_numpy() - tr_v.transformar(b)[0].to_numpy()).max(), 0, tol=0, seccion='Categorías vacías')
    anotar('La columna vacía no se crea', int(any('SIN_DATOS' in c for c in Zv.columns)), 0, tol=0, seccion='Categorías vacías')
    try:
        tr.transformar(nueva)
        error = False
    except T.ErrorValor:
        error = True
    anotar('Nivel no admitido por el esquema: error', int(error), 1, ok=error, seccion='Categorías vacías')

    # 8. Reproducibilidad.
    otra = T.calibrar(d, defs, 'famd')
    anotar('Calibrar dos veces da parámetros idénticos', int(json.dumps(otra) == json.dumps(params)), 1, tol=0, seccion='Reproducibilidad')
    permutados = T.calibrar(d.sample(frac=1, random_state=C.SEMILLA), defs, 'famd')
    a, b2 = pd.Series(pd.json_normalize(permutados['escaladores']).iloc[0]), pd.Series(pd.json_normalize(params['escaladores']).iloc[0])
    numericos = [k for k in a.index if isinstance(a[k], float)]
    anotar('El orden de las filas no cambia los parámetros', max(abs(a[k] - b2[k]) for k in numericos), 0, tol=1e-12, seccion='Reproducibilidad')

    # 9. Participante nueva: fila a fila y con parámetros congelados.
    copia = json.dumps(params, sort_keys=True)
    uno = pd.concat([tr.transformar(d.iloc[[i]])[0] for i in range(0, n, 37)])
    anotar('Fila de referencia como caso nuevo = misma fila', np.abs(uno.to_numpy() - Z.iloc[list(range(0, n, 37))].to_numpy()).max(), 0, tol=1e-12, seccion='Nueva participante')
    anotar('Transformar no altera los parámetros', int(copia == json.dumps(tr.p, sort_keys=True)), 1, tol=0, seccion='Nueva participante')
    F_nueva = uno.to_numpy() @ Vt.T
    anotar('Proyección de un caso nuevo = coordenada original', np.abs(F_nueva - F[list(range(0, n, 37))]).max(), 0, tol=1e-9, seccion='Nueva participante')

    # 10. Implementación de referencia, solo si se indica su carpeta.
    info_prince = {'disponible': False}
    if carpeta_prince:
        prince = importar_prince(carpeta_prince)
        version = next((p.name.split('-')[1].replace('.dist', '') for p in Path(carpeta_prince).glob('prince-*.dist-info')), 'desconocida')
        info_prince = {'disponible': True, 'version': version, 'instalada_en_el_proyecto': False}
        ds = d.copy()
        for v in cuant:
            ds[v] = ds[v].astype(float)
        modelo = prince.FAMD(n_components=8, n_iter=10, random_state=C.SEMILLA, engine='sklearn', categorical_columns=cat).fit(ds)
        anotar(f'prince {version}: 8 valores propios', np.abs(np.asarray(modelo.eigenvalues_)[:8] - lam[:8]).max(), 0, tol=1e-6, seccion='Referencia externa')
        coordenadas = modelo.row_coordinates(ds).to_numpy()
        anotar(f'prince {version}: coordenadas de filas (8 ejes)', alinear(coordenadas[:, :8], F[:, :8]), 0, tol=1e-5, seccion='Referencia externa')
        # prince recalcula las proporciones con los datos que recibe: con una sola fila, deja de usar las de referencia.
        una = modelo.row_coordinates(ds.iloc[[0]]).to_numpy()
        info_prince['diferencia_fila_sola_sin_congelar'] = float(np.abs(np.abs(una[0, :8]) - np.abs(F[0, :8])).max())
        anotar('prince no congela proporciones al proyectar una sola fila; el transformador propio sí',
               round(info_prince['diferencia_fila_sola_sin_congelar'], 6), '> 0', ok=info_prince['diferencia_fila_sola_sin_congelar'] > 1e-3, seccion='Referencia externa')
    return pd.DataFrame(filas), info_prince


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--referencia')
    ap.add_argument('--salida', default=str(AQUI / 'validacion'))
    a = ap.parse_args()
    tabla, info = validar(a.referencia)
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(salida / 'validacion_famd.csv', index=False, encoding='utf-8', lineterminator='\n')
    fallos = tabla[tabla['resultado'] != 'OK']
    resumen = {'datos': 'sintéticos (n = 400, semilla 42); ningún dato del estudio', 'comprobaciones': len(tabla), 'cumplen': int((tabla['resultado'] == 'OK').sum()),
               'referencia_externa': info, 'veredicto': 'SATISFACTORIA' if fallos.empty else 'NO SATISFACTORIA'}
    (salida / 'validacion_famd.json').write_text(json.dumps(resumen, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(tabla[['seccion', 'comprobacion', 'obtenido', 'resultado']].to_string(max_colwidth=62))
    print(resumen)


if __name__ == '__main__':
    main()
