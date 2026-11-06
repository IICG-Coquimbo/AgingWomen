"""
Versión complementaria EXPLORATORIA de FCBF con el módulo de cuidados completo: 31 candidatas.
No sustituye el resultado oficial de la Fase 35B. Protocolo: analisis/protocolo_cuidados_35b.md.

Uso:
    python analisis/complementario_cuidados.py --verificar     pruebas, estado y tamaños; no calcula ninguna SU real
    python analisis/complementario_cuidados.py --ejecutar --autorizado-por-usuaria

Agrega `sobrecarga_fisica_emocional` en una tercera etapa de cobertura, solo entre cuidadoras. Reutiliza las
funciones congeladas de la Fase 35B sin modificarlas. Trabaja con una vista en memoria: no genera ningún dataset.
"""
import argparse
import sys
import time
import unittest
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import complementario_fase35b as K
import seleccionar_fase35b as P
from eda import variables as V
from limpieza import reglas as R
from preprocesamiento import configuracion as C
from preprocesamiento import entropia as E
from preprocesamiento import fcbf as F

SOBRECARGA = 'sobrecarga_fisica_emocional'
ESCALA = (1, 2, 3, 4, 5)
INDICE_SOBRECARGA = 30                # fijo: las otras 30 candidatas conservan el índice que dio sus permutaciones
ETAPA_CUIDADORAS = 'cuidadoras'
OBSERVADAS, CUIDADORAS = 'observadas', 'cuidadoras'
CARPETA = P.ANALISIS / 'complementario_cuidados'
PROTOCOLO = P.ANALISIS / 'protocolo_cuidados_35b.md'
PRUEBAS = P.ANALISIS / 'preprocesamiento' / 'test_complementario_cuidados.py'
SUCIO = V.RAIZ / 'datos' / 'sintetico' / 'dataset_usuaria_sucio.csv'
ARCHIVOS_CSV = ['poblaciones_cuidados', 'su_objetivo', 'su_pares', 'decisiones_fcbf', 'pares_no_eliminados_cobertura',
                'pares_no_eliminados_sobrecarga', 'comparacion_resultados', 'efecto_familia', 'resumen_escenarios',
                'relacion_cuidados', 'sobrecarga_por_nivel']
COLUMNAS_NO_ELIMINADOS_SOBRECARGA = ['eliminable', 'su_par', 'q_par', 'su_sobrecarga_severidad', 'su_eliminable_severidad',
                                     'n']
COLUMNAS_LIMPIO = ['participante_id', 'cuida_otras_personas', 'trabaja_actualmente', SOBRECARGA, *C.LABORALES_35B]
COLUMNAS_SUCIO = ['participante_id', 'cuida_otras_personas', 'trabaja_actualmente', SOBRECARGA, *R.TRABAJO]
VACIOS = {'', '-', 'N/A', 'NA', 'S/D', 'SIN DATO', 'NAN', 'NONE', '-1', '99', '999', '9999'}
CUIDA_RESPONDIDA = {'SI', 'S', 'NO', 'N'}
TRABAJA_RESPONDIDA = {'TRUE', 'FALSE', 'VERDADERO', 'FALSO', '1', '0'}

# Tamaños comprobados antes de registrar el protocolo; si cambian, la versión complementaria no se ejecuta.
TAMANOS_ESPERADOS = {
    'todas': 529, 'laboral': 287, 'cuidadoras': 251, 'sobrecarga_observada': 239, 'sobrecarga_imputada': 12,
    'sobrecarga_y_laboral': 130, 'cuidadoras_y_laboral': 137, 'cuida_imputada_no': 21, 'cuida_deducida': 4,
    'cuida_imputada_en_observadas': 0, 'cuida_deducida_en_observadas': 3, 'sobrecarga_borrada_por_condicional': 2,
    'trabaja_imputada': 22, 'doble_con_trabaja_imputada': 10, 'trabaja_imputada_en_observadas': 10,
    'trabaja_imputada_en_sobrecarga_y_laboral': 0, 'laborales_observadas_en_287': 263,
    'laborales_observadas_en_sobrecarga_y_laboral': 122,
}


@dataclass(frozen=True)
class Plan:
    parametros: K.Parametros
    poblacion: str
    referencia: str


PLANES = (
    Plan(K.Parametros('C3', 50000, 0.05, 'Principal, q < 0,05'), OBSERVADAS, 'E3'),
    Plan(K.Parametros('C4', 50000, 0.10, 'Principal exploratorio, q < 0,10'), OBSERVADAS, 'E4'),
    Plan(K.Parametros('S3', 50000, 0.05, 'Sensibilidad con 251 cuidadoras, q < 0,05'), CUIDADORAS, 'E3'),
    Plan(K.Parametros('S4', 50000, 0.10, 'Sensibilidad con 251 cuidadoras, q < 0,10'), CUIDADORAS, 'E4'),
)


# --- Población: se define con los datos actuales, nunca con la versión verdadera del simulador ---

@dataclass
class Poblacion:
    valores: np.ndarray             # sobrecarga del conjunto limpio; NaN = no aplica
    cuidadora: np.ndarray           # cuida_otras_personas = SI en el conjunto limpio
    observada: np.ndarray           # además, respuesta válida de 1 a 5 en el conjunto sucio
    conteos: dict


def _normal(serie):
    return serie.astype('string').str.strip().str.upper().fillna('')


