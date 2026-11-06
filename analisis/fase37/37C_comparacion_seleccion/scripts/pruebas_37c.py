"""
Fase 37C: pruebas de la Parte 12 del encargo. Cada una registra su resultado real; ninguna se declara superada sin ejecutarse.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/pruebas_37c.py
Las funciones de acceso (`tabla`, `cadena`, ...) son el punto donde control_mutaciones_37c.py introduce errores deliberados.
"""
import re
import subprocess
import sys
import tempfile
import traceback
from functools import lru_cache
from math import comb
from pathlib import Path

import nucleo_37c as N
import numpy as np
import pandas as pd
import referencia_correlacionada as RC
from sklearn.metrics import adjusted_rand_score

Q = N.Q
B = N.BASE
PRUEBAS = []
MUESTRA = ['F2_c03_km_k3', 'P2_c12_km_k4', 'P1_c05_km_k2', 'F1_c03_ward_k4', 'P2_c05_ward_k3']
TERMINOS = ('mrs', 'severo', 'severidad', 'sintoma_')
ORIGEN_HEAD = '745d689'


def prueba(n, nombre):
    def deco(f):
        PRUEBAS.append((n, nombre, f))
        return f
    return deco


@lru_cache(maxsize=None)
def _csv(r):
    return pd.read_csv(B / r, encoding='utf-8', dtype={'participante_id': str})


def tabla(r):
    return _csv(r).copy()


@lru_cache(maxsize=None)
def _cadena():
    return N.Cadena()


def cadena():
    return _cadena()


def calibrada(cad, e, t, idx, modo='consecutivo'):
    return cad.calibrada(e, t, idx, modo)


def coords_cadena(Z, idx):
    return N.coordenadas_cadena(Z, idx)


def ari(a, b):
    return adjusted_rand_score(a, b)


def pares(todas, usadas):
    return N.ari_pares_compartidos(todas, usadas)


@lru_cache(maxsize=None)
def _copula():
    cad = cadena()
    return RC.Copula(cad.tabla, cad.defs['P1'][0], Q.MADRES, contraccion=N.leer_json(B / 'referencias_nulas' / 'contraccion_elegida.json')['alfa_elegido'])


def copula():
    return _copula()


def replica(r):
    return copula().muestrear(np.random.default_rng(np.random.SeedSequence([Q.SEMILLA, 3700, r])))


def manifiesto_filas(nombre, base, ruta):
    m = pd.read_csv(Path(base) / ruta)
    return [(r, h) for r, h in zip(m['ruta'], m['sha256'])]


def head():
    return subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=N.RAIZ, capture_output=True, text=True).stdout.strip()


def ramas_remotas():
    return subprocess.run(['git', 'branch', '-r'], cwd=N.RAIZ, capture_output=True, text=True).stdout


def estado_git():
    return subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all', '--', '.', ':!analisis'], cwd=N.RAIZ, capture_output=True, text=True).stdout


def ari_propio(a, b):
    a, b = np.asarray(a), np.asarray(b)
    t = pd.crosstab(a, b).to_numpy()
    s_ij = sum(comb(int(x), 2) for x in t.ravel())
    s_a = sum(comb(int(x), 2) for x in t.sum(axis=1))
    s_b = sum(comb(int(x), 2) for x in t.sum(axis=0))
    esperado = s_a * s_b / comb(int(t.sum()), 2)
    return (s_ij - esperado) / ((s_a + s_b) / 2 - esperado)


def silueta_propia(X, l):
    D = np.sqrt(((X[:, None] - X[None]) ** 2).sum(axis=2))
    s = np.zeros(len(X))
    for i in range(len(X)):
        a = D[i, l == l[i]].sum() / max((l == l[i]).sum() - 1, 1)
        b = min(D[i, l == g].mean() for g in np.unique(l) if g != l[i])
        s[i] = (b - a) / max(a, b)
    return s


