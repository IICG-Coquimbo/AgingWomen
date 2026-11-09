"""
Revisión EXPLORATORIA e informativa de la Fase 35B según la reunión del 03-11-2026: entropía de Shannon, información
mutua, Symmetrical Uncertainty, 10.000 permutaciones, Benjamini-Hochberg con q < 0,10, FCBF informativo y dirección.
Protocolo: analisis/reunion_2026-11-03/protocolo_revision_35b.md.

Uso, desde analisis/:
    python revision_35b_reunion_1103.py --verificar     pruebas, estado y tamaños; no calcula ninguna SU real
    python revision_35b_reunion_1103.py --ejecutar --autorizado-por-usuaria

Solo admite 10.000 permutaciones: 50.000 requiere otra autorización expresa. No elimina variables de la Fase 36.
Reutiliza las funciones congeladas de las fases anteriores sin modificarlas. No genera ningún dataset.
"""
import argparse
import sys
import time
import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import normalized_mutual_info_score

import complementario_cuidados as M
import complementario_fase35b as K
import seleccionar_fase35b as P
from eda import variables as V
from preprocesamiento import configuracion as C
from preprocesamiento import entropia as E
from preprocesamiento import fcbf as F

SOBRECARGA = M.SOBRECARGA
ID_REVISION = 1103                 # corriente de semillas propia, fijada antes de calcular
N_PERMUTACIONES = 10000
ALFA = 0.10
ALFA_REFERENCIA = 0.05
N_BOOTSTRAP, N_SORTEOS_MC, N_MINIMO_CATEGORIA = 2000, 20000, 10
TIPO_BOOTSTRAP_RHO, TIPO_MONTE_CARLO, TIPO_SENSIBILIDAD = 3, 4, 5
TOLERANCIA_INDEPENDIENTE = 1e-10
CARPETA = P.ANALISIS / 'reunion_2026-11-03'
SALIDA = CARPETA / 'permutaciones_10000'
PROTOCOLO = CARPETA / 'protocolo_revision_35b.md'
PRUEBAS = P.ANALISIS / 'preprocesamiento' / 'test_revision_35b.py'
ARCHIVOS_CSV = ['poblaciones', 'orientacion_escalas', 'shannon_componentes', 'relevancia_34', 'incertidumbre_monte_carlo',
                'pares_relevantes', 'decisiones_fcbf', 'pares_no_eliminados', 'su_todas_las_parejas', 'direccion_resumen',
                'direccion_categorias', 'comparacion_anteriores', 'sensibilidades']
TAMANOS = {'general': 529, 'laboral': 287, 'cuidadoras_observadas': 239}

CONTROLES_ANTIGUOS = ['edad', 'imc', 'trabaja_actualmente', 'usa_medicamentos_diabetes']
VARIABLES_34 = sorted([
    *CONTROLES_ANTIGUOS, 'alcohol_frecuencia', 'cantidad_personas_cuida', 'carnes_semana', 'dias_ejercicio_semana',
    'distension_abdominal', 'estres_entorno_laboral', 'evacuacion_intestinal', 'falta_tiempo_influye',
    'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_comida_fuera', 'frecuencia_fuerza', 'frutas_dia',
    'golosinas_semana', 'horas_sedentarismo', 'jugos_gaseosas_dia', 'lacteos_dia', 'legumbres_semana',
    'lugar_trabajo_comprensivo', 'operada_no_mas_hijos', 'panes_dia', 'pescado_semana', 'platos_verduras_dia',
    'quien_prepara_comidas', SOBRECARGA, 'tabaco_frecuencia', 'tiene_actividad_sexual', 'tiene_pareja',
    'usa_medicamentos_presion', 'vasos_agua_dia'])

# --- Orientación de las escalas, comprobada contra src/apps/encuestas/models.py en las pruebas ---------------
SI_NO = {0: 'No', 1: 'Sí'}
SEMANAL = {1: 'Nunca', 2: '1-2 veces por semana', 3: '3-4 veces por semana', 4: '5-6 veces por semana', 5: 'Diariamente'}
PORCIONES = {1: 'No consumo', 2: '1-2 porciones', 3: '3-4 porciones', 4: '5-6 porciones', 5: '7 o más porciones'}
SUBJETIVA = {1: 'Nunca o casi nunca', 2: 'Rara vez', 3: 'A veces', 4: 'Frecuentemente', 5: 'Siempre'}
FRECUENCIA = {0: 'No lo realiza', 2: 'Rara vez', 3: 'A veces', 4: 'Frecuentemente', 5: 'Siempre'}
ACUERDO = {1: 'Muy en desacuerdo', 2: 'En desacuerdo', 3: 'Neutral', 4: 'De acuerdo', 5: 'Muy de acuerdo'}
ESTRES = {1: 'Nada de estrés', 2: 'Estrés leve', 3: 'Estrés moderado', 4: 'Estrés alto', 5: 'Estrés extremo'}
EVACUACION = {1: 'Más de una vez al día', 2: '1 vez al día', 3: 'Cada 2 días', 4: '3 o más días entre evacuaciones'}
DISTENSION = {1: 'Nunca o casi nunca', 2: 'A veces', 3: 'Frecuentemente', 4: 'Siempre'}
CANTIDAD = {0: 'No cuida', 1: '1 persona', 2: '2 personas', 3: '3 o más personas'}
DIAS = {1: '0 días', 2: '1-2 días', 3: '3-4 días', 4: '5-6 días', 5: 'Todos los días'}
TRAMOS_EDAD = {1: '36-39', 2: '40-44', 3: '45-49', 4: '50-54', 5: '55-59', 6: '60-65'}
TRAMOS_IMC = {0: '< 18,5', 1: '18,5-24,9', 2: '25-29,9', 3: '30-34,9', 4: '35-39,9', 5: '>= 40'}
TRAMOS_HORAS = {0: '<= 5', 1: '> 5 a 6', 2: '> 6 a 8', 3: '> 8'}


@dataclass(frozen=True)
class Escala:
    tipo: str
    niveles: dict
    mayor_valor: str             # qué significa un valor mayor: de aquí se lee el signo
    clase_models: str = ''       # clase de choices en models.py; vacía si no aplica


