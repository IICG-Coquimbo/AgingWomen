"""
Fase 37A: pruebas de la reducción dimensional, según la Parte 8 del encargo.

Uso, desde analisis/: python fase37/37A_reduccion/scripts/pruebas_37a.py
Lee resultados ya construidos. Para la reproducibilidad repite el ajuste dos veces en una carpeta temporal, en procesos distintos.
Escribe solo pruebas/resultados_pruebas.csv.
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
ANALISIS = BASE.parents[1]
RAIZ = ANALISIS.parent
F36 = ANALISIS / 'fase36'
sys.path[:0] = [str(AQUI), str(F36)]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402

import graficos_37a as G  # noqa: E402
import reduccion as R  # noqa: E402
import transformador as TF  # noqa: E402

ESC = {'P1': 'P1_pca_con_imc', 'P2': 'P2_pca_sin_imc', 'F1': 'F1_famd_con_imc', 'F2': 'F2_famd_sin_imc'}
INERCIA = {'P1': 29.5047, 'P2': 29.0, 'F1': 38.5047, 'F2': 38.0}
RANGO = {'P1': 33, 'P2': 32, 'F1': 39, 'F2': 38}
PROYECCION = {'S-TRA': 22, 'S-CUI': 21, 'S-EJE': 75}
PRUEBAS = []
EXCLUIDAS = ('mrs', 'severo', 'severidad', 'usa_medicamentos_diabetes', 'doble_carga', 'prevision', 'etapa_menopausica', 'cuida_otras_personas', 'realiza_', 'lugar_trabajo', 'estres_entorno', 'sobrecarga', 'participante_id', '_imputado')


def prueba(numero, nombre):
    def deco(f):
        PRUEBAS.append((numero, nombre, f))
        return f
    return deco


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ids():
    return pd.read_csv(F36 / 'matrices' / 'identificadores.csv', dtype=str)['participante_id']


def matriz(e):
    return pd.read_csv(F36 / 'matrices' / f'{ESC[e]}.csv')


def modelo(e):
    return R.cargar(BASE / 'artefactos' / e / 'modelo.json')


def coordenadas(e, k):
    return pd.read_csv(BASE / 'coordenadas' / e / f'coordenadas_k{k:02d}.csv', dtype={'participante_id': str})


def variantes():
    return sorted(p.parent for p in (BASE / 'sensibilidades').glob('*/*/modelo.json'))


def tabla(n, **k):
    return pd.read_csv(BASE / 'tablas' / n, encoding='utf-8', **k)


@prueba(1, 'Conservación de las 529 participantes')
def p01():
    for e in ESC:
        assert modelo(e)['n_ajuste'] == 529
        for k in R.CANDIDATOS:
            assert len(coordenadas(e, k)) == 529
    for c in variantes():
        n = len(pd.read_csv(c / 'coordenadas_ajuste.csv', usecols=['participante_id']))
        if (c / 'coordenadas_proyeccion.csv').exists():
            n += len(pd.read_csv(c / 'coordenadas_proyeccion.csv', usecols=['participante_id']))
        assert n == 529, c
    return f'28 archivos principales y {len(variantes())} variantes con 529 participantes, sumando ajuste y proyección'


@prueba(2, 'Conservación del orden de identificadores')
def p02():
    i = list(ids())
    for e in ESC:
        for k in R.CANDIDATOS:
            assert list(coordenadas(e, k)['participante_id']) == i
    for c in variantes():
        a = pd.read_csv(c / 'coordenadas_ajuste.csv', dtype=str, usecols=['participante_id'])['participante_id'].tolist()
        assert a == [x for x in i if x in set(a)], c
    return 'Mismo orden que fase36/matrices/identificadores.csv; las variantes conservan el orden relativo'


@prueba(3, 'Integridad de las matrices de entrada')
def p03():
    for e, n in ESC.items():
        ruta = F36 / 'matrices' / f'{n}.csv'
        huellas = json.loads((F36 / 'artefactos' / e / 'huellas.json').read_text(encoding='utf-8'))
        m = modelo(e)
        assert sha(ruta) == huellas['matriz'] == m['matriz_sha256'], e
        assert m['columnas'] == list(matriz(e).columns) == json.loads((F36 / 'artefactos' / e / 'orden_columnas.json').read_text(encoding='utf-8')), e
        assert abs(matriz(e).var(ddof=0).sum() - INERCIA[e]) < 1e-3
    for c in variantes():
        m = R.cargar(c / 'modelo.json')
        if 'matriz_sha256' in m:
            assert m['matriz_sha256'] == sha(F36 / 'sensibilidades' / m['sensibilidad'] / m['base'] / 'matriz.csv'), c
    return 'SHA-256 iguales a los de la Fase 36; columnas e inercia esperadas'


@prueba(4, 'Ausencia de escalado adicional')
def p04():
    for e in ESC:
        m = modelo(e)
        Z = matriz(e)
        assert np.abs(np.array(m['media']) - Z.mean().to_numpy()).max() < 1e-15 and np.abs(m['media']).max() < 1e-12
        F = coordenadas(e, 20).drop(columns='participante_id').to_numpy()
        assert np.abs(F - Z.to_numpy() @ np.array(m['componentes'])[:20].T).max() < 1e-12, e
    for e in ('P1', 'F1'):
        F = R.proyectar(modelo(e), matriz(e))
        rec = F @ np.array(modelo(e)['componentes'])
        j = list(matriz(e).columns).index('imc')
        assert abs(rec[:, j].var() - 267 / 529) < 1e-12, e
    for s in ('reduccion.py', 'ejecutar_37a.py'):
        codigo = (AQUI / s).read_text(encoding='utf-8')
        assert 'StandardScaler' not in codigo and 'whiten' not in codigo and 'import' + ' prince' not in codigo
    return 'Coordenadas = matriz · V sin otra transformación; IMC reconstruido con varianza 267/529; sin StandardScaler, blanqueo ni prince'


@prueba(5, 'Ausencia de MRS en las entradas')
def p05():
    columnas = [(e, c) for e in ESC for c in modelo(e)['columnas']] + [(x, c) for x in variantes() for c in R.cargar(x / 'modelo.json')['columnas']]
    malas = [(e, c) for e, c in columnas if any(p in c.lower() for p in EXCLUIDAS)]
    assert not malas, malas[:4]
    leidos = pd.read_csv(BASE / 'integridad' / 'archivos_leidos.csv')['archivo_leido'].tolist()
    assert leidos and not [x for x in leidos if x.startswith('datos/')]
    assert any('P1_pca_con_imc.csv' in x for x in leidos), 'el gancho no registró lecturas'
    assert not [x for x in leidos if re.search(r'verdad|bitacora|dataset_fase35|mrs', x, re.I)]
    assert len(pd.read_csv(BASE / 'integridad' / 'escrituras_fuera.csv')) == 0
    for n in ('valores_propios.csv', 'cargas_columnas.csv', 'contribucion_variables.csv'):
        assert not tabla(n).astype(str).apply(lambda c: c.str.contains('mrs', case=False)).any().any()
    return f'{len(columnas)} columnas sin variables excluidas; {len(leidos)} archivos leídos según el gancho, ninguno de datos/; sin escrituras fuera de la salida'


@prueba(6, 'Valores propios no negativos y ordenados')
def p06():
    minimo = 1
    for m in [modelo(e) for e in ESC] + [R.cargar(x / 'modelo.json') for x in variantes()]:
        lam = np.array(m['valores_propios'])
        assert (lam > -1e-10).all() and (np.diff(lam) < 1e-10).all(), m.get('sensibilidad', 'principal')
        minimo = min(minimo, lam.min())
    return f'{4 + len(variantes())} modelos con valores propios no negativos y decrecientes; mínimo {minimo:.2e}'


@prueba(7, 'Ortogonalidad de los componentes')
def p07():
    mx, mf = 0.0, 0.0
    for e in ESC:
        m = modelo(e)
        V = np.array(m['componentes'])
        mx = max(mx, np.abs(V @ V.T - np.eye(m['rango'])).max())
        F = R.proyectar(m, matriz(e))
        C = F.T @ F / 529
        mf = max(mf, np.abs(C - np.diag(m['valores_propios'])).max())
    for x in variantes():
        V = np.array(R.cargar(x / 'modelo.json')['componentes'])
        mx = max(mx, np.abs(V @ V.T - np.eye(len(V))).max())
    assert mx < 1e-12 and mf < 1e-11, (mx, mf)
    return f'V·Vᵀ = I, diferencia máxima {mx:.1e}; coordenadas sin correlación y con varianza λ, diferencia {mf:.1e}'


@prueba(8, 'Consistencia de la inercia total')
def p08():
    for e in ESC:
        m = modelo(e)
        Z = matriz(e)
        lam = np.array(m['valores_propios'])
        assert m['rango'] == RANGO[e] == np.linalg.matrix_rank(Z.to_numpy()), e
        assert abs(lam.sum() - INERCIA[e]) < 1e-3 and abs(lam.sum() - Z.var(ddof=0).sum()) < 1e-11, e
        ev = PCA(n_components=m['rango'], svd_solver='full').fit(Z.to_numpy()).explained_variance_
        assert np.abs(ev * 528 / 529 - lam).max() < 1e-12
        assert abs(ev.sum() - lam.sum()) > 0.01, 'sin el factor no debería coincidir'
        v = tabla('valores_propios.csv').query('escenario == @e')
        assert np.abs(v['valor_propio'].to_numpy() - lam).max() < 1e-12 and abs(v['pct_acumulado'].iloc[-1] - 100) < 1e-9
    return 'Σλ = 29,5047, 29, 38,5047 y 38. Factor 528/529 comprobado frente a explained_variance_. Rangos 33, 32, 39 y 38'


@prueba(9, 'Reconstrucción numérica')
def p09():
    mx = 0.0
    for e in ESC:
        m = modelo(e)
        Z = matriz(e).to_numpy()
        F = R.proyectar(m, Z)
        V = np.array(m['componentes'])
        mx = max(mx, np.abs(F @ V + np.array(m['media']) - Z).max())
        lam = np.array(m['valores_propios'])
        for k in R.CANDIDATOS:
            err = ((Z - F[:, :k] @ V[:k]) ** 2).sum() / 529
            assert abs(err - lam[k:].sum()) < 1e-10, (e, k)
    assert mx < 1e-12, mx
    return f'Con todos los ejes, error máximo {mx:.1e}. Con k ejes, el error cuadrático medio iguala la suma de los λ omitidos'


@prueba(10, 'Reproducibilidad de coordenadas')
def p10():
    with tempfile.TemporaryDirectory() as t:
        tablas = []
        for i in (1, 2):
            s = Path(t) / f's{i}'
            r = subprocess.run([sys.executable, str(AQUI / 'ejecutar_37a.py'), '--salida', str(s)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=500)
            assert r.returncode == 0, r.stderr[-400:]
            tablas.append(pd.read_csv(s / 'integridad' / 'manifiesto_ejecucion.csv').set_index('ruta')['sha256'])
    oficial = pd.read_csv(BASE / 'integridad' / 'manifiesto_ejecucion.csv').set_index('ruta')['sha256']
    assert tablas[0].equals(tablas[1]) and tablas[0].sort_index().equals(oficial.sort_index())
    return f'Dos procesos distintos y la versión oficial: {len(oficial)} archivos con el mismo SHA-256'


def respuestas_desde_procedencia():
    """Reconstruye las respuestas originales sin abrir datos/: un vacío en una frecuencia significa madre = NO."""
    c = pd.read_csv(F36 / 'procedencia' / 'procedencia_celdas.csv', dtype=str, keep_default_na=False)
    p = c.pivot(index='participante_id', columns='variable', values='valor_original').reindex(ids())
    for v, m in (('frecuencia_aerobico', 'realiza_aerobico'), ('frecuencia_bajo_impacto', 'realiza_bajo_impacto'), ('frecuencia_fuerza', 'realiza_fuerza'), ('cantidad_personas_cuida', 'cuida_otras_personas')):
        p[m] = np.where(p[v] == '', 'NO', 'SI')
    return p


@prueba(11, 'Transformación de una participante nueva')
def p11():
    antes = {p.name + e: sha(p) for e in ESC for p in (BASE / 'artefactos' / e).glob('*')}
    p = respuestas_desde_procedencia()
    mx = 0.0
    for e in ESC:
        tr = TF.Transformador.cargar(F36 / 'artefactos' / e)
        m = modelo(e)
        F = coordenadas(e, 20).drop(columns='participante_id').to_numpy()
        for i in range(0, 529, 47):
            z = tr.transformar(p.iloc[[i]])[0]
            assert list(z.columns) == m['columnas']
            mx = max(mx, np.abs(R.proyectar(m, z.to_numpy(), 20)[0] - F[i]).max())
    assert mx < 1e-11, mx
    # Caso inventado, no es una fila del conjunto.
    nueva = {'edad': 58, 'imc': 33.5, 'horas_sedentarismo': 8, 'trabaja_actualmente': 'True', 'tiene_pareja': 'SI', 'tiene_actividad_sexual': 'NO', 'operada_no_mas_hijos': 'NO', 'usa_medicamentos_presion': 'SI', 'quien_prepara_comidas': 'OTRO',
             'realiza_aerobico': 'NO', 'realiza_bajo_impacto': 'SI', 'realiza_fuerza': 'NO', 'cuida_otras_personas': 'NO', 'frecuencia_aerobico': '', 'frecuencia_bajo_impacto': 4, 'frecuencia_fuerza': '', 'cantidad_personas_cuida': '', 'tabaco_frecuencia': 3}
    for v in p.columns:
        nueva.setdefault(v, 2)
    caso = pd.DataFrame([nueva], index=['nueva'])
    for e in ESC:
        tr = TF.Transformador.cargar(F36 / 'artefactos' / e)
        m = modelo(e)
        z = tr.transformar(caso)[0]
        c5 = R.proyectar(m, z.to_numpy(), 5)
        manual = (z.to_numpy() - np.array(m['media'])) @ np.array(m['componentes'])[:5].T
        assert np.abs(c5 - manual).max() == 0 and np.isfinite(c5).all() and c5.shape == (1, 5)
        lote = pd.concat([caso, p.iloc[[0, 1]]])
        assert np.abs(R.proyectar(m, tr.transformar(lote)[0].to_numpy(), 5)[0] - c5[0]).max() < 1e-13, 'el resultado depende de las otras filas'
    try:
        R.proyectar(modelo('P1'), matriz('P1').iloc[[0]].to_numpy(), 34)
        raise AssertionError('debía rechazar k mayor que el rango')
    except ValueError:
        pass
    assert antes == {p2.name + e: sha(p2) for e in ESC for p2 in (BASE / 'artefactos' / e).glob('*')}
    return f'24 filas desde sus respuestas originales: diferencia {mx:.1e} con la coordenada guardada. Caso inventado correcto en 4 escenarios, independiente de otras filas; artefactos intactos'


@prueba(12, 'Consistencia de las sensibilidades')
def p12():
    res = tabla('sens_resumen.csv')
    assert len(res) == len(variantes()) == 34
    for x in variantes():
        m = R.cargar(x / 'modelo.json')
        sid, e = m['sensibilidad'], m['base']
        assert abs(sum(m['valores_propios']) - m['inercia_total']) < 1e-9, x
        a = pd.read_csv(x / 'coordenadas_ajuste.csv', dtype={'participante_id': str})
        assert np.abs(a.drop(columns='participante_id').mean()).max() < 1e-11, x
        if sid in PROYECCION:
            assert (x / 'coordenadas_proyeccion.csv').exists() and len(pd.read_csv(x / 'coordenadas_proyeccion.csv')) == PROYECCION[sid] and m['n_ajuste'] == 529 - PROYECCION[sid], x
            pob = pd.read_csv(F36 / 'sensibilidades' / 'poblaciones' / f'{sid}.csv', dtype=str)
            assert set(a['participante_id']) == set(pob[pob['rol'] == 'ajuste']['participante_id'])
            Z = pd.read_csv(F36 / 'sensibilidades' / sid / e / 'matriz.csv')
            pr = pd.read_csv(x / 'coordenadas_proyeccion.csv', dtype={'participante_id': str})
            km = pr.shape[1] - 1
            fila = (pob['rol'] == 'proyeccion').to_numpy()
            assert np.abs(R.proyectar(m, Z[fila].to_numpy(), km) - pr.drop(columns='participante_id').to_numpy()).max() < 1e-12, x
        else:
            assert not (x / 'coordenadas_proyeccion.csv').exists(), x
    base = matriz('P1')
    sa = R.cargar(BASE / 'sensibilidades' / 'S-BLOQUE-SA' / 'P1' / 'modelo.json')
    assert sa['multiplicadores']['imc'] == 1.0 and abs(sa['inercia_total'] - base.var(ddof=0).sum()) < 1e-9
    fa = R.cargar(BASE / 'sensibilidades' / 'S-BLOQUE-SA' / 'F1' / 'modelo.json')
    assert fa['multiplicadores']['imc'] == 1.0 and abs(fa['inercia_total'] - matriz('F1').var(ddof=0).sum()) < 1e-9
    bl = R.cargar(BASE / 'sensibilidades' / 'S-BLOQUE' / 'F1' / 'modelo.json')
    assert bl['multiplicadores']['imc'] > 3
    assert 'edad' not in R.cargar(BASE / 'sensibilidades' / 'S-EDAD' / 'P1' / 'modelo.json')['columnas']
    s = tabla('sens_similitud.csv')['similitud_subespacio']
    assert s.between(0, 1 + 1e-12).all()
    F = coordenadas('P1', 5).drop(columns='participante_id').to_numpy()
    assert abs(R.similitud_subespacio(F, F) - 1) < 1e-12 and abs(R.similitud_subespacio(F, F @ np.linalg.qr(np.random.default_rng(42).normal(size=(5, 5)))[0]) - 1) < 1e-12
    return '34 variantes: ajuste y proyección separados, proyección con parámetros congelados, IMC sin amplificar en S-BLOQUE-SA con inercia global conservada; similitud 1 ante una rotación'


@prueba(13, 'Correspondencia entre resultados y gráficos')
def p13():
    v = tabla('valores_propios.csv')
    fig = G.f01_sedimentacion()
    for ax, e in zip(fig.axes, G.ESC):
        y = ax.lines[0].get_ydata()
        assert np.abs(np.asarray(y) - v[v['escenario'] == e]['pct'].to_numpy()).max() < 1e-12
    plt.close(fig)
    fig = G.f02_acumulada()
    lineas = [x for x in fig.axes[0].lines if len(x.get_xdata()) > 2]
    for ln, e in zip(lineas, G.ESC):
        assert np.abs(np.asarray(ln.get_ydata()) - v[v['escenario'] == e]['pct_acumulado'].to_numpy()).max() < 1e-12
    plt.close(fig)
    fig = G.f06_proyeccion()
    for ax, e in zip([a for a in fig.axes], G.ESC):
        pts = ax.collections[0].get_offsets()
        c = coordenadas(e, 2)
        assert len(pts) == 529 and np.abs(np.asarray(pts) - c[['C1', 'C2']].to_numpy()).max() < 1e-12
    plt.close(fig)
    fig = G.f04_contribucion('P1')
    c = tabla('contribucion_variables.csv').query("escenario == 'P1' and componente == 1").sort_values('contribucion_pct', ascending=False).head(10)[::-1]
    assert np.abs(np.array([b.get_width() for b in fig.axes[0].patches]) - c['contribucion_pct'].to_numpy()).max() < 1e-12
    plt.close(fig)
    fig = G.f07_imc()
    i = tabla('imc_por_eje.csv').query("variante == 'principal' and base == 'P1'")
    assert np.abs(np.asarray(fig.axes[0].lines[0].get_ydata()) - i['contribucion_pct'].to_numpy()).max() < 1e-12
    plt.close(fig)
    u = tabla('componentes_para_umbral.csv').set_index('id')
    fig = G.f08_metodos()
    for ln, e in zip(fig.axes[0].lines, G.ESC):
        assert list(ln.get_ydata()) == [u.loc[e, f'c{x}'] for x in (50, 60, 70, 80, 90)]
    plt.close(fig)
    fig = G.f06_proyeccion()
    assert all(len(a.collections[0].get_facecolor()) == 1 for a in fig.axes), 'la proyección no debe colorearse por una variable'
    plt.close(fig)
    assert len(list((BASE / 'figuras').glob('*.png'))) == 16
    return '6 figuras comparadas con sus tablas, punto a punto; proyección en un solo color; 16 PNG presentes'


@prueba(14, 'Conservación de los archivos protegidos')
def p14():
    sys.path.insert(0, str(ANALISIS / 'revision_correctiva_fase34'))
    from manifiesto import huella
    m = pd.read_csv(F36 / 'integridad' / 'manifiesto_final_36B.csv', encoding='utf-8')
    d = [r for r, h in zip(m['ruta'], m['sha256']) if not (F36 / r).exists() or huella(F36 / r) != h]
    assert not d, d[:5]
    b = pd.read_csv(ANALISIS / 'cierre_fases_34_35' / 'integridad' / 'manifiesto_despues.csv', encoding='utf-8')
    d = [r for r, h in zip(b['ruta'], b['sha256']) if not (RAIZ / r).exists() or huella(RAIZ / r) != h]
    assert not d, d[:5]

    def git(*a):
        return subprocess.run(['git', *a], cwd=RAIZ, capture_output=True, text=True, encoding='utf-8').stdout.rstrip()
    assert git('rev-parse', '--short', 'HEAD').strip() == '745d689' and not git('diff', '--cached', '--name-only')
    seguidos = sorted(x[3:] for x in git('status', '--short').splitlines() if not x.startswith('??'))
    assert len(seguidos) == 8 and all(x.startswith('analisis/') for x in seguidos), seguidos
    assert not [x for x in git('status', '--short').splitlines() if ' src/' in x or 'requirements' in x]
    return f'{len(b)} archivos del cierre 34-35 y {len(m)} de la Fase 36 sin cambios; HEAD 745d689; sin nada preparado; src/ y dependencias sin cambios'


@prueba(15, 'Protocolo sellado antes de los resultados')
def p15():
    s = json.loads((BASE / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    assert sha(BASE / 'protocolo' / s['archivo']) == s['sha256']
    assert (BASE / 'protocolo' / 'sello_protocolo.json').stat().st_mtime < min(p.stat().st_mtime for p in (BASE / 'scripts').glob('ejecutar_37a.py'))
    return f'SHA-256 igual al sello ({s["sha256"][:12]}…); el sello es anterior al programa que ajusta los modelos'


@prueba(16, 'Sin clústeres ni selección')
def p16():
    for p in (AQUI).glob('*.py'):
        codigo = re.sub(r'""".*?"""', '', p.read_text(encoding='utf-8'), flags=re.S)
        lineas = [x for x in codigo.splitlines() if x.lstrip().startswith(('import ', 'from '))]
        assert not [x for x in lineas if 'sklearn.cluster' in x or 'scipy.cluster' in x], p.name
        assert 'KMeans(' not in codigo.replace("'KMeans('", '') and 'AgglomerativeClustering(' not in codigo.replace("'AgglomerativeClustering('", '') and 'linkage(' not in codigo.replace("'linkage('", ''), p.name
    assert not [p for p in BASE.rglob('*') if p.is_file() and re.search(r'cluster|kmeans|etiqueta|perfil', p.name, re.I)]
    assert not (BASE.parent / '37B').exists() and sorted(x.name for x in BASE.parent.iterdir() if x.is_dir()) == ['37A_reduccion']
    return 'Sin importar módulos de agrupamiento, sin archivos de clústeres ni etiquetas; la Fase 37B no se inició'


@prueba(17, 'Coordenadas por candidato')
def p17():
    for e in ESC:
        total = coordenadas(e, 20)
        for k in R.CANDIDATOS:
            c = coordenadas(e, k)
            assert list(c.columns[1:]) == [f'C{i + 1}' for i in range(k)] and k <= RANGO[e]
            assert np.abs(c.drop(columns='participante_id').to_numpy() - total.iloc[:, 1:k + 1].to_numpy()).max() < 1e-13
    return '7 candidatos en 4 escenarios: cada archivo son los primeros k ejes del de 20; ninguno supera el rango'


@prueba(18, 'Contribuciones de FAMD frente a su definición')
def p18():
    mx = 0.0
    for e in ('F1', 'F2'):
        m = modelo(e)
        Z = matriz(e)
        F = R.proyectar(m, Z)
        c = tabla('contribucion_variables.csv').query('escenario == @e')
        col_var = {x: x.split('__')[0] for x in Z.columns}
        for a in range(8):
            for v in set(col_var.values()):
                col = [x for x in Z.columns if col_var[x] == v]
                f = F[:, a]
                if len(col) == 1:
                    teorico = Z[col[0]].var(ddof=0) * np.corrcoef(Z[col[0]], f)[0, 1] ** 2
                else:
                    teorico = sum((Z[x].to_numpy() > 0).mean() * f[Z[x].to_numpy() > 0].mean() ** 2 for x in col) / f.var()
                obs = c[(c['componente'] == a + 1) & (c['variable'] == v)]['aporte_absoluto'].iloc[0]
                mx = max(mx, abs(teorico - obs))
    assert mx < 1e-10, mx
    return f'En 8 ejes y todas las variables: aporte = r² (v·r² en IMC) o η², diferencia máxima {mx:.1e}'


@prueba(19, 'Orden de niveles')
def p19():
    o = tabla('famd_orden_niveles.csv')
    b = tabla('famd_baricentros.csv', dtype={'nivel': str})
    assert o['variable'].nunique() == 5 and (o.groupby(['escenario', 'variable'])['eje_principal'].sum() == 1).all()
    F = coordenadas('F1', 5)
    Z = matriz('F1')
    x = Z['frecuencia_fuerza__4+5'].to_numpy() > 0
    g = b[(b['escenario'] == 'F1') & (b['variable'] == 'frecuencia_fuerza') & (b['nivel'] == '4 + 5') & (b['componente'] == 1)]
    assert abs(g['baricentro'].iloc[0] - F.loc[x, 'C1'].mean()) < 1e-12 and g['n'].iloc[0] == 38
    return 'Cinco variables con un eje principal cada una; baricentro recalculado igual al de la tabla'


def main():
    filas = []
    for n, nombre, f in PRUEBAS:
        try:
            det, ok = f(), True
        except Exception as ex:  # noqa: BLE001
            ok, det = False, f'{type(ex).__name__}: {ex} | {traceback.format_exc(limit=2)[-260:]}'
        filas.append({'numero': n, 'prueba': nombre, 'resultado': 'OK' if ok else 'FALLA', 'detalle': det})
        print(n, 'OK' if ok else 'FALLA', '|', nombre, '|', str(det)[:210], flush=True)
    t = pd.DataFrame(filas)
    (BASE / 'pruebas').mkdir(exist_ok=True)
    t.to_csv(BASE / 'pruebas' / 'resultados_pruebas.csv', index=False, encoding='utf-8', lineterminator='\n')
    print(f'{(t["resultado"] == "OK").sum()} de {len(t)} pruebas superadas')
    return 0 if (t['resultado'] == 'OK').all() else 1


if __name__ == '__main__':
    raise SystemExit(main())