def _una_fila_por_id(sucio, ids):
    """El conjunto sucio repite algunos id: se aceptan solo si no discrepan en las columnas usadas."""
    faltan = set(ids) - set(sucio['participante_id'])
    if faltan:
        raise RuntimeError(f'Faltan {len(faltan)} participantes en el conjunto sucio.')
    filas = sucio[sucio['participante_id'].isin(ids)].copy()
    columnas = [c for c in filas.columns if c != 'participante_id']
    normalizadas = filas[columnas].apply(_normal)
    if normalizadas.assign(participante_id=filas['participante_id']).drop_duplicates()['participante_id'].duplicated().any():
        raise RuntimeError('Un participante repetido discrepa en el conjunto sucio.')
    return filas.drop_duplicates('participante_id').set_index('participante_id').loc[list(ids)]


def identificar_poblacion(ids, limpio, sucio, laboral, doble_carga):
    """Identifica quién cuida y quién respondió. `limpio` y `sucio` son tablas de texto."""
    ids = list(ids)
    L = limpio.set_index('participante_id').loc[ids]
    S = _una_fila_por_id(sucio, ids)
    laboral = pd.Series(np.asarray(laboral, dtype=bool), index=ids)
    doble = pd.Series(np.asarray(doble_carga), index=ids) == 1

    cuidadora = L['cuida_otras_personas'] == 'SI'
    valores = pd.to_numeric(L[SOBRECARGA], errors='coerce')
    original = pd.to_numeric(S[SOBRECARGA].astype('string').str.strip(), errors='coerce')
    valida = original.isin(ESCALA)
    observada = cuidadora & valida

    if valores[~cuidadora].notna().any():
        raise RuntimeError('Hay sobrecarga con valor en personas que no cuidan.')
    if valores[cuidadora].isna().any():
        raise RuntimeError('Hay cuidadoras sin sobrecarga en el conjunto limpio.')
    if not valores[cuidadora].isin(ESCALA).all():
        raise RuntimeError('Hay sobrecarga fuera de la escala 1 a 5 entre las cuidadoras.')
    if (valores[observada] != original[observada]).any():
        raise RuntimeError('Una respuesta observada de sobrecarga difiere entre el conjunto sucio y el limpio.')

    cuida_vacia = ~_normal(S['cuida_otras_personas']).isin(CUIDA_RESPONDIDA)
    trabaja_vacia = ~_normal(S['trabaja_actualmente']).isin(TRABAJA_RESPONDIDA)
    responde_trabajo = S[R.TRABAJO].apply(lambda c: ~_normal(c).isin(VACIOS)).any(axis=1)
    trabaja_imputada = trabaja_vacia & ~responde_trabajo & (L['trabaja_actualmente'] == 'True')
    cuida_imputada = cuida_vacia & ~cuidadora
    cuida_deducida = cuida_vacia & cuidadora
    laborales_validas = pd.concat([pd.to_numeric(S[c].astype('string').str.strip(), errors='coerce').isin(ESCALA)
                                   for c in C.LABORALES_35B], axis=1).all(axis=1)
    conteos = {
        'todas': len(ids), 'laboral': int(laboral.sum()), 'cuidadoras': int(cuidadora.sum()),
        'sobrecarga_observada': int(observada.sum()), 'sobrecarga_imputada': int((cuidadora & ~valida).sum()),
        'sobrecarga_y_laboral': int((observada & laboral).sum()), 'cuidadoras_y_laboral': int((cuidadora & laboral).sum()),
        'cuida_imputada_no': int(cuida_imputada.sum()), 'cuida_deducida': int(cuida_deducida.sum()),
        'cuida_imputada_en_observadas': int((observada & cuida_imputada).sum()),
        'cuida_deducida_en_observadas': int((observada & cuida_deducida).sum()),
        'sobrecarga_borrada_por_condicional': int((valida & ~cuidadora).sum()),
        'trabaja_imputada': int(trabaja_imputada.sum()), 'doble_con_trabaja_imputada': int((doble & trabaja_imputada).sum()),
        'trabaja_imputada_en_observadas': int((observada & trabaja_imputada).sum()),
        'trabaja_imputada_en_sobrecarga_y_laboral': int((observada & laboral & trabaja_imputada).sum()),
        'laborales_observadas_en_287': int((laboral & laborales_validas).sum()),
        'laborales_observadas_en_sobrecarga_y_laboral': int((observada & laboral & laborales_validas).sum()),
    }
    return Poblacion(valores.to_numpy(dtype=float), cuidadora.to_numpy(), observada.to_numpy(), conteos)


def controlar_tamanos(conteos, esperados=None):
    esperados = TAMANOS_ESPERADOS if esperados is None else esperados
    diferencias = {k: (esperados[k], conteos.get(k)) for k in esperados if conteos.get(k) != esperados[k]}
    if diferencias:
        raise RuntimeError(f'Los tamaños no coinciden con el protocolo (esperado, actual): {diferencias}')


def cargar_poblacion(datos):
    """Solo lectura del conjunto limpio y del sucio, sin escribir nada."""
    limpio = pd.read_csv(P.LIMPIO, encoding='utf-8-sig', dtype=str, usecols=COLUMNAS_LIMPIO)
    sucio = pd.read_csv(SUCIO, encoding='utf-8-sig', dtype=str, usecols=COLUMNAS_SUCIO)
    return identificar_poblacion(datos.tabla['participante_id'], limpio, sucio, datos.mascara, datos.tabla['doble_carga'])


