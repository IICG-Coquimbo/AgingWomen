"""
Random Forest como análisis complementario EXPLORATORIO de la Fase 35B.
No reemplaza FCBF, no sustituye el resultado oficial y no decide variables para la segmentación.
Protocolo: analisis/protocolo_random_forest_35b.md.

Uso:
    python analisis/random_forest_fase35b.py --verificar     pruebas, estado y estructura; no entrena con los datos reales
    python analisis/random_forest_fase35b.py --ejecutar --autorizado-por-usuaria

Trabaja con una vista en memoria: no genera ningún dataset. La preparación ocurre dentro de cada partición.
"""
import argparse
import sys
import time
import unittest
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from joblib import Parallel, delayed
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

import complementario_cuidados as M
import complementario_fase35b as K
import seleccionar_fase35b as P
from eda import variables as V
from preprocesamiento import configuracion as C
from preprocesamiento import entropia as E

PARAMETROS_RF = dict(n_estimators=500, min_samples_leaf=5, max_features='sqrt', class_weight='balanced', random_state=42,
                     n_jobs=1)
PARTICIONES, REPETICIONES, SEMILLA_PARTICIONES = 5, 3, 42
REPETICIONES_IMPORTANCIA = 20
N_ETIQUETAS = 200
PROCESOS = 6          # medido con datos inventados: el más rápido entre 4, 6 y 8, y el equipo tiene solo 7,7 GB de RAM
ID_RF, TIPO_ETIQUETAS, TIPO_IMPORTANCIA = 70, 1, 2
OBJETIVO = 'severo_mrs'
SOBRECARGA = M.SOBRECARGA
TODAS, TRABAJADORAS, CUIDADORAS = 'todas', 'trabajadoras', 'cuidadoras'
INDICE_POBLACION = {TODAS: 0, TRABAJADORAS: 1, CUIDADORAS: 2}
NOMINALES = {'quien_prepara_comidas'}
IMPUTABLES_EN_PARTICION = {'imc', *C.LABORALES_35B}          # reconstruidas como faltantes solo en memoria
ACTIVIDAD = ['dias_ejercicio_semana', 'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza']
CUIDADOS = ['cantidad_personas_cuida', 'doble_carga', SOBRECARGA]
TRABAJO_Y_CUIDADOS = ['trabaja_actualmente', *CUIDADOS]
GRUPOS = {'actividad física': ACTIVIDAD, 'cuidados': CUIDADOS, 'trabajo y cuidados': TRABAJO_Y_CUIDADOS,
          'entorno laboral': list(C.LABORALES_35B)}
VARIABLES_FOCO = [*ACTIVIDAD, *C.LABORALES_35B, *CUIDADOS, 'vasos_agua_dia', 'tabaco_frecuencia']
EXPRESAMENTE_PROHIBIDAS = {'participante_id', 'prevision', 'etapa_menopausica', 'imc_fue_imputado', OBJETIVO}

COMPARACIONES_PRINCIPALES = [('B', 'A'), ('C1', 'C0'), ('C2', 'C1'), ('D1', 'D0')]
COMPARACIONES_ADICIONALES = [
    ('C2', 'C0'), ('A', 'A_sin_imc'), ('B', 'B_sin_imc'), ('C2', 'C2_sin_imc'),
    ('B', 'B_sin_dias'), ('B', 'B_sin_fuerza'), ('B', 'B_sin_actividad'), ('B', 'B_sin_doble'),
    ('A_cantidad_doble', 'A_cantidad'), ('A_dias', 'A'), ('A_fuerza', 'A'), ('A_fuerza', 'A_dias'),
    ('Lista_E4_529', 'A'), ('C0_dias', 'C0'), ('Lista_E4_287', 'C0'),
    ('A', 'Ref_todas'), ('B', 'Ref_todas'), ('C0', 'Ref_trabajadoras'), ('C1', 'Ref_trabajadoras'),
    ('C2', 'Ref_trabajadoras'), ('D0', 'Ref_cuidadoras'), ('D1', 'Ref_cuidadoras'),
]
MODELOS_AZAR = ('A', 'B', 'C0', 'C2')
MODELOS_IMPORTANCIA = ('A', 'B', 'C0', 'C1', 'C2', 'D0', 'D1')
ESCENARIOS_FCBF = ('E1', 'E3', 'E4', 'C3', 'C4')
ARCHIVOS_CSV = ['poblaciones_rf', 'modelos_rf', 'rendimiento_particiones', 'rendimiento_modelos', 'matrices_confusion',
                'comparacion_modelos', 'importancia_variables', 'importancia_grupos', 'importancia_particiones',
                'pruebas_azar', 'distribucion_azar', 'sensibilidad_sin_imc', 'submodelo_cuidadoras', 'rf_vs_fcbf']
FIGURAS = ['rendimiento_modelos', 'comparacion_modelos', 'importancia_B', 'importancia_C2', 'importancia_D1',
           'importancia_grupos', 'pruebas_azar']
CARPETA = P.ANALISIS / 'random_forest_35b'
PROTOCOLO = P.ANALISIS / 'protocolo_random_forest_35b.md'
PRUEBAS = P.ANALISIS / 'preprocesamiento' / 'test_random_forest_35b.py'
TAMANOS_ESPERADOS = {'todas': 529, 'trabajadoras': 287, 'cuidadoras': 239, 'imc_reconstruido': 262, 'lugar_reconstruido': 16,
                     'estres_reconstruido': 10, 'laborales_observadas': 263}


# --- Vista en memoria -------------------------------------------------------------------------

@dataclass
class Vista:
    tabla: pd.DataFrame
    objetivo: np.ndarray
    poblaciones: dict
    conteos: dict


def laborales_observadas(datos, sucio=None):
    """Personas con respuesta laboral válida en el conjunto sucio. Comprueba que coincida con el conjunto analítico."""
    if sucio is None:
        sucio = pd.read_csv(M.SUCIO, encoding='utf-8-sig', dtype=str, usecols=['participante_id', *C.LABORALES_35B])
    ids = list(datos.tabla['participante_id'])
    S = M._una_fila_por_id(sucio, ids)
    observadas = {}
    for c in C.LABORALES_35B:
        original = pd.to_numeric(S[c].astype('string').str.strip(), errors='coerce')
        valida = original.isin(M.ESCALA).to_numpy() & datos.mascara
        if (datos.tabla[c].to_numpy()[valida] != original.to_numpy()[valida]).any():
            raise RuntimeError(f'{c}: una respuesta observada difiere entre el conjunto sucio y el analítico.')
        observadas[c] = valida
    return observadas


