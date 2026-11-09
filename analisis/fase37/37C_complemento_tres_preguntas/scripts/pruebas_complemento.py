"""
Complemento de la Fase 37C: pruebas críticas. Cada una usa las funciones de H, de modo que los controles negativos puedan introducir errores en memoria y exigir que se detecten.

Uso, desde analisis/: python fase37/37C_complemento_tres_preguntas/scripts/pruebas_complemento.py [--mutaciones]
Escribe pruebas/resultados_pruebas.csv y pruebas/control_mutaciones.csv.
"""
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import nucleo_complemento as C
import numpy as np
import pandas as pd
import repeticiones_complemento as R
from sklearn.metrics import adjusted_rand_score

import subprocess

N, Q, IN = C.N, C.Q, C.IN
B = C.BASE
ORIGEN_HEAD = '745d689'
SUBS = Q.subconjuntos()
CAD = None


def _cad():
    global CAD
    if CAD is None:
        CAD = N.Cadena()
    return CAD


def _git(*a):
    return subprocess.run(['git', *a], cwd=N.RAIZ, capture_output=True, text=True).stdout


H = SimpleNamespace(
    ari=adjusted_rand_score, alinear=N.alinear, alineados=C.alineados, tabla_celdas=C.tabla_celdas, celdas=C.celdas, r2=C.r2_fuera, pares=N.ari_pares_compartidos, pares_fuera=N.ari_pares_fuera, bloques=lambda: C.BLOQUES, trio=lambda: C.TRIO,
    oficial=lambda: pd.read_csv(C.C37 / 'seleccion' / 'artefactos_provisionales' / C.CONFIG / 'etiquetas.csv', dtype={'participante_id': str}).set_index('participante_id'),
    alternativas=lambda: pd.read_csv(B / 'asignaciones' / 'etiquetas_alternativas.csv', dtype={'participante_id': str}),
    lote=lambda r: np.load(B / 'fuera_de_muestra' / 'lotes' / f'r{r:02d}.npz'), subs=lambda: SUBS,
    manifiesto=lambda base, ruta: pd.read_csv(Path(base) / ruta), reproduccion=lambda: N.leer_json(B / 'reproduccion' / 'reproduccion_ari.json'), head=lambda: _git('rev-parse', '--short', 'HEAD').strip(), remotas=lambda: _git('branch', '-r'), estado=lambda: _git('status', '--porcelain', '--untracked-files=all', '--', '.', ':!analisis'),
    leidos=lambda: pd.read_csv(B / 'integridad' / 'archivos_leidos.csv')['archivo_leido'].astype(str).tolist(), fuera=lambda: pd.read_csv(B / 'integridad' / 'escrituras_fuera.csv')['escritura_fuera'].astype(str).tolist(), columnas_obj=lambda: list(C.objetivos(_cad())),
    estabilidad=lambda: pd.read_csv(B / 'estabilidad' / 'estabilidad_alternativas.csv'), decision=lambda: N.leer_json(C.C37 / 'seleccion' / 'decision_final_37C.json'), sens=lambda: pd.read_csv(B / 'complejidad' / 'sensibilidad_B1.csv'),
)
PRUEBAS = []


def prueba(n, nombre):
    def d(f):
        PRUEBAS.append((n, nombre, f))
        return f
    return d


@prueba(1, 'Archivos protegidos: manifiestos de 34-35, 36, 37A, 37B y 37C')
def p1():
    fuentes = [('fase36', N.F36, 'integridad/manifiesto_final_36B.csv', None), ('37A', N.A37, 'integridad/manifiesto_final_37A.csv', None), ('37B', N.B37, 'integridad/manifiesto_final_37B.csv', None), ('cierre', N.RAIZ / 'analisis' / 'cierre_fases_34_35', 'integridad/manifiesto_despues.csv', N.RAIZ), ('37C', C.C37, 'integridad/manifiesto_final_37C.csv', None)]
    total = 0
    for nombre, base, ruta, rel in fuentes:
        m = H.manifiesto(base, ruta)
        for r, h in zip(m['ruta'], m['sha256']):
            assert N.sha(Path(rel or base) / r) == h, f'{nombre}: {r} cambió'
            total += 1
    return f'{total} archivos iguales a sus manifiestos'


