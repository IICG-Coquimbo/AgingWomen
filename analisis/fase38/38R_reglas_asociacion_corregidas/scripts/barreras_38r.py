"""
Fase 38R: barreras metodológicas. Contrastan cada configuración con las decisiones conservadas de las Fases 35 y 36, leídas de sus propios archivos,
y detienen el proceso ante cualquier incumplimiento. Nunca corrigen nada: solo lanzan Incumplimiento.
"""
import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[4]
A = RAIZ / 'analisis'
PROHIBIDAS = ('prevision', 'usa_medicamentos_diabetes', 'doble_carga')
RESERVADAS = ('imc', 'lugar_trabajo_comprensivo', 'estres_entorno_laboral', 'sobrecarga_fisica_emocional')
FUENTES = {
    'elegibles_33': A / 'reunion_2026-11-03/revision_33_variables/fase35a/predictores_elegibles_33.csv',
    'candidatas_y_exclusiones': A / 'complemento_bootstrap_33/configuracion/candidatas_y_exclusiones.csv',
    'protocolo_revision_33': A / 'reunion_2026-11-03/revision_33_variables/protocolo_revision_33.md',
    'preprocesamiento_35_revisado': A / 'cierre_fases_34_35/informes/informe_preprocesamiento_fase35_revisado.md',
    'configuracion_36': A / 'fase36/configuracion_fase36.py',
    'protocolo_36_ajustado': A / 'fase36/informes/fuentes/01_protocolo_fase36A_ajustado.md',
    'esquema_P2': A / 'fase36/artefactos/P2/esquema_variables.json',
}
# Poblaciones autorizadas (instrucción de la Fase 38R), contrastadas con el protocolo ajustado de la Fase 36, sección 10.
POBLACION = {'principal': 529, 'S1': 529, 'S2a': 529, 'S2b': 529, 'S3-bajo': 529, 'S3-alto': 529, 'S4-1': 529, 'S4-2': 529, 'S5': 529, 'S6': 529,
             'S7a': 287, 'S7a-309': 309, 'S7b': 239, 'S7b-251': 251, 'S8a': 267, 'S8b': 267}
# Coincidencia exacta conocida y sin relación con el uso de etiquetas: en S2b el ítem «3 o más días» es por definición el primer paso de la regla B1.
IDENTIDADES_DECLARADAS = {('dias_ejercicio=3_o_mas_dias', 'B1_regla=1'), ('dias_ejercicio=3_o_mas_dias', 'B1=1'), ('dias_ejercicio=3_o_mas_dias', 'B1_cv=1')}

_EXCLUIDAS = re.compile(r'previs|fonasa|isapre|ffaa|diabet|doble.?carga')
_MRS = re.compile(r'^(mrs|pregunta|severo|severidad|sintoma)|mrs_|^item_?\d')
_POSTERIOR = re.compile(r'consecuenc')
_SEGMENTO = re.compile(r'^(segmento|grupo|cluster|etiqueta|b1|b2|a_complemento|p2_c12|etapa)')


class Incumplimiento(Exception):
    """Una barrera metodológica no se cumplió: el proceso debe detenerse sin corregir nada."""


