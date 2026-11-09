"""
Random Forest como análisis complementario de la Fase 35B, con la revisión corregida de 33 variables.
No reemplaza a Shannon ni a FCBF y no elige variables para la Fase 36.
Protocolo: analisis/random_forest_revision_35b_33_variables/protocolo_random_forest_33.md.

Uso, desde analisis/:
    python -m random_forest_revision_35b_33_variables.rf_33_variables --verificar     pruebas, estado y estructura; no entrena
    python -m random_forest_revision_35b_33_variables.rf_33_variables --ejecutar --autorizado-por-usuaria
    python -m random_forest_revision_35b_33_variables.rf_33_variables --resumir       tablas y figuras desde los resultados crudos; no entrena

Adapta random_forest_revision_35b/rf_revision_35b.py, que quedó preparado y nunca se entrenó, y se conserva sin cambios.
Las funciones sin cambios se importan de random_forest_fase35b.py. Lee dataset_fase35_33_variables.csv, trabaja con una
vista en memoria y no genera ningún dataset.
"""
import argparse
import subprocess
import sys
import time
import unittest
import warnings
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from joblib import Parallel, delayed
from scipy import stats
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

import complementario_cuidados as M
import complementario_fase35b as K
import informe_integrado_35b as I
import random_forest_fase35b as RF
import revision_33_variables as T
import revision_35b_reunion_1103 as R
import seleccionar_fase35b as P
from eda import variables as V
from preprocesamiento import configuracion as C
from preprocesamiento import entropia as E

PARAMETROS_RF = RF.PARAMETROS_RF
PARTICIONES, REPETICIONES = RF.PARTICIONES, RF.REPETICIONES
REPETICIONES_IMPORTANCIA = 20
N_ETIQUETAS = 200
PROCESOS = 4                # unos 145 MB por proceso, medido con datos inventados; no cambia los resultados
MEMORIA_MINIMA_MB = 500
ID_RF, TIPO_IMPORTANCIA = 71, 2
TODAS, TRABAJADORAS, CUIDADORAS = RF.TODAS, RF.TRABAJADORAS, RF.CUIDADORAS
SOBRECARGA = M.SOBRECARGA
LABORALES = list(C.LABORALES_35B)
VARIABLES_33 = list(T.VARIABLES_33)  # corrección de dominancia del 03-11-2026: sin usa_medicamentos_diabetes
GENERALES = sorted(set(VARIABLES_33) - set(LABORALES) - {SOBRECARGA})
CONTROLES = list(T.CONTROLES_33)
ACTIVIDAD = ['dias_ejercicio_semana', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'frecuencia_aerobico']
SEIS_SHANNON = ['dias_ejercicio_semana', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'imc', 'trabaja_actualmente', 'lugar_trabajo_comprensivo']
GRUPOS = {'Actividad física': ACTIVIDAD, 'Días y bajo impacto': ['dias_ejercicio_semana', 'frecuencia_bajo_impacto'], 'Trabajo': LABORALES, 'Cuidados': ['cantidad_personas_cuida', SOBRECARGA]}
EXCLUIDAS = {'doble_carga', 'prevision', T.EXCLUIDA}
ESPERADOS = {'general': (529, 281), 'laboral': (287, 166), 'cuidadoras': (239, 136)}
# Imputadas en la Fase 34B cuyo valor global difiere del de entrenamiento en alguna partición: se reimputan en la sensibilidad.
REIMPUTADAS = {'dias_ejercicio_semana': False, 'tiene_actividad_sexual': False, 'frecuencia_aerobico': True, 'frecuencia_fuerza': True, 'cantidad_personas_cuida': True}  # True: solo entre quienes responden (> 0)
CELDAS_REIMPUTADAS = {'dias_ejercicio_semana': 36, 'tiene_actividad_sexual': 30, 'frecuencia_aerobico': 7, 'frecuencia_fuerza': 2, 'cantidad_personas_cuida': 6}
IMPUTACION = 'imputación en partición'

PRINCIPALES = ('A', 'B', 'C0', 'C1', 'D0', 'D1')
MODELOS_AZAR = PRINCIPALES
MODELOS_IMPORTANCIA = (*PRINCIPALES, 'B_sin_imc', 'C1_sin_imc', 'D1_sin_imc')
COMPARACIONES = {
    'principal': [('B', 'A'), ('C1', 'C0'), ('D1', 'D0')],
    'referencia': [('A', 'Ref_general'), ('B', 'Ref_general'), ('C0', 'Ref_laboral'), ('C1', 'Ref_laboral'), ('D0', 'Ref_cuidadoras'), ('D1', 'Ref_cuidadoras')],
    'sensibilidad sin IMC': [('A', 'A_sin_imc'), ('B', 'B_sin_imc'), ('C0', 'C0_sin_imc'), ('C1', 'C1_sin_imc'), ('D0', 'D0_sin_imc'), ('D1', 'D1_sin_imc'),
                             ('B_sin_imc', 'A_sin_imc'), ('C1_sin_imc', 'C0_sin_imc'), ('D1_sin_imc', 'D0_sin_imc')],
    'retirada de variables': [('B', 'B_sin_dias'), ('B', 'B_sin_fuerza'), ('B', 'B_sin_bajo_impacto'), ('B', 'B_sin_dias_bajo_impacto'), ('B', 'B_sin_actividad')],
    IMPUTACION: [('B', 'B_imp_particion'), ('C1', 'C1_imp_particion'), ('D1', 'D1_imp_particion')],
    'conjunto Shannon': [('B', 'B_shannon'), ('B_shannon', 'A'), ('B_resto', 'Ref_general'), ('C1', 'C1_shannon')],
}
UMBRAL_APORTE, POSITIVAS_MINIMAS = 0.005, 12
CARPETA = P.ANALISIS / 'random_forest_revision_35b_33_variables'
PREPARADO = P.ANALISIS / 'random_forest_revision_35b'
PROTOCOLO = CARPETA / 'protocolo_random_forest_33.md'
PRUEBAS = CARPETA / 'test_rf_33_variables.py'
COMPARACION_SHANNON = T.CARPETA / 'informe' / 'comparacion_10000_50000.csv'
DIRECCION_SHANNON = T.CARPETA / 'permutaciones_50000' / 'direccion_resumen.csv'
METRICAS = ['roc_auc', 'balanced_accuracy', 'f1_severos', 'f1_no_severos', 'precision_severos', 'sensibilidad_severos', 'precision_no_severos', 'sensibilidad_no_severos']


# --- Modelos ----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Modelo:
    nombre: str
    poblacion: str
    variables: tuple
    funcion: str
    descripcion: str
    referencia: bool = False


