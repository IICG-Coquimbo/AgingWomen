"""
Fase 39: pruebas (sección 17 del protocolo de la usuaria) y controles negativos. Cada prueba recalcula desde el código o desde los datos de origen, no solo desde
las tablas. Cada control negativo introduce un error en memoria (en los datos cargados o en una función) y exige que alguna prueba falle.

Uso, desde la carpeta scripts: python pruebas_39.py [--mutaciones]
"""
import copy
import math
import shutil
import subprocess
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import busqueda_39 as B
import heterogeneidad_39 as H
import integridad_39 as I
import nucleo_39 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
warnings.filterwarnings('ignore', category=FutureWarning)
N.instalar_gancho()
BASE = N.BASE
G, N38 = N.G, N.N38


def contexto():
    d = N.cargar()
    T529, _ = N.base_items(d)
    ctx = {'d': d, 'T529': T529, 'y': d.M['severo_mrs'].to_numpy().astype(int), 'corte': 16,
           'pert': pd.read_csv(BASE / 'preparacion' / 'pertenencia_estratos.csv', dtype={'participante_id': str}),
           'dic': pd.read_csv(BASE / 'preparacion' / 'diccionario_estratos.csv'), 'verif': N.leer_json(BASE / 'preparacion' / 'verificacion_codificacion.json'),
           'TODAS': pd.read_csv(BASE / 'reglas' / 'reglas_todos_estratos.csv'), 'AB': pd.read_csv(BASE / 'ab1' / 'reglas_grupos_A_B1.csv'),
           'Hs': {g: pd.read_csv(BASE / 'comparacion' / f'comparacion_{g}.csv') for g in N.DIMENSIONES},
           'nulas_h': {g: pd.read_csv(BASE / 'comparacion' / f'nula_comparacion_{g}.csv') for g in N.DIMENSIONES},
           'conc': N.leer_json(BASE / 'resultados' / 'conclusion_39.json'),
           'limpio': pd.read_csv(N.N37.LIMPIO, dtype=str, keep_default_na=False)}
    ctx['masc'] = N.mascaras(d)
    return ctx


def p01(c):
    p = c['pert']
    ids36 = pd.read_csv(N.ANALISIS / 'fase36' / 'matrices' / 'identificadores.csv', dtype=str)['participante_id'].tolist()
    ok = len(p) == 529 and p['participante_id'].nunique() == 529 and p['participante_id'].tolist() == ids36
    for dim in N.DIMENSIONES:
        u = []
        for e in N.dims_de(dim):
            u += pd.read_csv(BASE / 'preparacion' / 'matrices' / f'matriz_{dim}_{e}.csv', dtype={'participante_id': str}, usecols=['participante_id'])['participante_id'].tolist()
        ok &= sorted(u) == sorted(ids36) and len(u) == len(set(u))
    return ok, f"{p['participante_id'].nunique()} identificadores únicos; cada dimensión los reparte sin repetir"


def p02(c):
    L = c['limpio'].set_index('participante_id').reindex(c['pert']['participante_id'])
    tot = L[[f'pregunta_{i}' for i in range(1, 12)]].apply(pd.to_numeric).sum(axis=1)
    sev = (tot >= c['corte']).astype(int).to_numpy()
    ok = (sev == c['pert']['severo_mrs'].to_numpy()).all() and sev.sum() == 281 and (len(sev) - sev.sum()) == 248 and (sev == c['y']).all()
    return ok, f'{sev.sum()} severas y {len(sev) - sev.sum()} no severas, recalculadas desde los 11 ítems de la limpieza'


