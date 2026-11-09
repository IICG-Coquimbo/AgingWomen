"""
Fase 36B: las 25 pruebas de plan_pruebas_fase36.md y 7 pruebas específicas agregadas en el encargo.

Uso, desde analisis/: python fase36/pruebas_fase36.py [--referencia CARPETA_CON_PRINCE]

Lee las matrices y los artefactos ya construidos. Para el determinismo reconstruye dos veces en una carpeta temporal, en procesos
distintos. Escribe solo fase36/pruebas/. No ajusta PCA ni FAMD sobre las matrices reales: las pruebas de FAMD usan datos sintéticos.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path[:0] = [str(AQUI), str(AQUI.parent), str(AQUI.parent / 'revision_correctiva_fase34'), str(AQUI.parent / 'fase36_diseno' / 'scripts')]
sys.dont_write_bytecode = True

import configuracion_fase36 as C  # noqa: E402
import transformador as T  # noqa: E402
import validar_famd as VF  # noqa: E402
from limpieza import catalogo  # noqa: E402
from manifiesto import huella  # noqa: E402

M = AQUI / 'matrices'
A = AQUI / 'artefactos'
SENS = AQUI / 'sensibilidades'
PRUEBAS = []
REFERENCIA = {'carpeta': None}
PROHIBIDAS_TEXTO = ('mrs', 'severo', 'severidad')


def prueba(numero, grupo, nombre, critica=True):
    def deco(f):
        PRUEBAS.append((numero, grupo, nombre, critica, f))
        return f
    return deco


def leer(ruta, **k):
    return pd.read_csv(ruta, encoding='utf-8-sig', **k)


def ids():
    return leer(C.F35, dtype=str, keep_default_na=False)['participante_id']


def limpio():
    t = leer(C.LIMPIO, dtype=str, keep_default_na=False)
    return t.where(t != '', np.nan).set_index('participante_id')


def entrada():
    return limpio().reindex(ids())[C.GENERALES + C.CAMPOS_CONTEXTO]


def matriz(e):
    return leer(M / f'{C.NOMBRE_ARCHIVO[e]}.csv')


def tr(e):
    return T.Transformador.cargar(A / e)


def celdas():
    return leer(AQUI / 'procedencia' / 'procedencia_celdas.csv', dtype=str, keep_default_na=False)


def huellas_parametros():
    return {str(p.relative_to(A)): huella(p) for p in sorted(A.rglob('*')) if p.is_file()}


def todas_las_matrices():
    salida = {e: matriz(e) for e in C.ESCENARIOS}
    for p in sorted(SENS.glob('*/*/matriz.csv')):
        salida[f'{p.parent.parent.name}_{p.parent.name}'] = leer(p)
    return salida


def excluida(nombre):
    base = nombre.split('__')[0]
    return base in C.EXCLUIDAS_NOMBRE or base.startswith(tuple(C.EXCLUIDAS_PREFIJO)) or base.endswith(tuple(C.EXCLUIDAS_SUFIJO))


@prueba(1, 'Plan', 'Conservación de las 529')
def p01():
    i = leer(M / 'identificadores.csv', dtype=str)['participante_id']
    assert list(i) == list(ids()) and i.is_unique and len(i) == 529
    filas = {k: len(v) for k, v in todas_las_matrices().items()}
    assert set(filas.values()) == {529}
    return f'529 identificadores iguales y en el mismo orden; {len(filas)} matrices con 529 filas'


@prueba(2, 'Plan', 'Las 30 generales')
def p02():
    r = leer(C.RELEVANCIA)
    esperadas = set(r[r['poblacion'] == 'general']['variable'])
    for e in C.ESCENARIOS:
        vs = {d['variable'] for d in tr(e).definiciones}
        assert vs == (esperadas if C.ESCENARIOS[e][1] else esperadas - {'imc'}), e
    assert len(esperadas) == 30
    return '30 en P1 y F1; 29 sin IMC en P2 y F2; conjunto exacto de relevancia_33.csv'


@prueba(3, 'Plan', 'Sin variables excluidas')
def p03():
    malas = [(k, c) for k, m in todas_las_matrices().items() for c in m.columns if excluida(c)]
    for e in C.ESCENARIOS:
        malas += [(e, d['variable']) for d in tr(e).definiciones if excluida(d['variable'])]
    assert not malas, malas[:5]
    # Ningún artefacto tabular lleva identificadores personales.
    personales = {'rut_hash', 'usuario_id', 'uuid_local', 'fecha_nacimiento', 'comuna', 'nombre', 'correo', 'rut', 'region_residencia', 'origen_procedencia'}
    tablas = [p for d in ('matrices', 'artefactos', 'procedencia', 'modulos', 'sensibilidades') for p in (AQUI / d).rglob('*.csv')]
    con_personales = [p.name for p in tablas if personales & set(pd.read_csv(p, nrows=0, encoding='utf-8').columns)]
    assert not con_personales, con_personales
    return f'Ninguna excluida en esquemas ni en columnas, por nombre, prefijo o sufijo; {len(tablas)} tablas sin identificadores personales'


@prueba(4, 'Plan', 'Códigos y significados')
def p04():
    dic = leer(C.DICCIONARIO, dtype=str, keep_default_na=False)
    campos, _ = catalogo.leer_modelos()
    revisados = 0
    for d in tr('P1').definiciones:
        v = d['variable']
        if d['tipo'] == 'cuantitativa':
            continue
        fila = dic[dic['variable'] == v]
        for f in fila.itertuples():
            clave = f.codigo_en_dataset_fase35 if d['tipo'] == 'ordinal' else f.nivel_instrumento
            assert clave in d['niveles'], (v, clave)
            assert d['niveles'][clave]['significado'] == f.significado, (v, clave)
            if d['tipo'] != 'nominal':
                assert str(d['niveles'][clave]['codigo']) == f.codificacion_pca, (v, clave)
            revisados += 1
        opciones = (campos.get(v) or {}).get('opciones') or {}
        for clave, significado in opciones.items():
            assert str(clave) in d['niveles'], (v, clave)
            assert d['niveles'][str(clave)]['significado'] == significado, (v, clave)
        if d['tipo'] == 'ordinal':
            cod = [x['codigo'] for k, x in sorted(d['niveles'].items(), key=lambda kv: int(kv[0]))]
            assert cod == sorted(cod), (v, 'orden')
            assert set(cod) == set(range(min(cod), max(cod) + 1)), (v, 'consecutivos')
    return f'{revisados} niveles iguales al diccionario y al catálogo; códigos ascendentes y consecutivos'


@prueba(5, 'Plan', 'Sin NaN ni códigos espurios')
def p05():
    for k, m in todas_las_matrices().items():
        assert np.isfinite(m.to_numpy()).all(), k
        assert not [c for c in m.columns if c.split('__')[0] in C.MODULOS], k
    for e, n in C.DIMENSIONES.items():
        assert matriz(e).shape == n and list(matriz(e).columns) == tr(e).p['orden'], e
    return 'Todo finito; sin columnas laborales ni de sobrecarga; columnas y orden exactos'


@prueba(6, 'Plan', 'Trazabilidad de imputaciones')
def p06():
    res = leer(AQUI / 'procedencia' / 'resumen_por_variable.csv').set_index('variable')
    con = leer(AQUI / 'procedencia' / 'contraste_auditorias.csv')
    assert con['coincide'].all()
    g = res.loc[C.GENERALES]
    assert g['imputada'].drop('imc').sum() == 665 and res.loc['imc', 'imputada'] == 262 and g['heredadas'].sum() == 100
    assert (res[['observada', 'deducida', 'imputada', 'no_aplicable', 'faltante']].sum(axis=1) == 529).all()
    # Celda por celda donde existe marca histórica.
    L, c, comparadas = limpio().reindex(ids()), celdas(), 0
    for v in C.GENERALES + C.MODULOS:
        marca = f'{v}_imputado'
        if marca in L.columns:
            est = c[c['variable'] == v].set_index('participante_id')['estado'].reindex(ids())
            assert ((L[marca] == '1').to_numpy() == (est == 'imputada').to_numpy()).all(), v
            comparadas += 1
    return f'{len(con)} recuentos iguales a las auditorías; 665 + 262 imputadas, 100 heredadas; {comparadas} variables iguales celda a celda con la marca histórica'


@prueba(7, 'Plan', 'Sin fuga del MRS')
def p07():
    e = entrada()
    r = np.random.default_rng(C.SEMILLA)
    t = tr('P1')
    con_mrs = e.assign(mrs_total=r.permutation(len(e)), severo_mrs=r.integers(0, 2, len(e)), severidad_mrs_4=r.integers(0, 4, len(e)))
    assert t.transformar(con_mrs)[0].equals(t.transformar(e)[0])
    defs = t.definiciones
    assert json.dumps(T.calibrar(con_mrs, defs, 'pca')['escaladores']) == json.dumps(T.calibrar(e, defs, 'pca')['escaladores'])
    codigo = (AQUI / 'transformador.py').read_text(encoding='utf-8')
    sin_docs = re.sub(r'""".*?"""', '', codigo, flags=re.S)
    sin_docs = re.sub(r'#.*', '', sin_docs)
    assert not any(x in sin_docs.lower() for x in PROHIBIDAS_TEXTO)
    fuente = (AQUI / 'construir_fase36.py').read_text(encoding='utf-8')
    assert 'entrada = L.reindex(ids)[columnas]' in fuente
    return 'Agregar y permutar el MRS no cambia matriz ni parámetros; el transformador no lo nombra en su código'


@prueba(8, 'Plan', 'Determinismo')
def p08():
    with tempfile.TemporaryDirectory() as t:
        tablas = []
        for i in (1, 2):
            s = Path(t) / f's{i}'
            r = subprocess.run([sys.executable, str(AQUI / 'construir_fase36.py'), '--salida', str(s)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900)
            assert r.returncode == 0, r.stderr[-400:]
            tablas.append(leer(s / 'integridad' / 'manifiesto_fase36.csv').set_index('ruta')['sha256'])
        oficial = leer(AQUI / 'integridad' / 'manifiesto_fase36.csv').set_index('ruta')['sha256']
        assert tablas[0].equals(tablas[1])
        assert tablas[0].sort_index().equals(oficial.sort_index())
    return f'Dos procesos distintos y la versión oficial: {len(oficial)} archivos con el mismo SHA-256'


@prueba(9, 'Plan', 'Escalado reproducible')
def p09():
    e = entrada()
    t = leer(A / 'parametros_escalado.csv')
    p1 = t[t['escenario'] == 'P1'].set_index('columna')
    m = matriz('P1')
    cod = tr('P1').p['codificadores']
    mx = 0.0
    for col in [c for c in p1.index if p1.loc[c, 'clase'] == 'z']:
        v = p1.loc[col, 'variable']
        if v in C.CUANTITATIVAS:
            x = pd.to_numeric(e[v]).fillna(p1.loc[col, 'media'])
        else:
            base = e[v].fillna('0').map(lambda z: str(z))
            x = base.map(cod[v]['mapa']).astype(float)
        mx = max(mx, float(np.abs((x.to_numpy() - p1.loc[col, 'media']) / p1.loc[col, 'de'] - m[col].to_numpy()).max()))
    assert mx < 1e-12, mx
    z = [c for c in p1.index if p1.loc[c, 'clase'] == 'z' and c != 'imc']
    assert np.abs(m[z].mean()).max() < 1e-12 and np.abs(m[z].var(ddof=0) - 1).max() < 1e-12
    return f'Recalculado a mano con el CSV de parámetros: diferencia máxima {mx:.1e}; media 0 y varianza 1 salvo IMC'


@prueba(10, 'Plan', 'Nueva participante: caso de referencia')
def p10():
    e = entrada()
    antes = huellas_parametros()
    mx = 0.0
    for es in C.ESCENARIOS:
        t, m = tr(es), matriz(es)
        for i in range(0, 529, 23):
            f = t.transformar(e.iloc[[i]])[0]
            mx = max(mx, float(np.abs(f.to_numpy()[0] - m.iloc[i].to_numpy()).max()))
    assert mx < 1e-12, mx
    assert antes == huellas_parametros()
    return f'24 filas transformadas de una en una en 4 escenarios: diferencia máxima {mx:.1e}; artefactos con el mismo SHA-256'


@prueba(11, 'Plan', 'Compatibilidad con PCA y FAMD')
def p11():
    detalle = []
    for e, (f, c) in C.DIMENSIONES.items():
        m = matriz(e)
        assert m.shape == (f, c), e
        inercia = float(m.var(ddof=0).sum())
        assert abs(inercia - C.INERCIA[e]) < 0.001, (e, inercia)
        assert np.abs(m.mean()).max() < 1e-12, e
        detalle.append(f'{e} {c} col., {inercia:.4f}')
    return '; '.join(detalle) + '. Centradas. No se ajustó ningún modelo'


@prueba(12, 'Plan', 'Separación de módulos')
def p12():
    lab = leer(AQUI / 'modulos' / 'modulo_laboral.csv', dtype=str)
    cui = leer(AQUI / 'modulos' / 'modulo_cuidados.csv', dtype=str)
    n = (len(lab), int((lab['sensibilidad_ambas_observadas'] == '1').sum()), int((cui['principal_observada'] == '1').sum()), len(cui))
    assert n == (287, 263, 239, 251), n
    for m in todas_las_matrices().values():
        assert not {c.split('__')[0] for c in m.columns} & set(C.MODULOS)
    i, o = set(lab['participante_id']), set(cui[cui['principal_observada'] == '1']['participante_id'])
    assert len(i & set(cui['participante_id'])) > 0
    observadas = set(lab[lab['sensibilidad_ambas_observadas'] == '1']['participante_id'])
    return f'Fuera de las matrices generales; 287, 263, 239 y 251; laboral y sobrecarga observada a la vez: {len(i & o)}; las tres observadas: {len(observadas & o)}'


@prueba(13, 'Plan', 'Datos históricos')
def p13():
    base = pd.read_csv(C.MANIFIESTO_CIERRE, encoding='utf-8').set_index('ruta')['sha256']
    datos = base[base.index.str.startswith('datos/')]
    assert len(datos) > 0
    distintos = [r for r, h in datos.items() if not (C.RAIZ / r).exists() or huella(C.RAIZ / r) != h]
    assert not distintos, distintos[:5]
    return f'{len(datos)} archivos de datos iguales al manifiesto del cierre'


@prueba(14, 'Adicional', 'Valores laborales falsos')
def p14():
    lab = leer(AQUI / 'modulos' / 'modulo_laboral.csv', dtype=str)
    L = limpio().reindex(ids())
    f = leer(C.F35, dtype=str).set_index('participante_id')
    assert set(lab['lugar_trabajo_comprensivo']) <= set('12345') and set(lab['estres_entorno_laboral']) <= set('12345')
    for v in C.LABORALES:
        assert (lab.set_index('participante_id')[v] == L.loc[lab['participante_id'], v]).all()
    c = celdas()
    imput = set(c[(c['variable'] == 'trabaja_actualmente') & (c['estado'] == 'imputada')]['participante_id'])
    assert len(imput) == 22 and not imput & set(lab['participante_id'])
    assert set(f.loc[sorted(imput), 'lugar_trabajo_comprensivo'].astype(float)) == {3.0}
    no_trabajan = set(ids()[(L['trabaja_actualmente'] == 'False').to_numpy()])
    assert len(no_trabajan) == 220 and not no_trabajan & set(lab['participante_id'])
    return '287 con valores 1 a 5 iguales al limpio; fuera las 22 con relleno 3 y las 220 con 0 de no aplica'


@prueba(15, 'Adicional', 'Confusión de ceros')
def p15():
    L = limpio().reindex(ids())
    ceros = set(ids()[(L['cuida_otras_personas'] == 'NO').to_numpy()])
    cui = leer(AQUI / 'modulos' / 'modulo_cuidados.csv', dtype=str)
    assert len(ceros) == 278 and not ceros & set(cui['participante_id'])
    assert '0' not in set(cui[C.SOBRECARGA])
    return '278 con cantidad 0 sin fila en el módulo de sobrecarga; ninguna sobrecarga 0'


@prueba(16, 'Adicional', 'Salto en frecuencias')
def p16():
    t = tr('P1').p['codificadores']
    for v in C.NUNCA_UNIFICADO:
        assert t[v]['mapa'] == {'0': 0, '1': 0, '2': 1, '3': 2, '4': 3, '5': 4}, v
    assert t['cantidad_personas_cuida']['mapa'] == {'0': 0, '1': 1, '2': 2, '3': 3}
    # «Nunca» es un nivel propio en el resto de las variables: la unificación no debe extenderse a ellas.
    otras = ['alcohol_frecuencia', 'carnes_semana', 'distension_abdominal', 'falta_tiempo_influye', 'frecuencia_comida_fuera', 'golosinas_semana', 'legumbres_semana', 'pescado_semana', 'tabaco_frecuencia']
    for v in otras:
        assert t[v]['mapa']['1'] == 1 and t[v]['mapa']['2'] == 2 and '0' not in t[v]['mapa'], v
    return f'Mapa 0, 1, 2, 3, 4, 5 → 0, 0, 1, 2, 3, 4 solo en las tres frecuencias de ejercicio; «Nunca» conserva su código en las otras {len(otras)} variables'


@prueba(17, 'Adicional', 'Agrupación de FAMD')
def p17():
    from generar_tablas_diseno import agrupar_adyacentes
    g = leer(A / 'agrupaciones_categorias.csv', dtype={'grupo': str, 'niveles': str})
    dic = leer(C.DICCIONARIO, dtype=str, keep_default_na=False)
    e = entrada()
    for v in C.ORDINALES_CATEGORICAS:
        s = e[v].map(T._texto).where(lambda x: x != '', '0')
        conteos = s.value_counts().to_dict()
        niveles = sorted(conteos, key=int)
        protegidos = ['0'] if v in C.MADRES else []
        grupos = agrupar_adyacentes(niveles, conteos, protegidos)
        fijos = [[x for x in ns if x != '1' or v not in C.NUNCA_UNIFICADO] for ns in C.GRUPOS_FAMD[v].values()]
        assert grupos == fijos, (v, grupos, fijos)
    for f in dic[dic['grupo_famd'].str.contains(r'\+')].itertuples():
        assert f.grupo_famd in C.GRUPOS_FAMD[f.variable], (f.variable, f.grupo_famd)
    assert (g['n_529'] / 529 >= 0.05).all(), g[g['n_529'] / 529 < 0.05]
    return f'La regla determinista reproduce la tabla fija; {len(g)} grupos, todos con al menos 5 % (mínimo {g["n_529"].min() / 529:.1%})'


@prueba(18, 'Adicional', 'IMC')
def p18():
    e = tr('P1').p['escaladores']['imc']
    assert abs(e['media'] - 29.2296) < 1e-3 and abs(e['de'] - 6.2636) < 1e-3 and e['n_referencia'] == 267
    z = matriz('P1')['imc']
    assert abs(z.var(ddof=0) - 0.505) < 0.001
    imp = limpio().reindex(ids())['imc'].isna().to_numpy()
    assert imp.sum() == 262 and (z[imp] == 0).all()
    return f'Media {e["media"]:.4f}, DE {e["de"]:.4f} en 267; varianza en 529 = {z.var(ddof=0):.4f}; 262 imputadas con z = 0'


@prueba(19, 'Adicional', 'Nominal')
def p19():
    m = matriz('P1')
    cols = [c for c in m.columns if c.startswith('quien_prepara_comidas__')]
    assert len(cols) == 5
    e = entrada()['quien_prepara_comidas']
    filas = [m.loc[(e == nivel).to_numpy(), cols].iloc[0].to_numpy() for nivel in ['YO_MAYORIA', 'COMPARTIDO', 'OTRA_HOGAR', 'COMPRO', 'OTRO']]
    d = [((a - b) ** 2).sum() for i, a in enumerate(filas) for b in filas[i + 1:]]
    assert np.ptp(d) < 1e-12 and abs(d[0] - 4.1068) < 1e-3
    assert abs(m[cols].var(ddof=0).sum() - 1) < 1e-12
    return f'Distancia² igual en las 10 parejas ({d[0]:.4f}); varianza total 1'


@prueba(20, 'Adicional', 'Nivel inválido')
def p20():
    e = entrada().iloc[[0]].copy()
    casos = {'frutas_dia': '9', 'tiene_pareja': 'QUIZA', 'quien_prepara_comidas': 'NADIE', 'edad': '300', 'horas_sedentarismo': 'mucho'}
    for es in C.ESCENARIOS:
        for v, x in casos.items():
            mala = e.copy()
            mala[v] = x
            try:
                tr(es).transformar(mala)
            except T.ErrorValor:
                continue
            raise AssertionError((es, v))
    return '5 valores no admitidos × 4 escenarios: error, sin matriz'


@prueba(21, 'Adicional', 'Variable constante')
def p21():
    d = pd.DataFrame({'a': [1.0, 1.0, 1.0], 'b': ['x', 'y', 'x']})
    defs = VF.definiciones(d, ['a'], ['b'])
    for ruta in ('pca', 'famd'):
        try:
            T.calibrar(d, defs, ruta)
        except ValueError as ex:
            assert 'constante' in str(ex)
            continue
        raise AssertionError(ruta)
    return 'DE = 0 detiene la calibración con error; la variable no se elimina en silencio'


@prueba(22, 'Adicional', 'Fuga de ajuste')
def p22():
    antes = huellas_parametros()
    e = entrada().sample(50, random_state=C.SEMILLA)
    copia = json.dumps(tr('F1').p, sort_keys=True)
    t = tr('F1')
    t.transformar(e)
    assert copia == json.dumps(t.p, sort_keys=True) and antes == huellas_parametros()
    assert not hasattr(T.Transformador, 'fit') and not hasattr(T.Transformador, 'calibrar')
    return 'Parámetros intactos en memoria y en disco (SHA-256); el transformador no tiene método de ajuste'


@prueba(23, 'Adicional', 'Verdad del simulador')
def p23():
    leidos = leer(AQUI / 'integridad' / 'archivos_leidos.csv')['archivo_leido'].tolist()
    assert any('dataset_usuaria_sucio.csv' in x for x in leidos), 'el gancho no registró lecturas'
    assert any('diccionario_codificacion_fase36.csv' in x for x in leidos)
    assert not [x for x in leidos if any(p in x for p in C.PROHIBIDOS)]
    assert len(leer(AQUI / 'integridad' / 'escrituras_fuera.csv')) == 0
    for archivo in ('procedencia.py', 'construir_fase36.py', 'transformador.py'):
        codigo = (AQUI / archivo).read_text(encoding='utf-8')
        assert 'auditoria_fase34 as' not in codigo and 'import auditoria_fase34' not in codigo
    return f'{len(leidos)} archivos leídos según el gancho de auditoría: ni la verdad ni la bitácora; sin escrituras fuera de la salida'


@prueba(24, 'Adicional', 'Sensibilidades')
def p24():
    esperado = {'S-TRA': (507, 22), 'S-CUI': (508, 21), 'S-EJE': (454, 75)}
    cat = leer(SENS / 'catalogo_sensibilidades.csv')
    for s, (a, b) in esperado.items():
        p = leer(SENS / 'poblaciones' / f'{s}.csv', dtype=str)
        assert ((p['rol'] == 'ajuste').sum(), (p['rol'] == 'proyeccion').sum()) == (a, b), s
        for e in C.ESCENARIOS:
            fila = cat[cat['id'] == f'{s}_{e}'].iloc[0]
            assert (fila['filas_ajuste'], fila['filas_proyeccion']) == (a, b)
            m = leer(SENS / s / e / 'matriz.csv')
            aj = (p['rol'] == 'ajuste').to_numpy()
            assert np.abs(m[aj].mean()).max() < 1e-12, (s, e)
            assert not m.equals(matriz(e))
            assert T.Transformador.cargar(SENS / s / e).p['orden'] == tr(e).p['orden']
    assert (cat['estado'] == 'preparada, no ejecutada').all()
    assert not list(AQUI.rglob('*cluster*')) and not list(AQUI.rglob('*coordenadas*'))
    return '507 + 22; 508 + 21; 454 + 75. Centradas en las filas de ajuste. 32 preparadas, ninguna ejecutada'


@prueba(25, 'Adicional', 'Etiquetas')
def p25():
    c = celdas()
    her = c[(c['valor_original'] == '') & (c['pregunta_previa_imputada'] == '1')].groupby('variable').size()
    assert her['cantidad_personas_cuida'] == 21 and her['frecuencia_aerobico'] == 29 and her['frecuencia_bajo_impacto'] == 22 and her['frecuencia_fuerza'] == 28
    assert ((c['variable'] == 'trabaja_actualmente') & (c['estado'] == 'imputada')).sum() == 22
    return '22 trabajo imputado; 21 cuidado; 29, 22 y 28 ceros de ejercicio'


@prueba(26, 'Encargo', 'Equivalencia matemática de FAMD')
def p26():
    tabla, info = VF.validar(REFERENCIA['carpeta'])
    assert (tabla['resultado'] == 'OK').all(), tabla[tabla['resultado'] != 'OK'].to_string()
    return f'{len(tabla)} comprobaciones con datos sintéticos, incluido un control negativo; referencia externa: {"prince " + info["version"] if info["disponible"] else "no indicada"}'


@prueba(27, 'Encargo', 'Ausencia de doble escalado del IMC')
def p27():
    obs = limpio().reindex(ids())['imc'].notna().to_numpy()
    for e in ('P1', 'F1'):
        z = matriz(e)['imc']
        assert abs(z.var(ddof=0) - 267 / 529) < 1e-12, (e, z.var(ddof=0))
        assert abs(z[obs].var(ddof=0) - 1) < 1e-12 and abs(z.mean()) < 1e-12
    assert np.array_equal(matriz('P1')['imc'], matriz('F1')['imc'])
    assert 'reescalar_prohibido' in tr('F1').p['esquema']
    assert not any(x in (AQUI / 'transformador.py').read_text(encoding='utf-8') for x in ('StandardScaler', '.fit('))
    return f'Varianza en 529 = 267/529 = {267 / 529:.4f} en P1 y F1; DE 1 solo entre las 267; misma columna en ambas rutas'


@prueba(28, 'Encargo', 'Conservación del cero válido de cuidados')
def p28():
    e = entrada()
    no_cuida = (e['cuida_otras_personas'] == 'NO').to_numpy()
    assert no_cuida.sum() == 278
    p, f = tr('P1'), tr('F1')
    esc = p.p['escaladores']['cantidad_personas_cuida']
    mp, mf = matriz('P1'), matriz('F1')
    assert np.allclose(mp.loc[no_cuida, 'cantidad_personas_cuida'], (0 - esc['media']) / esc['de'], atol=1e-12)
    uno = f.p['escaladores']['cantidad_personas_cuida__0']
    assert np.allclose(mf.loc[no_cuida, 'cantidad_personas_cuida__0'], (1 - uno['p']) / uno['divisor'], atol=1e-12)
    assert abs(uno['p'] - 278 / 529) < 1e-12
    avisos = p.transformar(e)[1]
    k = avisos[avisos['variable'] == 'cantidad_personas_cuida']
    assert set(k['marca']) == {'estructural'} and len(k) == 278
    c = celdas()
    k2 = c[(c['variable'] == 'cantidad_personas_cuida') & (c['valor_original'] == '')]
    assert len(k2) == 278 and set(k2['estado']) == {'no_aplicable'} and (k2['pregunta_previa_imputada'] == '1').sum() == 21
    return '278 ceros como nivel válido, no como ausencia; valor original vacío preservado; 21 marcados como heredados'


@prueba(29, 'Encargo', 'Trazabilidad del ejercicio con ceros heredados')
def p29():
    c = celdas()
    p = leer(SENS / 'poblaciones' / 'S-EJE.csv', dtype=str)
    union = set()
    for v, n in (('frecuencia_aerobico', 29), ('frecuencia_bajo_impacto', 22), ('frecuencia_fuerza', 28)):
        s = c[(c['variable'] == v) & (c['valor_original'] == '') & (c['pregunta_previa_imputada'] == '1')]
        assert len(s) == n and set(s['estado']) == {'no_aplicable'}, v
        marcadas = set(p[p[f'heredado_{v}'] == '1']['participante_id'])
        assert marcadas == set(s['participante_id']), v
        union |= marcadas
    assert union == set(p[p['rol'] == 'proyeccion']['participante_id']) and len(union) == 75
    L = limpio().reindex(ids())
    for v, m in (('frecuencia_aerobico', 'realiza_aerobico'), ('frecuencia_bajo_impacto', 'realiza_bajo_impacto'), ('frecuencia_fuerza', 'realiza_fuerza')):
        marcadas = p[p[f'heredado_{v}'] == '1']['participante_id']
        assert (L.loc[marcadas.to_numpy(), m] == 'NO').all(), v
    return '29, 22 y 28 ceros trazables por participante; unión 75; todos con la madre en NO'


@prueba(30, 'Encargo', 'Codificación de categorías válidas no observadas')
def p30():
    d = leer(AQUI / 'artefactos' / 'diccionario_codificacion_36B.csv', dtype=str, keep_default_na=False)
    no_obs = d[(d['n_529'] == '0')]
    assert len(no_obs) == 13, len(no_obs)
    base = entrada().iloc[[0]].copy()
    antes = huellas_parametros()
    for f in no_obs.itertuples():
        for es in C.ESCENARIOS:
            caso = base.copy()
            caso[f.variable] = f.nivel
            m = C.MADRES.get(f.variable)
            if m:
                caso[m['variable']] = 'SI'
            t = tr(es)
            z, av = t.transformar(caso)
            assert np.isfinite(z.to_numpy()).all()
            if f.variable in C.NUNCA_UNIFICADO:
                assert 'nunca_unificado' in set(av['marca']), f.variable
                cero = base.copy()
                cero[f.variable] = '0'
                cero[m['variable']] = 'SI'
                assert z.equals(t.transformar(cero)[0]), f.variable
            elif es == 'P1':
                e = t.p['escaladores'][f.variable]
                assert abs(z[f.variable].iloc[0] - (int(f.codigo_pca) - e['media']) / e['de']) < 1e-12
                assert 'fuera_rango_referencia' in set(av['marca']), f.variable
    assert antes == huellas_parametros()
    columnas = set(c for e in C.ESCENARIOS for c in tr(e).p['orden'])
    assert not any(f'{v}__' in c and c.endswith('__1') for v in C.NUNCA_UNIFICADO for c in columnas)
    return '13 niveles válidos sin observaciones en 4 escenarios: finitos, sin error ni cambio de parámetros, con marca; «Nunca» igual a «No lo realiza», sin columna propia'


@prueba(31, 'Encargo', 'Reutilización de parámetros con una nueva participante')
def p31():
    # Caso inventado, no es una fila del conjunto.
    nueva = {'edad': 58, 'imc': 33.5, 'horas_sedentarismo': 8, 'trabaja_actualmente': 'True', 'tiene_pareja': 'SI', 'tiene_actividad_sexual': 'NO', 'operada_no_mas_hijos': 'NO',
             'usa_medicamentos_presion': 'SI', 'quien_prepara_comidas': 'OTRO', 'realiza_aerobico': 'NO', 'realiza_bajo_impacto': 'SI', 'realiza_fuerza': 'NO', 'cuida_otras_personas': 'NO',
             'frecuencia_bajo_impacto': 4, 'tabaco_frecuencia': 3}
    for v in C.ORDINALES:
        nueva.setdefault(v, '' if v in C.MADRES else 2)
    caso = pd.DataFrame([nueva], index=['nueva'])
    antes = huellas_parametros()
    for es in C.ESCENARIOS:
        t = tr(es)
        z, _ = t.transformar(caso)
        assert list(z.columns) == t.p['orden'] and z.shape == (1, C.DIMENSIONES[es][1])
        assert z.equals(t.transformar(caso)[0])
    p, f = tr('P1'), tr('F1')
    zp = p.transformar(caso)[0].iloc[0]
    e = p.p['escaladores']
    assert abs(zp['imc'] - (33.5 - e['imc']['media']) / e['imc']['de']) < 1e-12
    assert abs(zp['frecuencia_bajo_impacto'] - (3 - e['frecuencia_bajo_impacto']['media']) / e['frecuencia_bajo_impacto']['de']) < 1e-12
    zf = f.transformar(caso)[0].iloc[0]
    o = f.p['escaladores']['quien_prepara_comidas__COMPRO+OTRO']
    assert abs(zf['quien_prepara_comidas__COMPRO+OTRO'] - (1 - o['p']) / o['divisor']) < 1e-12
    x = f.p['escaladores']['tabaco_frecuencia__2+3+4']
    assert abs(zf['tabaco_frecuencia__2+3+4'] - (1 - x['p']) / x['divisor']) < 1e-12
    # Respuestas ausentes
    sin_imc = caso.assign(imc=np.nan, frutas_dia=np.nan)
    z2, av = p.transformar(sin_imc)
    assert z2['imc'].iloc[0] == 0 and {'imc_ausente', 'ausente'} <= set(av['marca'])
    assert antes == huellas_parametros()
    return 'Caso inventado en 4 escenarios: columnas exactas, valores iguales al cálculo manual, IMC ausente en z = 0 con marca, otra ausente con valor congelado y aviso; parámetros intactos'


@prueba(32, 'Encargo', 'Integridad frente al manifiesto del cierre 34-35')
def p32():
    base = pd.read_csv(C.MANIFIESTO_CIERRE, encoding='utf-8').set_index('ruta')['sha256']
    distintos = [r for r, h in base.items() if not (C.RAIZ / r).exists() or huella(C.RAIZ / r) != h]
    assert not distintos, distintos[:5]

    def git(*a):
        return subprocess.run(['git', *a], cwd=C.RAIZ, capture_output=True, text=True, encoding='utf-8').stdout.strip()
    assert git('rev-parse', '--short', 'HEAD') == C.COMMIT_ESPERADO and not git('diff', '--cached', '--name-only')
    diseno = [p for p in (C.ANALISIS / 'fase36_diseno').rglob('*') if p.is_file()]
    nuevo = min(p.stat().st_mtime for p in (AQUI).glob('configuracion_fase36.py'))
    cambiados = [p.name for p in diseno if p.stat().st_mtime > nuevo and '__pycache__' not in p.parts]
    assert not cambiados, cambiados
    return f'{len(base)} archivos iguales al manifiesto; HEAD {C.COMMIT_ESPERADO}; nada preparado; {len(diseno)} archivos del diseño 36A sin modificar desde antes de la 36B'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--referencia')
    a = ap.parse_args()
    REFERENCIA['carpeta'] = a.referencia
    filas = []
    for numero, grupo, nombre, critica, f in PRUEBAS:
        try:
            detalle = f()
            ok = True
        except Exception as ex:  # noqa: BLE001
            ok, detalle = False, f'{type(ex).__name__}: {ex} | {traceback.format_exc(limit=2)[-300:]}'
        filas.append({'numero': numero, 'grupo': grupo, 'prueba': nombre, 'critica': critica, 'resultado': 'OK' if ok else 'FALLA', 'detalle': detalle})
        print(numero, 'OK' if ok else 'FALLA', '|', nombre, '|', str(detalle)[:170], flush=True)
    t = pd.DataFrame(filas)
    salida = AQUI / 'pruebas'
    salida.mkdir(exist_ok=True)
    t.to_csv(salida / 'resultados_pruebas.csv', index=False, encoding='utf-8', lineterminator='\n')
    print(f'{(t["resultado"] == "OK").sum()} de {len(t)} pruebas superadas')
    return 0 if (t['resultado'] == 'OK').all() else 1


if __name__ == '__main__':
    raise SystemExit(main())
