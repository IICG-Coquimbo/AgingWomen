"""
Fase 39R: núcleo correctivo. Reutiliza sin modificar las funciones históricas de las Fases 38 y 39 (agrupaciones, algoritmos, búsqueda, heterogeneidad, estratos) y define aquí solo
lo que cambia: el origen de las transacciones (29 variables y 90 ítems de la 38R), las barreras y la carpeta de escritura. Nada escribe en las carpetas históricas ni en la 38R.

Modo de humo (F39R_HUMO_DIR): comprueba que el código corre, con la severidad permutada, pocas permutaciones y salida en una carpeta temporal. No produce resultados del análisis.
"""
import os
import sys

sys.dont_write_bytecode = True
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import json  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
BASE_REAL = AQUI.parent
RAIZ = BASE_REAL.parents[2]
ANALISIS = RAIZ / 'analisis'
D38 = ANALISIS / 'fase38' / '38_reglas_asociacion_generales'
D38R = ANALISIS / 'fase38' / '38R_reglas_asociacion_corregidas'
D39 = ANALISIS / 'fase39' / '39_asociaciones_condicionadas'
for _p in (D38 / 'scripts', D38R / 'scripts', D39 / 'scripts', AQUI):
    sys.path.insert(0, str(_p))
import barreras_38r as B38  # noqa: E402
import barreras_39r as BAR  # noqa: E402
import nucleo_38r as R38  # noqa: E402
import nucleo_39 as H39  # noqa: E402

N38 = H39.N38
N37 = H39.N37
G = H39.G
EV38 = H39.EV38
HUMO_DIR = os.environ.get('F39R_HUMO_DIR')
HUMO = bool(HUMO_DIR)
BASE = Path(HUMO_DIR) if HUMO else BASE_REAL
CONSECUENTES = H39.CONSECUENTES
PROHIBIDOS = H39.PROHIBIDOS
SEMILLA = H39.SEMILLA
N_PERM = 12 if HUMO else H39.N_PERM
N_SUB = 8 if HUMO else H39.N_SUB
if not HUMO and (N_PERM != 1000 or N_SUB != 200 or SEMILLA != 42):
    raise SystemExit('Los parámetros históricos no coinciden con el protocolo.')
DIF_HET = H39.DIF_HET
COMPOSICION = H39.COMPOSICION
DIMENSIONES = H39.DIMENSIONES
ESTRATOS = H39.ESTRATOS
NUM_ESTRATO = H39.NUM_ESTRATO
NUM_DIM = H39.NUM_DIM
NOMBRE = H39.NOMBRE
UMBRALES = H39.UMBRALES
SENSIBILIDADES = H39.SENSIBILIDADES
NUCLEO_SENS = H39.NUCLEO_SENS
PRINCIPAL = R38.PRINCIPAL
RETIRADAS = ('prevision', 'usa_medicamentos_diabetes')
umbrales = H39.umbrales
dims_de = H39.dims_de
excluidas = H39.excluidas
variable_de_item = N38.variable_de_item
sha = H39.sha
a_csv = H39.a_csv
a_json = H39.a_json
leer_json = H39.leer_json
instalar_gancho = H39.instalar_gancho
MATRIZ_38R = D38R / 'preparacion' / 'matriz_transaccional_principal.csv'


def cargar():
    """Decisiones de las Fases 35 y 36, lista autorizada, carga de la 37D y máscaras vetadas (vía 38R). Etiquetas A y B1 históricas, sin reajustar."""
    pq = R38.cargar()
    d = pq.d
    if (d.E['B1'].to_numpy() != d.E['B1_regla'].to_numpy()).any():
        raise SystemExit('B1 histórica no coincide con la regla de cuatro pasos')
    if HUMO:
        d.M = d.M.copy()
        d.M['severo_mrs'] = np.random.default_rng([987, 39]).permutation(d.M['severo_mrs'].to_numpy())
    return pq


def mascaras(pq):
    return H39.mascaras(pq.d)


