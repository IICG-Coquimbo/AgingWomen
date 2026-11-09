"""
Fase 38R, etapa D: pruebas (adaptación de las históricas) y controles negativos. Cada prueba recalcula desde el código.
Las históricas p17 y p18 (HEAD 745d689 y src/ sin cambios) ya no pueden cumplirse: las sustituyen integridad_38r.py y test_40b1, y se documenta.

Uso, desde la carpeta scripts: python -B pruebas_38r.py [--mutaciones]
"""
import copy
import math
import sys
import time
from itertools import combinations

sys.dont_write_bytecode = True
import nucleo_38r as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

G, EV, H = N.G, N.EV, N.H
N.instalar_gancho()
B = N.BASE
PQ = N.cargar()
SELLO = N.huella_sello()
IDS = pd.read_csv(N.ANALISIS / 'fase36/matrices/identificadores.csv', dtype=str)['participante_id'].tolist()
LIMPIO = pd.read_csv(N.N37.LIMPIO, dtype=str, keep_default_na=False, na_values=['']).set_index('participante_id')
R_CSV = pd.read_csv(B / 'reglas/reglas_principal.csv')
NULA = pd.read_csv(B / 'referencia_nula/nula_principal.csv')
ORIG_CONSTRUIR = N.construir


class Ctx:
    pass


def contexto(pq=None):
    x = Ctx()
    x.pq = pq or PQ
    x.d = x.pq.d
    x.c = N.construir(x.pq, 'principal')
    x.frec = EV.descubrir(x.c)
    x.det = H.pares_determinados(x.c.T)
    x.R = EV.reglas_de(x.c, x.frec, x.det)
    return x


def p01(x):
    assert list(x.c.ids) == IDS and len(set(IDS)) == 529, 'identificadores u orden distintos de la Fase 36'
    return '529 únicas, en el orden de la Fase 36'


def p02(x):
    L = LIMPIO.reindex(x.c.ids)
    assert (x.c.T['trabaja=SI'].to_numpy() == L['trabaja_actualmente'].isin(['SI', 'True', '1']).to_numpy()).all(), 'trabaja no coincide con la limpieza'
    M = pd.read_csv(B / 'preparacion/matriz_transaccional_principal.csv', dtype={'participante_id': str})
    assert M['participante_id'].tolist() == list(x.c.ids) and (M.drop(columns=['participante_id', 'severo_mrs=SI', 'severo_mrs=NO']).to_numpy() == x.c.T.astype(int).to_numpy()).all(), 'la matriz guardada no coincide'
    return 'ítems coinciden con la limpieza y con la matriz guardada'


def p03(x):
    L = LIMPIO.reindex(x.c.ids)
    total = L[[f'pregunta_{i}' for i in range(1, 12)]].astype(int).sum(axis=1).to_numpy()
    assert (x.c.y == (total >= 16)).all() and x.c.n_si == 281 and (x.c.n - x.c.n_si) == 248, 'severo_mrs no reproduce MRS total ≥ 16'
    return '281 severas y 248 no severas'


def p04(x):
    vs = {N.variable_de_item(i) for i in x.c.T.columns}
    assert vs == set(x.pq.dec['principal']), f'variables distintas: {vs ^ set(x.pq.dec["principal"])}'
    assert x.c.T.shape[1] == 90 and len(vs) == 29, 'no son 29 variables y 90 ítems'
    N.B.verificar_contenido(x.c.T.set_axis(range(529)), x.pq.vetadas)
    return '29 variables autorizadas y 90 ítems, sin contenido vetado'


def p05(x):
    for s in H.transacciones(x.c.T, x.c.y):
        vs = [N.variable_de_item(i) for i in s if i not in N.CONSECUENTES]
        assert len(vs) == len(set(vs)) and len(s & set(N.CONSECUENTES)) == 1, 'transacción con dos estados o sin consecuente'
    return 'ninguna transacción contradictoria'


def p06(x):
    assert x.c.T.sum().min() >= 27, 'ítem con menos de 27'
    assert not any(i.startswith(('prepara=compra', 'prepara=otro=')) for i in x.c.T.columns), 'nominal escasa con ítem'
    return 'todos los ítems ≥ 27 y R3 aplicada'


