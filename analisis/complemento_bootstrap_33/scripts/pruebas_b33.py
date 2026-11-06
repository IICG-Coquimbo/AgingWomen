"""Pruebas del complemento (sección 12 de la instrucción) y controles negativos.

Uso, desde scripts/, después de ejecutar y resumir:  python pruebas_b33.py
Cada control es una función pura que recibe los datos; la prueba la aplica a los datos reales (debe pasar) y cada
control negativo la aplica a una copia alterada (debe fallar). No escribe fuera de pruebas/.
"""
import copy
import hashlib
import json
import sys
import traceback
from dataclasses import replace

import numpy as np
import pandas as pd

import integridad_b33 as I
import nucleo_b33 as N

B = N.BASE
SAL = B / 'pruebas'
ANT = N.ANALISIS / 'resultados' / 'usuaria'
REAL = {}


# --- controles puros ---------------------------------------------------------------------------------------------

def control_candidatas(variables):
    variables = sorted(variables)
    elegibles = pd.read_csv(N.V33.CARPETA / 'fase35a' / 'predictores_elegibles_33.csv', encoding='utf-8-sig')['variable'].tolist()
    assert len(variables) == 33, f'{len(variables)} candidatas'
    assert variables == sorted(elegibles) == N.VARIABLES_33, 'no son las 33 elegibles documentadas'
    assert 'doble_carga' not in variables and 'prevision' not in variables and 'usa_medicamentos_diabetes' not in variables
    assert not set(variables) & set(N.C.PROHIBIDAS), 'variable prohibida (MRS, resultado o auditoría)'


def control_poblaciones(esc):
    N.comprobar(esc)


def control_conteo(rutas):
    nombres = sorted(p.name for p in rutas)
    assert nombres == [f'rem_{i:04d}.json' for i in range(500)], f'{len(nombres)} archivos de remuestreo'


def control_indices(idx, objetivo):
    idx = np.asarray(idx)
    assert len(idx) == 529 and idx.min() >= 0 and idx.max() <= 528 and np.issubdtype(idx.dtype, np.integer), 'índices fuera del conjunto'
    # indices_bootstrap concatena las clases en orden: 248 no severas y luego 281 severas
    assert (objetivo[idx[:248]] == 0).all() and (objetivo[idx[248:]] == 1).all(), 'no respeta la estratificación'
    assert int(objetivo[idx].sum()) == 281, 'no mantiene 281 severas'
    assert len(np.unique(idx)) < 529, 'sin repetidas: no es con reemplazo'


def control_registro(r):
    vs = N.VARIABLES_33
    assert sorted(r['p']) == sorted(r['q']) == sorted(r['su']) == vs, 'relevancia incompleta'
    for var in N.VARIANTES:
        assert sorted(r[var]) == vs, f'decisiones incompletas en {var}'
        for v, d in r[var].items():
            assert d[0] in ('seleccionada', 'redundante', 'no relevante')
            assert (d[0] == 'no relevante') == (v not in r['relevantes']), f'{v}: decisión incoherente con la relevancia'
            assert d[1] != N.SOBRECARGA, 'la sobrecarga eliminó a otra variable'
            if v not in N.C.LABORALES_35B and v != N.SOBRECARGA:
                assert d[1] not in N.C.LABORALES_35B, 'una laboral eliminó a una general'
    q = N.E.benjamini_hochberg([r['p'][v] for v in vs])
    assert np.allclose(q, [r['q'][v] for v in vs], rtol=0, atol=1e-15), 'q no es BH de las 33'
    assert r['relevantes'] == [v for v in vs if r['q'][v] < N.ALFA], 'relevancia no usa q < 0,10'
    k = len(r['relevantes'])
    assert r['n_pares'] == k * (k - 1) // 2, 'no se evaluaron todos los pares de relevantes'
    assert r['n']['lugar_trabajo_comprensivo'] == r['n_laboral'] and r['n'][N.SOBRECARGA] == r['n_cuidadoras'], 'población mal aplicada'
    assert r['n']['edad'] == 529 and r['n_severas'] == 281