def comprobar_candidatas(datos):
    """Las 30 candidatas, su orden y los controles no cambian; las tres de cuidados siguen disponibles."""
    problemas = []
    if len(datos.candidatas) != C.N_CANDIDATAS_35B or datos.candidatas != sorted(datos.candidatas):
        problemas.append('Las 30 candidatas originales cambiaron.')
    if SOBRECARGA in datos.candidatas or SOBRECARGA in datos.tabla.columns:
        problemas.append('La sobrecarga ya está en el conjunto analítico: no debe tener un valor para quienes no cuidan.')
    if not {'doble_carga', 'cantidad_personas_cuida'} <= set(datos.candidatas):
        problemas.append('doble_carga y cantidad_personas_cuida deben seguir como candidatas.')
    if datos.control != list(C.CONTROL_35B) or 'trabaja_actualmente' in datos.candidatas:
        problemas.append('Los controles cambiaron.')
    return problemas


# --- Cálculo: medida con tres poblaciones; FCBF congelado para las 30 y Etapa 3 para la sobrecarga ---

@dataclass
class EscenarioCuidados:
    base: F.Escenario
    sobrecarga: np.ndarray
    poblacion: np.ndarray
    nombre_poblacion: str = OBSERVADAS

    def __post_init__(self):
        x, m = np.asarray(self.sobrecarga, dtype=float), np.asarray(self.poblacion, dtype=bool)
        if SOBRECARGA in self.base.candidatas or SOBRECARGA in self.base.laborales:
            raise ValueError('La sobrecarga no puede ser una candidata de las etapas 1 y 2.')
        if len(self.base.candidatas) > INDICE_SOBRECARGA:
            raise ValueError('El índice de la sobrecarga coincidiría con el de otra candidata.')
        if len(x) != len(self.base.objetivo) or len(m) != len(x) or not m.any():
            raise ValueError('La población de la sobrecarga no corresponde a los datos.')
        if not np.isin(x[m], ESCALA).all():
            raise ValueError('Dentro de la población, la sobrecarga debe estar observada en la escala 1 a 5.')
        if not np.isnan(x[~m]).all():
            raise ValueError('Fuera de la población, la sobrecarga debe quedar vacía: no aplica no es cero.')

    def indice(self):
        return {**self.base.indice(), SOBRECARGA: INDICE_SOBRECARGA}

    def datos(self):
        return {**self.base.datos, SOBRECARGA: self.sobrecarga}

    def mascara_de(self, *variables):
        """Personas de una medición: cobertura común de todas las variables que participan."""
        m = np.ones(len(self.base.objetivo), dtype=bool)
        if any(v in self.base.laborales for v in variables):
            m = m & self.base.mascara
        if SOBRECARGA in variables:
            m = m & self.poblacion
        return m


@dataclass
class MedidasCuidados(F.Medidas):
    su_otra_etapa3: dict = field(default_factory=dict)        # SU(z, severidad) en la población común con la sobrecarga
    su_sobrecarga_etapa3: dict = field(default_factory=dict)  # SU(sobrecarga, severidad) en esa misma población


def escenario_cuidados(datos, poblacion, nombre):
    if nombre == OBSERVADAS:
        m = poblacion.observada
    elif nombre == CUIDADORAS:
        m = poblacion.cuidadora
    else:
        raise ValueError(f'Población desconocida: {nombre}')
    return EscenarioCuidados(P.escenario_principal(datos), np.where(m, poblacion.valores, np.nan), m, nombre)


def medir(esc, n_permutaciones):
    """Como `fcbf.medir`, con 31 candidatas en una sola familia y las semillas de las 30 sin mover."""
    base, indice, datos, y = esc.base, esc.indice(), esc.datos(), esc.base.objetivo
    variables = sorted([*base.candidatas, SOBRECARGA])
    su_obj, n_obj, p_obj = {}, {}, {}
    for v in variables:
        m = esc.mascara_de(v)
        rng = E.generador(base.id_analisis, 0, F.TIPO_RELEVANCIA, indice[v])
        su_obj[v], p_obj[v] = E.prueba_permutacion(y[m], datos[v][m], n_permutaciones, rng)
        n_obj[v] = int(m.sum())
    q = E.benjamini_hochberg([p_obj[v] for v in variables])
    q_obj = dict(zip(variables, map(float, q)))
    relevantes = [v for v in variables if q_obj[v] < C.ALFA_Q_35B]

    medidas = MedidasCuidados(su_obj, n_obj, p_obj, q_obj, relevantes)
    for i, a in enumerate(relevantes):
        for b in relevantes[i + 1:]:
            m = esc.mascara_de(a, b)
            rng = E.generador(base.id_analisis, 0, F.TIPO_PAR, indice[a] * F.FACTOR_PAR + indice[b])
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


def _sin_sobrecarga(medidas):
    """Vista de las medidas para las funciones congeladas. Conserva los q calculados en la familia de 31."""
    def fuera(d):
        return {k: v for k, v in d.items() if k != SOBRECARGA and SOBRECARGA not in (k if isinstance(k, tuple) else ())}
    return F.Medidas(fuera(medidas.su_objetivo), fuera(medidas.n_objetivo), fuera(medidas.p_objetivo),
                     fuera(medidas.q_objetivo), [v for v in medidas.relevantes if v != SOBRECARGA],
                     su_par=fuera(medidas.su_par), n_par=fuera(medidas.n_par), p_par=fuera(medidas.p_par),
                     q_par=fuera(medidas.q_par), su_objetivo_laboral=dict(medidas.su_objetivo_laboral))