ORIENTACION = {
    'edad': Escala('continua', TRAMOS_EDAD, 'mayor edad'),
    'imc': Escala('continua', TRAMOS_IMC, 'mayor IMC'),
    'horas_sedentarismo': Escala('continua', TRAMOS_HORAS, 'más horas sentada al día'),
    'usa_medicamentos_diabetes': Escala('binaria', SI_NO, 'usa medicamentos para la diabetes', 'RespuestaSiNo'),
    'usa_medicamentos_presion': Escala('binaria', SI_NO, 'usa medicamentos para la presión', 'RespuestaSiNo'),
    'trabaja_actualmente': Escala('binaria', SI_NO, 'trabaja actualmente'),
    'tiene_pareja': Escala('binaria', SI_NO, 'tiene pareja', 'RespuestaSiNo'),
    'tiene_actividad_sexual': Escala('binaria', SI_NO, 'tiene actividad sexual', 'RespuestaSiNo'),
    'operada_no_mas_hijos': Escala('binaria', SI_NO, 'operada para no tener más hijos', 'RespuestaSiNo'),
    'evacuacion_intestinal': Escala('ordinal', EVACUACION, 'evacuaciones MENOS frecuentes (escala inversa a la frecuencia)',
                                    'FrecuenciaEvacuacionIntestinal'),
    'distension_abdominal': Escala('ordinal', DISTENSION, 'distensión abdominal más frecuente', 'FrecuenciaDistensionAbdominal'),
    'lugar_trabajo_comprensivo': Escala('ordinal', ACUERDO, 'lugar de trabajo percibido como más comprensivo', 'EscalaAcuerdo'),
    'estres_entorno_laboral': Escala('ordinal', ESTRES, 'más estrés del entorno laboral', 'EscalaEstresLaboral'),
    'cantidad_personas_cuida': Escala('ordinal', CANTIDAD, 'más personas cuidadas (0 = no cuida)', 'CantidadPersonasCuidado'),
    SOBRECARGA: Escala('ordinal', SUBJETIVA, 'sobrecarga más frecuente', 'EscalaFrecuenciaSubjetiva'),
    'dias_ejercicio_semana': Escala('ordinal', DIAS, 'más días de ejercicio a la semana (1 = 0 días)', 'DiasEjercicioSemana'),
    'frecuencia_aerobico': Escala('ordinal', FRECUENCIA, 'ejercicio aeróbico más frecuente (0 = no lo realiza)', 'EscalaFrecuencia'),
    'frecuencia_bajo_impacto': Escala('ordinal', FRECUENCIA, 'ejercicio de bajo impacto más frecuente (0 = no lo realiza)',
                                      'EscalaFrecuencia'),
    'frecuencia_fuerza': Escala('ordinal', FRECUENCIA, 'ejercicio de fuerza más frecuente (0 = no lo realiza)', 'EscalaFrecuencia'),
    'frecuencia_comida_fuera': Escala('ordinal', SEMANAL, 'más comidas preparadas fuera del hogar', 'EscalaFrecuenciaSemanal'),
    'falta_tiempo_influye': Escala('ordinal', SUBJETIVA, 'la falta de tiempo influye más en la alimentación',
                                   'EscalaFrecuenciaSubjetiva'),
    'vasos_agua_dia': Escala('ordinal', PORCIONES, 'más vasos de agua al día', 'EscalaPorciones'),
    'platos_verduras_dia': Escala('ordinal', PORCIONES, 'más platos de verduras al día', 'EscalaPorciones'),
    'frutas_dia': Escala('ordinal', PORCIONES, 'más frutas al día', 'EscalaPorciones'),
    'panes_dia': Escala('ordinal', PORCIONES, 'más panes al día', 'EscalaPorciones'),
    'lacteos_dia': Escala('ordinal', PORCIONES, 'más lácteos al día', 'EscalaPorciones'),
    'jugos_gaseosas_dia': Escala('ordinal', PORCIONES, 'más jugos o gaseosas al día', 'EscalaPorciones'),
    'pescado_semana': Escala('ordinal', SEMANAL, 'más pescado a la semana', 'EscalaFrecuenciaSemanal'),
    'legumbres_semana': Escala('ordinal', SEMANAL, 'más legumbres a la semana', 'EscalaFrecuenciaSemanal'),
    'carnes_semana': Escala('ordinal', SEMANAL, 'más carnes a la semana', 'EscalaFrecuenciaSemanal'),
    'golosinas_semana': Escala('ordinal', SEMANAL, 'más golosinas a la semana', 'EscalaFrecuenciaSemanal'),
    'tabaco_frecuencia': Escala('ordinal', SEMANAL, 'fuma con mayor frecuencia', 'EscalaFrecuenciaSemanal'),
    'alcohol_frecuencia': Escala('ordinal', SEMANAL, 'consume alcohol con mayor frecuencia', 'EscalaFrecuenciaSemanal'),
    'quien_prepara_comidas': Escala('nominal', {}, 'sin orden: no tiene signo', 'QuienPreparaComidas'),
}


# --- Entropía de Shannon: nombres explícitos sobre la implementación congelada ------------------------------

def entropia_shannon(x):
    """H(X) = -Σ p(x) log2 p(x), en bits. Variable constante: 0."""
    return E.entropia(x)


def entropia_conjunta_shannon(x, y):
    """H(X,Y) = -Σ p(x,y) log2 p(x,y), en bits."""
    x, y = E.codificar(x), E.codificar(y)
    return E.entropia(x * (y.max() + 1) + y)


def informacion_mutua(x, y):
    """I(X;Y) = H(X) + H(Y) - H(X,Y), en bits."""
    return entropia_shannon(x) + entropia_shannon(y) - entropia_conjunta_shannon(x, y)


def symmetrical_uncertainty(x, y):
    """SU(X,Y) = 2·I(X;Y) / [H(X) + H(Y)], la misma función congelada usada desde la Fase 35B."""
    return E.su(x, y)


def su_independiente(x, y):
    """Misma medida por otra vía: información mutua normalizada de scikit-learn con media aritmética."""
    x, y = E.codificar(x), E.codificar(y)
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        return 0.0
    return float(normalized_mutual_info_score(x, y, average_method='arithmetic'))


def componentes(x, y):
    hx, hy, hxy = entropia_shannon(x), entropia_shannon(y), entropia_conjunta_shannon(x, y)
    return {'k_categorias': len(np.unique(x)), 'h_x': hx, 'h_severidad': hy, 'h_conjunta': hxy, 'informacion_mutua': hx + hy - hxy,
            'su': symmetrical_uncertainty(x, y)}


# --- Escenario de 34 variables ------------------------------------------------------------------------------

@dataclass
class EscenarioRevision(M.EscenarioCuidados):
    """Las medidas y etapas de cuidados, con índice alfabético entre todas las variables."""

    def __post_init__(self):
        x, m = np.asarray(self.sobrecarga, dtype=float), np.asarray(self.poblacion, dtype=bool)
        if SOBRECARGA in self.base.candidatas or SOBRECARGA in self.base.laborales:
            raise ValueError('La sobrecarga no puede ser una candidata de las etapas 1 y 2.')
        if len(x) != len(self.base.objetivo) or len(m) != len(x) or not m.any():
            raise ValueError('La población de la sobrecarga no corresponde a los datos.')
        if not np.isin(x[m], M.ESCALA).all():
            raise ValueError('Dentro de la población, la sobrecarga debe estar observada en la escala 1 a 5.')
        if not np.isnan(x[~m]).all():
            raise ValueError('Fuera de la población, la sobrecarga debe quedar vacía: no aplica no es cero.')

    def indice(self):
        return {v: i for i, v in enumerate(sorted([*self.base.candidatas, SOBRECARGA]))}


