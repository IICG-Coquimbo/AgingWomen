"""
Fase 39R: barreras metodológicas. Reutilizan sin modificar las barreras de la 38R (decisiones de las Fases 35 y 36 leídas de sus archivos) y añaden lo propio de los estratos.
Nunca corrigen nada: solo lanzan Incumplimiento y detienen el proceso.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(RAIZ / 'analisis' / 'fase38' / '38R_reglas_asociacion_corregidas' / 'scripts'))
import barreras_38r as B38  # noqa: E402

Incumplimiento = B38.Incumplimiento
MODULOS = {'S7a': ['lugar_trabajo_comprensivo', 'estres_entorno_laboral'], 'S7b': ['sobrecarga_fisica_emocional']}
ESTRATO_MODULO = {'S7a': ('trabajo', 'trabaja'), 'S7b': ('cuidado', 'cuida')}
# Tamaños y severas: instrucción de la 39R y Fase 39 histórica. Los umbrales se comprueban con la fórmula del protocolo.
TAMANOS = {('trabajo', 'trabaja'): (309, 178), ('trabajo', 'no_trabaja'): (220, 103), ('pareja', 'con_pareja'): (356, 181), ('pareja', 'sin_pareja'): (173, 100),
           ('ejercicio', '0_dias'): (302, 177), ('ejercicio', '1-2_dias'): (148, 78), ('ejercicio', '3_o_mas_dias'): (79, 26), ('cuidado', 'cuida'): (251, 141), ('cuidado', 'no_cuida'): (278, 140)}
TAMANOS_GRUPOS = {('A', 'A_0'): 150, ('A', 'A_1'): 76, ('A', 'A_2'): 132, ('A', 'A_3'): 171, ('B1', 'B1_0'): 150, ('B1', 'B1_1'): 79, ('B1', 'B1_2'): 126, ('B1', 'B1_3'): 174}
TRIO = ['trabaja_actualmente', 'tiene_pareja', 'dias_ejercicio_semana']
VARIABLE_ESTRATO = {'trabajo': ['trabaja_actualmente'], 'pareja': ['tiene_pareja'], 'ejercicio': ['dias_ejercicio_semana'], 'cuidado': ['cantidad_personas_cuida'], 'A': TRIO, 'B1': TRIO}


def _alto(msg):
    raise Incumplimiento(msg)


def autorizadas(sens, dec):
    """Variables admitidas en las 529 de cada configuración de la Fase 39 (antes de quitar la variable del estrato)."""
    b = set(dec['principal'])
    if sens == 'S5':
        b -= {'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza'}
    elif sens == 'S6':
        b -= {'tiene_actividad_sexual', 'distension_abdominal', 'evacuacion_intestinal'}
    elif sens in MODULOS:
        b |= set(MODULOS[sens])
    return b


def verificar_base(T, sens, pq, variable_de):
    """Matriz de las 529 de una configuración: nombres, variables autorizadas y contenido (ni copia ni complemento de las máscaras vetadas)."""
    if T.shape[0] != 529:
        _alto(f'{sens}: la matriz no tiene 529 filas: {T.shape[0]}')
    B38.verificar_items(T.columns, variable_de, autorizadas(sens, pq.dec))
    B38.verificar_contenido(T, pq.vetadas)


def verificar_matriz_38r(T529, y, ids, ruta):
    """La matriz principal debe ser exactamente la matriz validada de la 38R."""
    M = pd.read_csv(ruta, dtype={'participante_id': str})
    cols = [c for c in M.columns if c not in ('participante_id', 'severo_mrs=SI', 'severo_mrs=NO')]
    if len(cols) != 90 or len(T529.columns) != 90:
        _alto(f'La matriz principal no tiene 90 ítems: {len(cols)} en la 38R, {len(T529.columns)} aquí')
    if cols != list(T529.columns):
        _alto('Los ítems no coinciden con los de la matriz validada de la 38R')
    if M['participante_id'].tolist() != list(ids):
        _alto('Los identificadores no coinciden con los de la 38R')
    if not (M[cols].to_numpy().astype(bool) == T529.to_numpy()).all():
        _alto('La matriz no es idéntica a la matriz validada de la 38R')
    if y is not None and not (M['severo_mrs=SI'].to_numpy() == y).all():
        _alto('El consecuente no coincide con el de la 38R')
    return len(cols)


def verificar_estrato(c, sens, dec, variable_de, umbrales, comprobar_severas=True):
    """Transacciones de un estrato o grupo: tamaño, severas, sin su variable, sin ítems constantes y umbrales del protocolo."""
    clave = (c.grupo, c.estrato)
    if clave in TAMANOS:
        n, si = TAMANOS[clave]
        if c.n != n or (comprobar_severas and c.n_si != si):
            _alto(f'{clave}: {c.n} participantes y {c.n_si} severas; se esperaban {n} y {si}')
    elif clave in TAMANOS_GRUPOS:
        if c.n != TAMANOS_GRUPOS[clave]:
            _alto(f'{clave}: {c.n} participantes; se esperaban {TAMANOS_GRUPOS[clave]}')
    else:
        _alto(f'Estrato no autorizado: {clave}')
    if sens in ESTRATO_MODULO and clave != ESTRATO_MODULO[sens]:
        _alto(f'{sens} solo puede ejecutarse en {ESTRATO_MODULO[sens]}, no en {clave}')
    excl = set(VARIABLE_ESTRATO[c.grupo])
    if set(c.excluidas) != excl:
        _alto(f'{clave}: variables excluidas {c.excluidas}, se esperaban {sorted(excl)}')
    perm = autorizadas(sens, dec) - excl
    B38.verificar_items(c.T.columns, variable_de, perm)
    tam = c.T.sum(axis=0)
    if ((tam == 0) | (tam == c.n)).any():
        _alto(f'{clave}: quedan ítems constantes o vacíos')
    if len(c.T) != c.n or len(c.y) != c.n or len(c.ids) != c.n or len(set(c.ids)) != c.n:
        _alto(f'{clave}: filas o identificadores inconsistentes')
    a, b, largo, comp = umbrales(c.n, sens)
    if (c.min_ant, c.min_conj, c.largo, c.comp) != (a, b, largo, comp):
        _alto(f'{clave}: umbrales {(c.min_ant, c.min_conj, c.largo, c.comp)} distintos de los del protocolo {(a, b, largo, comp)}')


def verificar_modulos(d, T, sens, m, variable_de):
    """Cómo entran los módulos en S7a y S7b: solo dentro del estrato, con la población y el tratamiento de faltantes históricos."""
    if sens not in MODULOS:
        return {}
    cols = [c for c in T.columns if variable_de(c) in MODULOS[sens]]
    if not cols:
        _alto(f'{sens}: no hay ítems del módulo')
    con_item = T[cols].any(axis=1).to_numpy()
    if con_item[~m].any():
        _alto(f'{sens}: hay ítems del módulo fuera del estrato')
    n = int(m.sum())
    if sens == 'S7a':
        if n != 309:
            _alto(f'S7a: población {n}, se esperaban 309')
        faltan = int((~con_item[m]).sum())
        if faltan != 22:
            _alto(f'S7a: {faltan} trabajadoras sin ítems laborales, se esperaban 22')
    else:
        if n != 251:
            _alto(f'S7b: población {n}, se esperaban 251')
        imp = int(d.estado.loc[np.array(d.ids)[m], 'sobrecarga_fisica_emocional'].eq('imputada').sum())
        if imp != 12 or not con_item[m].all():
            _alto(f'S7b: {imp} sobrecargas imputadas o cuidadoras sin ítem')
    return {'configuracion': sens, 'participantes': n, 'con_items_del_modulo': int(con_item[m].sum()), 'sin_items_del_modulo': int((~con_item[m]).sum()), 'items': ', '.join(cols)}


def verificar_tabla_reglas(R, sens, grupo, dec, variable_de, consecuentes):
    """Tabla de reglas de un estrato: ninguna variable no autorizada, ni la del estrato, en antecedentes ni en la columna de variables."""
    if not len(R):
        return
    B38.verificar_reglas(R, variable_de, autorizadas(sens, dec) - set(VARIABLE_ESTRATO[grupo]), consecuentes)


def verificar_tabla_comparacion(H, sens, grupo, dec, variable_de):
    """Tabla de comparación entre estratos: mismas exigencias que las reglas, sin consecuente."""
    if not len(H):
        return
    perm = autorizadas(sens, dec) - set(VARIABLE_ESTRATO[grupo])
    for a in H['antecedente'].unique():
        B38.verificar_items(a.split(' & '), variable_de, perm)
    for vs in H['variables'].unique():
        for v in vs.split(' & '):
            if v not in perm:
                _alto(f'Comparación con la variable no autorizada {v}')