# ---------------------------------------------------------------- 1 a 4
@prueba(1, 'Integridad de resultados históricos: manifiestos de las Fases 34-35, 36, 37A y 37B')
def p01():
    fuentes = [('fase36', N.F36, 'integridad/manifiesto_final_36B.csv'), ('37A', N.A37, 'integridad/manifiesto_final_37A.csv'), ('37B', N.B37, 'integridad/manifiesto_final_37B.csv'), ('cierre', N.RAIZ / 'analisis' / 'cierre_fases_34_35', 'integridad/manifiesto_despues.csv')]
    total = 0
    for nombre, base, ruta in fuentes:
        filas = manifiesto_filas(nombre, base, ruta)
        raiz_rel = N.RAIZ if nombre == 'cierre' else base
        for r, h in filas:
            p = Path(raiz_rel) / r
            if not p.exists():
                p = Path(base) / r
            if not p.exists():
                raise AssertionError(f'{nombre}: falta {r}')
            assert N.sha(p) == h, f'{nombre}: cambió {r}'
        total += len(filas)
    assert total > 2000
    return f'{total} archivos iguales a sus manifiestos'


@prueba(2, 'Identificadores: 529 únicos y en el mismo orden en etiquetas, coordenadas y Cadena')
def p02():
    ids = pd.read_csv(N.F36 / 'matrices' / 'identificadores.csv', dtype=str)['participante_id'].tolist()
    assert len(ids) == 529 and len(set(ids)) == 529
    et = tabla_etiquetas()
    assert et.index.tolist() == ids, 'etiquetas en otro orden'
    assert cadena().ids == ids
    assert cadena().tabla.index.tolist() == ids
    assert Q.coordenadas('F2', 3).index.tolist() == ids
    return '529 identificadores'


@lru_cache(maxsize=None)
def _etq():
    return N.etiquetas_37b()


def tabla_etiquetas():
    return _etq()


@prueba(3, 'Listas A y B coinciden con los archivos originales')
def p03():
    t = N.tabla_37b()
    a = tabla('candidatos/lista_A_completa.csv')
    assert sorted(a['config']) == sorted(t.index[t['lista_37C']]), 'Lista A distinta de la tabla de la Fase 37B'
    assert len(a) == 108
    assert int(a['senal_eje1'].sum()) == 57 and int(a['senal_repeticiones_inestables'].sum()) == 52
    b = tabla('candidatos/lista_B_exploratoria.csv')
    assert b['config'].tolist() == N.lista_b(), 'Lista B distinta del documento'
    assert len(b) == 15 and set(b['config']) <= set(a['config'])
    return '108 (57 y 52) y 15, leídas de sus originales'


@prueba(4, 'Ausencia de variables MRS en entradas y salidas')
def p04():
    malas = []
    for p in sorted(B.rglob('*.csv')):
        if 'lotes' in p.parts:
            continue
        cab = pd.read_csv(p, nrows=0).columns
        for c in cab:
            if any(x in str(c).lower() for x in TERMINOS):
                malas.append((p.name, c))
    cad = cadena()
    for c in list(cad.tabla.columns) + list(cad.celdas['variable'].unique()):
        if any(x in str(c).lower() for x in TERMINOS):
            malas.append(('entrada', c))
    for x in tabla('referencias_nulas/propiedades_spearman_pares_alpha_0.05.csv')[['a', 'b']].to_numpy().ravel():
        if any(t in str(x).lower() for t in TERMINOS):
            malas.append(('copula', x))
    assert not malas, f'Columnas prohibidas: {malas[:4]}'
    leidos = pd.read_csv(B / 'integridad' / 'archivos_leidos.csv')['archivo_leido'].astype(str)
    prohibidos = [x for x in leidos if x.startswith('datos/') or 'verdad' in x or 'bitacora' in x]
    assert not prohibidos, prohibidos
    return f'Sin columnas MRS; {len(leidos)} archivos leídos, ninguno de datos/'


# ---------------------------------------------------------------- 5 a 9
@prueba(5, 'Reproducibilidad: repetir la cadena en otra carpeta da las mismas etiquetas')
def p05():
    import estabilidad_37c as E
    E.CAD = cadena()
    subs = Q.subconjuntos()
    for base, nivel, r in (('F2', 'E3', 3), ('P2', 'E2', 7), ('P1', 'E1', 0)):
        idx = subs[r]
        guardado = np.load(B / 'estabilidad' / 'lotes' / f'{base}_{nivel}_r{r:02d}.npz')
        Z = cadena().matriz_nivel(base, nivel, idx).to_numpy()
        F, _ = N.coordenadas_cadena(Z, idx)
        for c in guardado.files[:6]:
            i = N.info_config(c)
            l = E.ajustar_config(F, Z, idx, i, r)[0]
            assert (l == guardado[c]).all(), f'{c} {nivel} r{r} no se reproduce'
    return '18 particiones recalculadas son idénticas a las guardadas'