def p03(c):
    D, p = c['dic'], c['pert']
    ok = True
    for r in D.itertuples():
        col = r.grupo
        m = (p[col].astype(str) == (r.estrato.split('_')[-1] if col in ('A', 'B1') else r.estrato))
        a, b, largo, comp = N.umbrales(int(m.sum()))
        ok &= int(m.sum()) == r.participantes and int(p.loc[m, 'severo_mrs'].sum()) == r.severas and abs(p.loc[m, 'severo_mrs'].mean() - r.frecuencia_basal_si) < 1e-12
        ok &= (r.umbral_antecedente, r.umbral_conjunto, r.largo_maximo, r.comparabilidad_minima) == (a, b, largo, comp)
    esperado = {('trabajo', 'trabaja'): 309, ('pareja', 'sin_pareja'): 173, ('ejercicio', '3_o_mas_dias'): 79, ('cuidado', 'cuida'): 251}
    ok &= all(int(D[(D.grupo == g) & (D.estrato == e)]['participantes'].iloc[0]) == v for (g, e), v in esperado.items())
    return bool(ok), f'{len(D)} estratos y grupos: tamaños, severas, basales y umbrales coinciden con el recuento y la fórmula del protocolo'


def p04(c):
    L = c['limpio'].set_index('participante_id').reindex(c['pert']['participante_id'])
    esp = {'trabajo': np.where(L['trabaja_actualmente'].isin(['True', 'SI', '1']), 'trabaja', 'no_trabaja'),
           'pareja': np.where(L['tiene_pareja'] == 'SI', 'con_pareja', 'sin_pareja'),
           'ejercicio': np.select([L['dias_ejercicio_semana'] == '1', L['dias_ejercicio_semana'] == '2'], ['0_dias', '1-2_dias'], '3_o_mas_dias'),
           'cuidado': np.where(L['cantidad_personas_cuida'].isin(['', '0']), 'no_cuida', 'cuida')}
    malos = {k: int((v != c['pert'][k].to_numpy()).sum()) for k, v in esp.items()}
    return all(v == 0 for v in malos.values()), f'pertenencia recalculada desde las respuestas crudas de la limpieza; discrepancias: {malos}'


def p05(c):
    v = c['verif']
    M38 = pd.read_csv(N.D38 / 'preparacion' / 'matriz_transaccional_principal.csv', dtype={'participante_id': str})
    cols = [x for x in M38.columns if x not in ('participante_id',) + N.CONSECUENTES]
    ok = all(v[k] for k in ('ids_iguales_y_en_orden', 'mismos_items', 'misma_matriz', 'consecuente_igual')) and cols == list(c['T529'].columns) \
        and (M38[cols].to_numpy().astype(bool) == c['T529'].to_numpy()).all()
    return bool(ok), f'{len(cols)} ítems idénticos a la matriz principal de la Fase 38'


def _items(t):
    return [i for a in t['antecedente'] for i in a.split(' & ')]


def p06(c):
    validas = set(N38.PRINCIPAL)
    malos = []
    for it in set(_items(c['TODAS'])) | set(_items(c['AB'])):
        try:
            v = N38.variable_de_item(it)
        except KeyError:
            malos.append(it)
            continue
        if v not in validas or any(x in it.lower() for x in ('mrs', 'pregunta', 'severo', 'segment')):
            malos.append(it)
    return not malos, f'ningún ítem del MRS, de los segmentos ni de A/B1 en los antecedentes; problemas: {malos[:3]}'


def p07(c):
    malos = 0
    for t in (c['TODAS'], c['AB']):
        for a, cons in zip(t['antecedente'], t['consecuente']):
            vs = [N38.variable_de_item(i) for i in a.split(' & ')] if all('=' in i and i.split('=')[0] in N38.VAR_DE_CORTO for i in a.split(' & ')) else ['?', '?']
            malos += len(vs) != len(set(vs)) or cons not in N.CONSECUENTES
    return malos == 0, f'{len(c["TODAS"]) + len(c["AB"])} reglas sin dos estados de una misma variable y con un solo consecuente'


