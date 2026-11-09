"""
Corrección de las Fases 35A y 35B: excluye `usa_medicamentos_diabetes` por dominancia y pasa de 34 a 33 variables.
Protocolo: analisis/reunion_2026-11-03/revision_33_variables/protocolo_revision_33.md.

Uso, desde analisis/:
    python revision_33_variables.py --verificar     estado, datos y reutilización; no escribe nada
    python revision_33_variables.py --ejecutar --autorizado-por-usuaria

No ejecuta permutaciones: reutiliza SU, k y p guardados y recalcula Benjamini-Hochberg, FCBF y las clases.
No regenera ni sobrescribe ningún conjunto de datos o resultado anterior.
"""
import argparse
import csv
import hashlib
import io
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

import complementario_cuidados as M
import complementario_fase35b as K
import informe_integrado_35b as I
import revision_35b_50000 as B
import revision_35b_reunion_1103 as R
import seleccionar_fase35b as P
from eda import variables as V
from preprocesamiento import configuracion as C
from preprocesamiento import entropia as E
from preprocesamiento import fcbf as F

EXCLUIDA = 'usa_medicamentos_diabetes'
VARIABLES_33 = sorted(set(R.VARIABLES_34) - {EXCLUIDA})
CONTROLES_33 = ['edad', 'imc', 'trabaja_actualmente']
UMBRAL_DOMINANCIA = C.UMBRAL_ELIMINAR_DOMINANCIA
CARPETA = R.CARPETA / 'revision_33_variables'
PROTOCOLO = CARPETA / 'protocolo_revision_33.md'
PRUEBAS = P.ANALISIS / 'preprocesamiento' / 'test_revision_33_variables.py'
DATASET_ORIGINAL = P.ENTRADA
DATASET_33 = P.ENTRADA.parent / 'dataset_fase35_33_variables.csv'
VERSIONES = {10000: ('R10', R.SALIDA, CARPETA / 'permutaciones_10000'), 50000: ('R50', B.SALIDA, CARPETA / 'permutaciones_50000')}
TOLERANCIA_REDONDEO = 5.1e-7       # los archivos guardan 6 decimales


# --- Fase 35A: conjunto de datos sin la columna ----------------------------------------------------------------------

def leer_filas(ruta):
    """Filas como texto, sin interpretar ningún valor. Devuelve también el fin de línea del archivo."""
    bruto = Path(ruta).read_bytes()
    fin = '\r\n' if b'\r\n' in bruto else '\n'
    return list(csv.reader(io.StringIO(bruto.decode('utf-8-sig'), newline=''))), fin


def quitar_columna(filas, columna):
    if filas[0].count(columna) != 1:
        raise ValueError(f'La columna {columna} debe aparecer una vez.')
    i = filas[0].index(columna)
    return [f[:i] + f[i + 1:] for f in filas]


def filas_a_bytes(filas, fin):
    salida = io.StringIO(newline='')
    csv.writer(salida, lineterminator=fin).writerows(filas)
    return ('﻿' + salida.getvalue()).encode('utf-8')


def comparar_columnas(original, nueva, excluida=EXCLUIDA):
    """Una fila por columna original. Compara el texto de cada celda y en el mismo orden."""
    cab_o, cab_n = original[0], nueva[0]
    filas = []
    for c in cab_o:
        o = [f[cab_o.index(c)] for f in original[1:]]
        if c == excluida:
            filas.append({'columna': c, 'filas': len(o), 'estado': 'excluida', 'identica': '', 'sha256_columna': hashlib.sha256('\n'.join(o).encode()).hexdigest()})
            continue
        n = [f[cab_n.index(c)] for f in nueva[1:]] if c in cab_n else None
        filas.append({'columna': c, 'filas': len(o), 'estado': 'conservada', 'identica': o == n, 'sha256_columna': hashlib.sha256('\n'.join(o).encode()).hexdigest()})
    return pd.DataFrame(filas)


def problemas_columnas(tabla, original, nueva, excluida=EXCLUIDA):
    problemas = []
    if nueva[0] != [c for c in original[0] if c != excluida]:
        problemas.append('El orden o el nombre de las columnas cambió.')
    if len(original) != len(nueva):
        problemas.append('El número de filas cambió.')
    if excluida in nueva[0]:
        problemas.append('La columna excluida sigue en el conjunto.')
    distintas = tabla[(tabla['estado'] == 'conservada') & (tabla['identica'] != True)]['columna'].tolist()  # noqa: E712
    if distintas:
        problemas.append(f'Columnas distintas: {distintas}')
    return problemas