def _decision_sobrecarga(medidas, generales, exigir_q):
    """Etapa 3: solo se puede eliminar la sobrecarga, con todas las condiciones medidas en la misma población."""
    if SOBRECARGA not in medidas.relevantes:
        return {'decision': 'no relevante', 'eliminada_por': '', 'etapa': '', 'su_y': medidas.su_objetivo[SOBRECARGA],
                'su_z': np.nan, 'su_par': np.nan, 'q_par': np.nan}
    posibles = []
    for z in generales:
        su_z, su_y = medidas.su_otra_etapa3[z], medidas.su_sobrecarga_etapa3[z]
        elimina, su_par, q_par = F._par_elimina(medidas, z, SOBRECARGA, su_y, exigir_q)
        if F._cumple(su_z, su_y) and elimina:
            posibles.append((z, su_z, su_y, su_par, q_par))
    if posibles:
        z, su_z, su_y, su_par, q_par = min(posibles, key=lambda t: (-t[1], t[0]))
        return {'decision': 'redundante', 'eliminada_por': z, 'etapa': ETAPA_CUIDADORAS, 'su_y': su_y, 'su_z': su_z,
                'su_par': su_par, 'q_par': q_par}
    return {'decision': 'seleccionada', 'eliminada_por': '', 'etapa': ETAPA_CUIDADORAS,
            'su_y': medidas.su_objetivo[SOBRECARGA], 'su_z': np.nan, 'su_par': np.nan, 'q_par': np.nan}


def seleccionar(esc, medidas, exigir_q):
    """Etapas 1 y 2 con la función congelada. La sobrecarga se evalúa al final y no elimina a nadie."""
    decisiones = F.seleccionar(esc.base, _sin_sobrecarga(medidas), exigir_q)
    decisiones[SOBRECARGA] = _decision_sobrecarga(medidas, F.seleccionadas(decisiones), exigir_q)
    return decisiones


def pares_no_eliminados_sobrecarga(medidas, decisiones):
    """Variables que la sobrecarga habría podido eliminar y que la regla de cobertura conserva. Solo se informan."""
    if SOBRECARGA not in medidas.relevantes:
        return []
    filas = []
    for z in sorted(v for v in F.seleccionadas(decisiones) if v != SOBRECARGA):
        su_z, su_s = medidas.su_otra_etapa3[z], medidas.su_sobrecarga_etapa3[z]
        elimina, su_par, q_par = F._par_elimina(medidas, SOBRECARGA, z, su_z, True)
        if elimina and F._cumple(su_s, su_z):
            filas.append({'eliminable': z, 'su_par': su_par, 'q_par': q_par, 'su_sobrecarga_severidad': su_s,
                          'su_eliminable_severidad': su_z, 'n': medidas.n_par[F._clave(z, SOBRECARGA)]})
    return filas


def controlar_etapa3(esc, medidas, decisiones):
    """Controles de la adaptación: detienen el análisis antes de escribir resultados."""
    if len(medidas.q_objetivo) != len(esc.base.candidatas) + 1:
        raise RuntimeError('La familia de relevancia no incluye a todas las candidatas.')
    if medidas.n_objetivo[SOBRECARGA] != int(esc.poblacion.sum()):
        raise RuntimeError('La relevancia de la sobrecarga no usa su población.')
    for par, n in medidas.n_par.items():
        if n != int(esc.mascara_de(*par).sum()):
            raise RuntimeError(f'{par}: el par no usa la población común.')
    for v, d in decisiones.items():
        if d['eliminada_por'] == SOBRECARGA:
            raise RuntimeError(f'La sobrecarga eliminó a {v}.')
    if decisiones[SOBRECARGA]['etapa'] not in ('', ETAPA_CUIDADORAS):
        raise RuntimeError('La sobrecarga se evaluó fuera de la Etapa 3.')


@dataclass
class Evaluacion:
    plan: Plan
    medidas: MedidasCuidados
    adaptado: dict
    estandar: dict
    no_eliminados: list
    no_eliminados_sobrecarga: list
    segundos: float = 0.0


def evaluar(esc, plan):
    t0 = time.perf_counter()
    with K.umbral(plan.parametros.alfa):
        medidas = medir(esc, plan.parametros.n_permutaciones)
        adaptado = seleccionar(esc, medidas, True)
        estandar = seleccionar(esc, medidas, False)
        generales = _sin_sobrecarga(medidas)
        for decisiones in (adaptado, estandar):
            P.controlar_seleccion(esc.base, generales, {v: d for v, d in decisiones.items() if v != SOBRECARGA})
            controlar_etapa3(esc, medidas, decisiones)
        no_eliminados = F.pares_no_eliminados(esc.base, generales, {v: d for v, d in adaptado.items() if v != SOBRECARGA})
        no_eliminados_sobrecarga = pares_no_eliminados_sobrecarga(medidas, adaptado)
    return Evaluacion(plan, medidas, adaptado, estandar, no_eliminados, no_eliminados_sobrecarga, time.perf_counter() - t0)


def iguales(a, b):
    """Coincidencia exacta de dos evaluaciones, con todos los decimales."""
    for campo in ('su_objetivo', 'n_objetivo', 'p_objetivo', 'q_objetivo', 'relevantes', 'su_par', 'n_par', 'p_par', 'q_par',
                  'su_objetivo_laboral', 'su_otra_etapa3', 'su_sobrecarga_etapa3'):
        if getattr(a.medidas, campo) != getattr(b.medidas, campo):
            return False
    return tabla_decisiones(a).equals(tabla_decisiones(b))


# --- Comparación con el análisis complementario anterior ----------------------------------------

def q_familia_30(medidas):
    """q de las 30 sin la sobrecarga, con los mismos p: separa el efecto de la familia del de la Etapa 3."""
    variables = sorted(v for v in medidas.p_objetivo if v != SOBRECARGA)
    return dict(zip(variables, map(float, E.benjamini_hochberg([medidas.p_objetivo[v] for v in variables]))))