def p08(c):
    malos = []
    for dim, e in N.ESTRATOS:
        M = pd.read_csv(BASE / 'preparacion' / 'matrices' / f'matriz_{dim}_{e}.csv', dtype={'participante_id': str})
        cols = [x for x in M.columns if x not in ('participante_id',) + N.CONSECUENTES]
        pre = M[cols].mean()
        cst = N.construir(c['d'], dim, e, T529=c['T529'], masc=c['masc'])
        if ((cst.T.sum() == 0) | (cst.T.sum() == cst.n)).any():
            malos.append(f'{e}: ítem constante en la construcción')
        R = c['TODAS'][(c['TODAS']['dimension'] == dim) & (c['TODAS']['estrato'] == e)]
        for it in set(_items(R)):
            if N38.variable_de_item(it) in N.excluidas(dim) or it not in pre.index or not (0 < pre[it] < 1):
                malos.append(f'{e}: {it}')
    return not malos, f'sin la variable del estrato ni ítems constantes dentro del estrato; problemas: {malos[:3]}'


def p09(c):
    T = c['TODAS'].sample(300, random_state=1)
    err = 0.0
    cache = {}
    for r in T.itertuples():
        if (r.dimension, r.estrato) not in cache:
            cache[(r.dimension, r.estrato)] = pd.read_csv(BASE / 'preparacion' / 'matrices' / f'matriz_{r.dimension}_{r.estrato}.csv')
        M = cache[(r.dimension, r.estrato)]
        a = np.ones(len(M), bool)
        for i in r.antecedente.split(' & '):
            a &= M[i].to_numpy() == 1
        y = M[r.consecuente].to_numpy() == 1
        nA, nAC = a.sum(), (a & y).sum()
        base = y.mean()
        c0 = (~a & y).sum() / (~a).sum()
        err = max(err, abs(nA - r.n_antecedente), abs(nAC - r.n_conjunto), abs(nAC / nA - r.confianza), abs(nAC / len(M) - r.soporte), abs(nAC / nA / base - r.lift),
                  abs(nAC / nA - c0 - r.diferencia_riesgo), abs(base - r.frecuencia_basal))
    return err < 1e-9, f'300 reglas recalculadas desde las matrices de los estratos; error máximo {err:.2e}'


def p10(c):
    dim, e = 'ejercicio', '3_o_mas_dias'
    cst = N.construir(c['d'], dim, e, T529=c['T529'], masc=c['masc'])
    frec = N.EV38.descubrir(cst)
    ants = list(G.antecedentes(frec, cst.min_ant, N38.pares_determinados(cst.T)))
    V = cst.T.to_numpy()
    col = {x: i for i, x in enumerate(cst.T.columns)}
    A = np.array([np.all(V[:, [col[i] for i in s]], axis=1) for s in ants])
    rng = np.random.default_rng([N.SEMILLA, 39, N.NUM_ESTRATO[(dim, e)]])
    perms = [rng.permutation(cst.n) for _ in range(N.N_PERM)]
    p0 = cst.n_si / cst.n
    mz = []
    for p in perms[:100]:
        yy = cst.y[p]
        if yy.sum() != cst.n_si:
            return False, 'una permutación cambió el número de severas del estrato'
        nA = A.sum(axis=1)
        k = A.astype(int) @ yy
        cc = k / nA
        kk = np.where(cc >= p0, k, nA - k)
        z = np.abs(cc - p0) / np.sqrt(p0 * (1 - p0) / nA)
        mz.append(np.where(kk >= cst.min_conj, z, 0).max())
    guard = pd.read_csv(BASE / 'referencia_nula' / f'nula_{dim}_{e}.csv')['max_z'].to_numpy()[:100]
    return bool(np.allclose(mz, guard, atol=1e-6)), f'primeras 100 permutaciones del estrato «3 días o más» recalculadas: máximo |z| igual; severas constantes ({cst.n_si})'