def definir_modelos():
    """Lista cerrada del protocolo."""
    fuera = lambda lista, *quitar: [v for v in lista if v not in quitar]
    a, b = list(CONTROLES), list(GENERALES)
    c0, c1 = fuera(b, 'trabaja_actualmente'), [*fuera(b, 'trabaja_actualmente'), *LABORALES]
    d0, d1 = list(b), [*b, SOBRECARGA]
    shannon = [v for v in SEIS_SHANNON if v in GENERALES]
    filas = [
        ('A', TODAS, a, 'principal', 'Referencia general: tres características'),
        ('B', TODAS, b, 'principal', 'Las 30 variables generales'),
        ('C0', TRABAJADORAS, c0, 'principal', 'Referencia laboral: generales sin trabajar actualmente'),
        ('C1', TRABAJADORAS, c1, 'principal', 'C0 y entorno laboral'),
        ('D0', CUIDADORAS, d0, 'principal', 'Referencia de cuidadoras: las 30 generales'),
        ('D1', CUIDADORAS, d1, 'principal', 'D0 y sobrecarga'),
        *[(f'{n}_sin_imc', p, fuera(v, 'imc'), 'sensibilidad sin IMC', f'{n} sin IMC')
          for n, p, v in (('A', TODAS, a), ('B', TODAS, b), ('C0', TRABAJADORAS, c0), ('C1', TRABAJADORAS, c1), ('D0', CUIDADORAS, d0), ('D1', CUIDADORAS, d1))],
        ('B_sin_dias', TODAS, fuera(b, 'dias_ejercicio_semana'), 'retirada de variables', 'B sin días de ejercicio'),
        ('B_sin_fuerza', TODAS, fuera(b, 'frecuencia_fuerza'), 'retirada de variables', 'B sin ejercicio de fuerza'),
        ('B_sin_bajo_impacto', TODAS, fuera(b, 'frecuencia_bajo_impacto'), 'retirada de variables', 'B sin ejercicio de bajo impacto'),
        ('B_sin_dias_bajo_impacto', TODAS, fuera(b, 'dias_ejercicio_semana', 'frecuencia_bajo_impacto'), 'retirada de variables', 'B sin días de ejercicio ni bajo impacto'),
        ('B_sin_actividad', TODAS, fuera(b, *ACTIVIDAD), 'retirada de variables', 'B sin el grupo de actividad física'),
        ('B_imp_particion', TODAS, b, IMPUTACION, 'B reimputando dentro de la partición cinco variables de la Fase 34B'),
        ('C1_imp_particion', TRABAJADORAS, c1, IMPUTACION, 'C1 reimputando dentro de la partición cinco variables de la Fase 34B'),
        ('D1_imp_particion', CUIDADORAS, d1, IMPUTACION, 'D1 reimputando dentro de la partición cinco variables de la Fase 34B'),
        ('B_shannon', TODAS, shannon, 'conjunto Shannon', 'Las 5 generales con q < 0,10; lista elegida con todos los datos'),
        ('B_resto', TODAS, fuera(b, *shannon), 'conjunto Shannon', 'Las 25 generales sin q < 0,10; lista elegida con todos los datos'),
        ('C1_shannon', TRABAJADORAS, [v for v in SEIS_SHANNON if v != 'trabaja_actualmente'], 'conjunto Shannon', 'Las 5 aplicables con q < 0,10; lista elegida con todos los datos'),
    ]
    modelos = [Modelo(n, p, tuple(v), f, d) for n, p, v, f, d in filas]
    modelos += [Modelo('Ref_general', TODAS, tuple(a), 'referencia', 'Clasificador sencillo', True),
                Modelo('Ref_laboral', TRABAJADORAS, tuple(c0), 'referencia', 'Clasificador sencillo', True),
                Modelo('Ref_cuidadoras', CUIDADORAS, tuple(d0), 'referencia', 'Clasificador sencillo', True)]
    return modelos


def prohibida(variable):
    return variable in EXCLUIDAS or RF._prohibida(variable)


def validar_modelos(modelos, vista):
    """Detiene el análisis si entra una variable prohibida, constante o con faltantes no previstos."""
    problemas = []
    for m in modelos:
        k = vista.poblaciones[m.poblacion]
        for v in m.variables:
            if prohibida(v):
                problemas.append(f'{m.nombre}: variable prohibida {v}.')
            elif v not in VARIABLES_33:
                problemas.append(f'{m.nombre}: {v} no está entre las 33.')
            elif v not in vista.tabla.columns:
                problemas.append(f'{m.nombre}: falta {v}.')
            else:
                x = vista.tabla.loc[k, v]
                if x.nunique(dropna=True) < 2:
                    problemas.append(f'{m.nombre}: {v} es constante en su población.')
                if x.isna().any() and v not in RF.IMPUTABLES_EN_PARTICION:
                    problemas.append(f'{m.nombre}: {v} tiene faltantes no previstos.')
        if len(set(m.variables)) != len(m.variables):
            problemas.append(f'{m.nombre}: variables repetidas.')
        if SOBRECARGA in m.variables and m.poblacion != CUIDADORAS:
            problemas.append(f'{m.nombre}: la sobrecarga fuera de cuidadoras.')
        if set(LABORALES) & set(m.variables) and m.poblacion != TRABAJADORAS:
            problemas.append(f'{m.nombre}: variables laborales fuera de su cobertura.')
    por_nombre = {m.nombre: m for m in modelos}
    for pares in COMPARACIONES.values():
        for a, b in pares:
            if a in por_nombre and b in por_nombre and por_nombre[a].poblacion != por_nombre[b].poblacion:
                problemas.append(f'{a} y {b} no usan la misma población.')
    return problemas


def comprobar_poblaciones(vista):
    actuales = {}
    for nombre, pob in (('general', TODAS), ('laboral', TRABAJADORAS), ('cuidadoras', CUIDADORAS)):
        k = vista.poblaciones[pob]
        actuales[nombre] = (int(k.sum()), int(vista.objetivo[k].sum()))
    return [] if actuales == ESPERADOS else [f'Poblaciones (esperado, actual): {ESPERADOS}, {actuales}']


def comprobar_no_aplica(vista):
    """«No aplica» queda vacío, nunca en cero."""
    t, problemas = vista.tabla, []
    if t.loc[~vista.poblaciones[CUIDADORAS], SOBRECARGA].notna().any():
        problemas.append('La sobrecarga tiene valores fuera de las cuidadoras observadas.')
    if (t[SOBRECARGA] == 0).any():
        problemas.append('La sobrecarga tiene ceros.')
    for c in LABORALES:
        if t.loc[~vista.poblaciones[TRABAJADORAS], c].notna().any():
            problemas.append(f'{c} tiene valores fuera de la población laboral.')
        if (t[c] == 0).any():
            problemas.append(f'{c} tiene ceros.')
    return problemas


def comprobar_fuga(vista, limite=0.5):
    """Sin entrenar: ningún predictor puede estar casi determinado por el MRS total."""
    problemas = []
    if 'mrs_total' not in vista.tabla.columns:
        return problemas
    for v in VARIABLES_33:
        if v == 'quien_prepara_comidas':
            continue
        d = vista.tabla[[v, 'mrs_total']].dropna()
        rho = stats.spearmanr(d[v], d['mrs_total']).statistic
        if abs(rho) >= limite:
            problemas.append(f'{v}: |rho| con mrs_total = {abs(rho):.3f}.')
    return problemas


# --- Imputaciones de la Fase 34B ---------------------------------------------------------------

class ImputadorParticion(TransformerMixin, BaseEstimator):
    """Mismo criterio de la limpieza (mediana inferior, solo entre quienes responden), aprendido solo con entrenamiento."""

    def __init__(self, columnas=None):
        self.columnas = columnas

    def fit(self, X, y=None):
        self.valores_ = {}
        for c, condicional in (self.columnas or {}).items():
            if c in X.columns:
                x = X[c].dropna().astype(float)
                self.valores_[c] = float(np.percentile(x[x > 0] if condicional else x, 50, method='lower'))
        return self

    def transform(self, X):
        return X.fillna(self.valores_)


