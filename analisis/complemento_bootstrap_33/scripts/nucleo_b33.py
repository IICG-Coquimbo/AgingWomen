"""Complemento de la Fase 35B: estabilidad de la selección con las 33 candidatas finales.

Reutiliza sin modificar las funciones congeladas de la Fase 35B y de su revisión del 03-11-2026:
  - datos y poblaciones: `revision_35b_reunion_1103.comprobar_datos_reales` (529, 287 y 239);
  - escenario de 33: `revision_33_variables.construir_escenario_33` (mapa de índices de las 34);
  - remuestreo: `preprocesamiento.fcbf.indices_bootstrap` (bootstrap estratificado por severo_mrs, con reemplazo);
  - selección: `complementario_cuidados.seleccionar` (etapas 1, 2 y 3; variantes adaptada y estándar).

La única función propia es `medir_remuestreo`: es `complementario_cuidados.medir` con el número de remuestreo en la
clave de semilla (allí está fijo en 0). Una prueba exige que, con el remuestreo 0 y sin remuestrear, dé exactamente lo
mismo que la función original.
"""
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
ANALISIS = BASE.parent
if str(ANALISIS) not in sys.path:
    sys.path.insert(0, str(ANALISIS))

import numpy as np  # noqa: E402

import complementario_cuidados as M  # noqa: E402
import complementario_fase35b as K  # noqa: E402
import revision_33_variables as V33  # noqa: E402
import revision_35b_reunion_1103 as R  # noqa: E402
import seleccionar_fase35b as P  # noqa: E402
from preprocesamiento import configuracion as C  # noqa: E402
from preprocesamiento import entropia as E  # noqa: E402
from preprocesamiento import fcbf as F  # noqa: E402

# --- Parámetros fijados en el protocolo de este complemento, antes de ejecutar ---------------------------------------
N_REMUESTREOS = 500
N_PERMUTACIONES = C.N_PERMUTACIONES_35B          # 5.000: configuración histórica de la estabilidad (protocolo 35B, §7)
ALFA = R.ALFA                                     # q < 0,10: criterio de la selección definitiva (revisión 03-11)
ID_ANALISIS = P.ID_ESTABILIDAD                    # 1: misma corriente que la corrida histórica -> mismas muestras
SOBRECARGA = R.SOBRECARGA
VARIABLES_33 = V33.VARIABLES_33
EXCLUIDAS = ['doble_carga', 'prevision', 'usa_medicamentos_diabetes']
CACHE = BASE / 'remuestreos' / 'cache'
VARIANTES = ('adaptado', 'estandar')


def cargar():
    """Datos, poblaciones y escenario definitivo de 33. Se detiene si algo no coincide con lo documentado."""
    datos, poblacion, problemas = R.comprobar_datos_reales()
    if problemas:
        raise RuntimeError('; '.join(problemas))
    esc34 = R.construir_escenario(datos, poblacion)
    esc = V33.construir_escenario_33(esc34)
    if {v: esc34.indice()[v] for v in esc.indice()} != esc.indice():
        raise RuntimeError('El mapa de índices de las 34 cambió.')
    esc = replace(esc, base=replace(esc.base, id_analisis=ID_ANALISIS, nombre='Estabilidad 33'))
    comprobar(esc)
    return datos, poblacion, esc


def comprobar(esc):
    variables = sorted([*esc.base.candidatas, SOBRECARGA])
    if variables != VARIABLES_33 or len(variables) != 33:
        raise RuntimeError('Las candidatas no son las 33 finales.')
    if set(variables) & set(EXCLUIDAS):
        raise RuntimeError('Una variable excluida está entre las candidatas.')
    if set(variables) & set(C.PROHIBIDAS):
        raise RuntimeError('Una variable prohibida (MRS, resultado o auditoría) está entre las candidatas.')
    tam = {'general': len(esc.base.objetivo), 'laboral': int(esc.base.mascara.sum()), 'cuidadoras': int(esc.poblacion.sum())}
    if tam != {'general': 529, 'laboral': 287, 'cuidadoras': 239}:
        raise RuntimeError(f'Tamaños inesperados: {tam}')
    if np.bincount(esc.base.objetivo).tolist() != [248, 281]:
        raise RuntimeError('severo_mrs no tiene 248 y 281 casos.')
    if sorted(esc.base.laborales) != sorted(C.LABORALES_35B):
        raise RuntimeError('Las laborales no son las documentadas.')


def aplicar_indices(esc, idx):
    """Toda la información por persona sigue a la persona remuestreada: datos, objetivo y las dos poblaciones."""
    base = F.aplicar_indices(esc.base, idx)
    return replace(esc, base=base, sobrecarga=np.asarray(esc.sobrecarga)[idx], poblacion=np.asarray(esc.poblacion)[idx])


def indices(esc, i):
    rng = E.generador(esc.base.id_analisis, i, F.TIPO_BOOTSTRAP)
    return F.indices_bootstrap(esc.base.objetivo, rng)


