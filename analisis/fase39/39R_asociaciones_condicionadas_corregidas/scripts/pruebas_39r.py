"""
Fase 39R: pruebas y controles negativos. Conserva las 22 pruebas de la Fase 39 (p05, p18 y p19 adaptadas a la 39R, porque las históricas dependen de la matriz de 94 ítems y de HEAD 745d689) y añade p23 a p27.
Cada prueba recalcula desde el código o desde los datos de origen. Cada control negativo introduce un error en memoria y exige que alguna prueba falle.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/pruebas_39r.py [--mutaciones]
"""
import copy
import math
import shutil
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import busqueda_39 as B  # noqa: E402
import heterogeneidad_39 as H  # noqa: E402
import integridad_39r as I  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

warnings.filterwarnings('ignore', category=FutureWarning)
N.instalar_gancho()
BASE = N.BASE
G, N38 = N.G, N.N38


def contexto():
    pq = N.cargar()
    d = pq.d
    T529, _ = N.base_items(pq)
    ctx = {'pq': pq, 'd': d, 'T529': T529, 'y': d.M['severo_mrs'].to_numpy().astype(int), 'corte': 16,
           'pert': pd.read_csv(BASE / 'preparacion' / 'pertenencia_estratos.csv', dtype={'participante_id': str}),
           'dic': pd.read_csv(BASE / 'preparacion' / 'diccionario_estratos.csv'), 'verif': N.leer_json(BASE / 'preparacion' / 'verificacion_preparacion.json'),
           'TODAS': pd.read_csv(BASE / 'reglas' / 'reglas_todos_estratos.csv'), 'AB': pd.read_csv(BASE / 'ab1' / 'reglas_grupos_A_B1.csv'),
           'Hs': {g: pd.read_csv(BASE / 'comparacion' / f'comparacion_{g}.csv') for g in N.DIMENSIONES},
           'nulas_h': {g: pd.read_csv(BASE / 'comparacion' / f'nula_comparacion_{g}.csv') for g in N.DIMENSIONES},
           'conc': N.leer_json(BASE / 'resultados' / 'conclusion_39R.json'), 'ini': I.leer(BASE / 'integridad' / 'huellas_inicial.csv'),
           'limpio': pd.read_csv(N.N37.LIMPIO, dtype=str, keep_default_na=False)}
    ctx['masc'] = N.mascaras(pq)
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
    esperado = {('trabajo', 'trabaja'): 309, ('trabajo', 'no_trabaja'): 220, ('pareja', 'con_pareja'): 356, ('pareja', 'sin_pareja'): 173, ('ejercicio', '0_dias'): 302, ('ejercicio', '1-2_dias'): 148, ('ejercicio', '3_o_mas_dias'): 79, ('cuidado', 'cuida'): 251, ('cuidado', 'no_cuida'): 278}
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
    """Adaptada: la matriz de referencia es la de 90 ítems de la 38R."""
    M = pd.read_csv(N.MATRIZ_38R, dtype={'participante_id': str})
    cols = [x for x in M.columns if x not in ('participante_id',) + N.CONSECUENTES]
    ok = c['verif']['matriz_identica_38R'] and c['verif']['items'] == 90 and c['verif']['variables'] == 29 and cols == list(c['T529'].columns) and (M[cols].to_numpy().astype(bool) == c['T529'].to_numpy()).all() and (M['severo_mrs=SI'].to_numpy() == c['y']).all() and M['participante_id'].tolist() == list(c['d'].ids)
    return bool(ok), f'{len(cols)} ítems idénticos a la matriz principal de la Fase 38R'


def _items(t):
    return [i for a in t['antecedente'] for i in a.split(' & ')]