def comprobar_referencia(ev, referencia):
    """Las 30 candidatas deben conservar exactamente su SU y su p, y los pares en común también."""
    m, nombre, errores = ev.medidas, ev.plan.referencia, []
    tabla = K._leer(referencia.csv('comparacion_con_original'))
    tabla = tabla[tabla['escenario'] == nombre].set_index('variable')
    q30 = q_familia_30(m)
    if set(tabla.index) != set(q30):
        errores.append('las candidatas')
    else:
        for v in q30:
            if tuple(tabla.loc[v, ['su', 'p', 'q']]) != (K._txt(m.su_objetivo[v]), K._txt(m.p_objetivo[v]), K._txt(q30[v])):
                errores.append(f'SU, p o q de {v}')
    pares = K._leer(referencia.csv('su_pares'))
    pares = pares[pares['escenario'] == nombre]
    for f in pares.itertuples():
        clave = (f.variable_1, f.variable_2)
        if clave in m.su_par and (str(m.n_par[clave]), K._txt(m.su_par[clave]), K._txt(m.p_par[clave])) != (f.n, f.su, f.p):
            errores.append(f'el par {clave}')
    if errores:
        raise RuntimeError(f'{ev.plan.parametros.nombre} no reproduce {nombre}: ' + '; '.join(errores))


def tabla_objetivo(esc, ev):
    m, q30 = ev.medidas, q_familia_30(ev.medidas)
    filas = []
    for v in sorted(m.su_objetivo):
        grupo = 'cuidadoras' if v == SOBRECARGA else 'laboral' if v in esc.base.laborales else 'no laboral'
        filas.append({'escenario': ev.plan.parametros.nombre, 'variable': v, 'grupo': grupo, 'n': m.n_objetivo[v],
                      'su': m.su_objetivo[v], 'p': m.p_objetivo[v], 'q_familia_31': m.q_objetivo[v],
                      'q_familia_30': q30.get(v, np.nan), 'relevante': v in m.relevantes})
    return pd.DataFrame(filas)


def tabla_pares(ev):
    m = ev.medidas
    return pd.DataFrame([{'escenario': ev.plan.parametros.nombre, 'variable_1': a, 'variable_2': b, 'n': m.n_par[(a, b)],
                          'su': m.su_par[(a, b)], 'p': m.p_par[(a, b)], 'q': m.q_par[(a, b)],
                          'supera_azar': m.q_par[(a, b)] < ev.plan.parametros.alfa} for a, b in sorted(m.su_par)],
                        columns=['escenario', *K.COLUMNAS_PARES])


def tabla_decisiones(ev):
    filas = P._tabla_decisiones(ev.adaptado, 'adaptado') + P._tabla_decisiones(ev.estandar, 'estandar')
    return pd.DataFrame(filas).assign(escenario=ev.plan.parametros.nombre)


def tabla_comparacion(evaluaciones, referencia):
    """E1, E3 y E4 tal como se guardaron, junto con las versiones nuevas: no se recalcula ni se sobrescribe nada."""
    guardada = K._leer(referencia.csv('comparacion_con_original'))
    guardada = guardada[guardada['escenario'].isin(['E1', 'E3', 'E4'])]
    filas = [{'escenario': f.escenario, 'origen': 'guardado', 'variable': f.variable, 'n': '', 'su': f.su, 'p': f.p, 'q': f.q,
              'relevante': f.relevante, 'decision_adaptado': f.decision_adaptado,
              'eliminada_por_adaptado': f.eliminada_por_adaptado, 'decision_estandar': f.decision_estandar,
              'eliminada_por_estandar': f.eliminada_por_estandar} for f in guardada.itertuples()]
    for ev in evaluaciones:
        m = ev.medidas
        for v in sorted(m.su_objetivo):
            filas.append({'escenario': ev.plan.parametros.nombre, 'origen': 'familia de 31', 'variable': v, 'n': m.n_objetivo[v],
                          'su': K._txt(m.su_objetivo[v]), 'p': K._txt(m.p_objetivo[v]), 'q': K._txt(m.q_objetivo[v]),
                          'relevante': str(v in m.relevantes), 'decision_adaptado': ev.adaptado[v]['decision'],
                          'eliminada_por_adaptado': ev.adaptado[v]['eliminada_por'],
                          'decision_estandar': ev.estandar[v]['decision'],
                          'eliminada_por_estandar': ev.estandar[v]['eliminada_por']})
    return pd.DataFrame(filas)


def tabla_efecto_familia(ev):
    """Qué cambia solo por pasar de 30 a 31 pruebas y qué cambia por agregar la sobrecarga a la selección."""
    m, alfa, q30 = ev.medidas, ev.plan.parametros.alfa, q_familia_30(ev.medidas)
    return pd.DataFrame([{'escenario': ev.plan.parametros.nombre, 'variable': v, 'p': m.p_objetivo[v], 'q_familia_30': q30[v],
                          'q_familia_31': m.q_objetivo[v], 'relevante_con_30': q30[v] < alfa,
                          'relevante_con_31': m.q_objetivo[v] < alfa,
                          'cambia_relevancia': (q30[v] < alfa) != (m.q_objetivo[v] < alfa)} for v in sorted(q30)])


