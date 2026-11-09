"""
Fase 39: núcleo compartido. Importa la Fase 38 (y, a través de ella, la 37D) solo para leer, sin escribir en sus carpetas. Estratos, umbrales por tamaño,
construcción de transacciones condicionadas, auditoría propia.
"""
import os
import sys

sys.dont_write_bytecode = True
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
ANALISIS = BASE.parents[1]
RAIZ = ANALISIS.parent
D38 = ANALISIS / 'fase38' / '38_reglas_asociacion_generales'
sys.path.insert(0, str(D38 / 'scripts'))
import algoritmos_38 as G  # noqa: E402
import evaluacion_38 as EV38  # noqa: E402
import nucleo_38 as N38  # noqa: E402

N37 = N38.N37
PROHIBIDOS = N38.PROHIBIDOS
CONSECUENTES = N38.CONSECUENTES
SEMILLA = 42
N_PERM = 1000
N_SUB = 200
FRAC_SUB = 0.8
DIF_MARCADA = 0.10
DIF_HET = 0.10
MEJORA_MIN = 0.05
ESTABLE_REAP = 0.70
ESTABLE_DIR = 0.95
ALFA = 0.05
COMPOSICION = 0.20

# ---- estratos (sección 1 del protocolo)
DIMENSIONES = {
    'trabajo': {'variable': 'trabaja_actualmente', 'estratos': [('trabaja', lambda x: x == 1), ('no_trabaja', lambda x: x == 0)]},
    'pareja': {'variable': 'tiene_pareja', 'estratos': [('con_pareja', lambda x: x == 1), ('sin_pareja', lambda x: x == 0)]},
    'ejercicio': {'variable': 'dias_ejercicio_semana', 'estratos': [('0_dias', lambda x: x == 1), ('1-2_dias', lambda x: x == 2), ('3_o_mas_dias', lambda x: x >= 3)]},
    'cuidado': {'variable': 'cantidad_personas_cuida', 'estratos': [('cuida', lambda x: x > 0), ('no_cuida', lambda x: x == 0)]},
}
ESTRATOS = [(dim, e) for dim, v in DIMENSIONES.items() for e, _ in v['estratos']]
NUM_ESTRATO = {k: i for i, k in enumerate(ESTRATOS)}
NUM_DIM = {d: i for i, d in enumerate(DIMENSIONES)}
NOMBRE = {'trabaja': 'Trabaja', 'no_trabaja': 'No trabaja', 'con_pareja': 'Tiene pareja', 'sin_pareja': 'No tiene pareja', '0_dias': '0 días de ejercicio',
          '1-2_dias': '1-2 días de ejercicio', '3_o_mas_dias': '3 días o más de ejercicio', 'cuida': 'Cuida a una o más personas', 'no_cuida': 'No cuida',
          'trabajo': 'Trabajo', 'pareja': 'Pareja', 'ejercicio': 'Ejercicio', 'cuidado': 'Cuidado'}
TRIO = ['trabaja_actualmente', 'tiene_pareja', 'dias_ejercicio_semana']

# ---- umbrales (sección 6) y sensibilidades (sección 11)
UMBRALES = {'principal': (0.10, 20, 0.05, 10, 20), 'S3-bajo': (0.075, 15, 0.0375, 8, 15), 'S3-alto': (0.15, 30, 0.075, 15, 30)}
SENSIBILIDADES = {
    'S1': 'Sin valores imputados ni deducidos (sin diabetes ni previsión)',
    'S2a': 'Categorías originales sin agrupar',
    'S3-bajo': 'Umbrales bajos: n_A ≥ max(15, 7,5 %), n_AC ≥ max(8, 3,75 %), comparabilidad ≥ 15',
    'S3-alto': 'Umbrales altos: n_A ≥ max(30, 15 %), n_AC ≥ max(15, 7,5 %), comparabilidad ≥ 30',
    'S4-1': 'Antecedentes de una condición',
    'S4-2': 'Antecedentes de hasta dos condiciones',
    'S5': 'Sin frecuencias de ejercicio aeróbico, bajo impacto y fuerza',
    'S6': 'Sin variables próximas a síntomas',
    'S7a': 'Quienes trabajan, con el módulo laboral',
    'S7b': 'Quienes cuidan, con la sobrecarga',
    'S9': 'Ejercicio sin el estrato de 3 días o más',
}
NUCLEO_SENS = ['S1', 'S2a', 'S3-bajo', 'S3-alto', 'S6']


def largo_por_tamano(n):
    return 3 if n >= 250 else 2 if n >= 120 else 1 if n >= 60 else 0


def umbrales(n, sens='principal', largo_max=3):
    fa, ma, fc, mc, comp = UMBRALES.get(sens, UMBRALES['principal'])
    a = max(ma, math.ceil(round(fa * n, 9)))
    b = max(mc, math.ceil(round(fc * n, 9)))
    largo = min(largo_por_tamano(n), largo_max, {'S4-1': 1, 'S4-2': 2}.get(sens, 3))
    return a, b, largo, comp


