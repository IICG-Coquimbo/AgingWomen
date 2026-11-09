"""
Selección de la Fase 35B: relevancia, redundancia y recorrido de FCBF.

  - `medir`: calcula SU, p y q (relevancia y pares). Es la única parte con azar.
  - `seleccionar`: recorre FCBF con esas medidas. Es determinista.
  - `un_remuestreo`: bootstrap estratificado y selección con ambas variantes.

Regla de cobertura: una variable solo puede eliminar a otra si tiene datos para
todas las personas de esa otra; por eso una laboral nunca elimina a una no laboral.
Protocolo: analisis/protocolo_fase35b.md, secciones 3 a 7.
"""
import json
import os
from dataclasses import dataclass, field, replace

import numpy as np

from . import configuracion as C
from . import entropia as E

COBERTURA, LISTA_UNICA = 'cobertura', 'lista_unica'
TIPO_BOOTSTRAP, TIPO_RELEVANCIA, TIPO_PAR = 0, 1, 2
FACTOR_PAR = 1000                 # clave de semilla de un par: índice_a * FACTOR_PAR + índice_b


@dataclass
class Escenario:
    """Datos de un análisis. `mascara` marca a las personas con respuesta laboral válida."""
    nombre: str
    id_analisis: int
    datos: dict
    objetivo: np.ndarray
    candidatas: list
    laborales: set
    mascara: np.ndarray
    modo: str = COBERTURA

    def indice(self):
        return {v: i for i, v in enumerate(sorted(self.candidatas))}


@dataclass
class Medidas:
    su_objetivo: dict
    n_objetivo: dict
    p_objetivo: dict
    q_objetivo: dict
    relevantes: list
    su_par: dict = field(default_factory=dict)
    n_par: dict = field(default_factory=dict)
    p_par: dict = field(default_factory=dict)
    q_par: dict = field(default_factory=dict)
    su_objetivo_laboral: dict = field(default_factory=dict)  # SU con la severidad entre quienes tienen respuesta laboral


def _clave(a, b):
    return tuple(sorted((a, b)))


def _usa_mascara(escenario, *variables):
    return escenario.modo == COBERTURA and any(v in escenario.laborales for v in variables)


def medir(escenario, remuestreo=0, n_permutaciones=C.N_PERMUTACIONES_35B):
    """Relevancia y pares. Cada SU con su p se calcula sobre las mismas personas."""
    indice, datos, y = escenario.indice(), escenario.datos, escenario.objetivo
    todas = np.ones(len(y), dtype=bool)
    variables = sorted(escenario.candidatas)
    su_obj, n_obj, p_obj = {}, {}, {}
    for v in variables:
        m = escenario.mascara if _usa_mascara(escenario, v) else todas
        rng = E.generador(escenario.id_analisis, remuestreo, TIPO_RELEVANCIA, indice[v])
        su_obj[v], p_obj[v] = E.prueba_permutacion(y[m], datos[v][m], n_permutaciones, rng)
        n_obj[v] = int(m.sum())
    q = E.benjamini_hochberg([p_obj[v] for v in variables])
    q_obj = dict(zip(variables, map(float, q)))
    relevantes = [v for v in variables if q_obj[v] < C.ALFA_Q_35B]

    medidas = Medidas(su_obj, n_obj, p_obj, q_obj, relevantes)
    for i, a in enumerate(relevantes):                  # orden alfabético: X = a es la que se permuta
        for b in relevantes[i + 1:]:
            m = escenario.mascara if _usa_mascara(escenario, a, b) else todas
            rng = E.generador(escenario.id_analisis, remuestreo, TIPO_PAR, indice[a] * FACTOR_PAR + indice[b])
            medidas.su_par[(a, b)], medidas.p_par[(a, b)] = E.prueba_permutacion(
                datos[a][m], datos[b][m], n_permutaciones, rng)
            medidas.n_par[(a, b)] = int(m.sum())
    pares = sorted(medidas.su_par)
    medidas.q_par = dict(zip(pares, map(float, E.benjamini_hochberg([medidas.p_par[p] for p in pares]))))

    if escenario.modo == COBERTURA and any(v in escenario.laborales for v in relevantes):
        m = escenario.mascara
        for v in relevantes:                            # todas con las mismas observaciones de la Etapa 2
            medidas.su_objetivo_laboral[v] = E.su(datos[v][m], y[m])
    return medidas


def _orden(variables, su_objetivo):
    """SU descendente con precisión completa, sin tolerancia; igualdad exacta: orden alfabético."""
    return sorted(variables, key=lambda v: (-su_objetivo[v], v))


def _cumple(su_comparada, su_referencia):
    return su_comparada >= su_referencia - C.TOLERANCIA_SU_35B


def _par_elimina(medidas, z, y, su_y, exigir_q):
    clave = _clave(z, y)
    su_par, q_par = medidas.su_par[clave], medidas.q_par[clave]
    return _cumple(su_par, su_y) and (not exigir_q or q_par < C.ALFA_Q_35B), su_par, q_par


def _recorrer_lista(variables, su_objetivo, medidas, exigir_q, etapa):
    """FCBF sobre una lista: cada variable que sigue en pie evalúa a las que están debajo."""
    orden, decisiones = _orden(variables, su_objetivo), {}
    for i, z in enumerate(orden):
        if z in decisiones:
            continue
        for y in orden[i + 1:]:
            if y in decisiones:
                continue
            elimina, su_par, q_par = _par_elimina(medidas, z, y, su_objetivo[y], exigir_q)
            if elimina:
                decisiones[y] = {'decision': 'redundante', 'eliminada_por': z, 'etapa': etapa, 'su_y': su_objetivo[y],
                                 'su_z': su_objetivo[z], 'su_par': su_par, 'q_par': q_par}
    for v in orden:
        decisiones.setdefault(v, {'decision': 'seleccionada', 'eliminada_por': '', 'etapa': etapa,
                                  'su_y': su_objetivo[v], 'su_z': np.nan, 'su_par': np.nan, 'q_par': np.nan})
    return decisiones