def lista_base(datos):
    """Candidatas actualizadas y antiguas de control, sin `doble_carga` ni `prevision`; la sobrecarga va aparte."""
    return sorted({*datos.candidatas, *C.CONTROL_35B} - {'doble_carga', 'prevision'})


def comprobar_lista(variables):
    """Lista cerrada del protocolo."""
    problemas = []
    if sorted(variables) != VARIABLES_34:
        problemas.append(f'La lista no son las 34 acordadas: {sorted(set(variables) ^ set(VARIABLES_34))}')
    prohibidas = set(variables) & ({'doble_carga', 'prevision'} | set(C.PROHIBIDAS))
    if prohibidas:
        problemas.append(f'Variables excluidas en la lista: {sorted(prohibidas)}')
    if set(variables) != set(ORIENTACION):
        problemas.append('La orientación de las escalas no cubre exactamente las variables.')
    return problemas


def codigos_su(tabla, variables):
    """Discretización fijada para SU: los valores originales no se tocan."""
    t, codigos = tabla, {}
    for v in variables:
        if v == 'edad':
            codigos[v] = E.tramos_cerrados_izquierda(t[v], C.CORTES_EDAD_35B)
        elif v == 'imc':
            codigos[v] = E.tramos_cerrados_izquierda(t[v], C.CORTES_IMC_35B)
        elif v == 'horas_sedentarismo':
            codigos[v] = E.tramos_cerrados_derecha(t[v], P.cortes_cuartiles(t[v]))
        else:
            codigos[v] = E.codificar(t[v])
    return codigos


def construir_escenario(datos, poblacion):
    variables = lista_base(datos)
    base = F.Escenario('Revision 03-11', ID_REVISION, codigos_su(datos.tabla, variables), E.codificar(datos.tabla['severo_mrs']),
                       variables, set(datos.laborales), datos.mascara)
    m = poblacion.observada
    return EscenarioRevision(base, np.where(m, poblacion.valores, np.nan), m, M.OBSERVADAS)


def poblacion_de(esc, v):
    return 'cuidadoras' if v == SOBRECARGA else 'laboral' if v in esc.base.laborales else 'general'


def comprobar_tamanos(esc, esperados=None):
    esperados = TAMANOS if esperados is None else esperados
    actuales = {'general': len(esc.base.objetivo), 'laboral': int(esc.base.mascara.sum()),
                'cuidadoras_observadas': int(esc.poblacion.sum())}
    return [] if actuales == esperados else [f'Tamaños (esperado, actual): {esperados}, {actuales}']


# --- Valores de cada persona para la dirección ---------------------------------------------------------------

def valores_originales(datos, esc, v):
    """Valores sin discretizar y personas de la población de la variable."""
    m = esc.mascara_de(v)
    if v == SOBRECARGA:
        return esc.sobrecarga, m
    return datos.tabla[v].to_numpy(), m


def excedencias(p, n_permutaciones):
    """k desde p = (1 + k) / (N + 1). Falla si p no corresponde a un conteo entero."""
    k = np.asarray(p, dtype=float) * (n_permutaciones + 1) - 1
    if np.abs(k - np.round(k)).max(initial=0) > 1e-6:
        raise RuntimeError('Un valor p no corresponde a un conteo entero de permutaciones.')
    return np.round(k).astype(int)


# --- Incertidumbre Monte Carlo: sección 7 del protocolo ------------------------------------------------------

def incertidumbre_mc(k, n_permutaciones, rng, sorteos=N_SORTEOS_MC, umbral=ALFA):
    """Propaga el error de cada p por BH: posterior de Jeffreys independiente por variable."""
    k = np.asarray(k, dtype=float)
    a, b = k + 0.5, n_permutaciones - k + 0.5
    muestras = rng.beta(a, b, size=(sorteos, len(k)))
    q = stats.false_discovery_control(muestras, method='bh', axis=1)
    return pd.DataFrame({
        'error_estandar_p': np.sqrt(a * b / ((a + b) ** 2 * (a + b + 1))),
        'p_mc_inferior': stats.beta.ppf(0.025, a, b), 'p_mc_superior': stats.beta.ppf(0.975, a, b),
        'q_mc_inferior': np.percentile(q, 2.5, axis=0), 'q_mc_superior': np.percentile(q, 97.5, axis=0),
        'prob_q_bajo_umbral': (q < umbral).mean(axis=0)})


def es_cercana(q_inferior, q_superior, umbral=ALFA):
    """Cercana: el intervalo de Monte Carlo al 95 % de q contiene el umbral."""
    return (np.asarray(q_inferior) <= umbral) & (np.asarray(q_superior) >= umbral)


def recomendar(cercanas, inestabilidades):
    """Regla predefinida. No considera qué variables se esperaban."""
    motivos = []
    if len(cercanas):
        motivos.append('variables cuyo intervalo de Monte Carlo de q contiene 0,10: ' + ', '.join(cercanas))
    if len(inestabilidades):
        motivos.append('inestabilidad numérica: ' + '; '.join(inestabilidades))
    return {'recomendar_50000': bool(motivos), 'motivos': motivos}


# --- Dirección: sección 6 del protocolo ---------------------------------------------------------------------

def wilson(exitos, n, nivel=0.95):
    z = stats.norm.ppf(0.5 + nivel / 2)
    p = exitos / n
    centro, ancho = (p + z ** 2 / (2 * n)) / (1 + z ** 2 / n), z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / (1 + z ** 2 / n)
    return max(0.0, centro - ancho), min(1.0, centro + ancho)


def newcombe(e1, n1, e2, n2):
    """IC 95 % de p2 - p1, método híbrido de Wilson."""
    p1, p2 = e1 / n1, e2 / n2
    l1, u1, l2, u2 = *wilson(e1, n1), *wilson(e2, n2)
    d = p2 - p1
    return d - np.sqrt((p2 - l2) ** 2 + (u1 - p1) ** 2), d + np.sqrt((u2 - p2) ** 2 + (p1 - l1) ** 2)


def welch(a, b):
    """Diferencia b - a con IC 95 % de Welch."""
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    d, ee = b.mean() - a.mean(), np.sqrt(va + vb)
    gl = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    margen = stats.t.ppf(0.975, gl) * ee
    return d, d - margen, d + margen


def ic_rho_bootstrap(x, y, rng, remuestreos=N_BOOTSTRAP):
    """Percentil pareado. Un remuestreo con una variable constante se descarta."""
    n = len(x)
    i = rng.integers(0, n, size=(remuestreos, n))
    a, b = stats.rankdata(x[i], axis=1), stats.rankdata(y[i], axis=1)
    a, b = a - a.mean(axis=1, keepdims=True), b - b.mean(axis=1, keepdims=True)
    den = np.sqrt((a ** 2).sum(axis=1) * (b ** 2).sum(axis=1))
    with np.errstate(divide='ignore', invalid='ignore'):
        rho = (a * b).sum(axis=1) / den
    return tuple(np.nanpercentile(rho, [2.5, 97.5]))