def control_parametros(ej, conf):
    assert ej['remuestreos'] == 500 and ej['permutaciones'] == 5000 and ej['alfa'] == 0.10 and ej['id_analisis'] == 1 and ej['procesos'] == 1
    assert conf['n_permutaciones_por_remuestreo'] == 5000 and conf['alfa_q'] == 0.10 and conf['familia_bh'] == 33


def frecuencias_independientes(registros):
    filas = []
    for var in N.VARIANTES:
        for v in N.VARIABLES_33:
            c = {'seleccionada': 0, 'redundante': 0, 'no relevante': 0}
            for r in registros:
                c[r[var][v][0]] += 1
            filas.append({'variante': var, 'variable': v, 'veces_seleccionada': c['seleccionada'],
                          'pct_seleccionada': 100 * c['seleccionada'] / len(registros),
                          'pct_redundante': 100 * c['redundante'] / len(registros), 'pct_no_relevante': 100 * c['no relevante'] / len(registros),
                          'pct_relevante_su': 100 * sum(v in r['relevantes'] for r in registros) / len(registros)})
    return pd.DataFrame(filas)


def control_frecuencias(tabla, registros):
    ind = frecuencias_independientes(registros).set_index(['variante', 'variable'])
    t = tabla.set_index(['variante', 'variable']).loc[ind.index]
    for c in ind.columns:
        assert np.allclose(t[c].to_numpy(float), ind[c].to_numpy(float), rtol=0, atol=1e-9), f'{c} mal calculada'


def control_rangos(tabla):
    for c in ('pct_seleccionada', 'pct_redundante', 'pct_no_relevante', 'pct_relevante_su'):
        assert tabla[c].between(0, 100).all(), f'{c} fuera de 0-100'
    assert np.allclose(tabla[['pct_seleccionada', 'pct_redundante', 'pct_no_relevante']].sum(axis=1), 100), 'los estados no suman 100'
    assert (tabla.pct_seleccionada <= tabla.pct_relevante_su + 1e-9).all(), 'seleccionada más veces que relevante'


def control_completitud(tabla):
    for var in N.VARIANTES:
        assert sorted(tabla[tabla.variante == var].variable) == N.VARIABLES_33, f'faltan variables en {var}'


def control_manifiesto(antes, ahora, prefijo=''):
    dif = [k for k in antes if k.startswith(prefijo) and ahora.get(k) != antes[k]]
    nuevos = [k for k in ahora if k.startswith(prefijo) and k not in antes]
    assert not dif and not nuevos, f'cambiados {dif[:3]}, nuevos {nuevos[:3]}'


def control_igual(a, b, nombre):
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True), f'{nombre}: difiere'


# --- pruebas ---------------------------------------------------------------------------------------------------

PRUEBAS = []


def prueba(n, nombre):
    def deco(f):
        PRUEBAS.append((n, nombre, f))
        return f
    return deco


def cache():
    if 'reg' not in REAL:
        REAL['rutas'] = sorted(N.CACHE.glob('rem_*.json'))
        REAL['reg'] = [json.loads(p.read_text(encoding='utf-8')) for p in REAL['rutas']]
    return REAL['reg']


@prueba(1, 'Exactamente las 33 candidatas documentadas')
def p01():
    control_candidatas(REAL['esc'].indice())
    return '33 = predictores_elegibles_33.csv = VARIABLES_33'


@prueba(2, 'doble_carga no es candidata')
def p02():
    assert 'doble_carga' not in REAL['esc'].datos() and all('doble_carga' not in r['adaptado'] for r in cache())
    return 'ausente del escenario y de los 500 resultados'


@prueba(3, 'prevision no ingresa a la selección')
def p03():
    assert 'prevision' not in REAL['esc'].datos() and all('prevision' not in r['p'] for r in cache())
    return 'ausente del escenario y de los 500 resultados'