# ---- auditoría (propia, escribe en la carpeta de la Fase 39)
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
    pd.DataFrame([{'momento': datetime.now().isoformat(timespec='seconds'), 'etapa': etapa, 'archivos_leidos': len(leidos), 'escrituras_fuera': len(fuera)}]).to_csv(
        ruta, mode='a', header=not ruta.exists(), index=False, encoding='utf-8', lineterminator='\n')
    malos = [x for x in leidos if any(p in x.lower() for p in PROHIBIDOS)]
    if malos or fuera:
        raise SystemExit(f'Lectura prohibida o escritura fuera de la carpeta: {malos} {sorted(fuera)[:5]}')


# ---- utilidades
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def huella_sello():
    s = json.loads((BASE / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    if sha(BASE / 'protocolo' / s['archivo']) != s['sha256']:
        raise SystemExit('El protocolo de la Fase 39 no coincide con su sello.')
    return s


def a_csv(t, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')


def a_json(o, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(o, ensure_ascii=False, indent=1, default=lambda x: x.item() if hasattr(x, 'item') else str(x)) + '\n', encoding='utf-8', newline='\n')


def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


# ---- carga y estratos
def cargar():
    d = N38.cargar()
    if (d.E['B1'].to_numpy() != d.E['B1_regla'].to_numpy()).any():
        raise SystemExit('B1 histórica no coincide con la regla de cuatro pasos')
    return d


def mascaras(d):
    """Pertenencia de las 529 a cada estrato (sección 1), más A y B1."""
    out = {}
    for dim, v in DIMENSIONES.items():
        x = d.X[v['variable']].to_numpy()
        for e, f in v['estratos']:
            out[(dim, e)] = f(x)
    for g in ('A', 'B1'):
        lab = d.E[g].to_numpy().astype(int)
        for k in sorted(set(lab)):
            out[(g, f'{g}_{k}')] = lab == k
    return out


def dims_de(grupo):
    """Estratos de una dimensión (o de A/B1) en orden."""
    if grupo in DIMENSIONES:
        return [e for e, _ in DIMENSIONES[grupo]['estratos']]
    return [f'{grupo}_{k}' for k in range(4)]


def excluidas(grupo):
    return TRIO if grupo in ('A', 'B1') else [DIMENSIONES[grupo]['variable']]


def base_items(d, sens='principal'):
    """Matriz de ítems de las 529 con la preparación de la Fase 38 (agrupaciones fijadas con las 529, sin el MRS)."""
    nombre = {'S1': 'S1', 'S2a': 'S2a', 'S5': 'S5', 'S6': 'S6', 'S7a': 'S7a', 'S7b': 'S7b'}.get(sens, 'principal')
    if nombre in ('S7a', 'S7b'):
        # todas las 529 con los módulos agregados; la población se restringe después
        X = d.X
        variables = list(N38.PRINCIPAL) + (['lugar_trabajo_comprensivo', 'estres_entorno_laboral'] if nombre == 'S7a' else ['sobrecarga_fisica_emocional'])
        esq = N38.esquema(X[variables], d.defs, 'principal')
        T, traza = N38.matriz_items(esq, len(X))
        T = T.loc[:, T.sum() > 0]
        return T, traza
    c = N38.construir(d, nombre)
    return c.T, c.traza


class Estrato:
    def __init__(self, **k):
        self.__dict__.update(k)


def construir(d, grupo, estrato, sens='principal', T529=None, masc=None):
    """Transacciones del estrato: ítems de la Fase 38 menos la variable del estrato, sin ítems constantes en el estrato."""
    if T529 is None:
        T529, _ = base_items(d, sens)
    masc = masc or mascaras(d)
    m = masc[(grupo, estrato)]
    excl = set(excluidas(grupo))
    cols = [c for c in T529.columns if N38.variable_de_item(c) not in excl]
    T = T529.loc[m, cols].reset_index(drop=True)
    n = int(m.sum())
    tam = T.sum(axis=0)
    constantes = tam.index[(tam == 0) | (tam == n)].tolist()
    T = T.drop(columns=constantes)
    y = d.M['severo_mrs'].to_numpy().astype(int)[m]
    a, b, largo, comp = umbrales(n, sens)
    return Estrato(nombre=f'{grupo}:{estrato}', grupo=grupo, estrato=estrato, sens=sens, T=T, y=y, n=n, n_si=int(y.sum()), ids=np.array(d.ids)[m],
                   min_ant=a, min_conj=b, largo=largo, comp=comp, constantes=constantes, excluidas=sorted(excl), mascara=m, descripcion=f'{grupo}:{estrato}:{sens}')


def legible(item):
    return N38.legible(item)


def legible_regla(a):
    return N38.legible_regla(a)