@prueba(6, 'Sin contaminación: cambiar a las participantes no usadas no altera parámetros, reducción ni etiquetas de la submuestra')
def p06():
    cad = cadena()
    idx = Q.subconjuntos()[5]
    resto = np.setdiff1d(np.arange(Q.N), idx)
    for e in ('F2', 'P2'):
        t = cad.tabla.copy()
        Z1 = calibrada(cad, e, t, idx).to_numpy()
        F1, m1 = coords_cadena(Z1, idx)
        t2 = t.copy()
        t2.loc[t2.index[resto], 'edad'] = '65'
        t2.loc[t2.index[resto], 'trabaja_actualmente'] = 'False'
        t2.loc[t2.index[resto], 'tiene_actividad_sexual'] = 'NO'
        t2.loc[t2.index[resto], 'horas_sedentarismo'] = '20'
        Z2 = calibrada(cad, e, t2, idx).to_numpy()
        F2, m2 = coords_cadena(Z2, idx)
        assert np.allclose(Z1[idx], Z2[idx], atol=1e-12), 'Los parámetros usan filas no usadas'
        assert np.allclose(m1['componentes'], m2['componentes'], atol=1e-9), 'La reducción usa filas no usadas'
        a = Q.ajustar(F1[idx][:, :5], 'km', 3, 11)[0]
        b = Q.ajustar(F2[idx][:, :5], 'km', 3, 11)[0]
        assert (a == b).all(), 'Las etiquetas de la submuestra dependen de las no usadas'
    # E3: la imputación tampoco mira fuera de la submuestra
    v1 = cad.tabla_imputada(idx)[1]
    cad2_valor = cad.valor.copy()
    cad.valor.iloc[resto, cad.valor.columns.get_loc('tiene_actividad_sexual')] = 'SI'
    try:
        v2 = cad.tabla_imputada(idx)[1]
    finally:
        cad.valor = cad2_valor
    assert v1 == v2, 'La imputación reestimada usa filas fuera de la submuestra'
    return 'Parámetros, reducción, etiquetas e imputaciones idénticos'


@prueba(7, 'Reajuste correcto de PCA y FAMD: con las 529 reproduce la Fase 37A; con la submuestra usa solo sus filas')
def p07():
    cad = cadena()
    todas = np.arange(Q.N)
    for e in Q.ESPACIOS:
        Z = cad.congelada(e).to_numpy()
        F, m = coords_cadena(Z, todas)
        h = Q.coordenadas(e, 20).to_numpy()
        assert np.abs(F[:, :20] - h).max() < 1e-8, f'{e}: no reproduce las coordenadas de la Fase 37A'
        idx = Q.subconjuntos()[2]
        Fs, ms = coords_cadena(Z, idx)
        assert ms['n_ajuste'] == 423
        centrado = Z[idx] - Z[idx].mean(axis=0)
        s = np.linalg.svd(centrado, compute_uv=False) ** 2 / 423
        assert np.allclose(s[:10], np.array(ms['valores_propios'])[:10], atol=1e-8), f'{e}: valores propios no salen de la submuestra'
        assert np.abs(np.array(ms['media']) - Z[idx].mean(axis=0)).max() < 1e-12
    return 'Reproducción con 1e-8; ajuste en submuestra comprobado con SVD independiente'