def p06(c):
    validas = set(N.PRINCIPAL)
    malos = []
    for it in set(_items(c['TODAS'])) | set(_items(c['AB'])):
        try:
            v = N38.variable_de_item(it)
        except KeyError:
            malos.append(it)
            continue
        if v not in validas or any(x in it.lower() for x in ('mrs', 'pregunta', 'severo', 'segment')):
            malos.append(it)
    return not malos, f'ningún ítem del MRS, de los segmentos, de A/B1 ni de las variables excluidas en los antecedentes; problemas: {malos[:3]}'


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
        cst = N.construir(c['pq'], dim, e, T529=c['T529'], masc=c['masc'])
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
    cst = N.construir(c['pq'], dim, e, T529=c['T529'], masc=c['masc'])
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
    ok = True
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
    T1, _ = N.base_items(c['pq'], 'S1')
    est, her = c['d'].estado, c['d'].heredada
    malos = 0
    for it in T1.columns:
        v = N38.variable_de_item(it)
        if v in est.columns:
            m = est[v].isin(['imputada', 'deducida']).to_numpy() | (her[v].astype(str) == '1').to_numpy()
            malos += int(T1[it].to_numpy()[m].sum())
    return malos == 0, f'en S1 ninguna celda imputada o deducida genera ítem ({malos} casos)'


def p16(c):
    tmp = BASE / 'pruebas' / 'tmp_reproducibilidad'
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        dim, e = 'ejercicio', '3_o_mas_dias'
        cst = N.construir(c['pq'], dim, e, T529=c['T529'], masc=c['masc'])
        R, _, _, _, _ = B.buscar(cst, tmp, [N.SEMILLA, 39, N.NUM_ESTRATO[(dim, e)]], n_perm=N.N_PERM)
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
    for p in (N.N37.C37 / 'seleccion' / 'artefactos_provisionales' / 'P2_c12_km_k4' / 'etiquetas.csv', N.N37.CMP / 'asignaciones' / 'etiquetas_alternativas.csv'):
        ok &= N.sha(p) == c['ini'][p.relative_to(N.RAIZ).as_posix()]
    tam = c['pert']['A'].value_counts().sort_index().tolist() == list(N.N37.TAMANOS_A) and c['pert']['B1'].value_counts().sort_index().tolist() == list(N.N37.TAMANOS_B1)
    return bool(ok and tam), 'etiquetas A y B1 iguales a los archivos históricos, con las mismas huellas y tamaños (150/76/132/171 y 150/79/126/174)'


def p18(c):
    """Adaptada: las únicas diferencias admitidas son las tres excepciones documentadas, anteriores a la 38R."""
    m = I.manifiestos()
    otras = sorted({e for x in m for e in x['ejemplos'].split('; ') if e} - I.EXCEPCIONES_DOCUMENTADAS)
    return not otras, f"{sum(x['archivos'] for x in m)} archivos de las Fases 34 a 39 por manifiesto; diferencias no documentadas: {otras[:3]}"


def p19(c):
    """Adaptada: src/ tiene cambios pendientes de la Fase 40; se exige que sigan iguales a la medición inicial."""
    malos = [r for r, h in c['ini'].items() if r.startswith('src/') and not h.startswith('sin abrir') and (not (N.RAIZ / r).is_file() or N.sha(N.RAIZ / r) != h)]
    return not malos, f"archivos de src/ iguales a la medición inicial; distintos: {len(malos)}"


def p20(c):
    s = N.huella_sello()
    t = datetime.fromisoformat(s['sellado']).timestamp()
    res = [BASE / 'reglas' / 'resumen_estratos.csv', BASE / 'comparacion' / 'resumen_comparacion.csv'] + list((BASE / 'referencia_nula').glob('nula_*.csv'))
    txt = (BASE / 'protocolo' / s['archivo']).read_text(encoding='utf-8')
    ok = all(p.stat().st_mtime > t for p in res) and all(f in txt for f in ('exploratorio', 'Westfall-Young', 'todas las filas', '**C:**')) and c['verif']['modo_humo'] is False and not N.HUMO
    return bool(ok), f"protocolo íntegro (sha {s['sha256'][:12]}…), sellado antes de todos los resultados; sin modo de humo"


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
    det = c['conc']['detalle_H5']
    cons = sum(x['consistente'] for x in det)
    esperado = 'A' if cons else ('B' if c5 else 'C')
    ok = c['conc']['resultado'] == esperado and c['conc']['diferencias_H5'] == h5 and cons <= h5
    for x in det:
        cond3 = x['dimension'] != 'ejercicio' or x['lectura_S9'] != 'no evaluable'
        ok &= x['consistente'] == bool(x['supera_nula_conjunta'] and x['mantiene_en_nucleo'] and cond3)
        ok &= not x['consistente'] or x['evaluables_nucleo'] >= 3
    return bool(ok), f'conclusión mecánica recalculada: {h5} comparaciones H5, {cons} consistentes, {c5} reglas de clase 5 con nula conjunta → resultado {esperado}'


