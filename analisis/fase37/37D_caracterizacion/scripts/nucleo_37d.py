"""
Fase 37D: núcleo compartido. Carga verificada de las 529 participantes, etiquetas históricas de A y B1, MRS y funciones estadísticas.

Lee las Fases 36 a 37C y los datos limpios sin modificarlos. Un gancho de auditoría registra cada archivo abierto y detiene la ejecución si se abre
un archivo del simulador. Un hilo por biblioteca numérica.
"""
import os
import sys

sys.dont_write_bytecode = True
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import hashlib  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
FASE37 = BASE.parent
ANALISIS = FASE37.parent
RAIZ = ANALISIS.parent
F36 = ANALISIS / 'fase36'
A37 = FASE37 / '37A_reduccion'
B37 = FASE37 / '37B_clustering'
C37 = FASE37 / '37C_comparacion_seleccion'
CMP = FASE37 / '37C_complemento_tres_preguntas'
LIMPIO = RAIZ / 'datos' / 'limpio_usuaria' / 'dataset_usuaria_limpio.csv'
F35 = RAIZ / 'datos' / 'analitico' / 'dataset_fase35.csv'
PROHIBIDOS = ('verdad', 'bitacora', 'dataset_usuaria_sucio')

SEMILLA = 42
N_BOOT = 2000
ALFA = 0.05
CONFIG = 'P2_c12_km_k4'
TAMANOS_A = (150, 76, 132, 171)
TAMANOS_B1 = (150, 79, 126, 174)
CORTE_MARGEN = 0.10
CORTES_MARGEN = (0.05, 0.10, 0.15, 0.20)
CORTE_SEVERO = 16
SEVERIDAD = ((4, 'Sin síntomas o muy leves'), (8, 'Leve'), (15, 'Moderada'), (44, 'Severa'))
ORDEN_SEVERIDAD = [s for _, s in SEVERIDAD]
ITEMS = [f'pregunta_{i}' for i in range(1, 12)]
DIMENSIONES = {'mrs_somatico': ITEMS[0:4], 'mrs_psicologico': ITEMS[4:8], 'mrs_urogenital': ITEMS[8:11]}
NOMBRE_ITEM = {'pregunta_1': 'Bochornos, sudoración', 'pregunta_2': 'Molestias al corazón', 'pregunta_3': 'Molestias musculares y articulares', 'pregunta_4': 'Dificultades en el sueño',
               'pregunta_5': 'Ánimo depresivo', 'pregunta_6': 'Irritabilidad', 'pregunta_7': 'Ansiedad', 'pregunta_8': 'Cansancio físico y mental',
               'pregunta_9': 'Problemas sexuales', 'pregunta_10': 'Problemas con la orina', 'pregunta_11': 'Sequedad vaginal'}
RESULTADOS = {'mrs_total': 'MRS total', 'mrs_somatico': 'Dimensión somática', 'mrs_psicologico': 'Dimensión psicológica', 'mrs_urogenital': 'Dimensión urogenital'}
MAXIMO = {'mrs_total': 44, 'mrs_somatico': 16, 'mrs_psicologico': 16, 'mrs_urogenital': 12, 'mrs_total_sin9': 40, 'mrs_urogenital_sin9': 8}

TRIO = ('trabaja_actualmente', 'tiene_pareja', 'dias_ejercicio_semana')
BLOQUES = {
    'Las tres preguntas': list(TRIO),
    'Actividad física adicional': ['frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza'],
    'Sedentarismo': ['horas_sedentarismo'],
    'Cuidados': ['cantidad_personas_cuida'],
    'Alimentación': ['quien_prepara_comidas', 'carnes_semana', 'falta_tiempo_influye', 'frecuencia_comida_fuera', 'frutas_dia', 'golosinas_semana', 'jugos_gaseosas_dia', 'lacteos_dia', 'legumbres_semana', 'panes_dia', 'pescado_semana', 'platos_verduras_dia', 'vasos_agua_dia'],
    'Tabaco y alcohol': ['tabaco_frecuencia', 'alcohol_frecuencia'],
    'Otras generales': ['edad', 'operada_no_mas_hijos', 'usa_medicamentos_presion'],
    'Actividad sexual': ['tiene_actividad_sexual'],
    'Digestión': ['distension_abdominal', 'evacuacion_intestinal'],
}
EN_A = [v for vs in BLOQUES.values() for v in vs]
EXTERNAS = {'imc': ('cuantitativa', 'Externa: salud'), 'etapa_menopausica': ('nominal', 'Externa: etapa'), 'usa_medicamentos_diabetes': ('binaria', 'Externa: salud'),
            'prevision': ('nominal', 'Externa: acceso a salud'), 'lugar_trabajo_comprensivo': ('ordinal', 'Externa: módulo laboral'),
            'estres_entorno_laboral': ('ordinal', 'Externa: módulo laboral'), 'sobrecarga_fisica_emocional': ('ordinal', 'Externa: módulo de cuidados')}