@prueba(8, 'Recalibración solo dentro de la muestra: con las 529 da la matriz histórica, y con la submuestra usa sus medias y proporciones')
def p08():
    cad = cadena()
    for e in Q.ESPACIOS:
        Z = calibrada(cad, e, cad.tabla, np.arange(Q.N)).to_numpy()
        H = cad.congelada(e).to_numpy()
        assert np.abs(Z - H).max() < 1e-10, f'{e}: recalibrar con las 529 no reproduce la matriz'
    idx = Q.subconjuntos()[4]
    Z = calibrada(cad, 'P2', cad.tabla, idx)
    edad = cad.tabla['edad'].astype(float).to_numpy()
    esperado = (edad - edad[idx].mean()) / edad[idx].std()
    assert np.allclose(Z['edad'].to_numpy(), esperado, atol=1e-10), 'edad no usa la media de la submuestra'
    assert abs(Z['edad'].to_numpy()[idx].mean()) < 1e-10
    Zf = calibrada(cad, 'F1', cad.tabla, idx)
    imc = pd.to_numeric(cad.tabla['imc'], errors='coerce').to_numpy()
    obs = imc[idx][~np.isnan(imc[idx])]
    z = Zf['imc'].to_numpy()
    assert np.allclose(z[~np.isnan(imc)], (imc[~np.isnan(imc)] - obs.mean()) / obs.std(), atol=1e-10), 'IMC no usa sus observadas de la submuestra'
    assert np.allclose(z[np.isnan(imc)], 0, atol=1e-10)
    return 'Reproducción histórica con 1e-10; medias e IMC de la submuestra'


@prueba(9, 'Proyección sin información futura: una fila a la vez da lo mismo que el lote')
def p09():
    cad = cadena()
    idx = Q.subconjuntos()[1]
    par_tr = 'P2'
    Z = calibrada(cad, par_tr, cad.tabla, idx).to_numpy()
    F, m = coords_cadena(Z, idx)
    tr = N.TF.Transformador.cargar(N.F36 / 'artefactos' / 'F2')
    lote = tr.transformar(cad.tabla)[0].to_numpy()
    modelo = N.R.cargar(N.A37 / 'artefactos' / 'F2' / 'modelo.json')
    Fl = N.R.proyectar(modelo, lote, 3)
    l = tabla_etiquetas()['F2_c03_km_k3'].to_numpy()
    protos = Q.prototipos(Fl, l, 3)
    for i in (0, 17, 250, 528):
        una = tr.transformar(cad.tabla.iloc[[i]])[0].to_numpy()
        assert np.abs(una[0] - lote[i]).max() < 1e-12, 'Transformar una fila cambia el resultado'
        f = N.R.proyectar(modelo, una, 3)
        assert np.abs(f[0] - Fl[i]).max() < 1e-12
        assert Q.asignar(protos, f)[0][0] == Q.asignar(protos, Fl)[0][i]
    return 'Cuatro participantes: transformar, proyectar y asignar no dependen de las demás'


# ---------------------------------------------------------------- 10 a 13
@prueba(10, 'ARI correcto: implementación propia, invariante al nombre de los grupos')
def p10():
    et = tabla_etiquetas()
    for c in MUESTRA:
        l = et[c].to_numpy()
        otro = np.roll(l, 7)
        assert abs(ari(l, otro) - ari_propio(l, otro)) < 1e-10, 'ARI distinto del propio'
        perm = (l + 1) % (l.max() + 1)
        assert abs(ari(l, perm) - 1) < 1e-12, 'ARI depende del nombre de los grupos'
    r = pd.read_csv(B / 'estabilidad' / 'ari_por_repeticion.csv')
    x = r[(r['config'] == 'F2_c03_km_k3') & (r['nivel'] == 'E3') & (r['repeticion'] == 3)].iloc[0]
    idx = Q.subconjuntos()[3]
    l = np.load(B / 'estabilidad' / 'lotes' / 'F2_E3_r03.npz')['F2_c03_km_k3']
    assert abs(x['ari_completo'] - ari_propio(et['F2_c03_km_k3'].to_numpy()[idx], l[idx])) < 1e-10, 'ari_completo guardado no coincide'
    return 'Coincide con implementación propia y con el valor guardado'