@prueba(2, 'Sin carpetas __pycache__ nuevas en fases protegidas')
def p2():
    malas = [p for b in (N.F36, N.A37, N.B37, C.C37) for p in Path(b).rglob('__pycache__')]
    assert not malas, malas[:2]
    return 'ninguna'


@prueba(3, 'Conservación e identificadores: 529 únicos en el mismo orden')
def p3():
    ids = _cad().ids
    a = H.alternativas()
    assert len(ids) == 529 and len(set(ids)) == 529
    assert a['participante_id'].tolist() == ids, 'orden distinto'
    assert H.oficial().index.tolist() == ids, 'orden distinto en A'
    assert all(H.lote(r)['A'].shape[0] == 529 for r in range(30))
    return '529 en etiquetas, A y las 30 repeticiones'


@prueba(4, 'Etiquetas históricas del Modelo A reproducidas exactamente')
def p4():
    o = H.oficial()['grupo'].to_numpy()
    assert (o == N.etiquetas_37b()[C.CONFIG].to_numpy()).all(), 'artefacto distinto de la Fase 37B'
    X = Q.coordenadas(C.ESPACIO, 12).to_numpy()
    assert (Q.ajustar_km(X, 4, Q.SEMILLA)[0] == o).all(), 'K-means no reproduce'
    m = N.leer_json(C.C37 / 'seleccion' / 'artefactos_provisionales' / C.CONFIG / 'modelo_segmentacion.json')
    assert (Q.asignar(np.array(m['centroides']), X)[0] == o).all(), 'centroides no reproducen'
    assert np.bincount(o).tolist() == [150, 76, 132, 171]
    return '150, 76, 132 y 171; K-means y centroides iguales'


@prueba(5, 'Las 30 repeticiones de A coinciden con los lotes E3 de la Fase 37C')
def p5():
    for r in range(30):
        h = np.load(C.C37 / 'estabilidad' / 'lotes' / f'P2_E3_r{r:02d}.npz')[C.CONFIG]
        assert (H.lote(r)['A'] == h).all(), f'r{r}'
    e = H.estabilidad()
    x = e[(e['alternativa'] == 'A') & (e['medida'] == 'entre')]['media'].iloc[0]
    d = N.leer_json(C.C37 / 'seleccion' / 'decision_final_37C.json')['estabilidad_E3']['ari_entre_media']
    assert abs(x - d) < 1e-12, f'{x} frente a {d}'
    return f'30 de 30; E3 entre {x:.3f}'


@prueba(6, 'ARI exploratorio de 0,677: reproducción y procedencia')
def p6():
    x = H.reproduccion()
    assert x['diferencia'] == 0 and x['posicion'] == 1 and x['n_combinaciones'] == 4060, x
    cad = _cad()
    defs, vals = IN.numericos(cad)
    enc = IN.codificar_para_celdas(defs, vals)
    t = C.TRIO
    r = IN.reconstruir(pd.factorize(enc[t[0]] * 10000 + enc[t[1]] * 100 + enc[t[2]])[0], H.oficial()['grupo'].to_numpy(), IN.particiones_cv(Q.N), 4)
    assert abs(r - x['ari_guardado']) < 1e-12, r
    return f'ARI {r:.4f}, igual al guardado'


@prueba(7, 'B1 y B2 usan solo las tres preguntas autorizadas')
def p7():
    cad = _cad()
    assert set(H.trio()) == {'trabaja_actualmente', 'tiene_pareja', 'dias_ejercicio_semana'}
    t = cad.tabla.copy()
    for v in t.columns:
        if v not in C.TRIO:
            t[v] = np.random.default_rng(1).permutation(t[v].to_numpy())
    assert (H.celdas(t) == H.celdas(cad.tabla)).all(), 'las celdas dependen de otra variable'
    for v in C.TRIO:
        s = cad.tabla.copy()
        s[v] = np.random.default_rng(2).permutation(s[v].to_numpy())
        assert (H.celdas(s) != H.celdas(cad.tabla)).any(), f'las celdas ignoran {v}'
    z = cad.congelada(C.ESPACIO)[list(C.TRIO)].to_numpy()
    a = H.alternativas()['B2'].to_numpy()
    assert H.ari(a, C.ajustar_b2(z, np.arange(529), Q.SEMILLA)[0]) == 1.0, 'B2 no se reproduce con las tres columnas'
    return 'celdas y B2 dependen solo del trío'


