"""
Fase 37B: pruebas de la Parte 12 del encargo, más la correspondencia de tablas, figuras y lista para la Fase 37C.

Uso, desde analisis/: python fase37/37B_clustering/scripts/pruebas_37b.py [--sin-reproducir]
Con --sin-reproducir omite la repetición completa en otra carpeta y la marca como no ejecutada.
Las métricas se recalculan con implementaciones propias, no con las mismas funciones que produjeron los resultados.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import traceback
from functools import lru_cache
from math import comb
from pathlib import Path

import nucleo_37b as Q
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

B = Q.BASE
AQUI = Q.AQUI
PRUEBAS = []
MUESTRA = ['P1_c05_km_k3', 'F1_c08_km_k5', 'P2_c20_ward_k4', 'F2_c02_ward_k8', 'R0P1_cTodas_km_k6', 'R0P2_cTodas_ward_k2']
REPRODUCIR = True


def prueba(n, nombre):
    def deco(f):
        PRUEBAS.append((n, nombre, f))
        return f
    return deco


@lru_cache(maxsize=None)
def _lote(c):
    return json.loads((B / 'resultados' / 'lotes' / f'{c}.json').read_text(encoding='utf-8'))


def lote(c):
    return _lote(c)


def cfgs():
    return Q.configuraciones()


@lru_cache(maxsize=None)
def _csv(r):
    return pd.read_csv(B / r, encoding='utf-8', dtype={'participante_id': str})


def tabla(r):
    return _csv(r).copy()


def etiquetas():
    return tabla('etiquetas/etiquetas_principales.csv')


def permutar(p, r):
    return Q.permutar_general(p, r)


def X_de(c):
    d = lote(c)
    return Q.coordenadas(d['espacio'], d['componentes']).to_numpy()


def silueta_propia(X, l):
    D = np.sqrt(((X[:, None] - X[None]) ** 2).sum(axis=2))
    s = np.zeros(len(X))
    for i in range(len(X)):
        a = D[i, l == l[i]].sum() / max((l == l[i]).sum() - 1, 1)
        b = min(D[i, l == g].mean() for g in np.unique(l) if g != l[i])
        s[i] = (b - a) / max(a, b)
    return s


def db_propio(X, l):
    g = np.unique(l)
    c = np.vstack([X[l == x].mean(axis=0) for x in g])
    S = np.array([np.sqrt(((X[l == x] - c[i]) ** 2).sum(axis=1)).mean() for i, x in enumerate(g)])
    return float(np.mean([max((S[i] + S[j]) / np.linalg.norm(c[i] - c[j]) for j in range(len(g)) if j != i) for i in range(len(g))]))


def ch_propio(X, l):
    g = np.unique(l)
    m = X.mean(axis=0)
    ssb = sum((l == x).sum() * ((X[l == x].mean(axis=0) - m) ** 2).sum() for x in g)
    ssw = sum(((X[l == x] - X[l == x].mean(axis=0)) ** 2).sum() for x in g)
    return float((ssb / (len(g) - 1)) / (ssw / (len(X) - len(g))))


def ari_propio(a, b):
    a, b = np.asarray(a), np.asarray(b)
    tc = pd.crosstab(a, b).to_numpy()
    n_ij = sum(comb(int(x), 2) for x in tc.ravel())
    n_a = sum(comb(int(x), 2) for x in tc.sum(axis=1))
    n_b = sum(comb(int(x), 2) for x in tc.sum(axis=0))
    esperado = n_a * n_b / comb(len(a), 2)
    maximo = (n_a + n_b) / 2
    return 1.0 if maximo == esperado else (n_ij - esperado) / (maximo - esperado)


@prueba(1, 'Integridad de matrices y coordenadas')
def p01():
    v = pd.read_csv(B / 'integridad' / 'verificacion_entradas.csv')
    assert (v['resultado'] == 'OK').all() and len(v) == 53
    for c in cfgs():
        d = lote(c['config'])
        e, k = d['espacio'], d['componentes']
        ruta = Q.F36 / 'matrices' / f'{Q.MATRIZ[e[2:]]}.csv' if k == 0 else Q.A37 / 'coordenadas' / e / f'coordenadas_k{k:02d}.csv'
        assert d['huella_entrada'] == Q.sha(ruta), c['config']
    return '53 verificaciones previas OK; cada configuración guarda la huella del archivo que coincide con su entrada'


@prueba(2, 'Conservación de las 529 participantes')
def p02():
    e = etiquetas()
    assert e.shape == (529, 421) and e.drop(columns='participante_id').notna().all().all()
    return '529 filas y 420 configuraciones, sin valores faltantes'


@prueba(3, 'Identificadores correctos')
def p03():
    ids = Q.identificadores()
    assert etiquetas()['participante_id'].tolist() == ids
    r = tabla('estabilidad/remuestreos.csv')
    assert set(r['participante_id']) <= set(ids)
    for p in sorted((B / 'sensibilidades' / 'etiquetas').glob('*.csv')):
        x = pd.read_csv(p, dtype={'participante_id': str}, usecols=['participante_id'])['participante_id']
        assert len(x) == 529 and sorted(x) == sorted(ids) and x.is_unique, p.name
    for f in (B / 'prototipos').glob('distancias_*.csv'):
        assert pd.read_csv(f, dtype=str, usecols=['participante_id'])['participante_id'].tolist() == ids
    return 'Etiquetas, distancias y las 34 variantes: los identificadores coinciden, sin repetidos ni faltantes'


@prueba(4, 'Ausencia de variables del MRS')
def p04():
    for e in Q.ESPACIOS:
        Q.verificar_columnas(Q.matriz(e).columns)
    Q.verificar_columnas(Q.tabla_general().columns)
    leidos = pd.read_csv(B / 'integridad' / 'archivos_leidos.csv')['archivo_leido'].astype(str).tolist()
    assert leidos and any('procedencia_celdas' in x for x in leidos)
    assert not [x for x in leidos if x.startswith('datos/') or re.search(r'verdad|bitacora|mrs', x, re.I)]
    assert len(pd.read_csv(B / 'integridad' / 'escrituras_fuera.csv')) == 0
    for s in AQUI.glob('*.py'):
        if s.name in ('pruebas_37b.py', 'control_mutaciones_37b.py', 'generar_informes_37b.py', 'verificar_entradas_37b.py'):
            continue
        codigo = s.read_text(encoding='utf-8')
        sin_lista = codigo.replace("TERMINOS_EXCLUIDOS = ('mrs', 'severo', 'severidad', 'sintoma_')", '')
        assert not re.search(r'mrs|severo|severidad', sin_lista, re.I), s.name
    return f'Sin columnas del MRS; {len(leidos)} archivos leídos según la auditoría, ninguno de datos/; los programas no lo mencionan'


@prueba(5, 'Ausencia de escalado adicional')
def p05():
    for c in MUESTRA:
        d, X = lote(c), X_de(c)
        l = np.array(d['etiquetas'])
        protos = np.vstack([X[l == g].mean(axis=0) for g in range(d['k'])])
        if d['algoritmo'] == 'km':
            assert abs(Q.inercia_interna(X, l) - d['inercia']) < 1e-8, c
            assert np.abs(protos - np.array(d['centroides'])).max() < 1e-8, c
        else:
            assert np.abs(protos - np.array(d['centroides'])).max() < 1e-12, c
    for s in AQUI.glob('*.py'):
        if s.name in ('pruebas_37b.py', 'control_mutaciones_37b.py'):
            continue
        assert not re.search(r'StandardScaler|RobustScaler|MinMaxScaler|whiten|normalize\(|\.std\(\)\s*\)', s.read_text(encoding='utf-8')), s.name
    return 'Inercia y centroides se reproducen con las coordenadas tal como están; sin escaladores en los programas'


def _repite(a):
    filas = []
    for c in MUESTRA:
        d = lote(c)
        if d['algoritmo'] != a:
            continue
        l1 = Q.ajustar(X_de(c), a, d['k'])[0]
        l2 = Q.ajustar(X_de(c), a, d['k'])[0]
        assert l1.tolist() == l2.tolist() == d['etiquetas'], c
        filas.append(c)
    return filas


@prueba(6, 'Reproducibilidad de K-means')
def p06():
    f = _repite('km')
    return f'{len(f)} configuraciones ajustadas otra vez: etiquetas idénticas. La repetición completa está en la prueba 22'


@prueba(7, 'Reproducibilidad del aglomerativo')
def p07():
    f = _repite('ward')
    return f'{len(f)} configuraciones ajustadas otra vez: etiquetas idénticas. La repetición completa está en la prueba 22'


@prueba(8, 'Número correcto de etiquetas')
def p08():
    e = etiquetas()
    for c in cfgs():
        l = e[c['config']].to_numpy()
        assert len(l) == 529 and sorted(np.unique(l)) == list(range(c['k'])), c['config']
    return 'Cada participante tiene una etiqueta, y cada configuración usa exactamente k grupos'


@prueba(9, 'Tamaños de grupos consistentes')
def p09():
    e = etiquetas()
    t = tabla('resultados/tamanos_grupos.csv').set_index('config')
    for c in cfgs():
        n = np.bincount(e[c['config']].to_numpy(), minlength=c['k'])
        assert n.sum() == 529 and ' '.join(map(str, n)) == t.loc[c['config'], 'tamanos'], c['config']
        assert n.min() == t.loc[c['config'], 'tam_min'] and (n < 27).sum() == t.loc[c['config'], 'grupos_pequenos'], c['config']
    g = tabla('resultados/grupos_pequenos.csv')
    assert len(g) == t['grupos_pequenos'].sum()
    return f'Tamaños recalculados iguales a la tabla en las 420; {len(g)} grupos bajo 27 registrados'


@prueba(10, 'Métricas correctamente calculadas')
def p10():
    t = tabla('resultados/metricas_calidad.csv').set_index('config')
    mx = 0.0
    for c in MUESTRA:
        X, l = X_de(c), np.array(lote(c)['etiquetas'])
        s = silueta_propia(X, l)
        dif = [abs(s.mean() - t.loc[c, 'silueta']), abs((s < 0).mean() - t.loc[c, 'silueta_negativos']), abs(db_propio(X, l) - t.loc[c, 'davies_bouldin']), abs(ch_propio(X, l) - t.loc[c, 'calinski_harabasz']) / t.loc[c, 'calinski_harabasz']]
        mx = max(mx, max(dif))
    assert mx < 1e-9, mx
    return f'{len(MUESTRA)} configuraciones con implementación propia de silueta, Davies-Bouldin y Calinski-Harabasz: diferencia máxima {mx:.1e}'


@prueba(11, 'ARI correcto e invariante a los nombres de los clústeres')
def p11():
    rng = np.random.default_rng(1)
    for _ in range(30):
        a, b = rng.integers(0, 5, 200), rng.integers(0, 4, 200)
        assert abs(ari_propio(a, b) - adjusted_rand_score(a, b)) < 1e-10
    e = etiquetas()
    for c in MUESTRA:
        l = e[c].to_numpy()
        renombre = rng.permutation(lote(c)['k'])
        assert abs(adjusted_rand_score(l, renombre[l]) - 1) < 1e-12
        idx = Q.subconjuntos()[0]
        lr = Q.ajustar(X_de(c)[idx], lote(c)['algoritmo'], lote(c)['k'], Q.semilla_rep(0))[0]
        v = adjusted_rand_score(l[idx], lr)
        assert abs(v - lote(c)['ari_completo_rep'][0]) < 1e-12 and abs(adjusted_rand_score(renombre[l][idx], lr) - v) < 1e-12, c
    return 'Coincide con una implementación propia; renombrar los grupos no cambia el valor; primera repetición reproducida'


@prueba(12, 'Remuestreos reproducibles')
def p12():
    subs = Q.subconjuntos()
    assert len(subs) == 30 and all(len(x) == 423 and len(set(x)) == 423 for x in subs)
    ids = np.array(Q.identificadores())
    r = tabla('estabilidad/remuestreos.csv')
    for i, x in enumerate(subs):
        assert r[r['repeticion'] == i]['participante_id'].tolist() == ids[x].tolist(), i
    assert len({tuple(x) for x in subs}) == 30
    c = 'P1_c05_km_k3'
    d = lote(c)
    est = Q.estabilidad(X_de(c), 'km', d['k'], np.array(d['etiquetas']), subs)
    assert all(abs(est[k] - d[k]) < 1e-12 for k in est), 'estabilidad distinta'
    return '30 subconjuntos de 423, sin repetidos y distintos entre sí, iguales a los guardados; estabilidad de una configuración reproducida completa'


@prueba(13, 'Comparaciones solo sobre participantes compartidas')
def p13():
    c = 'F1_c08_km_k5'
    d, X = lote(c), X_de(c)
    subs = Q.subconjuntos()[:6]
    et = [Q.ajustar(X[i], 'km', 5, Q.semilla_rep(r))[0] for r, i in enumerate(subs)]
    vals = []
    for a in range(6):
        for b in range(a + 1, 6):
            comunes, ia, ib = np.intersect1d(subs[a], subs[b], return_indices=True)
            assert 0 < len(comunes) < 423
            vals.append(ari_propio(et[a][ia], et[b][ib]))
    pos = Q.estabilidad(X, 'km', 5, np.array(d['etiquetas']), subs)['ari_entre_media']
    assert abs(np.mean(vals) - pos) < 1e-10, (np.mean(vals), pos)
    for nom, n_p in (('S-TRA_P1', 22), ('S-EJE_F1', 75), ('S-ORD_P1', 0)):
        e = pd.read_csv(B / 'sensibilidades' / 'etiquetas' / f'{nom}.csv', dtype={'participante_id': str}).set_index('participante_id')
        base = etiquetas().set_index('participante_id')['P1_c05_km_k3' if nom.endswith('P1') else 'F1_c05_km_k3']
        col = base.name
        aj = e[e['rol'] == 'ajuste']
        s = tabla('sensibilidades/comparacion_sensibilidades.csv')
        fila = s[(s['sensibilidad'] == nom.split('_')[0]) & (s['config_base'] == col)].iloc[0]
        assert abs(ari_propio(base.loc[aj.index], aj[col]) - fila['ari_ajuste']) < 1e-10 and (e['rol'] == 'proyeccion').sum() == n_p, nom
    return 'ARI entre remuestreos recalculado sobre la intersección; ARI de sensibilidades recalculado solo con las filas presentes en ambas'


@prueba(14, 'Referencia nula correctamente construida')
def p14():
    p = Q.tabla_general()
    t = permutar(p, 0)
    t2 = permutar(p, 0)
    assert t.equals(t2) and not t.equals(permutar(p, 1))
    assert list(t.index) == list(p.index)
    for v in p.columns:
        assert sorted(t[v]) == sorted(p[v]), f'marginal de {v}'
    for v, m in Q.MADRES.items():
        assert ((t[v] == '') == (t[m] == 'NO')).all(), f'{v} separada de su madre'
    gen = [v for v in p.columns if v not in Q.MADRES.values()]
    perms = 0
    orden = sorted(gen)
    for e in Q.ESPACIOS:
        Z0 = Q.matriz(e)
        Z1 = Q.TF.Transformador.cargar(Q.F36 / 'artefactos' / e).transformar(t)[0]
        assert abs(Z1.var(ddof=0).sum() - Z0.var(ddof=0).sum()) < 1e-9, 'la inercia debe conservarse sin reescalar'
        assert np.abs(Z1.mean().to_numpy() - Z0.mean().to_numpy()).max() < 1e-12
        for i, v in enumerate(orden):
            cols = [c for c in Z0.columns if c == v or c.startswith(v + '__')]
            if not cols:
                continue
            perm = np.random.default_rng(np.random.SeedSequence([Q.SEMILLA, 1000, i])).permutation(529)
            assert np.abs(Z1[cols].to_numpy() - Z0[cols].to_numpy()[perm]).max() < 1e-12, (e, v)
            perms += 1
    R0, R1 = Q.matriz('P1').drop(columns='imc').to_numpy(), Q.TF.Transformador.cargar(Q.F36 / 'artefactos' / 'P1').transformar(t)[0].drop(columns='imc').to_numpy()
    r0 = np.corrcoef(R0.T)
    r1 = np.corrcoef(R1.T)
    tri = np.triu_indices_from(r0, 1)
    assert np.abs(r1[tri]).mean() < np.abs(r0[tri]).mean(), 'la permutación debe debilitar las asociaciones'
    esp = Q.espacios_nulos(p, 0)
    n = tabla('referencia_nula/metricas_por_replica.csv')
    for c in MUESTRA[:3]:
        d = lote(c)
        X = esp[d['espacio']][:, :d['componentes']]
        l = Q.ajustar(X, d['algoritmo'], d['k'])[0]
        assert abs(Q.calidad(X, l)[0]['silueta'] - n[(n['replica'] == 0) & (n['config'] == c)]['silueta'].iloc[0]) < 1e-12, c
    assert len(n) == 8400 and n['replica'].nunique() == 20 and n['config'].nunique() == 420
    codigo = (AQUI / 'ejecutar_nula_37b.py').read_text(encoding='utf-8') + Q.Path(AQUI / 'nucleo_37b.py').read_text(encoding='utf-8').split('def permutar_general')[1].split('def verificar_columnas')[0]
    assert 'etiquetas_principales' not in codigo and 'coordenadas_k' not in codigo and 'resultados' not in codigo
    return f'Marginales conservadas; frecuencias con su madre; transformar lo permutado equivale a mover las columnas de cada variable ({perms} comprobaciones); inercia conservada sin reescalar; asociaciones debilitadas; 8.400 filas; no usa etiquetas observadas'


@prueba(15, 'Ausencia de fuga de información')
def p15():
    c = 'P1_c05_km_k3'
    X = X_de(c).copy()
    idx = Q.subconjuntos()[0]
    l0 = Q.ajustar(X[idx], 'km', 3, Q.semilla_rep(0))[0]
    resto = np.setdiff1d(np.arange(529), idx)
    X2 = X.copy()
    X2[resto] = X2[resto] + 1000
    assert l0.tolist() == Q.ajustar(X2[idx], 'km', 3, Q.semilla_rep(0))[0].tolist(), 'fuera de la muestra influye'
    for a in ('ward',):
        assert Q.ajustar(X[idx], a, 3)[0].tolist() == Q.ajustar(X2[idx], a, 3)[0].tolist()
    pr = (AQUI / 'ejecutar_principal_37b.py').read_text(encoding='utf-8')
    assert 'procedencia' not in pr
    aj = pd.read_csv(Q.A37 / 'sensibilidades' / 'S-TRA' / 'P1' / 'coordenadas_ajuste.csv', dtype={'participante_id': str}).set_index('participante_id')
    prx = pd.read_csv(Q.A37 / 'sensibilidades' / 'S-TRA' / 'P1' / 'coordenadas_proyeccion.csv', dtype={'participante_id': str}).set_index('participante_id')
    assert not set(aj.index) & set(prx.index)
    return 'Cambiar a quienes quedan fuera del subconjunto no altera las etiquetas; la ejecución principal no lee la procedencia; ajuste y proyección no comparten filas. Límite: la reducción se ajustó con las 529, como declara el protocolo'


@prueba(16, 'Separación entre ajuste y proyección')
def p16():
    s = tabla('sensibilidades/comparacion_sensibilidades.csv')
    esperado = {'S-TRA': (507, 22), 'S-CUI': (508, 21), 'S-EJE': (454, 75)}
    for sid, g in s.groupby('sensibilidad'):
        na, np_ = esperado.get(sid, (529, 0))
        assert (g['filas_ajuste'] == na).all() and (g['filas_proyeccion'] == np_).all(), sid
        assert g['ari_proyeccion'].notna().all() == (np_ > 0) and (g['ari_proyeccion'].isna().all() == (np_ == 0)), sid
    e = pd.read_csv(B / 'sensibilidades' / 'etiquetas' / 'S-TRA_P1.csv', dtype={'participante_id': str}).set_index('participante_id')
    aj = pd.read_csv(Q.A37 / 'sensibilidades' / 'S-TRA' / 'P1' / 'coordenadas_ajuste.csv', dtype={'participante_id': str}).set_index('participante_id')
    pr = pd.read_csv(Q.A37 / 'sensibilidades' / 'S-TRA' / 'P1' / 'coordenadas_proyeccion.csv', dtype={'participante_id': str}).set_index('participante_id')
    col = 'P1_c05_km_k3'
    cols = [f'C{i + 1}' for i in range(5)]
    Xa = aj[cols].to_numpy()
    la = e.loc[aj.index, col].to_numpy()
    protos = np.vstack([Xa[la == g].mean(axis=0) for g in range(3)])
    assert np.abs(Q.asignar(protos, pr[cols].to_numpy())[0] - e.loc[pr.index, col].to_numpy()).max() == 0
    return 'Filas 507/22, 508/21 y 454/75; las demás, 529/0. Las proyectadas se asignan con prototipos calculados solo con las filas de ajuste'


@prueba(17, 'Conservación de parámetros')
def p17():
    sello = json.loads((B / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    assert Q.sha(B / 'protocolo' / sello['archivo']) == sello['sha256']
    t = tabla('resultados/configuraciones.csv')
    assert len(t) == 420 and (t['estado'] == 'completa').all() and t['config'].is_unique
    assert t.groupby('metodo').size().to_dict() == {'FAMD': 196, 'PCA': 196, 'Sin reducción': 28}
    for c in cfgs():
        assert lote(c['config'])['huella_protocolo'] == sello['sha256'], c['config']
    n = (AQUI / 'nucleo_37b.py').read_text(encoding='utf-8')
    assert "n_init=50, random_state=semilla, algorithm='lloyd'" in n and "linkage='ward', metric='euclidean'" in n and 'SEMILLA = 42' in n and 'N_REP = 30' in n and 'N_NULA = 20' in n and 'N_SUB = 423' in n
    pro = json.loads((B / 'prototipos' / 'prototipos_F1_km.json').read_text(encoding='utf-8'))
    assert np.array(pro['F1_c05_km_k3']['centroides']).shape == (3, 5) and pro['F1_c05_km_k3']['centroides'] == lote('F1_c05_km_k3')['centroides']
    en = json.loads((B / 'resultados' / 'entorno.json').read_text(encoding='utf-8'))
    assert en['semilla'] == 42 and 'scikit_learn' in en
    return '420 configuraciones con la huella del protocolo sellado; parámetros, centroides y versiones guardados'


@prueba(18, 'Asignación por centroides')
def p18():
    t = tabla('prototipos/evaluacion_asignacion.csv')
    km = t[t['algoritmo'] == 'km']
    assert (km['acuerdo_prototipo_pct'] == 100).all(), km['acuerdo_prototipo_pct'].min()
    p = Q.tabla_general()
    nueva = {**p.iloc[10].to_dict(), 'imc': '33.5', 'edad': '58'}
    caso = pd.DataFrame([nueva], index=['nueva'])
    for e in Q.ESPACIOS:
        Z = Q.TF.Transformador.cargar(Q.F36 / 'artefactos' / e).transformar(caso)[0]
        F = Q.R.proyectar(Q.R.cargar(Q.A37 / 'artefactos' / e / 'modelo.json'), Z.to_numpy(), 5)
        d = lote(f'{e}_c05_km_k3')
        et, d1, d2, mar = Q.asignar(d['centroides'], F)
        manual = np.linalg.norm(F - np.array(d['centroides']), axis=1)
        assert et[0] == manual.argmin() and abs(d1[0] - manual.min()) < 1e-12 and abs(mar[0] - (1 - d1[0] / d2[0])) < 1e-12 and 0 <= mar[0] <= 1
        lote2 = Q.asignar(d['centroides'], np.vstack([F, X_de(f'{e}_c05_km_k3')[:3]]))
        assert lote2[0][0] == et[0], 'depende de otras filas'
    return 'K-means 100 % en las 210; flujo completo con un caso inventado en los 4 escenarios; distancia y margen coinciden con el cálculo manual'


@prueba(19, 'Prototipos del aglomerativo')
def p19():
    t = tabla('prototipos/evaluacion_asignacion.csv')
    w = t[t['algoritmo'] == 'ward'].set_index('config')
    for c in [x for x in MUESTRA if '_ward_' in x]:
        d, X = lote(c), X_de(c)
        l = np.array(d['etiquetas'])
        protos = np.vstack([X[l == g].mean(axis=0) for g in range(d['k'])])
        assert np.abs(protos - np.array(d['centroides'])).max() < 1e-12, c
        et = np.linalg.norm(X[:, None] - protos[None], axis=2).argmin(axis=1)
        assert abs(100 * (et == l).mean() - w.loc[c, 'acuerdo_prototipo_pct']) < 1e-9 and abs(ari_propio(l, et) - w.loc[c, 'acuerdo_prototipo_ari']) < 1e-10, c
    assert len(w) == 210 and w['acuerdo_prototipo_pct'].between(0, 100).all()
    assert (w['acuerdo_prototipo_pct'] < 100).any(), 'se esperaba al menos un desacuerdo'
    return f'Recalculado; acuerdo entre {w["acuerdo_prototipo_pct"].min():.1f} % y {w["acuerdo_prototipo_pct"].max():.1f} %: no se asume perfecto'


@prueba(20, 'Integridad de los archivos históricos')
def p20():
    sys.path.insert(0, str(Q.ANALISIS / 'revision_correctiva_fase34'))
    from manifiesto import huella
    m = pd.read_csv(Q.A37 / 'integridad' / 'manifiesto_final_37A.csv')
    d = [r for r, h in zip(m['ruta'], m['sha256']) if not (Q.A37 / r).exists() or Q.sha(Q.A37 / r) != h]
    assert not d, d[:4]
    extra = [p for p in Q.A37.rglob('*') if p.is_file() and p.name != 'manifiesto_final_37A.csv' and p.relative_to(Q.A37).as_posix() not in set(m['ruta'])]
    assert not extra, extra[:4]
    f = pd.read_csv(Q.F36 / 'integridad' / 'manifiesto_final_36B.csv', encoding='utf-8')
    d = [r for r, h in zip(f['ruta'], f['sha256']) if not (Q.F36 / r).exists() or huella(Q.F36 / r) != h]
    assert not d, d[:4]
    extra = [p for p in Q.F36.rglob('__pycache__')]
    c = pd.read_csv(Q.ANALISIS / 'cierre_fases_34_35' / 'integridad' / 'manifiesto_despues.csv', encoding='utf-8')
    d = [r for r, h in zip(c['ruta'], c['sha256']) if not (Q.RAIZ / r).exists() or huella(Q.RAIZ / r) != h]
    assert not d, d[:4]
    return f'{len(m)} de la Fase 37A (y sin archivos nuevos), {len(f)} de la Fase 36 y {len(c)} del cierre 34-35, sin cambios'


@prueba(21, 'Sin commits, push ni cambios en la plataforma')
def p21():
    def git(*a):
        return subprocess.run(['git', *a], cwd=Q.RAIZ, capture_output=True, text=True, encoding='utf-8').stdout.rstrip()
    assert git('rev-parse', '--short', 'HEAD').strip() == '745d689' and not git('diff', '--cached', '--name-only')
    seguidos = [x[3:] for x in git('status', '--short').splitlines() if not x.startswith('??')]
    assert len(seguidos) == 8 and all(x.startswith('analisis/') for x in seguidos), seguidos
    assert not [x for x in git('status', '--short').splitlines() if ' src/' in x or 'requirements' in x]
    return 'HEAD 745d689; nada preparado; los mismos 8 archivos seguidos con cambios previos; src/ y dependencias sin cambios'


@prueba(22, 'Reproducción completa en otra carpeta y con otro número de procesos')
def p22():
    if not REPRODUCIR:
        raise RuntimeError('NO EJECUTADA')
    with tempfile.TemporaryDirectory() as t:
        s = Path(t)
        for prog, extra in (('ejecutar_principal_37b.py', []), ('ejecutar_nula_37b.py', ['--replicas', '0,7'])):
            r = subprocess.run([sys.executable, str(AQUI / prog), '--procesos', '5', '--salida', str(s), *extra], capture_output=True, text=True, encoding='utf-8', errors='replace', stdin=subprocess.DEVNULL)
            assert r.returncode == 0, r.stdout[-300:] + r.stderr[-300:]
        difieren = [c['config'] for c in cfgs() if json.loads((s / 'resultados' / 'lotes' / f'{c["config"]}.json').read_text(encoding='utf-8')) != _lote(c['config'])]
        assert not difieren, difieren[:4]
        for x in (0, 7):
            assert Q.sha(s / 'referencia_nula' / 'lotes' / f'replica_{x:02d}.csv') == Q.sha(B / 'referencia_nula' / 'lotes' / f'replica_{x:02d}.csv'), x
    return 'Las 420 configuraciones con todos sus datos, y 2 réplicas nulas, idénticas con 5 procesos en lugar de 10'


@prueba(23, 'Tablas consolidadas iguales a los lotes')
def p23():
    t = tabla('resultados/tabla_completa_configuraciones.csv').set_index('config')
    e = tabla('estabilidad/ari_por_remuestreo.csv')
    assert len(t) == 420 and len(e) == 420 * 30
    for c in cfgs():
        d = lote(c['config'])
        assert abs(t.loc[c['config'], 'silueta'] - d['silueta']) < 1e-12 and abs(t.loc[c['config'], 'ari_entre_media'] - d['ari_entre_media']) < 1e-12, c['config']
    s = tabla('sensibilidades/comparacion_sensibilidades.csv')
    assert len(s) == 3332 and s[['sensibilidad', 'base']].drop_duplicates().shape[0] == 34
    return '420 configuraciones, 12.600 valores de ARI y 3.332 ajustes de sensibilidad'


@prueba(24, 'Comparación con la nula y lista para la Fase 37C según el protocolo')
def p24():
    t = tabla('resultados/tabla_completa_configuraciones.csv').set_index('config')
    n = tabla('referencia_nula/metricas_por_replica.csv')
    assert n['tam_min'].min() >= 1
    for m, sen in (('silueta', 1), ('ari_entre_media', 1), ('davies_bouldin', -1)):
        maximo = (n.pivot(index='replica', columns='config', values=m) * sen).max()
        assert (((t[m] * sen) > maximo.reindex(t.index)) == t[f'{m}_supera_todas'].astype(bool)).all(), m
    regla = (t['ari_completo_media'] >= 0.65) & (t['ari_entre_media'] >= 0.65) & t['silueta_supera_todas'].astype(bool) & t['ari_entre_media_supera_todas'].astype(bool)
    assert (regla == t['lista_37C'].astype(bool)).all()
    return f'{int(regla.sum())} configuraciones cumplen la regla, recalculada desde las tablas; sin puntuación compuesta'


@prueba(25, 'Sin GMM, reglas de asociación ni selección de un ganador')
def p25():
    for s in AQUI.glob('*.py'):
        if s.name in ('pruebas_37b.py', 'control_mutaciones_37b.py', 'generar_informes_37b.py'):
            continue
        c = s.read_text(encoding='utf-8')
        assert not re.search(r'GaussianMixture|apriori|association_rules|fpgrowth', c), s.name
    assert not [p for p in B.rglob('*') if p.is_file() and re.search(r'ganador|modelo_definitivo|perfil_', p.name, re.I)]
    assert sorted(x.name for x in Q.FASE37.iterdir() if x.is_dir()) == ['37A_reduccion', '37B_clustering']
    return 'Sin GMM ni reglas; sin archivos de modelo definitivo; la Fase 37C no se inició'


@prueba(26, 'Correspondencia entre resultados y gráficos')
def p26():
    import graficos_37b as G
    import matplotlib.pyplot as plt
    t = tabla('resultados/tabla_completa_configuraciones.csv')
    fig = G.f01_silueta()
    ax = fig.axes[0]
    x = t[(t['espacio'] == 'P1') & (t['algoritmo'] == 'km') & (t['componentes'] == 2)].sort_values('k')
    assert np.abs(np.asarray(ax.lines[0].get_ydata()) - x['silueta'].to_numpy()).max() < 1e-12
    plt.close(fig)
    fig = G.f06_estabilidad()
    mat = t[(t['espacio'] == 'P1') & (t['algoritmo'] == 'km')].pivot(index='componentes', columns='k', values='ari_entre_media').to_numpy()
    assert np.abs(np.asarray(fig.axes[0].images[0].get_array()) - mat).max() < 1e-12
    plt.close(fig)
    fig = G.f04_tamanos()
    x = t[t['algoritmo'] == 'km'].groupby('k')['tam_min_pct'].min()
    assert np.abs(np.asarray(fig.axes[0].lines[0].get_ydata()) - x.to_numpy()).max() < 1e-12
    plt.close(fig)
    assert len(list((B / 'figuras').glob('*.png'))) >= 10
    fuentes = (AQUI / 'graficos_37b.py').read_text(encoding='utf-8')
    assert not re.search(r'mrs|severo|severidad', fuentes, re.I)
    return f'3 figuras comparadas punto a punto con sus tablas; {len(list((B / "figuras").glob("*.png")))} PNG; sin color por severidad'


def main():
    global REPRODUCIR
    ap = argparse.ArgumentParser()
    ap.add_argument('--sin-reproducir', action='store_true')
    REPRODUCIR = not ap.parse_args().sin_reproducir
    filas = []
    for n, nombre, f in PRUEBAS:
        try:
            det, ok = f(), 'OK'
        except Exception as ex:  # noqa: BLE001
            ok = 'NO EJECUTADA' if str(ex) == 'NO EJECUTADA' else 'FALLA'
            det = f'{type(ex).__name__}: {ex} | {traceback.format_exc(limit=2)[-260:]}'
        filas.append({'numero': n, 'prueba': nombre, 'resultado': ok, 'detalle': det})
        print(n, ok, '|', nombre, '|', str(det)[:230], flush=True)
    t = pd.DataFrame(filas)
    (B / 'pruebas').mkdir(exist_ok=True)
    t.to_csv(B / 'pruebas' / 'resultados_pruebas.csv', index=False, encoding='utf-8', lineterminator='\n')
    print(f'{(t["resultado"] == "OK").sum()} de {len(t)} pruebas superadas')
    return 0 if (t['resultado'] == 'OK').all() else 1


if __name__ == '__main__':
    raise SystemExit(main())