def p07(x):
    c1 = N.construir(x.pq, 'S1')
    imp = x.d.estado['tiene_pareja'].isin(['imputada', 'deducida']).to_numpy()
    assert (~c1.T[['pareja=NO', 'pareja=SI']].any(axis=1).to_numpy() == imp).all(), 'S1 conserva imputadas'
    return f'S1 quita {int(imp.sum())} celdas de pareja imputadas'


def p08(x):
    for nom, n, entrada in (('S7a', 287, 'trabaja='), ('S7a-309', 309, 'trabaja=')):
        a = N.construir(x.pq, nom)
        assert a.n == n and not any(i.startswith(entrada) for i in a.T.columns), f'{nom} mal construida'
    assert N.construir(x.pq, 'S7a').T[[c for c in N.construir(x.pq, 'S7a').T.columns if c.startswith('lugar_comprensivo=')]].any(axis=1).all(), 'S7a con faltantes laborales'
    b = N.construir(x.pq, 'S7b')
    assert b.n == 239 and 'cuida=no_cuida' not in b.T.columns and N.construir(x.pq, 'S7b-251').n == 251, 'S7b mal construida'
    assert not any(i.startswith(('estres_laboral', 'lugar_comprensivo', 'sobrecarga', 'imc')) for i in x.c.T.columns), 'módulo en la principal'
    return 'S7a 287, S7a-309 309, S7b 239, S7b-251 251; módulos fuera de la principal'


def p09(x):
    from statsmodels.stats.proportion import proportion_confint
    rng = np.random.default_rng(7)
    p0 = x.c.n_si / x.c.n
    for r in x.R.iloc[rng.choice(len(x.R), 60, replace=False)].itertuples():
        m = x.c.T[list(r.items)].all(axis=1).to_numpy()
        si = r.consecuente.endswith('SI')
        nA, k, base = int(m.sum()), int((m & (x.c.y == (1 if si else 0))).sum()), (p0 if si else 1 - p0)
        conf = k / nA
        assert nA == r.n_antecedente and k == r.n_conjunto and math.isclose(r.confianza, conf) and math.isclose(r.lift, conf / base), 'recuentos, confianza o lift'
        assert math.isclose(r.leverage, k / 529 - nA / 529 * base, abs_tol=1e-12), 'leverage'
        lo, hi = H.wilson(k, nA)
        l2, h2 = proportion_confint(k, nA, method='wilson')
        assert abs(lo - l2) < 1e-9 and abs(hi - h2) < 1e-9 and r.lift >= 1, 'Wilson o dirección'
    return '60 reglas: recuentos, confianza, lift, leverage y Wilson correctos'


def p10(x):
    E = pd.read_csv(B / 'reglas/equivalencia_comparaciones.csv')
    assert E['mismos_conjuntos_y_recuentos'].all() and E['mismas_reglas'].all(), 'equivalencia guardada falla'
    rng = np.random.default_rng(11)
    for _ in range(2):
        y = rng.permutation(x.c.y)
        a, f, e = G.apriori(x.c.T, y, 27, 3), G.fpgrowth(x.c.T, y, 27, 3), G.exhaustiva(x.c.T, y, 27, 3)
        assert G.iguales(a, f)[0] and G.iguales(a, e)[0], 'algoritmos distintos'
    return 'Apriori = FP-Growth = exhaustiva, también en 2 permutaciones'


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
            assert (si if si is not None else f[s] - f[s | {N.CONSECUENTES[1]}]) == kk, 'evaluador distinto de FP-Growth'
    return 'evaluador matricial = FP-Growth en 2 permutaciones'