@prueba(8, 'B2 no usa etiquetas de A: permutarlas no lo cambia, y B1 sí depende de ellas')
def p8():
    d = N.leer_json(B / 'definiciones' / 'definicion_B1_B2.json')
    cad = _cad()
    o = H.oficial()['grupo'].to_numpy()
    cod = H.celdas(cad.tabla)
    m0 = H.tabla_celdas(cod, o)[0]
    assert m0.tolist() == d['B1']['mapa'], 'B1 no se reproduce'
    m1 = H.tabla_celdas(cod, np.random.default_rng(3).permutation(o))[0]
    assert (m0 != m1).any(), 'B1 no depende de las etiquetas'
    import inspect
    assert 'oficial' not in inspect.signature(C.ajustar_b2).parameters
    return 'B1 usa A por definición; B2 no recibe etiquetas'


@prueba(9, 'Sin fuga: alterar las participantes de evaluación no cambia nada ajustado')
def p9():
    cad = _cad()
    idx = H.subs()[0]
    resto = np.setdiff1d(np.arange(529), idx)
    t = cad.tabla_imputada(idx)[0]
    t2 = t.copy()
    nombres = t.index[resto]
    t2.loc[nombres, 'tiene_pareja'] = 'NO'
    t2.loc[nombres, 'trabaja_actualmente'] = 'False'
    t2.loc[nombres, 'dias_ejercicio_semana'] = '5'
    z1 = cad.calibrada(C.ESPACIO, t, idx).to_numpy()
    z2 = cad.calibrada(C.ESPACIO, t2, idx).to_numpy()
    assert np.allclose(z1[idx], z2[idx]), 'escalado contaminado'
    F1 = N.coordenadas_cadena(z1, idx)[0][:, :12]
    F2 = N.coordenadas_cadena(z2, idx)[0][:, :12]
    l1, l2 = Q.ajustar_km(F1[idx], 4, 7)[0], Q.ajustar_km(F2[idx], 4, 7)[0]
    assert (l1 == l2).all(), 'A contaminado'
    assert (H.tabla_celdas(H.celdas(t)[idx], l1)[0] == H.tabla_celdas(H.celdas(t2)[idx], l2)[0]).all(), 'B1 contaminada'
    return 'A, escalado y B1 iguales'


@prueba(10, 'Separación entre entrenamiento y evaluación')
def p10():
    for r, idx in enumerate(H.subs()):
        assert len(idx) == 423 and len(set(idx)) == 423
        l = H.lote(r)
        m = N.leer_json(B / 'fuera_de_muestra' / 'lotes' / f'r{r:02d}.json')
        rec = H.tabla_celdas(l['celdas'][idx].astype(int), l['A'][idx].astype(int))[0]
        assert rec.tolist() == m['mapa_b1'], f'r{r}: el mapa no sale solo del entrenamiento'
    return '423 y 106; los 30 mapas salen solo del entrenamiento'


@prueba(11, 'Reproducibilidad: rehacer la repetición 0 da lo mismo')
def p11():
    R.iniciar()
    sello = C.huella()
    with tempfile.TemporaryDirectory() as d:
        x = R.trabajo((0, H.subs()[0], sello, d))
        assert x[1] == 'completa', x[1]
        a, b = np.load(Path(d) / 'fuera_de_muestra' / 'lotes' / 'r00.npz'), H.lote(0)
        for k in b.files:
            assert np.array_equal(a[k], b[k]), k
        i1, i2 = pd.read_csv(Path(d) / 'fuera_de_muestra' / 'lotes' / 'r00_info.csv'), pd.read_csv(B / 'fuera_de_muestra' / 'lotes' / 'r00_info.csv')
        assert np.allclose(i1['r2_fuera'], i2['r2_fuera'], equal_nan=True)
        del a
    return 'etiquetas e información idénticas'