def fila_resumen(ev):
    m, p = ev.medidas, ev.plan.parametros
    fila = {'escenario': p.nombre, 'funcion': p.funcion, 'poblacion_sobrecarga': ev.plan.poblacion,
            'n_sobrecarga': m.n_objetivo[SOBRECARGA], 'permutaciones': p.n_permutaciones, 'umbral_q': p.alfa,
            'familia': len(m.q_objetivo), 'q_sobrecarga': m.q_objetivo[SOBRECARGA], 'n_relevantes': len(m.relevantes),
            'relevantes': ';'.join(m.relevantes), 'n_pares': len(m.su_par)}
    for variante, decisiones in (('adaptado', ev.adaptado), ('estandar', ev.estandar)):
        fuera, lista = K.eliminadas(decisiones), F.seleccionadas(decisiones)
        fila[f'redundantes_{variante}'] = ';'.join(f'{v}<-{z}' for v, z in fuera.items())
        fila[f'n_seleccionadas_{variante}'] = len(lista)
        fila[f'seleccionadas_{variante}'] = ';'.join(lista)
    fila['decision_sobrecarga_adaptado'] = ev.adaptado[SOBRECARGA]['decision']
    fila['segundos'] = ev.segundos
    return fila


def tabla_relacion(datos, esc):
    """Las tres variables entre sí. La fila con ceros solo documenta el artefacto: nunca entra a una decisión."""
    t = datos.tabla
    n = len(t)
    sobre, cant, doble = esc.sobrecarga, t['cantidad_personas_cuida'].to_numpy(dtype=float), t['doble_carga'].to_numpy(dtype=float)
    filas = []
    for nombre, m, x in (('población de la sobrecarga', esc.poblacion, sobre),
                         ('todas, con 0 si no aplica (solo referencia)', np.ones(n, dtype=bool), np.nan_to_num(sobre))):
        for par, a, b in (('sobrecarga y cantidad', x, cant), ('sobrecarga y doble carga', x, doble),
                          ('cantidad y doble carga', cant, doble)):
            constante = np.ptp(a[m]) == 0 or np.ptp(b[m]) == 0
            filas.append({'poblacion': nombre, 'par': par, 'n': int(m.sum()),
                          'rho_spearman': np.nan if constante else stats.spearmanr(a[m], b[m])[0], 'su': E.su(a[m], b[m])})
    return pd.DataFrame(filas)


def tabla_por_nivel(datos, esc):
    """Solo personas de la población: quienes no cuidan no entran en ningún promedio."""
    t = datos.tabla[esc.poblacion].assign(sobrecarga=esc.sobrecarga[esc.poblacion])
    filas = []
    for condicion, parte in (('todas', t), ('trabaja', t[t['trabaja_actualmente'] == 1]),
                             ('no trabaja', t[t['trabaja_actualmente'] == 0])):
        for nivel, g in parte.groupby('sobrecarga'):
            filas.append({'condicion': condicion, 'nivel': int(nivel), 'n': len(g), 'severas': int(g['severo_mrs'].sum()),
                          'pct_severas': 100 * g['severo_mrs'].mean(), 'mrs_medio': g['mrs_total'].mean()})
    return pd.DataFrame(filas)


# --- Rutas, informe y registro ---------------------------------------------------------------

@dataclass(frozen=True)
class RutasCuidados:
    carpeta: Path

    def csv(self, nombre):
        return self.carpeta / f'{nombre}.csv'

    @property
    def informe(self):
        return self.carpeta / 'informe_cuidados.md'

    @property
    def log(self):
        return self.carpeta / 'log_cuidados.txt'

    def declaradas(self):
        return {self.csv(n) for n in ARCHIVOS_CSV} | {self.informe, self.log}


RUTAS_CUIDADOS = RutasCuidados(CARPETA)


def validar_separacion(rutas, referencia=K.RUTAS_COMPLEMENTARIAS):
    """Ni dentro de las salidas originales ni de las del complementario anterior, y sin sobrescribir."""
    carpeta, previa = Path(rutas.carpeta).resolve(), Path(referencia.carpeta).resolve()
    if carpeta == previa or previa in carpeta.parents:
        raise PermissionError(f'La carpeta no puede estar dentro de {previa}.')
    K.validar_separacion(rutas)


def archivos_vigilados():
    """Todo lo anterior que no puede cambiar: datasets, resultados, complementario anterior y su código."""
    anteriores = [K.PROTOCOLO, K.PRUEBAS, Path(K.__file__).resolve(), P.ANALISIS / 'informe_seleccion_fase35b.md']
    return sorted({*K.archivos_vigilados(), *K.RUTAS_COMPLEMENTARIAS.declaradas(), *anteriores, *SUCIO.parent.glob('*.csv')})


