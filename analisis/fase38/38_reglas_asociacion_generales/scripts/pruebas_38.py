"""
Fase 38: pruebas y controles negativos. Cada prueba recalcula desde el código (no solo lee tablas), de modo que un error introducido en memoria la haga fallar.

Uso, desde la carpeta scripts: python pruebas_38.py [--mutaciones]
"""
import copy
import math
import subprocess
import sys
import time
import traceback
from itertools import combinations

import algoritmos_38 as G
import evaluacion_38 as EV
import integridad_38 as I
import nucleo_38 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
N.instalar_gancho()
B = N.BASE
D_ORIG = N.cargar()
SELLO = N.huella_sello()
IDS_F36 = pd.read_csv(N.ANALISIS / 'fase36' / 'matrices' / 'identificadores.csv', dtype=str)['participante_id'].tolist()
LIMPIO = pd.read_csv(N.N37.LIMPIO, dtype=str, keep_default_na=False, na_values=['']).set_index('participante_id')
R_CSV = pd.read_csv(B / 'reglas' / 'reglas_principal.csv')
NULA_CSV = pd.read_csv(B / 'referencia_nula' / 'nula_principal.csv')
PERMITIDAS = set(N.PRINCIPAL) | {'imc', 'lugar_trabajo_comprensivo', 'estres_entorno_laboral', 'sobrecarga_fisica_emocional'}


class Ctx:
    pass


def contexto(d=None):
    x = Ctx()
    x.d = d or D_ORIG
    x.c = N.construir(x.d, 'principal')
    x.frec = EV.descubrir(x.c)
    x.det = N.pares_determinados(x.c.T)
    x.R = EV.reglas_de(x.c, x.frec, x.det)
    return x


def p01(x):
    ids = list(x.c.ids)
    assert len(ids) == 529 and len(set(ids)) == 529, 'no son 529 únicas'
    assert ids == IDS_F36, 'identificadores u orden distintos de la Fase 36'
    return '529 únicas, en el orden de la Fase 36'


def p02(x):
    L = LIMPIO.reindex(x.c.ids)
    assert (x.c.T['trabaja=SI'].to_numpy() == L['trabaja_actualmente'].isin(['SI', 'True', '1']).to_numpy()).all(), 'trabaja no coincide con la limpieza'
    assert (x.c.T['pareja=SI'].to_numpy() == L['tiene_pareja'].isin(['SI', 'True', '1']).to_numpy()).all(), 'pareja no coincide con la limpieza'
    M = pd.read_csv(B / 'preparacion' / 'matriz_transaccional_principal.csv', dtype={'participante_id': str})
    assert M['participante_id'].tolist() == list(x.c.ids), 'la matriz guardada no está alineada'
    assert (M.drop(columns=['participante_id', 'severo_mrs=SI', 'severo_mrs=NO']).to_numpy() == x.c.T.astype(int).to_numpy()).all(), 'la matriz guardada no coincide'
    return 'ítems coinciden con la limpieza y con la matriz guardada'


def p03(x):
    L = LIMPIO.reindex(x.c.ids)
    total = L[[f'pregunta_{i}' for i in range(1, 12)]].astype(int).sum(axis=1).to_numpy()
    assert (x.c.y == (total >= 16)).all(), 'severo_mrs no reproduce MRS total ≥ 16'
    assert x.c.n_si == 281, f'severo = {x.c.n_si}, se esperaba 281'
    f35 = pd.read_csv(N.N37.F35, dtype=str)
    assert (pd.to_numeric(f35['severo_mrs']).to_numpy() == x.c.y).all(), 'no coincide con la Fase 35'
    return '281 severas; coincide con los ítems, la limpieza y la Fase 35'


def p04(x):
    malos = [i for i in x.c.T.columns if i.split('=')[0].startswith(('mrs', 'pregunta', 'severo', 'severidad', 'segmento', 'grupo'))]
    assert not malos, f'ítems prohibidos: {malos}'
    vs = {N.variable_de_item(i) for i in x.c.T.columns}
    assert vs == set(N.PRINCIPAL), f'variables distintas del protocolo: {vs ^ set(N.PRINCIPAL)}'
    return 'ningún ítem del MRS ni de segmentos; 31 variables del protocolo'