# --- Reconstrucción sin permutaciones --------------------------------------------------------------------------------

@contextmanager
def sin_permutaciones():
    """Cualquier intento de permutar detiene el programa."""
    original = E.prueba_permutacion

    def prohibida(*_, **__):
        raise RuntimeError('Esta corrección no ejecuta permutaciones.')
    E.prueba_permutacion = prohibida
    try:
        yield
    finally:
        E.prueba_permutacion = original


@dataclass
class Escenario33(R.EscenarioRevision):
    """Las 33 variables, con el mapa de índices de las 34 para no mover ninguna semilla."""
    indices_34: dict = None

    def indice(self):
        return {v: self.indices_34[v] for v in sorted([*self.base.candidatas, R.SOBRECARGA])}


def construir_escenario_33(esc34):
    variables = [v for v in esc34.base.candidatas if v != EXCLUIDA]
    if EXCLUIDA not in esc34.base.candidatas or len(variables) != 32:
        raise RuntimeError('La lista de partida no contiene 33 candidatas generales y laborales más la sobrecarga.')
    b = esc34.base
    base = F.Escenario('Revision 33', b.id_analisis, {v: b.datos[v] for v in variables}, b.objetivo, variables, set(b.laborales), b.mascara)
    return Escenario33(base, esc34.sobrecarga, esc34.poblacion, esc34.nombre_poblacion, esc34.indice())


def k_desde_p(p, n):
    """k de un p guardado con 6 decimales. Falla si la distancia a un conteo entero excede el redondeo."""
    k = np.asarray(p, dtype=float) * (n + 1) - 1
    if np.abs(k - np.round(k)).max(initial=0) > TOLERANCIA_REDONDEO * (n + 1) + 1e-9:
        raise RuntimeError('Un p guardado no corresponde a un conteo entero de permutaciones.')
    return np.round(k).astype(int)


def medidas_33(esc, relevancia, pares, n):
    """SU exacta desde los datos; k guardado; q recalculado. Falla si una SU o un tamaño difieren de lo guardado."""
    datos, y = esc.datos(), esc.base.objetivo
    t = relevancia[relevancia['variable'] != EXCLUIDA].sort_values('variable')
    if t['variable'].tolist() != VARIABLES_33:
        raise RuntimeError('Las variables guardadas no son las 33 esperadas.')
    su, tam, p = {}, {}, {}
    for f in t.itertuples():
        m = esc.mascara_de(f.variable)
        su[f.variable], tam[f.variable] = E.su(datos[f.variable][m], y[m]), int(m.sum())
        p[f.variable] = (int(f.k) + 1) / (n + 1)
        if K._txt(su[f.variable]) != K._txt(f.su) or tam[f.variable] != int(f.n):
            raise RuntimeError(f'{f.variable}: la SU o el tamaño difieren de lo guardado.')
        if K._txt(p[f.variable]) != K._txt(f.p):
            raise RuntimeError(f'{f.variable}: k y p guardados no coinciden.')
    variables = sorted(p)
    q = dict(zip(variables, map(float, E.benjamini_hochberg([p[v] for v in variables]))))
    relevantes = [v for v in variables if q[v] < R.ALFA]
    guardadas = sorted({*pares['variable_1'], *pares['variable_2']})
    if EXCLUIDA in guardadas:
        raise RuntimeError('Un par guardado incluye la variable excluida.')
    if sorted(relevantes) != guardadas:
        raise RuntimeError('Cambió el grupo de relevantes: habría que permutar pares nuevos, lo que requiere autorización.')

    medidas = M.MedidasCuidados(su, tam, p, q, relevantes)
    for f in pares.itertuples():
        clave = (f.variable_1, f.variable_2)
        m = esc.mascara_de(*clave)
        medidas.su_par[clave] = E.su(datos[clave[0]][m], datos[clave[1]][m])
        medidas.n_par[clave] = int(m.sum())
        medidas.p_par[clave] = (int(k_desde_p([f.p], n)[0]) + 1) / (n + 1)
        if K._txt(medidas.su_par[clave]) != K._txt(f.su) or medidas.n_par[clave] != int(f.n):
            raise RuntimeError(f'{clave}: la SU o el tamaño del par difieren de lo guardado.')
    claves = sorted(medidas.su_par)
    medidas.q_par = dict(zip(claves, map(float, E.benjamini_hochberg([medidas.p_par[c] for c in claves]))))
    for f in pares.itertuples():
        if abs(medidas.q_par[(f.variable_1, f.variable_2)] - f.q) > TOLERANCIA_REDONDEO:
            raise RuntimeError(f'q del par {f.variable_1}, {f.variable_2} difiere de lo guardado.')

    generales = [v for v in relevantes if v != R.SOBRECARGA]
    if any(v in esc.base.laborales for v in generales):
        m = esc.base.mascara
        for v in generales:
            medidas.su_objetivo_laboral[v] = E.su(datos[v][m], y[m])
    if R.SOBRECARGA in relevantes:
        raise RuntimeError('La sobrecarga pasó a ser relevante: el texto y las comparaciones de la Etapa 3 deben revisarse.')
    return medidas