def crear_pipeline(modelo, parametros=None):
    base = RF.crear_pipeline(modelo.variables, parametros, modelo.referencia)
    if modelo.funcion != IMPUTACION:
        return base
    return Pipeline([('reimputar', ImputadorParticion(REIMPUTADAS)), ('resto', base)])


def datos_de(vista, modelo):
    """En la sensibilidad, las celdas imputadas en 34B vuelven a estar vacías, solo en memoria."""
    X, y = RF.datos_de(vista, modelo)
    if modelo.funcion == IMPUTACION:
        k = vista.poblaciones[modelo.poblacion]
        for c, celdas in getattr(vista, 'celdas_34B', {}).items():
            if c in X.columns:
                X[c] = X[c].where(~celdas[k])
    return X, y


@dataclass
class Vista33(RF.Vista):
    celdas_34B: dict = field(default_factory=dict)


def marcar_celdas_34B(datos):
    """Con marca en el conjunto limpio si faltaba 5 % o más; si no, celdas vacías en el conjunto sucio, que omiten respuestas inválidas."""
    ids = list(datos.tabla['participante_id'])
    limpio = pd.read_csv(P.LIMPIO, encoding='utf-8-sig', dtype=str).set_index('participante_id').reindex(ids)
    sucio = pd.read_csv(M.SUCIO, encoding='utf-8-sig', dtype=str).drop_duplicates('participante_id').set_index('participante_id').reindex(ids)
    celdas = {}
    for c, condicional in REIMPUTADAS.items():
        marca = f'{c}_imputado'
        if marca in limpio.columns:
            m = limpio[marca].isin(['1', '1.0']).to_numpy()
        else:
            m = sucio[c].isna().to_numpy()
            if condicional:
                m = m & (datos.tabla[c].to_numpy() > 0)
        celdas[c] = m
    return celdas


def tabla_imputaciones(datos, vista):
    """Para cada variable imputada en 34B: valor global frente al de entrenamiento, en las 45 particiones de las tres poblaciones. No entrena."""
    registro = pd.read_csv(P.RUTAS_REALES.resultados / 'faltantes_por_variable.csv', encoding='utf-8-sig', keep_default_na=False).set_index('variable')
    ids = list(datos.tabla['participante_id'])
    limpio = pd.read_csv(P.LIMPIO, encoding='utf-8-sig', dtype=str).set_index('participante_id').reindex(ids)
    sucio = pd.read_csv(M.SUCIO, encoding='utf-8-sig', dtype=str).drop_duplicates('participante_id').set_index('participante_id').reindex(ids)
    condicionales = {'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'cantidad_personas_cuida'}
    filas = []
    for v in VARIABLES_33:
        if v in (SOBRECARGA, 'imc', 'edad', *LABORALES):
            continue
        x = datos.tabla[v].to_numpy()
        aplica = x > 0 if v in condicionales else np.ones(len(x), dtype=bool)
        marca = f'{v}_imputado'
        exacta = marca in limpio.columns
        m = limpio[marca].isin(['1', '1.0']).to_numpy() if exacta else sucio[v].isna().to_numpy() & aplica
        relleno = pd.Series(x[m]).mode().iloc[0]
        distintas = 0
        for pob in (TODAS, TRABAJADORAS, CUIDADORAS):
            k = vista.poblaciones[pob]
            for ent, _ in RF.particiones(vista.objetivo[k]):
                obs = x[k][ent][~m[k][ent] & aplica[k][ent]]
                valor = pd.Series(obs).mode().sort_values().iloc[0] if v == 'quien_prepara_comidas' else np.percentile(obs.astype(float), 50, method='lower')
                distintas += int(valor != relleno)
        filas.append({'variable': v, 'imputadas_34B': int(registro.loc[v, 'imputados_34B']), 'identificadas': int(m.sum()), 'identificacion_exacta': exacta, 'valor_global': relleno, 'particiones': 45, 'particiones_con_otro_valor': distintas,
                      'tratamiento': 'Reimputada en sensibilidad' if distintas else 'Sin cambio al usar entrenamiento', 'usa_la_severidad': False})
    return pd.DataFrame(filas)


def tabla_imc_faltante(vista):
    """Si faltar el IMC se relacionara con la severidad, el valor imputado funcionaría como filtración."""
    m = vista.tabla['imc'].isna().to_numpy()
    y = vista.objetivo
    tabla = [[int(((~m) & (y == 0)).sum()), int(((~m) & (y == 1)).sum())], [int((m & (y == 0)).sum()), int((m & (y == 1)).sum())]]
    return pd.DataFrame([{'imc_observado_no_severas': tabla[0][0], 'imc_observado_severas': tabla[0][1], 'imc_faltante_no_severas': tabla[1][0], 'imc_faltante_severas': tabla[1][1],
                          'pct_severas_observado': 100 * y[~m].mean(), 'pct_severas_faltante': 100 * y[m].mean(), 'p_ji_cuadrado': stats.chi2_contingency(tabla, correction=False)[1]}])


# --- Cálculo ----------------------------------------------------------------------------------

def metricas_ampliadas(y, prob, pred):
    m = RF.calcular_metricas(y, prob, pred)
    vn, fp, fn, vp = m['vn'], m['fp'], m['fn'], m['vp']
    razon = lambda a, b: a / b if b else 0.0
    m.update(precision_severos=razon(vp, vp + fp), sensibilidad_severos=razon(vp, vp + fn), precision_no_severos=razon(vn, vn + fn), sensibilidad_no_severos=razon(vn, vn + fp))
    return m


def grupos_de(variables):
    """Grupos con al menos dos variables en el modelo."""
    salida = {}
    for nombre, lista in GRUPOS.items():
        presentes = tuple(v for v in lista if v in variables)
        if len(presentes) >= 2:
            salida[nombre] = presentes
    return salida


def _importancias(pipe, Xe, ye, variables, i_modelo, k, n_repeticiones):
    base_auc, base_ba = RF._puntajes(pipe, Xe, ye)
    filas = []
    conjuntos = [('variable', v, (v,)) for v in variables] + [('grupo', g, c) for g, c in grupos_de(variables).items()]
    for i, (tipo, nombre, columnas) in enumerate(conjuntos):
        auc, ba = [], []
        for r in range(n_repeticiones):
            rng = E.generador(ID_RF, k, TIPO_IMPORTANCIA, i_modelo * 1_000_000 + i * 1000 + r)
            a, b = RF._puntajes(pipe, RF.permutar_columnas(Xe, columnas, rng), ye)
            auc.append(base_auc - a)
            ba.append(base_ba - b)
        filas.append({'tipo': tipo, 'nombre': nombre, 'variables': ';'.join(columnas), 'particion': k, 'importancia_auc': float(np.mean(auc)), 'importancia_ba': float(np.mean(ba))})
    return filas


def _una_particion(X, y, modelo, i_modelo, k, ent, eva, parametros, n_importancia):
    pipe = crear_pipeline(modelo, parametros).fit(X.iloc[ent], y[ent])
    filas = []
    for conjunto, idx in (('evaluacion', eva), ('entrenamiento', ent)):
        Xc = X.iloc[idx]
        filas.append({'modelo': modelo.nombre, 'repeticion': k // PARTICIONES, 'particion': k, 'conjunto': conjunto, 'n': len(idx),
                      **metricas_ampliadas(y[idx], pipe.predict_proba(Xc)[:, 1], pipe.predict(Xc))})
    imp = _importancias(pipe, X.iloc[eva], y[eva], modelo.variables, i_modelo, k, n_importancia) if n_importancia else []
    return filas, [{'modelo': modelo.nombre, **f} for f in imp]


def evaluar_modelos(vista, modelos, parametros=None, procesos=1, n_importancia=REPETICIONES_IMPORTANCIA, con_importancia=MODELOS_IMPORTANCIA):
    tareas = []
    for i, m in enumerate(modelos):
        X, y = datos_de(vista, m)
        partes = RF.particiones(y)
        RF.comprobar_particiones(partes, y)
        n_imp = n_importancia if m.nombre in con_importancia and not m.referencia else 0
        tareas += [delayed(_una_particion)(X, y, m, i, k, ent, eva, parametros, n_imp) for k, (ent, eva) in enumerate(partes)]
    salida = Parallel(n_jobs=procesos)(tareas)
    return pd.DataFrame([f for filas, _ in salida for f in filas]), pd.DataFrame([f for _, imp in salida for f in imp])


# --- Rutas y escritura -------------------------------------------------------------------------

@dataclass(frozen=True)
class Rutas:
    carpeta: Path

    def crudo(self, nombre):
        return self.carpeta / 'resultados' / 'crudos' / f'{nombre}.csv'

    def csv(self, nombre):
        return self.carpeta / 'resultados' / f'{nombre}.csv'

    def figura(self, nombre):
        return self.carpeta / 'figuras' / f'{nombre}.png'

    @property
    def log(self):
        return self.carpeta / 'registro_ejecucion.txt'


RUTAS = Rutas(CARPETA)


def validar_carpeta(rutas):
    """Fuera de todas las salidas anteriores."""
    carpeta = Path(rutas.carpeta).resolve()
    previas = [R.CARPETA, RF.CARPETA, PREPARADO, K.RUTAS_COMPLEMENTARIAS.carpeta, M.RUTAS_CUIDADOS.carpeta, P.RUTAS_REALES.resultados, P.RUTAS_REALES.figuras, P.RUTAS_REALES.dataset.parent]
    for previa in previas:
        previa = Path(previa).resolve()
        if carpeta == previa or previa in carpeta.parents:
            raise PermissionError(f'La carpeta no puede estar dentro de {previa}.')


def escribir_crudo(ruta, df):
    """Los resultados crudos se escriben una sola vez y con todos los decimales."""
    if ruta.exists():
        raise FileExistsError(f'No se sobrescribe un resultado crudo: {ruta}')
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix('.tmp')
    df.to_csv(temporal, index=False, encoding='utf-8-sig')
    temporal.replace(ruta)


def leer_crudo(ruta):
    return pd.read_csv(ruta, encoding='utf-8-sig', keep_default_na=False, na_values=[''])


def escribir_derivado(ruta, df):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding='utf-8-sig', float_format='%.6f')


