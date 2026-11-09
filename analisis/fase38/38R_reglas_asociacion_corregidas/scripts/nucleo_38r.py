"""
Fase 38R: núcleo. Reutiliza sin modificar las funciones históricas de la Fase 38 (agrupaciones, Apriori, FP-Growth, evaluación) y define aquí solo lo que cambia:
la lista de variables, las poblaciones de S7 y las barreras. Las escrituras van siempre a la carpeta de la 38R.
"""
import os
import sys

sys.dont_write_bytecode = True
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import json  # noqa: E402
import math  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
RAIZ = BASE.parents[2]
ANALISIS = RAIZ / 'analisis'
D38 = ANALISIS / 'fase38' / '38_reglas_asociacion_generales'
sys.path.insert(0, str(D38 / 'scripts'))
sys.path.insert(0, str(AQUI))
import algoritmos_38 as G  # noqa: E402,F401
import barreras_38r as B  # noqa: E402
import evaluacion_38 as EV  # noqa: E402,F401
import nucleo_38 as H  # noqa: E402

N37 = H.N37
CONSECUENTES = H.CONSECUENTES
SEMILLA = H.SEMILLA
variable_de_item = H.variable_de_item

# Orden histórico de la Fase 38 sin las dos variables indebidas.
PRINCIPAL = ['trabaja_actualmente', 'tiene_pareja', 'cantidad_personas_cuida',
             'dias_ejercicio_semana', 'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'horas_sedentarismo',
             'quien_prepara_comidas', 'carnes_semana', 'falta_tiempo_influye', 'frecuencia_comida_fuera', 'frutas_dia', 'golosinas_semana', 'jugos_gaseosas_dia',
             'lacteos_dia', 'legumbres_semana', 'panes_dia', 'pescado_semana', 'platos_verduras_dia', 'vasos_agua_dia',
             'tabaco_frecuencia', 'alcohol_frecuencia',
             'edad', 'operada_no_mas_hijos', 'usa_medicamentos_presion',
             'tiene_actividad_sexual', 'distension_abdominal', 'evacuacion_intestinal']
FRECUENCIAS_EJERCICIO = list(H.FRECUENCIAS_EJERCICIO)
PROXIMAS = list(H.PROXIMAS)