def p23(c):
    """Exclusiones en todas las entradas y tablas de modelado, por las barreras y por el nombre de cada ítem."""
    prohibidas = set(N.RETIRADAS) | {'doble_carga'}
    malos = [i for i in c['T529'].columns if N38.variable_de_item(i) in prohibidas]
    tablas = [c['TODAS'], c['AB'], *c['Hs'].values()]
    for t in tablas:
        for a in t['antecedente'].unique():
            for i in a.split(' & '):
                if 'prevision' in i or 'diabetes' in i or 'doble' in i or i.split('=')[0] not in N38.VAR_DE_CORTO or N38.variable_de_item(i) in prohibidas:
                    malos.append(i)
        for vs in t['variables'].astype(str).unique():
            malos += [v for v in vs.split(' & ') if v in prohibidas]
    for dim, Hd in c['Hs'].items():
        try:
            N.BAR.verificar_tabla_comparacion(Hd, 'principal', dim, c['pq'].dec, N.variable_de_item)
        except N.BAR.Incumplimiento as e:
            malos.append(str(e))
    for dim in N.DIMENSIONES:
        try:
            N.BAR.verificar_tabla_reglas(c['TODAS'][c['TODAS']['dimension'] == dim], 'principal', dim, c['pq'].dec, N.variable_de_item, N.CONSECUENTES)
        except N.BAR.Incumplimiento as e:
            malos.append(str(e))
    return not malos, f'sin prevision, usa_medicamentos_diabetes ni doble_carga en la matriz, las reglas, A/B1 y las comparaciones; problemas: {malos[:3]}'


def p24(c):
    """La construcción no depende de la lista histórica de 31: una lista histórica alterada no cambia nada, y cada configuración es la histórica menos las retiradas."""
    viejo = N38.PRINCIPAL
    try:
        N38.PRINCIPAL = [v for v in viejo if v != 'edad']
        T2, _ = N.base_items(c['pq'])
    finally:
        N38.PRINCIPAL = viejo
    ok = list(T2.columns) == list(c['T529'].columns) and bool((T2.to_numpy() == c['T529'].to_numpy()).all())
    filas = 0
    for sens in ('principal', 'S1', 'S2a', 'S5', 'S6', 'S7a', 'S7b'):
        Tc, _ = N.base_items(c['pq'], sens)
        Th, _ = N.H39.base_items(c['d'], sens)
        resto = Th.drop(columns=[x for x in Th.columns if N.variable_de_item(x) in N.RETIRADAS])
        ok &= list(resto.columns) == list(Tc.columns) and bool((resto.to_numpy() == Tc.to_numpy()).all())
        filas += 1
    return bool(ok), f'{filas} configuraciones iguales a la histórica sin las variables retiradas; la construcción no consulta N38.PRINCIPAL'


def p25(c):
    """Módulos de S7a y S7b: solo en su estrato, con la población declarada."""
    d = c['d']
    r = []
    for sens, (dim, e) in N.BAR.ESTRATO_MODULO.items():
        T, _ = N.base_items(c['pq'], sens)
        x = N.BAR.verificar_modulos(d, T, sens, c['masc'][(dim, e)], N.variable_de_item)
        r.append((sens, x['participantes'], x['con_items_del_modulo'], x['sin_items_del_modulo']))
    ok = r == [('S7a', 309, 287, 22), ('S7b', 251, 251, 0)]
    return ok, f'{r}: S7a sobre 309 (22 sin respuestas laborales) y S7b sobre 251; no se usa 263'