def evaluar(esc, medidas, nombre, n):
    """Recorre FCBF con las funciones congeladas, con los controles de la evaluación original."""
    plan = M.Plan(K.Parametros(nombre, n, R.ALFA, 'Revisión de 33 variables, q < 0,10'), M.OBSERVADAS, '')
    with K.umbral(R.ALFA):
        adaptado = M.seleccionar(esc, medidas, True)
        estandar = M.seleccionar(esc, medidas, False)
        generales = M._sin_sobrecarga(medidas)
        for decisiones in (adaptado, estandar):
            P.controlar_seleccion(esc.base, generales, {v: d for v, d in decisiones.items() if v != R.SOBRECARGA})
            M.controlar_etapa3(esc, medidas, decisiones)
        no_eliminados = F.pares_no_eliminados(esc.base, generales, {v: d for v, d in adaptado.items() if v != R.SOBRECARGA})
        no_sobrecarga = M.pares_no_eliminados_sobrecarga(medidas, adaptado)
    return M.Evaluacion(plan, medidas, adaptado, estandar, no_eliminados, no_sobrecarga)


def direccion_33(datos, esc, guardada, relevancia):
    """Conserva lo guardado y recalcula q de ρ y la clase. El p de ρ exacto se calcula de nuevo y se compara."""
    t = guardada[guardada['variable'] != EXCLUIDA].copy().reset_index(drop=True)
    mrs = datos.tabla['mrs_total'].to_numpy(dtype=float)
    exactos = []
    for f in t.itertuples():
        if pd.isna(f.rho_p):
            exactos.append(np.nan)
            continue
        x, m = R.valores_originales(datos, esc, f.variable)
        rho, p = stats.spearmanr(np.asarray(x, dtype=float)[m], mrs[m])
        if abs(rho - f.rho_mrs) > TOLERANCIA_REDONDEO or abs(p - f.rho_p) > TOLERANCIA_REDONDEO:
            raise RuntimeError(f'{f.variable}: ρ o su p difieren de lo guardado.')
        exactos.append(p)
    exactos = np.array(exactos, dtype=float)
    con_signo = ~np.isnan(exactos)
    t['rho_q'] = np.nan
    t.loc[con_signo, 'rho_q'] = E.benjamini_hochberg(exactos[con_signo])
    q = relevancia.set_index('variable')['q']
    t['clase'] = [R.clasificar_factor(f.direccion, q[f.variable], f.rho_q) for f in t.itertuples()]
    return t


def sensibilidades_33(guardada, medidas, n):
    t = guardada.copy()
    t['p_exacto'] = (k_desde_p(t['p'], n) + 1) / (n + 1)
    t['q_al_reemplazar'] = [R._q_reemplazando(medidas.p_objetivo, f.variable, f.p_exacto) for f in t.itertuples()]
    return t.drop(columns='p_exacto')


def sin_excluida(t, *columnas):
    for c in columnas:
        t = t[t[c] != EXCLUIDA]
    return t.reset_index(drop=True)


def version_33(datos, esc, n):
    """Todas las tablas de una versión. `g` son los archivos guardados de la revisión de 34."""
    nombre, origen, _ = VERSIONES[n]
    g = I.leer_version(origen)
    medidas = medidas_33(esc, g['relevancia_34'], g['pares_relevantes'], n)
    ev = evaluar(esc, medidas, nombre, n)
    relevancia = R.tabla_relevancia(esc, ev)
    q30 = g['relevancia_34'].set_index('variable')['q_familia_30']
    for f in relevancia.itertuples():
        if pd.notna(f.q_familia_30) and abs(f.q_familia_30 - q30[f.variable]) > TOLERANCIA_REDONDEO:
            raise RuntimeError(f'{f.variable}: q de la familia de 30 cambió.')
    mc = R.tabla_monte_carlo(relevancia, n) if n == 10000 else B.monte_carlo_b(n)(relevancia)
    t = {'poblaciones': g['poblaciones'], 'orientacion_escalas': sin_excluida(g['orientacion_escalas'], 'variable'),
         'shannon_componentes': sin_excluida(g['shannon_componentes'], 'variable'), 'relevancia_33': relevancia, 'incertidumbre_monte_carlo': mc,
         'pares_relevantes': M.tabla_pares(ev), 'decisiones_fcbf': M.tabla_decisiones(ev), 'pares_no_eliminados': R.tabla_no_eliminados(ev),
         'su_todas_las_parejas': sin_excluida(g['su_todas_las_parejas'], 'variable_1', 'variable_2'),
         'direccion_resumen': direccion_33(datos, esc, g['direccion_resumen'], relevancia),
         'direccion_categorias': sin_excluida(g['direccion_categorias'], 'variable'), 'sensibilidades': sensibilidades_33(g['sensibilidades'], medidas, n)}
    if len(t['su_todas_las_parejas']) != 33 * 32 // 2:
        raise RuntimeError('El número de parejas no corresponde a 33 variables.')
    return t, g, ev