@prueba(11, 'Comparaciones sobre participantes compartidas')
def p11():
    subs = Q.subconjuntos()
    usadas = np.zeros((30, Q.N), bool)
    for r, idx in enumerate(subs):
        usadas[r, idx] = True
    assert (usadas.sum(axis=1) == 423).all()
    assert (np.array([(usadas[i] & usadas[j]).sum() for i in range(30) for j in range(i + 1, 30)]) >= 317).all()
    for c, base in (('P2_c12_km_k4', 'P2'), ('F2_c03_km_k3', 'F2')):
        todas = np.vstack([np.load(B / 'estabilidad' / 'lotes' / f'{base}_E3_r{r:02d}.npz')[c] for r in range(30)])
        directo = []
        for i in range(30):
            for j in range(i + 1, 30):
                comunes = np.intersect1d(subs[i], subs[j])
                directo.append(ari_propio(todas[i][comunes], todas[j][comunes]))
        guardado = tabla('estabilidad/estabilidad_por_nivel.csv').query('config == @c and nivel == "E3"')['ari_entre_media'].iloc[0]
        assert abs(np.mean(pares(todas, usadas)) - np.mean(directo)) < 1e-9, 'Los pares no usan solo a las compartidas'
        assert abs(guardado - np.mean(directo)) < 1e-9, 'La media guardada no coincide'
        assert len(directo) == 435
    return '435 pares, intersección de al menos 317, recalculados de forma independiente'


@prueba(12, 'Referencia nula reproducible y bien definida')
def p12():
    a, b, c = replica(4), replica(4), replica(5)
    assert a.equals(b), 'Misma semilla, tablas distintas'
    assert not a.equals(c), 'Semillas distintas, tablas iguales'
    assert list(a.columns) == list(cadena().tabla.columns)
    # Una réplica guardada se reproduce
    import nula_37c as NU
    g = tabla('referencias_nulas/lotes/replica_004.csv').set_index('config')
    esp = NU.espacios(a)
    for cc in ('F2_c03_km_k3', 'P2_c12_km_k4'):
        i = N.info_config(cc)
        X = NU.x_de(esp, i)
        s = Q.calidad(X, Q.ajustar(X, i['algoritmo'], i['k'])[0])[0]['silueta']
        assert abs(s - g.loc[cc, 'silueta']) < 1e-9, 'La réplica guardada no se reproduce'
    h = N.leer_json(B / 'referencias_nulas' / 'parametros_copula_alpha_0.05.json')
    assert 'unimodal' in h['hipotesis']
    assert len(pd.read_csv(B / 'referencias_nulas' / 'metricas_por_replica.csv')['replica'].unique()) == 100
    return 'Semillas, réplica guardada e hipótesis comprobadas; 100 réplicas'


@prueba(13, 'La referencia correlacionada conserva lo que declara')
def p13():
    obs = cadena().tabla
    cop = copula()
    S_ = []
    for r in range(20):
        t = replica(r)
        for v in obs.columns:
            assert sorted(t[v].astype(str)) == sorted(obs[v].astype(str)), f'Marginal distinta en {v}'
        for h, m in Q.MADRES.items():
            assert ((t[h].astype(str) == '') == (t[m] == 'NO')).all(), f'Lógica de salto rota en {h}'
        S_.append(cop.spearman_tabla(t))
    iu = np.triu_indices(len(cop.nombres), 1)
    err = np.abs(np.mean(S_, axis=0) - cop.objetivo)[iu].max()
    assert err <= 0.05, f'Error de Spearman {err:.3f}'
    p = N.leer_json(B / 'referencias_nulas' / 'propiedades_referencia.json')
    assert all(p['criterios'].values()), 'Criterio de validez no cumplido'
    assert max(p['error_relativo_vp_P1_1a3'] + p['error_relativo_vp_F1_1a3']) < 0.10
    c = N.leer_json(B / 'referencias_nulas' / 'controles_sinteticos.json')
    assert all(c.values()), f'Controles sintéticos: {c}'
    return f'Marginales exactas, salto íntegro, Spearman {err:.3f}, controles sintéticos correctos'


# ---------------------------------------------------------------- 14 a 18
@prueba(14, 'Separación entre lo confirmatorio y lo exploratorio')
def p14():
    b = tabla('candidatos/lista_B_exploratoria.csv')
    assert b['caracter'].str.contains('Exploratoria').all(), 'Lista B sin rótulo exploratorio'
    prot = (B / 'protocolo' / '01_protocolo_37C.md').read_text(encoding='utf-8')
    for e in ('Previo-D13', 'Previo-37B', 'Encargo-37C', 'Propuesta-37C', 'Exploratoria permanentemente'):
        assert e in prot, f'Falta la etiqueta {e}'
    ctr = tabla('referencias_nulas/contraste_sin_contraccion.csv')
    assert ctr['nota'].str.contains('No válida').all()
    enm = (B / 'protocolo' / '02_enmienda_referencia_nula.md').read_text(encoding='utf-8')
    assert 'exploratorio' in enm
    return 'Lista B, enmienda y contraste rotulados; etiquetas de origen en el protocolo'