def _alto(msg):
    raise Incumplimiento(msg)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _leer_csv(p):
    with open(p, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def decisiones(fuentes=None):
    """Lee las decisiones conservadas y exige que sean coherentes entre sí. Devuelve las 29 autorizadas y las poblaciones de cada grupo."""
    F = {**FUENTES, **(fuentes or {})}
    for k, p in F.items():
        if not Path(p).is_file():
            _alto(f'Falta la fuente de decisiones {k}: {p}')
    el = _leer_csv(F['elegibles_33'])
    nombres = [r['variable'] for r in el]
    if len(nombres) != 33 or len(set(nombres)) != 33:
        _alto(f'La lista definitiva de la Fase 35 no tiene 33 variables únicas: {len(nombres)}')
    for v in PROHIBIDAS:
        if v in nombres:
            _alto(f'{v} aparece entre las 33 elegibles de la Fase 35')
    generales = {r['variable'] for r in el if r['poblacion'] == 'general'}
    if not set(RESERVADAS) <= set(nombres):
        _alto('Alguna variable reservada no está entre las 33 elegibles')
    principal = sorted(generales - set(RESERVADAS))
    if len(principal) != 29:
        _alto(f'Las generales autorizadas no son 29: {len(principal)}')
    ex = _leer_csv(F['candidatas_y_exclusiones'])
    if {r['variable'] for r in ex if r['estado'] == 'excluida'} != set(PROHIBIDAS):
        _alto('Las exclusiones registradas en candidatas_y_exclusiones.csv no son las tres definitivas')
    if {r['variable'] for r in ex if r['estado'] == 'candidata'} != set(nombres):
        _alto('Las candidatas registradas no coinciden con las 33 elegibles')
    t33 = Path(F['protocolo_revision_33']).read_text(encoding='utf-8')
    if '`usa_medicamentos_diabetes` queda fuera de todo el modelado' not in t33 or '`doble_carga` y `prevision` siguen excluidas' not in t33:
        _alto('El protocolo de la revisión de 33 variables no declara las exclusiones definitivas')
    t35 = Path(F['preprocesamiento_35_revisado']).read_text(encoding='utf-8')
    if 'salen `prevision`, `doble_carga` y `usa_medicamentos_diabetes`' not in t35:
        _alto('El informe revisado de la Fase 35A no declara las exclusiones')
    c36 = Path(F['configuracion_36']).read_text(encoding='utf-8')
    m = re.search(r'EXCLUIDAS_NOMBRE\s*=\s*\[(.*?)\]', c36, re.S)
    if not m or any(f"'{v}'" not in m.group(1) for v in PROHIBIDAS):
        _alto('La configuración de la Fase 36 no excluye las tres variables')
    p36 = Path(F['protocolo_36_ajustado']).read_text(encoding='utf-8')
    no_entran = next((l for l in p36.splitlines() if l.startswith('**No entran:**')), '')
    if any(f'`{v}`' not in no_entran for v in PROHIBIDAS):
        _alto('El protocolo ajustado de la Fase 36 no excluye las tres variables')
    if '| Laboral | 287 |' not in p36 or '| Cuidados | 239 con sobrecarga observada | 251 cuidadoras, con 12 imputadas |' not in p36:
        _alto('El protocolo ajustado de la Fase 36 no documenta las poblaciones de los módulos')
    p2 = sorted(x['variable'] for x in json.loads(Path(F['esquema_P2']).read_text(encoding='utf-8'))['variables'])
    if p2 != principal:
        _alto(f'El esquema P2 de la Fase 36 difiere de las 29 autorizadas: {set(p2) ^ set(principal)}')
    return {'principal': principal, 'elegibles': sorted(nombres), 'reservadas': list(RESERVADAS), 'prohibidas': list(PROHIBIDAS), 'huellas': {k: sha(p) for k, p in F.items()}}


def _norm(t):
    return unicodedata.normalize('NFKD', str(t).lower()).encode('ascii', 'ignore').decode('ascii')


def verificar_nombre(item):
    """Rechaza un ítem o variable por su nombre, incluidas formas transformadas."""
    n = _norm(item)
    izq = n.split('=')[0]
    if _EXCLUIDAS.search(n):
        _alto(f'Ítem derivado de una variable excluida: {item}')
    if _MRS.search(izq):
        _alto(f'Ítem o variable del MRS como antecedente: {item}')
    if _POSTERIOR.search(izq):
        _alto(f'Variable posterior a los síntomas como antecedente: {item}')
    if _SEGMENTO.search(izq):
        _alto(f'Etiqueta de segmentación o etapa como antecedente: {item}')


def verificar_lista_principal(variables, dec):
    if len(variables) != len(set(variables)) or len(variables) != 29:
        _alto(f'La matriz principal no tiene 29 variables únicas: {len(variables)}')
    if sorted(variables) != dec['principal']:
        _alto(f'Variables principales distintas de las autorizadas: {sorted(set(variables) ^ set(dec["principal"]))}')
    for v in variables:
        if v in dec['prohibidas'] or v in dec['reservadas']:
            _alto(f'{v} no puede estar en la matriz principal')
        verificar_nombre(v)


def permitidas(nombre, dec):
    """Variables admitidas por configuración, derivadas de las 29 autorizadas y de las reservadas."""
    b = set(dec['principal'])
    if nombre == 'S5':
        b -= {'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza'}
    elif nombre == 'S6':
        b -= {'tiene_actividad_sexual', 'distension_abdominal', 'evacuacion_intestinal'}
    elif nombre in ('S7a', 'S7a-309'):
        b = (b - {'trabaja_actualmente'}) | {'lugar_trabajo_comprensivo', 'estres_entorno_laboral'}
    elif nombre in ('S7b', 'S7b-251'):
        b |= {'sobrecarga_fisica_emocional'}
    elif nombre == 'S8b':
        b |= {'imc'}
    return b


def mascaras_vetadas(d):
    """Vectores de 529 que ningún ítem puede reproducir: categorías de las excluidas, MRS y severidad, y etiquetas de segmentación. Se usan sobre las 529 completas."""
    out = {}

    def agregar(nombre, m):
        m = np.asarray(m, bool)
        if 0 < m.sum() < len(m):
            out[nombre] = m
    X, M, E = d.X, d.M, d.E
    for v in ('prevision', 'usa_medicamentos_diabetes'):
        for c in X[v].dropna().unique():
            agregar(f'{v}={c}', (X[v] == c).to_numpy())
    dc = pd.read_csv(RAIZ / 'datos' / 'analitico' / 'dataset_fase35.csv', dtype=str).set_index('participante_id').reindex(d.ids)['doble_carga']
    for c in dc.dropna().unique():
        agregar(f'doble_carga={c}', (dc == c).to_numpy())
    agregar('severo_mrs=1', M['severo_mrs'].to_numpy() == 1)
    for col in [f'pregunta_{i}' for i in range(1, 12)]:
        for k in range(5):
            agregar(f'{col}={k}', M[col].to_numpy() == k)
            agregar(f'{col}>={k}', M[col].to_numpy() >= k)
    for s in M['severidad'].unique():
        agregar(f'severidad={s}', (M['severidad'] == s).to_numpy())
    for col in ('A', 'A_complemento', 'B1', 'B1_cv', 'B1_regla'):
        for k in pd.unique(E[col].dropna()):
            agregar(f'{col}={k:g}', (E[col] == k).to_numpy())
    return out


def verificar_contenido(T529, vetadas):
    """Rechaza un ítem cuyo vector (o su complemento) reproduce exactamente una máscara vetada, aunque su nombre sea inocuo."""
    idx = {}
    for nombre, m in vetadas.items():
        idx.setdefault(m.tobytes(), nombre)
        idx.setdefault((~m).tobytes(), nombre + ' (complemento)')
    for it in T529.columns:
        n = idx.get(T529[it].to_numpy(bool).tobytes())
        if n and (it, n.replace(' (complemento)', '')) not in IDENTIDADES_DECLARADAS:
            _alto(f'El ítem {it} reproduce exactamente {n}')


def verificar_items(items, variable_de, autorizadas):
    for it in items:
        verificar_nombre(it)
        try:
            v = variable_de(it)
        except KeyError:
            _alto(f'Ítem sin variable de origen conocida: {it}')
        if v not in autorizadas:
            _alto(f'Ítem {it} de la variable no autorizada {v}')


def verificar_poblacion(nombre, c, d):
    """Tamaño, identificadores y tratamiento de faltantes de cada configuración."""
    if c.n != POBLACION[nombre] or len(c.ids) != c.n or len(set(c.ids)) != c.n or len(c.T) != c.n:
        _alto(f'{nombre}: población {c.n}, se esperaba {POBLACION[nombre]}')
    p = pd.Index(c.ids)
    X, E = d.X.loc[p], d.estado.loc[p]
    if nombre == 'principal' and c.n_si != 281:
        _alto(f'principal: {c.n_si} severas, se esperaban 281')
    if nombre in ('S7a', 'S7a-309'):
        if not (X['trabaja_actualmente'] == 1).all():
            _alto(f'{nombre}: incluye a quien no trabaja')
        faltan = int(X[['lugar_trabajo_comprensivo', 'estres_entorno_laboral']].isna().any(axis=1).sum())
        if faltan != (0 if nombre == 'S7a' else 22):
            _alto(f'{nombre}: {faltan} participantes sin respuestas laborales')
        if nombre == 'S7a' and E['trabaja_actualmente'].eq('imputada').any():
            _alto('S7a: incluye trabajo imputado')
    if nombre in ('S7b', 'S7b-251'):
        if not (X['cantidad_personas_cuida'] > 0).all():
            _alto(f'{nombre}: incluye a quien no cuida')
        imp = int(E['sobrecarga_fisica_emocional'].eq('imputada').sum())
        if imp != (0 if nombre == 'S7b' else 12):
            _alto(f'{nombre}: {imp} valores de sobrecarga imputados')
    if nombre in ('S8a', 'S8b') and (not E['imc'].eq('observada').all() or X['imc'].isna().any()):
        _alto(f'{nombre}: incluye IMC no observado')
    if nombre == 'S1':
        for v in c.variables:
            cols = [i for i in c.T.columns if c.variable_de(i) == v]
            malas = E[v].isin(['imputada', 'deducida']).to_numpy() | (d.heredada.loc[p, v].astype(str) == '1').to_numpy()
            if cols and c.T[cols].any(axis=1).to_numpy()[malas].any():
                _alto(f'S1: {v} conserva ítem en celdas imputadas')


def verificar_reglas(R, variable_de, autorizadas, consecuentes):
    """Comprueba cada antecedente y la columna de variables de una tabla de reglas."""
    if not len(R):
        return
    for a in R['antecedente'].unique():
        verificar_items(a.split(' & '), variable_de, autorizadas)
    for vs in R['variables'].unique():
        for v in vs.split(' & '):
            if v not in autorizadas:
                _alto(f'Regla con la variable no autorizada {v}')
    if not set(R['consecuente']) <= set(consecuentes):
        _alto('Consecuente no autorizado')