def _comp_independiente(c, dim, ants):
    est = N.dims_de(dim)
    T, y, masc = c['T529'], c['y'], c['masc']
    out = []
    for a in ants:
        m = np.ones(529, bool)
        for i in a.split(' & '):
            m &= T[i].to_numpy()
        dr, w = [], []
        for e in est:
            s = masc[(dim, e)]
            nA, k = (m & s).sum(), (m & s & (y == 1)).sum()
            nn, k0 = (~m & s).sum(), (~m & s & (y == 1)).sum()
            p1, p0 = (k + 0.5) / (nA + 1), (k0 + 0.5) / (nn + 1)
            dr.append(k / nA - k0 / nn)
            w.append(1 / (p1 * (1 - p1) / nA + p0 * (1 - p0) / nn))
        dr, w = np.array(dr), np.array(w)
        q = (w * (dr - (w * dr).sum() / w.sum()) ** 2).sum()
        out.append((dr, q, (dr[0] - dr[-1]) / math.sqrt(1 / w[0] + 1 / w[-1]) if len(est) == 2 else np.nan))
    return out


def p11(c):
    err, cubre = 0.0, True
    for dim, Hd in c['Hs'].items():
        s = Hd.sample(min(150, len(Hd)), random_state=2)
        est = N.dims_de(dim)
        for (dr, q, z), (_, r) in zip(_comp_independiente(c, dim, s['antecedente']), s.iterrows()):
            err = max(err, abs(q - r['Q']), *(abs(dr[i] - r[f'DR_{e}']) for i, e in enumerate(est)), abs((dr.max() - dr.min()) - r['rango_DR']))
            if len(est) == 2:
                err = max(err, abs(z - r['z_interaccion']), abs(dr[0] - dr[1] - r['delta']), abs(r['z_interaccion'] ** 2 - r['Q']))
                cubre &= r['delta_inf'] <= r['delta'] <= r['delta_sup']
    return err < 1e-9 and bool(cubre), f'diferencias de riesgo, Q, Δ y z recalculados de forma independiente en hasta 150 antecedentes por dimensión; error máximo {err:.2e}; Q = z² con dos estratos'


def p12(c):
    dim = 'trabajo'
    est = N.dims_de(dim)
    ms = [c['masc'][(dim, e)] for e in est]
    perms = H.permutaciones(529, ms, [N.SEMILLA, 39, 100 + N.NUM_DIM[dim]])
    y = c['y']
    for p in perms:
        for m in ms:
            if not m[p][m].all() or y[p][m].sum() != y[m].sum():
                return False, 'una permutación mezcla participantes entre estratos o cambia su número de severas'
    Hd = c['Hs'][dim]
    A = G.matriz_antecedentes(c['T529'], [frozenset(a.split(' & ')) for a in Hd['antecedente']])
    Y = np.stack([y[p] for p in perms[:100]], axis=1)
    _, _, Q = H.estadisticos(H.recuentos(A, Y, ms))
    guard = c['nulas_h'][dim]['max_Q'].to_numpy()[:100]
    return bool(np.allclose(Q.max(axis=0), guard, atol=1e-6)), '1.000 permutaciones solo dentro de los estratos, con las severas de cada estrato constantes; máximo Q de las primeras 100 recalculado'


def p13(c):
    rng = np.random.default_rng(7)
    def sim(dr1, dr2, reps=4000):
        rec_y = []
        n1, n2 = 300, 220
        A = np.zeros((1, n1 + n2), np.uint8)
        a = rng.random(n1 + n2) < 0.3
        A[0] = a
        s1 = np.r_[np.ones(n1, bool), np.zeros(n2, bool)]
        p = np.where(s1, np.where(a, 0.5 + dr1, 0.5), np.where(a, 0.5 + dr2, 0.5))
        Y = (rng.random((reps, n1 + n2)) < p).T.astype(np.uint8)
        DR, V, Q = H.estadisticos(H.recuentos(A, Y, [s1, ~s1]))
        return (Q[0] > 3.841458820694124).mean()
    tam, pot = sim(0.15, 0.15), sim(0.25, -0.10)
    return 0.03 <= tam <= 0.075 and pot >= 0.8, f'simulación con asociación común no nula sin interacción: rechazo {tam:.3f} (esperado ≈ 0,05); con interacción: potencia {pot:.3f}'