def medir_remuestreo(esc, i, n_permutaciones):
    """`complementario_cuidados.medir` con el remuestreo i en la clave de semilla. Usa C.ALFA_Q_35B vigente."""
    base, indice, datos, y = esc.base, esc.indice(), esc.datos(), esc.base.objetivo
    variables = sorted([*base.candidatas, SOBRECARGA])
    su_obj, n_obj, p_obj = {}, {}, {}
    for v in variables:
        m = esc.mascara_de(v)
        rng = E.generador(base.id_analisis, i, F.TIPO_RELEVANCIA, indice[v])
        su_obj[v], p_obj[v] = E.prueba_permutacion(y[m], datos[v][m], n_permutaciones, rng)
        n_obj[v] = int(m.sum())
    q = E.benjamini_hochberg([p_obj[v] for v in variables])
    q_obj = dict(zip(variables, map(float, q)))
    relevantes = [v for v in variables if q_obj[v] < C.ALFA_Q_35B]

    medidas = M.MedidasCuidados(su_obj, n_obj, p_obj, q_obj, relevantes)
    for j, a in enumerate(relevantes):
        for b in relevantes[j + 1:]:
            m = esc.mascara_de(a, b)
            rng = E.generador(base.id_analisis, i, F.TIPO_PAR, indice[a] * F.FACTOR_PAR + indice[b])
            medidas.su_par[(a, b)], medidas.p_par[(a, b)] = E.prueba_permutacion(datos[a][m], datos[b][m], n_permutaciones, rng)
            medidas.n_par[(a, b)] = int(m.sum())
    pares = sorted(medidas.su_par)
    medidas.q_par = dict(zip(pares, map(float, E.benjamini_hochberg([medidas.p_par[p] for p in pares]))))

    generales = [v for v in relevantes if v != SOBRECARGA]
    if any(v in base.laborales for v in generales):
        m = base.mascara
        for v in generales:
            medidas.su_objetivo_laboral[v] = E.su(datos[v][m], y[m])
    if SOBRECARGA in relevantes:
        for z in generales:
            m = esc.mascara_de(z, SOBRECARGA)
            medidas.su_otra_etapa3[z] = E.su(datos[z][m], y[m])
            medidas.su_sobrecarga_etapa3[z] = E.su(datos[SOBRECARGA][m], y[m])
    return medidas


def seleccionar(muestra, medidas):
    """Ambas variantes con las funciones congeladas y sus controles. El umbral ya debe estar en ALFA."""
    salida = {}
    generales = M._sin_sobrecarga(medidas)
    for nombre, exigir_q in (('adaptado', True), ('estandar', False)):
        d = M.seleccionar(muestra, medidas, exigir_q)
        P.controlar_seleccion(muestra.base, generales, {v: x for v, x in d.items() if v != SOBRECARGA})
        M.controlar_etapa3(muestra, medidas, d)
        salida[nombre] = d
    return salida


def un_remuestreo(esc, i, n_permutaciones=N_PERMUTACIONES, cache=None):
    """Remuestreo i completo: bootstrap, relevancia con permutaciones, pares, FCBF en dos variantes. Reanudable."""
    ruta = Path(cache) / f'rem_{i:04d}.json' if cache else None
    if ruta and ruta.exists():
        return json.loads(ruta.read_text(encoding='utf-8'))
    idx = indices(esc, i)
    muestra = aplicar_indices(esc, idx)
    with K.umbral(ALFA):
        medidas = medir_remuestreo(muestra, i, n_permutaciones)
        decisiones = seleccionar(muestra, medidas)
    res = {
        'remuestreo': i,
        'indices_sha256': __import__('hashlib').sha256(np.asarray(idx, dtype=np.int64).tobytes()).hexdigest(),
        'n_unicas': int(len(np.unique(idx))),
        'n_laboral': int(muestra.base.mascara.sum()),
        'n_cuidadoras': int(muestra.poblacion.sum()),
        'n_severas': int(muestra.base.objetivo.sum()),
        'relevantes': list(medidas.relevantes),
        'n_pares': len(medidas.su_par),
        'p': {v: float(x) for v, x in medidas.p_objetivo.items()},
        'q': {v: float(x) for v, x in medidas.q_objetivo.items()},
        'su': {v: float(x) for v, x in medidas.su_objetivo.items()},
        'n': {v: int(x) for v, x in medidas.n_objetivo.items()},
    }
    for nombre, d in decisiones.items():
        res[nombre] = {v: [x['decision'], x['eliminada_por'], x['etapa']] for v, x in d.items()}
    if ruta:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        tmp = ruta.with_suffix(f'.{os.getpid()}.tmp')
        tmp.write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')
        os.replace(tmp, ruta)
    return res


def seleccion_definitiva():
    """Selección guardada de la configuración definitiva (33 variables, 10.000 y 50.000 permutaciones)."""
    import pandas as pd
    salida = {}
    for n in (10000, 50000):
        t = pd.read_csv(V33.CARPETA / f'permutaciones_{n}' / 'decisiones_fcbf.csv', encoding='utf-8-sig')
        r = pd.read_csv(V33.CARPETA / f'permutaciones_{n}' / 'relevancia_33.csv', encoding='utf-8-sig')
        salida[n] = {'decisiones': t, 'relevancia': r}
    return salida