def calcular(vista, modelos, rutas, parametros=None, n_etiquetas=N_ETIQUETAS, n_importancia=REPETICIONES_IMPORTANCIA, procesos=PROCESOS, verbose=0, huellas=None):
    """Entrena y guarda lo crudo. Si se interrumpe, retoma lo que falte: cada cálculo está determinado por sus semillas."""
    validar_carpeta(rutas)
    problemas = validar_modelos(modelos, vista)
    if problemas:
        raise RuntimeError('; '.join(problemas))
    tiempos = {}
    if huellas and not rutas.crudo('huellas_calculo').exists():
        escribir_crudo(rutas.crudo('huellas_calculo'), pd.DataFrame([{'archivo': k, 'sha256': v} for k, v in huellas.items()]))
    if rutas.crudo('rendimiento_particiones').exists():
        rendimiento = leer_crudo(rutas.crudo('rendimiento_particiones'))
    else:
        t0 = time.perf_counter()
        rendimiento, detalle = evaluar_modelos(vista, modelos, parametros, procesos, n_importancia)
        tiempos['modelos e importancia'] = time.perf_counter() - t0
        t0 = time.perf_counter()
        control = [m for m in modelos if m.nombre in ('C0', 'D1')]
        repetido, _ = evaluar_modelos(vista, control, parametros, 1, n_importancia, ())
        nombres = [m.nombre for m in control]
        a = rendimiento[rendimiento['modelo'].isin(nombres)].reset_index(drop=True)
        if not a.equals(repetido[a.columns].reset_index(drop=True)):
            raise RuntimeError('Dos corridas de los modelos de control no coinciden.')
        tiempos['control de reproducibilidad'] = time.perf_counter() - t0
        escribir_crudo(rutas.crudo('importancia_particiones'), detalle)
        escribir_crudo(rutas.crudo('rendimiento_particiones'), rendimiento)
    for m in [m for m in modelos if m.nombre in MODELOS_AZAR]:
        ruta = rutas.crudo(f'azar_{m.nombre}')
        if ruta.exists():
            continue
        t0 = time.perf_counter()
        escribir_crudo(ruta, RF.pruebas_azar(vista, [m], n_etiquetas, parametros, procesos, verbose))
        tiempos[f'azar {m.nombre}'] = time.perf_counter() - t0
    t0 = time.perf_counter()
    azar_modelos = [m for m in modelos if m.nombre in MODELOS_AZAR]
    if azar_modelos:
        m = azar_modelos[0]
        X, y = RF.datos_de(vista, m)
        fila = RF._una_permutacion(X, y, m, 0, parametros)
        guardada = leer_crudo(rutas.crudo(f'azar_{m.nombre}')).iloc[0]
        if abs(fila['roc_auc'] - guardada['roc_auc']) > 1e-12:
            raise RuntimeError('La permutación de control no coincide con la guardada.')
    tiempos['control de la prueba contra el azar'] = time.perf_counter() - t0
    if tiempos:
        previo = leer_crudo(rutas.crudo('tiempos')) if rutas.crudo('tiempos').exists() else pd.DataFrame(columns=['etapa', 'segundos'])
        nuevo = pd.concat([previo, pd.DataFrame([{'etapa': k, 'segundos': v} for k, v in tiempos.items()])], ignore_index=True)
        rutas.crudo('tiempos').parent.mkdir(parents=True, exist_ok=True)
        nuevo.to_csv(rutas.crudo('tiempos'), index=False, encoding='utf-8-sig')
    return rendimiento


# --- Tablas derivadas --------------------------------------------------------------------------

def resumir_rendimiento(rendimiento, modelos):
    filas = []
    for m in modelos:
        d = rendimiento[rendimiento['modelo'] == m.nombre]
        ev, en = d[d['conjunto'] == 'evaluacion'], d[d['conjunto'] == 'entrenamiento']
        fila = {'modelo': m.nombre, 'funcion': m.funcion, 'poblacion': m.poblacion, 'n': int(ev['n'].sum() / REPETICIONES), 'n_variables': len(m.variables)}
        for c in METRICAS:
            fila[f'{c}_evaluacion'] = ev[c].mean()
            fila[f'{c}_de'] = ev[c].std(ddof=1)
            fila[f'{c}_minimo'] = ev[c].min()
            fila[f'{c}_maximo'] = ev[c].max()
            fila[f'{c}_entrenamiento'] = en[c].mean()
            fila[f'{c}_diferencia_ent_eval'] = en[c].mean() - ev[c].mean()
        filas.append(fila)
    return pd.DataFrame(filas)


def matrices(rendimiento):
    return RF.matrices(rendimiento)


def lectura_diferencia(inferior, superior):
    if inferior > 0:
        return 'Mejora respaldada'
    if superior < 0:
        return 'Empeora'
    return 'Sin diferencia clara'