# --- Comparación 34 frente a 33 --------------------------------------------------------------------------------------

def _decision(d, variante, v):
    f = d[(d['variante'] == variante) & (d['variable'] == v)].iloc[0]
    x = f['eliminada_por'] if isinstance(f['eliminada_por'], str) else ''
    return f['decision'], x


def explicar_cambio(f):
    if f['variable'] == EXCLUIDA:
        return 'Excluida por dominancia: no integra la familia de 33.'
    if f['cambia_clase'] or f['cambia_q_0_10'] or f['cambia_fcbf']:
        return 'Cambia la clasificación. Revisar: la SU y el p son los mismos, de modo que el cambio viene de la familia.'
    if abs(f['dif_q']) < 5e-7:
        return 'SU, p y q sin cambios.'
    sentido = 'baja' if f['dif_q'] < 0 else 'sube'
    return f'SU y p idénticos; q {sentido} solo porque la corrección ahora considera 33 pruebas. No cambia la asociación ni la clasificación.'


def tabla_34_33(g, t, n):
    """34 filas: la variable excluida se muestra, sin valores de la revisión corregida."""
    r34, r33 = g['relevancia_34'].set_index('variable'), t['relevancia_33'].set_index('variable')
    d34, d33 = g['direccion_resumen'].set_index('variable'), t['direccion_resumen'].set_index('variable')
    filas = []
    for v in sorted(r34.index):
        a = r34.loc[v]
        f = {'variable': v, 'permutaciones': n, 'poblacion': a['poblacion'], 'n': int(a['n']), 'su_34': a['su'], 'p_34': a['p'], 'q_34': a['q'], 'q_menor_0_10_34': bool(a['q_bajo_0_10']),
             'q_menor_0_05_34': bool(a['q_bajo_0_05']), 'rho_q_34': d34.loc[v, 'rho_q'], 'clase_34': d34.loc[v, 'clase']}
        ad34, el_ad34 = _decision(g['decisiones_fcbf'], 'adaptado', v)
        es34, el_es34 = _decision(g['decisiones_fcbf'], 'estandar', v)
        f.update(fcbf_adaptado_34=ad34, redundante_con_adaptado_34=el_ad34, fcbf_estandar_34=es34, redundante_con_estandar_34=el_es34)
        if v == EXCLUIDA:
            f.update(su_33=np.nan, p_33=np.nan, q_33=np.nan, dif_q=np.nan, su_identica=True, p_identico=True, q_menor_0_10_33='', q_menor_0_05_33='', rho_q_33=np.nan, clase_33='Excluida por dominancia', fcbf_adaptado_33='', redundante_con_adaptado_33='',
                     fcbf_estandar_33='', redundante_con_estandar_33='', cambia_q_0_10=False, cambia_q_0_05=False, cambia_clase=False, cambia_fcbf=False)
        else:
            b = r33.loc[v]
            ad33, el_ad33 = _decision(t['decisiones_fcbf'], 'adaptado', v)
            es33, el_es33 = _decision(t['decisiones_fcbf'], 'estandar', v)
            f.update(su_33=b['su'], p_33=b['p'], q_33=b['q'], dif_q=b['q'] - a['q'], su_identica=K._txt(b['su']) == K._txt(a['su']), p_identico=K._txt(b['p']) == K._txt(a['p']), q_menor_0_10_33=bool(b['q_bajo_0_10']), q_menor_0_05_33=bool(b['q_bajo_0_05']),
                     rho_q_33=d33.loc[v, 'rho_q'], clase_33=d33.loc[v, 'clase'], fcbf_adaptado_33=ad33, redundante_con_adaptado_33=el_ad33, fcbf_estandar_33=es33, redundante_con_estandar_33=el_es33,
                     cambia_q_0_10=bool(a['q_bajo_0_10']) != bool(b['q_bajo_0_10']), cambia_q_0_05=bool(a['q_bajo_0_05']) != bool(b['q_bajo_0_05']), cambia_clase=d34.loc[v, 'clase'] != d33.loc[v, 'clase'], cambia_fcbf=(ad34, el_ad34, es34, el_es34) != (ad33, el_ad33, es33, el_es33))
        f['explicacion'] = explicar_cambio(f)
        filas.append(f)
    orden = ['variable', 'permutaciones', 'poblacion', 'n', 'su_34', 'su_33', 'su_identica', 'p_34', 'p_33', 'p_identico', 'q_34', 'q_33', 'dif_q', 'q_menor_0_10_34', 'q_menor_0_10_33', 'cambia_q_0_10', 'q_menor_0_05_34', 'q_menor_0_05_33', 'cambia_q_0_05', 'rho_q_34', 'rho_q_33',
             'clase_34', 'clase_33', 'cambia_clase', 'fcbf_adaptado_34', 'redundante_con_adaptado_34', 'fcbf_adaptado_33', 'redundante_con_adaptado_33', 'fcbf_estandar_34', 'redundante_con_estandar_34', 'fcbf_estandar_33', 'redundante_con_estandar_33', 'cambia_fcbf', 'explicacion']
    return pd.DataFrame(filas)[orden]