@prueba(12, 'Alineación correcta y calculada en el entrenamiento')
def p12():
    b = np.array([0, 0, 1, 1, 2, 2, 3, 3])
    o = np.array([3, 3, 2, 2, 0, 0, 1, 1])
    assert (H.alinear(b, o) == b).all(), 'no alinea una permutación'
    tr = np.arange(6)
    otra = np.array([3, 3, 2, 2, 0, 0, 0, 0])
    res = H.alineados(b[tr], otra[tr], otra)
    assert res.tolist() == [0, 0, 1, 1, 2, 2, 2, 2], res
    return 'permutación conocida recuperada; evaluación no influye'


@prueba(13, 'ARI correcto: frente a la fórmula y sin depender de los nombres; no es un porcentaje')
def p13():
    a = H.oficial()['grupo'].to_numpy()
    b = H.alternativas()['B1_cv'].to_numpy()
    tab = pd.crosstab(a, b).to_numpy()
    s = lambda x: (x * (x - 1) / 2).sum()  # noqa: E731
    e = s(tab.sum(axis=1)) * s(tab.sum(axis=0)) / (529 * 528 / 2)
    f = (s(tab) - e) / ((s(tab.sum(axis=1)) + s(tab.sum(axis=0))) / 2 - e)
    assert abs(H.ari(a, b) - f) < 1e-12, 'fórmula distinta'
    assert abs(H.ari(a, (b + 1) % 4) - f) < 1e-12, 'depende de los nombres'
    assert abs(100 * (a == b).mean() - 100 * f) > 5, 'coincide con un porcentaje'
    return f'ARI {f:.3f} y coincidencia {100 * (a == b).mean():.1f} %'


@prueba(14, 'Estabilidad con participantes compartidas')
def p14():
    t = np.array([[0, 0, 1, 1, 9, 9], [0, 0, 1, 1, 5, 7]])
    u = np.array([[True, True, True, True, False, False], [True, True, True, True, False, False]])
    assert H.pares(t, u)[0] == 1.0, 'usa participantes no compartidas'
    t2 = np.array([[0, 1, 0, 1, 0, 0, 1, 1], [0, 1, 0, 1, 0, 1, 0, 1]])
    u2 = np.array([[False] * 5 + [True] * 3, [False] * 5 + [True] * 3])
    assert H.pares_fuera(t2, u2)[0] == 1.0, 'usa participantes ya usadas'
    return 'ambas máscaras correctas'


@prueba(15, 'R² fuera de muestra: medias del entrenamiento y controles positivo y negativo')
def p15():
    rng = np.random.default_rng(5)
    l = rng.integers(0, 4, 500)
    D = C.indicadores(l)
    y = (l.astype(float) + rng.normal(0, 0.5, 500)).reshape(-1, 1)
    idx, resto = np.arange(400), np.arange(400, 500)
    marca = np.ones(500, bool)
    medias = np.array([y[idx][l[idx] == g].mean() for g in range(4)])
    a_mano = 1 - ((y[resto, 0] - medias[l[resto]]) ** 2).sum() / ((y[resto, 0] - y[idx].mean()) ** 2).sum()
    assert abs(H.r2(D, y, marca, idx, resto) - a_mano) < 1e-8, 'no equivale a medias por segmento'
    assert H.r2(D, y, marca, idx, resto) > 0.7, 'no detecta información'
    z = rng.normal(size=(500, 1))
    assert H.r2(D, z, marca, idx, resto) < 0.05, 've información en el ruido'
    m = marca.copy()
    m[resto[:50]] = False
    assert H.r2(D, y, m, idx, resto) != H.r2(D, y, marca, idx, resto), 'ignora la máscara de observadas'
    return 'equivale a medias; detecta señal y no ruido'


