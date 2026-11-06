"""
Fase 37A: ajusta PCA y FAMD sobre las matrices de la Fase 36, con sus sensibilidades. Solo reducción dimensional.

Uso, desde analisis/: python fase37/37A_reduccion/scripts/ejecutar_37a.py [--salida CARPETA]

No forma clústeres. No abre ningún archivo de datos/ ni lee el MRS: un gancho de auditoría registra lecturas y escrituras.
Se detiene si el protocolo D-13 sellado cambió o si alguna matriz de entrada no coincide con su huella.
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
ANALISIS = BASE.parents[1]
RAIZ = ANALISIS.parent
F36 = ANALISIS / 'fase36'
sys.path[:0] = [str(AQUI)]
ABIERTOS = []


def _gancho(evento, args):
    if evento == 'open' and isinstance(args[0], (str, Path)):
        modo, banderas = args[1], args[2] if len(args) > 2 else 0
        por_modo = isinstance(modo, str) and any(x in modo for x in 'wax+')
        por_bandera = not isinstance(modo, str) and isinstance(banderas, int) and bool(banderas & (os.O_WRONLY | os.O_RDWR))
        ABIERTOS.append((str(args[0]), por_modo or por_bandera))


sys.addaudithook(_gancho)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy  # noqa: E402
import sklearn  # noqa: E402

import reduccion as R  # noqa: E402

ESCENARIOS = {'P1': ('P1_pca_con_imc', 'PCA', True), 'P2': ('P2_pca_sin_imc', 'PCA', False), 'F1': ('F1_famd_con_imc', 'FAMD', True), 'F2': ('F2_famd_sin_imc', 'FAMD', False)}
ESPERADO = {'P1': (529, 34, 29.5047), 'P2': (529, 33, 29.0), 'F1': (529, 50, 38.5047), 'F2': (529, 49, 38.0)}
ORDINALES_CAT = ['frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'cantidad_personas_cuida', 'tabaco_frecuencia']
EJES_ORDEN = 5
N_PERM = 200
SEMILLA = 42
SEM_ESC = {'P1': 1, 'P2': 2, 'F1': 3, 'F2': 4}


def sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def a_csv(t, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')


def a_json(o, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(o, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


def verificar_entradas():
    sello = leer_json(BASE / 'protocolo' / 'sello_protocolo.json')
    if sha(BASE / 'protocolo' / sello['archivo']) != sello['sha256']:
        raise SystemExit('El protocolo D-13 cambió después de sellarse.')
    ids = pd.read_csv(F36 / 'matrices' / 'identificadores.csv', dtype=str)
    matrices = {}
    for e, (nombre, _, _) in ESCENARIOS.items():
        ruta = F36 / 'matrices' / f'{nombre}.csv'
        if sha(ruta) != leer_json(F36 / 'artefactos' / e / 'huellas.json')['matriz']:
            raise SystemExit(f'{e}: la matriz no coincide con su huella.')
        m = pd.read_csv(ruta)
        if list(m.columns) != leer_json(F36 / 'artefactos' / e / 'orden_columnas.json'):
            raise SystemExit(f'{e}: columnas distintas del orden guardado.')
        f, c, i = ESPERADO[e]
        if m.shape != (f, c) or abs(m.var(ddof=0).sum() - i) > 1e-3 or len(m) != len(ids):
            raise SystemExit(f'{e}: dimensiones o inercia inesperadas.')
        matrices[e] = m
    return ids, matrices, sello


def metadatos(carpeta):
    """Columna -> variable y variable -> bloque, desde los artefactos de la Fase 36."""
    esc = leer_json(carpeta / 'escaladores.json')
    esq = leer_json(carpeta / 'esquema_variables.json')
    return {c: e['variable'] for c, e in esc.items()}, {d['variable']: d['seccion'] for d in esq['variables']}


def tablas_modelo(e, modelo, X, col_var, var_blo):
    """Valores propios, cargas y contribuciones de un modelo."""
    lam = np.array(modelo['valores_propios'])
    V = np.array(modelo['componentes'])
    cols = modelo['columnas']
    de = X.std(ddof=0).to_numpy()
    k = modelo['rango']
    total = modelo['inercia_total']
    vp = pd.DataFrame({'escenario': e, 'componente': np.arange(1, k + 1), 'valor_propio': lam, 'pct': 100 * lam / total, 'pct_acumulado': 100 * np.cumsum(lam) / total})
    filas = []
    for a in range(k):
        for j, c in enumerate(cols):
            carga = V[a, j] * np.sqrt(lam[a])
            filas.append((e, a + 1, c, col_var[c], var_blo[col_var[c]], V[a, j], carga, carga / de[j], 100 * V[a, j] ** 2))
    cargas = pd.DataFrame(filas, columns=['escenario', 'componente', 'columna', 'variable', 'bloque', 'vector', 'carga', 'correlacion', 'contribucion_pct'])
    variables = cargas.groupby(['escenario', 'componente', 'variable', 'bloque'], sort=False)['contribucion_pct'].sum().reset_index()
    variables = variables.merge(vp[['componente', 'valor_propio']], on='componente')
    variables['aporte_absoluto'] = variables['contribucion_pct'] / 100 * variables['valor_propio']
    variables = variables.drop(columns='valor_propio')
    bloques = cargas.groupby(['escenario', 'componente', 'bloque'], sort=False)['contribucion_pct'].sum().reset_index()
    acum = []
    for kc in R.CANDIDATOS:
        if kc > k:
            continue
        s = bloques[bloques['componente'] <= kc].merge(vp[['componente', 'valor_propio']], on='componente')
        s = s.assign(a=s['contribucion_pct'] / 100 * s['valor_propio']).groupby('bloque', sort=False)['a'].sum()
        for b, x in s.items():
            acum.append((e, kc, b, 100 * x / lam[:kc].sum()))
    acum = pd.DataFrame(acum, columns=['escenario', 'k', 'bloque', 'contribucion_acumulada_pct'])
    return vp, cargas, variables, bloques, acum


def orden_niveles(e, m, F, carp, celdas, ids):
    """Baricentros de los niveles activos y de los niveles originales de las cinco ordinales categóricas."""
    cod = leer_json(carp / 'codificadores.json')
    filas, orden = [], []
    for v in ORDINALES_CAT:
        grupos = list(cod[v]['grupos'])
        columnas = [f'{v}__{g.replace(" ", "")}' for g in grupos]
        miembros = [m[c].to_numpy() > 0 for c in columnas]
        if not np.all(np.sum(miembros, axis=0) == 1):
            raise SystemExit(f'{v}: una fila no pertenece a exactamente un grupo.')
        bar = np.array([F[x][:, :EJES_ORDEN].mean(axis=0) for x in miembros])
        total = (F[:, :EJES_ORDEN] ** 2).sum(axis=0)
        n = np.array([x.sum() for x in miembros])
        eta2 = ((bar ** 2) * n[:, None]).sum(axis=0) / total
        for g, x, b in zip(grupos, miembros, bar):
            for a in range(EJES_ORDEN):
                filas.append((e, v, 'grupo activo', g, int(x.sum()), a + 1, b[a]))
        # Niveles originales, solo descriptivos: el vacío de estas variables es el nivel estructural 0.
        val = celdas[celdas['variable'] == v].set_index('participante_id')['valor_original'].reindex(ids).replace('', '0').to_numpy()
        niveles = sorted(set(val), key=int)
        bar_o = np.array([F[val == x][:, :EJES_ORDEN].mean(axis=0) for x in niveles])
        for x, b in zip(niveles, bar_o):
            for a in range(EJES_ORDEN):
                filas.append((e, v, 'nivel original', x, int((val == x).sum()), a + 1, b[a]))
        principal = int(np.argmax(eta2))
        for a in range(EJES_ORDEN):
            d = np.diff(bar[:, a])
            do = np.diff(bar_o[:, a])
            orden.append((e, v, a + 1, eta2[a], a == principal, bool((d > 0).all() or (d < 0).all()), bool((do > 0).all() or (do < 0).all())))
    return (pd.DataFrame(filas, columns=['escenario', 'variable', 'tipo_nivel', 'nivel', 'n', 'componente', 'baricentro']),
            pd.DataFrame(orden, columns=['escenario', 'variable', 'componente', 'eta2', 'eje_principal', 'monotono_grupos', 'monotono_niveles_originales']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', default=str(BASE))
    S = Path(ap.parse_args().salida).resolve()
    ids_tabla, matrices, sello = verificar_entradas()
    ids = ids_tabla['participante_id']
    celdas = pd.read_csv(F36 / 'procedencia' / 'procedencia_celdas.csv', dtype=str, keep_default_na=False, usecols=['participante_id', 'variable', 'valor_original'])
    git = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    entorno = {'python': sys.version.split()[0], 'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__, 'scikit_learn': sklearn.__version__, 'semilla_paralelo': SEMILLA,
               'permutaciones_paralelo': N_PERM, 'commit': git, 'protocolo_sha256': sello['sha256']}
    a_json(entorno, S / 'artefactos' / 'entorno.json')

    T = {k: [] for k in ('vp', 'cargas', 'variables', 'bloques', 'acum', 'bar', 'orden', 'umbrales')}
    modelos, coords, metas = {}, {}, {}

    def umbrales(nombre, lam):
        return {'id': nombre, **{f'c{u}': R.componentes_para(lam, u) for u in R.UMBRALES}}

    # ---- escenarios principales
    for e, (nombre, metodo, con_imc) in ESCENARIOS.items():
        m = matrices[e]
        carp = F36 / 'artefactos' / e
        col_var, var_blo = metadatos(carp)
        metas[e] = (col_var, var_blo)
        modelo = R.ajustar(m.to_numpy(), m.columns)
        modelo.update({'escenario': e, 'metodo': metodo, 'con_imc': con_imc, 'matriz_sha256': sha(F36 / 'matrices' / f'{nombre}.csv'), 'transformador_fase36': f'fase36/artefactos/{e}',
                       'orden_columnas_sha256': sha(carp / 'orden_columnas.json'), 'escaladores_sha256': sha(carp / 'escaladores.json'), 'candidatos': [k for k in R.CANDIDATOS]})
        R.guardar(modelo, S / 'artefactos' / e / 'modelo.json')
        F = R.proyectar(modelo, m.to_numpy())
        modelos[e], coords[e] = modelo, F
        vp, cargas, variables, bloques, acum = tablas_modelo(e, modelo, m, col_var, var_blo)
        lam = np.array(modelo['valores_propios'])
        p95 = R.analisis_paralelo(m.to_numpy(), [col_var[c] for c in m.columns], N_PERM, (SEMILLA, SEM_ESC[e]))[:modelo['rango']]
        vp['referencia_ruido_p95'] = p95
        vp['supera_ruido'] = lam > p95
        for k, t in zip(('vp', 'cargas', 'variables', 'bloques', 'acum'), (vp, cargas, variables, bloques, acum)):
            T[k].append(t)
        T['umbrales'].append(umbrales(e, lam))
        for k in R.CANDIDATOS:
            t = pd.DataFrame(F[:, :k], columns=[f'C{i + 1}' for i in range(k)])
            t.insert(0, 'participante_id', ids.to_numpy())
            a_csv(t, S / 'coordenadas' / e / f'coordenadas_k{k:02d}.csv')
        if metodo == 'FAMD':
            b, o = orden_niveles(e, m, F, carp, celdas, ids)
            T['bar'].append(b)
            T['orden'].append(o)

    tablas = S / 'tablas'
    a_csv(pd.concat(T['vp']), tablas / 'valores_propios.csv')
    a_csv(pd.concat(T['cargas']), tablas / 'cargas_columnas.csv')
    a_csv(pd.concat(T['variables']), tablas / 'contribucion_variables.csv')
    a_csv(pd.concat(T['bloques']), tablas / 'contribucion_bloques.csv')
    a_csv(pd.concat(T['acum']), tablas / 'contribucion_bloques_acumulada.csv')
    a_csv(pd.concat(T['bar']), tablas / 'famd_baricentros.csv')
    a_csv(pd.concat(T['orden']), tablas / 'famd_orden_niveles.csv')
    a_csv(pd.DataFrame(T['umbrales']), tablas / 'componentes_para_umbral.csv')

    # ---- comparaciones entre escenarios: filas, no varianza absoluta
    filas = []
    for a, b, tipo in (('P1', 'F1', 'PCA frente a FAMD, con IMC'), ('P2', 'F2', 'PCA frente a FAMD, sin IMC'), ('P1', 'P2', 'Con y sin IMC, PCA'), ('F1', 'F2', 'Con y sin IMC, FAMD')):
        for k in R.CANDIDATOS:
            filas.append((a, b, tipo, k, R.similitud_subespacio(coords[a][:, :k], coords[b][:, :k])))
    a_csv(pd.DataFrame(filas, columns=['a', 'b', 'comparacion', 'k', 'similitud_subespacio']), tablas / 'comparacion_subespacios.csv')
    corr = []
    for a, b in (('P1', 'F1'), ('P2', 'F2'), ('P1', 'P2'), ('F1', 'F2')):
        C = np.corrcoef(coords[a][:, :5].T, coords[b][:, :10].T)[:5, 5:]
        for i in range(5):
            corr.append((a, b, i + 1, int(np.argmax(np.abs(C[i]))) + 1, float(np.abs(C[i]).max())))
    a_csv(pd.DataFrame(corr, columns=['a', 'b', 'eje_a', 'eje_b_mas_parecido', 'correlacion_absoluta']), tablas / 'correspondencia_ejes.csv')

    # ---- sensibilidades
    sens = S / 'sensibilidades'
    cat = pd.read_csv(F36 / 'sensibilidades' / 'catalogo_sensibilidades.csv')
    pesos = leer_json(F36 / 'sensibilidades' / 'pesos_bloques.json')['escenarios']
    poblaciones = {s: pd.read_csv(F36 / 'sensibilidades' / 'poblaciones' / f'{s}.csv', dtype=str) for s in ('S-TRA', 'S-CUI', 'S-EJE')}
    res, simil, corr_ejes, proy, imc_bloque, pesos_sa = [], [], [], [], [], {}

    def evaluar(sid, e, Z, col_var, var_blo, extra, filas_ajuste=None):
        """Ajusta una variante, guarda modelo y coordenadas, y la compara con su base en las filas comunes."""
        aj = np.ones(len(Z), bool) if filas_ajuste is None else filas_ajuste
        X = Z[aj]
        modelo = R.ajustar(X.to_numpy(), Z.columns)
        modelo.update({'sensibilidad': sid, 'base': e, **extra})
        carpeta = sens / sid / e
        R.guardar(modelo, carpeta / 'modelo.json')
        F = R.proyectar(modelo, Z.to_numpy())
        km = min(20, modelo['rango'])
        t = pd.DataFrame(F[:, :km], columns=[f'C{i + 1}' for i in range(km)])
        t.insert(0, 'participante_id', ids.to_numpy())
        a_csv(t[aj], carpeta / 'coordenadas_ajuste.csv')
        if filas_ajuste is not None:
            a_csv(t[~aj], carpeta / 'coordenadas_proyeccion.csv')
        lam = np.array(modelo['valores_propios'])
        acumulado = 100 * np.cumsum(lam) / lam.sum()
        vt, _, variables, bloques, _ = tablas_modelo(f'{sid}_{e}', modelo, X, col_var, var_blo)
        top = variables[variables['componente'] == 1].sort_values('contribucion_pct', ascending=False).iloc[0]
        top2 = variables[variables['componente'] == 2].sort_values('contribucion_pct', ascending=False).iloc[0]
        res.append({'sensibilidad': sid, 'base': e, 'filas_ajuste': int(aj.sum()), 'filas_proyeccion': int((~aj).sum()), 'columnas': Z.shape[1], 'rango': modelo['rango'], 'inercia_filas_ajuste': modelo['inercia_total'],
                    **{f'pct_k{k}': acumulado[k - 1] for k in R.CANDIDATOS if k <= modelo['rango']}, **{f'c{u}': R.componentes_para(lam, u) for u in R.UMBRALES},
                    'eje1_variable_principal': top['variable'], 'eje1_contribucion_pct': top['contribucion_pct'], 'eje2_variable_principal': top2['variable'], 'eje2_contribucion_pct': top2['contribucion_pct']})
        for k in R.CANDIDATOS:
            if k <= modelo['rango']:
                simil.append((sid, e, k, R.similitud_subespacio(coords[e][aj][:, :k], F[aj][:, :k])))
        C = np.corrcoef(coords[e][aj][:, :5].T, F[aj][:, :min(10, modelo['rango'])].T)[:5, 5:]
        for i in range(5):
            corr_ejes.append((sid, e, i + 1, int(np.argmax(np.abs(C[i]))) + 1, float(np.abs(C[i]).max())))
        if filas_ajuste is not None:
            for k in (5, 8, 12):
                Rot = R.procrustes(coords[e][aj][:, :k], F[aj][:, :k])
                dif = F[~aj][:, :k] @ Rot - coords[e][~aj][:, :k]
                escala = np.sqrt(((coords[e][aj][:, :k] - coords[e][aj][:, :k].mean(axis=0)) ** 2).sum(axis=1).mean())
                dif_aj = F[aj][:, :k] @ Rot - coords[e][aj][:, :k]
                proy.append((sid, e, k, int((~aj).sum()), float(np.sqrt((dif ** 2).sum(axis=1).mean()) / escala), float(np.sqrt((dif_aj ** 2).sum(axis=1).mean()) / escala)))
        return modelo, bloques, variables

    for f in cat.itertuples():
        sid, e = f.sensibilidad, f.base
        m = matrices[e]
        if sid in ('S-ORD', 'S-FAMD', 'S-RARA', 'S-TRA', 'S-CUI', 'S-EJE'):
            carp = F36 / 'sensibilidades' / sid / e
            Z = pd.read_csv(carp / 'matriz.csv')
            col_var, var_blo = metadatos(carp)
            aj = (poblaciones[sid]['rol'] == 'ajuste').to_numpy() if sid in poblaciones else None
            evaluar(sid, e, Z, col_var, var_blo, {'matriz_sha256': sha(carp / 'matriz.csv'), 'transformador_fase36': f'fase36/sensibilidades/{sid}/{e}'}, aj)
        elif sid in ('S-EDAD', 'S-SOLAPE'):
            col_var, var_blo = metas[e]
            quitar = ['edad'] if sid == 'S-EDAD' else ['tiene_actividad_sexual', 'distension_abdominal']
            omitidas = [c for c in m.columns if col_var[c] in quitar]
            evaluar(sid, e, m.drop(columns=omitidas), col_var, var_blo, {'columnas_omitidas': omitidas, 'transformador_fase36': f'fase36/artefactos/{e}'})
        elif sid == 'S-BLOQUE':
            col_var, var_blo = metas[e]
            mult = pd.Series(pesos[e]['multiplicador_por_columna'])[m.columns]
            _, bloques, variables = evaluar(sid, e, m * mult, col_var, var_blo, {'multiplicadores': mult.to_dict(), 'transformador_fase36': f'fase36/artefactos/{e}'})
            if 'imc' in m.columns:
                imc_bloque.append(('S-BLOQUE', e, float(mult['imc']), variables))

    # Variante nueva: el IMC conserva multiplicador 1; los otros siete bloques se igualan con la inercia restante.
    for e in ('P1', 'F1'):
        m = matrices[e]
        col_var, var_blo = metas[e]
        bl_imc = var_blo['imc']
        inercia = {}
        for c in m.columns:
            b = var_blo[col_var[c]]
            inercia[b] = inercia.get(b, 0.0) + float(m[c].var(ddof=0))
        v_imc = inercia.pop(bl_imc)
        objetivo = sum(inercia.values()) / len(inercia)
        mb = {b: float(np.sqrt(objetivo / x)) for b, x in inercia.items()} | {bl_imc: 1.0}
        mult = pd.Series({c: mb[var_blo[col_var[c]]] for c in m.columns})
        pesos_sa[e] = {'objetivo_otros_bloques': objetivo, 'inercia_imc': v_imc, 'multiplicador_por_bloque': mb, 'multiplicador_por_columna': mult.to_dict()}
        _, _, variables = evaluar('S-BLOQUE-SA', e, m * mult, col_var, var_blo, {'multiplicadores': mult.to_dict(), 'transformador_fase36': f'fase36/artefactos/{e}'})
        imc_bloque.append(('S-BLOQUE-SA', e, 1.0, variables))
    a_json({'descripcion': 'Variante nueva de la Fase 37A: IMC sin amplificar. No modifica la Fase 36.', 'escenarios': pesos_sa}, sens / 'pesos_bloque_sa.json')

    a_csv(pd.DataFrame(res), tablas / 'sens_resumen.csv')
    a_csv(pd.DataFrame(simil, columns=['sensibilidad', 'base', 'k', 'similitud_subespacio']), tablas / 'sens_similitud.csv')
    a_csv(pd.DataFrame(corr_ejes, columns=['sensibilidad', 'base', 'eje_base', 'eje_variante', 'correlacion_absoluta']), tablas / 'sens_correlacion_ejes.csv')
    a_csv(pd.DataFrame(proy, columns=['sensibilidad', 'base', 'k', 'filas_proyectadas', 'desplazamiento_proyectadas', 'desplazamiento_ajuste']), tablas / 'sens_proyeccion.csv')
    # IMC en cada eje: escenarios principales y variantes de bloque
    filas = []
    vb = pd.concat(T['variables'])
    for e in ('P1', 'F1'):
        s = vb[(vb['escenario'] == e) & (vb['variable'] == 'imc')]
        for x in s.itertuples():
            filas.append(('principal', e, 1.0, x.componente, x.contribucion_pct))
    for sid, e, mult, variables in imc_bloque:
        s = variables[variables['variable'] == 'imc']
        for x in s.itertuples():
            filas.append((sid, e, mult, x.componente, x.contribucion_pct))
    a_csv(pd.DataFrame(filas, columns=['variante', 'base', 'multiplicador_imc', 'componente', 'contribucion_pct']), tablas / 'imc_por_eje.csv')

    # ---- registro de lecturas y escrituras
    raiz, leidos, fuera = RAIZ.resolve(), set(), set()
    for ruta, escribe in ABIERTOS:
        absoluta = Path(ruta).resolve()
        if escribe and not absoluta.is_relative_to(S):
            fuera.add(ruta)
        if not escribe and absoluta.is_relative_to(raiz) and (not absoluta.is_relative_to(S) or absoluta.is_relative_to(BASE / 'protocolo')) and absoluta.suffix not in ('.py', '.pyc') and absoluta.is_file() and '.git' not in absoluta.parts:
            leidos.add(absoluta.relative_to(raiz).as_posix())
    a_csv(pd.DataFrame({'archivo_leido': sorted(leidos)}), S / 'integridad' / 'archivos_leidos.csv')
    a_csv(pd.DataFrame({'escritura_fuera_de_salida': sorted(fuera)}, dtype=str), S / 'integridad' / 'escrituras_fuera.csv')
    if fuera or [x for x in leidos if x.startswith('datos/')]:
        raise SystemExit(f'Lectura de datos/ o escritura fuera de la salida: {sorted(fuera)} {[x for x in leidos if x.startswith("datos/")]}')

    producidos = sorted(p for d in ('tablas', 'coordenadas', 'artefactos', 'sensibilidades', 'integridad') for p in (S / d).rglob('*') if p.is_file() and not p.name.startswith('manifiesto_'))
    with (S / 'integridad' / 'manifiesto_ejecucion.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['ruta', 'sha256', 'bytes'])
        for p in producidos:
            w.writerow([p.relative_to(S).as_posix(), sha(p), p.stat().st_size])
    print('Archivos:', len(producidos) + 1, '| variantes:', len(res))
    for e in ESCENARIOS:
        print(e, 'rango', modelos[e]['rango'], 'inercia', round(modelos[e]['inercia_total'], 4), 'suma λ', round(sum(modelos[e]['valores_propios']), 4))


if __name__ == '__main__':
    main()