CARACTERISTICAS = EN_A + list(EXTERNAS)
BLOQUE_DE = {**{v: b for b, vs in BLOQUES.items() for v in vs}, **{v: b for v, (_, b) in EXTERNAS.items()}}
GRUPO_ETAPA = {'indeterminada': 'indeterminada', 'indeterminada (histerectomía)': 'indeterminada'}
GRUPO_PREVISION = {'NINGUNA': 'otra o ninguna', 'FFAA': 'otra o ninguna', 'NS': 'otra o ninguna'}
ETIQUETA = {
    'trabaja_actualmente': 'Trabaja actualmente', 'tiene_pareja': 'Tiene pareja', 'dias_ejercicio_semana': 'Días de ejercicio a la semana',
    'frecuencia_aerobico': 'Frecuencia de ejercicio aeróbico', 'frecuencia_bajo_impacto': 'Frecuencia de ejercicio de bajo impacto', 'frecuencia_fuerza': 'Frecuencia de ejercicio de fuerza',
    'horas_sedentarismo': 'Horas sentada al día', 'cantidad_personas_cuida': 'Personas a su cuidado', 'quien_prepara_comidas': 'Quién prepara las comidas',
    'carnes_semana': 'Carnes a la semana', 'falta_tiempo_influye': 'La falta de tiempo influye en su alimentación', 'frecuencia_comida_fuera': 'Comidas fuera de casa',
    'frutas_dia': 'Frutas al día', 'golosinas_semana': 'Golosinas a la semana', 'jugos_gaseosas_dia': 'Jugos o gaseosas al día', 'lacteos_dia': 'Lácteos al día',
    'legumbres_semana': 'Legumbres a la semana', 'panes_dia': 'Panes al día', 'pescado_semana': 'Pescado a la semana', 'platos_verduras_dia': 'Platos de verduras al día',
    'vasos_agua_dia': 'Vasos de agua al día', 'tabaco_frecuencia': 'Frecuencia de tabaco', 'alcohol_frecuencia': 'Frecuencia de alcohol', 'edad': 'Edad',
    'operada_no_mas_hijos': 'Operada para no tener más hijos', 'usa_medicamentos_presion': 'Usa medicamentos para la presión', 'tiene_actividad_sexual': 'Tiene actividad sexual',
    'distension_abdominal': 'Distensión abdominal', 'evacuacion_intestinal': 'Evacuación intestinal', 'imc': 'IMC (solo observado)', 'etapa_menopausica': 'Etapa menopáusica',
    'usa_medicamentos_diabetes': 'Usa medicamentos para la diabetes', 'prevision': 'Previsión de salud', 'lugar_trabajo_comprensivo': 'Lugar de trabajo comprensivo',
    'estres_entorno_laboral': 'Estrés en el entorno laboral', 'sobrecarga_fisica_emocional': 'Sobrecarga física o emocional por cuidar',
}
POBLACION = {'lugar_trabajo_comprensivo': 'Solo quienes trabajan', 'estres_entorno_laboral': 'Solo quienes trabajan', 'sobrecarga_fisica_emocional': 'Solo quienes cuidan', 'imc': 'Solo IMC observado'}


# ---- auditoría
_LEIDOS, _ESCRITOS = set(), set()


def _gancho(evento, args):
    if evento == 'open' and isinstance(args[0], (str, Path)):
        modo, banderas = args[1], args[2] if len(args) > 2 else 0
        escribe = (isinstance(modo, str) and any(x in modo for x in 'wax+')) or (not isinstance(modo, str) and isinstance(banderas, int) and bool(banderas & (os.O_WRONLY | os.O_RDWR)))
        nombre = Path(str(args[0])).name.lower()
        if not escribe and any(p in nombre for p in PROHIBIDOS):
            raise PermissionError(f'Lectura prohibida: {args[0]}')
        (_ESCRITOS if escribe else _LEIDOS).add(str(args[0]))