def construir_vista(datos, poblacion, observadas):
    """Reconstruye faltantes solo en memoria. «No aplica» queda vacío y fuera de las poblaciones que lo usan."""
    t = datos.tabla.copy()
    imc_imputado = t['imc_fue_imputado'].to_numpy() == 1
    t.loc[imc_imputado, 'imc'] = np.nan
    conteos = {'todas': len(t), 'trabajadoras': int(datos.mascara.sum()), 'cuidadoras': int(poblacion.observada.sum()),
               'imc_reconstruido': int(imc_imputado.sum())}
    for c, nombre in zip(C.LABORALES_35B, ('lugar_reconstruido', 'estres_reconstruido')):
        conteos[nombre] = int((datos.mascara & ~observadas[c]).sum())
        t.loc[~observadas[c], c] = np.nan
    conteos['laborales_observadas'] = int(np.logical_and.reduce([observadas[c] for c in C.LABORALES_35B]).sum())
    t[SOBRECARGA] = np.where(poblacion.observada, poblacion.valores, np.nan)
    pob = {TODAS: np.ones(len(t), dtype=bool), TRABAJADORAS: np.asarray(datos.mascara, dtype=bool),
           CUIDADORAS: np.asarray(poblacion.observada, dtype=bool)}
    return Vista(t, t[OBJETIVO].to_numpy(dtype=int), pob, conteos)


def controlar_tamanos(conteos, esperados=None):
    esperados = TAMANOS_ESPERADOS if esperados is None else esperados
    diferencias = {k: (v, conteos.get(k)) for k, v in esperados.items() if conteos.get(k) != v}
    if diferencias:
        raise RuntimeError(f'Los tamaños no coinciden con el protocolo (esperado, actual): {diferencias}')


# --- Modelos ----------------------------------------------------------------------------------

@dataclass(frozen=True)
class Modelo:
    nombre: str
    poblacion: str
    variables: tuple
    funcion: str
    descripcion: str
    referencia: bool = False


def definir_modelos(candidatas, control=None):
    """Lista cerrada. Cualquier adición debe constar en el protocolo."""
    control = list(C.CONTROL_35B if control is None else control)
    no_lab = sorted(v for v in candidatas if v not in C.LABORALES_35B)
    sin_trabaja = [v for v in control if v != 'trabaja_actualmente']
    lab = list(C.LABORALES_35B)
    a, b = control, [*control, *no_lab]
    c0, c1, c2 = sin_trabaja, [*sin_trabaja, *no_lab], [*sin_trabaja, *no_lab, *lab]
    d0 = [v for v in b if v != 'doble_carga']          # entre cuidadoras, doble_carga es idéntica a trabaja_actualmente
    fuera = lambda lista, *quitar: [v for v in lista if v not in quitar]
    filas = [
        ('A', TODAS, a, 'principal', 'Controles'),
        ('B', TODAS, b, 'principal', 'Controles y 28 candidatas no laborales'),
        ('C0', TRABAJADORAS, c0, 'principal', 'Edad, IMC y diabetes'),
        ('C1', TRABAJADORAS, c1, 'principal', 'C0 y 28 candidatas no laborales'),
        ('C2', TRABAJADORAS, c2, 'principal', 'C1 y entorno laboral'),
        ('D0', CUIDADORAS, d0, 'principal', 'Controles y 27 no laborales, sin doble carga ni sobrecarga'),
        ('D1', CUIDADORAS, [*d0, SOBRECARGA], 'principal', 'D0 y sobrecarga'),
        ('A_sin_imc', TODAS, fuera(a, 'imc'), 'sensibilidad sin IMC', 'A sin IMC'),
        ('B_sin_imc', TODAS, fuera(b, 'imc'), 'sensibilidad sin IMC', 'B sin IMC'),
        ('C2_sin_imc', TRABAJADORAS, fuera(c2, 'imc'), 'sensibilidad sin IMC', 'C2 sin IMC'),
        ('B_sin_dias', TODAS, fuera(b, 'dias_ejercicio_semana'), 'retirada de variables', 'B sin días de ejercicio'),
        ('B_sin_fuerza', TODAS, fuera(b, 'frecuencia_fuerza'), 'retirada de variables', 'B sin ejercicio de fuerza'),
        ('B_sin_actividad', TODAS, fuera(b, *ACTIVIDAD), 'retirada de variables', 'B sin el grupo de actividad física'),
        ('B_sin_doble', TODAS, fuera(b, 'doble_carga'), 'retirada de variables', 'B sin doble carga'),
        ('A_cantidad', TODAS, [*a, 'cantidad_personas_cuida'], 'retirada de variables', 'A y cantidad de personas cuidadas'),
        ('A_cantidad_doble', TODAS, [*a, 'cantidad_personas_cuida', 'doble_carga'], 'retirada de variables',
         'A, cantidad de personas cuidadas y doble carga'),
        ('A_dias', TODAS, [*a, 'dias_ejercicio_semana'], 'lista FCBF elegida con todos los datos', 'A y lista E3/C3'),
        ('A_fuerza', TODAS, [*a, 'frecuencia_fuerza'], 'lista FCBF elegida con todos los datos', 'A y ejercicio de fuerza'),
        ('Lista_E4_529', TODAS, [*a, 'frecuencia_fuerza', 'doble_carga'], 'lista FCBF elegida con todos los datos',
         'A y lista E4/C4, sin la variable laboral'),
        ('C0_dias', TRABAJADORAS, [*c0, 'dias_ejercicio_semana'], 'lista FCBF elegida con todos los datos', 'C0 y lista E3/C3'),
        ('Lista_E4_287', TRABAJADORAS, [*c0, 'frecuencia_fuerza', 'lugar_trabajo_comprensivo', 'doble_carga'],
         'lista FCBF elegida con todos los datos', 'C0 y lista E4/C4 completa'),
    ]
    modelos = [Modelo(n, p, tuple(v), f, d) for n, p, v, f, d in filas]
    modelos += [Modelo('Ref_todas', TODAS, tuple(a), 'referencia', 'Clasificador sencillo: frecuencia de cada clase', True),
                Modelo('Ref_trabajadoras', TRABAJADORAS, tuple(c0), 'referencia', 'Clasificador sencillo: frecuencia de cada clase', True),
                Modelo('Ref_cuidadoras', CUIDADORAS, tuple(d0), 'referencia', 'Clasificador sencillo: frecuencia de cada clase', True)]
    return modelos


def _prohibida(variable):
    return (variable in EXPRESAMENTE_PROHIBIDAS or variable in C.PROHIBIDAS or variable in C.EXCLUIDAS_MODELADO
            or variable.endswith('_imputado') or variable.startswith('pregunta_') or variable.startswith('mrs_'))