@prueba(4, 'Población analítica correcta (529; 281/248; 287 laborales; 239 cuidadoras) y datos idénticos al conjunto de 33')
def p04():
    control_poblaciones(REAL['esc'])
    a = pd.read_csv(N.P.ENTRADA, encoding='utf-8-sig', dtype=str, keep_default_na=False)
    b = pd.read_csv(N.V33.DATASET_33, encoding='utf-8-sig', dtype=str, keep_default_na=False)
    comunes = [c for c in a.columns if c != 'usa_medicamentos_diabetes']
    assert list(b.columns) == comunes and a[comunes].equals(b), 'dataset_fase35_33_variables difiere'
    return 'tamaños correctos; dataset de 33 igual texto a texto sin la diabetes'


@prueba(5, 'Exactamente 500 remuestreos')
def p05():
    control_conteo(REAL['rutas'])
    return '500 archivos, rem_0000 a rem_0499'


@prueba(6, 'Índices dentro del conjunto original y guardados con su huella')
def p06():
    y = REAL['esc'].base.objetivo
    for r in cache():
        idx = N.indices(REAL['esc'], r['remuestreo'])
        control_indices(idx, y)
        assert hashlib.sha256(np.asarray(idx, dtype=np.int64).tobytes()).hexdigest() == r['indices_sha256']
        assert len(np.unique(idx)) == r['n_unicas']
    return '500 vectores en 0-528; huellas iguales'


@prueba(7, 'Mecanismo: bootstrap estratificado con reemplazo, mismas muestras que la corrida antigua')
def p07():
    ra = pd.read_csv(ANT / 'estabilidad_remuestreos.csv', encoding='utf-8-sig', keep_default_na=False)
    ra = ra[ra.variante == 'adaptado'].set_index('remuestreo')['n_laboral']
    distintos = [r['remuestreo'] for r in cache() if r['n_laboral'] != int(ra.loc[r['remuestreo']])]
    assert not distintos, f'n laboral distinto de la corrida antigua en {distintos[:5]}'
    u = [r['n_unicas'] for r in cache()]
    return f'281/248 en cada muestra; personas distintas {min(u)}-{max(u)} (media {np.mean(u):.0f}); n laboral igual a la antigua en 500/500'


@prueba(8, 'Sin filtraciones del MRS: solo severo_mrs como objetivo, como en la definitiva')
def p08():
    esc = REAL['esc']
    assert not set(esc.datos()) & set(N.C.PROHIBIDAS)
    t = pd.read_csv(N.P.ENTRADA, encoding='utf-8-sig')
    assert (esc.base.objetivo == N.E.codificar(t['severo_mrs'])).all()
    for v, x in esc.datos().items():
        m = esc.mascara_de(v)
        assert not np.array_equal(np.asarray(x)[m], esc.base.objetivo[m]), f'{v} es copia del objetivo'
    return 'ninguna candidata es ítem, puntaje o categoría del MRS; objetivo = severo_mrs'


@prueba(9, 'Cada remuestreo aplica el procedimiento completo; tres se recalculan desde cero')
def p09():
    for r in cache():
        control_registro(r)
    for i in (0, 250, 499):
        control_igual(N.un_remuestreo(REAL['esc'], i, N.N_PERMUTACIONES, None), cache()[i], f'remuestreo {i}')
    return '500 registros coherentes; 0, 250 y 499 recalculados iguales'


@prueba(10, 'Parámetros constantes y umbral restaurado')
def p10():
    ej = json.loads((B / 'remuestreos' / 'ejecucion.json').read_text(encoding='utf-8'))
    conf = json.loads((B / 'configuracion' / 'configuracion.json').read_text(encoding='utf-8'))
    control_parametros(ej, conf)
    assert N.C.ALFA_Q_35B == 0.05, 'el umbral global no se restauró'
    assert len({tuple(sorted(r)) for r in cache()}) == 1
    return '500 / 5.000 / q < 0,10 / id 1 / 1 proceso; umbral global 0,05 restaurado'


@prueba(11, 'Frecuencias recalculadas de forma independiente')
def p11():
    control_frecuencias(REAL['frec'], cache())
    return 'cinco columnas iguales al recuento directo'


@prueba(12, 'Ninguna frecuencia supera 100 %')
def p12():
    control_rangos(REAL['frec'])
    return 'todas en 0-100; estados suman 100'