def clasificar_direccion(tipo, ic_inferior, ic_superior, rho_severo, p_kw):
    kw = pd.notna(p_kw) and p_kw < 0.05
    if tipo == 'nominal':
        return 'mixta' if kw else 'poco clara'
    if ic_inferior > 0:
        return 'positiva' if rho_severo > 0 else 'mixta'
    if ic_superior < 0:
        return 'negativa' if rho_severo < 0 else 'mixta'
    return 'mixta' if kw else 'poco clara'


def clasificar_factor(direccion, q_su, q_rho, umbral=ALFA):
    orientada = direccion in ('positiva', 'negativa')
    factor = {'positiva': 'riesgo', 'negativa': 'protección'}.get(direccion, '')
    if q_su < umbral:
        return f'Posible factor de {factor}' if orientada else 'Asociación sin dirección clara'
    if orientada and pd.notna(q_rho) and q_rho < umbral:
        return f'Indicio de {factor} (solo orden)'
    return 'Sin respaldo tras la corrección'


def _categorias_de(v, x, codigos):
    """Etiquetas por persona: tramos para las continuas y categorías originales para el resto."""
    niveles = ORIENTACION[v].niveles
    if ORIENTACION[v].tipo == 'continua':
        return codigos, niveles
    if ORIENTACION[v].tipo == 'nominal':
        return x, {c: c for c in sorted(set(x))}
    return x.astype(int), niveles


def direccion_variable(v, x, mrs, severo, codigos, rng):
    """Una fila de resumen y las filas por categoría. Todo dentro de la población de la variable."""
    escala = ORIENTACION[v]
    grupos, niveles = _categorias_de(v, x, codigos)
    categorias = []
    for c in sorted(set(grupos.tolist()), key=str):
        mask = grupos == c
        g, s = mrs[mask], severo[mask]
        e_lo, e_hi = wilson(int(s.sum()), len(s))
        margen = stats.t.ppf(0.975, len(g) - 1) * g.std(ddof=1) / np.sqrt(len(g)) if len(g) > 1 else np.nan
        categorias.append({'variable': v, 'valor': c, 'categoria': niveles.get(c, str(c)), 'n': int(mask.sum()),
                           'mrs_medio': g.mean(), 'mrs_ic95_inferior': g.mean() - margen, 'mrs_ic95_superior': g.mean() + margen,
                           'mrs_mediana': np.median(g), 'mrs_q1': np.percentile(g, 25), 'mrs_q3': np.percentile(g, 75),
                           'severas': int(s.sum()), 'pct_severas': 100 * s.mean(), 'pct_ic95_inferior': 100 * e_lo,
                           'pct_ic95_superior': 100 * e_hi})
    muestras = [mrs[grupos == c] for c in sorted(set(grupos.tolist()), key=str)]
    h, p_kw = stats.kruskal(*muestras) if len(muestras) > 1 else (np.nan, np.nan)
    fila = {'variable': v, 'tipo': escala.tipo, 'n': len(mrs), 'mayor_valor': escala.mayor_valor, 'kw_h': h, 'kw_p': p_kw,
            'epsilon2': h / (len(mrs) - 1) if pd.notna(h) else np.nan, 'rho_mrs': np.nan, 'rho_p': np.nan, 'rho_ic95_inferior': np.nan,
            'rho_ic95_superior': np.nan, 'rho_severo': np.nan, 'cat_baja': '', 'cat_alta': '', 'dif_mrs': np.nan,
            'dif_mrs_ic_inferior': np.nan, 'dif_mrs_ic_superior': np.nan, 'dif_pct_severas': np.nan,
            'dif_pct_ic_inferior': np.nan, 'dif_pct_ic_superior': np.nan}
    if escala.tipo != 'nominal':
        z = np.asarray(x, dtype=float)
        rho, p_rho = stats.spearmanr(z, mrs)
        fila.update(rho_mrs=rho, rho_p=p_rho, rho_severo=stats.spearmanr(z, severo)[0])
        fila['rho_ic95_inferior'], fila['rho_ic95_superior'] = ic_rho_bootstrap(z, mrs, rng)
        suficientes = [c for c in categorias if c['n'] >= N_MINIMO_CATEGORIA]
        if len(suficientes) >= 2:
            baja, alta = suficientes[0], suficientes[-1]
            d, li, ls = welch(mrs[grupos == baja['valor']], mrs[grupos == alta['valor']])
            pl, ps = newcombe(baja['severas'], baja['n'], alta['severas'], alta['n'])
            fila.update(cat_baja=baja['categoria'], cat_alta=alta['categoria'], dif_mrs=d, dif_mrs_ic_inferior=li,
                        dif_mrs_ic_superior=ls, dif_pct_severas=alta['pct_severas'] - baja['pct_severas'],
                        dif_pct_ic_inferior=100 * pl, dif_pct_ic_superior=100 * ps)
    fila['direccion'] = clasificar_direccion(escala.tipo, fila['rho_ic95_inferior'], fila['rho_ic95_superior'], fila['rho_severo'], p_kw)
    return fila, categorias


def tabla_direccion(datos, esc):
    t = datos.tabla
    indice = esc.indice()
    mrs, severo = t['mrs_total'].to_numpy(dtype=float), t['severo_mrs'].to_numpy(dtype=int)
    codigos = esc.datos()
    resumen, categorias = [], []
    for v in sorted(indice):
        x, m = valores_originales(datos, esc, v)
        rng = E.generador(ID_REVISION, 0, TIPO_BOOTSTRAP_RHO, indice[v])
        fila, cats = direccion_variable(v, x[m], mrs[m], severo[m], np.asarray(codigos[v])[m], rng)
        resumen.append(fila)
        categorias += cats
    resumen = pd.DataFrame(resumen)
    con_signo = resumen['rho_p'].notna()
    resumen['rho_q'] = np.nan
    resumen.loc[con_signo, 'rho_q'] = E.benjamini_hochberg(resumen.loc[con_signo, 'rho_p'].to_numpy())
    return resumen, pd.DataFrame(categorias)


# --- Tablas de resultados -----------------------------------------------------------------------------------

def tabla_shannon(esc):
    filas, y = [], esc.base.objetivo
    for v in sorted(esc.indice()):
        m = esc.mascara_de(v)
        filas.append({'variable': v, 'poblacion': poblacion_de(esc, v), 'n': int(m.sum()), **componentes(esc.datos()[v][m], y[m])})
    return pd.DataFrame(filas)


def tabla_relevancia(esc, ev):
    """Las 34 variables, con los q de la familia y los de las 30 candidatas sin las antiguas de control."""
    m = ev.medidas
    variables = sorted(m.su_objetivo)
    k = excedencias([m.p_objetivo[v] for v in variables], ev.plan.parametros.n_permutaciones)
    candidatas = [v for v in variables if v not in CONTROLES_ANTIGUOS]
    q30 = dict(zip(candidatas, map(float, E.benjamini_hochberg([m.p_objetivo[v] for v in candidatas]))))
    return pd.DataFrame([{'variable': v, 'poblacion': poblacion_de(esc, v), 'n': m.n_objetivo[v], 'su': m.su_objetivo[v], 'k': int(i),
                          'p': m.p_objetivo[v], 'q': m.q_objetivo[v], 'q_bajo_0_10': m.q_objetivo[v] < ALFA,
                          'q_bajo_0_05': m.q_objetivo[v] < ALFA_REFERENCIA, 'q_familia_30': q30.get(v, np.nan),
                          'antigua_control': v in CONTROLES_ANTIGUOS} for v, i in zip(variables, k)])


