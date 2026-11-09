"""
Fase 37D: pruebas críticas y controles negativos. Cada prueba usa las funciones de H; los controles negativos reemplazan una de ellas por una versión
con un error introducido y exigen que alguna prueba falle.

Uso, desde analisis/: python fase37/37D_caracterizacion/scripts/pruebas_37d.py [--mutaciones]
Escribe pruebas/resultados_pruebas.csv y pruebas/control_mutaciones.csv.
"""
import copy
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import integridad_37d as I
import nucleo_37d as N
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

import individual_37d as IND
import segmentos_37d as SEG

B = N.BASE
R = B / 'resultados'
_D = None


def _cargar():
    global _D
    if _D is None:
        _D = N.cargar()
    return copy.deepcopy(_D)


def _leer(r):
    return pd.read_csv(R / r, encoding='utf-8')


H_ORIG = SimpleNamespace(
    cargar=_cargar, asociacion=N.asociacion, bh=N.bh, holm=N.holm, bootstrap=N.bootstrap, regla_b1=N.regla_b1, solo_observado=N.solo_observado, leer=_leer,
    oficial=lambda: N.etiquetas()[0], alternativas=lambda: N.etiquetas()[1], f35=lambda: pd.read_csv(N.F35, dtype=str),
    limpio=lambda: pd.read_csv(N.LIMPIO, dtype=str, keep_default_na=False, na_values=['']), et37b=lambda: pd.read_csv(N.B37 / 'etiquetas' / 'etiquetas_principales.csv', dtype={'participante_id': str}).set_index('participante_id'),
    leidos=lambda: pd.read_csv(B / 'integridad' / 'archivos_leidos.csv')['archivo_leido'].astype(str).tolist(), fuera=lambda: pd.read_csv(B / 'integridad' / 'escrituras_fuera.csv')['escritura_fuera'].astype(str).tolist(),
    manifiestos=I.manifiestos, git=I.estado_git, pycache=I.pycache, sello=lambda: N.leer_json(B / 'protocolo' / 'sello_protocolo.json'),
    severidad=lambda t: next(n for m, n in N.SEVERIDAD if t <= m), caracteristicas=lambda: list(N.CARACTERISTICAS), para_prueba=N.para_prueba,
)
H = SimpleNamespace(**vars(H_ORIG))
PRUEBAS = []


def prueba(n, nombre):
    def d(f):
        PRUEBAS.append((n, nombre, f))
        return f
    return d


@prueba(1, '529 identificadores únicos, alineados en todas las fuentes')
def p1():
    D = H.cargar()
    ids = D.ids
    assert len(ids) == 529 and len(set(ids)) == 529, 'no son 529 únicos'
    assert list(D.X.index) == ids and list(D.M.index) == ids and list(D.E.index) == ids, 'tablas desalineadas'
    assert H.f35()['participante_id'].tolist() == ids, 'Fase 35 desalineada'
    assert set(ids) <= set(H.limpio()['participante_id']), 'faltan identificadores en la limpieza'
    assert sorted(H.oficial().index) == sorted(ids) and sorted(H.alternativas().index) == sorted(ids), 'etiquetas con otros identificadores'
    return '529 en procedencia, Fase 35, limpieza, A y B1'


@prueba(2, 'Etiquetas de A idénticas a las históricas, con sus tamaños')
def p2():
    D = H.cargar()
    a = D.E['A'].to_numpy()
    assert (a == H.oficial().reindex(D.ids).to_numpy()).all(), 'A distinta del artefacto de la 37C'
    assert (a == H.alternativas().reindex(D.ids)['A'].to_numpy()).all(), 'A distinta del complemento'
    assert (a == H.et37b().reindex(D.ids)[N.CONFIG].to_numpy()).all(), 'A distinta de la 37B'
    assert tuple(np.bincount(a)) == N.TAMANOS_A, f'tamaños {np.bincount(a)}'
    return f'idénticas en 3 fuentes; tamaños {N.TAMANOS_A}'