def intervalo_corregido(d, razon=0.25, nivel=0.95):
    """Nadeau y Bengio: varianza × (1/J + n_evaluación/n_entrenamiento), porque las particiones comparten datos."""
    d = np.asarray(d, dtype=float)
    j = len(d)
    if j < 2 or d.std(ddof=1) == 0:
        return float(d.mean()), float(d.mean())
    error = np.sqrt((1 / j + razon) * d.var(ddof=1))
    t = stats.t.ppf(0.5 + nivel / 2, j - 1)
    return float(d.mean() - t * error), float(d.mean() + t * error)


def comparar(rendimiento, comparaciones=None):
    """Diferencias por partición entre modelos con las mismas particiones."""
    ev = rendimiento[rendimiento['conjunto'] == 'evaluacion']
    filas = []
    for tipo, pares in (COMPARACIONES if comparaciones is None else comparaciones).items():
        for a, b in pares:
            pa, pb = ev[ev['modelo'] == a].set_index('particion'), ev[ev['modelo'] == b].set_index('particion')
            if len(pa) == 0 or len(pb) == 0:
                continue
            if list(pa.index) != list(pb.index) or (pa['n'] != pb['n']).any():
                raise RuntimeError(f'{a} y {b} no son comparables.')
            for metrica in ('roc_auc', 'balanced_accuracy'):
                d = pa[metrica] - pb[metrica]
                inferior, superior = intervalo_corregido(d)
                filas.append({'modelo': a, 'referencia': b, 'tipo': tipo, 'metrica': metrica, 'media_modelo': pa[metrica].mean(), 'media_referencia': pb[metrica].mean(), 'diferencia': d.mean(), 'de': d.std(ddof=1),
                              'minimo': d.min(), 'maximo': d.max(), 'particiones_positivas': int((d > 0).sum()), 'particiones': len(d), 'ic95_inferior': inferior, 'ic95_superior': superior, 'lectura': lectura_diferencia(inferior, superior)})
    return pd.DataFrame(filas)


def clasificar_aporte(media, positivas, total=15):
    """Regla descriptiva fijada antes de ver resultados."""
    if media <= 0:
        return 'Nulo o negativo'
    if positivas / total < POSITIVAS_MINIMAS / 15:
        return 'Aporte inestable'
    return 'Aporte consistente' if media >= UMBRAL_APORTE else 'Aporte pequeño'


def resumir_importancia(detalle, tipo):
    if len(detalle) == 0:
        return pd.DataFrame()
    filas = []
    for (m, nombre), g in detalle[detalle['tipo'] == tipo].groupby(['modelo', 'nombre'], sort=False):
        fila = {'modelo': m, 'nombre': nombre, 'variables': g['variables'].iloc[0], 'particiones': len(g)}
        for metrica, col in (('auc', 'importancia_auc'), ('ba', 'importancia_ba')):
            x = g[col]
            fila.update({f'{metrica}_media': x.mean(), f'{metrica}_de': x.std(ddof=1), f'{metrica}_minimo': x.min(), f'{metrica}_maximo': x.max(), f'{metrica}_positivas': int((x > 0).sum())})
        fila['aporte'] = clasificar_aporte(fila['auc_media'], fila['auc_positivas'], len(g))
        fila['q_menor_0_10'] = nombre in SEIS_SHANNON
        filas.append(fila)
    t = pd.DataFrame(filas).sort_values(['modelo', 'auc_media'], ascending=[True, False], kind='stable')
    t['orden_en_modelo'] = t.groupby('modelo').cumcount() + 1
    return t


def modelo_de_lectura(variable):
    return 'D1' if variable == SOBRECARGA else 'C1' if variable in LABORALES else 'B'


def consistencia(relevante, aporte):
    if relevante:
        return {'Aporte consistente': 'Coinciden ambos métodos', 'Aporte pequeño': 'Shannon sí; RF aporte pequeño'}.get(aporte, 'Solo Shannon')
    return {'Aporte consistente': 'Solo Random Forest', 'Aporte pequeño': 'Ninguno claro (aporte pequeño)'}.get(aporte, 'Sin respaldo en ninguno')


ADVERTENCIAS = {
    'imc': '49,5 % imputado; se evaluó sin IMC',
    'trabaja_actualmente': '22 valores imputados; sin efecto directo en el simulador',
    'lugar_trabajo_comprensivo': 'Solo 287; depende de la composición de la familia',
    'estres_entorno_laboral': 'Solo 287',
    SOBRECARGA: 'Solo 239; pregunta menciona «su trabajo» y 99 no trabajan',
    'frecuencia_fuerza': '84,7 % no la realiza; relacionada con otros indicadores de ejercicio; depende de la familia',
    'dias_ejercicio_semana': 'Relacionada con otros indicadores de ejercicio',
    'frecuencia_bajo_impacto': 'Relacionada con otros indicadores de ejercicio',
    'frecuencia_aerobico': 'Relacionada con otros indicadores de ejercicio',
    'distension_abdominal': 'Podría solaparse con síntomas',
    'quien_prepara_comidas': 'Nominal: sin signo',
    'cantidad_personas_cuida': 'Incluye 21 ceros por imputación de cuidar',
}


def tabla_shannon_rf(importancia, comparacion, direccion):
    """33 filas. Cada variable se lee en un solo modelo; las poblaciones no se ordenan juntas."""
    comparacion = comparacion.set_index('variable')
    direccion = direccion.set_index('variable')
    filas = []
    for v in VARIABLES_33:
        modelo = modelo_de_lectura(v)
        c, d = comparacion.loc[v], direccion.loc[v]
        i = importancia[(importancia['modelo'] == modelo) & (importancia['nombre'] == v)]
        if len(i) != 1:
            raise RuntimeError(f'{v}: falta su importancia en {modelo}.')
        i = i.iloc[0]
        r10, r50 = str(c['relevante_10000']) == 'True', str(c['relevante_50000']) == 'True'
        filas.append({'variable': v, 'etiqueta': V.etiqueta(v), 'poblacion': c['poblacion'], 'n': int(c['n']), 'su': float(c['su']), 'q_10000': float(c['q_10000']), 'q_50000': float(c['q_50000']),
                      'q_menor_0_10': r50, 'q_coincide': r10 == r50, 'direccion': d['direccion'], 'clase_shannon': d['clase'], 'rho_mrs': d['rho_mrs'], 'modelo_rf': modelo,
                      'auc_media': i['auc_media'], 'auc_de': i['auc_de'], 'auc_positivas': int(i['auc_positivas']), 'particiones': int(i['particiones']), 'ba_media': i['ba_media'], 'ba_positivas': int(i['ba_positivas']), 'aporte_rf': i['aporte'], 'orden_en_modelo': int(i['orden_en_modelo']),
                      'consistencia': consistencia(r50, i['aporte']), 'advertencias': ADVERTENCIAS.get(v, '')})
    t = pd.DataFrame(filas)
    orden = {'general': 0, 'laboral': 1, 'cuidadoras': 2}
    return t.assign(_o=t['poblacion'].map(orden)).sort_values(['_o', 'orden_en_modelo'], kind='stable').drop(columns='_o').reset_index(drop=True)