def validar_modelos(modelos, vista):
    """Detiene el análisis si entra una variable prohibida, constante o con faltantes no previstos."""
    problemas = []
    for m in modelos:
        k = vista.poblaciones[m.poblacion]
        for v in m.variables:
            if _prohibida(v):
                problemas.append(f'{m.nombre}: variable prohibida {v}.')
            elif v not in vista.tabla.columns:
                problemas.append(f'{m.nombre}: falta {v}.')
            else:
                x = vista.tabla.loc[k, v]
                if x.nunique(dropna=True) < 2:
                    problemas.append(f'{m.nombre}: {v} es constante en su población.')
                if x.isna().any() and v not in IMPUTABLES_EN_PARTICION:
                    problemas.append(f'{m.nombre}: {v} tiene faltantes no previstos.')
        if len(set(m.variables)) != len(m.variables):
            problemas.append(f'{m.nombre}: variables repetidas.')
        if SOBRECARGA in m.variables and m.nombre != 'D1':
            problemas.append(f'{m.nombre}: la sobrecarga solo corresponde a D1.')
        if set(C.LABORALES_35B) & set(m.variables) and m.poblacion != TRABAJADORAS:
            problemas.append(f'{m.nombre}: variables laborales fuera de su cobertura.')
    por_nombre = {m.nombre: m for m in modelos}
    for a, b in [*COMPARACIONES_PRINCIPALES, *COMPARACIONES_ADICIONALES]:
        if a in por_nombre and b in por_nombre and por_nombre[a].poblacion != por_nombre[b].poblacion:
            problemas.append(f'{a} y {b} no usan la misma población.')
    return problemas


def comprobar_candidatas(datos):
    problemas = M.comprobar_candidatas(datos)
    if set(C.CONTROL_35B) - set(datos.tabla.columns):
        problemas.append('Faltan controles.')
    if set(datos.candidatas) - set(datos.tabla.columns):
        problemas.append('Faltan candidatas.')
    return problemas


# --- Particiones y preparación dentro de cada partición ---------------------------------------

def particiones(y):
    return list(RepeatedStratifiedKFold(n_splits=PARTICIONES, n_repeats=REPETICIONES,
                                        random_state=SEMILLA_PARTICIONES).split(np.zeros(len(y)), y))


def comprobar_particiones(partes, y):
    n = len(y)
    if len(partes) != PARTICIONES * REPETICIONES:
        raise RuntimeError('Número de particiones incorrecto.')
    for r in range(REPETICIONES):
        evaluadas = []
        for ent, eva in partes[r * PARTICIONES:(r + 1) * PARTICIONES]:
            if set(ent) & set(eva) or len(ent) + len(eva) != n:
                raise RuntimeError('Hay superposición entre entrenamiento y evaluación.')
            evaluadas.extend(eva)
        if sorted(evaluadas) != list(range(n)):
            raise RuntimeError('Una persona no se evalúa exactamente una vez por repetición.')


def crear_pipeline(variables, parametros=None, referencia=False):
    """Imputación con mediana y codificación nominal: se ajustan solo con los datos de entrenamiento."""
    variables = list(variables)
    nominales = [v for v in variables if v in NOMINALES]
    numericas = [v for v in variables if v not in NOMINALES]
    pasos = [('numericas', SimpleImputer(strategy='median'), numericas)]
    if nominales:
        pasos.append(('nominales', OneHotEncoder(handle_unknown='ignore', sparse_output=False), nominales))
    clasificador = (DummyClassifier(strategy='prior') if referencia
                    else RandomForestClassifier(**(PARAMETROS_RF if parametros is None else parametros)))
    return Pipeline([('preparar', ColumnTransformer(pasos)), ('modelo', clasificador)])


def calcular_metricas(y, prob, pred):
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {'balanced_accuracy': balanced_accuracy_score(y, pred), 'roc_auc': roc_auc_score(y, prob),
            'f1_severos': f1_score(y, pred, pos_label=1, zero_division=0), 'f1_no_severos': f1_score(y, pred, pos_label=0, zero_division=0),
            'vn': int(tn), 'fp': int(fp), 'fn': int(fn), 'vp': int(tp)}


def _puntajes(pipe, X, y):
    prob = pipe.predict_proba(X)[:, 1]
    return roc_auc_score(y, prob), balanced_accuracy_score(y, pipe.predict(X))


def permutar_columnas(X, columnas, rng):
    """Baraja filas completas de las columnas indicadas en una copia: las combinaciones del grupo siguen siendo posibles."""
    orden = rng.permutation(len(X))
    Xp = X.copy()
    for c in columnas:
        Xp[c] = X[c].to_numpy()[orden]
    return Xp


def grupos_de(variables):
    """Grupos presentes en un modelo, sin repetir conjuntos idénticos."""
    grupos, vistos = {}, set()
    for nombre, lista in GRUPOS.items():
        presentes = tuple(v for v in lista if v in variables)
        if presentes and presentes not in vistos:
            grupos[nombre] = presentes
            vistos.add(presentes)
    return grupos


def _importancias(pipe, Xe, ye, variables, i_modelo, k, n_repeticiones):
    base_auc, base_ba = _puntajes(pipe, Xe, ye)
    filas = []
    conjuntos = [('variable', v, (v,)) for v in variables] + [('grupo', g, c) for g, c in grupos_de(variables).items()]
    for i, (tipo, nombre, columnas) in enumerate(conjuntos):
        auc, ba = [], []
        for r in range(n_repeticiones):
            rng = E.generador(ID_RF, k, TIPO_IMPORTANCIA, i_modelo * 1_000_000 + i * 1000 + r)
            a, b = _puntajes(pipe, permutar_columnas(Xe, columnas, rng), ye)
            auc.append(base_auc - a)
            ba.append(base_ba - b)
        filas.append({'tipo': tipo, 'nombre': nombre, 'variables': ';'.join(columnas), 'particion': k, 'importancia_auc': float(np.mean(auc)),
                      'importancia_ba': float(np.mean(ba))})
    return filas


def _una_particion(X, y, modelo, i_modelo, k, ent, eva, parametros, n_importancia):
    pipe = crear_pipeline(modelo.variables, parametros, modelo.referencia).fit(X.iloc[ent], y[ent])
    filas = []
    for conjunto, idx in (('evaluacion', eva), ('entrenamiento', ent)):
        Xc = X.iloc[idx]
        filas.append({'modelo': modelo.nombre, 'repeticion': k // PARTICIONES, 'particion': k, 'conjunto': conjunto, 'n': len(idx),
                      **calcular_metricas(y[idx], pipe.predict_proba(Xc)[:, 1], pipe.predict(Xc))})
    imp = (_importancias(pipe, X.iloc[eva], y[eva], modelo.variables, i_modelo, k, n_importancia) if n_importancia else [])
    return filas, [{'modelo': modelo.nombre, **f} for f in imp]