@prueba(3, 'Etiquetas de B1 idénticas a las históricas y a la regla')
def p3():
    D = H.cargar()
    b = D.E['B1'].to_numpy()
    X = D.X
    assert (b == H.alternativas().reindex(D.ids)['B1_doble_uso'].to_numpy()).all(), 'B1 distinta de la guardada'
    assert (b == H.regla_b1(X['trabaja_actualmente'], X['tiene_pareja'], X['dias_ejercicio_semana'])).all(), 'B1 no sigue la regla de cuatro pasos'
    assert (b == N.b1_desde_mapa(X['trabaja_actualmente'], X['tiene_pareja'], X['dias_ejercicio_semana'])).all(), 'B1 no sigue el mapa de celdas'
    assert tuple(np.bincount(b)) == N.TAMANOS_B1, f'tamaños {np.bincount(b)}'
    return f'idénticas a la columna guardada, a la regla y al mapa; tamaños {N.TAMANOS_B1}'


@prueba(4, 'MRS: ítems, dimensiones, total, severidad y severo correctos')
def p4():
    D = H.cargar()
    M = D.M
    L = H.limpio().set_index('participante_id').reindex(D.ids)
    it = L[N.ITEMS].astype(int)
    assert (M['mrs_total'].to_numpy() == it.sum(axis=1).to_numpy()).all(), 'total distinto de la suma de 11 ítems'
    for d, cols in N.DIMENSIONES.items():
        assert (M[d].to_numpy() == it[cols].sum(axis=1).to_numpy()).all(), f'{d} distinta'
        assert (M[d].to_numpy() == L[d].astype(int).to_numpy()).all(), f'{d} distinta de la limpieza'
    assert (M['mrs_somatico'] + M['mrs_psicologico'] + M['mrs_urogenital'] == M['mrs_total']).all(), 'dimensiones no suman el total'
    for t, esp in ((0, 'Sin síntomas o muy leves'), (4, 'Sin síntomas o muy leves'), (5, 'Leve'), (8, 'Leve'), (9, 'Moderada'), (15, 'Moderada'), (16, 'Severa'), (44, 'Severa')):
        assert H.severidad(t) == esp, f'corte en {t}'
    assert (M['severidad'].to_numpy() == L['mrs_severidad'].to_numpy()).all(), 'severidad distinta de la limpieza'
    assert (M['severo_mrs'].to_numpy() == H.f35()['severo_mrs'].astype(int).to_numpy()).all(), 'severo distinto de la Fase 35'
    assert (M['severo_mrs'].to_numpy() == (M['mrs_total'] >= 16).astype(int).to_numpy()).all(), 'severo no es total ≥ 16'
    return 'recalculado desde los ítems; coincide con la limpieza y la Fase 35; cortes 4/5, 8/9, 15/16'