def p14(c):
    ok, det = True, []
    for dim, Hd in c['Hs'].items():
        mq = c['nulas_h'][dim]['max_Q'].to_numpy()
        pa = np.array([(1 + (mq >= q).sum()) / (1 + len(mq)) for q in Hd['Q']])
        ok &= np.allclose(pa, Hd['p_ajustado_dimension']) and np.allclose(N38.bh(Hd['p_chi2'].to_numpy()), Hd['q_bh_dimension'])
        ok &= (Hd['p_ajustado_conjunto'] >= Hd['p_ajustado_dimension'] - 1e-12).all() and (Hd['p_ajustado_dimension'] >= 1 / 1001).all()
        o = Hd.sort_values('Q')
        ok &= (np.diff(o['p_ajustado_dimension'].to_numpy()) <= 1e-12).all()
    T = c['TODAS']
    ok &= (T['p_ajustado_conjunto'] >= T['p_ajustado_estrato'] - 1e-12).all()
    for (dim, e), R in T.groupby(['dimension', 'estrato']):
        ok &= np.allclose(N38.bh(R['p_fisher'].to_numpy()), R['q_bh_estrato'])
    return bool(ok), 'p ajustados por máximo Q recalculados para todas las comparaciones; BH sobre todas las filas evaluadas; ajuste conjunto ≥ ajuste por dimensión o estrato'


def p15(c):
    T1, _ = N.base_items(c['d'], 'S1')
    est, her = c['d'].estado, c['d'].heredada
    malos = 0
    for it in T1.columns:
        v = N38.variable_de_item(it)
        if v in est.columns:
            m = est[v].isin(['imputada', 'deducida']).to_numpy() | (her[v].astype(str) == '1').to_numpy()
            malos += int(T1[it].to_numpy()[m].sum())
    sin = not any(N38.variable_de_item(i) in N38.SIN_MARCA for i in T1.columns)
    return malos == 0 and sin, f'en S1 ninguna celda imputada o deducida genera ítem ({malos} casos) y diabetes y previsión quedan fuera'


def p16(c):
    tmp = BASE / 'pruebas' / 'tmp_reproducibilidad'
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        dim, e = 'ejercicio', '3_o_mas_dias'
        cst = N.construir(c['d'], dim, e, T529=c['T529'], masc=c['masc'])
        R, _, _, _, _ = B.buscar(cst, tmp, [N.SEMILLA, 39, N.NUM_ESTRATO[(dim, e)]])
        g = pd.read_csv(BASE / 'reglas' / dim / f'reglas_{e}.csv')
        cols = ['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']
        R = R.reset_index(drop=True)
        ok = len(R) == len(g) and (R[cols].astype(str) == g[cols].astype(str)).all().all() \
            and np.allclose(R[['confianza', 'z', 'p_ajustado_estrato']].to_numpy(float), g[['confianza', 'z', 'p_ajustado_estrato']].to_numpy(float), rtol=1e-12, atol=1e-15)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return bool(ok), f'búsqueda y nula del estrato «3 días o más» repetidas desde cero: {len(R)} reglas idénticas'


def p17(c):
    ofi, alt = N.N37.etiquetas()
    ids = c['pert']['participante_id']
    ok = (ofi.reindex(ids).to_numpy() == c['pert']['A'].to_numpy()).all() and (alt['B1_doble_uso'].reindex(ids).to_numpy() == c['pert']['B1'].to_numpy()).all()
    h = pd.read_csv(BASE / 'integridad' / 'huellas_entradas_inicial.csv').set_index('archivo')['sha256']
    for p in (N.N37.C37 / 'seleccion' / 'artefactos_provisionales' / 'P2_c12_km_k4' / 'etiquetas.csv', N.N37.CMP / 'asignaciones' / 'etiquetas_alternativas.csv'):
        ok &= N.sha(p) == h[p.relative_to(N.RAIZ).as_posix()]
    tam = c['pert']['A'].value_counts().sort_index().tolist() == list(N.N37.TAMANOS_A) and c['pert']['B1'].value_counts().sort_index().tolist() == list(N.N37.TAMANOS_B1)
    return bool(ok and tam), 'etiquetas A y B1 iguales a los archivos históricos, con las mismas huellas y tamaños (150/76/132/171 y 150/79/126/174)'