def tabla_monte_carlo(relevancia, n_permutaciones=N_PERMUTACIONES):
    k = relevancia['k'].to_numpy()
    actual = incertidumbre_mc(k, n_permutaciones, E.generador(ID_REVISION, 0, TIPO_MONTE_CARLO, 0))
    escalado = np.round((k + 0.5) * (50000 / n_permutaciones) - 0.5)   # misma proporción, con la precisión de 50.000
    proy = incertidumbre_mc(escalado, 50000, E.generador(ID_REVISION, 0, TIPO_MONTE_CARLO, 1))
    t = pd.concat([relevancia[['variable', 'k', 'p', 'q']], actual], axis=1)
    t['cercana'] = es_cercana(t['q_mc_inferior'], t['q_mc_superior'])
    t['q_mc_inferior_proyectado_50000'] = proy['q_mc_inferior']
    t['q_mc_superior_proyectado_50000'] = proy['q_mc_superior']
    t['error_estandar_p_proyectado_50000'] = proy['error_estandar_p']
    return t


def tabla_todas_las_parejas(esc):
    d, variables, filas = esc.datos(), sorted(esc.indice()), []
    for i, a in enumerate(variables):
        for b in variables[i + 1:]:
            m = esc.mascara_de(a, b)
            filas.append({'variable_1': a, 'variable_2': b, 'n': int(m.sum()), 'su': E.su(d[a][m], d[b][m])})
    return pd.DataFrame(filas).sort_values(['su', 'variable_1', 'variable_2'], ascending=[False, True, True], ignore_index=True)


def tabla_no_eliminados(ev):
    filas = [{'tipo': 'laboral sobre general', 'conserva': f['no_laboral'], 'podria_eliminar': f['laboral'], 'su_par': f['su_par'],
              'q_par': f['q_par'], 'n': f['n']} for f in ev.no_eliminados]
    filas += [{'tipo': 'sobrecarga sobre otra', 'conserva': f['eliminable'], 'podria_eliminar': SOBRECARGA, 'su_par': f['su_par'],
               'q_par': f['q_par'], 'n': f['n']} for f in ev.no_eliminados_sobrecarga]
    return pd.DataFrame(filas, columns=['tipo', 'conserva', 'podria_eliminar', 'su_par', 'q_par', 'n'])


def _q_reemplazando(p_familia, variable, p_nuevo):
    variables = sorted(p_familia)
    valores = [p_nuevo if v == variable else p_familia[v] for v in variables]
    return dict(zip(variables, map(float, E.benjamini_hochberg(valores))))[variable]


def tabla_sensibilidades(datos, esc, poblacion, ev):
    """Fuera de la familia: no cambian ningún resultado principal."""
    y, indice, filas = esc.base.objetivo, esc.indice(), []
    observado = datos.tabla['imc_fue_imputado'].to_numpy() == 0
    casos = [('imc', 'solo observados', esc.datos()['imc'], observado),
             (SOBRECARGA, 'cuidadoras, con 12 imputadas', np.where(poblacion.cuidadora, poblacion.valores, np.nan), poblacion.cuidadora)]
    for v, nombre, x, m in casos:
        rng = E.generador(ID_REVISION, 0, TIPO_SENSIBILIDAD, indice[v])
        su, p = E.prueba_permutacion(y[m], x[m], ev.plan.parametros.n_permutaciones, rng)
        z = datos.tabla[v].to_numpy(dtype=float) if v == 'imc' else x
        rho = stats.spearmanr(z[m], datos.tabla['mrs_total'].to_numpy(dtype=float)[m])[0]
        filas.append({'variable': v, 'version': nombre, 'n': int(m.sum()), 'su': su, 'p': p,
                      'q_al_reemplazar': _q_reemplazando(ev.medidas.p_objetivo, v, p), 'rho_mrs': rho})
    return pd.DataFrame(filas)


# --- Comparación con los resultados guardados ------------------------------------------------------------------

def leer_anteriores(oficial=P.RUTAS_REALES, previas=K.RUTAS_COMPLEMENTARIAS, cuidados=M.RUTAS_CUIDADOS):
    return {'oficial': K._leer(oficial.csv('su_objetivo')), 'previas': K._leer(previas.csv('comparacion_con_original')),
            'cuidados': K._leer(cuidados.csv('su_objetivo'))}


def _float(x):
    return float(x) if x not in ('', None) else np.nan


def su_guardadas(anteriores):
    """SU guardadas con 6 decimales: 29 comunes y sobrecarga en cuidados; las antiguas de control en el oficial."""
    c = anteriores['cuidados']
    guardadas = {f.variable: f.su for f in c[c['escenario'] == 'C4'].itertuples() if f.variable != 'doble_carga'}
    o = anteriores['oficial']
    for v in CONTROLES_ANTIGUOS:
        guardadas[v] = o[(o['variable'] == v) & (o['nota'] == 'descriptiva; no decide')]['su'].iloc[0]
    return guardadas


def comprobar_su(medidas, guardadas):
    """SU no depende de la semilla: debe coincidir con lo guardado en todas las variables."""
    if set(guardadas) != set(medidas.su_objetivo):
        return [f'Variables distintas de las guardadas: {sorted(set(guardadas) ^ set(medidas.su_objetivo))}']
    return [f'SU de {v} no coincide con la guardada' for v, s in sorted(guardadas.items()) if K._txt(medidas.su_objetivo[v]) != s]


def comprobar_independiente(esc):
    """Inestabilidad numérica: SU frente a una implementación independiente."""
    d, y, problemas = esc.datos(), esc.base.objetivo, []
    for v in sorted(esc.indice()):
        m = esc.mascara_de(v)
        if abs(symmetrical_uncertainty(d[v][m], y[m]) - su_independiente(d[v][m], y[m])) > TOLERANCIA_INDEPENDIENTE:
            problemas.append(f'SU de {v} difiere de la implementación independiente')
    return problemas