@prueba(5, 'Faltantes, no aplica e imputadas tratados según el protocolo')
def p5():
    D = H.cargar()
    X, est = D.X, D.estado
    for v in ('frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'cantidad_personas_cuida'):
        na = (est[v] == 'no_aplicable').to_numpy()
        assert (X[v].to_numpy()[na] == 0).all(), f'{v}: no aplica no es 0 estructural'
        assert X[v].notna().all(), f'{v}: faltantes donde no debería'
    for v in ('lugar_trabajo_comprensivo', 'estres_entorno_laboral'):
        assert X[v].isna().sum() == int(est[v].isin(['no_aplicable', 'faltante']).sum()), f'{v}: faltantes mal contados'
        assert X.loc[X['trabaja_actualmente'] == 0, v].isna().all(), f'{v}: valores en quienes no trabajan'
    assert X['imc'].notna().sum() == int((est['imc'] == 'observada').sum()) == 267, 'IMC con imputados'
    O = H.solo_observado(X, est, D.heredada)
    for v in N.EN_A:
        esperado = est[v].isin(['imputada', 'deducida']) | (D.heredada[v].astype(str) == '1')
        assert O[v].isna().sum() == X[v].isna().sum() + int((esperado & X[v].notna()).sum()), f'S-OBS mal en {v}'
    return 'no aplica = 0 en ejercicio y cuidado; módulos solo en su población; IMC solo observado (267); S-OBS quita imputadas, deducida y heredadas'


@prueba(6, 'Ninguna lectura del simulador ni escritura fuera de la carpeta')
def p6():
    leidos = H.leidos()
    malos = [x for x in leidos if any(p in x.lower() for p in N.PROHIBIDOS)]
    assert not malos, f'lecturas prohibidas: {malos}'
    assert not H.fuera(), 'escrituras fuera de la carpeta'
    try:
        open(N.RAIZ / 'no_existe_verdad.csv')
        raise AssertionError('el gancho no bloquea archivos del simulador')
    except PermissionError:
        pass
    except FileNotFoundError:
        raise AssertionError('el gancho no bloquea archivos del simulador')
    D = H.cargar()
    cols = list(D.X.columns) + list(D.M.columns) + list(D.E.columns)
    assert not [c for c in cols if 'verdad' in c or 'latente' in c], 'columnas del simulador'
    return f'{len(leidos)} archivos leídos, ninguno del simulador; 0 escrituras fuera; el gancho bloquea'


@prueba(7, 'Prueba estadística apropiada para cada tipo de variable, con valores correctos')
def p7():
    rng = np.random.default_rng(1)
    y = rng.normal(size=200)
    xo = rng.integers(1, 6, 200).astype(float)
    xb = rng.integers(0, 2, 200).astype(float)
    xn = rng.choice(['a', 'b', 'c'], 200)
    a = H.asociacion(xo, y, 'ordinal')
    assert a['prueba'] == 'Spearman' and np.isclose(a['efecto'], stats.spearmanr(xo, y)[0]), 'ordinal'
    b = H.asociacion(xb, y, 'binaria')
    u = stats.mannwhitneyu(y[xb == 1], y[xb == 0], alternative='two-sided')
    assert b['prueba'] == 'Mann-Whitney' and np.isclose(b['p'], u.pvalue) and np.isclose(b['efecto'], 2 * u.statistic / ((xb == 1).sum() * (xb == 0).sum()) - 1), 'binaria'
    c = H.asociacion(xn, y, 'nominal')
    h = stats.kruskal(*[y[xn == k] for k in 'abc'])
    assert c['prueba'] == 'Kruskal-Wallis' and np.isclose(c['efecto'], (h.statistic - 2) / (200 - 3)), 'nominal'
    d = H.asociacion(xb, (y > 0).astype(int), 'binaria', 'binaria')
    assert d['prueba'] in ('χ²', 'Fisher exacta') and d['medida'] == 'V', 'severo con binaria'
    e = H.asociacion(xo, (y > 0).astype(int), 'ordinal', 'binaria')
    assert e['prueba'] == 'Mann-Whitney', 'severo con ordinal'
    f1 = H.leer('individual/F1_total.csv')
    for v, p in (('edad', 'Spearman'), ('trabaja_actualmente', 'Mann-Whitney'), ('quien_prepara_comidas', 'Kruskal-Wallis'), ('dias_ejercicio_semana', 'Spearman'), ('etapa_menopausica', 'Kruskal-Wallis')):
        assert f1.set_index('variable').loc[v, 'prueba'] == p, f'{v} con prueba equivocada'
    return 'Spearman, Mann-Whitney, Kruskal-Wallis y χ² según el tipo; valores iguales a scipy'


@prueba(8, 'Control de comparaciones múltiples (Benjamini-Hochberg y Holm)')
def p8():
    rng = np.random.default_rng(2)
    p = rng.uniform(size=50) ** 2
    assert np.allclose(H.bh(p), multipletests(p, method='fdr_bh')[1]), 'BH distinto de statsmodels'
    assert np.allclose(H.holm(p[:6]), multipletests(p[:6], method='holm')[1]), 'Holm distinto de statsmodels'
    for r, n in (('individual/F1_total.csv', 36), ('individual/F2_dimensiones.csv', 108), ('individual/F3_severo.csv', 36), ('individual/F4_items.csv', 396)):
        d = H.leer(r)
        assert len(d) == n and np.allclose(d['q'], multipletests(d['p'], method='fdr_bh')[1]), f'{r}: q mal corregida'
    g = H.leer('segmentos/F5_global.csv')
    assert len(g) == 12 and np.allclose(g['q'], multipletests(g['p'], method='fdr_bh')[1]), 'F5 mal corregida'
    return 'BH y Holm iguales a statsmodels; F1 a F5 con el número de pruebas del protocolo'


@prueba(9, 'Resultados reproducibles')
def p9():
    D = H.cargar()
    f1 = H.leer('individual/F1_total.csv').set_index('variable')
    for i, v in enumerate(N.CARACTERISTICAS):
        if v not in ('edad', 'trabaja_actualmente', 'prevision', 'imc'):
            continue
        t = N.tipo_de(v, D.defs)
        x = N.para_prueba(D.X, v).to_numpy()
        a = H.asociacion(x, D.M['mrs_total'].to_numpy(), t)
        ic = H.bootstrap(x, D.M['mrs_total'].to_numpy(), t, semilla_extra=i)
        assert np.isclose(a['efecto'], f1.loc[v, 'efecto']) and np.isclose(a['p'], f1.loc[v, 'p']), f'{v}: efecto distinto'
        assert np.isclose(ic[0], f1.loc[v, 'ic_inf']) and np.isclose(ic[1], f1.loc[v, 'ic_sup']), f'{v}: IC distinto'
    g = H.leer('segmentos/F5_global.csv').set_index(['segmentacion', 'resultado'])
    for s in ('A', 'B1'):
        r = N.segmento_frente_a(D.M['mrs_total'].to_numpy(), D.E[s].to_numpy(), 'continua')
        assert np.isclose(r['efecto'], g.loc[(s, 'mrs_total'), 'efecto']), f'F5 {s} distinto'
    return 'efectos, p e IC bootstrap recalculados iguales a los guardados'


@prueba(10, 'Sin selección retrospectiva por MRS')
def p10():
    sello = datetime.fromisoformat(H.sello()['sellado']).timestamp()
    previos = [p.name for p in R.rglob('*.csv') if p.stat().st_mtime < sello]
    assert not previos, f'resultados anteriores al sello: {previos[:3]}'
    proto = (B / 'protocolo' / '01_protocolo_37D.md').read_text(encoding='utf-8')
    secc = proto.split('### 4.2')[1].split('### 4.4')[0]
    del_protocolo = set(re.findall(r'`([a-z_]+)`', secc)) - {'doble_carga'}
    alimentacion = set(N.BLOQUES['Alimentación']) - {'quien_prepara_comidas'}
    car = set(H.caracteristicas())
    assert del_protocolo | alimentacion == car and len(car) == 36, f'variables distintas del protocolo: {sorted(car ^ (del_protocolo | alimentacion))}'
    f1 = H.leer('individual/F1_total.csv')
    assert set(f1['variable']) == car, 'F1 no cubre las 36 del protocolo'
    for r in ('segmentos/F6_caracterizacion_efectos.csv',):
        d = H.leer(r)
        assert all(set(d[d['segmentacion'] == s]['variable']) == car for s in ('A', 'B1')), 'F6 incompleta'
    dec = (B / 'resultados' / 'segmentos' / 'correspondencia_resumen.json').read_text(encoding='utf-8')
    assert 'ganador' not in dec and 'seleccion' not in dec, 'la comparación guarda una elección'
    return 'todos los resultados son posteriores al sello; las 36 variables son las del protocolo; ninguna elección guardada'


@prueba(11, 'Fases anteriores intactas')
def p11():
    m = H.manifiestos()
    assert int(m['distintos'].sum()) == 0, f'archivos distintos: {m[m["distintos"] > 0]["ejemplos"].tolist()}'
    assert int(m['sin_verificar_por_nombre'].sum()) <= 4, 'más archivos sin verificar que los 4 del simulador'
    assert not H.pycache(), 'carpetas __pycache__ en fases protegidas'
    return f'{int(m["comparados_por_huella"].sum())} archivos iguales a sus manifiestos; 4 del simulador sin abrir'


@prueba(12, 'Django, datos versionados y git sin cambios')
def p12():
    g = H.git()
    assert g['head'] == I.HEAD_ESPERADO, f'HEAD {g["head"]}'
    assert not g['cambios_en_src'], f'cambios en la plataforma: {g["cambios_en_src"][:3]}'
    assert not g['cambios_fuera_de_analisis'], 'cambios fuera de analisis/'
    assert not g['datos_versionados_modificados'], 'datos modificados'
    return f'HEAD {g["head"]}; sin cambios en src/, datos/ ni fuera de analisis/'


@prueba(13, 'Caracterización de A reproduce los efectos de la Fase 37C')
def p13():
    c = H.leer('segmentos/comparacion_con_37C.csv')
    assert len(c) == 10 and np.allclose(c['efecto'], c['efecto_37C']), 'η² distintos de la Fase 37C'
    return '10 de 10 variables con el mismo η² que la 37C'


@prueba(14, 'Agrupaciones de etapa y previsión fijadas en el protocolo')
def p14():
    D = H.cargar()
    e = H.para_prueba(D.X, 'etapa_menopausica')
    p = H.para_prueba(D.X, 'prevision')
    assert e.nunique() == 5 and (e == 'indeterminada').sum() == 22, 'etapa mal agrupada'
    assert set(p.unique()) == {'FONASA', 'ISAPRE', 'otra o ninguna'} and (p == 'otra o ninguna').sum() == 24, 'previsión mal agrupada'
    return 'etapa: 5 categorías (22 indeterminadas); previsión: 3 categorías (24 otra o ninguna)'


@prueba(15, 'Tamaños efectivos informados y coherentes')
def p15():
    f1 = H.leer('individual/F1_total.csv').set_index('variable')
    assert f1.loc['imc', 'n'] == 267 and f1.loc['lugar_trabajo_comprensivo', 'n'] == 287 and f1.loc['sobrecarga_fisica_emocional', 'n'] == 251, 'n de subpoblaciones'
    assert (f1.drop(['imc', 'lugar_trabajo_comprensivo', 'estres_entorno_laboral', 'sobrecarga_fisica_emocional'])['n'] == 529).all(), 'n distinto de 529'
    g = H.leer('segmentos/F5_mrs_por_grupo.csv').query("resultado == 'mrs_total'")
    assert tuple(g[g['segmentacion'] == 'A']['n']) == N.TAMANOS_A and tuple(g[g['segmentacion'] == 'B1']['n']) == N.TAMANOS_B1, 'n por grupo'
    return 'n por prueba y por grupo según el protocolo'


def correr(registrar=True):
    filas = []
    for n, nombre, f in PRUEBAS:
        t = time.time()
        try:
            det, ok = f(), True
        except Exception as e:  # noqa: BLE001
            det, ok = f'{type(e).__name__}: {e}', False
        filas.append({'n': n, 'prueba': nombre, 'resultado': 'superada' if ok else 'FALLA', 'detalle': det, 'segundos': round(time.time() - t, 2)})
    return pd.DataFrame(filas)


def _envolver_D(f):
    def c():
        D = _cargar()
        f(D)
        return D
    return c


def _sin_heredadas(X, est, her):
    return H_ORIG.solo_observado(X, est, her.map(lambda x: '0'))


def _leer_mut(r, quitar=None, mult=None):
    d = _leer(r)
    if quitar and r == 'individual/F1_total.csv':
        d = d[d['variable'] != quitar]
    if mult and r == mult[0]:
        d['q'] = np.minimum(d['p'] * len(d), 1)
    return d


MUTACIONES = [
    ('Etiquetas de A desalineadas (permutadas)', 'cargar', _envolver_D(lambda D: D.E.__setitem__('A', np.random.default_rng(0).permutation(D.E['A'].to_numpy())))),
    ('Se filtra una participante', 'cargar', lambda: (lambda D: SimpleNamespace(**{**vars(D), 'ids': D.ids[:-1], 'X': D.X.iloc[:-1], 'M': D.M.iloc[:-1], 'E': D.E.iloc[:-1]}))(_cargar())),
    ('B1 con validación cruzada en lugar de B1', 'cargar', _envolver_D(lambda D: D.E.__setitem__('B1', D.E['B1_cv'].to_numpy()))),
    ('Regla B1 con corte de 2 días', 'regla_b1', lambda t, p, d: np.where(np.asarray(d) >= 2, 1, np.where(np.asarray(p) == 0, 0, np.where(np.asarray(t) == 0, 2, 3)))),
    ('MRS total sin el ítem 11', 'cargar', _envolver_D(lambda D: D.M.__setitem__('mrs_total', D.M['mrs_total'] - D.M['pregunta_11']))),
    ('Severidad con corte en 15', 'severidad', lambda t: next(n for m, n in ((4, 'Sin síntomas o muy leves'), (8, 'Leve'), (14, 'Moderada'), (44, 'Severa')) if t <= m)),
    ('No aplica como faltante en ejercicio', 'cargar', _envolver_D(lambda D: D.X.__setitem__('frecuencia_fuerza', D.X['frecuencia_fuerza'].where(D.estado['frecuencia_fuerza'] != 'no_aplicable')))),
    ('IMC imputado por la media incluido', 'cargar', _envolver_D(lambda D: D.X.__setitem__('imc', D.X['imc'].fillna(D.X['imc'].mean())))),
    ('S-OBS sin quitar las heredadas', 'solo_observado', _sin_heredadas),
    ('Binaria analizada con Spearman', 'asociacion', lambda x, y, t, ty='continua': N.asociacion(x, y, 'ordinal' if t == 'binaria' else t, ty)),
    ('Bonferroni en lugar de Benjamini-Hochberg', 'bh', lambda p: np.minimum(np.asarray(p, float) * len(p), 1)),
    ('q de F4 corregida con otro método', 'leer', lambda r: _leer_mut(r, mult=('individual/F4_items.csv',))),
    ('Bootstrap con otra semilla', 'bootstrap', lambda x, y, t, semilla_extra=0, b=N.N_BOOT: N.bootstrap(x, y, t, semilla_extra + 1, b)),
    ('Se lee la verdad del simulador', 'leidos', lambda: H_ORIG.leidos() + ['datos/sintetico/dataset_usuaria_verdad.csv']),
    ('Una variable fuera de F1', 'leer', lambda r: _leer_mut(r, quitar='edad')),
    ('Una variable externa agregada después', 'caracteristicas', lambda: list(N.CARACTERISTICAS) + ['usa_antidepresivos']),
    ('Un archivo protegido cambia', 'manifiestos', lambda: H_ORIG.manifiestos(sha=lambda p: '0' * 64 if p.name == 'etiquetas.csv' else N.sha(p))),
    ('Cambio en la plataforma Django', 'git', lambda: {**H_ORIG.git(), 'cambios_en_src': [' M src/apps/encuestas/models.py']}),
    ('Etapa sin agrupar las indeterminadas', 'para_prueba', lambda X, v: X[v] if v == 'etapa_menopausica' else N.para_prueba(X, v)),
    ('A distinta en la 37B', 'et37b', lambda: H_ORIG.et37b().assign(**{N.CONFIG: lambda d: (d[N.CONFIG] + 1) % 4})),
]


def main():
    N.instalar_gancho()
    N.huella_sello()
    base = correr()
    N.a_csv(base, B / 'pruebas' / 'resultados_pruebas.csv')
    print(base[['n', 'prueba', 'resultado', 'detalle']].to_string(index=False))
    if '--mutaciones' in sys.argv:
        filas = []
        for nombre, attr, f in MUTACIONES:
            setattr(H, attr, f)
            r = correr()
            setattr(H, attr, getattr(H_ORIG, attr))
            fallas = r[r['resultado'] != 'superada']
            filas.append({'control_negativo': nombre, 'funcion_alterada': attr, 'detectado': len(fallas) > 0, 'pruebas_que_fallan': ', '.join(map(str, fallas['n'])), 'motivo': fallas['detalle'].iloc[0][:160] if len(fallas) else ''})
        m = pd.DataFrame(filas)
        N.a_csv(m, B / 'pruebas' / 'control_mutaciones.csv')
        print(m[['control_negativo', 'detectado', 'pruebas_que_fallan', 'motivo']].to_string(index=False))
        print(f"{int(m['detectado'].sum())} de {len(m)} errores detectados")
    N.registrar('pruebas')
    sys.exit(int((base['resultado'] != 'superada').any()))


if __name__ == '__main__':
    main()