@prueba(16, 'ΔR² puede detectar información adicional cuando existe')
def p16():
    rng = np.random.default_rng(6)
    celda = rng.integers(0, 20, 529)
    otro = rng.integers(0, 4, 529)
    y = (otro.astype(float) + rng.normal(0, 0.8, 529)).reshape(-1, 1)
    marca = np.ones(529, bool)
    deltas = []
    for idx in H.subs():
        resto = np.setdiff1d(np.arange(529), idx)
        Dc, Da = C.indicadores(celda), C.indicadores(otro)
        deltas.append(H.r2(np.hstack([Dc, Da]), y, marca, idx, resto) - H.r2(Dc, y, marca, idx, resto))
    assert np.mean(deltas) > 0.06, np.mean(deltas)
    return f'información inyectada detectada: ΔR² {np.mean(deltas):.2f}'


@prueba(17, 'Los bloques reparten las 29 variables de P2 sin solapamiento')
def p17():
    defs = {d['variable'] for d in N.leer_json(N.F36 / 'artefactos' / C.ESPACIO / 'esquema_variables.json')['variables']}
    todas = [v for b in H.bloques().values() for v in b]
    assert len(todas) == len(set(todas)), 'solapamiento'
    assert set(todas) == defs and len(defs) == 29, set(todas) ^ defs
    return '29 variables en 9 bloques'


@prueba(18, 'Búsqueda anidada exhaustiva y solo con entrenamiento')
def p18():
    R.iniciar()
    idx = H.subs()[3]
    tabla = R.CAD.tabla_imputada(idx)[0]
    enc = R.codificar_en_entrenamiento(tabla, idx)
    assert len(enc) == 30, len(enc)
    v = ['edad', 'frutas_dia', 'tabaco_frecuencia']
    plantado = pd.factorize(enc[v[0]] * 10000 + enc[v[1]] * 100 + enc[v[2]])[0]
    l = (plantado[idx] % 4).astype(int)
    trio, s, pred = R.busqueda_anidada(tabla, idx, l, 3)
    assert set(trio) == set(v), f'no encontró el trío plantado: {trio}'
    assert s > 0.6, s
    t2 = tabla.copy()
    resto = np.setdiff1d(np.arange(529), idx)
    t2.loc[t2.index[resto], 'tabaco_frecuencia'] = '1'
    assert set(R.busqueda_anidada(t2, idx, l, 3)[0]) == set(v), 'el resultado cambió con la evaluación'
    n = pd.read_csv(B / 'fuera_de_muestra' / 'trios_busqueda_anidada.csv')
    assert n['repeticiones'].sum() == 30
    return f"trío plantado recuperado; el trío evaluado salió en {int(n[n['trio'] == ' + '.join(C.TRIO)]['repeticiones'].sum())} de 30"


@prueba(19, 'Sin MRS ni datos de origen: ni en lecturas ni en variables')
def p19():
    pal = ('mrs', 'severo', 'severidad', 'sintoma_', 'verdad', 'bitacora')
    malas = [x for x in H.leidos() if x.startswith('datos/') or any(t in x.lower() for t in pal)]
    assert not malas, malas[:3]
    malas = [c for c in H.columnas_obj() if any(t in c.lower() for t in pal)]
    assert not malas, malas
    for p in list(B.rglob('*.csv')) + list(B.rglob('*.json')):
        if p.name in ('archivos_leidos.csv', 'registro_ejecucion.csv', 'resultados_pruebas.csv', 'control_mutaciones.csv', 'manifiesto_final.csv', 'registro_memoria.csv', 'verificacion_informes.csv'):
            continue
        if p.suffix == '.csv':
            cab = p.read_text(encoding='utf-8').split('\n', 1)[0].lower()
            assert not any(t in cab for t in pal[:4]), f'{p.name}: {cab[:80]}'
    return f'{len(H.leidos())} archivos leídos, ninguno prohibido'