_INSTALADO = False


def instalar_gancho():
    global _INSTALADO
    if not _INSTALADO:
        sys.addaudithook(_gancho)
        _INSTALADO = True


def registrar(etapa):
    """Agrega las lecturas y escrituras de este proceso a los registros de integridad. Detiene si hubo escrituras fuera de la carpeta."""
    d = BASE / 'integridad'
    d.mkdir(parents=True, exist_ok=True)
    raiz, base = RAIZ.resolve(), BASE.resolve()
    leidos, fuera = set(), set()
    for x in list(_LEIDOS):
        a = Path(x).resolve()
        if a.is_relative_to(raiz) and a.is_file() and a.suffix not in ('.py', '.pyc') and '.git' not in a.parts and not a.is_relative_to(base):
            leidos.add(a.relative_to(raiz).as_posix())
    for x in list(_ESCRITOS):
        a = Path(x).resolve()
        if not a.is_relative_to(base) and a.suffix != '.pyc' and 'Temp' not in a.parts:
            fuera.add(str(a))
    for nombre, col, valores in (('archivos_leidos.csv', 'archivo_leido', leidos), ('escrituras_fuera.csv', 'escritura_fuera', fuera)):
        ruta = d / nombre
        previos = set(pd.read_csv(ruta)[col].astype(str)) if ruta.exists() and ruta.stat().st_size > 20 else set()
        pd.DataFrame({col: sorted(previos | valores)}, dtype=str).to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')
    ruta = d / 'registro_ejecucion.csv'
    pd.DataFrame([{'etapa': etapa, 'archivos_leidos': len(leidos), 'escrituras_fuera': len(fuera)}]).to_csv(ruta, mode='a', header=not ruta.exists(), index=False, encoding='utf-8', lineterminator='\n')
    malos = [x for x in leidos if any(p in x.lower() for p in PROHIBIDOS)]
    if malos or fuera:
        raise SystemExit(f'Lectura prohibida o escritura fuera de la carpeta: {malos} {sorted(fuera)[:5]}')