_P = {'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3}
CONFIGS = {
    'principal': {'descripcion': 'Análisis principal', **_P},
    'S1': {'descripcion': 'Sin valores imputados', **_P},
    'S2a': {'descripcion': 'Categorías originales sin agrupar', **_P},
    'S2b': {'descripcion': 'Agrupación gruesa', **_P},
    'S3-bajo': {'descripcion': 'Umbral 5 % (antecedente ≥ 27, conjunto ≥ 14)', 'min_ant': 27, 'min_conj': 14, 'largo': 3},
    'S3-alto': {'descripcion': 'Umbral 15 % (antecedente ≥ 80, conjunto ≥ 40)', 'min_ant': 80, 'min_conj': 40, 'largo': 3},
    'S4-1': {'descripcion': 'Antecedentes de una condición', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 1},
    'S4-2': {'descripcion': 'Antecedentes de hasta dos condiciones', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 2},
    'S5': {'descripcion': 'Sin frecuencias de ejercicio aeróbico, bajo impacto y fuerza', **_P},
    'S6': {'descripcion': 'Sin variables próximas a síntomas', **_P},
    'S7a': {'descripcion': 'Trabajadoras con información laboral (287), con módulo laboral', **_P},
    'S7a-309': {'descripcion': 'Población laboral ampliada (309), con módulo laboral', **_P},
    'S7b': {'descripcion': 'Cuidadoras con sobrecarga observada (239), con sobrecarga', **_P},
    'S7b-251': {'descripcion': 'Población de cuidadoras ampliada (251, 12 imputadas), con sobrecarga', **_P},
    'S8a': {'descripcion': 'Con IMC observado, sin IMC', **_P},
    'S8b': {'descripcion': 'Con IMC observado, con IMC', **_P},
}
# Correspondencia con la configuración histórica. None: sin equivalente (cambia la población).
HISTORICA = {'principal': 'principal', 'S1': 'S1', 'S2a': 'S2a', 'S2b': 'S2b', 'S3-bajo': 'S3-bajo', 'S3-alto': 'S3-alto', 'S4-1': 'S4-1', 'S4-2': 'S4-2', 'S5': 'S5', 'S6': 'S6',
             'S7a': None, 'S7a-309': 'S7a', 'S7b': None, 'S7b-251': 'S7b', 'S8a': 'S8a', 'S8b': 'S8b'}


def umbrales(nombre, n):
    c = CONFIGS[nombre]
    a = c['min_ant'] if isinstance(c['min_ant'], int) else math.ceil(round(c['min_ant'] * n, 9))
    b = c['min_conj'] if isinstance(c['min_conj'], int) else math.ceil(round(c['min_conj'] * n, 9))
    return a, b, c['largo']


class Paquete:
    def __init__(self, **k):
        self.__dict__.update(k)


def cargar():
    """Decisiones de la Fase 35 y 36, lista autorizada, carga verificada de la 37D y máscaras vetadas. Cualquier incumplimiento detiene el proceso."""
    dec = B.decisiones()
    B.verificar_lista_principal(PRINCIPAL, dec)
    if set(H.PRINCIPAL) - set(PRINCIPAL) != {'prevision', 'usa_medicamentos_diabetes'} or set(PRINCIPAL) - set(H.PRINCIPAL):
        raise B.Incumplimiento('La lista corregida no es la histórica menos las dos variables indebidas')
    d = H.cargar()
    return Paquete(d=d, dec=dec, vetadas=B.mascaras_vetadas(d))


def construir(pq, nombre):
    """Transacciones de una configuración, con la misma lógica de la Fase 38 (agrupaciones fijadas con las 529, sin el MRS; luego se restringe la población)."""
    d, dec = pq.d, pq.dec
    B.verificar_lista_principal(PRINCIPAL, dec)
    X = d.X.copy()
    ids = np.array(d.ids)
    y = d.M['severo_mrs'].to_numpy().astype(int)
    pob = np.ones(len(X), bool)
    variables = list(PRINCIPAL)
    modo = {'S2a': 'original', 'S2b': 'gruesa'}.get(nombre, 'principal')
    if nombre == 'S1':
        X = N37.solo_observado(X, d.estado, d.heredada)
    if nombre == 'S5':
        variables = [v for v in variables if v not in FRECUENCIAS_EJERCICIO]
    if nombre == 'S6':
        variables = [v for v in variables if v not in PROXIMAS]
    if nombre in ('S7a', 'S7a-309'):
        pob = (X['trabaja_actualmente'] == 1).to_numpy()
        if nombre == 'S7a':
            pob &= X[['lugar_trabajo_comprensivo', 'estres_entorno_laboral']].notna().all(axis=1).to_numpy()
        variables = [v for v in variables if v != 'trabaja_actualmente'] + ['lugar_trabajo_comprensivo', 'estres_entorno_laboral']
    if nombre in ('S7b', 'S7b-251'):
        pob = (X['cantidad_personas_cuida'] > 0).to_numpy()
        if nombre == 'S7b':
            pob &= d.estado['sobrecarga_fisica_emocional'].eq('observada').to_numpy()
        variables = variables + ['sobrecarga_fisica_emocional']
    if nombre in ('S8a', 'S8b'):
        pob = X['imc'].notna().to_numpy()
        if nombre == 'S8b':
            variables = variables + ['imc']
    autorizadas = B.permitidas(nombre, dec)
    if set(variables) != autorizadas:
        raise B.Incumplimiento(f'{nombre}: variables distintas de las autorizadas: {sorted(set(variables) ^ autorizadas)}')
    esq = H.esquema(X[variables], d.defs, modo)
    T, traza = H.matriz_items(esq, len(X))
    B.verificar_items(T.columns, variable_de_item, autorizadas)
    B.verificar_contenido(T, pq.vetadas)
    T.index = ids
    T, ids_p, y_p = T[pob], ids[pob], y[pob]
    n = int(pob.sum())
    tam = T.sum(axis=0)
    constantes = tam.index[(tam == 0) | (tam == n)].tolist()
    T = T.drop(columns=constantes)
    a, b, largo = umbrales(nombre, n)
    c = H.Config(nombre=nombre, T=T.reset_index(drop=True), ids=ids_p, y=y_p, n=n, n_si=int(y_p.sum()), min_ant=a, min_conj=b, largo=largo, traza=traza,
                 constantes=constantes, variables=variables, modo=modo, descripcion=CONFIGS[nombre]['descripcion'], variable_de=variable_de_item, autorizadas=autorizadas, esquema=esq)
    B.verificar_items(c.T.columns, variable_de_item, autorizadas)
    B.verificar_poblacion(nombre, c, d)
    return c


# ---- sello y registro
def huella_sello():
    s = json.loads((BASE / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    if B.sha(BASE / 'protocolo' / s['archivo']) != s['sha256']:
        raise SystemExit('El protocolo de la Fase 38R no coincide con su sello.')
    for nombre, h in s['fuentes_decisiones'].items():
        if B.sha(B.FUENTES[nombre]) != h:
            raise SystemExit(f'La fuente de decisiones cambió después del sello: {nombre}')
    for nombre, h in s['codigo'].items():
        if B.sha(AQUI / nombre) != h:
            raise SystemExit(f'El código cambió después del sello: {nombre}')
    return s


def instalar_gancho():
    H.instalar_gancho()


def registrar(etapa):
    d = BASE / 'integridad'
    d.mkdir(parents=True, exist_ok=True)
    raiz, base = RAIZ.resolve(), BASE.resolve()
    leidos = {Path(x).resolve().relative_to(raiz).as_posix() for x in H._LEIDOS if Path(x).resolve().is_relative_to(raiz) and Path(x).resolve().is_file() and Path(x).suffix not in ('.py', '.pyc') and '.git' not in Path(x).resolve().parts and not Path(x).resolve().is_relative_to(base)}
    fuera = {str(Path(x).resolve()) for x in H._ESCRITOS if not Path(x).resolve().is_relative_to(base) and Path(x).suffix != '.pyc' and 'Temp' not in Path(x).resolve().parts}
    ruta = d / 'archivos_leidos.csv'
    previos = set(pd.read_csv(ruta)['archivo_leido'].astype(str)) if ruta.exists() else set()
    pd.DataFrame({'archivo_leido': sorted(previos | leidos)}, dtype=str).to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')
    ruta = d / 'registro_ejecucion.csv'
    pd.DataFrame([{'momento': datetime.now().isoformat(timespec='seconds'), 'etapa': etapa, 'archivos_leidos': len(leidos), 'escrituras_fuera': len(fuera)}]).to_csv(
        ruta, mode='a', header=not ruta.exists(), index=False, encoding='utf-8', lineterminator='\n')
    if fuera:
        raise SystemExit(f'Escritura fuera de la carpeta de la 38R: {sorted(fuera)[:5]}')


a_csv = H.a_csv
a_json = H.a_json
leer_json = H.leer_json