def p18(c):
    m = I.manifiestos()
    return int(m['distintos'].sum()) == 0, f"{int(m['comparados_por_huella'].sum())} archivos de las Fases 34 a 38 comparados por huella; distintos: {int(m['distintos'].sum())}"


def p19(c):
    g = I.estado_git()
    h = pd.read_csv(BASE / 'integridad' / 'huellas_entradas_inicial.csv').set_index('archivo')['sha256']
    ok = not g['cambios_en_src'] and N.sha(N.RAIZ / 'src' / 'apps' / 'encuestas' / 'models.py') == h['src/apps/encuestas/models.py'] and g['head'] == I.HEAD_ESPERADO
    return bool(ok), f"sin cambios en src/ ({len(g['cambios_en_src'])}); HEAD {g['head']}"


def p20(c):
    s = N.huella_sello()
    t = datetime.fromisoformat(s['sellado']).timestamp()
    res = [BASE / 'reglas' / 'resumen_estratos.csv', BASE / 'comparacion' / 'resumen_comparacion.csv'] + list((BASE / 'referencia_nula').glob('nula_*.csv'))
    txt = (BASE / 'protocolo' / s['archivo']).read_text(encoding='utf-8')
    ok = all(p.stat().st_mtime > t for p in res) and all(f in txt for f in ('exploratorio', 'Westfall-Young', 'no solo a las seleccionadas', 'Resultado C'))
    return bool(ok), f"protocolo íntegro (sha {s['sha256'][:12]}…), sellado antes de todos los resultados"


def p21(c):
    T = c['TODAS']
    esp = np.where(~T['marcada'], '1', np.where(T['redundante'].fillna(False).astype(bool), '2', np.where(~T['supera_nula_estrato'], '3', np.where(~T['estable'].fillna(False).astype(bool), '4', '5'))))
    ok = (T['clase'].str[0] == esp).all()
    for Hd in c['Hs'].values():
        e = np.where(~Hd['marcada'], 'H1', np.where(Hd['redundante'], 'H2', np.where(~Hd['supera_nula_dimension'], 'H3', np.where(~Hd['estable'].astype(bool), 'H4', 'H5'))))
        ok &= (Hd['clase'].str[:2] == e).all()
        ok &= (Hd['marcada'] == (Hd['rango_DR'] >= N.DIF_HET)).all()
    return bool(ok), 'clases de reglas y comparaciones recalculadas con las reglas excluyentes del protocolo'


def p22(c):
    h5 = sum(int(Hd['clase'].str.startswith('H5').sum()) for Hd in c['Hs'].values())
    c5 = int((c['TODAS']['clase'].str.startswith('5') & c['TODAS']['supera_nula_conjunta']).sum())
    cons = sum(x['consistente'] for x in c['conc']['detalle_H5'])
    esperado = 'A' if cons else ('B' if c5 else 'C')
    ok = c['conc']['resultado'] == esperado and c['conc']['diferencias_H5'] == h5 and cons <= h5
    return bool(ok), f'conclusión mecánica recalculada: {h5} comparaciones H5, {cons} consistentes, {c5} reglas de clase 5 con nula conjunta → resultado {esperado}'