def p26(c):
    tmp = BASE / 'pruebas' / 'tmp_reproducibilidad_comp'
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        dim = 'trabajo'
        Hd, _, _ = H.comparar(c['T529'], c['y'], c['masc'], dim, N.dims_de(dim), N.UMBRALES['principal'][4], 2, tmp, [N.SEMILLA, 39, 100 + N.NUM_DIM[dim]], [N.SEMILLA, 39, 3, N.NUM_DIM[dim]], n_perm=N.N_PERM)
        g = pd.read_csv(BASE / 'comparacion' / f'comparacion_{dim}.csv')
        ok = len(Hd) == len(g) and (Hd['antecedente'].to_numpy() == g['antecedente'].to_numpy()).all() and np.allclose(Hd['Q'].to_numpy(float), g['Q'].to_numpy(float), rtol=1e-12) and np.allclose(Hd['p_ajustado_dimension'].to_numpy(float), g['p_ajustado_dimension'].to_numpy(float), rtol=1e-12) and (Hd['clase'].to_numpy() == g['clase'].to_numpy()).all() and np.allclose(Hd['reaparece_marcada'].to_numpy(float), g['reaparece_marcada'].to_numpy(float))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return bool(ok), f'comparación de trabajo, nula y estabilidad repetidas desde cero: {len(Hd)} comparaciones idénticas'


def p27(c):
    """Las salidas coinciden con el protocolo sellado: estratos, sensibilidades, 1.000 permutaciones y 200 submuestras."""
    malos = []
    M = pd.read_csv(BASE / 'reglas' / 'resumen_estratos.csv')
    if len(M) != 9 or set(M['estrato']) != {e for _, e in N.ESTRATOS}:
        malos.append('estratos')
    for dim, e in N.ESTRATOS:
        if len(pd.read_csv(BASE / 'referencia_nula' / f'nula_{dim}_{e}.csv')) != 1000:
            malos.append(f'nula {e}')
    for dim in N.DIMENSIONES:
        if len(c['nulas_h'][dim]) != 1000 or c['Hs'][dim]['submuestras_evaluables'].max() > 200:
            malos.append(f'comparación {dim}')
    if len(pd.read_csv(BASE / 'referencia_nula' / 'nula_conjunta_estratos.csv')) != 1000 or len(pd.read_csv(BASE / 'comparacion' / 'nula_conjunta_dimensiones.csv')) != 1000:
        malos.append('nulas conjuntas')
    S = pd.read_csv(BASE / 'sensibilidades' / 'resumen_sensibilidades_estratos.csv')
    esperado = {'S1': 9, 'S2a': 9, 'S3-bajo': 9, 'S3-alto': 9, 'S4-1': 9, 'S4-2': 9, 'S5': 9, 'S6': 9, 'S7a': 1, 'S7b': 1}
    if S.groupby('sensibilidad').size().to_dict() != esperado or 'S7a-263' in set(S['sensibilidad']):
        malos.append('sensibilidades de estratos')
    Hc = pd.read_csv(BASE / 'sensibilidades' / 'resumen_sensibilidades_comparacion.csv')
    if set(Hc['sensibilidad']) != set(N.SENSIBILIDADES) or len(Hc[(Hc['sensibilidad'] == 'S9')]) != 1:
        malos.append('sensibilidades de comparación')
    G_ = pd.read_csv(BASE / 'ab1' / 'resumen_grupos_A_B1.csv')
    if len(G_) != 8:
        malos.append('A y B1')
    return not malos, f'9 estratos, 11 sensibilidades, 8 grupos, 1.000 permutaciones por referencia; problemas: {malos[:3]}'


PRUEBAS = [('Exactamente 529 identificadores originales', p01), ('MRS severo correcto', p02), ('Tamaños de estratos, frecuencias basales y umbrales', p03),
           ('Pertenencia correcta a los estratos', p04), ('Codificación idéntica a la Fase 38R', p05), ('Sin ítems del MRS, etiquetas ni variables excluidas entre los antecedentes', p06),
           ('Sin reglas contradictorias', p07), ('Sin la variable del estrato ni condiciones constantes', p08), ('Soporte, confianza, lift y diferencias de riesgo', p09),
           ('Referencia nula dentro del estrato', p10), ('Comparación entre estratos', p11), ('Referencia nula de la comparación', p12),
           ('Calibración del estadístico de interacción', p13), ('Control de la búsqueda múltiple', p14), ('Tratamiento de imputaciones', p15),
           ('Reproducibilidad de reglas y nula', p16), ('Etiquetas A y B1 intactas', p17), ('Fases anteriores sin cambios (control correctivo)', p18), ('src/ sin cambios desde la medición inicial (control correctivo)', p19),
           ('Sello del protocolo previo a los resultados', p20), ('Clasificación', p21), ('Conclusión mecánica', p22), ('Exclusiones en todas las entradas y salidas de modelado', p23),
           ('Construcción independiente de la lista histórica', p24), ('Módulos de S7a y S7b', p25), ('Reproducibilidad de la comparación', p26), ('Salidas coinciden con el protocolo sellado', p27)]