@prueba(15, 'Trazabilidad de los cambios de codificación')
def p15():
    cad = cadena()
    for e in Q.ESPACIOS:
        hist = pd.read_csv(N.F36 / 'sensibilidades' / 'S-ORD' / e / 'matriz.csv')
        Z = cad.matriz_nivel(e, 'E1', None, 'ridit')
        assert list(hist.columns) == list(Z.columns)
        assert np.abs(hist.to_numpy() - Z.to_numpy()).max() < 1e-10, f'{e}: ridit no reproduce S-ORD de la Fase 36'
    Zn = cad.matriz_nivel('P2', 'E1', None, 'normal')
    ord_z = [d['variable'] for d in cad.defs['P2'][0] if d['tipo'] == 'ordinal']
    assert np.abs(Zn[ord_z].mean()).max() < 1e-10 and np.abs(Zn[ord_z].std(ddof=0) - 1).max() < 1e-10, 'Puntuaciones normales mal escaladas'
    assert np.corrcoef(Zn['carnes_semana'], cad.congelada('P2')['carnes_semana'])[0, 1] > 0.8
    return 'Ridit reproduce la Fase 36 con 1e-10; puntuaciones normales con media 0 y DE 1; sin artefactos que la reemplacen'


@prueba(16, 'Tamaños y métricas consistentes')
def p16():
    t = N.tabla_37b()
    et = tabla_etiquetas()
    for c in MUESTRA:
        l = et[c].to_numpy()
        assert np.bincount(l).sum() == 529
        assert np.bincount(l).min() == t.loc[c, 'tam_min'], 'tam_min distinto'
        i = N.info_config(c)
        X = Q.coordenadas(i['espacio'], i['componentes']).to_numpy()
        assert abs(silueta_propia(X, l).mean() - t.loc[c, 'silueta']) < 1e-9, 'silueta distinta'
    r = tabla('estabilidad/tamanos_por_repeticion.csv')
    assert (r['tamanos_submuestra'].map(lambda s: sum(map(int, s.split()))) == 423).all(), 'Una repetición no suma 423'
    d = tabla('sensibilidades/s_ord/descomposicion.csv').set_index('config')
    assert (d['tamanos_base'].map(lambda s: sum(map(int, s.split()))) == 529).all()
    ev = tabla('seleccion/evaluacion_por_etapa.csv')
    x = ev[(ev['criterio'] == 'Grupo menor')].set_index('config')['valor']
    assert all(x[c] == t.loc[c, 'tam_min'] for c in x.index), 'Selección con otro tamaño'
    return 'Tamaños suman 529 y 423; siluetas recalculadas'


@prueba(17, 'Ausencia de selección por MRS: el código de decisión no lee nada relacionado')
def p17():
    for f in ('seleccion_37c.py', 'interpretabilidad_37c.py', 'asignacion_37c.py', 'estabilidad_37c.py', 's_ord_37c.py', 'sensibilidades_37c.py', 'referencia_correlacionada.py'):
        texto = (N.AQUI / f).read_text(encoding='utf-8')
        sin_docs = re.sub(r'""".*?"""', '', texto, flags=re.S)
        lineas = [x for x in sin_docs.splitlines() if not x.strip().startswith('#')]
        assert not any(re.search(r"mrs_|'mrs|severo|severidad|sintoma_", x, re.I) for x in lineas), f'{f} menciona una variable prohibida'
        assert 'RandomForest' not in texto and 'GaussianMixture' not in texto and 'entropy' not in texto.lower().replace('entropía', ''), f'{f} usa un método excluido'
    ev = tabla('seleccion/evaluacion_por_etapa.csv')
    assert not ev['criterio'].str.contains('MRS|severidad', case=False).any()
    return 'Sin MRS, Random Forest, GMM ni Shannon en el código de decisión'