def datos_de(vista, modelo):
    k = vista.poblaciones[modelo.poblacion]
    return vista.tabla.loc[k, list(modelo.variables)].reset_index(drop=True), vista.objetivo[k]


def evaluar_modelos(vista, modelos, parametros=None, procesos=1, n_importancia=REPETICIONES_IMPORTANCIA, con_importancia=MODELOS_IMPORTANCIA):
    tareas = []
    for i, m in enumerate(modelos):
        X, y = datos_de(vista, m)
        partes = particiones(y)
        comprobar_particiones(partes, y)
        n_imp = n_importancia if m.nombre in con_importancia else 0
        tareas += [delayed(_una_particion)(X, y, m, i, k, ent, eva, parametros, n_imp) for k, (ent, eva) in enumerate(partes)]
    salida = Parallel(n_jobs=procesos)(tareas)
    return pd.DataFrame([f for filas, _ in salida for f in filas]), pd.DataFrame([f for _, imp in salida for f in imp])


# --- Pruebas contra el azar: todo el procedimiento se repite con las etiquetas barajadas ----------

def etiquetas_barajadas(y, poblacion, i):
    rng = E.generador(ID_RF, 0, TIPO_ETIQUETAS, INDICE_POBLACION[poblacion] * 100_000 + i)
    return rng.permutation(y)


def _una_permutacion(X, y, modelo, i, parametros):
    barajada = etiquetas_barajadas(y, modelo.poblacion, i)
    auc, ba = [], []
    for ent, eva in particiones(barajada):
        pipe = crear_pipeline(modelo.variables, parametros).fit(X.iloc[ent], barajada[ent])
        a, b = _puntajes(pipe, X.iloc[eva], barajada[eva])
        auc.append(a)
        ba.append(b)
    return {'modelo': modelo.nombre, 'permutacion': i, 'roc_auc': float(np.mean(auc)), 'balanced_accuracy': float(np.mean(ba))}


def pruebas_azar(vista, modelos, n_etiquetas=N_ETIQUETAS, parametros=None, procesos=1, verbose=0):
    tareas = []
    for m in modelos:
        X, y = datos_de(vista, m)
        tareas += [delayed(_una_permutacion)(X, y, m, i, parametros) for i in range(n_etiquetas)]
    return pd.DataFrame(Parallel(n_jobs=procesos, verbose=verbose)(tareas))


def resumir_azar(distribucion, rendimiento):
    filas = []
    for m, g in distribucion.groupby('modelo', sort=False):
        ev = rendimiento[(rendimiento['modelo'] == m) & (rendimiento['conjunto'] == 'evaluacion')]
        for metrica in ('roc_auc', 'balanced_accuracy'):
            obs = float(ev[metrica].mean())
            d = g[metrica].to_numpy()
            filas.append({'modelo': m, 'metrica': metrica, 'observado': obs, 'media_azar': d.mean(), 'de_azar': d.std(ddof=1),
                          'p95_azar': float(np.quantile(d, 0.95)), 'n_permutaciones': len(d), 'k_mayores_o_iguales': int((d >= obs).sum()),
                          'p': (1 + int((d >= obs).sum())) / (len(d) + 1)})
    return pd.DataFrame(filas)


# --- Tablas ------------------------------------------------------------------------------------

METRICAS = ['balanced_accuracy', 'roc_auc', 'f1_severos', 'f1_no_severos']


def resumir_rendimiento(rendimiento, modelos):
    filas = []
    for m in modelos:
        d = rendimiento[rendimiento['modelo'] == m.nombre]
        ev, en = d[d['conjunto'] == 'evaluacion'], d[d['conjunto'] == 'entrenamiento']
        fila = {'modelo': m.nombre, 'funcion': m.funcion, 'poblacion': m.poblacion, 'n': int(ev['n'].sum() / REPETICIONES), 'n_variables': len(m.variables)}
        for c in METRICAS:
            fila[f'{c}_evaluacion'] = ev[c].mean()
            fila[f'{c}_de'] = ev[c].std(ddof=1)
            fila[f'{c}_entrenamiento'] = en[c].mean()
            fila[f'{c}_diferencia_ent_eval'] = en[c].mean() - ev[c].mean()
        filas.append(fila)
    return pd.DataFrame(filas)


def matrices(rendimiento):
    ev = rendimiento[rendimiento['conjunto'] == 'evaluacion']
    t = ev.groupby(['modelo', 'repeticion'], sort=False)[['vn', 'fp', 'fn', 'vp']].sum().reset_index()
    t['n'] = t[['vn', 'fp', 'fn', 'vp']].sum(axis=1)
    return t


def comparar(rendimiento, pares):
    """Diferencias por partición entre modelos con las mismas particiones. Describe la variación; no es una prueba formal."""
    ev = rendimiento[rendimiento['conjunto'] == 'evaluacion']
    filas = []
    for a, b in pares:
        pa, pb = ev[ev['modelo'] == a].set_index('particion'), ev[ev['modelo'] == b].set_index('particion')
        if list(pa.index) != list(pb.index) or (pa['n'] != pb['n']).any():
            raise RuntimeError(f'{a} y {b} no son comparables.')
        for metrica in ('roc_auc', 'balanced_accuracy'):
            d = pa[metrica] - pb[metrica]
            por_rep = d.groupby(pa['repeticion']).mean()
            filas.append({'modelo': a, 'referencia': b, 'tipo': 'principal' if (a, b) in COMPARACIONES_PRINCIPALES else 'adicional',
                          'metrica': metrica, 'media_modelo': pa[metrica].mean(), 'media_referencia': pb[metrica].mean(), 'diferencia': d.mean(), 'de': d.std(ddof=1),
                          'minimo': d.min(), 'maximo': d.max(), 'particiones_positivas': int((d > 0).sum()), 'particiones': len(d),
                          'min_por_repeticion': por_rep.min(), 'max_por_repeticion': por_rep.max()})
    return pd.DataFrame(filas)


def lectura_importancia(media, positivas, total):
    """Descripción sin umbrales: solo signo y frecuencia."""
    if media <= 0:
        return 'nula o negativa en promedio'
    if positivas == total:
        return f'positiva en todas las particiones ({positivas}/{total})'
    return f'positiva en promedio, signo variable ({positivas}/{total})'