def p05(x):
    t = N.transacciones(x.c.T, x.c.y)
    for s in t:
        vs = [N.variable_de_item(i) for i in s if i not in N.CONSECUENTES]
        assert len(vs) == len(set(vs)), 'dos estados de una misma variable'
        assert len(s & set(N.CONSECUENTES)) == 1, 'consecuente ausente o duplicado'
    return 'ninguna transacción con dos estados de una variable'


def p06(x):
    sup = x.c.T.sum()
    assert sup.min() >= N.MIN_CAT, f'ítem con menos de 27: {sup.idxmin()} ({sup.min()})'
    assert not any(i.startswith(('prepara=compra', 'prepara=otro=', 'prevision=FFAA', 'prevision=NINGUNA', 'prevision=NS')) for i in x.c.T.columns), 'nominal escasa con ítem'
    for v in N.PRINCIPAL:
        cols = [i for i in x.c.T.columns if N.variable_de_item(i) == v]
        cubierto = x.c.T[cols].any(axis=1).to_numpy()
        s = x.d.X[v]
        sin = (~cubierto).sum()
        esperado = int(s.isna().sum()) + (int(s.isin(['COMPRO', 'OTRO']).sum()) if v == 'quien_prepara_comidas' else 0) + (int(s.isin(['FFAA', 'NINGUNA', 'NS']).sum()) if v == 'prevision' else 0)
        assert sin == esperado, f'{v}: {sin} sin ítem, se esperaban {esperado}'
    g = N.agrupar_ordinal([(1, 302), (2, 148), (3, 52), (4, 15), (5, 12)])
    assert g == [([1], 302), ([2], 148), ([3], 52), ([4, 5], 27)], f'R2 incorrecta: {g}'
    return 'todos los ítems ≥ 27; R2 y R3 aplicadas; cada participante tiene ítem salvo faltantes y R3'


def p07(x):
    c1 = N.construir(x.d, 'S1')
    imp = x.d.estado['tiene_pareja'].isin(['imputada', 'deducida']).to_numpy()
    tiene = c1.T[['pareja=NO', 'pareja=SI']].any(axis=1).to_numpy()
    assert (~tiene == imp).all(), 'S1: las celdas imputadas de pareja conservan ítem'
    assert not any(N.variable_de_item(i) in N.SIN_MARCA for i in c1.T.columns), 'S1 conserva diabetes o previsión'
    assert x.c.T[['pareja=NO', 'pareja=SI']].any(axis=1).all(), 'principal sin ítem de pareja en imputadas'
    return f'S1 quita {int(imp.sum())} celdas imputadas de pareja; principal las conserva'


def p08(x):
    a = N.construir(x.d, 'S7a')
    assert a.n == int((x.d.X['trabaja_actualmente'] == 1).sum()) == 309, 'S7a no es la población que trabaja'
    assert not any(i.startswith('trabaja=') for i in a.T.columns), 'S7a conserva la pregunta de entrada'
    assert any(i.startswith('estres_laboral=') for i in a.T.columns)
    b = N.construir(x.d, 'S7b')
    assert b.n == 251 and 'cuida=no_cuida' not in b.T.columns, 'S7b mal construida'
    assert not any(i.startswith(('estres_laboral', 'lugar_comprensivo', 'sobrecarga', 'imc')) for i in x.c.T.columns), 'módulo en la principal'
    return 'S7a: 309 que trabajan; S7b: 251 que cuidan; módulos fuera de la principal'