PRUEBAS = [('Exactamente 529 identificadores originales', p01), ('MRS severo correcto', p02), ('Tamaños de estratos, frecuencias basales y umbrales', p03),
           ('Pertenencia correcta a los estratos', p04), ('Codificación idéntica a la Fase 38', p05), ('Sin ítems del MRS ni etiquetas entre los antecedentes', p06),
           ('Sin reglas contradictorias', p07), ('Sin la variable del estrato ni condiciones constantes', p08), ('Soporte, confianza, lift y diferencias de riesgo', p09),
           ('Referencia nula dentro del estrato', p10), ('Comparación entre estratos', p11), ('Referencia nula de la comparación', p12),
           ('Calibración del estadístico de interacción', p13), ('Control de la búsqueda múltiple', p14), ('Tratamiento de imputaciones', p15),
           ('Reproducibilidad', p16), ('Etiquetas A y B1 intactas', p17), ('Fases anteriores sin cambios', p18), ('Django sin modificaciones', p19),
           ('Sello del protocolo previo a los resultados', p20), ('Clasificación', p21), ('Conclusión mecánica', p22)]
LENTAS = {'p16', 'p18'}


def correr(ctx, solo=None):
    out = []
    for nombre, f in PRUEBAS:
        if solo is not None and f.__name__ not in solo:
            continue
        try:
            ok, det = f(ctx)
        except Exception as ex:  # noqa: BLE001
            ok, det = False, f'error: {type(ex).__name__}: {str(ex)[:150]}'
        out.append({'n': f.__name__, 'prueba': nombre, 'resultado': 'superada' if ok else 'FALLA', 'detalle': det})
    return out


# ---- controles negativos
def _parche(mod, nombre, nuevo):
    viejo = getattr(mod, nombre)
    setattr(mod, nombre, nuevo)
    return lambda: setattr(mod, nombre, viejo)


def m_fila(c, t, **k):
    fila = c[t].iloc[[0]].copy()
    for a, b in k.items():
        fila[a] = b
    c[t] = pd.concat([c[t], fila], ignore_index=True)


def mut_permutar_todo():
    viejo = H.permutaciones
    def mala(n, ms, semilla, n_perm=N.N_PERM):
        rng = np.random.default_rng(semilla)
        return [rng.permutation(n) for _ in range(n_perm)]
    H.permutaciones = mala
    return lambda: setattr(H, 'permutaciones', viejo)


def mut_varianza():
    viejo = H.estadisticos
    def mala(rec):
        DR, V, Q = viejo(rec)
        return DR, V / 2, Q * 2
    H.estadisticos = mala
    return lambda: setattr(H, 'estadisticos', viejo)


def mut_s1():
    viejo = N.base_items
    N.base_items = lambda d, sens='principal': viejo(d, 'principal' if sens == 'S1' else sens)
    return lambda: setattr(N, 'base_items', viejo)


def mut_constante():
    viejo = N.construir
    def malo(*a, **k):
        e = viejo(*a, **k)
        e.T['constante'] = True
        return e
    N.construir = malo
    return lambda: setattr(N, 'construir', viejo)


def mut_sha():
    viejo = N.sha
    N.sha = lambda p: 'x' * 64 if str(p).endswith('etiquetas.csv') else viejo(p)
    return lambda: setattr(N, 'sha', viejo)


def mut_semilla():
    viejo = N.SEMILLA
    N.SEMILLA = 43
    return lambda: setattr(N, 'SEMILLA', viejo)


def _set(c, t, col, f):
    c[t][col] = f(c[t][col])


