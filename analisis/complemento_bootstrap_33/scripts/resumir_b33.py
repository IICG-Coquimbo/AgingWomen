"""Resume los 500 remuestreos: frecuencias, SU, FCBF, global, comparaciones y figuras. Solo lee la caché y los archivos
históricos; no ejecuta permutaciones. Uso, desde scripts/: python resumir_b33.py"""
import hashlib
import json
import platform
import sys
from datetime import datetime
from itertools import combinations

import numpy as np
import pandas as pd
import scipy

import nucleo_b33 as N
from preprocesamiento import estabilidad as S

B = N.BASE
ANT = N.ANALISIS / 'resultados' / 'usuaria'
FIG_ANT = N.ANALISIS / 'figuras' / 'seleccion_35b' / 'estabilidad_seleccion.png'
LOG_ANT = ANT / 'log_seleccion_fase35b.txt'
LOG_33 = N.V33.CARPETA / 'log_revision_33.txt'
DIRS = {k: B / k for k in ('configuracion', 'remuestreos', 'resultados', 'comparacion', 'figuras')}
SCRIPTS = ['nucleo_b33.py', 'ejecutar_b33.py', 'resumir_b33.py', 'pruebas_b33.py', 'integridad_b33.py']


def sha(ruta):
    return hashlib.sha256(open(ruta, 'rb').read()).hexdigest()


def guardar(df, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding='utf-8')


def a_json(obj, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=float), encoding='utf-8')


def leer_cache():
    rem = []
    for i in range(N.N_REMUESTREOS):
        ruta = N.CACHE / f'rem_{i:04d}.json'
        if not ruta.exists():
            raise SystemExit(f'Falta el remuestreo {i}: la ejecución no terminó.')
        rem.append(json.loads(ruta.read_text(encoding='utf-8')))
    if [r['remuestreo'] for r in rem] != list(range(N.N_REMUESTREOS)):
        raise SystemExit('Numeración de remuestreos incorrecta.')
    return rem


def poblacion(v):
    return 'cuidadoras (239)' if v == N.SOBRECARGA else 'laboral (287)' if v in N.C.LABORALES_35B else 'general (529)'


def rol_fase36(v):
    if v in N.C.LABORALES_35B or v == N.SOBRECARGA:
        return 'módulo aparte (no entra al PCA de A)'
    if v == 'imc':
        return 'matriz global P1/F1; fuera de P2 (A)'
    return 'matriz global P1 y P2 (A)'


def definitiva():
    d = N.seleccion_definitiva()
    out = {}
    for n in (10000, 50000):
        t = d[n]['decisiones']
        out[n] = {var: dict(zip(t[t.variante == var]['variable'], t[t.variante == var]['decision'])) for var in N.VARIANTES}
        out[n]['relevancia'] = d[n]['relevancia'].set_index('variable')
    if out[10000]['adaptado'] != out[50000]['adaptado'] or out[10000]['estandar'] != out[50000]['estandar']:
        raise SystemExit('Las selecciones definitivas de 10.000 y 50.000 difieren: revisar antes de comparar.')
    return out


def matriz(rem, variante, estado='seleccionada'):
    return np.array([[r[variante][v][0] == estado for v in N.VARIABLES_33] for r in rem], dtype=int)