def tabla_comparacion(relevancia, anteriores):
    def escenario(tabla, nombre, columna_q):
        t = tabla[tabla['escenario'] == nombre].set_index('variable')
        return lambda v, c: _float(t.loc[v, c]) if v in t.index else np.nan, lambda v: _float(t.loc[v, columna_q]) if v in t.index else np.nan

    previas, cuidados = anteriores['previas'], anteriores['cuidados']
    e1_col, e1_q = escenario(previas, 'E1', 'q')
    e4_col, e4_q = escenario(previas, 'E4', 'q')
    c4_col, c4_q = escenario(cuidados, 'C4', 'q_familia_31')
    filas = []
    for f in relevancia.itertuples():
        p50, q31 = c4_col(f.variable, 'p'), c4_q(f.variable)
        filas.append({'variable': f.variable, 'su': f.su, 'p_5000_E1': e1_col(f.variable, 'p'), 'q_5000_E1': e1_q(f.variable),
                      'p_50000_E4': e4_col(f.variable, 'p'), 'q_50000_E4': e4_q(f.variable), 'p_50000_C4': p50, 'q_50000_C4': q31,
                      'p_10000': f.p, 'q_10000': f.q, 'q_10000_familia_30': f.q_familia_30, 'q_bajo_0_10_10000': f.q_bajo_0_10,
                      'q_bajo_0_10_C4': q31 < ALFA if pd.notna(q31) else '', 'q_bajo_0_10_E4': e4_q(f.variable) < ALFA if pd.notna(e4_q(f.variable)) else '',
                      'dif_p_con_50000': f.p - p50 if pd.notna(p50) else np.nan})
    return pd.DataFrame(filas)


# --- Informe y registro ------------------------------------------------------------------------------------

def _pv(x):
    return P._n(x, 5)


def _s(x):
    return P._n(x, 4)


def _r(x, d=3):
    return '-' if pd.isna(x) else f'{x:+.{d}f}'.replace('.', ',')


def _lista_v(variables):
    return ', '.join(f'`{v}`' for v in variables) or 'ninguna'


def informe(r):
    rel, mc, dir_, dec, pares, ev = r['relevancia'], r['monte_carlo'], r['direccion'], r['decisiones'], r['pares'], r['evaluacion']
    orden = rel.sort_values(['q', 'p', 'variable'])
    bajo10 = orden[orden['q_bajo_0_10']]['variable'].tolist()
    bajo05 = orden[orden['q_bajo_0_05']]['variable'].tolist()
    cercanas = mc[mc['cercana']].sort_values('q')
    rec = r['recomendacion']
    adaptado, estandar = F.seleccionadas(ev.adaptado), F.seleccionadas(ev.estandar)
    d = dir_.merge(rel[['variable', 'q', 'su']], on='variable')
    d['clase'] = [clasificar_factor(f.direccion, f.q, f.rho_q) for f in d.itertuples()]
    grupos = ['Posible factor de riesgo', 'Posible factor de protección', 'Asociación sin dirección clara', 'Indicio de riesgo (solo orden)',
              'Indicio de protección (solo orden)', 'Sin respaldo tras la corrección']
    filas_clase = []
    for g in grupos:
        parte = d[d['clase'] == g].sort_values('q')
        filas_clase += [[g, f'`{f.variable}`', f.mayor_valor, f.n, _r(f.rho_mrs), f'{_r(f.rho_ic95_inferior)} a {_r(f.rho_ic95_superior)}',
                         f.direccion, _pv(f.q), _pv(f.rho_q)] for f in parte.itertuples()]
    extremos = d[d['cat_baja'] != ''].sort_values(['q', 'variable'])
    comp = r['comparacion']
    cambian = comp[(comp['q_bajo_0_10_10000'].astype(str) != comp['q_bajo_0_10_C4'].astype(str)) & (comp['q_bajo_0_10_C4'].astype(str) != '')]
    partes = [
        '# Revisión de la Fase 35B. Primera ejecución con 10.000 permutaciones',
        f'*Generado por `analisis/revision_35b_reunion_1103.py` el {datetime.now():%d-%m-%Y}. Protocolo: `protocolo_revision_35b.md`.*',
        '> **Análisis exploratorio e informativo.** Usa entropía de Shannon (log₂), información mutua y SU. Ninguna variable sale de la '
        'Fase 36 por estos resultados. Los datos son sintéticos y **ninguna asociación se interpreta como causal**.',
        '## 1. Las 34 variables',
        'Benjamini-Hochberg sobre una única familia de 34 pruebas. p = (1 + k) / 10.001.',
        K._tabla_md(['Variable', 'Población', 'n', 'SU', 'k', 'p', 'q', 'q < 0,10', 'q < 0,05'],
                    [[f'`{f.variable}`', f.poblacion, f.n, _s(f.su), f.k, _pv(f.p), _pv(f.q), 'sí' if f.q_bajo_0_10 else 'no',
                      'sí' if f.q_bajo_0_05 else 'no'] for f in orden.itertuples()]),
        '## 2. Variables con q < 0,10',
        f'{len(bajo10)}: {_lista_v(bajo10)}.',
        '## 3. Variables con q < 0,05 (referencia)',
        f'{len(bajo05)}: {_lista_v(bajo05)}.',
        '## 4. Variables cercanas a q = 0,10',
        'Cercana = el intervalo de Monte Carlo al 95 % de q contiene 0,10 (regla registrada antes de ver resultados).',
        (K._tabla_md(['Variable', 'q', 'IC Monte Carlo de q', 'P(q < 0,10)'],
                     [[f'`{f.variable}`', _pv(f.q), f'{_pv(f.q_mc_inferior)} a {_pv(f.q_mc_superior)}', P._n(f.prob_q_bajo_umbral, 3)]
                      for f in cercanas.itertuples()]) if len(cercanas) else 'Ninguna.'),
        '## 5. FCBF informativo y redundancia',
        f'Pares evaluados entre relevantes: {len(pares)}. Rótulos descriptivos: **no eliminan variables de la Fase 36**.',
        f'- **Variante adaptada (q del par < 0,10), no redundantes ({len(adaptado)}):** {_lista_v(adaptado)}.',
        f'- **Variante estándar, no redundantes ({len(estandar)}):** {_lista_v(estandar)}.',
        K._tabla_md(['Variante', 'Variable', 'Etapa', 'Decisión', 'Redundante con', 'SU con severidad', 'SU del par', 'q del par'],
                    [[f.variante, f'`{f.variable}`', f.etapa or '-', f.decision, f'`{f.eliminada_por}`' if f.eliminada_por else '-',
                      _s(f.su_con_severidad), _s(f.su_par), _pv(f.q_par)]
                     for f in dec[dec['decision'] != 'no relevante'].sort_values(['variante', 'su_con_severidad'], ascending=[True, False]).itertuples()]),
        '**Pares evaluados:**',
        (K._tabla_md(['Variable 1', 'Variable 2', 'n', 'SU', 'p', 'q'],
                     [[f'`{f.variable_1}`', f'`{f.variable_2}`', f.n, _s(f.su), _pv(f.p), _pv(f.q)] for f in pares.itertuples()])
         if len(pares) else 'No hay pares.'),
        '**Parejas con mayor SU entre las 34** (cobertura común, sin permutaciones; detalle en `su_todas_las_parejas.csv`):',
        K._tabla_md(['Variable 1', 'Variable 2', 'n', 'SU'],
                    [[f'`{f.variable_1}`', f'`{f.variable_2}`', f.n, _s(f.su)] for f in r['parejas'].head(12).itertuples()]),
        '## 6. Clasificación descriptiva de posibles factores',
        'Clases fijadas en el protocolo. La columna «Un valor mayor significa» indica cómo leer el signo. No implica causalidad.',
        K._tabla_md(['Clase', 'Variable', 'Un valor mayor significa', 'n', 'ρ con MRS', 'IC 95 %', 'Dirección', 'q SU', 'q ρ'], filas_clase),
        '**Magnitud: categoría más baja frente a la más alta con n ≥ 10.** Diferencia = alta − baja.',
        K._tabla_md(['Variable', 'Baja', 'Alta', 'Dif. MRS (IC 95 %)', 'Dif. % severas (IC 95 %)', 'ε²', 'K-W p'],
                    [[f'`{f.variable}`', f.cat_baja, f.cat_alta, f'{_r(f.dif_mrs, 2)} ({_r(f.dif_mrs_ic_inferior, 2)} a {_r(f.dif_mrs_ic_superior, 2)})',
                      f'{_r(f.dif_pct_severas, 1)} ({_r(f.dif_pct_ic_inferior, 1)} a {_r(f.dif_pct_ic_superior, 1)})', P._n(f.epsilon2, 4), _pv(f.kw_p)]
                     for f in extremos.itertuples()]),
        'Las comparaciones por categoría están en `direccion_categorias.csv`.',
        '## 7. Comparación con resultados anteriores',
        'E1 y E4 tienen familia de 30, con `doble_carga` y sin sobrecarga. C4 tiene familia de 31. Las antiguas de control no tenían q.',
        K._tabla_md(['Variable', 'SU', 'q E1 (5.000)', 'q E4 (50.000)', 'q C4 (50.000)', 'p 50.000', 'p 10.000', 'q 10.000', 'q 10.000, solo 30'],
                    [[f'`{f.variable}`', _s(f.su), _pv(f.q_5000_E1), _pv(f.q_50000_E4), _pv(f.q_50000_C4), _pv(f.p_50000_C4), _pv(f.p_10000), _pv(f.q_10000),
                      _pv(f.q_10000_familia_30)] for f in comp.sort_values('q_10000').itertuples()]),
        f'Cambian de clasificación respecto de C4 con q < 0,10: {_lista_v(cambian["variable"].tolist())}.',
        '**Sensibilidades, fuera de la familia:**',
        K._tabla_md(['Variable', 'Versión', 'n', 'SU', 'p', 'q al reemplazar', 'ρ con MRS'],
                    [[f'`{f.variable}`', f.version, f.n, _s(f.su), _pv(f.p), _pv(f.q_al_reemplazar), _r(f.rho_mrs)] for f in r['sensibilidades'].itertuples()]),
        '## 8. Incertidumbre Monte Carlo',
        'Posterior de Jeffreys para cada p, 20.000 sorteos propagados por Benjamini-Hochberg. La proyección con 50.000 es solo una referencia.',
        K._tabla_md(['Variable', 'k', 'p', 'EE de p', 'IC MC de p', 'q', 'IC MC de q', 'P(q < 0,10)', 'IC MC de q proyectado con 50.000'],
                    [[f'`{f.variable}`', f.k, _pv(f.p), _pv(f.error_estandar_p), f'{_pv(f.p_mc_inferior)} a {_pv(f.p_mc_superior)}', _pv(f.q),
                      f'{_pv(f.q_mc_inferior)} a {_pv(f.q_mc_superior)}', P._n(f.prob_q_bajo_umbral, 3),
                      f'{_pv(f.q_mc_inferior_proyectado_50000)} a {_pv(f.q_mc_superior_proyectado_50000)}'] for f in mc.sort_values('q').head(16).itertuples()]),
        'Se muestran las 16 con menor q; el resto está en `incertidumbre_monte_carlo.csv`.',
        '**Estabilidad numérica:** dos corridas idénticas; SU igual a la guardada y a una implementación independiente en las 34.',
        '## 9. Recomendación técnica',
        ('**Según la regla registrada, se recomienda ejecutar 50.000 permutaciones.** Motivo: ' + '; '.join(rec['motivos']) + '.'
         if rec['recomendar_50000'] else '**Según la regla registrada, no se recomienda ejecutar 50.000 permutaciones:** ninguna variable tiene un '
         'intervalo de Monte Carlo de q que contenga 0,10 y no hay inestabilidad numérica.'),
        'La ejecución de 50.000 **no se realizó** y requiere autorización expresa.',
        '## 10. Advertencias',
        '- **Exploratorio:** la lista de variables y el umbral se fijaron conociendo resultados anteriores.',
        '- **`evacuacion_intestinal`:** un valor mayor significa evacuaciones menos frecuentes.',
        '- **`cantidad_personas_cuida`:** se mide en las 529, con 0 = no cuida; su signo mezcla cuidar o no cuidar con cuántas personas.',
        '- **`imc`:** 262 de 529 valores están imputados y caen en 25-29,9; ver la sensibilidad con observadas.',
        '- **`trabaja_actualmente`:** 22 valores imputados como True; la variable es constante entre las 287.',
        '- **Consecuencias posibles:** `distension_abdominal` puede solaparse con síntomas, y los medicamentos pueden ser consecuencia o marcar otra condición.',
        '- **Sobrecarga:** describe a quienes se identifican como cuidadoras y respondieron; la pregunta menciona «su trabajo».',
        '- **Poblaciones:** una SU con 239 o 287 personas no se compara directamente con una con 529.',
        '## 11. Tiempo de ejecución',
        K._tabla_md(['Etapa', 'Segundos'], [[k, P._n(v, 1)] for k, v in r['tiempos'].items()]),
    ]
    return '\n\n'.join(partes) + '\n'