@prueba(18, 'Asignación de nuevas participantes: la regla reproduce K-means y el margen está bien calculado')
def p18():
    et = tabla_etiquetas()
    for c in ('F2_c05_km_k3', 'P2_c12_km_k4'):
        i = N.info_config(c)
        X = Q.coordenadas(i['espacio'], i['componentes']).to_numpy()
        l = et[c].to_numpy()
        e, d1, d2, m = Q.asignar(Q.prototipos(X, l, i['k']), X)
        assert (e == l).all(), f'{c}: el centroide más cercano no reproduce K-means'
        assert (d2 >= d1).all() and np.allclose(m, 1 - d1 / d2)
    w = 'F2_c03_ward_k4'
    t = N.tabla_37b().loc[w]
    i = N.info_config(w)
    X = Q.coordenadas(i['espacio'], i['componentes']).to_numpy()
    e = Q.asignar(Q.prototipos(X, et[w].to_numpy(), 4), X)[0]
    assert abs(adjusted_rand_score(et[w], e) - t['acuerdo_prototipo_ari']) < 1e-9
    ev = tabla('asignacion/evaluacion_asignacion.csv').set_index('config')
    assert 'no equivale' in ev.loc[w, 'regla']
    g = tabla('asignacion/grilla_incertidumbre.csv')
    assert {'margen', 'distancia_percentil'} == set(g['tipo'])
    return 'K-means 100 %; Ward por prototipos reproducido y rotulado como aproximación'


# ---------------------------------------------------------------- 19 a 26
@prueba(19, 'Conservación de parámetros y versiones')
def p19():
    h = N.leer_json(N.B37 / 'resultados' / 'entorno.json')
    import scipy
    import sklearn
    assert (np.__version__, pd.__version__, scipy.__version__, sklearn.__version__) == (h['numpy'], h['pandas'], h['scipy'], h['scikit_learn']), 'Versiones distintas de la Fase 37B'
    assert (Q.SEMILLA, Q.N_REP, Q.N_SUB) == (42, 30, 423)
    assert N.huella_sello()
    s = N.leer_json(B / 'protocolo' / 'sello_enmienda_1.json')
    assert N.sha(B / 'protocolo' / s['archivo']) == s['sha256'], 'La enmienda cambió'
    assert N.leer_json(B / 'referencias_nulas' / 'contraccion_elegida.json')['alfa_elegido'] == 0.05
    return 'Versiones iguales a la Fase 37B; protocolo y enmienda coinciden con sus sellos'


@prueba(20, 'Correspondencia entre tablas y figuras')
def p20():
    import graficos_37c as G
    n = 0
    for nombre, f in G.FIGURAS.items():
        fig, datos = f()
        for tabla_ruta, col, valores in datos:
            esperado = tabla(tabla_ruta)
            for clave, val in valores.items():
                if isinstance(clave, tuple):
                    fila = esperado
                    for col_f, v_f in clave:
                        fila = fila[fila[col_f] == v_f]
                    x = fila[col].iloc[0]
                else:
                    x = esperado.set_index(esperado.columns[0]).loc[clave, col]
                assert abs(float(x) - float(val)) < 1e-6, f'{nombre}: {clave} dibujado {val}, tabla {x}'
                n += 1
        G.plt.close(fig)
        assert (B / 'figuras' / f'{nombre}.png').exists(), f'Falta {nombre}.png'
    assert len(G.FIGURAS) >= 12
    return f'{len(G.FIGURAS)} figuras; {n} valores dibujados coinciden con las tablas'


@prueba(21, 'Ausencia de cambios en la plataforma')
def p21():
    estado = estado_git()
    assert not estado.strip(), f'Hay cambios fuera de analisis/: {estado[:300]}'
    return 'git status fuera de analisis/ vacío'


@prueba(22, 'Ausencia de commit y de push')
def p22():
    assert head() == ORIGEN_HEAD, f'HEAD cambió: {head()}'
    assert 'datos-simulados' not in ramas_remotas(), 'La rama aparece en el remoto'
    return f'HEAD {ORIGEN_HEAD}; la rama no existe en el remoto'