LENTAS = {'p16', 'p18', 'p26'}


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
def m_fila(c, t, **k):
    fila = c[t].iloc[[0]].copy()
    for a, b in k.items():
        fila[a] = b
    c[t] = pd.concat([c[t], fila], ignore_index=True)


def m_fila_h(c, dim, **k):
    fila = c['Hs'][dim].iloc[[0]].copy()
    for a, b in k.items():
        fila[a] = b
    c['Hs'][dim] = pd.concat([c['Hs'][dim], fila], ignore_index=True)


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
    N.base_items = lambda pq, sens='principal': viejo(pq, 'principal' if sens == 'S1' else sens)
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


def mut_lista_31():
    """La construcción vuelve a usar la lista histórica de 31 variables: la matriz deja de ser la de la 38R."""
    viejo = N.base_items

    def malo(pq, sens='principal'):
        T, tr = N.H39.base_items(pq.d, sens)
        return T, tr
    N.base_items = malo
    return lambda: setattr(N, 'base_items', viejo)


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
    ('Regla con prevision', lambda c: m_fila(c, 'TODAS', antecedente='prevision=FONASA', variables='prevision'), None),
    ('Regla con med_diabetes', lambda c: m_fila(c, 'TODAS', antecedente='med_diabetes=SI', variables='usa_medicamentos_diabetes'), None),
    ('Regla con doble_carga', lambda c: m_fila(c, 'TODAS', antecedente='doble_carga=SI', variables='doble_carga'), None),
    ('Regla en A o B1 con prevision', lambda c: m_fila(c, 'AB', antecedente='prevision=ISAPRE', variables='prevision'), None),
    ('Comparación con prevision', lambda c: m_fila_h(c, 'pareja', antecedente='prevision=FONASA', variables='prevision'), None),
    ('Comparación con doble_carga', lambda c: m_fila_h(c, 'cuidado', antecedente='doble_carga=SI', variables='doble_carga'), None),
    ('Etiqueta A como antecedente', lambda c: m_fila(c, 'TODAS', antecedente='A=1', variables='A'), None),
    ('Construcción con la lista histórica de 31', lambda c: c.update(T529=N.H39.base_items(c['d'])[0]), None),
    ('base_items histórico en la corrección', lambda c: None, mut_lista_31),
    ('Conclusión sin exigir la nula conjunta', lambda c: c['conc'].__setitem__('detalle_H5', [{'dimension': 'trabajo', 'supera_nula_conjunta': False, 'mantiene_en_nucleo': True, 'lectura_S9': 'no evaluable', 'evaluables_nucleo': 5, 'consistente': True}]), None),
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
            c = {k: (copy.deepcopy(v) if k not in ('d', 'pq', 'T529', 'masc', 'limpio', 'ini') else v) for k, v in ctx.items()}
            deshacer = parche() if parche else None
            try:
                f(c)
                solo = None if nombre in ('Semilla distinta (no reproducible)', 'Archivo histórico modificado') else {p.__name__ for _, p in PRUEBAS} - LENTAS
                r = correr(c, solo)
            finally:
                if deshacer:
                    deshacer()
            fallan = [x['n'] for x in r if x['resultado'] != 'superada' and x['n'] in base_ok]
            filas.append({'control_negativo': nombre, 'detectado': bool(fallan), 'pruebas_que_fallan': ', '.join(fallan), 'motivo': '; '.join(x['detalle'] for x in r if x['n'] in fallan)[:300]})
            print(nombre, '→', fallan, flush=True)
        Mt = pd.DataFrame(filas)
        N.a_csv(Mt, BASE / 'pruebas' / 'control_mutaciones.csv')
        print(f"{int(Mt['detectado'].sum())}/{len(Mt)} controles negativos detectados")
        if not Mt['detectado'].all():
            print(Mt[~Mt['detectado']].to_string())
    N.registrar('pruebas')
    print(f"{(D['resultado'] == 'superada').sum()}/{len(D)} pruebas superadas, {time.time() - t0:.0f} s")
    sys.exit(0 if (D['resultado'] == 'superada').all() else 1)


if __name__ == '__main__':
    main()