def resumir_importancia(detalle, tipo):
    filas = []
    if len(detalle) == 0:
        return pd.DataFrame(filas)
    d = detalle[detalle['tipo'] == tipo]
    for (m, nombre), g in d.groupby(['modelo', 'nombre'], sort=False):
        fila = {'modelo': m, 'nombre': nombre, 'variables': g['variables'].iloc[0], 'particiones': len(g)}
        for metrica, col in (('auc', 'importancia_auc'), ('ba', 'importancia_ba')):
            x = g[col]
            fila.update({f'{metrica}_media': x.mean(), f'{metrica}_de': x.std(ddof=1), f'{metrica}_minimo': x.min(), f'{metrica}_maximo': x.max(),
                         f'{metrica}_positivas': int((x > 0).sum())})
        fila['lectura'] = lectura_importancia(fila['auc_media'], fila['auc_positivas'], len(g))
        fila['foco'] = nombre in VARIABLES_FOCO
        filas.append(fila)
    return pd.DataFrame(filas).sort_values(['modelo', 'auc_media'], ascending=[True, False], kind='stable')


def modelo_de_referencia(variable):
    """Modelo donde cada variable se compara con FCBF: sobrecarga en D1, laborales en C2 y el resto en B."""
    return 'D1' if variable == SOBRECARGA else 'C2' if variable in C.LABORALES_35B else 'B'


def tabla_rf_vs_fcbf(importancia, comparacion_fcbf, candidatas):
    """Lee las decisiones ya guardadas de FCBF; no las recalcula. Las listas de FCBF se eligieron con todos los datos."""
    variables = [*sorted(candidatas), SOBRECARGA]
    filas = []
    for v in variables:
        modelo = modelo_de_referencia(v)
        imp = importancia[(importancia['modelo'] == modelo) & (importancia['nombre'] == v)]
        fila = {'variable': v, 'modelo_rf': modelo}
        if len(imp):
            f = imp.iloc[0]
            fila.update({'auc_media': f['auc_media'], 'auc_de': f['auc_de'], 'auc_positivas': f['auc_positivas'], 'particiones': f['particiones'],
                         'ba_media': f['ba_media'], 'lectura_rf': f['lectura']})
        for esc in ESCENARIOS_FCBF:
            d = comparacion_fcbf[(comparacion_fcbf['escenario'] == esc) & (comparacion_fcbf['variable'] == v)]
            fila[f'fcbf_{esc}'] = d['decision_adaptado'].iloc[0] if len(d) else 'no evaluada'
        filas.append(fila)
    t = pd.DataFrame(filas)
    t['orden_rf_en_su_modelo'] = t.groupby('modelo_rf')['auc_media'].rank(ascending=False, method='min').astype(int)
    return t.sort_values('auc_media', ascending=False, kind='stable')


# --- Rutas y figuras ----------------------------------------------------------------------------

@dataclass(frozen=True)
class RutasRF:
    carpeta: Path

    def csv(self, nombre):
        return self.carpeta / f'{nombre}.csv'

    def figura(self, nombre):
        return self.carpeta / 'figuras' / f'{nombre}.png'

    @property
    def informe(self):
        return self.carpeta / 'informe_random_forest.md'

    @property
    def log(self):
        return self.carpeta / 'log_random_forest.txt'

    def declaradas(self):
        return {self.csv(n) for n in ARCHIVOS_CSV} | {self.figura(n) for n in FIGURAS} | {self.informe, self.log}


RUTAS_RF = RutasRF(CARPETA)


def validar_separacion(rutas):
    carpeta = Path(rutas.carpeta).resolve()
    for previa in (K.RUTAS_COMPLEMENTARIAS.carpeta, M.RUTAS_CUIDADOS.carpeta):
        previa = Path(previa).resolve()
        if carpeta == previa or previa in carpeta.parents:
            raise PermissionError(f'La carpeta no puede estar dentro de {previa}.')
    K.validar_separacion(rutas)


def archivos_vigilados():
    """Todo lo anterior: datasets, resultados, FCBF, complementarios, sus protocolos y su código."""
    anteriores = [M.PROTOCOLO, M.PRUEBAS, Path(M.__file__).resolve()]
    return sorted({*M.archivos_vigilados(), *M.RUTAS_CUIDADOS.declaradas(), *anteriores})


