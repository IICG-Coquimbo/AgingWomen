"""
Fase 37B: núcleo compartido. Carga entradas verificadas, ajusta, mide y compara. No escribe resultados.

Fija un hilo por proceso antes de importar numpy y scikit-learn, para que los resultados no dependan del paralelismo.
"""
import os

for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import hashlib  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

sys.dont_write_bytecode = True

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.cluster import AgglomerativeClustering, KMeans  # noqa: E402
from sklearn.exceptions import ConvergenceWarning  # noqa: E402
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_samples  # noqa: E402

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
FASE37 = BASE.parent
ANALISIS = FASE37.parent
RAIZ = ANALISIS.parent
F36 = ANALISIS / 'fase36'
A37 = FASE37 / '37A_reduccion'
sys.path[:0] = [str(F36), str(A37 / 'scripts')]

import reduccion as R  # noqa: E402
import transformador as TF  # noqa: E402

N = 529
N_SUB = 423
SEMILLA = 42
N_REP = 30
N_NULA = 20
UMBRAL_TAMANO = 27
COMPONENTES = [2, 3, 5, 8, 12, 16, 20]
CLUSTERES = [2, 3, 4, 5, 6, 7, 8]
ALGORITMOS = ['km', 'ward']
ESPACIOS = ['P1', 'P2', 'F1', 'F2']
ESPACIOS_R0 = ['R0P1', 'R0P2']
MATRIZ = {'P1': 'P1_pca_con_imc', 'P2': 'P2_pca_sin_imc', 'F1': 'F1_famd_con_imc', 'F2': 'F2_famd_sin_imc'}
FAMILIA = {'S-ORD': 'Codificación', 'S-FAMD': 'Codificación', 'S-RARA': 'Codificación', 'S-TRA': 'Población', 'S-CUI': 'Población', 'S-EJE': 'Población',
           'S-EDAD': 'Variables', 'S-SOLAPE': 'Variables', 'S-BLOQUE': 'Ponderación', 'S-BLOQUE-SA': 'Ponderación'}
# Cada frecuencia se mueve con su pregunta madre.
MADRES = {'frecuencia_aerobico': 'realiza_aerobico', 'frecuencia_bajo_impacto': 'realiza_bajo_impacto', 'frecuencia_fuerza': 'realiza_fuerza', 'cantidad_personas_cuida': 'cuida_otras_personas'}
NO_GENERALES = ('estres_entorno_laboral', 'lugar_trabajo_comprensivo', 'sobrecarga_fisica_emocional')
TERMINOS_EXCLUIDOS = ('mrs', 'severo', 'severidad', 'sintoma_')


_LEIDOS = set()
_ESCRITOS = set()


def _gancho(evento, args):
    if evento == 'open' and isinstance(args[0], (str, Path)):
        modo, banderas = args[1], args[2] if len(args) > 2 else 0
        escribe = (isinstance(modo, str) and any(x in modo for x in 'wax+')) or (not isinstance(modo, str) and isinstance(banderas, int) and bool(banderas & (os.O_WRONLY | os.O_RDWR)))
        (_ESCRITOS if escribe else _LEIDOS).add(str(args[0]))


def instalar_gancho():
    sys.addaudithook(_gancho)


def leidos():
    """Archivos abiertos por este proceso hasta ahora, como rutas absolutas."""
    return sorted(_LEIDOS), sorted(_ESCRITOS)