def p09(x):
    rng = np.random.default_rng(7)
    V = x.c.T
    muestra = x.R.iloc[rng.choice(len(x.R), 60, replace=False)]
    p0 = x.c.n_si / x.c.n
    for r in muestra.itertuples():
        m = V[list(r.items)].all(axis=1).to_numpy()
        nA = int(m.sum())
        k = int((m & (x.c.y == 1)).sum()) if r.consecuente.endswith('SI') else int((m & (x.c.y == 0)).sum())
        base = p0 if r.consecuente.endswith('SI') else 1 - p0
        conf = k / nA
        assert nA == r.n_antecedente and k == r.n_conjunto, 'recuentos'
        assert math.isclose(r.soporte, k / 529) and math.isclose(r.confianza, conf), 'soporte o confianza'
        assert math.isclose(r.lift, conf / base), 'lift'
        assert math.isclose(r.leverage, k / 529 - nA / 529 * base, abs_tol=1e-12), 'leverage'
        kno = (int((x.c.y == 1).sum()) if r.consecuente.endswith('SI') else int((x.c.y == 0).sum())) - k
        assert math.isclose(r.diferencia_riesgo, conf - kno / (529 - nA)), 'diferencia de riesgo'
        lo, hi = N.wilson(k, nA)
        from statsmodels.stats.proportion import proportion_confint
        l2, h2 = proportion_confint(k, nA, method='wilson')
        assert abs(lo - l2) < 1e-9 and abs(hi - h2) < 1e-9, 'Wilson distinto de statsmodels'
        assert r.lift >= 1, 'dirección con lift < 1'
    return '60 reglas al azar: recuentos, soporte, confianza, lift, leverage, diferencia de riesgo y Wilson correctos'


def p10(x):
    E = pd.read_csv(B / 'reglas' / 'equivalencia_comparaciones.csv')
    assert E['mismos_conjuntos_y_recuentos'].all() and E['mismas_reglas'].all(), 'equivalencia guardada falla'
    rng = np.random.default_rng(11)
    for _ in range(2):
        y = rng.permutation(x.c.y)
        a, f, e = G.apriori(x.c.T, y, 27, 3), G.fpgrowth(x.c.T, y, 27, 3), G.exhaustiva(x.c.T, y, 27, 3)
        assert G.iguales(a, f)[0] and G.iguales(a, e)[0], 'algoritmos distintos con consecuente permutado'
    return 'Apriori = FP-Growth = exhaustiva en la principal y en 2 permutaciones'


def p11(x):
    rng = np.random.default_rng(12)
    ants = list(G.antecedentes(x.frec, x.c.min_ant, x.det))
    A = G.matriz_antecedentes(x.c.T, ants)
    for _ in range(2):
        y = rng.permutation(x.c.y)
        k = G.contar(A, y[:, None])[:, 0]
        f = G.fpgrowth(x.c.T, y, 27, 3)
        for s, kk in zip(ants, k):
            si = f.get(s | {N.CONSECUENTES[0]})
            si = si if si is not None else f[s] - f[s | {N.CONSECUENTES[1]}]
            assert si == kk, 'evaluador matricial distinto de FP-Growth'
    sub = np.sort(rng.choice(529, 423, replace=False))
    T2 = x.c.T.iloc[sub].reset_index(drop=True)
    f2 = G.fpgrowth(T2, x.c.y[sub], 1, 3)
    S = np.zeros((529, 1), np.uint8)
    S[sub, 0] = 1
    nA = G.contar(A, S)[:, 0]
    for s, n in list(zip(ants, nA))[:3000]:
        assert f2.get(s, 0) == n, 'submuestra: evaluador distinto de FP-Growth'
    return 'evaluador matricial = FP-Growth en 2 permutaciones y en una submuestra'


def p12(x):
    a = R_CSV[['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']].reset_index(drop=True)
    b = x.R[['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']].reset_index(drop=True)
    assert a.equals(b), 'las reglas no se reproducen'
    assert np.allclose(R_CSV['q_bh_todas'], x.R['q_bh_todas']), 'q no se reproduce'
    rng = np.random.default_rng(N.SEMILLA)
    perms = [rng.permutation(x.c.n) for _ in range(100)]
    ants = list(G.antecedentes(x.frec, x.c.min_ant, x.det))
    A = G.matriz_antecedentes(x.c.T, ants)
    nA = np.array([x.frec[s] for s in ants], float)
    Y = np.stack([x.c.y[p] for p in perms], axis=1)
    z, val, dif = G.z_y_validez(nA, G.contar(A, Y), x.c.n, x.c.n_si, x.c.min_conj)
    assert np.allclose(np.where(val, z, 0).max(axis=0), NULA_CSV['max_z'].iloc[:100]), 'el primer lote nulo no se reproduce'
    return 'reglas, q y primer lote de la referencia nula se reproducen exactamente'