def _figuras(salida, rutas, resumen, comparacion, importancia, grupos, distribucion, azar):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    azul, gris, tinta, tenue, grilla = '#1c5cab', '#898781', '#52514e', '#898781', '#e1e0d9'

    def lienzo(n, ancho=8.5, alto_fila=0.3, ax=None):
        fig = None
        if ax is None:
            fig, ax = plt.subplots(figsize=(ancho, max(3.0, alto_fila * n + 1.5)))
        ax.grid(axis='x', color=grilla, linewidth=0.7)
        ax.set_axisbelow(True)
        ax.tick_params(axis='x', colors=tenue)
        ax.tick_params(axis='y', length=0)
        for lado in ('top', 'right', 'left'):
            ax.spines[lado].set_visible(False)
        ax.spines['bottom'].set_color(grilla)
        return fig, ax

    def puntos(ax, etiquetas, medias, inferior, superior, colores):
        y = np.arange(len(etiquetas))
        ax.hlines(y, inferior, superior, color=colores, linewidth=1.6)
        ax.scatter(medias, y, color=colores, s=42, zorder=3, edgecolors='white', linewidths=1)
        ax.set_yticks(y, etiquetas, color=tinta, fontsize=9)
        ax.invert_yaxis()

    def guardar(fig, nombre):
        fig.tight_layout()
        fig.savefig(salida.preparar(rutas.figura(nombre)), dpi=180)
        plt.close(fig)

    t = resumen[resumen['funcion'].isin(['principal', 'sensibilidad sin IMC'])]
    fig, ax = lienzo(len(t))
    medias, de = t['roc_auc_evaluacion'], t['roc_auc_de']
    puntos(ax, [f'{f.modelo} (n = {f.n})' for f in t.itertuples()], medias, medias - de, medias + de,
           [azul if f == 'principal' else gris for f in t['funcion']])
    ax.axvline(0.5, color=tinta, linewidth=1, linestyle='--')
    ax.text(0.5, -0.9, ' azar (0,5)', color=tinta, fontsize=8, ha='left')
    ax.set_title('Capacidad de predicción de cada modelo', loc='left', fontsize=12, fontweight='bold')
    ax.set_xlabel('ROC-AUC en evaluación: promedio y ± 1 desviación estándar entre particiones', color=tinta)
    ax.legend(handles=[Line2D([], [], color=azul, marker='o', label='Principal'), Line2D([], [], color=gris, marker='o', label='Sensibilidad sin IMC')],
              frameon=False, loc='lower right')
    guardar(fig, 'rendimiento_modelos')

    t = comparacion[(comparacion['metrica'] == 'roc_auc') & ~comparacion['referencia'].str.startswith('Ref_')]
    fig, ax = lienzo(len(t))
    puntos(ax, [f'{f.modelo} − {f.referencia}' for f in t.itertuples()], t['diferencia'], t['diferencia'] - t['de'], t['diferencia'] + t['de'],
           [azul if x == 'principal' else gris for x in t['tipo']])
    ax.axvline(0, color=tinta, linewidth=1)
    ax.set_title('Cuánto cambia la predicción al comparar modelos', loc='left', fontsize=12, fontweight='bold')
    ax.set_xlabel('Diferencia de ROC-AUC: promedio y ± 1 desviación estándar entre particiones', color=tinta)
    ax.legend(handles=[Line2D([], [], color=azul, marker='o', label='Comparación principal'), Line2D([], [], color=gris, marker='o', label='Adicional')],
              frameon=False, loc='lower right')
    guardar(fig, 'comparacion_modelos')

    for modelo in ('B', 'C2', 'D1'):
        d = importancia[importancia['modelo'] == modelo].sort_values('auc_media', ascending=False, kind='stable')
        fig, ax = lienzo(len(d))
        puntos(ax, [V.etiqueta(v) for v in d['nombre']], d['auc_media'], d['auc_media'] - d['auc_de'], d['auc_media'] + d['auc_de'],
               [azul if v else gris for v in d['foco']])
        ax.axvline(0, color=tinta, linewidth=1)
        ax.set_title(f'Importancia de cada variable en el modelo {modelo}', loc='left', fontsize=12, fontweight='bold')
        ax.set_xlabel('Pérdida de ROC-AUC al barajar la variable: promedio y ± 1 desviación estándar', color=tinta)
        ax.legend(handles=[Line2D([], [], color=azul, marker='o', label='Variable de interés'), Line2D([], [], color=gris, marker='o', label='Otra variable')],
                  frameon=False, loc='lower right')
        guardar(fig, f'importancia_{modelo}')

    d = grupos[grupos['modelo'].isin(['B', 'C1', 'C2', 'D0', 'D1'])]
    fig, ax = lienzo(len(d))
    puntos(ax, [f'{f.modelo}: {f.nombre}' for f in d.itertuples()], d['auc_media'], d['auc_media'] - d['auc_de'], d['auc_media'] + d['auc_de'], azul)
    ax.axvline(0, color=tinta, linewidth=1)
    ax.set_title('Importancia conjunta de variables relacionadas', loc='left', fontsize=12, fontweight='bold')
    ax.set_xlabel('Pérdida de ROC-AUC al barajar el grupo completo: promedio y ± 1 desviación estándar', color=tinta)
    guardar(fig, 'importancia_grupos')

    fig, ejes = plt.subplots(2, 2, figsize=(9, 5.6), sharex=True)
    for ax, modelo in zip(ejes.ravel(), MODELOS_AZAR):
        lienzo(1, ax=ax)
        x = distribucion[distribucion['modelo'] == modelo]['roc_auc']
        ax.hist(x, bins=20, color=gris, edgecolor='white')
        fila = azar[(azar['modelo'] == modelo) & (azar['metrica'] == 'roc_auc')]
        if len(fila):
            obs = fila['observado'].iloc[0]
            ax.axvline(obs, color=azul, linewidth=2)
            ax.set_title(f'{modelo}: observado {P._n(obs, 3)}; p = {P._n(fila["p"].iloc[0], 3)}', loc='left', fontsize=10, color=tinta)
        ax.set_yticks([])
    fig.suptitle('ROC-AUC real (línea) frente a etiquetas barajadas (barras)', x=0.02, ha='left', fontsize=12, fontweight='bold')
    guardar(fig, 'pruebas_azar')


# --- Informe ------------------------------------------------------------------------------------

def _tabla_rendimiento(resumen, filtro):
    t = resumen[filtro]
    return K._tabla_md(['Modelo', 'Población', 'n', 'Variables', 'AUC', 'DE', 'Exactitud balanceada', 'F1 severos', 'F1 no severos', 'AUC entrenamiento'],
                       [[f.modelo, f.poblacion, f.n, f.n_variables, P._n(f.roc_auc_evaluacion, 3), P._n(f.roc_auc_de, 3), P._n(f.balanced_accuracy_evaluacion, 3),
                         P._n(f.f1_severos_evaluacion, 3), P._n(f.f1_no_severos_evaluacion, 3), P._n(f.roc_auc_entrenamiento, 3)] for f in t.itertuples()])


def _tabla_comparacion(comparacion):
    return K._tabla_md(['Comparación', 'Medida', 'Diferencia', 'DE', 'Mín.', 'Máx.', 'Particiones a favor'],
                       [[f'{f.modelo} − {f.referencia}', 'AUC' if f.metrica == 'roc_auc' else 'Exactitud bal.', P._n(f.diferencia, 3), P._n(f.de, 3), P._n(f.minimo, 3),
                         P._n(f.maximo, 3), f'{f.particiones_positivas}/{f.particiones}'] for f in comparacion.itertuples()])


def _tabla_importancia(t):
    return K._tabla_md(['Modelo', 'Variable o grupo', 'Pérdida AUC', 'DE', 'Positiva', 'Pérdida exactitud bal.', 'Lectura'],
                       [[f.modelo, V.etiqueta(f.nombre), P._n(f.auc_media, 4), P._n(f.auc_de, 4), f'{f.auc_positivas}/{f.particiones}', P._n(f.ba_media, 4), f.lectura]
                        for f in t.itertuples()])