def registrar(S, etapa, resultados):
    """Agrega tiempos y estados al registro de ejecución, y las lecturas y escrituras al registro de auditoría."""
    S = Path(S)
    d = S / 'integridad'
    d.mkdir(parents=True, exist_ok=True)
    reg = pd.DataFrame([{'etapa': etapa, 'trabajo': r[0], 'estado': r[1], 'segundos': round(r[2], 2)} for r in resultados])
    ruta = d / 'registro_ejecucion.csv'
    reg.to_csv(ruta, mode='a', header=not ruta.exists(), index=False, encoding='utf-8', lineterminator='\n')
    raiz = RAIZ.resolve()
    leidos_, fuera = set(), set()
    for r in resultados:
        for x in r[3][0]:
            a = Path(x).resolve()
            if a.is_relative_to(raiz) and a.is_file() and a.suffix not in ('.py', '.pyc') and '.git' not in a.parts and (not a.is_relative_to(S)):
                leidos_.add(a.relative_to(raiz).as_posix())
        for x in r[3][1]:
            a = Path(x).resolve()
            if not a.is_relative_to(S) and a.suffix not in ('.pyc',):
                fuera.add(str(a))
    for nombre, col, valores in (('archivos_leidos.csv', 'archivo_leido', leidos_), ('escrituras_fuera.csv', 'escritura_fuera', fuera)):
        ruta = d / nombre
        previos = set(pd.read_csv(ruta)[col].astype(str)) if ruta.exists() else set()
        pd.DataFrame({col: sorted(previos | valores)}, dtype=str).to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')
    prohibidos = [x for x in leidos_ if x.startswith('datos/') or 'verdad' in x or 'bitacora' in x]
    if prohibidos or fuera:
        raise SystemExit(f'Lectura prohibida o escritura fuera de la salida: {prohibidos} {sorted(fuera)[:5]}')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def huella_sello():
    s = json.loads((BASE / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    if sha(BASE / 'protocolo' / s['archivo']) != s['sha256']:
        raise SystemExit('El protocolo no coincide con su sello.')
    return s['sha256']


def identificadores():
    return pd.read_csv(F36 / 'matrices' / 'identificadores.csv', dtype=str)['participante_id'].tolist()


def configuraciones():
    """Las 420 configuraciones principales, siempre en el mismo orden."""
    filas = []
    for e in ESPACIOS:
        for c in COMPONENTES:
            for a in ALGORITMOS:
                for k in CLUSTERES:
                    filas.append({'config': f'{e}_c{c:02d}_{a}_k{k}', 'espacio': e, 'base': e, 'metodo': 'PCA' if e[0] == 'P' else 'FAMD', 'con_imc': e[1] == '1', 'componentes': c, 'algoritmo': a, 'k': k})
    for e in ESPACIOS_R0:
        for a in ALGORITMOS:
            for k in CLUSTERES:
                filas.append({'config': f'{e}_cTodas_{a}_k{k}', 'espacio': e, 'base': e[2:], 'metodo': 'Sin reducción', 'con_imc': e == 'R0P1', 'componentes': 0, 'algoritmo': a, 'k': k})
    return filas


def coordenadas(e, c):
    if c == 0:
        return matriz(e[2:])
    x = pd.read_csv(A37 / 'coordenadas' / e / f'coordenadas_k{c:02d}.csv', dtype={'participante_id': str}).set_index('participante_id')
    return x


def matriz(e):
    x = pd.read_csv(F36 / 'matrices' / f'{MATRIZ[e]}.csv')
    x.index = identificadores()
    x.index.name = 'participante_id'
    return x


def eje1(base):
    x = pd.read_csv(A37 / 'coordenadas' / base / 'coordenadas_k02.csv', dtype={'participante_id': str}).set_index('participante_id')
    return x['C1']


def ajustar_km(X, k, semilla=SEMILLA):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always', ConvergenceWarning)
        m = KMeans(n_clusters=k, n_init=50, random_state=semilla, algorithm='lloyd').fit(X)
    return m.labels_.astype(int), {'iteraciones': int(m.n_iter_), 'max_iter': int(m.max_iter), 'convergio': bool(m.n_iter_ < m.max_iter and not any(issubclass(x.category, ConvergenceWarning) for x in w)), 'inercia': float(m.inertia_)}, m.cluster_centers_


def ajustar_ward(X, k):
    m = AgglomerativeClustering(n_clusters=k, linkage='ward', metric='euclidean').fit(X)
    return m.labels_.astype(int), {'iteraciones': None, 'max_iter': None, 'convergio': True, 'inercia': None}, None


def ajustar(X, a, k, semilla=SEMILLA):
    return ajustar_km(X, k, semilla) if a == 'km' else ajustar_ward(X, k)


def prototipos(X, l, k):
    return np.vstack([X[l == g].mean(axis=0) for g in range(k)])


def asignar(protos, X):
    """Prototipo más cercano. Devuelve etiqueta, distancia al más cercano, al segundo y margen 1 − d1/d2. No recalcula nada con las filas recibidas."""
    d = np.sqrt(((np.asarray(X)[:, None, :] - np.asarray(protos)[None, :, :]) ** 2).sum(axis=2))
    et = d.argmin(axis=1)
    o = np.sort(d, axis=1)
    return et, o[:, 0], o[:, 1], 1 - o[:, 0] / np.where(o[:, 1] > 0, o[:, 1], 1)


def inercia_interna(X, l):
    return float(sum(((X[l == g] - X[l == g].mean(axis=0)) ** 2).sum() for g in np.unique(l)))


def fraccion_eje1(X, l, c1):
    """Parte de la separación entre grupos que ocurre sobre el eje 1: SSB en C1 / SSB total."""
    media = X.mean(axis=0)
    ssb = sum((l == g).sum() * ((X[l == g].mean(axis=0) - media) ** 2).sum() for g in np.unique(l))
    ssb1 = sum((l == g).sum() * (c1[l == g].mean() - c1.mean()) ** 2 for g in np.unique(l))
    return float(ssb1 / ssb) if ssb > 0 else float('nan')


def calidad(X, l):
    s = silhouette_samples(X, l, metric='euclidean')
    return {'silueta': float(s.mean()), 'silueta_negativos': float((s < 0).mean()), 'silueta_min': float(s.min()), 'silueta_max': float(s.max()),
            'davies_bouldin': float(davies_bouldin_score(X, l)), 'calinski_harabasz': float(calinski_harabasz_score(X, l))}, s


def tamanos(l, k, umbral=UMBRAL_TAMANO):
    t = np.bincount(l, minlength=k)
    p = t[t > 0] / t.sum()
    return {'tam_min': int(t.min()), 'tam_max': int(t.max()), 'razon_tam': float(t.max() / max(t.min(), 1)), 'equilibrio': float(-(p * np.log(p)).sum() / np.log(k)), 'grupos_pequenos': int((t < umbral).sum()), 'tamanos': t.tolist()}


def subconjuntos():
    """Los 30 subconjuntos, como posiciones ordenadas. Salen de una sola semilla y son iguales para todas las configuraciones."""
    rng = np.random.default_rng(SEMILLA)
    return [np.sort(rng.choice(N, size=N_SUB, replace=False)) for _ in range(N_REP)]


def semilla_rep(r):
    return int(np.random.SeedSequence([SEMILLA, r]).generate_state(1)[0] % (2 ** 31))


def resumir(v, prefijo):
    v = np.asarray(v, dtype=float)
    return {f'{prefijo}_media': float(v.mean()), f'{prefijo}_mediana': float(np.median(v)), f'{prefijo}_de': float(v.std(ddof=1)), f'{prefijo}_min': float(v.min()), f'{prefijo}_max': float(v.max()),
            f'{prefijo}_p05': float(np.percentile(v, 5)), f'{prefijo}_p25': float(np.percentile(v, 25)), f'{prefijo}_p75': float(np.percentile(v, 75)),
            f'{prefijo}_n_baja': int((v < 0.65).sum()), f'{prefijo}_n_intermedia': int(((v >= 0.65) & (v <= 0.80)).sum()), f'{prefijo}_n_alta': int((v > 0.80).sum())}


def estabilidad(X, a, k, l_completo, subs, detalle=False):
    """Vuelve a ajustar en cada subconjunto. Solo le entrega al algoritmo las filas del subconjunto."""
    etiquetas, frente, fuera = [], [], []
    for r, idx in enumerate(subs):
        lr, _, _ = ajustar(X[idx], a, k, semilla_rep(r))
        etiquetas.append(lr)
        frente.append(adjusted_rand_score(l_completo[idx], lr))
        resto = np.setdiff1d(np.arange(len(X)), idx)
        grupos = np.unique(lr)
        protos = np.vstack([X[idx][lr == g].mean(axis=0) for g in grupos])
        fuera.append(adjusted_rand_score(l_completo[resto], grupos[asignar(protos, X[resto])[0]]))
    entre = []
    posiciones = [np.full(len(X), -1) for _ in subs]
    for p, idx, lr in zip(posiciones, subs, etiquetas):
        p[idx] = lr
    for i in range(len(subs)):
        for j in range(i + 1, len(subs)):
            ambas = (posiciones[i] >= 0) & (posiciones[j] >= 0)
            entre.append(adjusted_rand_score(posiciones[i][ambas], posiciones[j][ambas]))
    res = {**resumir(frente, 'ari_completo'), **resumir(entre, 'ari_entre'), **resumir(fuera, 'ari_fuera')}
    return (res, frente, fuera) if detalle else res


def tabla_general():
    """Variables generales previas a la reducción, desde la procedencia de la Fase 36. Incluye las preguntas madre, que el Transformador necesita."""
    c = pd.read_csv(F36 / 'procedencia' / 'procedencia_celdas.csv', dtype=str, keep_default_na=False)
    p = c.pivot(index='participante_id', columns='variable', values='valor_original').reindex(identificadores())
    p = p[[v for v in p.columns if v not in NO_GENERALES]]
    for v, m in MADRES.items():
        p[m] = np.where(p[v] == '', 'NO', 'SI')
    return p


def permutar_general(p, replica):
    """Permuta cada variable por separado. Cada frecuencia se mueve con su madre. Las filas siguen siendo participantes, pero sin relación entre sus variables."""
    t = p.copy()
    orden = [v for v in sorted(p.columns) if v not in MADRES.values()]
    for i, v in enumerate(orden):
        rng = np.random.default_rng(np.random.SeedSequence([SEMILLA, 1000 + replica, i]))
        perm = rng.permutation(len(p))
        t[v] = p[v].to_numpy()[perm]
        if v in MADRES:
            t[MADRES[v]] = p[MADRES[v]].to_numpy()[perm]
    return t


def espacios_nulos(p, replica):
    """Devuelve, para una réplica, las coordenadas de cada configuración: transforma con parámetros congelados y recalcula la reducción."""
    t = permutar_general(p, replica)
    salida = {}
    for e in ESPACIOS:
        Z = TF.Transformador.cargar(F36 / 'artefactos' / e).transformar(t)[0]
        m = R.ajustar(Z.to_numpy(), list(Z.columns))
        salida[e] = R.proyectar(m, Z.to_numpy(), 20)
        if e[0] == 'P':
            salida['R0' + e] = Z.to_numpy()
    return salida


def verificar_columnas(columnas):
    malas = [c for c in columnas if any(t in str(c).lower() for t in TERMINOS_EXCLUIDOS)]
    if malas:
        raise ValueError(f'Columnas excluidas en la entrada: {malas}')