def cambios_sin_imc(importancia):
    """Cómo cambia el orden de cada variable al retirar IMC."""
    filas = []
    for con, sin in (('B', 'B_sin_imc'), ('C1', 'C1_sin_imc'), ('D1', 'D1_sin_imc')):
        a = importancia[importancia['modelo'] == con].set_index('nombre')
        b = importancia[importancia['modelo'] == sin].set_index('nombre')
        for v in b.index:
            filas.append({'modelo': con, 'variable': v, 'auc_con_imc': a.loc[v, 'auc_media'], 'auc_sin_imc': b.loc[v, 'auc_media'], 'orden_con_imc': a.loc[v, 'orden_en_modelo'], 'orden_sin_imc': b.loc[v, 'orden_en_modelo'], 'aporte_con_imc': a.loc[v, 'aporte'], 'aporte_sin_imc': b.loc[v, 'aporte']})
    return pd.DataFrame(filas)


def leer_azar(rutas, modelos):
    partes = [leer_crudo(rutas.crudo(f'azar_{m.nombre}')) for m in modelos if m.nombre in MODELOS_AZAR]
    return pd.concat(partes, ignore_index=True)


# --- Figuras -----------------------------------------------------------------------------------

AZUL, GRIS, TINTA, TENUE, GRILLA, ROJO = '#1c5cab', '#898781', '#52514e', '#898781', '#e1e0d9', '#c8402f'
ETIQ_POB = {TODAS: 'General', TRABAJADORAS: 'Laboral', CUIDADORAS: 'Cuidadoras'}


def _figuras(rutas, resumen, comparacion, importancia, grupos, distribucion, azar, shannon, matriz):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter

    coma = FuncFormatter(lambda v, _: f'{v:g}'.replace('.', ',').replace('-', '−'))

    def ejes(ax):
        ax.xaxis.set_major_formatter(coma)
        ax.grid(axis='x', color=GRILLA, linewidth=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis='x', colors=TENUE, labelsize=8.5)
        ax.tick_params(axis='y', length=0)
        for lado in ('top', 'right', 'left'):
            ax.spines[lado].set_visible(False)
        ax.spines['bottom'].set_color(GRILLA)

    def puntos(ax, etiquetas, medias, inf, sup, colores, tam=9):
        y = np.arange(len(etiquetas))
        ax.hlines(y, inf, sup, color=colores, linewidth=1.6)
        ax.scatter(medias, y, color=colores, s=40, zorder=3, edgecolors='white', linewidths=1)
        ax.set_yticks(y, etiquetas, color=TINTA, fontsize=tam)
        ax.invert_yaxis()

    def guardar(fig, nombre):
        ruta = rutas.figura(nombre)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        fig.tight_layout()
        fig.savefig(ruta, dpi=200, facecolor='white')
        plt.close(fig)

    # Rendimiento de los modelos principales
    t = resumen[resumen['funcion'] == 'principal']
    fig, ax_ = plt.subplots(1, 2, figsize=(7.4, 3.5), sharey=True)
    for ax, metrica, nombre in zip(ax_, ('roc_auc', 'balanced_accuracy'), ('ROC-AUC', 'Exactitud balanceada')):
        ejes(ax)
        m, de = t[f'{metrica}_evaluacion'], t[f'{metrica}_de']
        puntos(ax, [f'{f.modelo} ({ETIQ_POB[f.poblacion]}, n = {f.n})' for f in t.itertuples()], m, m - de, m + de, AZUL)
        ax.axvline(0.5, color=TINTA, linewidth=1, linestyle='--')
        ax.set_xlabel(f'{nombre} en evaluación (± 1 DE)', color=TINTA, fontsize=9)
    if not ax_[0].yaxis_inverted():  # el eje compartido se invirtió dos veces
        ax_[0].invert_yaxis()
    fig.supxlabel('Línea discontinua: clasificador sencillo (0,5)', color=TINTA, fontsize=7.5)
    guardar(fig, 'rendimiento_modelos')

    # Comparaciones principales y sin IMC
    t = comparacion[(comparacion['metrica'] == 'roc_auc') & comparacion['tipo'].isin(['principal', 'conjunto Shannon', 'retirada de variables'])]
    t = pd.concat([t[t['tipo'] == k] for k in ('principal', 'retirada de variables', 'conjunto Shannon')])
    fig, ax = plt.subplots(figsize=(7.2, 0.33 * len(t) + 1.3))
    ejes(ax)
    colores = [AZUL if x == 'principal' else GRIS for x in t['tipo']]
    puntos(ax, [f'{f.modelo} − {f.referencia}' for f in t.itertuples()], t['diferencia'], t['ic95_inferior'], t['ic95_superior'], colores)
    ax.axvline(0, color=TINTA, linewidth=1)
    ax.set_xlabel('Diferencia de ROC-AUC, con IC 95 % corregido', color=TINTA, fontsize=9)
    ax.legend(handles=[Line2D([], [], color=AZUL, marker='o', label='Principal'), Line2D([], [], color=GRIS, marker='o', label='Secundaria')], frameon=False, fontsize=8, loc='lower right')
    guardar(fig, 'comparacion_modelos')

    # Importancias: una figura por modelo
    for modelo in ('B', 'C1', 'D1'):
        d = importancia[importancia['modelo'] == modelo]
        fig, ax = plt.subplots(figsize=(7.2, 0.235 * len(d) + 1.1))
        ejes(ax)
        colores = [AZUL if x else GRIS for x in d['q_menor_0_10']]
        puntos(ax, [V.etiqueta(v) for v in d['nombre']], d['auc_media'], d['auc_media'] - d['auc_de'], d['auc_media'] + d['auc_de'], colores, 8)
        ax.axvline(0, color=TINTA, linewidth=1)
        ax.set_xlabel('Pérdida de ROC-AUC al barajar la variable (± 1 DE entre particiones)', color=TINTA, fontsize=9)
        ax.legend(handles=[Line2D([], [], color=AZUL, marker='o', label='q < 0,10 en Shannon'), Line2D([], [], color=GRIS, marker='o', label='q ≥ 0,10 en Shannon')], frameon=False, fontsize=8, loc='lower right')
        guardar(fig, f'importancia_{modelo}')

    # Grupos
    d = grupos[grupos['modelo'].isin(PRINCIPALES)]
    fig, ax = plt.subplots(figsize=(7.2, 0.34 * len(d) + 1.1))
    ejes(ax)
    puntos(ax, [f'{f.modelo}: {f.nombre}' for f in d.itertuples()], d['auc_media'], d['auc_media'] - d['auc_de'], d['auc_media'] + d['auc_de'], AZUL)
    ax.axvline(0, color=TINTA, linewidth=1)
    ax.set_xlabel('Pérdida de ROC-AUC al barajar el grupo completo (± 1 DE)', color=TINTA, fontsize=9)
    guardar(fig, 'importancia_grupos')

    # Azar
    fig, ejes_azar = plt.subplots(2, 3, figsize=(7.4, 3.9), sharex=True)
    for ax, modelo in zip(ejes_azar.ravel(), MODELOS_AZAR):
        ejes(ax)
        ax.hist(distribucion[distribucion['modelo'] == modelo]['roc_auc'], bins=18, color=GRIS, edgecolor='white')
        fila = azar[(azar['modelo'] == modelo) & (azar['metrica'] == 'roc_auc')].iloc[0]
        ax.axvline(fila['observado'], color=AZUL, linewidth=2)
        ax.set_title(f'{modelo}: AUC {P._n(fila["observado"], 3)}; p = {P._n(fila["p"], 3)}', loc='left', fontsize=9, color=TINTA)
        ax.set_yticks([])
    fig.supxlabel('ROC-AUC promedio: etiquetas barajadas (barras) y real (línea)', color=TINTA, fontsize=9)
    guardar(fig, 'pruebas_azar')

    # Shannon frente a Random Forest, solo población general
    d = shannon[shannon['modelo_rf'] == 'B']
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.grid(color=GRILLA, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors=TENUE, labelsize=8.5)
    for lado in ('top', 'right'):
        ax.spines[lado].set_visible(False)
    for lado in ('left', 'bottom'):
        ax.spines[lado].set_color(GRILLA)
    ax.xaxis.set_major_formatter(coma)
    ax.yaxis.set_major_formatter(coma)
    ax.scatter(d['su'], d['auc_media'], color=[AZUL if x else GRIS for x in d['q_menor_0_10']], s=46, edgecolors='white', linewidths=1, zorder=3)
    ax.axhline(0, color=TINTA, linewidth=1)
    destacar = set(d[d['q_menor_0_10']]['variable']) | set(d.nlargest(8, 'auc_media')['variable'])
    a_la_izquierda = {'trabaja_actualmente', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'dias_ejercicio_semana', 'imc'}
    for f in d[d['variable'].isin(destacar)].itertuples():
        izquierda = f.variable in a_la_izquierda
        ax.annotate(f.etiqueta, (f.su, f.auc_media), xytext=(-6 if izquierda else 6, 3), textcoords='offset points', fontsize=7, color=TINTA, ha='right' if izquierda else 'left')
    ax.set_xlabel('SU con la severidad (asociación marginal)', color=TINTA, fontsize=9)
    ax.set_ylabel('Pérdida de ROC-AUC en el modelo B', color=TINTA, fontsize=9)
    ax.legend(handles=[Line2D([], [], color=AZUL, marker='o', linestyle='', label='q < 0,10 en Shannon'), Line2D([], [], color=GRIS, marker='o', linestyle='', label='q ≥ 0,10 en Shannon')], frameon=False, fontsize=8, loc='upper left')
    guardar(fig, 'shannon_vs_rf')

    # Sin IMC
    t = comparacion[(comparacion['tipo'] == 'sensibilidad sin IMC') & (comparacion['metrica'] == 'roc_auc') & comparacion['modelo'].isin(PRINCIPALES) & comparacion['referencia'].isin([f'{m}_sin_imc' for m in PRINCIPALES])]
    fig, ax = plt.subplots(figsize=(7.0, 2.7))
    ejes(ax)
    y = np.arange(len(t))
    ax.hlines(y, t['media_referencia'], t['media_modelo'], color=GRILLA, linewidth=2)
    ax.scatter(t['media_modelo'], y, color=AZUL, s=44, zorder=3, label='Con IMC')
    ax.scatter(t['media_referencia'], y, color=GRIS, s=44, zorder=3, label='Sin IMC')
    ax.set_yticks(y, t['modelo'], color=TINTA, fontsize=9)
    ax.invert_yaxis()
    ax.axvline(0.5, color=TINTA, linewidth=1, linestyle='--')
    ax.set_xlabel('ROC-AUC promedio en evaluación', color=TINTA, fontsize=9)
    ax.legend(frameon=False, fontsize=8, loc='best')
    guardar(fig, 'sensibilidad_imc')

    # Matrices de confusión, promedio de las tres repeticiones
    fig, ax_ = plt.subplots(2, 3, figsize=(7.2, 4.6))
    for ax, modelo in zip(ax_.ravel(), PRINCIPALES):
        g = matriz[matriz['modelo'] == modelo][['vn', 'fp', 'fn', 'vp']].mean()
        z = np.array([[g['vn'], g['fp']], [g['fn'], g['vp']]])
        fila = 100 * z / z.sum(axis=1, keepdims=True)  # una sola escala en los seis paneles: % de cada clase real
        ax.imshow(fila, cmap='Blues', vmin=0, vmax=100)
        for (i, j), valor in np.ndenumerate(z):
            ax.text(j, i, f'{P._n(valor, 1)}\n({P._n(fila[i, j], 0)} %)', ha='center', va='center', fontsize=8.5, color='white' if fila[i, j] > 62 else '#000000')
        ax.set_xticks([0, 1], ['No severo', 'Severo'], fontsize=8, color=TINTA)
        ax.set_yticks([0, 1], ['No severo', 'Severo'], fontsize=8, color=TINTA)
        ax.set_title(modelo, loc='left', fontsize=9.5, color=TINTA)
        ax.tick_params(length=0)
        for lado in ax.spines.values():
            lado.set_visible(False)
    fig.supxlabel('Predicción', fontsize=9, color=TINTA)
    fig.supylabel('Valor real', fontsize=9, color=TINTA)
    guardar(fig, 'matrices_confusion')