@prueba(13, 'Las nunca seleccionadas aparecen con 0 %')
def p13():
    control_completitud(REAL['frec'])
    ceros = REAL['frec'][(REAL['frec'].variante == 'adaptado') & (REAL['frec'].veces_seleccionada == 0)].variable.tolist()
    return f'33 por variante; con 0 % en adaptado: {len(ceros)}'


@prueba(14, 'Reproducibilidad y fidelidad con la función original')
def p14():
    esc = REAL['esc']
    a = N.un_remuestreo(esc, 7, N.N_PERMUTACIONES, None)
    b = N.un_remuestreo(esc, 7, N.N_PERMUTACIONES, None)
    control_igual(a, b, 'dos corridas del remuestreo 7')
    with N.K.umbral(N.ALFA):
        mia = N.medir_remuestreo(esc, 0, N.N_PERMUTACIONES)
        orig = N.M.medir(esc, N.N_PERMUTACIONES)
    for campo in ('su_objetivo', 'p_objetivo', 'q_objetivo', 'relevantes', 'su_par', 'p_par', 'q_par', 'su_objetivo_laboral',
                  'su_otra_etapa3', 'su_sobrecarga_etapa3'):
        assert getattr(mia, campo) == getattr(orig, campo), f'medir_remuestreo difiere de complementario_cuidados.medir en {campo}'
    return 'mismo resultado dos veces; medir_remuestreo(i = 0) = complementario_cuidados.medir'


@prueba(15, 'Comparación con la corrida antigua bien identificada; el código reproduce un remuestreo antiguo')
def p15():
    fa = pd.read_csv(ANT / 'estabilidad_fcbf.csv', encoding='utf-8-sig')
    assert sorted(fa[fa.variante == 'adaptado'].variable) == sorted(fa[fa.variante == 'estandar'].variable) and fa.variable.nunique() == 30
    assert 'doble_carga' in set(fa.variable)
    ca = pd.read_csv(B / 'comparacion' / 'comparacion_corrida_antigua_por_variable.csv')
    assert ca.en_antigua.sum() == 30 and ca.en_33.sum() == 33 and ca.comparable_solo_descriptivamente.sum() == 29
    datos, _ = N.P.cargar()
    pr = N.P.escenario_principal(datos)
    viejo = N.F.Escenario('Estabilidad', N.P.ID_ESTABILIDAD, pr.datos, pr.objetivo, pr.candidatas, pr.laborales, pr.mascara)
    ra = pd.read_csv(ANT / 'estabilidad_remuestreos.csv', encoding='utf-8-sig', keep_default_na=False).set_index(['variante', 'remuestreo'])
    for i in (0, 1):
        r = N.F.un_remuestreo(viejo, i, 5000)
        for var in N.VARIANTES:
            s = ';'.join(v for v in sorted(viejo.candidatas) if r[var][v][0] == 'seleccionada')
            assert s == ra.loc[(var, i), 'seleccionadas'], f'remuestreo antiguo {i} {var} no se reproduce'
    return '30 antiguas con doble_carga, 29 comunes; remuestreos antiguos 0 y 1 reproducidos exactamente'


@prueba(16, 'Ningún archivo de las Fases 34 a 39 (ni del resto de analisis/ y datos/) cambió')
def p16():
    antes = json.loads((B / 'integridad' / 'manifiesto_antes.json').read_text(encoding='utf-8'))['archivos']
    REAL['ahora'] = I.manifiesto()
    control_manifiesto(antes, REAL['ahora'], 'analisis/')
    control_manifiesto(antes, REAL['ahora'], 'datos/')
    return f'{sum(k.startswith(("analisis/", "datos/")) for k in antes)} archivos con la misma huella'


@prueba(17, 'Django intacto')
def p17():
    antes = json.loads((B / 'integridad' / 'manifiesto_antes.json').read_text(encoding='utf-8'))['archivos']
    control_manifiesto(antes, REAL['ahora'], 'src/')
    assert I.git('status', '--porcelain', '--', 'src').strip() == ''
    return f'{sum(k.startswith("src/") for k in antes)} archivos de src/ iguales; git sin cambios en src/'