def tabla_reutilizacion(g, t, n):
    r34 = g['relevancia_34'][g['relevancia_34']['variable'] != EXCLUIDA].sort_values('variable').reset_index(drop=True)
    r33 = t['relevancia_33'].sort_values('variable').reset_index(drop=True)
    return pd.DataFrame([{'permutaciones': n, 'elemento': 'SU de variables', 'n_comparados': len(r33), 'iguales': int(sum(K._txt(a) == K._txt(b) for a, b in zip(r34['su'], r33['su']))), 'tratamiento': 'recalculada desde los datos y comparada'},
                         {'permutaciones': n, 'elemento': 'tamaño de población', 'n_comparados': len(r33), 'iguales': int((r34['n'].astype(int) == r33['n'].astype(int)).sum()), 'tratamiento': 'recalculado y comparado'},
                         {'permutaciones': n, 'elemento': 'k de variables', 'n_comparados': len(r33), 'iguales': int((r34['k'].astype(int) == r33['k'].astype(int)).sum()), 'tratamiento': 'reutilizado'},
                         {'permutaciones': n, 'elemento': 'p de variables', 'n_comparados': len(r33), 'iguales': int(sum(K._txt(a) == K._txt(b) for a, b in zip(r34['p'], r33['p']))), 'tratamiento': 'reutilizado'},
                         {'permutaciones': n, 'elemento': 'pares entre relevantes', 'n_comparados': len(t['pares_relevantes']), 'iguales': len(t['pares_relevantes'].merge(g['pares_relevantes'], on=['variable_1', 'variable_2', 'n'])), 'tratamiento': 'p reutilizado, q recalculado'},
                         {'permutaciones': n, 'elemento': 'permutaciones nuevas', 'n_comparados': 0, 'iguales': 0, 'tratamiento': 'ninguna'}])


# --- Diagnóstico de dominancia -----------------------------------------------------------------------------------------

def dominancia(x):
    valores, conteos = np.unique(np.asarray(x), return_counts=True)
    i = int(conteos.argmax())
    return valores[i], int(conteos[i]), len(x), 100 * conteos[i] / len(x)