def main():
    rem = leer_cache()
    dfn = definitiva()
    sel_def = {var: sorted(v for v, d in dfn[50000][var].items() if d == 'seleccionada') for var in N.VARIANTES}
    rel_def = dfn[50000]['relevancia']
    _, _, esc = N.cargar()

    # --- configuración --------------------------------------------------------------------------------------------
    import matplotlib
    conf = {
        'descripcion': 'Complemento retrospectivo de la Fase 35B: estabilidad de la selección con las 33 candidatas finales',
        'ejecutado_despues_de': 'cierre de las Fases 36 a 39',
        'n_remuestreos': N.N_REMUESTREOS, 'n_permutaciones_por_remuestreo': N.N_PERMUTACIONES, 'alfa_q': N.ALFA,
        'tolerancia_su': N.C.TOLERANCIA_SU_35B, 'semilla_raiz': N.C.SEMILLA, 'id_analisis': N.ID_ANALISIS,
        'clave_semilla': 'SeedSequence(42, spawn_key=(id_analisis, remuestreo, tipo, indice)); tipo 0 bootstrap, 1 relevancia, 2 par',
        'indice_semilla': 'alfabético entre las 34 de la revisión 03-11 (mapa de revision_33_variables)',
        'remuestreo': 'bootstrap estratificado por severo_mrs, con reemplazo, 281 + 248 = 529 filas',
        'familia_bh': 33, 'variantes': list(N.VARIANTES), 'etapas': ['no laboral', 'laboral', 'cuidadoras'],
        'objetivo_su': 'severo_mrs (MRS >= 16), igual que la selección definitiva',
        'candidatas': N.VARIABLES_33, 'excluidas': N.EXCLUIDAS,
        'poblaciones': {'general': 529, 'laboral': 287, 'cuidadoras_observadas': 239},
        'procesos': 1,
        'versiones': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
                      'scipy': scipy.__version__, 'matplotlib': matplotlib.__version__},
        'git_head': json.loads((B / 'integridad' / 'manifiesto_antes.json').read_text(encoding='utf-8'))['git']['head'],
        'protocolo_sha256': json.loads((B / 'protocolo' / 'sello.json').read_text(encoding='utf-8'))['sha256'],
        'entradas_sha256': {str(p.relative_to(N.ANALISIS.parent).as_posix()): sha(p) for p in [
            N.P.ENTRADA, N.P.LIMPIO, N.M.SUCIO, N.V33.CARPETA / 'permutaciones_10000' / 'decisiones_fcbf.csv',
            N.V33.CARPETA / 'permutaciones_50000' / 'decisiones_fcbf.csv', N.V33.CARPETA / 'permutaciones_50000' / 'relevancia_33.csv',
            ANT / 'estabilidad_remuestreos.csv', ANT / 'estabilidad_fcbf.csv', ANT / 'estabilidad_global.csv', LOG_ANT, LOG_33, FIG_ANT]},
        'codigo_reutilizado_sha256': {p.name: sha(p) for p in [
            N.ANALISIS / 'preprocesamiento' / f for f in ('fcbf.py', 'entropia.py', 'estabilidad.py', 'configuracion.py')] + [
            N.ANALISIS / f for f in ('complementario_cuidados.py', 'revision_35b_reunion_1103.py', 'revision_33_variables.py',
                                     'seleccionar_fase35b.py', 'complementario_fase35b.py')]},
        'codigo_propio_sha256': {f: sha(N.AQUI / f) for f in SCRIPTS if (N.AQUI / f).exists()},
        'ejecucion': json.loads((B / 'remuestreos' / 'ejecucion.json').read_text(encoding='utf-8')),
        'fecha_resumen': datetime.now().isoformat(timespec='seconds'),
    }
    a_json(conf, DIRS['configuracion'] / 'configuracion.json')
    filas = [{'variable': v, 'estado': 'candidata', 'poblacion': poblacion(v), 'rol_fase36': rol_fase36(v), 'motivo': ''} for v in N.VARIABLES_33]
    motivos = {'doble_carga': 'excluida de SU/FCBF desde la revisión del 03-11 (derivada de trabajo y cuidado)',
               'prevision': 'excluida del filtro y del modelado (protocolo 35B, pendiente)',
               'usa_medicamentos_diabetes': 'excluida por dominancia > 85 % (corrección 34 -> 33)'}
    filas += [{'variable': v, 'estado': 'excluida', 'poblacion': '', 'rol_fase36': 'no entra', 'motivo': m} for v, m in motivos.items()]
    guardar(pd.DataFrame(filas), DIRS['configuracion'] / 'candidatas_y_exclusiones.csv')
    a_json({'semilla_raiz': 42, 'id_analisis': N.ID_ANALISIS, 'indices_semilla': esc.indice(),
            'tipos': {'bootstrap': 0, 'relevancia': 1, 'par': 2}, 'factor_par': N.F.FACTOR_PAR,
            'n_permutaciones': N.N_PERMUTACIONES, 'lote_permutaciones': N.E.LOTE_PERMUTACIONES, 'alfa': N.ALFA,
            'tolerancia': N.C.TOLERANCIA_SU_35B}, DIRS['configuracion'] / 'semillas_y_parametros.json')

    # --- por remuestreo -------------------------------------------------------------------------------------------
    Z = {var: matriz(rem, var) for var in N.VARIANTES}
    REL = np.array([[v in r['relevantes'] for v in N.VARIABLES_33] for r in rem], dtype=int)
    det = []
    for var in N.VARIANTES:
        for r, fila in zip(rem, Z[var]):
            s = [v for v, z in zip(N.VARIABLES_33, fila) if z]
            det.append({'variante': var, 'remuestreo': r['remuestreo'], 'personas_distintas': r['n_unicas'],
                        'n_laboral': r['n_laboral'], 'n_cuidadoras': r['n_cuidadoras'], 'n_severas': r['n_severas'],
                        'n_relevantes': len(r['relevantes']), 'n_pares': r['n_pares'], 'n_seleccionadas': len(s),
                        'seleccionadas': ';'.join(s), 'relevantes': ';'.join(r['relevantes']),
                        'jaccard_con_definitiva': S.jaccard(s, sel_def[var]), 'igual_a_definitiva': s == sel_def[var],
                        'indices_sha256': r['indices_sha256']})
    det = pd.DataFrame(det)
    guardar(det, DIRS['remuestreos'] / 'remuestreos_33.csv')

    # --- frecuencias por variable -------------------------------------------------------------------------------
    frec = []
    for var in N.VARIANTES:
        for j, v in enumerate(N.VARIABLES_33):
            dec = [r[var][v] for r in rem]
            elim = pd.Series([d[1] for d in dec if d[0] == 'redundante'], dtype=object)
            k = int(Z[var][:, j].sum())
            frec.append({
                'variante': var, 'variable': v, 'poblacion': poblacion(v), 'veces_seleccionada': k,
                'pct_seleccionada': 100 * k / len(rem), 'pct_relevante_su': 100 * REL[:, j].mean(),
                'pct_redundante': 100 * np.mean([d[0] == 'redundante' for d in dec]),
                'pct_no_relevante': 100 * np.mean([d[0] == 'no relevante' for d in dec]),
                'eliminadora_mas_frecuente': elim.mode().sort_values().iloc[0] if len(elim) else '',
                'banda_descriptiva_protocolo_35b': S.banda(100 * k / len(rem)),
                'estado_definitivo': dfn[50000][var].get(v, 'no relevante'),
                'relevante_definitiva_q010': bool(rel_def.loc[v, 'q_bajo_0_10']),
                'q_definitiva_50000': float(rel_def.loc[v, 'q']), 'su_definitiva': float(rel_def.loc[v, 'su']),
                'rol_fase36': rol_fase36(v)})
    frec = pd.DataFrame(frec).sort_values(['variante', 'pct_seleccionada', 'variable'], ascending=[True, False, True])
    guardar(frec, DIRS['resultados'] / 'frecuencias_seleccion.csv')

    # --- SU ------------------------------------------------------------------------------------------------------
    su = []
    for j, v in enumerate(N.VARIABLES_33):
        s = np.array([r['su'][v] for r in rem]); q = np.array([r['q'][v] for r in rem]); n = np.array([r['n'][v] for r in rem])
        su.append({'variable': v, 'poblacion': poblacion(v), 'veces_relevante': int(REL[:, j].sum()), 'pct_relevante_q010': 100 * REL[:, j].mean(),
                   'su_mediana': np.median(s), 'su_p05': np.percentile(s, 5), 'su_p95': np.percentile(s, 95),
                   'q_mediana': np.median(q), 'pct_q_bajo_005': 100 * (q < 0.05).mean(), 'n_mediano': float(np.median(n)),
                   'su_definitiva': float(rel_def.loc[v, 'su']), 'q_definitiva_50000': float(rel_def.loc[v, 'q']),
                   'relevante_definitiva': bool(rel_def.loc[v, 'q_bajo_0_10'])})
    su = pd.DataFrame(su).sort_values(['pct_relevante_q010', 'variable'], ascending=[False, True])
    guardar(su, DIRS['resultados'] / 'resultados_su.csv')

    # --- FCBF: entre las relevantes, cuántas veces sobrevive y quién la elimina --------------------------------------
    fc = []
    for var in N.VARIANTES:
        for j, v in enumerate(N.VARIABLES_33):
            nrel = int(REL[:, j].sum())
            elim = pd.Series([r[var][v][1] for r in rem if r[var][v][0] == 'redundante'], dtype=object).value_counts()
            fc.append({'variante': var, 'variable': v, 'veces_relevante': nrel, 'veces_seleccionada': int(Z[var][:, j].sum()),
                       'pct_sobrevive_si_relevante': 100 * Z[var][:, j].sum() / nrel if nrel else np.nan,
                       'veces_redundante': int(elim.sum()),
                       'principales_eliminadoras': '; '.join(f'{a} ({b})' for a, b in elim.head(3).items())})
    fc = pd.DataFrame(fc).sort_values(['variante', 'veces_seleccionada', 'variable'], ascending=[True, False, True])
    guardar(fc, DIRS['resultados'] / 'resultados_fcbf.csv')

    # --- global ----------------------------------------------------------------------------------------------------
    glob = []
    for var in N.VARIANTES:
        nog = S.nogueira(Z[var]); t = Z[var].sum(axis=1); dv = det[det.variante == var]
        glob.append({'variante': var, 'remuestreos': len(rem), 'candidatas': 33, 'nogueira': nog['indice'],
                     'nogueira_ic95_inferior': nog['ic_inferior'], 'nogueira_ic95_superior': nog['ic_superior'],
                     'jaccard_promedio_entre_remuestreos': S.jaccard_promedio(Z[var]),
                     'tamano_medio': t.mean(), 'tamano_de': t.std(ddof=1), 'tamano_mediano': float(np.median(t)),
                     'tamano_minimo': int(t.min()), 'tamano_maximo': int(t.max()),
                     'seleccion_definitiva': ';'.join(sel_def[var]), 'tamano_definitiva': len(sel_def[var]),
                     'jaccard_medio_con_definitiva': dv['jaccard_con_definitiva'].mean(),
                     'pct_remuestreos_igual_a_definitiva': 100 * dv['igual_a_definitiva'].mean(),
                     'relevantes_medio': REL.sum(axis=1).mean(), 'relevantes_minimo': int(REL.sum(axis=1).min()),
                     'relevantes_maximo': int(REL.sum(axis=1).max()), 'nogueira_relevancia': S.nogueira(REL)['indice']})
    glob = pd.DataFrame(glob)
    guardar(glob, DIRS['resultados'] / 'resultado_global.csv')
    a_json(glob.to_dict(orient='records'), DIRS['resultados'] / 'resultado_global.json')
    dist = pd.concat([pd.Series(Z[var].sum(axis=1)).value_counts().sort_index().rename_axis('tamano').reset_index(name='remuestreos').assign(variante=var)
                      for var in N.VARIANTES])[['variante', 'tamano', 'remuestreos']]
    guardar(dist, DIRS['resultados'] / 'distribucion_tamano_seleccion.csv')

    # --- lectura descriptiva NO especificada en el protocolo (añadida tras ver las frecuencias) ------------------
    # Las tres variables de ejercicio de la definitiva son relevantes juntas y FCBF se queda con una u otra.
    bloques = {'ejercicio (fuerza, días, bajo impacto)': ['frecuencia_fuerza', 'dias_ejercicio_semana', 'frecuencia_bajo_impacto'],
               'imc o trabaja_actualmente': ['imc', 'trabaja_actualmente'],
               'lugar_trabajo_comprensivo o estres_entorno_laboral': list(N.C.LABORALES_35B)}
    seis = sorted(rel_def.index[rel_def['q_bajo_0_10'].astype(bool)])
    bl = []
    for var in N.VARIANTES:
        for nombre, vs in bloques.items():
            j = [N.VARIABLES_33.index(v) for v in vs]
            k = Z[var][:, j].sum(axis=1)
            bl.append({'variante': var, 'bloque': nombre, 'pct_al_menos_una_seleccionada': 100 * (k >= 1).mean(),
                       'pct_dos_o_mas_seleccionadas': 100 * (k >= 2).mean(), 'pct_al_menos_una_relevante': 100 * (REL[:, j].sum(axis=1) >= 1).mean()})
        j6 = [N.VARIABLES_33.index(v) for v in seis]
        bl.append({'variante': var, 'bloque': 'las 6 relevantes de la definitiva, todas relevantes a la vez',
                   'pct_al_menos_una_relevante': 100 * REL[:, j6].all(axis=1).mean()})
    guardar(pd.DataFrame(bl), DIRS['resultados'] / 'bloques_posthoc_descriptivo.csv')

    # --- dependencia de personas (descriptiva) ------------------------------------------------------------------
    pres = np.zeros((len(rem), 529), dtype=bool)
    for r in rem:
        idx = N.indices(esc, r['remuestreo'])
        if hashlib.sha256(np.asarray(idx, dtype=np.int64).tobytes()).hexdigest() != r['indices_sha256']:
            raise SystemExit('Los índices recalculados no coinciden con los guardados.')
        pres[r['remuestreo'], np.unique(idx)] = True
    dep = []
    for var in ('adaptado',):
        for j, v in enumerate(N.VARIABLES_33):
            z = Z[var][:, j].astype(float); p = z.mean()
            if p < 0.05 or p > 0.95:
                continue
            con = (z[:, None] * pres).sum(0) / pres.sum(0); sin = (z[:, None] * ~pres).sum(0) / (~pres).sum(0)
            dif = 100 * (sin - con)                  # cuánto cambia la selección cuando la persona NO está
            se = 100 * np.sqrt(p * (1 - p) * (1 / pres.sum(0) + 1 / (~pres).sum(0)))
            zt = dif / se
            corr_u = np.corrcoef(z, [r['n_unicas'] for r in rem])[0, 1]
            fila = {'variante': var, 'variable': v, 'pct_seleccionada': 100 * p,
                    'max_abs_cambio_al_excluir_una_persona_pp': float(np.abs(dif).max()),
                    'personas_con_abs_z_mayor_3': int((np.abs(zt) > 3).sum()),
                    'esperado_por_azar_abs_z_mayor_3': round(529 * 0.0027, 1),
                    'max_abs_z': float(np.abs(zt).max()), 'corr_con_personas_distintas': corr_u}
            if v in N.C.LABORALES_35B:
                fila['corr_con_n_laboral'] = np.corrcoef(z, [r['n_laboral'] for r in rem])[0, 1]
            if v == N.SOBRECARGA:
                fila['corr_con_n_cuidadoras'] = np.corrcoef(z, [r['n_cuidadoras'] for r in rem])[0, 1]
            dep.append(fila)
    guardar(pd.DataFrame(dep), DIRS['resultados'] / 'dependencia_de_participantes.csv')

    # --- comparación con la selección definitiva ----------------------------------------------------------------
    a = frec[frec.variante == 'adaptado'].set_index('variable'); e = frec[frec.variante == 'estandar'].set_index('variable')
    comp = pd.DataFrame({'variable': N.VARIABLES_33})
    comp['estado_definitivo_adaptado'] = comp.variable.map(a['estado_definitivo'])
    comp['estado_definitivo_estandar'] = comp.variable.map(e['estado_definitivo'])
    comp['relevante_definitiva'] = comp.variable.map(a['relevante_definitiva_q010'])
    comp['pct_relevante_su'] = comp.variable.map(a['pct_relevante_su'])
    comp['pct_seleccionada_adaptado'] = comp.variable.map(a['pct_seleccionada'])
    comp['pct_seleccionada_estandar'] = comp.variable.map(e['pct_seleccionada'])
    comp['banda_descriptiva_adaptado'] = comp.variable.map(a['banda_descriptiva_protocolo_35b'])
    comp['lectura'] = np.select(
        [comp.estado_definitivo_adaptado.eq('seleccionada'), comp.relevante_definitiva & comp.estado_definitivo_adaptado.eq('redundante'),
         ~comp.relevante_definitiva & (comp.pct_seleccionada_adaptado >= 20)],
        ['seleccionada en la definitiva', 'relevante pero redundante en la definitiva', 'no relevante en la definitiva, pero aparece en al menos 20 % de los remuestreos'],
        'no relevante en la definitiva')
    comp['rol_fase36'] = comp.variable.map(rol_fase36)
    comp = comp.sort_values(['pct_seleccionada_adaptado', 'variable'], ascending=[False, True])
    guardar(comp, DIRS['comparacion'] / 'comparacion_seleccion_definitiva.csv')

    # --- comparación con la corrida antigua --------------------------------------------------------------------
    fa = pd.read_csv(ANT / 'estabilidad_fcbf.csv', encoding='utf-8-sig')
    ga = pd.read_csv(ANT / 'estabilidad_global.csv', encoding='utf-8-sig')
    ra = pd.read_csv(ANT / 'estabilidad_remuestreos.csv', encoding='utf-8-sig', keep_default_na=False)
    viejas = sorted(fa.variable.unique())
    if len(viejas) != 30:
        raise SystemExit('La corrida antigua no tiene 30 candidatas.')
    univ = sorted(set(viejas) | set(N.VARIABLES_33))
    ca = []
    for v in univ:
        f = {'variable': v, 'en_antigua': v in viejas, 'en_33': v in N.VARIABLES_33, 'comparable_solo_descriptivamente': v in viejas and v in N.VARIABLES_33}
        for var in N.VARIANTES:
            old = fa[(fa.variante == var) & (fa.variable == v)]
            f[f'pct_antigua_{var}'] = float(old.pct_seleccionada.iloc[0]) if len(old) else np.nan
            f[f'pct_33_{var}'] = float(frec[(frec.variante == var) & (frec.variable == v)].pct_seleccionada.iloc[0]) if v in N.VARIABLES_33 else np.nan
            f[f'diferencia_descriptiva_{var}_pp'] = round(f[f'pct_33_{var}'] - f[f'pct_antigua_{var}'], 1)
        f['nota'] = ('solo en la antigua' if not f['en_33'] else 'solo en las 33 (antes era control o no existía)' if not f['en_antigua']
                     else 'en ambas; cambió el umbral (0,05 -> 0,10), la familia y la competencia')
        ca.append(f)
    ca = pd.DataFrame(ca).sort_values('pct_33_adaptado', ascending=False)
    guardar(ca, DIRS['comparacion'] / 'comparacion_corrida_antigua_por_variable.csv')
    # pareada: mismas muestras
    par = []
    for var in N.VARIANTES:
        ro = ra[ra.variante == var].set_index('remuestreo')
        dn = det[det.variante == var].set_index('remuestreo')
        for i in range(len(rem)):
            so = set(filter(None, ro.loc[i, 'seleccionadas'].split(';'))); sn = set(filter(None, dn.loc[i, 'seleccionadas'].split(';')))
            comun = set(viejas) & set(N.VARIABLES_33)
            par.append({'variante': var, 'remuestreo': i, 'misma_n_laboral': int(ro.loc[i, 'n_laboral']) == int(dn.loc[i, 'n_laboral']),
                        'n_antigua': len(so), 'n_33': len(sn), 'jaccard_entre_corridas': S.jaccard(so, sn),
                        'jaccard_variables_comunes': S.jaccard(so & comun, sn & comun)})
    par = pd.DataFrame(par)
    guardar(par, DIRS['comparacion'] / 'comparacion_pareada_por_remuestreo.csv')
    resumen = pd.DataFrame([
        {'atributo': 'Fecha', 'antigua': '2026-11-02 21:13', 'complemento_33': datetime.now().strftime('%Y-%m-%d')},
        {'atributo': 'Candidatas', 'antigua': '30', 'complemento_33': '33'},
        {'atributo': 'Excluidas respecto de la otra', 'antigua': 'edad, imc, trabaja_actualmente, usa_medicamentos_diabetes (control), sobrecarga (no existía)',
         'complemento_33': 'doble_carga, usa_medicamentos_diabetes, prevision'},
        {'atributo': 'Método de remuestreo', 'antigua': 'bootstrap estratificado por severo_mrs, con reemplazo', 'complemento_33': 'igual; mismas 500 muestras (misma semilla)'},
        {'atributo': 'Remuestreos', 'antigua': '500', 'complemento_33': '500'},
        {'atributo': 'Permutaciones por remuestreo', 'antigua': '5.000', 'complemento_33': '5.000'},
        {'atributo': 'Umbral de relevancia y de pares', 'antigua': 'q < 0,05', 'complemento_33': 'q < 0,10'},
        {'atributo': 'Familia BH', 'antigua': '30', 'complemento_33': '33'},
        {'atributo': 'Etapas FCBF', 'antigua': 'no laboral, laboral', 'complemento_33': 'no laboral, laboral, cuidadoras'},
        {'atributo': 'Semilla', 'antigua': 'SeedSequence(42, (1, i, tipo, índice de 30))', 'complemento_33': 'SeedSequence(42, (1, i, tipo, índice de 34))'},
        {'atributo': 'Procesos', 'antigua': '11', 'complemento_33': '1'},
        *[{'atributo': f'{m} ({var})', 'antigua': f"{ga[ga.variante == var][c].iloc[0]:.3f}", 'complemento_33': f"{glob[glob.variante == var][c2].iloc[0]:.3f}"}
          for var in N.VARIANTES for m, c, c2 in (('Nogueira', 'nogueira', 'nogueira'), ('Jaccard promedio', 'jaccard_promedio', 'jaccard_promedio_entre_remuestreos'),
                                                  ('Tamaño medio', 'tamano_medio', 'tamano_medio'))],
        *[{'atributo': f'Jaccard pareado medio entre corridas ({var})', 'antigua': '', 'complemento_33': f"{par[par.variante == var].jaccard_entre_corridas.mean():.3f}"} for var in N.VARIANTES],
    ])
    guardar(resumen, DIRS['comparacion'] / 'comparacion_corridas_resumen.csv')

    figuras(frec, dist, ca, glob, sel_def)
    print('resumen listo')
    print(glob.to_string())