def p12(x):
    a, b = R_CSV[['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']].reset_index(drop=True), x.R[['antecedente', 'consecuente', 'n_antecedente', 'n_conjunto']].reset_index(drop=True)
    assert a.equals(b) and np.allclose(R_CSV['q_bh_todas'], x.R['q_bh_todas']), 'las reglas o q no se reproducen'
    rng = np.random.default_rng(N.SEMILLA)
    perms = [rng.permutation(x.c.n) for _ in range(100)]
    ants = list(G.antecedentes(x.frec, x.c.min_ant, x.det))
    A = G.matriz_antecedentes(x.c.T, ants)
    nA = np.array([x.frec[s] for s in ants], float)
    z, val, _ = G.z_y_validez(nA, G.contar(A, np.stack([x.c.y[p] for p in perms], axis=1)), x.c.n, x.c.n_si, x.c.min_conj)
    assert np.allclose(np.where(val, z, 0).max(axis=0), NULA['max_z'].iloc[:100]), 'el primer lote nulo no se reproduce'
    return 'reglas, q y primer lote nulo se reproducen'


def p13(x):
    d2 = copy.copy(x.d)
    d2.M = x.d.M.copy()
    d2.M['severo_mrs'] = np.random.default_rng(3).permutation(x.d.M['severo_mrs'].to_numpy())
    T1 = H.matriz_items(H.esquema(x.d.X[N.PRINCIPAL], x.d.defs, 'principal'), 529)[0]
    T2 = H.matriz_items(H.esquema(d2.X[N.PRINCIPAL], d2.defs, 'principal'), 529)[0]
    assert T1.equals(T2), 'las agrupaciones dependen del consecuente'
    meta = N.leer_json(B / 'reglas/resumen_principal.json')['estabilidad']
    assert (meta['n_submuestra'], meta['umbral_antecedente'], meta['umbral_conjunto']) == (423, 43, 22), 'umbrales de submuestra'
    return 'las agrupaciones no dependen del consecuente; submuestras con umbrales 43 y 22'


def p14(x):
    m = NULA['max_z'].to_numpy()
    assert len(m) == H.N_PERM, 'no son 1.000 permutaciones'
    for r in R_CSV.sample(40, random_state=1).itertuples():
        assert math.isclose(r.p_ajustado_busqueda, (1 + (m >= abs(r.z)).sum()) / (1 + len(m))), 'p ajustado mal calculado'
    y = np.random.default_rng(99).permutation(x.c.y)
    Rp = G.reglas(G.fpgrowth(x.c.T, y, 27, 3), 529, int(y.sum()), 53, 27, x.det)
    marc = NULA['reglas_marcadas']
    assert marc.min() <= Rp['marcada'].sum() <= marc.max(), 'una permutación nueva queda fuera del rango nulo'
    return f'p ajustado verificado; una permutación nueva da {int(Rp["marcada"].sum())} marcadas (nula: media {marc.mean():.0f})'


def p15(x):
    from statsmodels.stats.multitest import multipletests
    assert len(x.R) == len(R_CSV) and np.allclose(multipletests(x.R['p_fisher'], method='fdr_bh')[1], x.R['q_bh_todas']), 'BH incorrecto'
    return f'BH sobre las {len(x.R)} reglas evaluadas'


def p16(x):
    for it in x.R['items']:
        vs = [N.variable_de_item(i) for i in it]
        assert 1 <= len(it) <= 3 and len(vs) == len(set(vs)) and not set(it) & set(N.CONSECUENTES), 'antecedente inválido'
    c = N.construir(x.pq, 'S2a')
    det = H.pares_determinados(c.T)
    assert det, 'S2a debería tener pares determinados'
    R2 = EV.reglas_de(c, EV.descubrir(c), det)
    assert not any((a, b) in det for it in R2['items'] for a in it for b in it if a != b), 'regla con par determinado'
    return f'antecedentes válidos; en S2a se excluyen {len(det)} pares determinados'


def p17(x):
    s = N.huella_sello()
    t = pd.Timestamp(s['sellado']).timestamp()
    for p in list((B / 'reglas').glob('*.csv')) + list((B / 'referencia_nula').rglob('*.npz')):
        assert p.stat().st_mtime > t, f'resultado anterior al sello: {p.name}'
    return 'protocolo y código íntegros; resultados posteriores al sello'