@prueba(18, 'Resultados antiguos no sobrescritos')
def p18():
    antes = json.loads((B / 'integridad' / 'manifiesto_antes.json').read_text(encoding='utf-8'))['archivos']
    viejos = ['analisis/resultados/usuaria/' + n for n in ('estabilidad_remuestreos.csv', 'estabilidad_fcbf.csv', 'estabilidad_global.csv', 'log_seleccion_fase35b.txt')]
    viejos += ['analisis/figuras/seleccion_35b/estabilidad_seleccion.png', 'analisis/reunion_2026-11-03/revision_33_variables/log_revision_33.txt']
    for k in viejos:
        assert I.sha(N.ANALISIS.parent / k) == antes[k], k
    return f'{len(viejos)} archivos históricos con la misma huella'


@prueba(19, 'La selección definitiva leída coincide con el registro del 03-11')
def p19():
    log = (N.V33.CARPETA / 'log_revision_33.txt').read_text(encoding='utf-8')
    d = N.seleccion_definitiva()
    for n in (10000, 50000):
        t = d[n]['decisiones']
        for var in N.VARIANTES:
            s = ';'.join(sorted(t[(t.variante == var) & (t.decision == 'seleccionada')].variable))
            assert f'{n}: {"adaptado" if var == "adaptado" else "estandar"} = {s}' in log, f'{n} {var}'
    return 'adaptado y estándar, 10.000 y 50.000, iguales al log'


# --- controles negativos -----------------------------------------------------------------------------------------

def mutaciones():
    esc, reg, frec = REAL['esc'], cache(), REAL['frec']
    y = esc.base.objetivo
    idx = N.indices(esc, 3)
    antes = json.loads((B / 'integridad' / 'manifiesto_antes.json').read_text(encoding='utf-8'))['archivos']
    ej = json.loads((B / 'remuestreos' / 'ejecucion.json').read_text(encoding='utf-8'))
    conf = json.loads((B / 'configuracion' / 'configuracion.json').read_text(encoding='utf-8'))

    def con_variable(extra):
        return lambda: control_candidatas([*N.VARIABLES_33, extra])

    def registro_mutado(f):
        r = copy.deepcopy(reg[5]); f(r); return lambda: control_registro(r)

    def frec_mutada(f):
        t = frec.copy(); f(t); return t

    escenario_mal = replace(esc, base=replace(esc.base, candidatas=[*esc.base.candidatas, 'doble_carga']))
    sin_estratos = np.random.default_rng(0).choice(529, 529, replace=True)
    sin_reemplazo = np.concatenate([np.flatnonzero(y == 0), np.flatnonzero(y == 1)])
    manif = dict(REAL['ahora']); k = next(k for k in manif if k.startswith('analisis/fase37/')); manif[k] = '0' * 64
    manif_src = dict(REAL['ahora']); ks = next(k for k in manif_src if k.startswith('src/')); manif_src[ks] = '0' * 64
    return [
        ('Candidata extra doble_carga', con_variable('doble_carga')),
        ('Candidata extra prevision', con_variable('prevision')),
        ('Candidata del MRS (mrs_total)', con_variable('mrs_total')),
        ('Falta una candidata (32)', lambda: control_candidatas(N.VARIABLES_33[:-1])),
        ('Escenario con doble_carga', lambda: control_poblaciones(escenario_mal)),
        ('Población laboral alterada', lambda: control_poblaciones(replace(esc, base=replace(esc.base, mascara=np.ones(529, bool))))),
        ('Índice fuera del conjunto (529)', lambda: control_indices(np.r_[idx[:-1], 529], y)),
        ('Remuestreo sin estratificar', lambda: control_indices(sin_estratos, y)),
        ('Remuestreo sin reemplazo', lambda: control_indices(sin_reemplazo, y)),
        ('499 remuestreos', lambda: control_conteo(REAL['rutas'][:-1])),
        ('Decisión incoherente con la relevancia', registro_mutado(lambda r: r['adaptado'].__setitem__('carnes_semana', ['seleccionada', '', '']) if 'carnes_semana' not in r['relevantes'] else r['relevantes'].remove('carnes_semana'))),
        ('Faltan pares', registro_mutado(lambda r: r.__setitem__('n_pares', r['n_pares'] - 1))),
        ('Umbral 0,05 en vez de 0,10', registro_mutado(lambda r: r.__setitem__('relevantes', [v for v in N.VARIABLES_33 if r['q'][v] < 0.05]) if any(0.05 <= r['q'][v] < 0.10 for v in N.VARIABLES_33) else r['q'].__setitem__('edad', 0.07))),
        ('Laboral elimina a una general', registro_mutado(lambda r: r['adaptado'].__setitem__('edad', ['redundante', 'lugar_trabajo_comprensivo', '']))),
        ('Parámetro de permutaciones alterado', lambda: control_parametros({**ej, 'permutaciones': 10000}, conf)),
        ('Alfa alterado en la configuración', lambda: control_parametros(ej, {**conf, 'alfa_q': 0.05})),
        ('Frecuencia con un conteo de más', lambda: control_frecuencias(frec_mutada(lambda t: t.__setitem__('veces_seleccionada', t.veces_seleccionada + (t.index == t.index[0]))), reg)),
        ('Porcentaje con otra base (sobre 499)', lambda: control_frecuencias(frec_mutada(lambda t: t.__setitem__('pct_seleccionada', t.veces_seleccionada / 4.99)), reg)),
        ('Frecuencia mayor que 100', lambda: control_rangos(frec_mutada(lambda t: t.__setitem__('pct_seleccionada', t.pct_seleccionada.where(t.index != t.index[0], 101.0))))),
        ('Falta una variable con 0 %', lambda: control_completitud(frec[frec.variable != frec.variable.iloc[-1]])),
        ('Remuestreo guardado alterado', lambda: control_igual({**reg[0], 'relevantes': reg[0]['relevantes'][:-1]}, reg[0], 'r0')),
        ('Archivo de una fase anterior alterado', lambda: control_manifiesto(antes, manif, 'analisis/')),
        ('Archivo de Django alterado', lambda: control_manifiesto(antes, manif_src, 'src/')),
    ]