def informe(resumen, comparacion, importancia, grupos, azar, rf_fcbf, matriz, conteos, tiempos):
    principales = resumen['funcion'] == 'principal'
    foco = importancia[importancia['foco'] & importancia['modelo'].isin(['B', 'C2', 'D1'])]
    partes = [
        '# Random Forest como análisis complementario de la Fase 35B',
        f'*Generado por `analisis/random_forest_fase35b.py` el {datetime.now():%d-%m-%Y}. Protocolo: `analisis/protocolo_random_forest_35b.md`. '
        'Este informe entrega los resultados; la interpretación escrita está en `interpretacion_resultados.md`.*',
        '> **Análisis exploratorio. No reemplaza FCBF ni sustituye el resultado oficial de la Fase 35B (0 variables seleccionadas). '
        'No selecciona variables para la segmentación. Los datos son sintéticos: no demuestran relaciones causales.**',
        '## 1. Poblaciones', K._tabla_md(['Elemento', 'n'], [[k.replace('_', ' '), v] for k, v in conteos.items()]),
        '## 2. Rendimiento de los modelos principales', _tabla_rendimiento(resumen, principales),
        '## 3. Clasificador sencillo de referencia', _tabla_rendimiento(resumen, resumen['funcion'] == 'referencia'),
        '## 4. Comparaciones principales',
        'Cada diferencia usa las mismas particiones. Las particiones no son independientes: esta variación es descriptiva y no una prueba formal.',
        _tabla_comparacion(comparacion[comparacion['tipo'] == 'principal']),
        '## 5. Pruebas contra el azar',
        K._tabla_md(['Modelo', 'Medida', 'Observado', 'Media con azar', 'Percentil 95 con azar', 'p'],
                    [[f.modelo, 'AUC' if f.metrica == 'roc_auc' else 'Exactitud bal.', P._n(f.observado, 3), P._n(f.media_azar, 3), P._n(f.p95_azar, 3), P._n(f.p, 4)]
                     for f in azar.itertuples()]) if len(azar) else 'No se ejecutaron.',
        '## 6. Variables de interés', _tabla_importancia(foco),
        'Las variables relacionadas pueden reemplazarse entre sí: su importancia individual no mide un aporte independiente. '
        'Barajar `doble_carga` sola crea combinaciones imposibles con trabajo y cuidado; hay que leerla junto con su grupo y con la retirada de la variable.',
        '## 7. Importancia conjunta', _tabla_importancia(grupos),
        '## 8. Otras comparaciones (retirada de variables, listas FCBF y sin IMC)',
        'Las listas de FCBF se eligieron con todos los datos: estas comparaciones son **exploratorias y potencialmente optimistas**, no una evaluación independiente.',
        _tabla_comparacion(comparacion[(comparacion['tipo'] == 'adicional') & ~comparacion['referencia'].str.startswith('Ref_')]),
        '## 9. Random Forest frente a FCBF',
        K._tabla_md(['Variable', 'Modelo RF', 'Pérdida AUC', 'Positiva', *ESCENARIOS_FCBF],
                    [[V.etiqueta(f.variable), f.modelo_rf, P._n(f.auc_media, 4), f'{f.auc_positivas}/{f.particiones}', *[getattr(f, f'fcbf_{e}') for e in ESCENARIOS_FCBF]]
                     for f in rf_fcbf.itertuples()]),
        '## 10. Matrices de confusión (suma de cada repetición)',
        K._tabla_md(['Modelo', 'Repetición', 'VN', 'FP', 'FN', 'VP', 'n'],
                    [[f.modelo, f.repeticion + 1, f.vn, f.fp, f.fn, f.vp, f.n] for f in matriz[matriz['modelo'].isin(['A', 'B', 'C0', 'C1', 'C2', 'D0', 'D1'])].itertuples()]),
        '## 11. Lo que no se hizo',
        '- **FCBF dentro de cada partición:** no se implementó. Requiere decisiones nuevas y queda pendiente de aprobación.',
        '- **Hiperparámetros:** no se buscaron; la configuración es fija.',
        '- **Variables para la Fase 36:** no se eligieron.',
        '## 12. Advertencias',
        '- Casi la mitad del IMC está reconstruida como faltante y recibe la mediana de entrenamiento; esto reduce su capacidad de aportar.',
        '- Las demás imputaciones de la Fase 34B, incluidas las de `trabaja_actualmente` y `cuida_otras_personas`, se mantienen.',
        '- Las 287 son quienes tienen datos laborales, no todas las trabajadoras; 263 tienen ambas preguntas observadas.',
        '- El clasificador es de predicción: importancia no significa causa.',
        '## 13. Tiempo de ejecución', K._tabla_md(['Etapa', 'Segundos'], [[k, P._n(v, 1)] for k, v in tiempos.items()]),
    ]
    return '\n\n'.join(partes) + '\n'


def registro(modelos, conteos, tiempos, huellas, avisos):
    lineas = ['LOG Random Forest, Fase 35B — análisis complementario EXPLORATORIO', f'Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M}',
              f'Commit original: {K.COMMIT_ORIGINAL}', f'HEAD: {P._git("rev-parse", "HEAD").strip()}',
              f'Parámetros: {PARAMETROS_RF}; particiones {PARTICIONES}x{REPETICIONES}, semilla {SEMILLA_PARTICIONES}; importancia {REPETICIONES_IMPORTANCIA} repeticiones; etiquetas {N_ETIQUETAS}',
              f'Versiones: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}, scikit-learn {sklearn.__version__}',
              'Poblaciones: ' + ', '.join(f'{k}={v}' for k, v in conteos.items()), f'Modelos: {len(modelos)}']
    lineas += [f'SHA-256 {nombre}: {h}' for nombre, h in huellas.items()]
    lineas.append(f'Avisos de Python durante el cálculo: {len(avisos)}')
    lineas += [f'  {a}' for a in sorted(set(avisos))[:20]]
    lineas.append('Comprobaciones: particiones sin superposición; resultado igual con un proceso y con varios; dos corridas coinciden.')
    lineas.append('Tiempo real (s): ' + ', '.join(f'{k} {v:.1f}' for k, v in tiempos.items()))
    return '\n'.join(lineas) + '\n'


# --- Flujo --------------------------------------------------------------------------------------