def p18(x):
    R = EV.clasificar(EV.ajustar(x.R, NULA), pd.read_csv(B / 'estabilidad/estabilidad_reglas.csv'))
    assert (R['clase'] == R_CSV['clase']).all(), 'la clasificación no se reproduce'
    s = R[R['clase'].str.startswith('6')]
    assert (s['marcada'] & s['supera_nula'] & s['estable']).all(), 'clase 6 sin todos los criterios'
    fc = EV.mapa_consecuente(x.frec)
    for rr in R[R['largo'] > 1].sample(80, random_state=2).itertuples():
        subs = [s_ for k in range(1, rr.largo) for s_ in combinations(rr.items, k)]
        cs = [(fc[frozenset(s_)][1] if rr.consecuente.endswith('SI') else fc[frozenset(s_)][0] - fc[frozenset(s_)][1]) / fc[frozenset(s_)][0] for s_ in subs]
        assert math.isclose(rr.mejora_sobre_subreglas, rr.confianza - max(cs)) and rr.redundante == (rr.mejora_sobre_subreglas < 0.05), 'redundancia'
    return f'clasificación reproducida; {len(s)} en clase 6; redundancia verificada en 80 reglas'


def p19(x):
    for nom in N.CONFIGS:
        R = R_CSV if nom == 'principal' else pd.read_csv(B / f'sensibilidades/reglas/reglas_{nom}.csv')
        N.B.verificar_reglas(R, N.variable_de_item, N.B.permitidas(nom, x.pq.dec), N.CONSECUENTES)
    return f'{len(N.CONFIGS)} tablas de reglas sin variables no autorizadas'


def p20(x):
    Hn = pd.read_csv(N.D38 / 'referencia_nula/nula_principal.csv')
    assert (NULA['max_z'].to_numpy() <= Hn['max_z'].to_numpy() + 1e-12).all() and (NULA['reglas_marcadas'].to_numpy() <= Hn['reglas_marcadas'].to_numpy()).all(), 'la nula corregida supera a la histórica en alguna permutación'
    return 'en las 1.000 permutaciones la nula corregida es ≤ a la histórica, como exige un subconjunto de reglas'


PRUEBAS = [('529 participantes e identificadores', p01), ('Correspondencia con las fuentes', p02), ('MRS severo correcto', p03), ('29 variables y 90 ítems, sin contenido vetado', p04), ('Sin condiciones contradictorias', p05), ('Categorías agrupadas', p06),
           ('Imputaciones (S1)', p07), ('Módulos y poblaciones (S7)', p08), ('Soporte, confianza, lift, leverage', p09), ('Equivalencia Apriori / FP-Growth / exhaustiva', p10), ('Evaluador matricial', p11), ('Reproducibilidad', p12),
           ('Estabilidad sin fuga', p13), ('Referencia nula', p14), ('Comparaciones múltiples', p15), ('Sin reglas triviales', p16), ('Protocolo sellado antes de resultados', p17), ('Clasificación y redundancia', p18), ('Barreras en todas las tablas', p19), ('Nula coherente con la histórica', p20)]


def correr(x, solo=None):
    out = []
    for i, (nombre, f) in enumerate(PRUEBAS, 1):
        if solo and i not in solo:
            continue
        t = time.time()
        try:
            out.append({'n': i, 'prueba': nombre, 'resultado': 'superada', 'detalle': f(x), 'segundos': round(time.time() - t, 1)})
        except Exception as e:  # noqa: BLE001
            out.append({'n': i, 'prueba': nombre, 'resultado': 'FALLA', 'detalle': f'{type(e).__name__}: {e}'[:300], 'segundos': round(time.time() - t, 1)})
    return pd.DataFrame(out)