def tabla_dominancia(datos, esc34):
    """Con los valores de cada variable en su población, más lo registrado en la Fase 35A para las 529."""
    registro = pd.read_csv(P.RESULTADOS / 'variables_baja_variabilidad.csv', encoding='utf-8-sig').set_index('variable')
    resumen = pd.read_csv(P.RESULTADOS / 'eda_univariado_resumen.csv', encoding='utf-8-sig').set_index('variable')
    codigos, filas = esc34.datos(), []
    poblaciones = {'general': np.ones(len(esc34.base.objetivo), dtype=bool), 'laboral': esc34.base.mascara, 'cuidadoras': esc34.poblacion}
    for v in R.VARIABLES_34:
        pob = R.poblacion_de(esc34, v)
        _, cuenta, n, pct = dominancia(np.asarray(codigos[v])[poblaciones[pob]])
        f = {'variable': v, 'etiqueta': V.etiqueta(v), 'tipo': R.ORIENTACION[v].tipo, 'poblacion_propia': pob, 'n_propia': n, 'n_dominante': cuenta, 'pct_dominante_propia': pct,
             'pct_dominante_fase35a': registro.loc[v, 'porcentaje_dominancia'] if v in registro.index else np.nan, 'decision_fase35a': registro.loc[v, 'decision'] if v in registro.index else 'no registrada: continua, se mide por tramos de SU'}
        for nombre, m in poblaciones.items():
            if nombre == 'general' and pob != 'general':
                continue
            aplica = (pob == 'general') or (nombre == pob)
            f[f'pct_dominante_{nombre}'] = dominancia(np.asarray(codigos[v])[m])[3] if aplica else np.nan
        base = {'frecuencia_fuerza': 'realiza_fuerza', 'frecuencia_aerobico': 'realiza_aerobico', 'frecuencia_bajo_impacto': 'realiza_bajo_impacto'}.get(v, v)
        f['pct_dominante_sin_imputados_34B'] = resumen.loc[base, 'pct_dominante_sin_imputados_34B'] if base in resumen.index else np.nan
        f['supera_85_regla'] = pct > UMBRAL_DOMINANCIA
        f['supera_85_subpoblacion'] = any(pd.notna(f.get(f'pct_dominante_{x}')) and f[f'pct_dominante_{x}'] > UMBRAL_DOMINANCIA for x in ('laboral', 'cuidadoras') if pob == 'general' or x == pob)
        f['decision_corregida'] = 'excluir por dominancia' if v == EXCLUIDA else 'conservar'
        filas.append(f)
    return pd.DataFrame(filas).sort_values('pct_dominante_propia', ascending=False, ignore_index=True)


def problemas_dominancia(t):
    problemas = []
    x = t.set_index('variable')
    if not x.loc[EXCLUIDA, 'pct_dominante_propia'] > UMBRAL_DOMINANCIA:
        problemas.append('La variable excluida no supera el umbral.')
    otras = x[(x.index != EXCLUIDA) & x['supera_85_regla']].index.tolist()
    if otras:
        problemas.append(f'Otras variables superan el umbral: {otras}')
    return problemas


def tabla_elegibles(t10, dominio):
    r = t10['relevancia_33'].set_index('variable')
    d = dominio.set_index('variable')
    return pd.DataFrame([{'orden': i, 'variable': v, 'etiqueta': V.etiqueta(v), 'tipo': R.ORIENTACION[v].tipo, 'poblacion': r.loc[v, 'poblacion'], 'n': int(r.loc[v, 'n']), 'antigua_control': v in CONTROLES_33,
                          'pct_dominante_poblacion': d.loc[v, 'pct_dominante_propia'], 'origen': 'en memoria desde el conjunto limpio; n = 239 observadas, 251 con 12 imputadas' if v == R.SOBRECARGA else 'dataset_fase35_33_variables.csv'} for i, v in enumerate(VARIABLES_33, 1)])


# --- Salidas -------------------------------------------------------------------------------------------------------------

class Escritor:
    """Nunca sobrescribe y solo escribe dentro de la carpeta de la corrección o el conjunto nuevo."""

    def __init__(self):
        self.escritos = []

    def _preparar(self, ruta):
        ruta = Path(ruta)
        dentro = Path(CARPETA).resolve() in ruta.resolve().parents or ruta.resolve() == DATASET_33.resolve()
        if not dentro:
            raise PermissionError(f'Ruta fuera de la corrección: {ruta}')
        if ruta.exists():
            raise FileExistsError(f'No se sobrescribe: {ruta}')
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self.escritos.append(ruta)
        return ruta

    def tabla(self, ruta, df):
        df.to_csv(self._preparar(ruta), index=False, encoding='utf-8-sig', float_format=P.FORMATO)

    def texto(self, ruta, texto):
        self._preparar(ruta).write_text(texto, encoding='utf-8')

    def bytes(self, ruta, contenido):
        self._preparar(ruta).write_bytes(contenido)