def informe(evaluaciones, conteos, tiempos):
    principal = next((ev for ev in evaluaciones if ev.plan.parametros.nombre == 'C4'), evaluaciones[-1])
    m = principal.medidas
    orden = sorted(m.su_objetivo, key=lambda v: (-m.su_objetivo[v], v))
    partes = [
        '# Módulo de cuidados. Versión complementaria exploratoria de FCBF',
        f'*Generado por `analisis/complementario_cuidados.py` el {datetime.now():%d-%m-%Y}. '
        'Protocolo: `analisis/protocolo_cuidados_35b.md`. Este informe no interpreta causalidad.*',
        '> **Análisis exploratorio y posterior a los resultados anteriores. No sustituye el resultado oficial de la Fase 35B: '
        f'0 variables seleccionadas con 5.000 permutaciones y q < 0,05 (commit `{K.COMMIT_ORIGINAL[:7]}`).**',
        '## 1. Poblaciones',
        K._tabla_md(['Población', 'n'], [[k.replace('_', ' '), v] for k, v in conteos.items()]),
        '## 2. Resultado por escenario',
        K._tabla_md(['Escenario', 'Sobrecarga', 'n', 'q <', 'q de sobrecarga', 'Decisión de sobrecarga', 'Relevantes',
                     'Seleccionadas (adaptado)', 'Seleccionadas (estándar)'],
                    [[ev.plan.parametros.nombre, ev.plan.poblacion, ev.medidas.n_objetivo[SOBRECARGA],
                      P._n(ev.plan.parametros.alfa, 2), K._p(ev.medidas.q_objetivo[SOBRECARGA]), ev.adaptado[SOBRECARGA]['decision'],
                      len(ev.medidas.relevantes), P._lista(F.seleccionadas(ev.adaptado)),
                      P._lista(F.seleccionadas(ev.estandar))] for ev in evaluaciones]),
        '## 3. Las 31 candidatas con 50.000 permutaciones y q < 0,10',
        K._tabla_md(['Variable', 'n', 'SU', 'p', 'q', 'Decisión (adaptado)'],
                    [[V.etiqueta(v), m.n_objetivo[v], P._n(m.su_objetivo[v]), K._p(m.p_objetivo[v]), K._p(m.q_objetivo[v]),
                      K._decision_corta(principal.adaptado[v])] for v in orden]),
        '## 4. Las tres variables de cuidados',
        K._tabla_md(['Variable', *[ev.plan.parametros.nombre for ev in evaluaciones]],
                    [[V.etiqueta(v), *[K._decision_corta(ev.adaptado[v]) for ev in evaluaciones]]
                     for v in ('doble_carga', 'cantidad_personas_cuida', SOBRECARGA)]),
        'Las decisiones se informan tal como resultan del método: ninguna variable se conserva ni se retira por fuera de él.',
        '## 5. Advertencias',
        '- **Posterior a los resultados:** el umbral y la incorporación de la sobrecarga se decidieron conociendo ejecuciones anteriores.',
        '- **Sobrecarga:** una SU con 239 personas no se compara directamente con una SU con 529; se lee con su n y su población.',
        '- **No aplica:** quienes no cuidan no tienen sobrecarga 0; quedan fuera de toda medición de esta variable.',
        '- **Población de la Etapa 3:** describe a quienes se identifican como cuidadoras y respondieron, no a todas las que cuidan.',
        '- **Texto de la pregunta:** menciona "su trabajo" y también se muestra a cuidadoras que no trabajan.',
        '- **`doble_carga`:** entre cuidadoras coincide con `trabaja_actualmente`; 10 de sus valores 1 dependen de `trabaja_actualmente` imputada.',
        '- **`cantidad_personas_cuida`:** 21 de sus ceros provienen de `cuida_otras_personas` imputada como "No".',
        '- **Laborales:** las 287 no son todas respuestas observadas; 263 tienen ambas preguntas observadas.',
        '- **Sin estabilidad:** no se ejecutaron remuestreos para estas selecciones.',
        '- **Carácter sintético:** refleja lo que generó el simulador, no evidencia sobre la población.',
        '- **Interpretación:** seleccionada no significa causal, y eliminada no significa irrelevante.',
        '## 6. Tiempo de ejecución',
        K._tabla_md(['Etapa', 'Segundos'], [[k, P._n(v, 1)] for k, v in tiempos.items()]),
    ]
    return '\n\n'.join(partes) + '\n'


def registro(evaluaciones, conteos, tiempos, huellas):
    lineas = ['LOG módulo de cuidados — versión complementaria EXPLORATORIA (no sustituye el resultado oficial)',
              f'Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M}', f'Commit original: {K.COMMIT_ORIGINAL}',
              f'HEAD: {P._git("rev-parse", "HEAD").strip()}',
              f'Semilla: {C.SEMILLA}; tolerancia: {C.TOLERANCIA_SU_35B}; índice de la sobrecarga: {INDICE_SOBRECARGA}; un solo proceso',
              f'Versiones: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}',
              'Poblaciones: ' + ', '.join(f'{k}={v}' for k, v in conteos.items())]
    lineas += [f'SHA-256 {nombre}: {h}' for nombre, h in huellas.items()]
    for ev in evaluaciones:
        p = ev.plan.parametros
        lineas.append(f'{p.nombre} ({ev.plan.poblacion}, {p.n_permutaciones} permutaciones, q < {p.alfa}): relevantes '
                      f'{len(ev.medidas.relevantes)}, pares {len(ev.medidas.su_par)}, adaptado [{";".join(F.seleccionadas(ev.adaptado))}], '
                      f'estandar [{";".join(F.seleccionadas(ev.estandar))}]')
    lineas.append(f'Comprobaciones: las 30 candidatas reproducen SU y p de {", ".join(sorted({ev.plan.referencia for ev in evaluaciones}))}; '
                  'dos corridas del último escenario coinciden exactamente.')
    lineas.append('Tiempo real (s): ' + ', '.join(f'{k} {v:.1f}' for k, v in tiempos.items()))
    return '\n'.join(lineas) + '\n'


# --- Flujo --------------------------------------------------------------------------------