def p13(x):
    d2 = copy.copy(x.d)
    d2.M = x.d.M.copy()
    d2.M['severo_mrs'] = np.random.default_rng(3).permutation(x.d.M['severo_mrs'].to_numpy())
    c2 = N.construir(d2, 'principal')
    assert c2.T.equals(x.c.T), 'las agrupaciones dependen del consecuente'
    E = pd.read_csv(B / 'estabilidad' / 'estabilidad_reglas.csv')
    meta = N.leer_json(B / 'reglas' / 'resumen_principal.json')['estabilidad']
    assert meta['n_submuestra'] == 423 and meta['umbral_antecedente'] == 43 and meta['umbral_conjunto'] == 22, 'umbrales de submuestra no proporcionales'
    assert len(E) == len(x.R) and E['reaparece_marcada'].between(0, 1).all()
    return 'las agrupaciones no dependen del consecuente; umbrales de submuestra 43 y 22 (proporcionales)'


def p14(x):
    rng = np.random.default_rng(N.SEMILLA)
    p = rng.permutation(x.c.n)
    assert x.c.y[p].sum() == x.c.y.sum(), 'la permutación no conserva la frecuencia basal'
    ants = list(G.antecedentes(x.frec, x.c.min_ant, x.det))
    assert len(ants) == N.leer_json(B / 'reglas' / 'resumen_principal.json')['antecedentes_evaluados'], 'antecedentes de la nula distintos'
    m = NULA_CSV['max_z'].to_numpy()
    assert len(m) == N.N_PERM
    for r in R_CSV.sample(40, random_state=1).itertuples():
        assert math.isclose(r.p_ajustado_busqueda, (1 + (m >= abs(r.z)).sum()) / (1 + len(m))), 'p ajustado mal calculado'
    marc = NULA_CSV['reglas_marcadas']
    assert marc.mean() < R_CSV['marcada'].sum(), 'sin diferencia con la nula'
    # control: con y permutado, las reglas marcadas deben estar en el rango nulo
    y = np.random.default_rng(99).permutation(x.c.y)
    f = G.fpgrowth(x.c.T, y, 27, 3)
    Rp = G.reglas(f, 529, int(y.sum()), 53, 27, x.det)
    assert marc.min() <= Rp['marcada'].sum() <= marc.max() and Rp['marcada'].sum() < R_CSV['marcada'].sum(), 'una permutación nueva queda fuera del rango nulo'
    return f'permutación conserva 281; p ajustado verificado; una permutación nueva da {int(Rp["marcada"].sum())} marcadas (nula: media {marc.mean():.0f})'


def p15(x):
    assert len(x.R) == len(R_CSV) and x.R['q_bh_todas'].notna().all(), 'BH no aplicado a todas las reglas'
    from statsmodels.stats.multitest import multipletests
    q2 = multipletests(x.R['p_fisher'], method='fdr_bh')[1]
    assert np.allclose(q2, x.R['q_bh_todas']), 'BH distinto de statsmodels'
    prot = (B / 'protocolo' / '01_protocolo_38.md').read_text(encoding='utf-8')
    assert 'no confirma nada' in prot and 'Westfall-Young' in prot and 'no solo a las seleccionadas' in prot, 'el protocolo no declara la multiplicidad'
    return f'BH sobre las {len(x.R)} reglas evaluadas; control de búsqueda por máximo |z|; declarado en el protocolo'


def p16(x):
    for it in x.R['items']:
        assert 1 <= len(it) <= 3, 'largo fuera de 1-3'
        vs = [N.variable_de_item(i) for i in it]
        assert len(vs) == len(set(vs)), 'antecedente repite variable'
        assert not set(it) & set(N.CONSECUENTES), 'consecuente en el antecedente'
    c = N.construir(x.d, 'S2a')
    det = N.pares_determinados(c.T)
    assert det, 'S2a debería tener pares determinados'
    f = EV.descubrir(c)
    R2 = EV.reglas_de(c, f, det)
    for it in R2['items']:
        assert not any((a, b) in det for a in it for b in it if a != b), 'regla con par determinado'
    f1 = G.exhaustiva(c.T, c.y, 1, 2)
    ants = G.antecedentes(f1, 1, det)
    assert not any((a, b) in det for s_ in ants for a in s_ for b in s_ if a != b), 'el filtro deja pasar pares determinados'
    assert any((a, b) in det for s_ in f1 for a in s_ for b in s_ if a != b), 'control: sin pares determinados que filtrar'
    return f'antecedentes de 1-3 variables distintas, sin consecuente; en S2a se excluyen {len(det)} pares determinados'