def registro(r, huellas):
    ev, rec = r['evaluacion'], r['recomendacion']
    lineas = ['LOG revisión Fase 35B, reunión 03-11-2026: entropía de Shannon, 10.000 permutaciones, EXPLORATORIO',
              f'Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M}', f'HEAD: {P._git("rev-parse", "HEAD").strip()}',
              f'Semilla: SeedSequence({C.SEMILLA}, spawn_key=({ID_REVISION}, 0, tipo, indice)); tolerancia: {C.TOLERANCIA_SU_35B}; un solo proceso',
              f'Versiones: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}',
              f'Variables: {len(ev.medidas.su_objetivo)}; relevantes q<0,10: {len(ev.medidas.relevantes)}; pares: {len(ev.medidas.su_par)}',
              f'Relevantes: {";".join(ev.medidas.relevantes)}',
              f'FCBF adaptado: {";".join(F.seleccionadas(ev.adaptado))}', f'FCBF estandar: {";".join(F.seleccionadas(ev.estandar))}',
              f'Recomendar 50.000: {rec["recomendar_50000"]}; motivos: {rec["motivos"]}',
              'Comprobaciones: dos corridas idénticas; SU igual a la guardada y a la implementación independiente.',
              'Tiempo real (s): ' + ', '.join(f'{k} {v:.1f}' for k, v in r['tiempos'].items())]
    lineas += [f'SHA-256 {nombre}: {h}' for nombre, h in (huellas or {}).items()]
    return '\n'.join(lineas) + '\n'