@prueba(20, 'Sensibilidades de A leídas de la Fase 37C sin recalcular')
def p20():
    h = pd.read_csv(C.C37 / 'sensibilidades' / 'sensibilidades_priorizadas.csv')
    h = h[h['config'] == C.CONFIG].set_index('sensibilidad')['ari_ajuste']
    s = H.sens().set_index('sensibilidad')['ari_A_sellado']
    for k, v in s.items():
        assert abs(h[k] - v) < 1e-12, k
    return f'{len(s)} valores iguales'


@prueba(21, 'La conclusión B de la Fase 37C sigue intacta')
def p21():
    d = H.decision()
    assert d['conclusion'].startswith('B.') and d['configuracion_propuesta'] == C.CONFIG, d['conclusion']
    return d['conclusion']


@prueba(22, 'Imputación: la moda de 529 solo cambia actividad sexual; las celdas no cambian')
def p22():
    cad = _cad()
    t, _ = cad.tabla_imputada()
    dif = (t.astype(str) != cad.tabla.astype(str)).sum()
    dif = dif[dif > 0]
    assert list(dif.index) == ['tiene_actividad_sexual'] and int(dif.iloc[0]) == 30, dif.to_dict()
    assert (H.celdas(t) == H.celdas(cad.tabla)).all()
    return '30 celdas de esa variable; sin efecto en las tres preguntas'


@prueba(23, 'Git y alcance: sin commit, sin push, sin Django, sin escrituras fuera y sin Fase 37D')
def p23():
    assert H.head() == ORIGEN_HEAD, H.head()
    assert 'datos-simulados' not in H.remotas(), 'rama en el remoto'
    assert not H.estado().strip(), 'cambios fuera de analisis'
    assert not H.fuera(), H.fuera()[:2]
    assert not [p for p in (B.parent).iterdir() if p.name.startswith('37D')], 'Fase 37D iniciada'
    return f'HEAD {ORIGEN_HEAD}; sin cambios fuera de analisis/'


def ejecutar():
    filas = []
    for n, nombre, f in PRUEBAS:
        try:
            filas.append({'numero': n, 'prueba': nombre, 'resultado': 'superada', 'detalle': f()})
        except Exception as ex:  # noqa: BLE001
            filas.append({'numero': n, 'prueba': nombre, 'resultado': 'FALLA', 'detalle': f'{type(ex).__name__}: {ex}'[:300]})
    return pd.DataFrame(filas)


# ---- controles negativos
def _ari_coincidencia(a, b):
    return float((np.asarray(a) == np.asarray(b)).mean())


def _pares_todas(t, u):
    return [adjusted_rand_score(t[i], t[j]) for i in range(len(t)) for j in range(i + 1, len(t))]


def _fuera_todas(t, u):
    return [adjusted_rand_score(t[i], t[j]) for i in range(len(t)) for j in range(i + 1, len(t))]


def _celdas_con_otra(t):
    return C.celdas(t) + 100 * pd.factorize(t['frutas_dia'])[0]


def _celdas_sin_pareja(t):
    x = t.copy()
    x['tiene_pareja'] = 'NO'
    return C.celdas(x)


def _r2_con_evaluacion(D, Y, marca, idx, resto):
    todas = np.concatenate([idx, resto])
    return C.r2_fuera(D, Y, marca, todas, resto)


def _r2_sin_marca(D, Y, marca, idx, resto):
    return C.r2_fuera(D, Y, np.ones_like(marca), idx, resto)


def _alinear_nada(b, o, k=None):
    return np.asarray(o)


def _alineados_todo(base, otra_tr, otra):
    return np.asarray(otra)


def _tabla_minoria(cod, l, k=4, m=20):
    mapa, p, c = C.tabla_celdas(cod, l, k, m)
    return np.array([int(np.argmin(c[i])) for i in range(m)]), p, c