# ---- utilidades
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def huella_sello():
    s = json.loads((BASE / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    if sha(BASE / 'protocolo' / s['archivo']) != s['sha256']:
        raise SystemExit('El protocolo de la Fase 37D no coincide con su sello.')
    return s


def a_csv(t, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')


def a_json(o, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(o, ensure_ascii=False, indent=1, default=float) + '\n', encoding='utf-8', newline='\n')


def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


# ---- carga
def identificadores():
    return pd.read_csv(F36 / 'matrices' / 'identificadores.csv', dtype=str)['participante_id'].tolist()


def definiciones_p2():
    esq = leer_json(F36 / 'artefactos' / 'P2' / 'esquema_variables.json')
    return {d['variable']: d for d in esq['variables']}


def tipo_de(v, defs=None):
    if v in EXTERNAS:
        return EXTERNAS[v][0]
    defs = defs or definiciones_p2()
    return defs[v]['tipo']


def celdas():
    return pd.read_csv(F36 / 'procedencia' / 'procedencia_celdas.csv', dtype=str, keep_default_na=False)


def codificar(c, ids, defs):
    """Códigos del instrumento por variable (como en la interpretabilidad de la Fase 37C) y estado de cada celda. «No aplica» es 0 estructural en ejercicio y
    cuidado, y faltante (NaN) en los módulos. El IMC imputado queda como NaN."""
    val = c.pivot(index='participante_id', columns='variable', values='valor_original').reindex(ids)
    est = c.pivot(index='participante_id', columns='variable', values='estado').reindex(ids)
    her = c.pivot(index='participante_id', columns='variable', values='pregunta_previa_imputada').reindex(ids)
    X = pd.DataFrame(index=pd.Index(ids, name='participante_id'))
    for v in EN_A:
        d = defs[v]
        s = val[v].astype(str)
        if d.get('madre'):
            s = s.where(s != '', d['madre']['estructural'])
        if d['tipo'] == 'cuantitativa':
            X[v] = pd.to_numeric(s, errors='coerce')
        elif d['tipo'] == 'nominal':
            X[v] = s.where(s != '', np.nan)
        else:
            X[v] = s.map({n: x['codigo'] for n, x in d['niveles'].items()}).astype(float)
    X['imc'] = pd.to_numeric(val['imc'], errors='coerce').where(est['imc'] == 'observada')
    for v in ('lugar_trabajo_comprensivo', 'estres_entorno_laboral', 'sobrecarga_fisica_emocional'):
        X[v] = pd.to_numeric(val[v].replace('', np.nan), errors='coerce')
    return X, est, her


def mrs(limpio, ids):
    """Recalcula dimensiones, total y severidad desde los ítems y exige que coincidan con lo guardado en la limpieza."""
    L = limpio.set_index('participante_id').reindex(ids)
    it = L[ITEMS].apply(pd.to_numeric, errors='raise')
    if it.isna().any().any() or not it.isin(range(5)).all().all():
        raise ValueError('Ítems del MRS faltantes o fuera de 0 a 4')
    M = it.copy()
    for d, cols in DIMENSIONES.items():
        M[d] = it[cols].sum(axis=1)
    M['mrs_total'] = it.sum(axis=1)
    M['mrs_total_sin9'] = M['mrs_total'] - it['pregunta_9']
    M['mrs_urogenital_sin9'] = M['mrs_urogenital'] - it['pregunta_9']
    M['severidad'] = M['mrs_total'].map(lambda t: next(n for m, n in SEVERIDAD if t <= m))
    M['severo_mrs'] = (M['mrs_total'] >= CORTE_SEVERO).astype(int)
    for col in list(DIMENSIONES) + ['mrs_total']:
        if not (pd.to_numeric(L[col]).to_numpy() == M[col].to_numpy()).all():
            raise ValueError(f'{col} no coincide con la limpieza')
    if not (L['mrs_severidad'].to_numpy() == M['severidad'].to_numpy()).all():
        raise ValueError('La severidad no coincide con la limpieza')
    return M


def etiquetas():
    ofi = pd.read_csv(C37 / 'seleccion' / 'artefactos_provisionales' / CONFIG / 'etiquetas.csv', dtype={'participante_id': str}).set_index('participante_id')['grupo']
    alt = pd.read_csv(CMP / 'asignaciones' / 'etiquetas_alternativas.csv', dtype={'participante_id': str}).set_index('participante_id')
    return ofi, alt


def regla_b1(trabaja, pareja, dias):
    """Regla de cuatro pasos del complemento, aplicada a los códigos: ejercicio de 3 días o más (código 3 o mayor) → 1; sin pareja → 0; sin trabajo → 2; si no → 3."""
    trabaja, pareja, dias = np.asarray(trabaja), np.asarray(pareja), np.asarray(dias)
    return np.where(dias >= 3, 1, np.where(pareja == 0, 0, np.where(trabaja == 0, 2, 3))).astype(int)


def b1_desde_mapa(trabaja, pareja, dias):
    mapa = np.array(leer_json(CMP / 'definiciones' / 'definicion_B1_B2.json')['B1']['mapa'])
    celda = (np.asarray(trabaja) * 10 + np.asarray(pareja) * 5 + (np.asarray(dias) - 1)).astype(int)
    return mapa[celda]


def cargar():
    """Tabla única de las 529, alineada por identificador. Comprueba alineación, etiquetas y MRS; si algo no coincide, se detiene."""
    ids = identificadores()
    if len(ids) != 529 or len(set(ids)) != 529:
        raise ValueError('Identificadores no son 529 únicos')
    defs = definiciones_p2()
    X, est, her = codificar(celdas(), ids, defs)
    limpio = pd.read_csv(LIMPIO, dtype=str, keep_default_na=False, na_values=[''])
    f35 = pd.read_csv(F35, dtype=str)
    if f35['participante_id'].tolist() != ids:
        raise ValueError('dataset_fase35 no está alineado con los identificadores de la Fase 36')
    M = mrs(limpio, ids)
    if not (pd.to_numeric(f35['severo_mrs']).to_numpy() == M['severo_mrs'].to_numpy()).all():
        raise ValueError('severo_mrs no coincide con la Fase 35')
    L = limpio.set_index('participante_id').reindex(ids)
    X['etapa_menopausica'] = L['etapa_menopausica']
    X['usa_medicamentos_diabetes'] = L['usa_medicamentos_diabetes'].map({'NO': 0, 'SI': 1}).astype(float)
    X['prevision'] = L['prevision']
    ofi, alt = etiquetas()
    E = pd.DataFrame(index=X.index)
    E['A'] = ofi.reindex(ids).to_numpy()
    alt = alt.reindex(ids)
    E['A_complemento'] = alt['A'].to_numpy()
    E['B1'] = alt['B1_doble_uso'].to_numpy()
    E['B1_cv'] = alt['B1_cv'].to_numpy()
    E['margen_A'] = alt['margen_A'].to_numpy()
    E['B1_regla'] = regla_b1(X['trabaja_actualmente'], X['tiene_pareja'], X['dias_ejercicio_semana'])
    return SimpleData(X=X, estado=est.reindex(columns=[c for c in est.columns]), heredada=her, M=M, E=E, defs=defs, ids=ids)


class SimpleData:
    def __init__(self, **k):
        self.__dict__.update(k)


def para_prueba(X, v):
    """Versión de la característica usada en las pruebas: etapa y previsión con sus categorías agrupadas según el protocolo."""
    s = X[v]
    if v == 'etapa_menopausica':
        return s.replace(GRUPO_ETAPA)
    if v == 'prevision':
        return s.replace(GRUPO_PREVISION)
    return s


def solo_observado(X, est, her):
    """S-OBS: celdas imputadas, deducidas o con pregunta madre imputada pasan a faltantes. Las externas sin marca por participante quedan igual."""
    Y = X.copy()
    for v in X.columns:
        if v in est.columns:
            m = est[v].isin(['imputada', 'deducida']).to_numpy() | (her[v].astype(str) == '1').to_numpy()
            Y.loc[m, v] = np.nan
    return Y


# ---- estadística
def banda(e, medida):
    a = abs(e) if pd.notna(e) else np.nan
    if np.isnan(a):
        return 'sin dato'
    cortes = (0.10, 0.30, 0.50) if medida in ('rho', 'r_rb', 'V') else (0.01, 0.06, 0.14)
    return 'despreciable' if a < cortes[0] else 'pequeña' if a < cortes[1] else 'moderada' if a < cortes[2] else 'grande'


def bh(p):
    """Benjamini-Hochberg. Devuelve q en el orden original; NaN se ignora."""
    p = np.asarray(p, float)
    q = np.full_like(p, np.nan)
    m = ~np.isnan(p)
    pv = p[m]
    n = len(pv)
    if n == 0:
        return q
    o = np.argsort(pv)
    r = pv[o] * n / np.arange(1, n + 1)
    r = np.minimum.accumulate(r[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.minimum(r, 1)
    q[m] = out
    return q


def holm(p):
    p = np.asarray(p, float)
    n = len(p)
    o = np.argsort(p)
    r = np.maximum.accumulate((n - np.arange(n)) * p[o])
    out = np.empty(n)
    out[o] = np.minimum(r, 1)
    return out


def r_biserial(y, g):
    """r biserial de rangos: 2·AUC − 1, positivo si el grupo 1 tiene valores mayores."""
    y, g = np.asarray(y, float), np.asarray(g, float)
    m = ~np.isnan(y) & ~np.isnan(g)
    y, g = y[m], g[m]
    n1, n0 = int((g == 1).sum()), int((g == 0).sum())
    if n1 == 0 or n0 == 0:
        return np.nan
    rk = stats.rankdata(y)
    u1 = rk[g == 1].sum() - n1 * (n1 + 1) / 2
    return 2 * u1 / (n1 * n0) - 1


def epsilon2(h, n, k):
    return (h - k + 1) / (n - k) if n > k else np.nan


def eta2(x, l):
    x, l = np.asarray(x, float), np.asarray(l)
    m = ~np.isnan(x)
    x, l = x[m], l[m]
    tot = ((x - x.mean()) ** 2).sum()
    if tot == 0:
        return 0.0
    return float(sum((l == g).sum() * (x[l == g].mean() - x.mean()) ** 2 for g in np.unique(l)) / tot)


def tabla_chi(x, l):
    s = pd.DataFrame({'x': x, 'l': l}).dropna()
    t = pd.crosstab(s['x'], s['l'])
    return t


def chi2(t):
    """χ² sin corrección; si es 2 × 2 y más del 20 % de las esperadas es menor que 5, Fisher exacta. Devuelve p, V, V², prueba y advertencia."""
    t = np.asarray(t, float)
    if t.shape[0] < 2 or t.shape[1] < 2:
        return np.nan, np.nan, np.nan, 'no aplicable', ''
    est, p, _, esp = stats.chi2_contingency(t, correction=False)
    n = t.sum()
    v2 = est / (n * (min(t.shape) - 1))
    bajas = (esp < 5).mean()
    prueba, aviso = 'χ²', ''
    if bajas > 0.20:
        if t.shape == (2, 2):
            p = stats.fisher_exact(t)[1]
            prueba = 'Fisher exacta'
        else:
            aviso = f'{bajas:.0%} de esperadas < 5'
    return float(p), float(np.sqrt(v2)), float(v2), prueba, aviso


def asociacion(x, y, tipo_x, tipo_y='continua'):
    """Prueba fijada en el protocolo según el tipo de característica y de resultado. y continua: MRS total, dimensión o ítem. y binaria: severo_mrs."""
    s = pd.DataFrame({'x': np.asarray(x, dtype=object), 'y': np.asarray(y, dtype=object)}).dropna()
    n = len(s)
    if n < 3:
        return dict(prueba='sin datos', medida={'cuantitativa': 'rho', 'ordinal': 'rho', 'binaria': 'r_rb'}.get(tipo_x, 'epsilon2') if tipo_y == 'continua' else 'r_rb' if tipo_x in ('cuantitativa', 'ordinal') else 'V',
                    efecto=np.nan, p=np.nan, n=n, aviso='menos de 3 participantes aplicables')
    if tipo_y == 'continua':
        yy = s['y'].astype(float).to_numpy()
        if tipo_x in ('cuantitativa', 'ordinal'):
            xx = s['x'].astype(float).to_numpy()
            if np.ptp(xx) == 0 or np.ptp(yy) == 0:
                return dict(prueba='Spearman', medida='rho', efecto=np.nan, p=np.nan, n=n, aviso='sin variación')
            r, p = stats.spearmanr(xx, yy)
            return dict(prueba='Spearman', medida='rho', efecto=float(r), p=float(p), n=n, aviso='')
        if tipo_x == 'binaria':
            g = s['x'].astype(float).to_numpy()
            a, b = yy[g == 1], yy[g == 0]
            if len(a) == 0 or len(b) == 0:
                return dict(prueba='Mann-Whitney', medida='r_rb', efecto=np.nan, p=np.nan, n=n, aviso='un solo nivel')
            p = stats.mannwhitneyu(a, b, alternative='two-sided').pvalue
            return dict(prueba='Mann-Whitney', medida='r_rb', efecto=float(r_biserial(yy, g)), p=float(p), n=n, aviso='')
        grupos = [yy[(s['x'] == c).to_numpy()] for c in sorted(s['x'].unique())]
        if len(grupos) < 2:
            return dict(prueba='Kruskal-Wallis', medida='epsilon2', efecto=np.nan, p=np.nan, n=n, aviso='un solo nivel')
        h, p = stats.kruskal(*grupos)
        return dict(prueba='Kruskal-Wallis', medida='epsilon2', efecto=float(epsilon2(h, n, len(grupos))), p=float(p), n=n, aviso='')
    yb = s['y'].astype(int).to_numpy()
    if tipo_x in ('cuantitativa', 'ordinal'):
        xx = s['x'].astype(float).to_numpy()
        p = stats.mannwhitneyu(xx[yb == 1], xx[yb == 0], alternative='two-sided').pvalue
        return dict(prueba='Mann-Whitney', medida='r_rb', efecto=float(r_biserial(xx, yb)), p=float(p), n=n, aviso='')
    p, v, _, prueba, aviso = chi2(pd.crosstab(s['x'], s['y']))
    return dict(prueba=prueba, medida='V', efecto=v, p=p, n=n, aviso=aviso)


def efecto_rapido(x, y, tipo_x):
    """Solo el efecto, para el bootstrap. Mismas definiciones que asociacion() con resultado continuo."""
    if tipo_x in ('cuantitativa', 'ordinal'):
        if np.ptp(x) == 0 or np.ptp(y) == 0:
            return np.nan
        return stats.spearmanr(x, y)[0]
    if tipo_x == 'binaria':
        return r_biserial(y, x)
    cats = np.unique(x)
    grupos = [y[x == c] for c in cats]
    grupos = [g for g in grupos if len(g)]
    if len(grupos) < 2 or np.ptp(y) == 0:
        return np.nan
    h = stats.kruskal(*grupos)[0]
    return epsilon2(h, len(y), len(grupos))


def bootstrap(x, y, tipo_x, semilla_extra=0, b=N_BOOT):
    """Intervalo percentil del 95 % del efecto. Remuestrea participantes con la semilla 42 y un índice fijo por prueba."""
    s = pd.DataFrame({'x': np.asarray(x, dtype=object), 'y': np.asarray(y, dtype=object)}).dropna()
    xx = s['x'].to_numpy() if tipo_x == 'nominal' else s['x'].astype(float).to_numpy()
    yy = s['y'].astype(float).to_numpy()
    rng = np.random.default_rng(np.random.SeedSequence([SEMILLA, semilla_extra]))
    n = len(yy)
    v = np.empty(b)
    for i in range(b):
        j = rng.integers(0, n, n)
        v[i] = efecto_rapido(xx[j], yy[j], tipo_x)
    v = v[~np.isnan(v)]
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else (np.nan, np.nan)


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    c = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / (1 + z ** 2 / n)
    m = (p + z ** 2 / (2 * n)) / (1 + z ** 2 / n)
    return float(m - c), float(m + c)


def ic_media_mediana(y, semilla_extra=0, b=N_BOOT):
    y = np.asarray(y, float)
    rng = np.random.default_rng(np.random.SeedSequence([SEMILLA, 7000 + semilla_extra]))
    j = rng.integers(0, len(y), (b, len(y)))
    me = y[j].mean(axis=1)
    md = np.median(y[j], axis=1)
    return (float(np.percentile(me, 2.5)), float(np.percentile(me, 97.5))), (float(np.percentile(md, 2.5)), float(np.percentile(md, 97.5)))


def segmento_frente_a(y, l, tipo_y):
    """Una segmentación frente a un resultado: Kruskal-Wallis con ε² (continuo) o χ² con V (severidad, severo)."""
    l = np.asarray(l)
    if tipo_y == 'continua':
        y = np.asarray(y, float)
        grupos = [y[l == g] for g in np.unique(l)]
        h, p = stats.kruskal(*grupos)
        return dict(prueba='Kruskal-Wallis', medida='epsilon2', efecto=float(epsilon2(h, len(y), len(grupos))), p=float(p), n=len(y), eta2=eta2(y, l), aviso='')
    p, v, v2, prueba, aviso = chi2(pd.crosstab(np.asarray(y), l))
    return dict(prueba=prueba, medida='V', efecto=v, p=p, n=len(l), eta2=v2, aviso=aviso)


def boot_segmento(y, l, tipo_y, semilla_extra=0, b=N_BOOT):
    y, l = np.asarray(y), np.asarray(l)
    rng = np.random.default_rng(np.random.SeedSequence([SEMILLA, 9000 + semilla_extra]))
    n = len(y)
    v = np.empty(b)
    for i in range(b):
        j = rng.integers(0, n, n)
        if tipo_y == 'continua':
            yy, ll = y[j].astype(float), l[j]
            grupos = [yy[ll == g] for g in np.unique(ll)]
            v[i] = epsilon2(stats.kruskal(*grupos)[0], n, len(grupos)) if np.ptp(yy) > 0 else np.nan
        else:
            v[i] = chi2(pd.crosstab(y[j], l[j]))[1]
    v = v[~np.isnan(v)]
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def ari_y_coincidencia(a, b):
    from scipy.optimize import linear_sum_assignment
    from sklearn.metrics import adjusted_rand_score
    a, b = np.asarray(a), np.asarray(b)
    t = pd.crosstab(a, b).to_numpy()
    f, c = linear_sum_assignment(-t)
    return float(adjusted_rand_score(a, b)), float(t[f, c].sum() / t.sum())