def mutaciones():
    M = []

    def con(nombre, aplicar, deshacer, solo):
        aplicar()
        try:
            try:
                r = correr(contexto(), solo)
                fallan = r[r['resultado'] != 'superada']
                M.append({'control_negativo': nombre, 'detectado': len(fallan) > 0, 'pruebas_que_fallan': ', '.join(map(str, fallan['n'])), 'motivo': fallan['detalle'].iloc[0] if len(fallan) else ''})
            except Exception as e:  # noqa: BLE001
                M.append({'control_negativo': nombre, 'detectado': True, 'pruebas_que_fallan': 'construcción', 'motivo': f'{type(e).__name__}: {e}'[:200]})
        finally:
            deshacer()
        print(M[-1]['control_negativo'], M[-1]['detectado'], M[-1]['pruebas_que_fallan'], flush=True)

    o_h = {k: getattr(H, k) for k in ('medidas', 'wilson', 'transacciones', 'bh', 'MEJORA_MIN', 'pares_determinados')}
    o_g = {k: getattr(G, k) for k in ('fpgrowth', 'contar')}
    o_ev = {'clasificar': EV.clasificar}

    def rest():
        for k, v in o_h.items():
            setattr(H, k, v)
        for k, v in o_g.items():
            setattr(G, k, v)
        EV.clasificar = o_ev['clasificar']
        N.construir = ORIG_CONSTRUIR

    def lift_malo(*a, **k):
        R = o_h['medidas'](*a, **k)
        R['lift'] = R['confianza'] / (1 - R['frecuencia_basal'])
        return R
    con('Lift con la basal equivocada', lambda: setattr(H, 'medidas', lift_malo), rest, [9])
    con('Wilson sin corrección', lambda: setattr(H, 'wilson', lambda k, n, z=1.96: (np.asarray(k) / n - 0.01, np.asarray(k) / n + 0.01)), rest, [9])
    con('Dos estados de una variable', lambda: setattr(H, 'transacciones', lambda T, y: [s | {'trabaja=NO', 'trabaja=SI'} for s in o_h['transacciones'](T, y)]), rest, [5])

    def fp_malo(T, y, minsup, max_ant=3):
        f = o_g['fpgrowth'](T, y, minsup, max_ant)
        f.pop(sorted(f, key=lambda s: sorted(s))[100])
        return f
    con('FP-Growth pierde un conjunto', lambda: setattr(G, 'fpgrowth', fp_malo), rest, [10, 11, 12])
    con('Evaluador con recuento desplazado', lambda: setattr(G, 'contar', lambda A, Y, lote=20000: o_g['contar'](A, Y, lote) + 1), rest, [11, 12])

    def bh_sel(p):
        p = np.asarray(p, float)
        q = p.copy()
        s = p < 0.01
        q[s] = o_h['bh'](p[s]) if s.any() else q[s]
        return q
    con('BH solo en las seleccionadas', lambda: setattr(H, 'bh', bh_sel), rest, [12, 15])
    con('Mejora mínima en 0', lambda: setattr(H, 'MEJORA_MIN', 0.0), rest, [12, 18])

    def clas_mala(R, E=None, sp=None):
        R2 = o_ev['clasificar'](R, E, sp)
        R2.loc[R2['clase'].str.startswith('4'), 'clase'] = '6 asociación relativamente más marcada'
        return R2
    con('Compatibles con la nula pasadas a clase 6', lambda: setattr(EV, 'clasificar', clas_mala), rest, [18])
    con('Pares determinados nunca detectados', lambda: setattr(H, 'pares_determinados', lambda T: set()), rest, [16])

    def s1_mala(pq, nombre):
        return ORIG_CONSTRUIR(pq, 'principal' if nombre == 'S1' else nombre)
    con('S1 sin quitar imputados', lambda: setattr(N, 'construir', s1_mala), rest, [7])

    def s7_mala(pq, nombre):
        return ORIG_CONSTRUIR(pq, 'S7a-309' if nombre == 'S7a' else nombre)
    con('S7a con la población de 309', lambda: setattr(N, 'construir', s7_mala), rest, [8])
    return pd.DataFrame(M)


if __name__ == '__main__':
    t0 = time.time()
    r = correr(contexto())
    N.a_csv(r, B / 'pruebas' / 'resultados_pruebas.csv')
    print(r[['n', 'prueba', 'resultado', 'detalle']].to_string(index=False, max_colwidth=100))
    fallo = (r['resultado'] != 'superada').any()
    if '--mutaciones' in sys.argv:
        m = mutaciones()
        N.a_csv(m, B / 'pruebas' / 'control_mutaciones.csv')
        print(f"{int(m['detectado'].sum())} de {len(m)} errores detectados")
        fallo = fallo or not m['detectado'].all()
    N.registrar('pruebas')
    print(f'{(r["resultado"] == "superada").sum()}/{len(r)} superadas en {time.time() - t0:.0f} s')
    sys.exit(int(fallo))