MUTACIONES = [
    ('Un archivo protegido cambia', 'manifiesto', lambda b, r: H_ORIG.manifiesto(b, r).assign(sha256=lambda d: ['0' * 64] + d['sha256'].tolist()[1:]), 1),
    ('Etiquetas desordenadas', 'alternativas', lambda: H_ORIG.alternativas().iloc[::-1], 3),
    ('Etiquetas oficiales alteradas', 'oficial', lambda: H_ORIG.oficial().assign(grupo=lambda d: (d['grupo'] + 1) % 4), 4),
    ('Lote de A cambiado', 'lote', lambda r: {**dict(H_ORIG.lote(r)), 'A': (H_ORIG.lote(r)['A'] + 1) % 4}, 5),
    ('El 0,677 no se reproduce', 'reproduccion', lambda: {**H_ORIG.reproduccion(), 'diferencia': 0.02}, 6),
    ('Otra variable entra en las celdas', 'celdas', _celdas_con_otra, 7),
    ('Una pregunta se ignora', 'celdas', _celdas_sin_pareja, 7),
    ('Variable no autorizada en el trío', 'trio', lambda: ('trabaja_actualmente', 'tiene_pareja', 'frutas_dia'), 7),
    ('B1 elige la minoría', 'tabla_celdas', _tabla_minoria, 8),
    ('Coincidencia en vez de ARI', 'ari', _ari_coincidencia, 13),
    ('Sin alinear', 'alinear', _alinear_nada, 12),
    ('Alineación ignorada', 'alineados', _alineados_todo, 12),
    ('Estabilidad con todas las filas', 'pares', _pares_todas, 14),
    ('Fuera de muestra con filas usadas', 'pares_fuera', _fuera_todas, 14),
    ('R² ajustado también con evaluación', 'r2', _r2_con_evaluacion, 15),
    ('R² con celdas imputadas', 'r2', _r2_sin_marca, 15),
    ('Bloques con solapamiento', 'bloques', lambda: {**C.BLOQUES, 'Extra': ['edad']}, 17),
    ('Lectura de datos de origen', 'leidos', lambda: H_ORIG.leidos() + ['datos/original.csv'], 19),
    ('Lectura de MRS', 'columnas_obj', lambda: H_ORIG.columnas_obj() + ['mrs_total'], 19),
    ('Sensibilidad de A recalculada', 'sens', lambda: H_ORIG.sens().assign(ari_A_sellado=lambda d: d['ari_A_sellado'] + 0.01), 20),
    ('La conclusión de 37C cambia', 'decision', lambda: {**H_ORIG.decision(), 'conclusion': 'A. Modelo respaldado'}, 21),
    ('HEAD cambia (commit)', 'head', lambda: 'abc1234', 23),
    ('Rama publicada (push)', 'remotas', lambda: 'origin/datos-simulados', 23),
    ('Cambio en Django', 'estado', lambda: ' M src/apps/encuestas/models.py', 23),
    ('Escritura fuera de la carpeta', 'fuera', lambda: ['C:/otra/ruta.csv'], 23),
]
H_ORIG = SimpleNamespace(**vars(H))


def mutaciones():
    por_n = {n: (nombre, f) for n, nombre, f in PRUEBAS}
    filas = []
    for nombre, attr, mut, n in MUTACIONES:
        setattr(H, attr, mut)
        try:
            por_n[n][1]()
            filas.append({'mutacion': nombre, 'prueba': n, 'detectada': False, 'detalle': 'La prueba no falló'})
        except Exception as ex:  # noqa: BLE001
            filas.append({'mutacion': nombre, 'prueba': n, 'detectada': True, 'detalle': f'{type(ex).__name__}: {ex}'[:160]})
        finally:
            setattr(H, attr, getattr(H_ORIG, attr))
    return pd.DataFrame(filas)


def main():
    C.huella()
    t = ejecutar()
    N.a_csv(t, B / 'pruebas' / 'resultados_pruebas.csv')
    print(t[['numero', 'resultado', 'detalle']].to_string())
    ok = (t['resultado'] == 'superada').all()
    if '--mutaciones' in sys.argv:
        m = mutaciones()
        N.a_csv(m, B / 'pruebas' / 'control_mutaciones.csv')
        print(m[['mutacion', 'prueba', 'detectada']].to_string())
        ok = ok and m['detectada'].all()
    print('Superadas', int((t['resultado'] == 'superada').sum()), 'de', len(t))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