def nota_35a(dom, comp):
    x = dom.set_index('variable')
    d = x.loc[EXCLUIDA]
    resumen = pd.read_csv(P.RESULTADOS / 'eda_univariado_resumen.csv', encoding='utf-8-sig').set_index('variable')
    return f"""# Corrección de la Fase 35A: `{EXCLUIDA}`

*Generado por `analisis/revision_33_variables.py` el {datetime.now():%d-%m-%Y}. Los registros históricos de la Fase 35A no se modifican.*

## Dominancia

«No» concentra **{d['n_dominante']} de {d['n_propia']} respuestas ({P._n(d['pct_dominante_propia'], 2)} %)**, sobre el umbral estricto de {UMBRAL_DOMINANCIA} %. Sin las {int(resumen.loc[EXCLUIDA, 'imputados_34B'])} imputaciones de la Fase 34B sería {P._n(resumen.loc[EXCLUIDA, 'pct_dominante_sin_imputados_34B'], 2)} %: también lo supera.

## Excepción que se revierte

`preprocesamiento/configuracion.py` y `resultados/usuaria/variables_baja_variabilidad.csv` registran la decisión del 28-10-2026: «conservar (excepción)», por ser factor validado por la profesora el 20-10 y variable de control. La corrección aplica el criterio sin excepciones.

**`configuracion.py` no se modifica,** porque es código congelado. Si alguna vez se ejecuta `preprocesar_fase35.py` sin actualizarlo, la variable volvería a aparecer.

## Las demás variables

Ninguna de las otras 33 supera {UMBRAL_DOMINANCIA} % en su población. La más alta es `frecuencia_fuerza`, con {P._n(x.loc['frecuencia_fuerza', 'pct_dominante_propia'], 2)} %. Dentro de las cuidadoras llega a {P._n(x.loc['frecuencia_fuerza', 'pct_dominante_cuidadoras'], 2)} %; la regla se definió sobre la población de cada variable, de modo que esto solo se informa.

## Conjunto de datos

`datos/analitico/dataset_fase35_33_variables.csv`: {comp['filas'].iloc[0]} participantes y {len(comp) - 1} columnas. {int((comp['identica'] == True).sum())} columnas conservadas son idénticas, texto a texto, a `dataset_fase35.csv`, que no cambió. No se ejecutó la limpieza.

- `prevision` y `doble_carga` siguen como columnas, pero no son elegibles.
- `sobrecarga_fisica_emocional` es elegible, pero no es columna: se incorpora en memoria desde el conjunto limpio. La Fase 36 deberá decidir cómo representarla.
- `dataset_fase35b.csv` es un producto histórico que todavía incluye la variable excluida: **no debe usarse como entrada de la Fase 36.**

La lista de elegibles está en `predictores_elegibles_33.csv`.
"""


def calcular(datos, poblacion):
    esc34 = R.construir_escenario(datos, poblacion)
    esc = construir_escenario_33(esc34)
    if {v: esc34.indice()[v] for v in esc.indice()} != esc.indice():
        raise RuntimeError('El mapa de índices cambió.')
    with sin_permutaciones():
        versiones = {n: version_33(datos, esc, n) for n in VERSIONES}
    return esc34, esc, versiones


def archivos_vigilados():
    revision = [r for r in R.CARPETA.rglob('*') if r.is_file() and Path(CARPETA).resolve() not in r.resolve().parents]
    return sorted({*B.archivos_vigilados(), *revision, *B.SALIDA.glob('*'), DATASET_ORIGINAL, P.RUTAS_REALES.dataset, Path(R.__file__).resolve(), Path(B.__file__).resolve(), Path(I.__file__).resolve(), P.ANALISIS / 'informe_word_35b.py'})