def main():
    SAL.mkdir(exist_ok=True)
    _, _, REAL['esc'] = N.cargar()
    REAL['frec'] = pd.read_csv(B / 'resultados' / 'frecuencias_seleccion.csv')
    filas = []
    for n, nombre, f in PRUEBAS:
        try:
            det = f(); ok = True
        except Exception as e:  # noqa: BLE001
            det, ok = f'{type(e).__name__}: {e}', False
            traceback.print_exc()
        filas.append({'prueba': n, 'nombre': nombre, 'resultado': 'superada' if ok else 'FALLA', 'detalle': det})
        print(f"{n:02d} {'OK ' if ok else 'FALLA'} {nombre}: {det}")
    neg = []
    for nombre, f in mutaciones():
        try:
            f(); detectado, msg = False, 'no detectado'
        except (AssertionError, RuntimeError, ValueError) as e:
            detectado, msg = True, f'{type(e).__name__}: {str(e)[:120]}'
        neg.append({'control_negativo': nombre, 'detectado': detectado, 'detalle': msg})
        print(f"   {'detectado' if detectado else 'NO DETECTADO'}: {nombre}")
    pd.DataFrame(filas).to_csv(SAL / 'resultados_pruebas.csv', index=False, encoding='utf-8')
    pd.DataFrame(neg).to_csv(SAL / 'controles_negativos.csv', index=False, encoding='utf-8')
    ok_p, ok_n = sum(f['resultado'] == 'superada' for f in filas), sum(x['detectado'] for x in neg)
    print(f'{ok_p}/{len(filas)} pruebas; {ok_n}/{len(neg)} controles negativos detectados')
    sys.exit(int(ok_p != len(filas) or ok_n != len(neg)))


if __name__ == '__main__':
    main()
