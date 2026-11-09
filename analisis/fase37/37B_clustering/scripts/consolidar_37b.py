"""
Fase 37B: reúne los lotes en las tablas de entrega y aplica las comparaciones del protocolo. No ajusta ningún algoritmo. Se detiene si falta algún trabajo.

Uso, desde analisis/: python fase37/37B_clustering/scripts/consolidar_37b.py [--salida CARPETA]
"""
import argparse
import json
from pathlib import Path

import nucleo_37b as Q
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

MEDIDAS_NULA = {'silueta': 1, 'davies_bouldin': -1, 'calinski_harabasz': 1, 'ari_completo_media': 1, 'ari_entre_media': 1, 'ari_fuera_media': 1}
COMUNES = ['config', 'espacio', 'base', 'metodo', 'con_imc', 'componentes', 'algoritmo', 'k']


def a_csv(t, ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')


def cargar_lotes(S):
    cfgs = Q.configuraciones()
    faltan = [c['config'] for c in cfgs if not (S / 'resultados' / 'lotes' / f'{c["config"]}.json').exists()]
    if faltan:
        raise SystemExit(f'Faltan {len(faltan)} configuraciones: {faltan[:5]}')
    return [json.loads((S / 'resultados' / 'lotes' / f'{c["config"]}.json').read_text(encoding='utf-8')) for c in cfgs]


def imc_observado():
    c = pd.read_csv(Q.F36 / 'procedencia' / 'procedencia_celdas.csv', dtype=str, keep_default_na=False)
    x = c[c['variable'] == 'imc'].set_index('participante_id').reindex(Q.identificadores())
    return (x['estado'] == 'observada').to_numpy()


def nula_por_config(nula, obs):
    """Compara cada configuración con sus 20 réplicas. El sentido de Davies-Bouldin se invierte: en esta tabla, mejor siempre es más alto."""
    filas = []
    por = {c: g.sort_values('replica') for c, g in nula.groupby('config')}
    for _, o in obs.iterrows():
        g = por[o['config']]
        f = {'config': o['config']}
        for m, s in MEDIDAS_NULA.items():
            v = g[m].to_numpy() * s
            x = o[m] * s
            f[f'{m}_obs'] = o[m]
            f[f'{m}_nula_media'] = g[m].mean()
            f[f'{m}_nula_de'] = g[m].std(ddof=1)
            f[f'{m}_nula_min'] = g[m].min()
            f[f'{m}_nula_max'] = g[m].max()
            f[f'{m}_z'] = (x - v.mean()) / v.std(ddof=1) if v.std(ddof=1) > 0 else np.nan
            f[f'{m}_p'] = (1 + (v >= x).sum()) / (len(v) + 1)
            f[f'{m}_supera_todas'] = bool((x > v).all())
        filas.append(f)
    return pd.DataFrame(filas)


def busqueda_multiple(nula, obs):
    """Controles de la búsqueda sobre 420 configuraciones: el mayor z y el conteo de configuraciones que superan a todas las réplicas.

    Cada réplica se trata como si fuera el dato observado, con media y DE de las otras 19.
    """
    filas = []
    orden = obs['config'].tolist()
    reps = sorted(nula['replica'].unique())
    for m, s in MEDIDAS_NULA.items():
        A = nula.pivot(index='replica', columns='config', values=m).loc[reps, orden].to_numpy() * s
        x = obs.set_index('config').loc[orden, m].to_numpy() * s
        de = A.std(axis=0, ddof=1)
        z = (x - A.mean(axis=0)) / de
        z_max_obs = float(np.nanmax(z))
        cuenta_obs = int((x > A.max(axis=0)).sum())
        zr, cr = [], []
        for i in range(len(reps)):
            otras = np.delete(A, i, axis=0)
            zr.append(float(np.nanmax((A[i] - otras.mean(axis=0)) / otras.std(axis=0, ddof=1))))
            cr.append(int((A[i] > otras.max(axis=0)).sum()))
        filas.append({'medida': m, 'z_max_observado': z_max_obs, 'config_z_max': orden[int(np.nanargmax(z))], 'z_max_nula_mediana': float(np.median(zr)), 'z_max_nula_max': float(np.max(zr)), 'p_z_max': (1 + sum(v >= z_max_obs for v in zr)) / (len(zr) + 1),
                      'conteo_supera_observado': cuenta_obs, 'conteo_nula_mediana': float(np.median(cr)), 'conteo_nula_max': int(np.max(cr)), 'p_conteo': (1 + sum(v >= cuenta_obs for v in cr)) / (len(cr) + 1)})
    return pd.DataFrame(filas)


def preseleccion(t, resumen_sens, M=12):
    """Regla de la sección 11 del protocolo. No hay puntuación compuesta ni ganador."""
    t = t.copy()
    t['cumple_estabilidad'] = (t['ari_completo_media'] >= 0.65) & (t['ari_entre_media'] >= 0.65)
    t['cumple_nula'] = t['silueta_supera_todas'] & t['ari_entre_media_supera_todas']
    t['lista_37C'] = t['cumple_estabilidad'] & t['cumple_nula']
    t['senal_grupos_pequenos'] = t['grupos_pequenos'] > 0
    t['senal_eje1'] = t['fraccion_eje1'] >= 0.80
    t['senal_repeticiones_inestables'] = t['ari_entre_p05'] < 0.65
    t = t.merge(resumen_sens, on='config', how='left')
    lista = t[t['lista_37C']].copy()
    lista['familia_reduccion'] = lista['metodo']
    if len(lista) > M:
        vis = lista.sort_values('ari_entre_media', ascending=False).groupby(['metodo', 'algoritmo', 'k'], sort=False).head(1)
    else:
        vis = lista
    t['lista_37C_visible'] = t['config'].isin(vis['config'])
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', default=str(Q.BASE))
    S = Path(ap.parse_args().salida).resolve()
    lotes = cargar_lotes(S)
    ids = Q.identificadores()
    cfgs = pd.DataFrame(Q.configuraciones())
    cfgs['parametros'] = np.where(cfgs['algoritmo'] == 'km', "KMeans(n_init=50, random_state=42, algorithm='lloyd')", "AgglomerativeClustering(linkage='ward', metric='euclidean')")
    cfgs['estado'] = 'completa'
    a_csv(cfgs, S / 'resultados' / 'configuraciones.csv')
    import platform

    import scipy
    import sklearn
    (S / 'resultados' / 'entorno.json').write_text(json.dumps({'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__, 'scipy': scipy.__version__, 'scikit_learn': sklearn.__version__, 'semilla': Q.SEMILLA, 'remuestreos': Q.N_REP, 'tamano_subconjunto': Q.N_SUB, 'replicas_nulas': Q.N_NULA, 'hilos_por_proceso': 1}, indent=1) + '\n', encoding='utf-8', newline='\n')

    # etiquetas
    et = pd.DataFrame({'participante_id': ids, **{d['config']: d['etiquetas'] for d in lotes}})
    a_csv(et, S / 'etiquetas' / 'etiquetas_principales.csv')

    # calidad, tamaños y siluetas
    calidad_cols = COMUNES + ['iteraciones', 'max_iter', 'convergio', 'inercia', 'silueta', 'silueta_negativos', 'silueta_min', 'silueta_max', 'davies_bouldin', 'calinski_harabasz', 'fraccion_eje1', 'ari_semilla_alterna', 'inercia_semilla_alterna']
    cal = pd.DataFrame([{c: d.get(c) for c in calidad_cols} for d in lotes])
    a_csv(cal, S / 'resultados' / 'metricas_calidad.csv')
    tam = pd.DataFrame([{**{c: d[c] for c in COMUNES}, **{c: d[c] for c in ('tam_min', 'tam_max', 'razon_tam', 'equilibrio', 'grupos_pequenos')}, 'tam_min_pct': 100 * d['tam_min'] / Q.N, 'tamanos': ' '.join(map(str, d['tamanos']))} for d in lotes])
    a_csv(tam, S / 'resultados' / 'tamanos_grupos.csv')
    peq = [{'config': d['config'], 'grupo': g, 'n': n, 'pct': 100 * n / Q.N} for d in lotes for g, n in enumerate(d['tamanos']) if n < Q.UMBRAL_TAMANO]
    a_csv(pd.DataFrame(peq, columns=['config', 'grupo', 'n', 'pct']), S / 'resultados' / 'grupos_pequenos.csv')
    a_csv(pd.DataFrame([{'config': d['config'], **g} for d in lotes for g in d['silueta_por_grupo']]), S / 'resultados' / 'siluetas_por_grupo.csv')

    # estabilidad
    subs = Q.subconjuntos()
    a_csv(pd.DataFrame({'repeticion': [r for r, x in enumerate(subs) for _ in x], 'semilla_kmeans': [Q.semilla_rep(r) for r, x in enumerate(subs) for _ in x], 'participante_id': [ids[i] for x in subs for i in x]}), S / 'estabilidad' / 'remuestreos.csv')
    est_cols = [f'{p}_{s}' for p in ('ari_completo', 'ari_entre', 'ari_fuera') for s in ('media', 'mediana', 'de', 'min', 'max', 'p05', 'p25', 'p75', 'n_baja', 'n_intermedia', 'n_alta')]
    est = pd.DataFrame([{**{c: d[c] for c in COMUNES}, **{c: d[c] for c in est_cols}} for d in lotes])
    a_csv(est, S / 'estabilidad' / 'resumen_estabilidad.csv')
    a_csv(pd.DataFrame([{'config': d['config'], 'repeticion': r, 'ari_completo': a, 'ari_fuera': b} for d in lotes for r, (a, b) in enumerate(zip(d['ari_completo_rep'], d['ari_fuera_rep']))]), S / 'estabilidad' / 'ari_por_remuestreo.csv')

    # prototipos y distancias
    (S / 'prototipos').mkdir(exist_ok=True)
    for e in Q.ESPACIOS + Q.ESPACIOS_R0:
        for a in Q.ALGORITMOS:
            g = [d for d in lotes if d['espacio'] == e and d['algoritmo'] == a]
            (S / 'prototipos' / f'prototipos_{e}_{a}.json').write_text(json.dumps({d['config']: {'tipo': 'centroide de K-means' if a == 'km' else 'centroide de los grupos formados (no equivale a la asignación jerárquica)', 'componentes': d['componentes'], 'k': d['k'], 'centroides': d['centroides'], 'distancia_p95_grupo': d['distancia_p95_grupo']} for d in g}, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
            filas = {'participante_id': ids}
            for d in g:
                X = Q.coordenadas(e, d['componentes']).to_numpy()
                _, d1, _, mar = Q.asignar(d['centroides'], X)
                filas[d['config'] + '__d'] = np.round(d1, 5)
                filas[d['config'] + '__margen'] = np.round(mar, 5)
            a_csv(pd.DataFrame(filas), S / 'prototipos' / f'distancias_{e}_{a}.csv')
    asg = pd.DataFrame([{**{c: d[c] for c in COMUNES}, 'acuerdo_prototipo_pct': d['acuerdo_prototipo_pct'], 'acuerdo_prototipo_ari': d['acuerdo_prototipo_ari'], 'margen_mediano': d['margen_mediano'], **{c: d[c] for c in est_cols if c.startswith('ari_fuera') and c.split('_')[-1] in ('media', 'min', 'p05')}} for d in lotes])
    a_csv(asg, S / 'prototipos' / 'evaluacion_asignacion.csv')

    # comparaciones entre configuraciones
    obs_imc = imc_observado()
    filas = []
    L = {c: et[c].to_numpy() for c in et.columns if c != 'participante_id'}
    pares = [('P1', 'P2', 'Con y sin IMC, PCA'), ('F1', 'F2', 'Con y sin IMC, FAMD'), ('R0P1', 'R0P2', 'Con y sin IMC, sin reducción'), ('P1', 'F1', 'PCA y FAMD, con IMC'), ('P2', 'F2', 'PCA y FAMD, sin IMC')]
    for a_, b_, nombre in pares:
        for c in ([0] if a_.startswith('R0') else Q.COMPONENTES):
            sufijo = 'cTodas' if c == 0 else f'c{c:02d}'
            for a in Q.ALGORITMOS:
                for k in Q.CLUSTERES:
                    x, y = L[f'{a_}_{sufijo}_{a}_k{k}'], L[f'{b_}_{sufijo}_{a}_k{k}']
                    filas.append({'comparacion': nombre, 'a': a_, 'b': b_, 'componentes': c, 'algoritmo': a, 'k': k, 'ari_529': adjusted_rand_score(x, y), 'ari_267_imc_observado': adjusted_rand_score(x[obs_imc], y[obs_imc]) if 'IMC' in nombre else np.nan})
    for e in Q.ESPACIOS + Q.ESPACIOS_R0:
        for c in ([0] if e.startswith('R0') else Q.COMPONENTES):
            sufijo = 'cTodas' if c == 0 else f'c{c:02d}'
            for k in Q.CLUSTERES:
                filas.append({'comparacion': 'K-means y aglomerativo', 'a': e, 'b': e, 'componentes': c, 'algoritmo': 'km-ward', 'k': k, 'ari_529': adjusted_rand_score(L[f'{e}_{sufijo}_km_k{k}'], L[f'{e}_{sufijo}_ward_k{k}']), 'ari_267_imc_observado': np.nan})
    a_csv(pd.DataFrame(filas), S / 'resultados' / 'comparaciones_ari.csv')
    filas = []
    for d in lotes:
        if d['con_imc']:
            l = np.array(d['etiquetas'])
            for g in range(d['k']):
                filas.append({'config': d['config'], 'grupo': g, 'n': int((l == g).sum()), 'imc_imputado_pct': 100 * float((~obs_imc[l == g]).mean())})
    a_csv(pd.DataFrame(filas), S / 'resultados' / 'imc_imputado_por_grupo.csv')

    # referencia nula
    faltan = [r for r in range(Q.N_NULA) if not (S / 'referencia_nula' / 'lotes' / f'replica_{r:02d}.csv').exists()]
    if faltan:
        raise SystemExit(f'Faltan réplicas nulas: {faltan}')
    nula = pd.concat([pd.read_csv(S / 'referencia_nula' / 'lotes' / f'replica_{r:02d}.csv') for r in range(Q.N_NULA)], ignore_index=True)
    if len(nula) != Q.N_NULA * 420:
        raise SystemExit(f'Filas nulas: {len(nula)}')
    a_csv(nula, S / 'referencia_nula' / 'metricas_por_replica.csv')
    obs = cal.merge(est.drop(columns=COMUNES[1:]), on='config')
    comp = nula_por_config(nula, obs)
    a_csv(comp, S / 'referencia_nula' / 'comparacion_por_configuracion.csv')
    bm = busqueda_multiple(nula, obs)
    a_csv(bm, S / 'referencia_nula' / 'busqueda_multiple.csv')

    # sensibilidades
    nombres = sorted(p.parent.parent.name + '_' + p.parent.name for p in (Q.A37 / 'sensibilidades').glob('*/*/modelo.json'))
    faltan = [v for v in nombres if not (S / 'sensibilidades' / 'lotes' / f'{v}.csv').exists()]
    if faltan:
        raise SystemExit(f'Faltan sensibilidades: {faltan}')
    sens = pd.concat([pd.read_csv(S / 'sensibilidades' / 'lotes' / f'{v}.csv') for v in nombres], ignore_index=True)
    if len(sens) != 3332:
        raise SystemExit(f'Ajustes de sensibilidad: {len(sens)}')
    a_csv(sens, S / 'sensibilidades' / 'comparacion_sensibilidades.csv')
    res_sid = sens.groupby(['familia', 'sensibilidad', 'algoritmo']).agg(ari_ajuste_mediana=('ari_ajuste', 'median'), ari_ajuste_p25=('ari_ajuste', lambda v: np.percentile(v, 25)), ari_ajuste_p75=('ari_ajuste', lambda v: np.percentile(v, 75)), ari_proyeccion_mediana=('ari_proyeccion', 'median'), ajustes_con_grupo_pequeno=('grupos_pequenos', lambda v: int((v > 0).sum())), ajustes=('ari_ajuste', 'size')).reset_index()
    a_csv(res_sid, S / 'sensibilidades' / 'resumen_por_variante.csv')
    resumen_sens = sens.pivot_table(index='config_base', columns='familia', values='ari_ajuste', aggfunc='median').rename(columns=lambda c: f'sens_{c}').rename_axis(columns=None).reset_index().rename(columns={'config_base': 'config'})

    # lista para la Fase 37C
    t = cal.merge(tam.drop(columns=COMUNES[1:]), on='config').merge(est.drop(columns=COMUNES[1:]), on='config').merge(asg[['config', 'acuerdo_prototipo_pct', 'acuerdo_prototipo_ari', 'margen_mediano']], on='config')
    supera = comp[['config'] + [f'{m}_supera_todas' for m in MEDIDAS_NULA] + [f'{m}_z' for m in MEDIDAS_NULA]]
    t = preseleccion(t.merge(supera, on='config'), resumen_sens)
    a_csv(t, S / 'resultados' / 'tabla_completa_configuraciones.csv')
    print('Configuraciones:', len(t), '| en lista:', int(t['lista_37C'].sum()), '| visibles:', int(t['lista_37C_visible'].sum()))
    print(bm.round(3).to_string())


if __name__ == '__main__':
    main()