@prueba(23, 'La decisión se deriva de las tablas y una debilidad crítica no se compensa')
def p23():
    import seleccion_37c as SE
    ev = tabla('seleccion/evaluacion_por_etapa.csv')
    assert (ev.loc[ev['criterio'] == 'E3 ari_entre media', 'estado'] == ev.loc[ev['criterio'] == 'E3 ari_entre media', 'valor'].map(lambda x: SE.estado(x, 0.80, 0.65))).all(), 'Estado distinto de la regla'
    f = tabla('seleccion/finalistas.csv')
    et = ev[(ev['estado'] == 'CRIT') & ev['etapa'].isin(['1. Integridad', '2. Asignación', '3. Estabilidad', '4. Codificación', '4. Población e imputación'])]
    assert not set(f['config']) & set(et['config']), 'Una finalista tiene CRIT en una etapa que la excluye'
    assert not any(x.startswith('R0') for x in f['config']), 'Una referencia sin reducción quedó como finalista'
    d = N.leer_json(B / 'seleccion' / 'decision_preliminar_reglas.json')
    if d['conclusion'] in ('A', 'B'):
        assert (f['clase'] == 'Segmentación multivariable').any(), 'Se seleccionó una clase no multivariable'
    assert not any('puntuacion' in c or 'score' in c for c in f.columns)
    return f'Conclusión por reglas: {d["conclusion"]}; {len(f)} particiones finalistas'


@prueba(24, 'La imputación reestimada con las 529 reproduce la histórica, salvo la excepción documentada')
def p24():
    cad = cadena()
    t, _ = cad.tabla_imputada()
    dif = (t.astype(str) != cad.tabla.astype(str)).sum()
    dif = dif[dif > 0]
    assert dif.to_dict() == {'tiene_actividad_sexual': 30}, f'Diferencias: {dif.to_dict()}'
    return 'Solo difieren las 30 celdas de tiene_actividad_sexual'


@prueba(25, 'Niveles distintos no se tratan como equivalentes: E1 sin reducción coincide con E0, y las tablas guardan cada nivel')
def p25():
    t = tabla('estabilidad/comparacion_niveles.csv').set_index('config')
    r0 = t[t.index.str.startswith('R0')]
    assert (np.abs(r0['E1_entre_media'] - r0['E0_entre_media']) < 1e-9).all(), 'Sin reducción, E1 debe igualar a E0'
    assert (t.index.isin(N.lista_a()).sum() == 108)
    n = tabla('estabilidad/estabilidad_por_nivel.csv')
    assert set(n['nivel']) == {'E1', 'E2', 'E3'} and (n.groupby('config').size() == 3).all()
    x = t.loc['F2_c03_km_k3']
    assert x['E0_entre_media'] != x['E1_entre_media']
    return 'E1 = E0 en las referencias sin reducción; tres niveles por configuración'


@prueba(26, 'Sin archivos ajenos: todo queda en la carpeta 37C, y sin carpetas __pycache__ en fases protegidas')
def p26():
    fuera = pd.read_csv(B / 'integridad' / 'escrituras_fuera.csv')
    assert fuera.empty, fuera.head().to_string()
    for nombre, base in N.PROTEGIDAS.items():
        assert not list(Path(base).rglob('__pycache__')), f'__pycache__ en {nombre}'
    return 'Sin escrituras fuera de 37C ni __pycache__ en fases protegidas'


def ejecutar(seleccion=None):
    filas = []
    for n, nombre, f in PRUEBAS:
        if seleccion and n not in seleccion:
            continue
        try:
            d = f()
            filas.append({'n': n, 'prueba': nombre, 'resultado': 'superada', 'detalle': d})
        except Exception as ex:  # noqa: BLE001
            filas.append({'n': n, 'prueba': nombre, 'resultado': 'FALLA', 'detalle': f'{type(ex).__name__}: {ex}'})
    return filas


def main():
    N.huella_sello()
    r = ejecutar()
    t = pd.DataFrame(r)
    N.a_csv(t, B / 'pruebas' / 'resultados_pruebas.csv')
    print(t[['n', 'resultado', 'detalle']].to_string(max_colwidth=120))
    print(f'{(t["resultado"] == "superada").sum()} de {len(t)} superadas')
    return 0 if (t['resultado'] == 'superada').all() else 1


if __name__ == '__main__':
    sys.exit(main())