def correr(vista, modelos, rutas, comparacion_fcbf, candidatas, parametros=None, n_etiquetas=N_ETIQUETAS, n_importancia=REPETICIONES_IMPORTANCIA,
           procesos=PROCESOS, huellas=None, verbose=0):
    """Calcula y comprueba todo antes de escribir: si algo falla, no queda ningún archivo."""
    inicio = time.perf_counter()
    validar_separacion(rutas)
    problemas = validar_modelos(modelos, vista)
    if problemas:
        raise RuntimeError('; '.join(problemas))
    salida = P.Escritor(rutas)
    tiempos = {}
    with warnings.catch_warnings(record=True) as capturados:
        warnings.simplefilter('always')
        t0 = time.perf_counter()
        rendimiento, detalle = evaluar_modelos(vista, modelos, parametros, procesos, n_importancia)
        tiempos['modelos e importancia'] = time.perf_counter() - t0

        # Mismo resultado con un solo proceso y en una segunda corrida.
        t0 = time.perf_counter()
        control = [m for m in modelos if m.nombre in ('C0', 'D1')]
        repetido, detalle_repetido = evaluar_modelos(vista, control, parametros, 1, n_importancia, ())
        nombres = [m.nombre for m in control]
        col = [c for c in rendimiento.columns]
        a = rendimiento[rendimiento['modelo'].isin(nombres)][col].reset_index(drop=True)
        if not a.equals(repetido[col].reset_index(drop=True)):
            raise RuntimeError('Dos corridas de los modelos de control no coinciden.')
        tiempos['control de reproducibilidad'] = time.perf_counter() - t0

        t0 = time.perf_counter()
        azar_modelos = [m for m in modelos if m.nombre in MODELOS_AZAR]
        distribucion = pruebas_azar(vista, azar_modelos, n_etiquetas, parametros, procesos, verbose)
        tiempos['pruebas contra el azar'] = time.perf_counter() - t0

    avisos = [f'{w.category.__name__}: {str(w.message)[:160]}' for w in capturados]
    resumen = resumir_rendimiento(rendimiento, modelos)
    comparacion = comparar(rendimiento, [*COMPARACIONES_PRINCIPALES, *COMPARACIONES_ADICIONALES])
    importancia, grupos = resumir_importancia(detalle, 'variable'), resumir_importancia(detalle, 'grupo')
    azar = resumir_azar(distribucion, rendimiento)
    rf_fcbf = tabla_rf_vs_fcbf(importancia, comparacion_fcbf, candidatas)
    matriz = matrices(rendimiento)
    sin_imc = comparacion[comparacion['referencia'].str.endswith('_sin_imc')]
    cuidadoras = resumen[resumen['poblacion'] == CUIDADORAS]

    salida.tabla(rutas.csv('poblaciones_rf'), pd.DataFrame(list(vista.conteos.items()), columns=['poblacion', 'n']))
    salida.tabla(rutas.csv('modelos_rf'), pd.DataFrame([{'modelo': m.nombre, 'poblacion': m.poblacion, 'funcion': m.funcion, 'descripcion': m.descripcion,
                                                          'n_variables': len(m.variables), 'variables': ';'.join(m.variables)} for m in modelos]))
    salida.tabla(rutas.csv('rendimiento_particiones'), rendimiento)
    salida.tabla(rutas.csv('rendimiento_modelos'), resumen)
    salida.tabla(rutas.csv('matrices_confusion'), matriz)
    salida.tabla(rutas.csv('comparacion_modelos'), comparacion)
    salida.tabla(rutas.csv('importancia_variables'), importancia)
    salida.tabla(rutas.csv('importancia_grupos'), grupos)
    salida.tabla(rutas.csv('importancia_particiones'), detalle)
    salida.tabla(rutas.csv('pruebas_azar'), azar)
    salida.tabla(rutas.csv('distribucion_azar'), distribucion)
    salida.tabla(rutas.csv('sensibilidad_sin_imc'), sin_imc)
    salida.tabla(rutas.csv('submodelo_cuidadoras'), cuidadoras)
    salida.tabla(rutas.csv('rf_vs_fcbf'), rf_fcbf)
    _figuras(salida, rutas, resumen, comparacion, importancia, grupos, distribucion, azar)
    tiempos['total'] = time.perf_counter() - inicio
    salida.texto(rutas.informe, informe(resumen, comparacion, importancia, grupos, azar, rf_fcbf, matriz, vista.conteos, tiempos))
    salida.texto(rutas.log, registro(modelos, vista.conteos, tiempos, huellas or {}, avisos))
    return {'resumen': resumen, 'comparacion': comparacion, 'importancia': importancia, 'grupos': grupos, 'azar': azar, 'rf_fcbf': rf_fcbf,
            'rendimiento': rendimiento, 'tiempos': tiempos, 'avisos': avisos}


def correr_pruebas():
    nombres = ['preprocesamiento.test_entropia', 'preprocesamiento.test_complementario_35b',
               'preprocesamiento.test_complementario_cuidados', 'preprocesamiento.test_random_forest_35b']
    suite = unittest.defaultTestLoader.loadTestsFromNames(nombres)
    return unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite).wasSuccessful()


def construir_parser():
    parser = argparse.ArgumentParser(description='Random Forest: análisis complementario exploratorio de la Fase 35B.')
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--verificar', action='store_true')
    modo.add_argument('--ejecutar', action='store_true')
    parser.add_argument('--autorizado-por-usuaria', action='store_true')
    return parser


def comprobar_datos_reales():
    """Solo identifica poblaciones y variables. No entrena ningún modelo."""
    datos, poblacion, problemas = M.comprobar_datos_reales()
    problemas = [*problemas, *comprobar_candidatas(datos)]
    vista = construir_vista(datos, poblacion, laborales_observadas(datos))
    try:
        controlar_tamanos(vista.conteos)
    except RuntimeError as error:
        problemas.append(str(error))
    modelos = definir_modelos(datos.candidatas)
    problemas += validar_modelos(modelos, vista)
    return datos, vista, modelos, list(dict.fromkeys(problemas))


def main():
    args = construir_parser().parse_args()
    if args.ejecutar and not args.autorizado_por_usuaria:
        sys.exit('La ejecución requiere --autorizado-por-usuaria.')
    problemas = K.estado_inicial()
    if not correr_pruebas():
        sys.exit('Fallaron pruebas: no se ejecuta el análisis.')
    datos, vista, modelos, de_datos = comprobar_datos_reales()
    problemas += de_datos
    for problema in problemas:
        print(f'[FALLA] {problema}')
    if problemas:
        sys.exit('El estado inicial tiene fallas: no se ejecuta el análisis.')
    validar_separacion(RUTAS_RF)
    for nombre, n in vista.conteos.items():
        print(f'{nombre}: {n}')
    for m in modelos:
        print(f'{m.nombre}: {m.poblacion}, {len(m.variables)} variables, {m.funcion}')
    if args.verificar:
        print('Pruebas, estado y estructura correctos. No se entrenó ningún modelo con los datos reales.')
        return
    huellas = {r.name: P.sha256(r) for r in (Path(__file__).resolve(), PROTOCOLO, PRUEBAS)}
    antes = P.manifiesto(archivos_vigilados())
    comparacion_fcbf = K._leer(M.RUTAS_CUIDADOS.csv('comparacion_resultados'))
    resultado = correr(vista, modelos, RUTAS_RF, comparacion_fcbf, datos.candidatas, huellas=huellas, verbose=5)
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(archivos_vigilados()))
    if cambiados:
        sys.exit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    print(f'Total {resultado["tiempos"]["total"]:.1f} s. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