MUTACIONES = [
    ('Corte del MRS en 15 en vez de 16', lambda c: c.update(corte=15), None),
    ('Identificador duplicado', lambda c: c['pert'].__setitem__('participante_id', c['pert']['participante_id'].where(c['pert'].index != 1, c['pert']['participante_id'][0])), None),
    ('Participante asignada al estrato equivocado', lambda c: c['pert'].__setitem__('trabajo', c['pert']['trabajo'].where(c['pert'].index != 0, 'no_trabaja' if c['pert']['trabajo'][0] == 'trabaja' else 'trabaja')), None),
    ('Umbral menor que el del protocolo', lambda c: c['dic'].__setitem__('umbral_antecedente', c['dic']['umbral_antecedente'].where(c['dic'].index != 0, 10)), None),
    ('Variable del estrato como antecedente', lambda c: m_fila(c, 'TODAS', dimension='trabajo', estrato='trabaja', antecedente='trabaja=SI & edad=45-54'), None),
    ('Ítem del MRS como antecedente', lambda c: m_fila(c, 'TODAS', antecedente='mrs_total=alto'), None),
    ('Regla contradictoria', lambda c: m_fila(c, 'TODAS', antecedente='edad=36-44 & edad=45-54'), None),
    ('Ítem constante no quitado', lambda c: None, mut_constante),
    ('Confianza mal calculada', lambda c: c['TODAS'].__setitem__('confianza', c['TODAS']['confianza'] + 0.02), None),
    ('Nula que permuta entre estratos', lambda c: None, mut_permutar_todo),
    ('Q sin ponderar', lambda c: c['Hs']['trabajo'].__setitem__('Q', c['Hs']['trabajo'][[f'DR_{e}' for e in N.dims_de('trabajo')]].var(axis=1)), None),
    ('Signo de Δ invertido', lambda c: c['Hs']['pareja'].__setitem__('delta', -c['Hs']['pareja']['delta']), None),
    ('Varianza de la interacción subestimada', lambda c: None, mut_varianza),
    ('Ajuste aplicado solo a la regla seleccionada', lambda c: c['Hs']['cuidado'].__setitem__('p_ajustado_dimension', c['Hs']['cuidado']['p_chi2']), None),
    ('Imputados conservados en S1', lambda c: None, mut_s1),
    ('Semilla distinta (no reproducible)', lambda c: None, mut_semilla),
    ('Etiqueta A alterada', lambda c: c['pert'].__setitem__('A', c['pert']['A'].where(c['pert'].index != 0, (c['pert']['A'][0] + 1) % 4)), None),
    ('Archivo histórico modificado', lambda c: None, mut_sha),
    ('Clase de comparación mal asignada', lambda c: c['Hs']['trabajo'].__setitem__('clase', 'H5 diferencia que supera los controles de la dimensión'), None),
    ('Conclusión forzada a A', lambda c: c['conc'].update(resultado='A'), None),
]


def main():
    t0 = time.time()
    ctx = contexto()
    res = correr(ctx)
    D = pd.DataFrame(res)
    N.a_csv(D, BASE / 'pruebas' / 'resultados_pruebas.csv')
    print(D[['n', 'resultado', 'detalle']].to_string(index=False), flush=True)
    if '--mutaciones' in sys.argv:
        filas = []
        base_ok = set(D.loc[D['resultado'] == 'superada', 'n'])
        for nombre, f, parche in MUTACIONES:
            c = {k: (copy.deepcopy(v) if k not in ('d', 'T529', 'masc', 'limpio') else v) for k, v in ctx.items()}
            deshacer = parche() if parche else None
            try:
                f(c)
                solo = None if nombre in ('Semilla distinta (no reproducible)', 'Archivo histórico modificado') else {p.__name__ for _, p in PRUEBAS} - LENTAS
                r = correr(c, solo)
            finally:
                if deshacer:
                    deshacer()
            fallan = [x['n'] for x in r if x['resultado'] != 'superada' and x['n'] in base_ok]
            filas.append({'control_negativo': nombre, 'detectado': bool(fallan), 'pruebas_que_fallan': ', '.join(fallan),
                          'motivo': '; '.join(x['detalle'] for x in r if x['n'] in fallan)[:300]})
            print(nombre, '→', fallan, flush=True)
        Mt = pd.DataFrame(filas)
        N.a_csv(Mt, BASE / 'pruebas' / 'control_mutaciones.csv')
        print(f"{int(Mt['detectado'].sum())}/{len(Mt)} controles negativos detectados")
    N.registrar('pruebas')
    print(f"{(D['resultado'] == 'superada').sum()}/{len(D)} pruebas superadas, {time.time() - t0:.0f} s")


if __name__ == '__main__':
    main()
