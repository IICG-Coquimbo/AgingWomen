"""
Fase 36B: construye las matrices de entrada para PCA y FAMD, sus transformadores y las poblaciones de sensibilidad.

Uso, desde analisis/: python fase36/construir_fase36.py [--salida CARPETA]

No ajusta PCA, FAMD, K-means ni aglomerativo. No lee la verdad del simulador ni la bitácora. Solo escribe dentro de la carpeta
de salida. Toda lectura y escritura queda registrada mediante un gancho de auditoría de Python, y el registro se guarda.
No usa azar ni la hora, de modo que dos ejecuciones producen los mismos bytes.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path[:0] = [str(AQUI), str(AQUI.parent), str(AQUI.parent / 'revision_correctiva_fase34')]
sys.dont_write_bytecode = True
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

import configuracion_fase36 as C  # noqa: E402
import procedencia as PR  # noqa: E402
import transformador as T  # noqa: E402
from manifiesto import huella  # noqa: E402


def leer_csv(ruta, **k):
    return pd.read_csv(ruta, encoding='utf-8-sig', **k)


def a_csv(tabla, ruta, **k):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n', **k)


def a_json(objeto, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(objeto, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


def definiciones():
    """Una definición por variable general, tomada del diccionario aprobado. Los niveles salen del instrumento, no de los datos."""
    dic = leer_csv(C.DICCIONARIO, dtype=str, keep_default_na=False)
    mat = leer_csv(C.MATRIZ_DECISIONES, dtype=str, keep_default_na=False).set_index('variable')
    salida = []
    for v in C.GENERALES:
        tipo = 'cuantitativa' if v in C.CUANTITATIVAS else 'binaria' if v in C.BINARIAS else 'nominal' if v in C.NOMINALES else 'ordinal'
        d = {'variable': v, 'tipo': tipo, 'seccion': mat.loc[v, 'seccion_encuesta'],
             'rol_famd': {'cuantitativa': 'cuantitativa', 'categórica': 'categorica'}[mat.loc[v, 'rol_famd']]}
        if tipo == 'cuantitativa':
            d['limites'] = list(C.LIMITES[v])
            d['niveles'] = None
            d['ausente_es_media'] = v == 'imc'
        else:
            niveles = {}
            for f in dic[dic['variable'] == v].itertuples():
                clave = f.codigo_en_dataset_fase35 if tipo == 'ordinal' else f.nivel_instrumento
                codigo = None if tipo == 'nominal' else int(f.codificacion_pca)
                niveles[clave] = {'codigo': codigo, 'significado': f.significado}
            d['niveles'] = niveles
            d['madre'] = C.MADRES.get(v)
            d['nunca_unificado'] = v in C.NUNCA_UNIFICADO
            if v in C.GRUPOS_FAMD:
                d['grupos_famd'] = C.GRUPOS_FAMD[v]
        salida.append(d)
    return salida


def sin(defs, *quitar):
    return [d for d in defs if d['variable'] not in quitar]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', default=str(C.SALIDA_POR_DEFECTO))
    S = Path(ap.parse_args().salida).resolve()

    f35 = leer_csv(C.F35, dtype=str, keep_default_na=False)
    ids = f35['participante_id']
    celdas, L = PR.tabla_celdas(ids)
    res = PR.resumen(celdas)
    contraste = PR.contrastar(res, L)
    if not contraste['coincide'].all():
        raise SystemExit('La procedencia reconstruida no coincide con las auditorías históricas.')

    columnas = C.GENERALES + C.CAMPOS_CONTEXTO
    entrada = L.reindex(ids)[columnas].copy()     # Ninguna columna del MRS, de los módulos ni de auditoría entra aquí.
    generales = celdas[celdas['variable'].isin(C.GENERALES)].assign(i=lambda t: t['estado'] == 'imputada')
    imputadas = generales.pivot(index='participante_id', columns='variable', values='i').reindex(ids)
    defs = definiciones()

    a_csv(pd.DataFrame({'fila': range(len(ids)), 'participante_id': ids}), S / 'matrices' / 'identificadores.csv')
    catalogo, parametros_tabla, resumen_matrices = [], [], {}
    entradas = {p.name: huella(p) for p in [C.SUCIO, C.LIMPIO, C.F35, C.DICCIONARIO, C.MATRIZ_DECISIONES, C.RELEVANCIA, C.ORIGEN, C.AUDITORIA_FIGURAS]}
    git = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=C.RAIZ, capture_output=True, text=True).stdout.strip()
    entorno = {'version_parametros': C.VERSION, 'fecha_version': C.FECHA_VERSION, 'commit': git, 'semilla_validacion': C.SEMILLA,
               'python': sys.version.split()[0], 'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__, 'scikit_learn': sklearn.__version__,
               'nota': 'La construcción no usa azar. scikit-learn solo interviene en la validación con datos de prueba.'}

    def escenario(carpeta, archivo, nombre, ruta, con_imc, **k):
        ds = defs if con_imc else sin(defs, 'imc')
        params = T.calibrar(entrada, ds, ruta, excluir_de_congelado=imputadas, **k)
        tr = T.Transformador(params)
        matriz, avisos = tr.transformar(entrada)
        tr.guardar(carpeta)
        a_json(entorno, carpeta / 'entorno.json')
        vistas = [d['variable'] for d in ds]
        a_json({'imputadas_por_variable': {v: int(res.loc[v, 'imputada']) for v in vistas},
                'heredadas_por_variable': {v: int(res.loc[v, 'heredadas']) for v in vistas if res.loc[v, 'heredadas']},
                'avisos_al_transformar_referencia': {k2: int(n) for k2, n in avisos.groupby('marca').size().items()} if len(avisos) else {},
                'detalle_por_celda': 'procedencia/procedencia_celdas.csv'}, carpeta / 'procedencia.json')
        matriz = matriz.reset_index(drop=True)
        a_csv(matriz, archivo)
        artefactos = {x.name: huella(x) for x in sorted(carpeta.glob('*.json')) if x.name != 'huellas.json'}
        a_json({'entradas': entradas, 'matriz': huella(archivo), 'artefactos': artefactos}, carpeta / 'huellas.json')
        resumen_matrices[nombre] = {'filas': matriz.shape[0], 'columnas': matriz.shape[1], 'inercia': float(matriz.var(ddof=0).sum())}
        return tr, matriz

    # ---- escenarios principales
    principales = {}
    for e, (ruta, con_imc) in C.ESCENARIOS.items():
        tr, matriz = escenario(S / 'artefactos' / e, S / 'matrices' / f'{C.NOMBRE_ARCHIVO[e]}.csv', e, ruta, con_imc)
        principales[e] = (tr, matriz)
        for col, x in tr.p['escaladores'].items():
            parametros_tabla.append({'escenario': e, 'columna': col, 'variable': x['variable'], 'clase': x['clase'], 'media': x.get('media', ''), 'de': x.get('de', ''),
                                     'grupo': x.get('grupo', ''), 'p': x.get('p', ''), 'divisor': x.get('divisor', ''), 'n_referencia': x.get('n_referencia', 529),
                                     'varianza_en_529': float(matriz[col].var(ddof=0))})
    a_csv(pd.DataFrame(parametros_tabla), S / 'artefactos' / 'parametros_escalado.csv')

    # ---- diccionario final y agrupaciones
    filas, grupos_filas = [], []
    tr_f = principales['F1'][0]
    for d in defs:
        v = d['variable']
        if d['tipo'] == 'cuantitativa':
            filas.append({'variable': v, 'tipo': d['tipo'], 'rol_famd': d['rol_famd'], 'nivel': 'numérico', 'significado': 'valor', 'codigo_pca': 'z',
                          'grupo_famd': 'cuantitativa', 'n_529': 529 if v != 'imc' else 267, 'unificado_con_cero': False})
            continue
        n = entrada[v].map(T._texto)
        madre = d.get('madre')
        if madre:
            n = n.where(n != '', madre['estructural'])
        cuentas = n.value_counts()
        cf = tr_f.p['codificadores'][v]
        for nivel, x in d['niveles'].items():
            grupo = next((g for g, ns in cf['grupos'].items() if nivel in ns), '') if 'grupos' in cf else 'cuantitativa'
            filas.append({'variable': v, 'tipo': d['tipo'], 'rol_famd': d['rol_famd'], 'nivel': nivel, 'significado': x['significado'],
                          'codigo_pca': '' if x['codigo'] is None else x['codigo'], 'grupo_famd': grupo, 'n_529': int(cuentas.get(nivel, 0)),
                          'unificado_con_cero': v in C.NUNCA_UNIFICADO and nivel == '1'})
        if d['rol_famd'] == 'categorica':
            for g, ns in cf['grupos'].items():
                p = cf['proporciones'][g]
                grupos_filas.append({'variable': v, 'grupo': g, 'niveles': ' | '.join(ns), 'n_529': int(sum(cuentas.get(x, 0) for x in ns)), 'p': p,
                                     'columna': f'{v}__{g.replace(" ", "")}', 'valor_maximo_columna': (1 - p) / np.sqrt(p)})
    a_csv(pd.DataFrame(filas), S / 'artefactos' / 'diccionario_codificacion_36B.csv')
    a_csv(pd.DataFrame(grupos_filas), S / 'artefactos' / 'agrupaciones_categorias.csv')

    esquema = {'descripcion': 'Campos que necesita el transformador para una participante nueva. Ningún parámetro se recalcula.',
               'version_parametros': C.VERSION, 'variables': C.GENERALES,
               'campos_contexto': {k: 'Solo decide si la pregunta condicional aplica; no es variable de agrupamiento.' for k in C.CAMPOS_CONTEXTO},
               'niveles_admitidos': {d['variable']: (list(d['niveles']) if d['niveles'] else {'limites_plausibles': d['limites']}) for d in defs},
               'reglas_valores_desconocidos': T.REGLAS_DESCONOCIDOS,
               'flujo': ['validar esquema', 'aplicar reglas condicionales', 'codificar con mapas guardados', 'completar con valores congelados y marcar',
                         'escalar con parámetros guardados', 'ordenar columnas', 'proyectar (Fases 37 y 40)'],
               'uso': "from transformador import Transformador; matriz, avisos = Transformador.cargar('artefactos/P1').transformar(tabla)",
               'congelacion': 'Cambiar cualquier parámetro exige una versión nueva de parámetros y de perfiles. No se recalibra al llegar una usuaria.',
               'advertencia': 'La columna IMC ya tiene varianza 0,505: no aplicar otra estandarización. Los módulos no alimentan el perfil general.'}
    a_json(esquema, S / 'artefactos' / 'esquema_nueva_participante.json')

    # ---- procedencia
    a_csv(celdas, S / 'procedencia' / 'procedencia_celdas.csv')
    a_csv(res.reset_index(), S / 'procedencia' / 'resumen_por_variable.csv')
    a_csv(contraste, S / 'procedencia' / 'contraste_auditorias.csv')

    # ---- módulos: sin escalar, con valores del conjunto limpio. No se forman clústeres.
    lim = L.reindex(ids)
    estado = celdas.pivot(index='participante_id', columns='variable', values='estado').reindex(ids)
    con_lab = lim[C.LABORALES].notna().all(axis=1)
    lab = pd.DataFrame({'participante_id': ids[con_lab.to_numpy()].to_numpy()})
    for v in C.LABORALES:
        lab[v] = lim.loc[con_lab, v].to_numpy()
        lab[f'estado_{v}'] = estado.loc[con_lab, v].to_numpy()
    lab['sensibilidad_ambas_observadas'] = (estado.loc[con_lab, C.LABORALES] == 'observada').all(axis=1).to_numpy().astype(int)
    a_csv(lab, S / 'modulos' / 'modulo_laboral.csv')
    con_cui = lim[C.SOBRECARGA].notna()
    cui = pd.DataFrame({'participante_id': ids[con_cui.to_numpy()].to_numpy(), C.SOBRECARGA: lim.loc[con_cui, C.SOBRECARGA].to_numpy(),
                        f'estado_{C.SOBRECARGA}': estado.loc[con_cui, C.SOBRECARGA].to_numpy()})
    cui['principal_observada'] = (cui[f'estado_{C.SOBRECARGA}'] == 'observada').astype(int)
    a_csv(cui, S / 'modulos' / 'modulo_cuidados.csv')

    # ---- poblaciones de sensibilidad
    previa = {v: celdas[(celdas['variable'] == v) & (celdas['valor_original'] == '') & (celdas['pregunta_previa_imputada'] == 1)]['participante_id']
              for v in C.NUNCA_UNIFICADO + ['cantidad_personas_cuida']}
    conjuntos = {'S-TRA': set(celdas[(celdas['variable'] == 'trabaja_actualmente') & (celdas['estado'] == 'imputada')]['participante_id']),
                 'S-CUI': set(previa['cantidad_personas_cuida']),
                 'S-EJE': set().union(*[set(previa[v]) for v in C.NUNCA_UNIFICADO])}
    for clave, conjunto in conjuntos.items():
        t = pd.DataFrame({'participante_id': ids, 'rol': ['proyeccion' if i in conjunto else 'ajuste' for i in ids]})
        if clave == 'S-EJE':
            for v in C.NUNCA_UNIFICADO:
                t[f'heredado_{v}'] = ids.isin(previa[v]).astype(int).to_numpy()
        a_csv(t, S / 'sensibilidades' / 'poblaciones' / f'{clave}.csv')

    # ---- sensibilidades preparadas, no ejecutadas: ningún modelo las usa todavía
    sens = S / 'sensibilidades'

    def preparar(sid, e, factor, **k):
        ruta, con_imc = C.ESCENARIOS[e]
        nombre = f'{sid}_{e}'
        filas_aj = k.get('filas_ajuste')
        _, matriz = escenario(sens / sid / e, sens / sid / e / 'matriz.csv', nombre, ruta, con_imc, **k)
        catalogo.append({'id': nombre, 'sensibilidad': sid, 'factor': factor, 'base': e, 'filas': len(matriz), 'columnas': matriz.shape[1],
                         'filas_ajuste': int(filas_aj.sum()) if filas_aj is not None else 529, 'filas_proyeccion': int((~filas_aj).sum()) if filas_aj is not None else 0,
                         'inercia_en_529': round(float(matriz.var(ddof=0).sum()), 6), 'estado': 'preparada, no ejecutada', 'archivo': f'sensibilidades/{sid}/{e}/matriz.csv'})

    for e in C.ESCENARIOS:
        preparar('S-ORD', e, 'Ordinales en ridit en vez de códigos consecutivos', modo_ordinal='ridit')
    for e in ('F1', 'F2'):
        preparar('S-FAMD', e, 'Las cinco ordinales categóricas pasan a cuantitativas', roles={v: 'cuantitativa' for v in C.ORDINALES_CATEGORICAS})
        preparar('S-RARA', e, 'FAMD sin agrupar categorías raras', grupos=C.GRUPOS_SIN_AGRUPAR)
    for clave, conjunto in conjuntos.items():
        ajuste = pd.Series([i not in conjunto for i in ids], index=ids)
        for e in C.ESCENARIOS:
            preparar(clave, e, 'Ajustar sin las marcadas y proyectarlas con parámetros congelados (grupos de FAMD fijos)', filas_ajuste=ajuste)
    for sid, factor, quitar in (('S-EDAD', 'Sin edad', ['edad']), ('S-SOLAPE', 'Sin tiene_actividad_sexual ni distension_abdominal', ['tiene_actividad_sexual', 'distension_abdominal'])):
        for e, (tr, m) in principales.items():
            fuera_col = [c for c in m.columns if tr.p['escaladores'][c]['variable'] in quitar]
            catalogo.append({'id': f'{sid}_{e}', 'sensibilidad': sid, 'factor': factor, 'base': e, 'filas': 529, 'columnas': m.shape[1] - len(fuera_col), 'filas_ajuste': 529, 'filas_proyeccion': 0,
                             'inercia_en_529': round(float(m.drop(columns=fuera_col).var(ddof=0).sum()), 6), 'estado': 'preparada, no ejecutada',
                             'archivo': f'matrices/{C.NOMBRE_ARCHIVO[e]}.csv, omitiendo: {"; ".join(fuera_col)}'})
    bloques = {d['variable']: d['seccion'] for d in defs}
    pesos = {}
    for e, (tr, m) in principales.items():
        pesos[e] = T.pesos_por_bloque(m, tr.p['escaladores'], bloques)
        catalogo.append({'id': f'S-BLOQUE_{e}', 'sensibilidad': 'S-BLOQUE', 'factor': 'Misma inercia total por bloque', 'base': e, 'filas': 529, 'columnas': m.shape[1], 'filas_ajuste': 529, 'filas_proyeccion': 0,
                         'inercia_en_529': round(pesos[e]['inercia_total'], 6), 'estado': 'preparada, no ejecutada', 'archivo': f'matrices/{C.NOMBRE_ARCHIVO[e]}.csv por sensibilidades/pesos_bloques.json'})
    a_json({'descripcion': 'Multiplicadores de S-BLOQUE. No se aplicaron a matrices principales ni a clústeres.', 'escenarios': pesos}, sens / 'pesos_bloques.json')
    a_csv(pd.DataFrame(catalogo), sens / 'catalogo_sensibilidades.csv')
    a_json(resumen_matrices, S / 'matrices' / 'resumen_matrices.json')

    # ---- registro de lecturas y escrituras
    raiz, leidos, fuera = C.RAIZ.resolve(), set(), set()
    for ruta, escribe in ABIERTOS:
        absoluta = Path(ruta).resolve()
        if escribe and not absoluta.is_relative_to(S):
            fuera.add(ruta)
        relevante = absoluta.is_relative_to(raiz) and not absoluta.is_relative_to(S) and absoluta.suffix not in ('.py', '.pyc') and absoluta.is_file() and '.git' not in absoluta.parts
        if not escribe and relevante:
            leidos.add(absoluta.relative_to(raiz).as_posix())
    a_csv(pd.DataFrame({'archivo_leido': sorted(leidos)}), S / 'integridad' / 'archivos_leidos.csv')
    a_csv(pd.DataFrame({'escritura_fuera_de_salida': sorted(fuera)}, dtype=str), S / 'integridad' / 'escrituras_fuera.csv')
    prohibidos = [x for x in leidos if any(p in x for p in C.PROHIBIDOS)]
    if prohibidos or fuera:
        raise SystemExit(f'Se abrió un archivo prohibido {prohibidos} o se escribió fuera de la salida {sorted(fuera)}.')

    # ---- manifiesto de lo producido por esta construcción
    producidos = sorted(p for d in ('matrices', 'artefactos', 'procedencia', 'modulos', 'sensibilidades', 'integridad') for p in (S / d).rglob('*')
                        if p.is_file() and p.name != 'manifiesto_fase36.csv')
    with (S / 'integridad' / 'manifiesto_fase36.csv').open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['ruta', 'sha256', 'bytes'])
        for p in producidos:
            w.writerow([p.relative_to(S).as_posix(), huella(p), p.stat().st_size])
    print({k: (v['filas'], v['columnas'], round(v['inercia'], 4)) for k, v in resumen_matrices.items() if k in C.ESCENARIOS})
    print('Sensibilidades:', len(catalogo), '| poblaciones:', {k: len(v) for k, v in conjuntos.items()},
          '| módulos:', len(lab), int(lab['sensibilidad_ambas_observadas'].sum()), len(cui), int(cui['principal_observada'].sum()))
    print('Archivos producidos:', len(producidos) + 1)


if __name__ == '__main__':
    main()