# --- Derivados y registro -----------------------------------------------------------------------

def resumir(rutas, modelos, conteos=None, comparacion_shannon=None, direccion_shannon=None, huellas=None):
    """Tablas, figuras y registro desde lo crudo. No entrena."""
    rendimiento = leer_crudo(rutas.crudo('rendimiento_particiones'))
    detalle = leer_crudo(rutas.crudo('importancia_particiones'))
    distribucion = leer_azar(rutas, modelos)
    comparacion_shannon = K._leer(COMPARACION_SHANNON) if comparacion_shannon is None else comparacion_shannon
    direccion_shannon = pd.read_csv(DIRECCION_SHANNON, encoding='utf-8-sig') if direccion_shannon is None else direccion_shannon
    resumen = resumir_rendimiento(rendimiento, modelos)
    comparacion = comparar(rendimiento)
    importancia, grupos = resumir_importancia(detalle, 'variable'), resumir_importancia(detalle, 'grupo')
    azar = RF.resumir_azar(distribucion, rendimiento)
    shannon = tabla_shannon_rf(importancia, comparacion_shannon, direccion_shannon)
    matriz = matrices(rendimiento)
    tablas = {'modelos': pd.DataFrame([{'modelo': m.nombre, 'poblacion': m.poblacion, 'funcion': m.funcion, 'descripcion': m.descripcion, 'n_variables': len(m.variables), 'variables': ';'.join(m.variables)} for m in modelos]),
              'rendimiento_modelos': resumen, 'comparacion_modelos': comparacion, 'matrices_confusion': matriz, 'importancia_variables': importancia, 'importancia_grupos': grupos, 'pruebas_azar': azar,
              'shannon_vs_rf': shannon, 'sensibilidad_imc': comparacion[comparacion['tipo'] == 'sensibilidad sin IMC'], 'sensibilidad_imc_importancia': cambios_sin_imc(importancia), 'sensibilidad_imputacion': comparacion[comparacion['tipo'] == IMPUTACION]}
    if conteos:
        tablas['poblaciones'] = pd.DataFrame(list(conteos.items()), columns=['elemento', 'n'])
    for nombre, tabla in tablas.items():
        escribir_derivado(rutas.csv(nombre), tabla)
    _figuras(rutas, resumen, comparacion, importancia, grupos, distribucion, azar, shannon, matriz)
    tiempos = leer_crudo(rutas.crudo('tiempos')) if rutas.crudo('tiempos').exists() else pd.DataFrame(columns=['etapa', 'segundos'])
    calculo = leer_crudo(rutas.crudo('huellas_calculo')) if rutas.crudo('huellas_calculo').exists() else pd.DataFrame(columns=['archivo', 'sha256'])
    lineas = ['REGISTRO Random Forest, revisión de 33 variables de la Fase 35B — análisis complementario', f'Tablas y figuras generadas: {datetime.now():%Y-%m-%d %H:%M}', f'HEAD: {_head()}',
              f'Parámetros: {PARAMETROS_RF}; particiones {PARTICIONES}x{REPETICIONES}, semilla {RF.SEMILLA_PARTICIONES}; importancia {REPETICIONES_IMPORTANCIA} repeticiones; etiquetas {N_ETIQUETAS}; procesos {PROCESOS}',
              f'Versiones: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}, scikit-learn {sklearn.__version__}', f'Modelos: {len(modelos)}']
    if conteos:
        lineas.append('Poblaciones: ' + ', '.join(f'{k}={v}' for k, v in conteos.items()))
    lineas += [f'Durante el cálculo, SHA-256 {f.archivo}: {f.sha256}' for f in calculo.itertuples()]
    lineas += [f'Al resumir, SHA-256 {k}: {v}' for k, v in (huellas or {}).items()]
    lineas.append('Comprobaciones: particiones sin superposición; modelos de control iguales con uno y con varios procesos; permutación de control igual a la guardada.')
    lineas += [f'Tiempo {f.etapa}: {float(f.segundos):.1f} s' for f in tiempos.itertuples()]
    rutas.log.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    return tablas