# --- Flujo -------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class RutasRevision:
    carpeta: Path

    def csv(self, nombre):
        return self.carpeta / f'{nombre}.csv'

    @property
    def informe(self):
        return self.carpeta / 'informe_revision_10000.md'

    @property
    def log(self):
        return self.carpeta / 'log_revision_10000.txt'

    def declaradas(self):
        return {self.csv(n) for n in ARCHIVOS_CSV} | {self.informe, self.log}


RUTAS_REVISION = RutasRevision(SALIDA)


def correr(datos, poblacion, rutas, anteriores=None, n_permutaciones=N_PERMUTACIONES, huellas=None):
    """Calcula y comprueba todo antes de escribir: si algo falla, no queda ningún archivo."""
    inicio = time.perf_counter()
    M.validar_separacion(rutas)
    salida = P.Escritor(rutas)
    esc = construir_escenario(datos, poblacion)
    plan = M.Plan(K.Parametros('R10', n_permutaciones, ALFA, 'Revisión 03-11, q < 0,10'), M.OBSERVADAS, '')
    alfa_original = C.ALFA_Q_35B
    ev = M.evaluar(esc, plan)
    repeticion = M.evaluar(esc, plan)
    tiempos = {'permutaciones': ev.segundos, 'repeticion': repeticion.segundos}
    inestabilidades = []
    if not M.iguales(ev, repeticion):
        inestabilidades.append('dos corridas no coinciden')
    inestabilidades += comprobar_independiente(esc)
    if C.ALFA_Q_35B != alfa_original:
        raise RuntimeError('El umbral original no se restauró.')
    if anteriores is not None:
        diferencias = comprobar_su(ev.medidas, su_guardadas(anteriores))
        if diferencias:
            raise RuntimeError('; '.join(diferencias))
    if inestabilidades:
        raise RuntimeError('Inestabilidad numérica: ' + '; '.join(inestabilidades))

    relevancia = tabla_relevancia(esc, ev)
    monte_carlo = tabla_monte_carlo(relevancia, n_permutaciones)
    direccion, categorias = tabla_direccion(datos, esc)
    d = direccion.merge(relevancia[['variable', 'q']], on='variable')
    direccion['clase'] = [clasificar_factor(f.direccion, f.q, f.rho_q) for f in d.itertuples()]
    resultado = {'evaluacion': ev, 'relevancia': relevancia, 'monte_carlo': monte_carlo, 'direccion': direccion,
                 'pares': M.tabla_pares(ev), 'decisiones': M.tabla_decisiones(ev), 'parejas': tabla_todas_las_parejas(esc),
                 'sensibilidades': tabla_sensibilidades(datos, esc, poblacion, ev),
                 'recomendacion': recomendar(monte_carlo[monte_carlo['cercana']]['variable'].tolist(), inestabilidades),
                 'comparacion': tabla_comparacion(relevancia, anteriores if anteriores is not None else leer_anteriores())}
    orientacion = pd.DataFrame([{'variable': v, 'tipo': e.tipo, 'mayor_valor': e.mayor_valor, 'clase_models': e.clase_models,
                                 'niveles': '; '.join(f'{k} = {t}' for k, t in e.niveles.items())} for v, e in sorted(ORIENTACION.items())])
    poblaciones = pd.DataFrame(list(poblacion.conteos.items()), columns=['poblacion', 'n'])
    tablas = {'poblaciones': poblaciones, 'orientacion_escalas': orientacion, 'shannon_componentes': tabla_shannon(esc), 'relevancia_34': relevancia,
              'incertidumbre_monte_carlo': monte_carlo, 'pares_relevantes': resultado['pares'], 'decisiones_fcbf': resultado['decisiones'],
              'pares_no_eliminados': tabla_no_eliminados(ev), 'su_todas_las_parejas': resultado['parejas'], 'direccion_resumen': direccion,
              'direccion_categorias': categorias, 'comparacion_anteriores': resultado['comparacion'], 'sensibilidades': resultado['sensibilidades']}
    tiempos['total'] = time.perf_counter() - inicio
    resultado['tiempos'] = tiempos
    texto_informe, texto_log = informe(resultado), registro(resultado, huellas)
    for nombre, tabla in tablas.items():
        salida.tabla(rutas.csv(nombre), tabla)
    salida.texto(rutas.informe, texto_informe)
    salida.texto(rutas.log, texto_log)
    return resultado


def archivos_vigilados():
    """Todo lo anterior que no puede cambiar, incluido el análisis de cuidados y el programa de Random Forest."""
    rf = [P.ANALISIS / n for n in ('protocolo_random_forest_35b.md', 'random_forest_fase35b.py')]
    rf.append(P.ANALISIS / 'preprocesamiento' / 'test_random_forest_35b.py')
    cuidados = [M.PROTOCOLO, M.PRUEBAS, Path(M.__file__).resolve(), *M.RUTAS_CUIDADOS.declaradas()]
    return sorted({*M.archivos_vigilados(), *cuidados, *rf})


def correr_pruebas():
    nombres = ['preprocesamiento.test_entropia', 'preprocesamiento.test_complementario_35b',
               'preprocesamiento.test_complementario_cuidados', 'preprocesamiento.test_revision_35b']
    suite = unittest.defaultTestLoader.loadTestsFromNames(nombres)
    return unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite).wasSuccessful()


def comprobar_datos_reales():
    """Solo identifica poblaciones y variables. No usa la severidad ni calcula ninguna SU."""
    datos, poblacion, problemas = M.comprobar_datos_reales()
    esc = construir_escenario(datos, poblacion)
    return datos, poblacion, [*problemas, *comprobar_lista(sorted(esc.indice())), *comprobar_tamanos(esc)]


def main():
    parser = argparse.ArgumentParser(description='Revisión de la Fase 35B, reunión del 03-11-2026: 10.000 permutaciones.')
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--verificar', action='store_true')
    modo.add_argument('--ejecutar', action='store_true')
    parser.add_argument('--autorizado-por-usuaria', action='store_true')
    args = parser.parse_args()
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
    M.validar_separacion(RUTAS_REVISION)
    print(f'34 variables: {len(VARIABLES_34)}; general 529, laboral {int(datos.mascara.sum())}, cuidadoras {int(poblacion.observada.sum())}.')
    if args.verificar:
        print('Pruebas, estado y tamaños correctos. No se calculó ninguna SU con los datos reales.')
        return
    huellas = {r.name: P.sha256(r) for r in (Path(__file__).resolve(), PROTOCOLO, PRUEBAS)}
    antes = P.manifiesto(archivos_vigilados())
    r = correr(datos, poblacion, RUTAS_REVISION, leer_anteriores(), huellas=huellas)
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(archivos_vigilados()))
    if cambiados:
        sys.exit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    print(f'Relevantes q<0,10: {len(r["evaluacion"].medidas.relevantes)}. Recomendar 50.000: {r["recomendacion"]["recomendar_50000"]}.')
    print(f'Total {r["tiempos"]["total"]:.1f} s. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