def p17(x):
    m = I.manifiestos()
    assert int(m['distintos'].sum()) == 0, f'archivos protegidos modificados: {m[m["distintos"] > 0]["fase"].tolist()}'
    assert not I.pycache(), 'hay __pycache__ en fases protegidas'
    return f"{int(m['comparados_por_huella'].sum())} archivos protegidos iguales a sus manifiestos (34 a 37D)"


def p18(x):
    g = I.estado_git()
    assert g['head'] == I.HEAD_ESPERADO and not g['cambios_en_src'] and not g['datos_versionados_modificados'] and not g['cambios_fuera_de_analisis'], 'git, Django o datos cambiaron'
    return 'HEAD 745d689; sin cambios en src/, datos/ ni fuera de analisis/'


def p19(x):
    s = N.huella_sello()
    t = pd.Timestamp(s['sellado']).timestamp()
    for p in list((B / 'reglas').glob('*.csv')) + list((B / 'referencia_nula').rglob('*.npz')):
        assert p.stat().st_mtime > t, f'resultado anterior al sello: {p.name}'
    return 'protocolo íntegro; todas las reglas y permutaciones son posteriores al sello'


def p20(x):
    R = EV.ajustar(x.R, NULA_CSV)
    E = pd.read_csv(B / 'estabilidad' / 'estabilidad_reglas.csv')
    R = EV.clasificar(R, E)
    assert (R['clase'] == R_CSV['clase']).all(), 'la clasificación no se reproduce'
    s = R[R['clase'].str.startswith('6')]
    assert (s['marcada'] & s['supera_nula'] & s['estable'] & (s['mejora_sobre_subreglas'].isna() | (s['mejora_sobre_subreglas'] >= 0.05))).all(), 'clase 6 sin todos los criterios'
    fc = EV.mapa_consecuente(x.frec)
    for rr in R[R['largo'] > 1].sample(80, random_state=2).itertuples():
        subs = [s_ for k in range(1, rr.largo) for s_ in combinations(rr.items, k)]
        cs = [(fc[frozenset(s_)][1] if rr.consecuente.endswith('SI') else fc[frozenset(s_)][0] - fc[frozenset(s_)][1]) / fc[frozenset(s_)][0] for s_ in subs]
        assert math.isclose(rr.mejora_sobre_subreglas, rr.confianza - max(cs)), 'mejora mal calculada'
        assert rr.redundante == (rr.mejora_sobre_subreglas < 0.05), 'umbral de redundancia distinto de 0,05'
    return f"clasificación reproducida; {len(s)} en clase 6, con todos los criterios; redundancia verificada en 80 reglas"


PRUEBAS = [('529 participantes únicas e identificadores', p01), ('Correspondencia con las fuentes históricas', p02), ('MRS severo correcto', p03),
           ('Sin variables MRS ni segmentos entre los antecedentes', p04), ('Sin condiciones contradictorias', p05), ('Categorías originales y agrupadas', p06),
           ('Tratamiento de imputaciones (S1)', p07), ('Módulos parciales (S7)', p08), ('Soporte, confianza, lift, leverage', p09),
           ('Equivalencia Apriori / FP-Growth / exhaustiva', p10), ('Evaluador matricial equivalente', p11), ('Reproducibilidad', p12),
           ('Estabilidad sin fuga de información', p13), ('Referencia nula', p14), ('Comparaciones múltiples reconocidas', p15),
           ('Sin reglas triviales', p16), ('Fases anteriores intactas', p17), ('Django, datos y git sin cambios', p18), ('Protocolo sellado antes de los resultados', p19),
           ('Clasificación y redundancia coherentes', p20)]