def correr(datos, poblacion, rutas, referencia, planes=PLANES, huellas=None):
    """Calcula y comprueba todo antes de escribir: si algo falla, no queda ningún archivo."""
    inicio = time.perf_counter()
    validar_separacion(rutas, referencia)
    salida = P.Escritor(rutas)
    alfa_original = C.ALFA_Q_35B
    escenarios = {n: escenario_cuidados(datos, poblacion, n) for n in (OBSERVADAS, CUIDADORAS)}
    evaluaciones, tiempos = [], {}
    for plan in planes:
        ev = evaluar(escenarios[plan.poblacion], plan)
        comprobar_referencia(ev, referencia)
        evaluaciones.append(ev)
        tiempos[plan.parametros.nombre] = ev.segundos
    ultimo = planes[-1]
    repeticion = evaluar(escenarios[ultimo.poblacion], ultimo)
    tiempos['repeticion_ultimo_escenario'] = repeticion.segundos
    if not iguales(evaluaciones[-1], repeticion):
        raise RuntimeError('Dos corridas del último escenario no coinciden.')
    if C.ALFA_Q_35B != alfa_original:
        raise RuntimeError('El umbral original no se restauró.')

    principal = escenarios[OBSERVADAS]

    def unir(funcion):
        tablas = [t for t in (funcion(ev) for ev in evaluaciones) if len(t)]
        return pd.concat(tablas, ignore_index=True) if tablas else pd.DataFrame(columns=['escenario'])

    def con_nombre(filas, columnas):
        return lambda ev: pd.DataFrame(filas(ev), columns=columnas).assign(escenario=ev.plan.parametros.nombre)

    salida.tabla(rutas.csv('poblaciones_cuidados'), pd.DataFrame(list(poblacion.conteos.items()), columns=['poblacion', 'n']))
    salida.tabla(rutas.csv('su_objetivo'), unir(lambda ev: tabla_objetivo(escenarios[ev.plan.poblacion], ev)))
    salida.tabla(rutas.csv('su_pares'), unir(tabla_pares))
    salida.tabla(rutas.csv('decisiones_fcbf'), unir(tabla_decisiones))
    salida.tabla(rutas.csv('pares_no_eliminados_cobertura'), unir(con_nombre(lambda ev: ev.no_eliminados, K.COLUMNAS_NO_ELIMINADOS)))
    salida.tabla(rutas.csv('pares_no_eliminados_sobrecarga'),
                 unir(con_nombre(lambda ev: ev.no_eliminados_sobrecarga, COLUMNAS_NO_ELIMINADOS_SOBRECARGA)))
    salida.tabla(rutas.csv('comparacion_resultados'), tabla_comparacion(evaluaciones, referencia))
    salida.tabla(rutas.csv('efecto_familia'), unir(tabla_efecto_familia))
    salida.tabla(rutas.csv('resumen_escenarios'), pd.DataFrame([fila_resumen(ev) for ev in evaluaciones]))
    salida.tabla(rutas.csv('relacion_cuidados'), tabla_relacion(datos, principal))
    salida.tabla(rutas.csv('sobrecarga_por_nivel'), tabla_por_nivel(datos, principal))
    tiempos['total'] = time.perf_counter() - inicio
    salida.texto(rutas.informe, informe(evaluaciones, poblacion.conteos, tiempos))
    salida.texto(rutas.log, registro(evaluaciones, poblacion.conteos, tiempos, huellas or {}))
    return evaluaciones, tiempos


def correr_pruebas():
    nombres = ['preprocesamiento.test_entropia', 'preprocesamiento.test_complementario_35b',
               'preprocesamiento.test_complementario_cuidados']
    suite = unittest.defaultTestLoader.loadTestsFromNames(nombres)
    return unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite).wasSuccessful()


def construir_parser():
    parser = argparse.ArgumentParser(description='Módulo de cuidados: versión complementaria exploratoria de FCBF.')
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--verificar', action='store_true')
    modo.add_argument('--ejecutar', action='store_true')
    parser.add_argument('--autorizado-por-usuaria', action='store_true')
    return parser


def comprobar_datos_reales():
    """Solo identifica poblaciones y candidatas. No usa la severidad ni calcula ninguna SU."""
    datos, _ = P.cargar()
    problemas = comprobar_candidatas(datos)
    poblacion = cargar_poblacion(datos)
    try:
        controlar_tamanos(poblacion.conteos)
    except RuntimeError as error:
        problemas.append(str(error))
    return datos, poblacion, problemas


def main():
    args = construir_parser().parse_args()
    if args.ejecutar and not args.autorizado_por_usuaria:
        sys.exit('La ejecución requiere --autorizado-por-usuaria.')
    problemas = K.estado_inicial()
    if not correr_pruebas():
        sys.exit('Fallaron pruebas: no se ejecuta el análisis.')
    datos, poblacion, de_datos = comprobar_datos_reales()
    problemas += de_datos
    for problema in problemas:
        print(f'[FALLA] {problema}')
    if problemas:
        sys.exit('El estado inicial tiene fallas: no se ejecuta el análisis.')
    validar_separacion(RUTAS_CUIDADOS)
    for nombre, n in poblacion.conteos.items():
        print(f'{nombre}: {n}')
    if args.verificar:
        print('Pruebas, estado y tamaños correctos. No se calculó ninguna SU con los datos reales.')
        return
    huellas = {r.name: P.sha256(r) for r in (Path(__file__).resolve(), PROTOCOLO, PRUEBAS)}
    antes = P.manifiesto(archivos_vigilados())
    evaluaciones, tiempos = correr(datos, poblacion, RUTAS_CUIDADOS, K.RUTAS_COMPLEMENTARIAS, huellas=huellas)
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(archivos_vigilados()))
    if cambiados:
        sys.exit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    for ev in evaluaciones:
        print(f'{ev.plan.parametros.nombre}: {len(ev.medidas.relevantes)} relevantes; adaptado '
              f'{len(F.seleccionadas(ev.adaptado))}; estándar {len(F.seleccionadas(ev.estandar))}.')
    print(f'Total {tiempos["total"]:.1f} s. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