def _etapa_laboral(laborales, sobrevivientes, medidas, exigir_q):
    """Etapa 2: toda condición se mide con las mismas observaciones laborales. Solo se eliminan laborales."""
    su_lab = medidas.su_objetivo_laboral
    orden, decisiones, en_pie = _orden(laborales, su_lab), {}, []
    for y in orden:
        posibles = []
        for z in en_pie + list(sobrevivientes):
            elimina, su_par, q_par = _par_elimina(medidas, z, y, su_lab[y], exigir_q)
            if _cumple(su_lab[z], su_lab[y]) and elimina:
                posibles.append((z, su_par, q_par))
        if posibles:
            z, su_par, q_par = min(posibles, key=lambda t: (-su_lab[t[0]], t[0]))
            decisiones[y] = {'decision': 'redundante', 'eliminada_por': z, 'etapa': 'laboral', 'su_y': su_lab[y],
                             'su_z': su_lab[z], 'su_par': su_par, 'q_par': q_par}
        else:
            en_pie.append(y)
            decisiones[y] = {'decision': 'seleccionada', 'eliminada_por': '', 'etapa': 'laboral', 'su_y': su_lab[y],
                             'su_z': np.nan, 'su_par': np.nan, 'q_par': np.nan}
    return decisiones


def seleccionar(escenario, medidas, exigir_q):
    """Decisión de cada candidata. exigir_q=True: variante adaptada; False: estándar."""
    if escenario.modo == LISTA_UNICA:
        decisiones = _recorrer_lista(medidas.relevantes, medidas.su_objetivo, medidas, exigir_q, 'lista única')
    else:
        no_laborales = [v for v in medidas.relevantes if v not in escenario.laborales]
        laborales = [v for v in medidas.relevantes if v in escenario.laborales]
        decisiones = _recorrer_lista(no_laborales, medidas.su_objetivo, medidas, exigir_q, 'no laboral')
        sobrevivientes = [v for v in _orden(no_laborales, medidas.su_objetivo)
                          if decisiones[v]['decision'] == 'seleccionada']
        decisiones.update(_etapa_laboral(laborales, sobrevivientes, medidas, exigir_q))
    for v in escenario.candidatas:
        decisiones.setdefault(v, {'decision': 'no relevante', 'eliminada_por': '', 'etapa': '',
                                  'su_y': medidas.su_objetivo[v], 'su_z': np.nan, 'su_par': np.nan, 'q_par': np.nan})
    return decisiones


def seleccionadas(decisiones):
    return sorted(v for v, d in decisiones.items() if d['decision'] == 'seleccionada')


def pares_no_eliminados(escenario, medidas, decisiones):
    """Pares laboral-no laboral que parecen redundantes y que la regla de cobertura no permite eliminar."""
    su_lab, filas = medidas.su_objetivo_laboral, []
    laborales = [v for v in medidas.relevantes if v in escenario.laborales]
    no_laborales = [v for v in seleccionadas(decisiones) if v not in escenario.laborales]
    for l in laborales:
        for n in no_laborales:
            elimina, su_par, q_par = _par_elimina(medidas, l, n, su_lab[n], True)
            if elimina and _cumple(su_lab[l], su_lab[n]):
                filas.append({'laboral': l, 'no_laboral': n, 'su_par': su_par, 'q_par': q_par,
                              'su_laboral_severidad': su_lab[l], 'su_no_laboral_severidad': su_lab[n],
                              'n': medidas.n_par[_clave(l, n)]})
    return filas


def aplicar_indices(escenario, idx):
    return replace(escenario, datos={v: x[idx] for v, x in escenario.datos.items()},
                   objetivo=escenario.objetivo[idx], mascara=escenario.mascara[idx])


def indices_bootstrap(objetivo, rng):
    """Con reemplazo dentro de cada clase del objetivo, manteniendo el tamaño de cada una."""
    return np.concatenate([rng.choice(np.flatnonzero(objetivo == k), int((objetivo == k).sum()), replace=True)
                           for k in np.unique(objetivo)])


def un_remuestreo(escenario, i, n_permutaciones, carpeta_cache=None):
    """Un remuestreo con ambas variantes. Si ya está en la caché, no se recalcula."""
    ruta = os.path.join(carpeta_cache, f'rem_{i:04d}.json') if carpeta_cache else None
    if ruta and os.path.exists(ruta):
        with open(ruta, encoding='utf-8') as f:
            return json.load(f)
    rng = E.generador(escenario.id_analisis, i, TIPO_BOOTSTRAP)
    muestra = aplicar_indices(escenario, indices_bootstrap(escenario.objetivo, rng))
    medidas = medir(muestra, i, n_permutaciones)
    resultado = {'remuestreo': i, 'n_laboral': int(muestra.mascara.sum())}
    for nombre, exigir_q in (('adaptado', True), ('estandar', False)):
        decisiones = seleccionar(muestra, medidas, exigir_q)
        resultado[nombre] = {v: [d['decision'], d['eliminada_por']] for v, d in decisiones.items()}
    if ruta:
        temporal = f'{ruta}.{os.getpid()}.tmp'
        with open(temporal, 'w', encoding='utf-8') as f:
            json.dump(resultado, f)
        os.replace(temporal, ruta)
    return resultado