def correr(x, solo=None):
    out = []
    for i, (nombre, f) in enumerate(PRUEBAS, 1):
        if solo and i not in solo:
            continue
        t = time.time()
        try:
            det = f(x)
            out.append({'n': i, 'prueba': nombre, 'resultado': 'superada', 'detalle': det, 'segundos': round(time.time() - t, 1)})
        except Exception as e:
            out.append({'n': i, 'prueba': nombre, 'resultado': 'FALLA', 'detalle': f'{type(e).__name__}: {e}'[:300], 'segundos': round(time.time() - t, 1)})
    return pd.DataFrame(out)


def mutaciones():
    """Cada control cambia algo en memoria, reconstruye el contexto y exige que alguna prueba falle. Se restaura después."""
    M = []

    def con(nombre, aplicar, deshacer, d=None, solo=None):
        aplicar()
        try:
            try:
                x = contexto(d() if d else None)
                r = correr(x, solo)
                fallan = r[r['resultado'] != 'superada']
                M.append({'control_negativo': nombre, 'detectado': len(fallan) > 0, 'pruebas_que_fallan': ', '.join(map(str, fallan['n'])),
                          'motivo': fallan['detalle'].iloc[0] if len(fallan) else ''})
            except Exception as e:
                M.append({'control_negativo': nombre, 'detectado': True, 'pruebas_que_fallan': 'construcción', 'motivo': f'{type(e).__name__}: {e}'[:200]})
        finally:
            deshacer()
        print(M[-1]['control_negativo'], M[-1]['detectado'], M[-1]['pruebas_que_fallan'], flush=True)

    orig = {k: getattr(N, k) for k in ('medidas', 'agrupar_ordinal', 'transacciones', 'wilson', 'construir', 'bh', 'pares_determinados', 'MEJORA_MIN', 'esquema')}
    orig_g = {k: getattr(G, k) for k in ('fpgrowth', 'contar', 'antecedentes')}
    orig_ev = {k: getattr(EV, k) for k in ('clasificar',)}

    def rest():
        for k, v in orig.items():
            setattr(N, k, v)
        for k, v in orig_g.items():
            setattr(G, k, v)
        for k, v in orig_ev.items():
            setattr(EV, k, v)

    def lift_malo(*a, **k):
        R = orig['medidas'](*a, **k)
        R['lift'] = R['confianza'] / (1 - R['frecuencia_basal'])
        return R
    con('Lift calculado con la basal equivocada', lambda: setattr(N, 'medidas', lift_malo), rest, solo=[9])
    con('Wilson sin corrección', lambda: setattr(N, 'wilson', lambda k, n, z=1.96: (np.asarray(k) / n - 0.01, np.asarray(k) / n + 0.01)), rest, solo=[9])
    con('R2 desactivada (sin unir categorías escasas)', lambda: setattr(N, 'agrupar_ordinal', lambda conteos, minimo=27: [([c], n) for c, n in conteos]), rest, solo=[6])

    def con_severo(d, nombre):
        c = orig['construir'](d, nombre)
        c.T['severidad_mrs=alta'] = c.y.astype(bool)
        return c
    con('Severidad del MRS como antecedente', lambda: setattr(N, 'construir', con_severo), rest, solo=[4])

    def trans_mala(T, y):
        t = orig['transacciones'](T, y)
        return [s | {'trabaja=NO', 'trabaja=SI'} for s in t]
    con('Dos estados de una variable en la transacción', lambda: setattr(N, 'transacciones', trans_mala), rest, solo=[5])

    def d_corte15():
        d2 = copy.copy(D_ORIG)
        d2.M = D_ORIG.M.copy()
        d2.M['severo_mrs'] = (d2.M['mrs_total'] >= 15).astype(int)
        return d2
    con('Corte de severidad en 15', lambda: None, rest, d=d_corte15, solo=[3])

    def d_ids():
        d2 = copy.copy(D_ORIG)
        d2.ids = list(reversed(D_ORIG.ids))
        return d2
    con('Identificadores en otro orden', lambda: None, rest, d=d_ids, solo=[1, 2])

    def s1_mala(d, nombre):
        if nombre == 'S1':
            return orig['construir'](d, 'principal')
        return orig['construir'](d, nombre)
    con('S1 sin quitar imputados', lambda: setattr(N, 'construir', s1_mala), rest, solo=[7])

    def s7_mala(d, nombre):
        if nombre == 'S7a':
            c = orig['construir'](d, 'principal')
            c.n = 529
            return c
        return orig['construir'](d, nombre)
    con('S7a sin restringir a quienes trabajan', lambda: setattr(N, 'construir', s7_mala), rest, solo=[8])

    def fp_malo(T, y, minsup, max_ant=3):
        f = orig_g['fpgrowth'](T, y, minsup, max_ant)
        f.pop(sorted(f, key=lambda s: sorted(s))[100])
        return f
    con('FP-Growth pierde un conjunto frecuente', lambda: setattr(G, 'fpgrowth', fp_malo), rest, solo=[10, 11, 12])
    con('Evaluador matricial con recuento desplazado', lambda: setattr(G, 'contar', lambda A, Y, lote=20000: orig_g['contar'](A, Y, lote) + 1), rest, solo=[11, 12])

    def bh_seleccion(p):
        p = np.asarray(p, float)
        q = p.copy()
        sel = p < 0.01
        q[sel] = orig['bh'](p[sel]) if sel.any() else q[sel]
        return q
    con('BH aplicado solo a las reglas seleccionadas', lambda: setattr(N, 'bh', bh_seleccion), rest, solo=[12, 15])
    con('Sin excluir pares determinados', lambda: setattr(G, 'antecedentes', lambda frec, m, det=frozenset(): orig_g['antecedentes'](frec, m, frozenset())), rest, solo=[16])
    con('Mejora mínima de redundancia en 0', lambda: setattr(N, 'MEJORA_MIN', 0.0), rest, solo=[12, 20])

    def clas_mala(R, E=None, sp=None):
        R2 = orig_ev['clasificar'](R, E, sp)
        R2.loc[R2['clase'].str.startswith('4'), 'clase'] = '6 asociación relativamente más marcada'
        return R2
    con('Reglas compatibles con la nula pasadas a la clase 6', lambda: setattr(EV, 'clasificar', clas_mala), rest, solo=[20])

    def esq_y(X, defs, modo='principal'):
        e = orig['esquema'](X, defs, modo)
        y = D_ORIG.M['severo_mrs'].to_numpy()
        if 'edad' in e:
            e['edad'][0]['mascara'] = e['edad'][0]['mascara'] & (y == 1) if len(y) == len(e['edad'][0]['mascara']) else e['edad'][0]['mascara']
        return e

    def d_perm():
        d2 = copy.copy(D_ORIG)
        d2.M = D_ORIG.M.copy()
        d2.M['severo_mrs'] = np.random.default_rng(5).permutation(D_ORIG.M['severo_mrs'].to_numpy())
        return d2
    con('Agrupación que usa el consecuente (fuga)', lambda: setattr(N, 'esquema', esq_y), rest, solo=[13])
    con('Consecuente permutado (sin relación real)', lambda: None, rest, d=d_perm, solo=[3, 12])
    con('Pares determinados nunca detectados', lambda: setattr(N, 'pares_determinados', lambda T: set()), rest, solo=[16])
    return pd.DataFrame(M)


if __name__ == '__main__':
    t0 = time.time()
    x = contexto()
    r = correr(x)
    N.a_csv(r, B / 'pruebas' / 'resultados_pruebas.csv')
    print(r[['n', 'prueba', 'resultado', 'detalle']].to_string(index=False))
    if '--mutaciones' in sys.argv:
        m = mutaciones()
        N.a_csv(m, B / 'pruebas' / 'control_mutaciones.csv')
        print(f"{int(m['detectado'].sum())} de {len(m)} errores detectados")
    N.registrar('pruebas')
    print(f'{(r["resultado"] == "superada").sum()}/{len(r)} superadas en {time.time() - t0:.0f} s')
    sys.exit(int((r['resultado'] != 'superada').any()))