def base_items(pq, sens='principal'):
    """Matriz de las 529 de cada configuración, construida ya sin las variables excluidas. Sustituye a H39.base_items, que usa N38.PRINCIPAL y N38.construir."""
    d = pq.d
    nombre = {'S1': 'S1', 'S2a': 'S2a', 'S5': 'S5', 'S6': 'S6', 'S7a': 'S7a', 'S7b': 'S7b'}.get(sens, 'principal')
    B38.verificar_lista_principal(PRINCIPAL, pq.dec)
    if nombre in BAR.MODULOS:
        # Igual que la Fase 39: las 529 con el módulo agregado; la población se restringe al construir el estrato.
        variables = list(PRINCIPAL) + BAR.MODULOS[nombre]
        esq = N38.esquema(d.X[variables], d.defs, 'principal')
        T, traza = N38.matriz_items(esq, len(d.X))
        T = T.loc[:, T.sum() > 0]
    else:
        c = R38.construir(pq, nombre)
        T, traza = c.T, c.traza
    BAR.verificar_base(T, sens, pq, variable_de_item)
    return T, traza


def construir(pq, grupo, estrato, sens='principal', T529=None, masc=None):
    """Transacciones del estrato con la función histórica, a partir de la matriz corregida. Barreras antes de devolverlas."""
    if T529 is None:
        T529, _ = base_items(pq, sens)
    masc = masc or mascaras(pq)
    c = H39.construir(pq.d, grupo, estrato, sens, T529=T529, masc=masc)
    BAR.verificar_estrato(c, sens, pq.dec, variable_de_item, umbrales, comprobar_severas=not HUMO)
    return c


def huella_sello():
    if HUMO:
        return {'sha256': 'humo', 'sellado': datetime.now().isoformat(timespec='seconds')}
    s = json.loads((BASE_REAL / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    if sha(BASE_REAL / 'protocolo' / s['archivo']) != s['sha256']:
        raise SystemExit('El protocolo de la Fase 39R no coincide con su sello.')
    for nombre, h in s['codigo'].items():
        if sha(AQUI / nombre) != h:
            raise SystemExit(f'El código cambió después del sello: {nombre}')
    for ruta, h in s['fuentes'].items():
        if sha(RAIZ / ruta) != h:
            raise SystemExit(f'Una fuente cambió después del sello: {ruta}')
    return s


def registrar(etapa):
    """Archivos leídos y control de escrituras: nada fuera de la carpeta de la 39R."""
    d = BASE / 'integridad'
    d.mkdir(parents=True, exist_ok=True)
    raiz, base = RAIZ.resolve(), BASE.resolve()
    leidos, fuera = set(), set()
    for x in list(H39._LEIDOS) + list(N38._LEIDOS):
        a = Path(x).resolve()
        if a.is_relative_to(raiz) and a.is_file() and a.suffix not in ('.py', '.pyc') and '.git' not in a.parts and not a.is_relative_to(base):
            leidos.add(a.relative_to(raiz).as_posix())
    for x in list(H39._ESCRITOS) + list(N38._ESCRITOS):
        a = Path(x).resolve()
        if not a.is_relative_to(base) and a.suffix != '.pyc' and 'Temp' not in a.parts:
            fuera.add(str(a))
    ruta = d / 'archivos_leidos.csv'
    previos = set(pd.read_csv(ruta)['archivo_leido'].astype(str)) if ruta.exists() else set()
    pd.DataFrame({'archivo_leido': sorted(previos | leidos)}, dtype=str).to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')
    ruta = d / 'registro_ejecucion.csv'
    pd.DataFrame([{'momento': datetime.now().isoformat(timespec='seconds'), 'etapa': etapa, 'archivos_leidos': len(leidos), 'escrituras_fuera': len(fuera)}]).to_csv(
        ruta, mode='a', header=not ruta.exists(), index=False, encoding='utf-8', lineterminator='\n')
    malos = [x for x in leidos if any(p in x.lower() for p in PROHIBIDOS)]
    if malos or fuera:
        raise SystemExit(f'Lectura prohibida o escritura fuera de la carpeta de la 39R: {malos} {sorted(fuera)[:5]}')