def correr(datos, poblacion, huellas):
    esc34, esc, versiones = calcular(datos, poblacion)
    dom = tabla_dominancia(datos, esc34)
    problemas = problemas_dominancia(dom)
    original, fin = leer_filas(DATASET_ORIGINAL)
    nueva = quitar_columna(original, EXCLUIDA)
    contenido = filas_a_bytes(nueva, fin)
    releida = list(csv.reader(io.StringIO(contenido.decode('utf-8-sig'), newline='')))
    comp = comparar_columnas(original, releida)
    problemas += problemas_columnas(comp, original, releida)
    if problemas:
        raise RuntimeError('; '.join(problemas))

    comparaciones = {n: tabla_34_33(g, t, n) for n, (t, g, _) in versiones.items()}
    reutilizacion = pd.concat([tabla_reutilizacion(g, t, n) for n, (t, g, _) in versiones.items()], ignore_index=True)
    fcbf = pd.concat([c[['variable', 'permutaciones', 'fcbf_adaptado_34', 'redundante_con_adaptado_34', 'fcbf_adaptado_33', 'redundante_con_adaptado_33', 'fcbf_estandar_34', 'redundante_con_estandar_34', 'fcbf_estandar_33', 'redundante_con_estandar_33', 'cambia_fcbf']] for c in comparaciones.values()], ignore_index=True)
    a, b = alias(versiones[10000][0]), alias(versiones[50000][0])
    c1050, f1050, previas = I.tabla_comparacion(a, b), I.tabla_fcbf(a, b), I.tabla_versiones_previas()

    salida = Escritor()
    salida.bytes(DATASET_33, contenido)
    salida.tabla(CARPETA / 'fase35a' / 'diagnostico_dominancia.csv', dom)
    salida.tabla(CARPETA / 'fase35a' / 'comparacion_columnas_dataset.csv', comp)
    salida.tabla(CARPETA / 'fase35a' / 'predictores_elegibles_33.csv', tabla_elegibles(versiones[10000][0], dom))
    salida.texto(CARPETA / 'fase35a' / 'nota_correccion_35a.md', nota_35a(dom, comp))
    for n, (t, _, _) in versiones.items():
        for nombre, df in t.items():
            salida.tabla(VERSIONES[n][2] / f'{nombre}.csv', df)
    salida.tabla(CARPETA / 'comparacion_34_33' / 'comparacion_10000.csv', comparaciones[10000])
    salida.tabla(CARPETA / 'comparacion_34_33' / 'comparacion_50000.csv', comparaciones[50000])
    salida.tabla(CARPETA / 'comparacion_34_33' / 'fcbf_34_33.csv', fcbf)
    salida.tabla(CARPETA / 'comparacion_34_33' / 'reutilizacion.csv', reutilizacion)
    salida.tabla(CARPETA / 'informe' / 'comparacion_10000_50000.csv', c1050)
    salida.tabla(CARPETA / 'informe' / 'fcbf_10000_50000.csv', f1050)
    salida.tabla(CARPETA / 'informe' / 'versiones_previas.csv', previas)
    lineas = ['LOG corrección de 34 a 33 variables, Fases 35A y 35B', f'Fecha: {datetime.now():%Y-%m-%d %H:%M}', f'HEAD: {P._git("rev-parse", "HEAD").strip()}', f'Variable excluida: {EXCLUIDA}', 'Permutaciones nuevas: 0',
              f'Versiones: Python {sys.version.split()[0]}, numpy {np.__version__}, pandas {pd.__version__}']
    for n, (t, _, ev) in versiones.items():
        lineas += [f'{n}: q<0,10 = {";".join(ev.medidas.relevantes)}', f'{n}: adaptado = {";".join(F.seleccionadas(ev.adaptado))}', f'{n}: estandar = {";".join(F.seleccionadas(ev.estandar))}']
    lineas += [f'SHA-256 {k}: {v}' for k, v in huellas.items()]
    lineas.append(f'SHA-256 {DATASET_33.name}: {hashlib.sha256(contenido).hexdigest()}')
    salida.texto(CARPETA / 'log_revision_33.txt', '\n'.join(lineas) + '\n')
    return versiones, comparaciones, dom


def alias(t):
    """Las funciones del informe integrado esperan la clave histórica de la tabla de relevancia."""
    return {**t, 'relevancia_34': t['relevancia_33']}


def main():
    parser = argparse.ArgumentParser(description='Corrección de 34 a 33 variables, Fases 35A y 35B.')
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument('--verificar', action='store_true')
    modo.add_argument('--ejecutar', action='store_true')
    parser.add_argument('--autorizado-por-usuaria', action='store_true')
    args = parser.parse_args()
    if args.ejecutar and not args.autorizado_por_usuaria:
        sys.exit('La ejecución requiere --autorizado-por-usuaria.')
    datos, poblacion, problemas = R.comprobar_datos_reales()
    problemas = [*K.estado_inicial(), *problemas]
    for problema in problemas:
        print(f'[FALLA] {problema}')
    if problemas:
        sys.exit('El estado inicial tiene fallas.')
    if args.verificar:
        esc34, _, versiones = calcular(datos, poblacion)
        print(f'Sin permutaciones. Dominancia: {problemas_dominancia(tabla_dominancia(datos, esc34)) or "correcta"}.')
        for n, (t, _, ev) in versiones.items():
            print(f'{n}: relevantes {ev.medidas.relevantes}')
        return
    huellas = {r.name: P.sha256(r) for r in (Path(__file__).resolve(), PROTOCOLO)}
    antes = P.manifiesto(archivos_vigilados())
    versiones, comparaciones, dom = correr(datos, poblacion, huellas)
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(archivos_vigilados()))
    if cambiados:
        sys.exit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    for n, c in comparaciones.items():
        print(f'{n}: cambian q<0,10 {int(c["cambia_q_0_10"].sum())}, q<0,05 {int(c["cambia_q_0_05"].sum())}, clase {int(c["cambia_clase"].sum())}, FCBF {int(c["cambia_fcbf"].sum())}.')
    print(f'Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