def figuras(frec, dist, ca, glob, sel_def):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from eda import variables as EV
    AZUL, NARANJA, GRIS, TINTA, SUAVE, GRILLA = '#2b6cb0', '#dd6b20', '#a0aec0', '#2d3748', '#718096', '#e2e8f0'
    plt.rcParams.update({'font.size': 9, 'axes.edgecolor': GRILLA, 'axes.labelcolor': TINTA, 'xtick.color': SUAVE, 'ytick.color': TINTA,
                         'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRILLA, 'grid.linewidth': 0.6,
                         'axes.axisbelow': True})
    et = lambda v: EV.etiqueta(v) if v != N.SOBRECARGA else 'Sobrecarga física o emocional'  # noqa: E731
    F = DIRS['figuras']; F.mkdir(exist_ok=True)

    t = frec[frec.variante == 'adaptado'].sort_values(['pct_seleccionada', 'variable'], ascending=[False, True])
    fig, ax = plt.subplots(figsize=(8.5, 0.27 * len(t) + 1.8))
    y = np.arange(len(t))
    col = [AZUL if s == 'seleccionada' else NARANJA if s == 'redundante' else GRIS for s in t.estado_definitivo]
    ax.barh(y, t.pct_seleccionada, color=col, height=0.62)
    ax.scatter(t.pct_relevante_su, y, marker='|', s=90, color=TINTA, zorder=3, label='% relevante (q < 0,10)')
    for yy, p in zip(y, t.pct_seleccionada):
        ax.text(p + 1, yy, f'{p:.1f}'.replace('.', ','), va='center', fontsize=7, color=SUAVE)
    ax.set_yticks(y, [et(v) for v in t.variable]); ax.invert_yaxis(); ax.set_xlim(0, 100); ax.grid(axis='y', visible=False)
    ax.set_xlabel('% de los 500 remuestreos en que queda seleccionada')
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    ax.legend(handles=[Patch(color=AZUL, label='Seleccionada en la definitiva'), Patch(color=NARANJA, label='Relevante, redundante en la definitiva'),
                       Patch(color=GRIS, label='No relevante en la definitiva'), Line2D([], [], color=TINTA, marker='|', ls='', ms=9, label='% relevante (q < 0,10)')],
              frameon=False, loc='lower right', fontsize=8)
    ax.set_title('Estabilidad de la selección, 33 variables finales\n(FCBF adaptado, 500 remuestreos bootstrap)', loc='left', fontsize=10.5, color=TINTA)
    fig.tight_layout(); fig.savefig(F / 'f01_estabilidad_33_variables_finales.png', dpi=180); plt.close(fig)

    a = frec[frec.variante == 'adaptado'].set_index('variable'); e = frec[frec.variante == 'estandar'].set_index('variable')
    orden = a.sort_values('pct_seleccionada', ascending=False).index
    fig, ax = plt.subplots(figsize=(8.5, 0.27 * len(orden) + 1.8)); y = np.arange(len(orden))
    ax.hlines(y, e.loc[orden, 'pct_seleccionada'], a.loc[orden, 'pct_seleccionada'], color=GRILLA, lw=2)
    ax.scatter(a.loc[orden, 'pct_seleccionada'], y, color=AZUL, s=22, zorder=3, label='Adaptado (exige q del par)')
    ax.scatter(e.loc[orden, 'pct_seleccionada'], y, color=NARANJA, s=22, zorder=3, label='Estándar')
    ax.set_yticks(y, [et(v) for v in orden]); ax.invert_yaxis(); ax.set_xlim(0, 100); ax.grid(axis='y', visible=False)
    ax.set_xlabel('% de remuestreos en que queda seleccionada'); ax.legend(frameon=False, loc='lower right', fontsize=8)
    ax.set_title('Variante adaptada y estándar, 33 variables finales', loc='left', fontsize=10.5, color=TINTA)
    fig.tight_layout(); fig.savefig(F / 'f02_adaptado_y_estandar_33_variables_finales.png', dpi=180); plt.close(fig)

    fig, axs = plt.subplots(1, 2, figsize=(8.5, 3.2), sharey=True)
    for ax, var, c in zip(axs, N.VARIANTES, (AZUL, NARANJA)):
        d = dist[dist.variante == var]
        ax.bar(d.tamano, d.remuestreos, color=c, width=0.7)
        ax.axvline(len(sel_def[var]), color=TINTA, ls=':', lw=1)
        ax.text(len(sel_def[var]) + 0.15, ax.get_ylim()[1] * 0.92, f'definitiva: {len(sel_def[var])}', fontsize=8, color=TINTA)
        ax.set_title('Adaptado' if var == 'adaptado' else 'Estándar', loc='left', fontsize=9.5, color=TINTA)
        ax.set_xlabel('Variables seleccionadas en el remuestreo'); ax.grid(axis='x', visible=False)
    axs[0].set_ylabel('Remuestreos')
    fig.suptitle('Tamaño de la selección en los 500 remuestreos, 33 variables finales', x=0.01, ha='left', fontsize=10.5, color=TINTA)
    fig.tight_layout(); fig.savefig(F / 'f03_tamano_seleccion_33_variables_finales.png', dpi=180); plt.close(fig)

    c = ca[ca.comparable_solo_descriptivamente].sort_values('pct_33_adaptado', ascending=False)
    fig, ax = plt.subplots(figsize=(8.5, 0.27 * len(c) + 2.0)); y = np.arange(len(c))
    ax.hlines(y, c.pct_antigua_adaptado, c.pct_33_adaptado, color=GRILLA, lw=2)
    ax.scatter(c.pct_antigua_adaptado, y, color=GRIS, s=22, zorder=3, label='Corrida antigua (30 candidatas, q < 0,05)')
    ax.scatter(c.pct_33_adaptado, y, color=AZUL, s=22, zorder=3, label='Complemento (33 variables finales, q < 0,10)')
    ax.set_yticks(y, [et(v) for v in c.variable]); ax.invert_yaxis(); ax.set_xlim(0, 100); ax.grid(axis='y', visible=False)
    ax.set_xlabel('% de remuestreos en que queda seleccionada (FCBF adaptado)'); ax.legend(frameon=False, loc='lower right', fontsize=8)
    ax.set_title('Variables comunes a ambas corridas: cambiaron a la vez el universo,\nel umbral y una etapa; la comparación es solo descriptiva',
                 loc='left', fontsize=10, color=TINTA)
    fig.tight_layout(); fig.savefig(F / 'f04_comparacion_corrida_antigua_descriptiva.png', dpi=180); plt.close(fig)


if __name__ == '__main__':
    main()