def _head():
    try:
        return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=P.ANALISIS).stdout.strip()
    except OSError:
        return 'no disponible'


# --- Flujo --------------------------------------------------------------------------------------

def archivos_vigilados():
    """Todo lo anterior: datasets, resultados de Shannon, informes, programas y el programa de Random Forest anterior."""
    revision = [r for r in R.CARPETA.rglob('*') if r.is_file()]
    preparado = [r for r in PREPARADO.glob('*') if r.is_file()]
    return sorted({*R.archivos_vigilados(), *revision, *preparado, T.DATASET_33, T.DATASET_ORIGINAL, Path(T.__file__).resolve(), Path(R.__file__).resolve(), Path(I.__file__).resolve(), P.ANALISIS / 'informe_word_35b.py', P.ANALISIS / 'informe_word_33.py'})


def estado():
    """HEAD se registra, sin exigir un valor: un commit posterior no debe impedir reproducir."""
    return [p for p in K.estado_inicial() if not p.startswith('HEAD es')]


def comprobar_datos_reales():
    """Identifica poblaciones y variables. No entrena ningún modelo."""
    datos, poblacion, problemas = M.comprobar_datos_reales()
    tabla_33 = pd.read_csv(T.DATASET_33, encoding='utf-8-sig', dtype={'participante_id': str}, float_precision='round_trip')
    if T.EXCLUIDA in tabla_33.columns:
        problemas = [*problemas, f'{T.EXCLUIDA} sigue en el conjunto de 33 variables.']
    if not datos.tabla.drop(columns=T.EXCLUIDA).equals(tabla_33):
        problemas = [*problemas, 'El conjunto de 33 variables difiere de dataset_fase35.csv en algo más que la columna excluida.']
    datos = replace(datos, tabla=tabla_33)
    base = RF.construir_vista(datos, poblacion, RF.laborales_observadas(datos))
    vista = Vista33(base.tabla, base.objetivo, base.poblaciones, base.conteos, marcar_celdas_34B(datos))
    identificadas = {c: int(m.sum()) for c, m in vista.celdas_34B.items()}
    if identificadas != CELDAS_REIMPUTADAS:
        problemas = [*problemas, f'Celdas a reimputar (esperado, actual): {CELDAS_REIMPUTADAS}, {identificadas}']
    try:
        RF.controlar_tamanos(vista.conteos)
    except RuntimeError as error:
        problemas = [*problemas, str(error)]
    modelos = definir_modelos()
    problemas = [*problemas, *comprobar_poblaciones(vista), *comprobar_no_aplica(vista), *comprobar_fuga(vista), *validar_modelos(modelos, vista)]
    if int((vista.objetivo == 0).sum()) != 248:
        problemas.append('No hay 248 participantes no severas.')
    return datos, vista, modelos, list(dict.fromkeys(problemas))


def correr_pruebas():
    nombres = ['preprocesamiento.test_entropia', 'preprocesamiento.test_random_forest_35b', 'preprocesamiento.test_revision_35b', 'preprocesamiento.test_revision_33_variables', 'random_forest_revision_35b_33_variables.test_rf_33_variables']
    suite = unittest.defaultTestLoader.loadTestsFromNames(nombres)
    return unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite).wasSuccessful()


def memoria_disponible_mb():
    import psutil
    return psutil.virtual_memory().available / 2 ** 20


def huellas_programa():
    return {r.name: P.sha256(r) for r in (Path(__file__).resolve(), PROTOCOLO, PRUEBAS, Path(RF.__file__).resolve())}


def construir_parser():
    parser = argparse.ArgumentParser(description='Random Forest: análisis complementario de la Fase 35B con 33 variables.')
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--verificar', action='store_true')
    modo.add_argument('--ejecutar', action='store_true')
    modo.add_argument('--resumir', action='store_true')
    parser.add_argument('--autorizado-por-usuaria', action='store_true')
    return parser


def main():
    args = construir_parser().parse_args()
    if args.ejecutar and not args.autorizado_por_usuaria:
        sys.exit('La ejecución requiere --autorizado-por-usuaria.')
    if args.resumir:
        datos, vista, modelos, problemas = comprobar_datos_reales()
        if problemas:
            sys.exit('; '.join(problemas))
        resumir(RUTAS, modelos, vista.conteos, huellas=huellas_programa())
        print('Tablas y figuras generadas sin entrenar.')
        return
    problemas = estado()
    if not correr_pruebas():
        sys.exit('Fallaron pruebas: no se ejecuta el análisis.')
    datos, vista, modelos, de_datos = comprobar_datos_reales()
    problemas += de_datos
    for problema in problemas:
        print(f'[FALLA] {problema}')
    if problemas:
        sys.exit('El estado inicial tiene fallas: no se ejecuta el análisis.')
    validar_carpeta(RUTAS)
    for nombre, n in vista.conteos.items():
        print(f'{nombre}: {n}')
    for m in modelos:
        print(f'{m.nombre}: {m.poblacion}, {len(m.variables)} variables, {m.funcion}')
    print(f'Memoria disponible: {memoria_disponible_mb():.0f} MB')
    if args.verificar:
        print('Pruebas, estado y estructura correctos. No se entrenó ningún modelo con los datos reales.')
        return
    if memoria_disponible_mb() < MEMORIA_MINIMA_MB:
        sys.exit(f'Hay menos de {MEMORIA_MINIMA_MB} MB disponibles: cierra programas antes de ejecutar.')
    antes = P.manifiesto(archivos_vigilados())
    RUTAS.csv('x').parent.mkdir(parents=True, exist_ok=True)
    escribir_derivado(RUTAS.csv('revision_imputaciones_34B'), tabla_imputaciones(datos, vista))
    escribir_derivado(RUTAS.csv('imc_faltante_y_severidad'), tabla_imc_faltante(vista))
    calcular(vista, modelos, RUTAS, verbose=5, huellas=huellas_programa())
    resumir(RUTAS, modelos, vista.conteos, huellas=huellas_programa())
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(archivos_vigilados()))
    if cambiados:
        sys.exit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    print(f'Listo. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    with warnings.catch_warnings():
        main()
